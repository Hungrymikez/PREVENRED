"""
Puerto CaseCodeGenerator: el consecutivo visible que se le muestra al ciudadano
(`INC-2026-0001`, RF-22).

Por qué es un puerto compartido y no un repositorio: incidentes, inmuebles y
necesidades de ayuda necesitan el MISMO formato de código y la MISMA garantía
(que dos casos no repitan número), aunque cada uno viva en su colección. El
dominio no sabe de dónde sale el número; la capa de infraestructura decide cómo
se cuenta (en MongoDB: un documento de `counters` incrementado atómicamente).
"""
from abc import ABC, abstractmethod
from enum import StrEnum


class CaseKind(StrEnum):
    """Prefijo del consecutivo: a qué tipo de caso pertenece el código (RF-22)."""
    INCIDENTE = "INC"        # reportes de emergencia (CU-29)
    INMUEBLE = "INM"         # inspecciones de inmuebles (CU-17/33)
    AYUDA = "AYU"            # necesidades de ayuda (CU-31)
    SERVICIO = "SRV"         # solicitudes de servicio (CU-40)


class CaseCodeGenerator(ABC):
    """Puerto: entrega el siguiente código de caso, único dentro del año en curso.

    Garantía que deben cumplir TODAS las implementaciones: dos llamadas seguidas
    NUNCA devuelven el mismo código, aunque las hagan dos procesos a la vez.
    """

    @abstractmethod
    def next_code(self, kind: CaseKind, *, year: int | None = None) -> str:
        """Devuelve el siguiente código (`INC-2026-0001`) y lo da por consumido.

        `year` solo se usa para pruebas o para recuperar un consecutivo de un año
        anterior; por omisión es el año en curso.
        """
