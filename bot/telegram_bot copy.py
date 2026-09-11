
#TODO: pip show python-telegram-bot
#? -m → Para usar el pip del Python que ejecutas
# pip install python-telegram-bot || 
# python -m pip install python-telegram-bot
# python -m pip install loguru 

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
_tasa_es_manual: bool = False #? Luego le hacemos toggle para ver el btn
_umbral_actual: float = UMBRAL_VARIACION

#* ─── MENÚ PRINCIPAL ───────────────────────────────────────────────────────────
# InlineKeyboardButton - Genera botones inline 
# callback_data — Identificador de texto que Telegram devuelve cuando el usuario hace clic. 
# Ejemplo: el botón "Ver productos" envía callback_data="menu_ver_productos", que luego se captura en manejar_menu().
def menu_principal_keyboard(): #* Retorna la Grilla botoneta del menu principal.
    botones = [
        [InlineKeyboardButton("📋 Ver productos",       callback_data="menu_ver_productos")],
        [InlineKeyboardButton("✏️ Editar precio",       callback_data="menu_editar_precio")],
        [InlineKeyboardButton("🔄 Forzar consulta BCV", callback_data="menu_forzar_bcv")],
        [InlineKeyboardButton("💱 Tasa manual",         callback_data="menu_tasa_manual")],
        [InlineKeyboardButton("⚙️ Cambiar umbral",      callback_data="menu_umbral")],
        [InlineKeyboardButton("📊 Ver tasa actual",     callback_data="menu_ver_tasa")],
    ]
    #* BTN EXTRA: Mostrar opción de restablecer solo si la tasa es manual
    if _tasa_es_manual: #? la definimos arriba
        botones.append([
            InlineKeyboardButton("↩️ Restablecer tasa BCV", callback_data="menu_restablecer_bcv")
        ])
    return InlineKeyboardMarkup(botones) #* 🎯 InlineKeyboardMarkup - El Constructor de Botones, Grilla botoneta en telegram.


#* ─── COMANDO /START ──────────────────────────────────────────────────────────
# llamada en →  app.add_handler(CommandHandler("start", cmd_start))
# Manejador del comando "/start" — cuando usuario lo envie
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE): #* Manejador del comando "/start"
    # solo envía un texto diciendole al usuario que escriba /menu para llegar al menú 
    await update.message.reply_text(
        "👋 ¡Bienvenido al Bot de Precios USD/VES!\nEscribe /menu para ver las opciones.",
    )
    

#* ─── COMANDO /MENU ────────────────────────────────────────────────────────────
# llamada en →  app.add_handler(CommandHandler("menu", cmd_menu))
# Que se ejecuta cuando el usuario escribe "/menu" en el chat de Telegram.
# Se llama en la configuración del bot cuando: inicia la conversación y para "salida de emergencia"
async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE): #* Manejador del comando "/menu"
    indicador = "⚠️ _Tasa actual: establecida manualmente_\n\n" if _tasa_es_manual else "" #& esta false
    await update.message.reply_text(
        f"🤖 *Bot de Precios USD/VES*\n{indicador}¿Qué deseas hacer?",
        parse_mode="Markdown", # Telegram que interprete *negrita* y _cursiva_.
        reply_markup=menu_principal_keyboard() #& Función de Grilla 6-7 botones del menu y los adjunta al mensaje.
    )


#* ─── ARRANQUE ─────────────────────────────────────────────────────────────────

def iniciar_bot():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
  
    # conv = ConversationHandler(
    #     entry_points=[
    #         CommandHandler("menu", cmd_menu), 
    #         # Si el usuario escribe "/menu" estando "en reposo", arranca el flujo
    #         # CallbackQueryHandler(manejar_menu, pattern="^menu_"),
    #     ],
    #     states={
    #         #ESPERANDO_UMBRAL:      [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_umbral)],
    #         #ESPERANDO_TASA_MANUAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_tasa_manual)],
    #         #ESPERANDO_PRODUCTO_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_producto_id)],
    #         #ESPERANDO_MODO_EDICION:  [CallbackQueryHandler(manejar_edicion, pattern="^editar_")],
    #         #ESPERANDO_VALOR_PRECIO:  [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_precio)],
    #     },
    #     fallbacks=[CommandHandler("menu", cmd_menu)],
    #     # Si el usuario está atascado en medio de otro flujo y escribe "/menu" en vez de responder, esto lo saca de ahí y lo regresa al menú principal.
    #     allow_reentry=True,
    # )

    
    app.add_handler(CommandHandler("start", cmd_start))
    # app.add_handler(conv)
    #app.add_handler(CallbackQueryHandler(manejar_autorizacion))
    app.add_handler(CommandHandler("menu", cmd_menu))
    logger.info("Bot de Telegram iniciado.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)





# #TODO: main.py
# from bot.telegram_bot import iniciar_bot

# if __name__ == "__main__":
#     iniciar_bot()