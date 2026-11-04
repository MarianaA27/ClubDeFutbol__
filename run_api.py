"""Ejecuta la API REST del MVP: ``python run_api.py`` y abra http://127.0.0.1:8000/docs (Swagger)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

import uvicorn  # noqa: E402

from paladinesfc.presentacion.api import crear_app  # noqa: E402

if __name__ == "__main__":
    puerto = int(os.environ.get("PALADINES_API_PUERTO", "8000"))
    uvicorn.run(crear_app(), host="127.0.0.1", port=puerto)
