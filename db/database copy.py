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
            
#TODO def obtener_producto_por_id() -> List:   
#TODO def actualizar_producto()
#TODO ─── PRODUCTOS ───────────────────────────────────────────────────────

def obtener_producto_por_id(producto_id: int):
    """Devuelve un producto por su ID, o None si no existe."""
    with get_session() as session:
        producto = session.get(Producto, producto_id)
        if producto:
            session.expunge(producto)  # Desvincula antes de cerrar la sesión
        return producto

def actualizar_producto(producto_id: int, precio_usd: float = None, precio_ves: float = None) -> None:
    """Actualiza precio USD y/o VES de un producto. Solo cambia los valores que se pasen."""
    with get_session() as session:
        producto = session.get(Producto, producto_id)
        if not producto:
            return
        if precio_usd is not None:
            producto.precio_usd = precio_usd
        if precio_ves is not None:
            producto.precio_ves = precio_ves
    logger.info(f"Producto ID {producto_id} actualizado.")



# def actualizar_precio_ves(producto_id: int, precio_nuevo: float) -> None:
#     with get_session() as session:
#         producto = session.get(Producto, producto_id)
#         if producto:
#             producto.precio_ves = precio_nuevo
#     logger.info(f"Precio VES actualizado: ID {producto_id} → {precio_nuevo} Bs")


# def actualizar_producto(producto_id: int, precio_usd: float = None, precio_ves: float = None) -> None:
#     with get_session() as session:
#         producto = session.get(Producto, producto_id)
#         if not producto:
#             return
#         if precio_usd is not None:
#             producto.precio_usd = precio_usd
#         if precio_ves is not None:
#             producto.precio_ves = precio_ves


# # ─── TASAS ───────────────────────────────────────────────────────────
# def guardar_tasa(fuente: str, tasa: float) -> None:
#     with get_session() as session:
#         session.add(TasaCambio(fuente=fuente, tasa=tasa))
#     logger.info(f"Tasa guardada: {fuente} = {tasa}")


# def obtener_ultima_tasa(fuente: str = "BCV") -> float | None:
#     with get_session() as session:
#         registro = (
#             session.query(TasaCambio)
#             .filter(TasaCambio.fuente == fuente)
#             .order_by(TasaCambio.timestamp.desc())
#             .first()
#         )
#         return registro.tasa if registro else None


# # ─── LOGS ────────────────────────────────────────────────────────────
# def guardar_log(producto_id: int, producto_nombre: str, precio_antes: float,
#                 precio_despues: float, tasa: float, aprobado: bool) -> None:
#     variacion = (
#         round((precio_despues - precio_antes) / precio_antes * 100, 2)
#         if precio_antes != 0 else 100.0
#     )
#     with get_session() as session:
#         session.add(LogCambio(
#             producto_id=producto_id,
#             producto_nombre=producto_nombre,
#             precio_antes=precio_antes,
#             precio_despues=precio_despues,
#             variacion_pct=variacion,
#             tasa_usada=tasa,
#             aprobado=aprobado,
#         ))
#     logger.info(f"Log: {producto_nombre} {'APROBADO' if aprobado else 'RECHAZADO'}")