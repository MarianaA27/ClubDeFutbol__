"""Punto de entrada: ``python -m paladinesfc`` (con ``src`` en el PYTHONPATH) o ``python run.py``."""
from paladinesfc.presentacion.app import AppClubFutbol


def main() -> None:
    app = AppClubFutbol()
    app.mainloop()


if __name__ == "__main__":
    main()
