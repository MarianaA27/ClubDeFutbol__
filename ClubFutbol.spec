# -*- mode: python ; coding: utf-8 -*-
# Empaquetado de PaladinesFC con la nueva estructura (issue #20).
#
#   pip install pyinstaller
#   pyinstaller ClubFutbol.spec
#
# Resultado: dist/ClubFutbol.exe. Junto al .exe se copia config.ini.example: renómbrelo a
# config.ini y ajuste el servidor. La bitácora se crea en dist/logs/ al primer fallo.
from pathlib import Path
import shutil

from PyInstaller.utils.hooks import collect_data_files

RAIZ = Path(SPECPATH)

a = Analysis(
    ['run.py'],
    pathex=[str(RAIZ / 'src')],
    binaries=[],
    # customtkinter necesita sus temas y fuentes; los scripts SQL viajan para referencia
    datas=collect_data_files('customtkinter') + [('src/sql', 'sql')],
    hiddenimports=['pyodbc'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # La API, las pruebas y la evaluación no forman parte del ejecutable de escritorio
    excludes=['fastapi', 'uvicorn', 'starlette', 'pytest', 'httpx'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ClubFutbol',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icono.ico'],
)

# config.ini va FUERA del .exe (junto a él) para poder cambiar el servidor sin recompilar
shutil.copy(RAIZ / 'config.ini.example', Path(DISTPATH) / 'config.ini.example')
