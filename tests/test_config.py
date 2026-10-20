"""ADR-0002 (mejora colateral): la cadena de conexión ya no está fijada en el código."""
from paladinesfc.infraestructura.config import cargar_config


def test_valores_por_defecto_sin_archivo_ni_entorno(tmp_path):
    cfg = cargar_config(ruta_ini=tmp_path / "no_existe.ini", entorno={})
    assert cfg.server == "localhost"
    assert cfg.database == "ClubFutbolDB"
    assert cfg.trusted_connection is True
    assert "SERVER=localhost;" in cfg.cadena()
    assert "GIANY" not in cfg.cadena()


def test_archivo_ini_sobrescribe_valores_por_defecto(tmp_path):
    ini = tmp_path / "config.ini"
    ini.write_text("[database]\nserver = EQUIPO-CLUB\\SQLEXPRESS\n", encoding="utf-8")
    cfg = cargar_config(ruta_ini=ini, entorno={})
    assert cfg.server == "EQUIPO-CLUB\\SQLEXPRESS"


def test_variables_de_entorno_tienen_prioridad(tmp_path):
    ini = tmp_path / "config.ini"
    ini.write_text("[database]\nserver = DESDE-ARCHIVO\n", encoding="utf-8")
    cfg = cargar_config(ruta_ini=ini, entorno={"PALADINES_DB_SERVER": "DESDE-ENTORNO"})
    assert cfg.server == "DESDE-ENTORNO"


def test_autenticacion_sql_usa_usuario_y_clave(tmp_path):
    cfg = cargar_config(ruta_ini=tmp_path / "x.ini", entorno={
        "PALADINES_DB_TRUSTED": "no",
        "PALADINES_DB_USER": "club",
        "PALADINES_DB_PASSWORD": "secreta",
    })
    cadena = cfg.cadena()
    assert "Trusted_Connection" not in cadena
    assert "UID=club;" in cadena and "PWD=secreta;" in cadena
