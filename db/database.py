# db/database.py
from contextlib import contextmanager
from typing import List
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from loguru import logger

from db.models import Base, Producto, TasasCambio, LogCambio
from config import DATABASE_URL

# #* ─── CONEXIÓN ────────────────────────────────────────────────────────
#? motor con el que se crean las la conexion de la BBDD
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Muestra las consultas SQL en la consola
    pool_pre_ping=True,  # Verifica que la conexión este bien antes de usarla
    pool_size= 5,  # Tamaño del pool de conexiones
    max_overflow= 10,  # Máximo de conexiones adicionales que se pueden crear
    pool_recycle= 3600,  # Tiempo en segundos para reciclar conexiones, 1 hora
)

#? produce las sessiones individuales (por cada operacion CRUD) para interactuar con la BBDD, 
Session = sessionmaker(bind=engine)
#? cual es el proceso?
#& 1. creamos la sesion
# session = Session()
#& 2.usamos la sesion
# session.query(sql)
# session.query(Producto)
#& 3. cerramos la sesion
# session.close()

@contextmanager
def get_session(): # para abrir y cerra autometicamente la sesion
    session = Session()
    try:
        yield session
        session.commit()  # Confirma los cambios si no hay errores
    except Exception as e:
        session.rollback() ## Deshace los cambios si hay errores
        raise
    finally:
        session.close()  # Cierra la sesión al final 

def init_db(): #Crear las las tablas potr si no existen.
    Base.metadata.create_all(engine)
    logger.info("Tablas de la base de datos inicializadas correctamente.") 
    

# #* ─── PRODUCTOS ───────────────────────────────────────────────────────

def obtener_productos_activos() -> List:  
    with get_session() as session: 
        productos = (
            session.query(Producto)  #SELECT FROM * productos WHERE activo = true
            .filter(Producto.activo == True)
            .order_by(Producto.id.asc())
            .all()
        )
        for p in productos:
            session.expunge(p)  # Desvincula el objeto de la sesión para evitar problemas de cierre
        return productos
            
#TODO def obtener_productos_por_id() -> List:   
        