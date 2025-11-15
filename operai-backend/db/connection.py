# AGENT/db/connection.py
import os
from dotenv import load_dotenv   # ← NUEVO
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

load_dotenv()  # ← NUEVO: carga .env del proyecto

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")   # ← opcional
MYSQL_DB   = os.getenv("MYSQL_DB", "casino_gastos")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASS = os.getenv("MYSQL_PASS", "root")

_DSN = f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASS}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
_engine: Engine | None = None

def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(
            _DSN,
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_size=5,
            max_overflow=10,
        )
    return _engine
