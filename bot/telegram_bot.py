
# pip show python-telegram-bot
#? -m → Para usar el pip del Python que ejecutas
# pip install python-telegram-bot || 
# python -m pip install python-telegram-bot
# python -m pip install loguru 

import asyncio
from flask import app
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler
from loguru import logger
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, UMBRAL_VARIACION
# from db.database import actualizar_precios_ves, grardar_log, get_session, obtener_productos, guardar_tasa, obtener_ultima_tasa
from db.database import obtener_productos_activos, actualizar_producto, obtener_producto_por_id



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
#Retornar una grid de los btn, BOTONERA
# esto va a ser la respuesta a "/menu"
def menu_principal_keyboard():
    botones = [
        [InlineKeyboardButton("📦Ver productos", callback_data="menu_ver_productos")],   #R
        [InlineKeyboardButton("✏️Editar precio", callback_data="menu_editar_productos")], # U
        [InlineKeyboardButton("🌀Forzar consulta BCV", callback_data="menu_forzar_bcv")], # R
        [InlineKeyboardButton("💲Tasa manual", callback_data="menu_tasa_manual")], #? U
        [InlineKeyboardButton("💡Cambiar umbral", callback_data="menu_cambiar_umbral")], # U # TODO: greggar menu_
        [InlineKeyboardButton("📊Ver tasa actual", callback_data="menu_ver_tasa")], # R      # TODO: greggar menu_
    ]
    if _tasa_es_manual:
        botones.append([InlineKeyboardButton("Restablecer tasa BCV", callback_data="menu_restablecer_bcv")])
    
    return InlineKeyboardMarkup(botones) #Botoneta contenedor de los BOTONES 

#? con if-else 
#?  callback_data=="menu_ver_productos"→ obtener_productos esta funcion debe retornar los productos de la bbdd
#?  callback_data=="menu_editar_productos"→ actualizar_precios_ves debe modificar/actualizar/editarlos los productos de la bbdd
#?  callback_data=="menu_forzar_bcv"→ obtener_ultima_tasa esta funcion debe retornar los productos de la bbdd
#?  callback_data=="menu_tasa_manual"→ guardar_tasa esta funcion debe guardar la tasa digitada por el usuario.

#* ─── COMANDO /START ──────────────────────────────────────────────────────────
# CommandHandler('start', cdm_start())  
# Esta es la ftuncion manejadora del evento envio "/start" → sale un texto
# es async porque el sistema debe esperar que el usuario escriba '/start' y luego el bot le responde con un mensaje de bienvenida.
async def cdm_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # el bot tiene interaccion con el usuario mediante "Update"
    await update.message.reply_text('👋 ¡Bienvenido al Bot de Precios USD/VES! \nEscribe /menu para ver las opciones.')

#* ─── COMANDO /MENU ────────────────────────────────────────────────────────────
# Esta es la ftuncion manejadora del evento envio "/menu" → salen los botones 
# CommandHandler('/menu', cdm_menu)  
async def cdm_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # if _tasa_es_manual  → se lo dire
    indicador = '⚠️ Tasa actual: establecida manualmente' if _tasa_es_manual else "🏫 Tasa actual: obtenida de BCV"
    await update.message.reply_text(
        f"🤖 *Bot de Precios USD/VES* \n{indicador} \n\n¿Qué deseas hacer?" ,
        parse_mode='Markdown',
        reply_markup=menu_principal_keyboard()
    )
    
#* ─── FLUJO DEL MANEJADOR DE BOTONES ─────────────────────────────────────────────────────
# Usuario presiona "📦Ver productos"
#           ↓
# Telegram envía un "CallbackQuery" al bot, es una notificacion para que sepa que paso este tipo de interaccion
#           ↓
# Se ejecuta manejar_menu(update, context) #TODO: Hay que crearla, para saber q tbn clickeo usuario 🤔⁉️
#           ↓
# update.callback_query  →  info del clic
#           ↓
# query.answer()  →  confirma recepción a Telegram, NECESARIA
#           ↓
# query.data  →  "menu_ver_productos", "menu_editar_productos", ...
#           ↓
# if data == "menu_ver_productos":  →  entra al bloque
#           ↓
# ... muestra los productos

#* ─── FUNC MANEJADORA DEL MENU - BOTONERA ───────
async def maneja_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Confirma la recepción del clic al usuario
    data = query.data
    
    #* ─── MANEJO DEL CLIC SOBRE EL BTN "ver productos" ───────
    if data == "menu_ver_productos":
        productos =  obtener_productos_activos()
        if not productos:
            await query.edit_message_text('No hay productos en la DB que mostrar.') #Modificara el text label del btn, que esta generando el obj "Update"
            return
        lineas = ["📦 Productos activos:"]
        for p in  productos:
            lineas.append(
                f'ID {p.id} — {p.nombre}\n'
                f'💵 USD: {p.precio_usd} $ | 🇻🇪 VES: {p.precio_ves} Bs'
                )
        lineas.append('\nUsa /menu para volver.')
            
        await query.edit_message_text('\n'.join(lineas), parse_mode='Markdown') #Modificara el text label del btn, que esta generando el obj "Update"
    
    #TODO ─── ******************MANEJO DEL CLIC SOBRE EL BTN "ver productos" *******************───────
    if data == "menu_editar_productos":
        # 1. le muestro todos lols productos con su id, para q me indique el id
        # 2. obtengo de usuario el id de usuario, lo guado en una var y se lo paso a la func para obtener el proc que se desea acctualzar
        
        # tengo que conseguir el id, del chat
        producto =  obtener_producto_por_id(id)
        actualizar_producto(2, 200)
    
    
    #* ─── MANEJO DEL CLIC SOBRE CUALQUIER OTRO BOTON ─────── 
    else:  
        await query.edit_message_text(f' ⚠️ `{data}` no ha sido implemantado aun. \nUsa /menu para volver.', parse_mode='Markdown') #Modificara el text label del btn, que esta generando el obj "Update"

        
        
    
#* ─── ARRANQUE ─────────────────────────────────────────────────────────────────
def iniciar_bot():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler('start', cdm_start))
    app.add_handler(CommandHandler('menu', cdm_menu))
    app.add_handler(CallbackQueryHandler (maneja_menu, pattern="^menu_"))  # Maneja los clics en los botones del menú
    
    logger.info('Bot de telegran iniciado. Esperando comandos...')
    app.run_polling(allowed_updates=Update.ALL_TYPES)  # Inicia el bot y espera comandos de los usuarios
    
