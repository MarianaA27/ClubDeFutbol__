# Cobertura de pruebas del dominio y la aplicación (E1)

Medida del Entregable 1 (§3.4, Mantenibilidad): *"Las reglas de dominio de los cuatro
módulos se ejecutan sin interfaz gráfica ni base de datos, con cobertura de pruebas igual
o superior al 70 %"*.

Se mide con las **119 pruebas unitarias** (dobles en memoria, sin SQL Server ni pantallas):

```bash
pip install -r requirements.txt          # incluye pytest-cov
python -m pytest --cov=src/paladinesfc/dominio --cov=src/paladinesfc/aplicacion --cov-report=term
```

## Resultado (2026-11-05)

| Archivo | Sentencias | Sin cubrir | Cobertura |
|---|---|---|---|
| `dominio/jugador.py` | 50 | 2 | 96 % |
| `dominio/tutor.py` | 43 | 3 | 93 % |
| `dominio/profesor.py` | 46 | 3 | 93 % |
| `dominio/vinculo.py` | 57 | 3 | 95 % |
| `dominio/validaciones.py` | 75 | 5 | 93 % |
| `dominio/errores.py`, `__init__.py` | 8 | 0 | 100 % |
| **Dominio (total)** | **279** | **16** | **94 %** |
| `aplicacion/jugador_service.py` | 56 | 0 | 100 % |
| `aplicacion/tutor_service.py` | 49 | 1 | 98 % |
| `aplicacion/profesor_service.py` | 55 | 2 | 96 % |
| `aplicacion/vinculacion_service.py` | 31 | 2 | 94 % |
| `aplicacion/puertos.py`, `_base.py`, `__init__.py` | 23 | 0 | 100 % |
| **Aplicación (total)** | **214** | **5** | **98 %** |
| **Dominio + aplicación** | **493** | **21** | **96 %** |

**¿Cumple?** Sí: cada archivo está entre 93 % y 100 %, por encima de la meta del 70 %.

Como referencia, la misma ejecución da 77 % en `infraestructura/` (los repositorios SQL
se prueban sobre todo en `tests/integracion/`, contra SQL Server) y 97 % en la API
(`presentacion/api/`). Las pantallas de CustomTkinter y el código legado no forman parte
de la meta.
