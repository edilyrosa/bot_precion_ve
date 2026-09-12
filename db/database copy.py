# def actualizar_precios_ves():
#     pass
# def grardar_log():
#     pass
# def get_session():
#     pass
# def obtener_productos():
#     pass
# def guardar_tasa():
#     pass 
# def obtener_ultima_tasa():
#     pass



# db/database.py
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from loguru import logger

from db.models import Base, Producto, TasaCambio, LogCambio
from config import DATABASE_URL

#* ─── CONEXIÓN ────────────────────────────────────────────────────────
engine = create_engine(             #? El "motor" de conexión a la BD
    DATABASE_URL,                   # La cadena de conexión a Supabase
    echo=False,                     # No imprime cada SQL en consola (si True, lo imprime)
    pool_pre_ping=True,             # Antes de usar una conexión, verifica que siga viva
    pool_size=5,                    # Mantiene 5 conexiones abiertas listas para usar
    max_overflow=10,                # Si las 5 están ocupadas, abre hasta 10 más
    pool_recycle=3600,              # Renueva cada conexión después de 1 hora
)
Session = sessionmaker(bind=engine)  #? La "fábrica" de sesiones individuales para cada operación conectadas a ese motor.

# session = Session() # 1. Creas una sesión
# session.query(TABLA).all() 2. Usas la sesión, tomando una conexión del pool.
# session.close()3. Cierras la sesión (devuelve la conexión al pool)

@contextmanager
def get_session():
    """Abre y cierra la sesión automáticamente."""
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db():
    """Crea las tablas si no existen."""
    Base.metadata.create_all(engine)
    logger.info("Base de datos inicializada.")


#* ─── PRODUCTOS ───────────────────────────────────────────────────────
def obtener_productos_activos() -> list: # Func que usaremos en bot/telegram_bot.py para mostrar los productos activos en el menú
    with get_session() as session: # get_session() la acabamos de crear arriba, es un context manager que abre y cierra la sesión automáticamente.
        productos = ( # La llamada a esta Fucn retorna una lista de objetos Producto, activos (activo=True) y ordenados por id ascendente.
            session.query(Producto) #  → SELECT * FROM productos
            .filter(Producto.activo == True)
            .order_by(Producto.id.asc())
            .all()
        )
        for p in productos:
            session.expunge(p) # Desvinculacada ele de la sesión, para que no se cierre al salir del context manager.
        return productos


def obtener_producto_por_id(producto_id: int):
    with get_session() as session:
        producto = session.get(Producto, producto_id)
        if producto:
            session.expunge(producto)
        return producto




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