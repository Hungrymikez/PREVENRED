"""
Implementación del puerto `SecondFactorGateway` (CU-03).

`InMemorySecondFactorGateway` es una implementación DIDÁCTICA y COMPLETA:
  - genera un `OneTimeCode` de 6 dígitos y recuerda cuál entregó para cada secreto;
  - si la cuenta aún no tiene secreto, crea uno aleatorio y lo devuelve CIFRADO;
  - compara en tiempo constante y no acepta dos veces el mismo código.

El secreto se envuelve con un marcador reversible (`enc:v1:`): el cifrado real
depende del gestor de claves (doc 07, O-16). Lo importante es el CONTRATO: el
dominio nunca recibe el secreto en claro.

Para usar TOTP real basta con otra clase que implemente el mismo puerto.
"""
import secrets
from collections.abc import Callable

from prevenred.identity.domain.repositories import SecondFactorGateway
from prevenred.identity.domain.value_objects import OneTimeCode, SecondFactorMethod

_PREFIX = "enc:v1:"


class InMemorySecondFactorGateway(SecondFactorGateway):
    """Gateway de v1: códigos de un solo uso, en memoria del proceso."""

    def __init__(self, method: SecondFactorMethod | None = None) -> None:
        self._method = method or SecondFactorMethod("totp")
        self._issued: dict[str, str] = {}        # code_hash -> código en claro
        self._current: dict[str, str] = {}       # secret_enc -> code_hash vigente

    def default_method(self) -> SecondFactorMethod:
        """El método que se ofrece cuando la operación no impone uno."""
        return self._method

    def issue_code(
        self, *, secret_enc: str, code_hash: Callable[[str], str]
    ) -> tuple[str, str]:
        """Entrega un código nuevo; crea y cifra el secreto si la cuenta no tiene."""
        if not secret_enc:
            secret_enc = _PREFIX + secrets.token_urlsafe(20)
        code = OneTimeCode.generate()
        # Un código nuevo invalida el anterior de ese secreto: pedir otro código
        # deja inservible el viejo aunque todavía no haya vencido.
        previous = self._current.get(secret_enc)
        if previous is not None:
            self._issued.pop(previous, None)
        digest = code_hash(code.value)
        self._issued[digest] = code.value
        self._current[secret_enc] = digest
        return code, secret_enc

    def matches(self, *, code: OneTimeCode, code_hash: str) -> bool:
        """True si el código produce ese hash; el código entregado se consume (uso único)."""
        expected = self._issued.pop(code_hash, None)
        if expected is None:
            return False
        return code.mismo_valor_que(OneTimeCode(expected))