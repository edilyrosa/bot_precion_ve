
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

#TODO from db.database import obtener_productos_activos
from db.database import obtener_productos_activos,   obtener_producto_por_id, actualizar_producto

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
        [InlineKeyboardButton("💡Cambiar umbral", callback_data="cambiar_umbral")], # U # TODO: greggar menu_
        [InlineKeyboardButton("📊Ver tasa actual", callback_data="ver_tasa")], # R      # TODO: greggar menu_
    ]
    if _tasa_es_manual:
        botones.append([InlineKeyboardButton("Restablecer tasa BCV", callback_data="restablecer_bcv")])
    
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
    

# TODO *********************************************************************
#* ─── FLUJO DEL MANEJADOR DE BOTONES ─────────────────────────────────────────────────────
# Usuario presiona "📦Ver productos"
#           ↓
# Telegram envía un "CallbackQuery" al bot
#           ↓
# Se ejecuta manejar_menu(update, context) #TODO: Hay que crearla, para finalmente saber q tbn clickeo usuario 🤔⁉️
#           ↓
# update.callback_query  →  info del clic
#           ↓
# query.answer()  →  confirma recepción a Telegram
#           ↓
# query.data  →  "menu_ver_productos", "menu_editar_productos", ...
#           ↓
# if data == "menu_ver_productos":  →  entra al bloque
#           ↓
# ... muestra los productos
#* ─── MANEJADOR DE BOTONES ─────────────────────────────────────────────────────
# app.add_handler(CallbackQueryHandler(manejar_menu, pattern="^menu_"))  # TODO ← AGREGARLO EN APP
async def manejar_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 💡Cuando el usuario escribe → update.message
    query = update.callback_query
    #? Cuando el usuario presiona un botón, la info viene → update.callback_query → quién lo hizo, qué botón, en qué mensaje...
    await query.answer() # Le dice a Telegram: "recibí el clic", confimacion para no quedar colgado.
    data = query.data    # Aquí viene el callback_data que definiste al crear el botón → "menu_ver_productos"
    # empezamos a unsar a data, como 🏳️ para saber que btn esta clickeando usuario
    
    #* ── Ver productos ──────────────────────────────────────────────
    #? [InlineKeyboardButton("📦Ver productos", callback_data="menu_ver_productos")],   #R
    if data == "menu_ver_productos":
        productos = obtener_productos_activos() #La hicimos en db/database.py, retorna una lista de objetos Producto activos (activo=True) y ordenados por id ascendente.
        if not productos:
            await query.edit_message_text("No hay productos registrados.") #?💡Voy a contestar el clic modificando el texto del btn
            return
        #? edit_message_text vs reply_text vs send_message
        # query.edit_message_text(...)	    Edita el mensaje del botón, usado en: manejar_menu (respuesta a clic)
        # update.message.reply_text(...)	Responde al mensaje del usuario, usado en: cmd_menu, recibir_precio
        # context.bot.send_message(...)	    Envía un mensaje nuevo.	Para notificaciones fuera del flujo

        lineas = ["📦 *Productos activos:*\n"] #? Var con todo el texto del btn
        for p in productos:
            lineas.append(
                f"ID `{p.id}` — {p.nombre}\n"
                f"   💵 USD: {p.precio_usd}  |  🇻🇪 VES: {p.precio_ves:,.0f} Bs"
            )
        lineas.append("\nUsa /menu para volver.")
        await query.edit_message_text("\n".join(lineas), parse_mode="Markdown")

    
        #TODO ── Editar precio ──────────────────────────────────────────────
    elif data == "menu_editar_productos":
        productos = obtener_productos_activos()
        if not productos:
            await query.edit_message_text("No hay productos registrados.")
            return ConversationHandler.END

        lineas = ["✏️ *¿Qué producto deseas editar?*\n"]
        for p in productos:
            lineas.append(f"ID `{p.id}` — {p.nombre}")
        lineas.append("\nEscribe el *ID* del producto:")

        await query.edit_message_text("\n".join(lineas), parse_mode="Markdown")
        return ESPERANDO_PRODUCTO_ID
    
    
    
    #* ── Otros botones: aún no implementados ────────────────────────
    else:
        await query.edit_message_text(
            f"⚠️ `{data}` aún no implementado.\n\nUsa /menu para volver.",
            parse_mode="Markdown"
        )
