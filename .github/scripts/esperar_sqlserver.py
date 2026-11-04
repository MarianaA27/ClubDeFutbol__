"""Espera (hasta 120 s) a que el contenedor de SQL Server acepte conexiones."""
import os
import sys
import time

import pyodbc

cadena = (f"DRIVER={{{os.environ['PALADINES_DB_DRIVER']}}};SERVER={os.environ['PALADINES_DB_SERVER']};"
          f"DATABASE=master;UID={os.environ['PALADINES_DB_USER']};PWD={os.environ['PALADINES_DB_PASSWORD']};"
          "Encrypt=yes;TrustServerCertificate=yes;")
for intento in range(60):
    try:
        version = pyodbc.connect(cadena, timeout=5).cursor().execute("SELECT @@VERSION").fetchone()[0]
        print(version.splitlines()[0])
        sys.exit(0)
    except pyodbc.Error as error:
        print(f"Intento {intento + 1}: SQL Server aún no responde ({error.args[0]})")
        time.sleep(2)
sys.exit("SQL Server no respondió a tiempo.")
