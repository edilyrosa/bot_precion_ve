
# db/models.py
#* Representación en Python de las tablas que ya existen en Supabase.
#? cada __tablename__ debe coincidir exacto con el nombre de la tabla en Supabase.

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base() 

class Producto(Base):
    __tablename__ = 'productos'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(200), nullable=False)
    categoria = Column(String(100))
    precio_usd = Column(Float, default=0.0)
    precio_ves = Column(Float, default=0.0)
    activo = Column(Boolean, default=True) 
    # creado_en  = Column(DateTime, default=datetime.utcnow)   # TODO ← AGREGAR ESTA LÍNEA
    
class TasasCambio(Base):
    __tablename__    = 'tasas_cambio'  
    id              = Column(Integer, primary_key=True, autoincrement=True)
    fuente           = Column(String(50), nullable=False)
    tasa             = Column(Float, nullable=False)
    timestamp        = Column(DateTime, default=datetime.utcnow)   
    

class LogCambio(Base):
    __tablename__   = 'log_cambios'
    id              = Column(Integer, primary_key=True, autoincrement=True)
    producto_id     = Column(Integer)
    producto_nombre = Column(String(200))
    precio_antes    = Column(Float)
    precio_despues  = Column(Float)
    variacion_pct   = Column(Float)
    tasa_usada      = Column(Float)
    aprobado        = Column(Boolean)
    timestamp       = Column(DateTime, default=datetime.utcnow)




    
#* EJECUTA: python -c "from db.database import engine; from sqlalchemy import text; print(engine.connect().execute(text('SELECT 1')).scalar())"
# DEBE RETORNAR 1