# TODO

#TODO ─── RECIBIR ID DEL PRODUCTO ────────────────────────────────
async def recibir_producto_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        prod_id = int(update.message.text.strip())
        producto = obtener_producto_por_id(prod_id)
        if not producto:
            await update.message.reply_text("❌ ID no encontrado. Usa /menu.")
            return ConversationHandler.END

        # Guardar en memoria del contexto
        context.user_data["producto_id"]     = producto.id
        context.user_data["producto_nombre"] = producto.nombre

        # Submenú USD / VES / Cancelar
        teclado = InlineKeyboardMarkup([
            [InlineKeyboardButton("💵 Cambiar precio USD",  callback_data="editar_usd")],
            [InlineKeyboardButton("🇻🇪 Cambiar precio VES", callback_data="editar_ves")],
            [InlineKeyboardButton("❌ Cancelar",            callback_data="editar_cancelar")],
        ])
        await update.message.reply_text(
            f"📦 *{producto.nombre}*\n"
            f"   💵 USD: {producto.precio_usd}\n"
            f"   🇻🇪 VES: {producto.precio_ves:,.0f} Bs\n\n"
            f"¿Qué deseas modificar?",
            parse_mode="Markdown",
            reply_markup=teclado
        )
        return ESPERANDO_MODO_EDICION

    except ValueError:
        await update.message.reply_text("❌ Escribe solo el número del ID.")
        return ConversationHandler.END

#* ─── RECIBIR MODO DE EDICIÓN (USD / VES / CANCELAR) ──────────────────────────
async def manejar_edicion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    modo = query.data

    if modo == "editar_cancelar":
        await query.edit_message_text("❌ Edición cancelada. Usa /menu.")
        return ConversationHandler.END

    context.user_data["editar_modo"] = modo   # "editar_usd" o "editar_ves"
    nombre = context.user_data.get("producto_nombre", "producto")

    if modo == "editar_ves":
        await query.edit_message_text(
            f"🇻🇪 Escribe el nuevo *precio en Bs* para *{nombre}*:",
            parse_mode="Markdown"
        )
    else:
        await query.edit_message_text(
            f"💵 Escribe el nuevo *precio en USD* para *{nombre}*:",
            parse_mode="Markdown"
        )
    return ESPERANDO_VALOR_PRECIO

#* ─── RECIBIR PRECIO Y ACTUALIZAR ─────────────────────────────────────────────
async def recibir_precio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        valor  = float(update.message.text.strip().replace(",", "."))
        prod_id = context.user_data.get("producto_id")
        modo    = context.user_data.get("editar_modo")

        if modo == "editar_usd":
            actualizar_producto(prod_id, precio_usd=valor)
            await update.message.reply_text(f"✅ USD actualizado a {valor}")
        elif modo == "editar_ves":
            actualizar_producto(prod_id, precio_ves=valor)
            await update.message.reply_text(f"✅ VES actualizado a {valor:,.0f} Bs")

        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ Escribe un número válido.")
        return ESPERANDO_VALOR_PRECIO
# TODO   
#* ─── ARRANQUE ─────────────────────────────────────────────────────────────────
def iniciar_bot():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler('start', cdm_start))
    app.add_handler(CommandHandler('menu', cdm_menu))
    
    
    #TODO: SUSTITUIMOS.. app.add_handler(CallbackQueryHandler(manejar_menu, pattern="^menu_"))  # TODO ← AGREGAR ESTA LÍNEA
    
    conv = ConversationHandler(
        entry_points=[
                CommandHandler("menu", cdm_menu),
                CallbackQueryHandler(manejar_menu, pattern="^menu_"),
            ],
            states={
                ESPERANDO_PRODUCTO_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_producto_id)],
                ESPERANDO_MODO_EDICION: [CallbackQueryHandler(manejar_edicion, pattern="^editar_")],  
                ESPERANDO_VALOR_PRECIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_precio)],

            },
            fallbacks=[CommandHandler("menu", cdm_menu)],
            allow_reentry=True,
    )
    app.add_handler(conv)
    
    
    logger.info('Bot de telegran iniciado. Esperando comandos...')
    app.run_polling(allowed_updates=Update.ALL_TYPES)  # Inicia el bot y espera comandos de los usuarios
    
