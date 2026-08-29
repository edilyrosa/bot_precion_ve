import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler
from loguru import logger
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, UMBRAL_VARIACION
from db.database import actualizar_precios_ves, grardar_log, get_session, obtener_productos, guardar_tasa, obtener_ultima_tasa

#* ----------ESTADOS -------------------------------------
ESPERANDO_UMBRAL              = 1
ESPERANDO_TASA_MANUAL         = 2
ESPERANDO_PRODUCTO_ID         = 3
ESPERANDO_MODO_EDICION        = 4
ESPERANDO_VALOR_PRECIO        = 5
_propuestas_pendientes: dict[int, dict] =  {}
_tasa_es_manual: bool = False
_umbral_actual: float = UMBRAL_VARIACION
