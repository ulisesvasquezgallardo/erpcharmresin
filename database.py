import os
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. Preparación para Producción: Leemos de variables de entorno, o usamos SQLite por defecto
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./erp_epoxicas.db")

# 2. Configuración del Motor
# check_same_thread=False solo se inyecta si estamos usando SQLite
connect_args = {"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args,
    # pool_pre_ping=True ayuda a evitar desconexiones "fantasma" en bases de datos en la nube
    pool_pre_ping=True
)

# 3. BLINDAJE EXPERTO: Forzar a SQLite a respetar las Llaves Foráneas (Foreign Keys)
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if "sqlite" in SQLALCHEMY_DATABASE_URL:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()