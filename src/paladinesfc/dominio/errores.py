"""Errores del dominio."""


class ReglaNegocioError(ValueError):
    """Se viola una regla de negocio. El mensaje está pensado para la usuaria final.

    Hereda de ``ValueError`` para que la interfaz existente (que muestra el texto
    de cualquier ``ValueError`` en un cuadro de diálogo) no requiera cambios.
    """


class NoEncontradoError(ReglaNegocioError):
    """El registro solicitado no existe."""
