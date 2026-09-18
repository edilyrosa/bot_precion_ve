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
            session.query(Producto)  # SELECT FROM * productos WHERE activo = true
            .filter(Producto.activo == True)
            .order_by(Producto.id.asc())
            .all()
        )
        for p in productos:
            session.expunge(p)  # Desvincula el objeto de la sesión para evitar problemas de cierre
        return productos
            
#TODO def obtener_producto_por_id(), actualizar_producto() -> List:   
def obtener_producto_por_id(producto_id:int):
        with get_session() as session: 
            producto = session.get(Producto, producto_id)  #SELECT FROM * productos WHERE activo = true
            if producto:
                session.expunge(producto)  # Desvincula el objeto de la sesión para evitar problemas de cierre 
            return producto


def actualizar_producto(producto_id:int, precio_usd:float =None, precio_ves:float=None):
    #Actualizar el precio en USD o VES de un producto en la base de datos, Y SOLOL ESOS CAMPOS
    with get_session() as session:  
        producto = session.get(Producto, producto_id)  #SELECT FROM * productos WHERE activo = true
        if not producto:
            return None  # Producto no encontrado
        
        if precio_usd is not None:
            producto.precio_usd = precio_usd
        if precio_ves is not None:
            producto.precio_ves = precio_ves
    logger.info(f"Producto {producto_id} actualizado: precio_usd={precio_usd}, precio_ves={precio_ves}")

