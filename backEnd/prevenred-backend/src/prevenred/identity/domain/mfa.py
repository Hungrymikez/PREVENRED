"""
CU-03 · Autenticación reforzada (MFA) de las cuentas administrativas (RN-07).

Por qué existe: un administrador puede cambiar el modo operacional de todo el
sistema (CU-04). Una contraseña sola no basta para esa operación, así que el
sistema exige un SEGUNDO FACTOR y solo continúa si se validó.

Aquí viven las reglas; el envío real del código (TOTP/SMS/correo) es un detalle
técnico que resuelve la capa infrastructure a través de un puerto.

Reglas de la ficha (docs/cu/CU-03.md):
  - paso 3: el segundo factor debe ser correcto, VIGENTE y DE UN SOLO USO.
  - A1: se puede pedir un código nuevo cuando el anterior venció.
  - E1: un código incorrecto o vencido permite reintentar un número LIMITADO.
  - E2: agotados los intentos se bloquea la operación y se registra el evento (CU-05).
  - E3: si el servicio del segundo factor no está disponible, la operación NO se autoriza.
  - Criterio de aceptación: sin verificación reforzada válida no hay cambio de modo.

El mecanismo concreto lo define el documento 07; por eso el código se maneja como
texto (`OneTimeCode`) y no se asume TOTP en la entidad.
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from prevenred.identity.domain.events import (
    MfaEnabled,
    MfaVerificationFailed,
    MfaVerificationLocked,
    MfaVerified,
)
from prevenred.identity.domain.role import Role
from prevenred.identity.domain.value_objects import OneTimeCode, SecondFactorMethod
from prevenred.shared.domain.entity import Entity
from prevenred.shared.domain.errors import (
    ConflictError,
    ForbiddenError,
    TooManyAttemptsError,
    UnauthorizedError,
    ValidationError,
)
from prevenred.shared.domain.events import utcnow
from prevenred.shared.domain.guards import (
    require_between,
    require_one_of,
    require_text,
    require_utc,
)

#: Vigencia de un código (A1: "un nuevo código cuando el anterior venció").
#: Provisional hasta definir el mecanismo y su ventana en el doc 07 (O-16).
CODE_TTL = timedelta(minutes=5)

#: Intentos antes de bloquear la operación (E1/E2). Provisional (O-16).
MFA_MAX_ATTEMPTS = 3

#: Espera mínima antes de pedir otro código (A1). Evita que pedir códigos en
#: bucle se use para adivinar el anterior o para inundar el SMS del administrador.
MIN_RETRY_AFTER = timedelta(seconds=30)

#: Cuánto vale una verificación YA hecha para autorizar la operación protegida.
#: Más larga que el código (que dura CODE_TTL) y más corta que una sesión: el
#: administrador valida una vez y opera; pasado este tiempo debe volver a validar.
#: Provisional hasta fijar las ventanas en el doc 07 (O-16).
VERIFICATION_TTL = timedelta(minutes=10)

#: Estados de un desafío.
CHALLENGE_STATUSES = ("PENDIENTE", "VERIFICADO", "FALLIDO", "EXPIRADO", "BLOQUEADO")

#: Operación del PROPIO inicio de sesión (CU-02 A1). Se declara aquí, junto a los
#: estados, para que el guardia de MFA pueda excluirla: haberse autenticado no
#: autoriza operaciones administrativas, solo permite entrar.
LOGIN_PURPOSE = "login"


@dataclass(kw_only=True, eq=False)
class MfaChallenge(Entity):
    """Desafío del segundo factor para UNA operación crítica (CU-03 pasos 1-5).

    Separado de `User` a propósito: el estado del desafío (código vigente,
    intentos, bloqueo) es de la operación en curso, no de la persona. Así dos
    pestañas del administrador no comparten intentos ni se pisan el código.

    El código se guarda como HASH (`code_hash`), nunca en claro: si alguien lee
    la base no puede usarlo (misma decisión que en `PasswordReset`).
    """
    user_id: str
    purpose: str                       # qué operación se protege (CU-04)
    method: SecondFactorMethod
    code_hash: str
    # Secreto del segundo factor YA cifrado (`users.security.mfa.secretEnc`). Lo
    # entrega la capa de aplicación desde la cuenta; el dominio nunca lo descifra.
    # Sin secreto, ningún código puede ser correcto (se falla cerrado).
    secret_enc: str | None = None
    expires_at: datetime = field(default_factory=lambda: utcnow() + CODE_TTL)
    attempts: int = 0
    status: str = "PENDIENTE"
    verified_at: datetime | None = None
    last_sent_at: datetime = field(default_factory=utcnow)
    created_at: datetime = field(default_factory=utcnow)

    def __post_init__(self) -> None:
        """Valida el desafío: sin usuario, sin propósito o sin hash no existe."""
        require_text(self.user_id, "user_id", max_length=64)
        require_text(self.purpose, "purpose", max_length=60)
        require_text(self.code_hash, "code_hash", max_length=128)
        require_one_of(self.status, CHALLENGE_STATUSES, "status")
        require_between(self.attempts, 0, MFA_MAX_ATTEMPTS, "attempts")
        self.expires_at = require_utc(self.expires_at, "expires_at")
        self.last_sent_at = require_utc(self.last_sent_at, "last_sent_at")
        self.created_at = require_utc(self.created_at, "created_at")
        if self.verified_at is not None:
            self.verified_at = require_utc(self.verified_at, "verified_at")
        if self.status == "VERIFICADO" and self.verified_at is None:
            raise ValidationError("Una verificación satisfecha debe registrar cuándo ocurrió.")

    # ---- Fábrica: la única forma válida de abrir un desafío (CU-03 paso 1) ----
    @classmethod
    def open(
        cls,
        *,
        user_id: str,
        role: Role,
        purpose: str,
        method: SecondFactorMethod,
        code_hash: str,
        secret_enc: str,
        now: datetime | None = None,
    ) -> "MfaChallenge":
        """Abre el desafío del segundo factor para una operación crítica.

        RN-07: solo tiene sentido en cuentas administrativas; pedir MFA a un
        ciudadano sería pedirle un factor que nunca configuró. El secreto es
        obligatorio: sin él no hay forma de validar ningún código.
        """
        if not role.is_administrative:
            raise ForbiddenError(
                "La verificación en dos pasos es solo para cuentas administrativas."
            )
        require_text(secret_enc, "secret_enc", max_length=512)
        issued = require_utc(now or utcnow(), "created_at")
        return cls(
            user_id=user_id,
            purpose=purpose.strip(),
            method=method,
            code_hash=code_hash,
            secret_enc=secret_enc,
            expires_at=issued + CODE_TTL,
            last_sent_at=issued,
            created_at=issued,
        )

    def require_secret(self) -> str:
        """Devuelve el secreto cifrado o lanza si la cuenta no tiene segundo factor.

        E3/RN-07: una cuenta administrativa sin secreto no puede autorizar
        operaciones críticas; se falla cerrado con un mensaje accionable.
        """
        if not self.secret_enc:
            raise ForbiddenError(
                "Tu cuenta no tiene la verificación en dos pasos configurada. "
                "Configúrala antes de hacer esta operación."
            )
        return self.secret_enc

    # ---- Consultas de estado ----
    @property
    def is_satisfied(self) -> bool:
        """CU-03 paso 4: la operación protegida ya puede continuar."""
        return self.status == "VERIFICADO"

    def is_expired(self, now: datetime) -> bool:
        """True si el código venció: A1 permite pedir uno nuevo en ese caso."""
        return now >= self.expires_at

    def is_locked_out(self) -> bool:
        """CU-03 E2: intentos agotados; el desafío ya no acepta códigos."""
        return self.status == "BLOQUEADO"

    def require_not_satisfied(self) -> None:
        """Un desafío satisfecho es de un solo uso: no se revalida ni se reutiliza."""
        if self.is_satisfied:
            raise ConflictError("Esta verificación ya se completó. Abre una nueva operación.")

    def require_satisfied(self, now: datetime | None = None) -> None:
        """Criterio de aceptación de CU-03: sin verificación válida no hay operación.

        La usan las operaciones críticas (CU-08): si el desafío no está VERIFICADO
        —o la verificación venció— se niega con el mismo mensaje que un desafío
        inexistente, para no revelar en qué estado quedó.
        """
        moment = require_utc(now or utcnow(), "now")
        verified = self.verified_at
        if not self.is_satisfied or verified is None or moment >= verified + VERIFICATION_TTL:
            raise ForbiddenError(
                "Esta operación exige la verificación en dos pasos. Pide un código y valídalo."
            )

    # ---- CU-03 paso 3: validar el segundo factor ----
    def verify(
        self,
        submitted_code: OneTimeCode | None,
        *,
        code_matches: bool = True,
        now: datetime | None = None,
    ) -> None:
        """Valida que el código sea correcto, vigente y de un solo uso.

        `code_matches` es el resultado de comparar el código con el secreto del
        segundo factor, que resuelve la capa técnica (Puerto `SecondFactorGateway`):
        este dominio guarda `code_hash`, un HASH, así que no puede descifrarlo
        solo. Pasarlo SIEMPRE explícito evita el error de "olvidar comprobarlo".

        Acepta `None` (texto mal formado, vía `OneTimeCode.parse`): cuenta como
        intento fallido y NO como error distinto, para no revelar nada al atacante.
        Lanza TooManyAttemptsError (E2), ConflictError (reutilización),
        UnauthorizedError (código incorrecto/vencido, E1) o ValidationError (A1).
        Si no lanza, la verificación quedó satisfecha (paso 4) y la operación
        protegida puede continuar.
        """
        moment = require_utc(now or utcnow(), "now")
        self.require_not_satisfied()                       # paso 3: un solo uso
        if self.is_locked_out():                           # E2
            raise TooManyAttemptsError(
                "Se bloquearon los intentos de verificación. Comunícate con otro administrador."
            )
        if self.is_expired(moment):                        # A1
            self.status = "EXPIRADO"
            self._fail(moment, "El código venció. Solicita uno nuevo.")
        if submitted_code is None or not code_matches:
            # E1: se registra el intento y se permite reintentar hasta el límite.
            self._fail(moment, "El código no es correcto. Verifícalo e intenta de nuevo.")

        self.status = "VERIFICADO"
        self.verified_at = moment                   # paso 4: satisfecha la verificación
        self.record_event(
            MfaVerified(user_id=self.user_id, challenge_id=self.id, purpose=self.purpose)
        )

    def _fail(self, moment: datetime, message: str) -> None:
        """Cuenta el intento fallido y decide si todavía se puede reintentar (E1/E2).

        Siempre lanza: un intento fallido nunca deja el desafío "aprobado" por
        descuido; la operación crítica sigue bloqueada.
        """
        self.attempts += 1
        if self.attempts >= MFA_MAX_ATTEMPTS:
            self.status = "BLOQUEADO"
            self.record_event(
                MfaVerificationLocked(
                    user_id=self.user_id,
                    challenge_id=self.id,
                    purpose=self.purpose,
                    attempts=self.attempts,
                )
            )
            raise TooManyAttemptsError(
                "Agotaste los intentos de verificación. La operación quedó bloqueada."
            )
        self.record_event(
            MfaVerificationFailed(
                user_id=self.user_id,
                challenge_id=self.id,
                purpose=self.purpose,
                attempts=self.attempts,
            )
        )
        raise UnauthorizedError(
            f"{message} Te quedan {MFA_MAX_ATTEMPTS - self.attempts} intento(s)."
        )

    # ---- A1: pedir un código nuevo ----
    def issue_code(self, *, code_hash: str, now: datetime | None = None) -> None:
        """Entrega un código nuevo (paso 1 y A1) sin las esperas de `request_new_code`.

        Es el envío del código que el puerto técnico acaba de producir tras
        obtener el secreto vigente. Los intentos se reinician porque es un
        código distinto; `request_new_code` sigue siendo la vía para pedirlo
        desde la interfaz, con su espera mínima.
        """
        moment = require_utc(now or utcnow(), "now")
        self.require_not_satisfied()
        if self.is_locked_out():
            raise TooManyAttemptsError(
                "La verificación está bloqueada. No se pueden pedir más códigos."
            )
        require_text(code_hash, "code_hash", max_length=128)
        self.code_hash = code_hash
        self.expires_at = moment + CODE_TTL
        self.last_sent_at = moment
        self.attempts = 0
        self.status = "PENDIENTE"

    def request_new_code(
        self, *, new_code_hash: str, now: datetime | None = None
    ) -> None:
        """A1: reemplaza el código vencido (o no recibido) por uno nuevo.

        Reglas:
          - no después de agotar los intentos (sería saltarse E2 por la puerta trasera);
          - no mientras el código anterior sigue vigente (antivigencia: pedirlo de
            inmediato anularía el código antes de que llegue al administrador) y con
            una espera mínima entre envíos;
          - no en un desafío ya verificado (sería reutilizar la operación).
        """
        moment = require_utc(now or utcnow(), "now")
        self.require_not_satisfied()
        if self.is_locked_out():
            raise TooManyAttemptsError(
                "La verificación está bloqueada. No se pueden pedir más códigos."
            )
        require_text(new_code_hash, "code_hash", max_length=128)
        if moment - self.last_sent_at < MIN_RETRY_AFTER:
            raise TooManyAttemptsError("Espera unos segundos antes de pedir otro código.")
        self.code_hash = new_code_hash
        self.expires_at = moment + CODE_TTL
        self.last_sent_at = moment
        # Intentos frescos: el código nuevo es un intento nuevo, no la continuación del viejo.
        self.attempts = 0
        self.status = "PENDIENTE"

    # ---- E3: el servicio del segundo factor no responde ----
    def fail_on_service_unavailable(self) -> None:
        """E3: sin el servicio del segundo factor la operación crítica NO se autoriza.

        Se falla cerrado: se bloquea el desafío (no se deja "pendiente" para que
        alguien lo apruebe por otro camino) y se registra el bloqueo (CU-05).
        """
        if self.is_satisfied:
            return
        self.status = "BLOQUEADO"
        self.record_event(
            MfaVerificationLocked(
                user_id=self.user_id,
                challenge_id=self.id,
                purpose=self.purpose,
                attempts=self.attempts,
            )
        )


@dataclass(kw_only=True, eq=False)
class MfaSettings(Entity):
    """Configuración del segundo factor de una cuenta (`users.security.mfa`).

    El secreto se guarda CIFRADO (`secretEnc`) y aquí nunca se maneja en claro:
    descifrarlo es trabajo de la capa infrastructure con la clave del servidor.
    """
    user_id: str
    enabled: bool = False
    secret_enc: str | None = None
    method: SecondFactorMethod = field(default_factory=lambda: SecondFactorMethod("TOTP"))
    confirmed_at: datetime | None = None

    def __post_init__(self) -> None:
        """Valida la coherencia: un segundo factor activo siempre tiene secreto."""
        require_text(self.user_id, "user_id", max_length=64)
        if self.confirmed_at is not None:
            self.confirmed_at = require_utc(self.confirmed_at, "confirmed_at")
        if self.enabled:
            require_text(self.secret_enc or "", "secret_enc", max_length=512)

    @property
    def is_configured(self) -> bool:
        """True si la cuenta ya tiene un segundo factor utilizable (precondición de CU-03)."""
        return self.enabled and bool(self.secret_enc)

    def enable(
        self, *, secret_enc: str, method: SecondFactorMethod, now: datetime | None = None
    ) -> None:
        """Configura y activa el segundo factor (RN-07).

        Si ya había otro secreto, se REEMPLAZA: el anterior deja de servir (así
        se revoca un autenticador perdido).
        """
        require_text(secret_enc, "secret_enc", max_length=512)
        self.secret_enc = secret_enc
        self.method = method
        self.enabled = True
        self.confirmed_at = require_utc(now or utcnow(), "confirmed_at")
        self.record_event(MfaEnabled(user_id=self.user_id, method=str(method)))

    def disable(self, *, role: Role) -> None:
        """Apaga el segundo factor. RN-07 lo PROHÍBE en cuentas administrativas.

        Es la regla que sostiene CU-04: si un administrador pudiera apagar el
        segundo factor, el control de CU-03 quedaría a un clic de desaparecer.
        """
        if role.is_administrative:
            raise ForbiddenError(
                "La verificación en dos pasos es obligatoria para las cuentas administrativas."
            )
        self.enabled = False
        self.secret_enc = None
        self.confirmed_at = None


