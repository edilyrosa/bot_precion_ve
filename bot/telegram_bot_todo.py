
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
#TODO: from db.database import obtener_productos_activos, actualizar_producto, obtener_producto_por_id, 
from db.database import obtener_productos_activos, actualizar_producto, obtener_producto_por_id, guardar_tasa, obtener_ultima_tasa, actualizar_precio_ves
from scraper.bcv import obtener_tasa_bcv   #TODO


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
    global _tasa_es_manual        #TODO ← AGREGAR ESTA LÍNEA
    query = update.callback_query
    await query.answer()  #* Confirma la recepción del clic al usuario
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
    
    #*─── ******************AQUI QUEDAMOS: MANEJO DEL CLIC SOBRE EL BTN "ver productos" *******************───────
    elif data == "menu_editar_productos":
        productos = obtener_productos_activos()
        if not productos:
            await query.edit_message_text('No hay productos en la DB que mostrar para editar.') #Modificara el text label del btn, que esta generando el obj "Update"
            return ConversationHandler.END
        
        lineas = ["Que productos deseas editar? :\n"]
        for p in  productos:
            lineas.append(f'ID {p.id} — {p.nombre}\n')
        lineas.append('\n Escribe el *ID* del producto.')
        await query.edit_message_text('\n'.join(lineas), parse_mode='Markdown')
        return ESPERANDO_PRODUCTO_ID

    
    
#TODO ───
    #* ── Ver tasa actual ────────────────────────────────────────────────────────
    elif data == "menu_ver_tasa":
        tasa   = obtener_ultima_tasa("BCV") #* Get de BBDD
        origen = "⚠️ establecida manualmente" if _tasa_es_manual else "🏦 BCV"
        if tasa:
            await query.edit_message_text( # Modifica el texto del Btn con Uso *negrita* y _cursiva_.
                f"💱 *Tasa actual:* {tasa:,.4f} Bs/USD\n"
                f"Origen: {origen}\n\nUsa /menu para volver.",
                parse_mode="Markdown" #Uso *negrita* y _cursiva_.
            )
        else:
            await query.edit_message_text("No hay tasa registrada aún.") # Modifica el texto del Btn.
        return ConversationHandler.END #* Termina la interacción.

    #* ── Forzar consulta BCV ───────────────────────────────────────────
    elif data == "menu_forzar_bcv":
        await query.edit_message_text("🔄 Consultando tasa BCV...")
        tasa = obtener_tasa_bcv()
        if tasa:
            guardar_tasa("BCV", tasa)
            _tasa_es_manual = False
            await _evaluar_y_proponer(context.bot, tasa)
        else:
            await context.bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text="❌ No se pudo obtener la tasa del BCV. Intenta con 💱 Tasa manual."
            )
        return ConversationHandler.END
    
    
        #* ── Restablecer tasa BCV ──────────────────────────────────────────
    elif data == "menu_restablecer_bcv":
        await query.edit_message_text("🔄 Restableciendo tasa desde el BCV...")
        tasa = obtener_tasa_bcv()
        if tasa:
            guardar_tasa("BCV", tasa)
            _tasa_es_manual = False
            await context.bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=f"✅ Tasa restablecida desde el BCV: *{tasa:,.4f} Bs/USD*\n\nUsa /menu para más opciones.",
                parse_mode="Markdown"
            )
            await _evaluar_y_proponer(context.bot, tasa)
        else:
            await context.bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text="❌ No se pudo conectar al BCV. La tasa manual sigue activa."
            )
        return ConversationHandler.END

 #TODO ───
    
    
    
    #* ─── MANEJO DEL CLIC SOBRE CUALQUIER OTRO BOTON ─────── 
    else:  
        await query.edit_message_text(f' ⚠️ `{data}` no ha sido implemantado aun. \nUsa /menu para volver.', parse_mode='Markdown') #Modificara el text label del btn, que esta generando el obj "Update"


async def recibir_producto_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        prod_id = int(update.message.text.strip()) #* Obteniendo el id digitado por usuario 
        producto = obtener_producto_por_id(prod_id) #* Obteniendo el producto de la BBDD que usuaario quiere EDITAR.
        if not producto:
            await update.message.reply_text('No hay producto en la DB con ese id.') #Modificara el text label del btn, que esta generando el obj "Update"
            return ConversationHandler.END
        #* si hay producto vamos a guarda info en el contexto del bot
        context.user_data['producto_id'] = producto.id # este dato lo vamos y podemos usar en otras funciones.
        context.user_data['producto_nombre'] = producto.nombre # este dato lo vamos y podemos usar en otras funciones.
        teclado = InlineKeyboardMarkup([ # & AGREGAR: [] *********** MATRIZ: [InlineKeyboardButton("💵 Cambiar precio USD",  callback_data="editar_usd")], 
            [InlineKeyboardButton( 'Cambiar precios USD',callback_data='editar_usd')],
            [InlineKeyboardButton( 'Cambiar precios VES',callback_data='editar_ves')],
            [InlineKeyboardButton( 'Cancelar',           callback_data='editar_cancelar')]
        ])
        await update.message.reply_text( #Contestamos con texto + la botonera
            f' *{producto.nombre}*\n'
            f' USD: *{producto.precio_usd}*\n'
            f' VES: *{producto.precio_ves}*\n'
            f' Que precio deseas modificar\n',
            parse_mode='Markdown',
            reply_markup=teclado
        )
        return ESPERANDO_MODO_EDICION # *lo siguiente es manejar la edicion... lo cual depende de si 4es en UDS o VES
    
    except ValueError:
        await update.message.reply_text('Escribe el ID valido del producto que deseas editar.')
        return ConversationHandler.END

async def manejar_edicion(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()  #* Confirma la recepción del clic al usuario
        modo = query.data
        if modo == "editar_cancelar":
            #& SUSTITUTIR POR: ****************************** query.edit_message_text()
            #!await update.message.reply_text('Edicion cancelada.')
            await query.edit_message_text('❌ Edicion cancelada. Usa /menu')
            return ConversationHandler.END
        
        context.user_data['editar_modo'] = modo
        nombre = context.user_data.get('producto_nombre', 'producto')
        if modo == "editar_ves": 
            await query.edit_message_text(
                f'Escribe el  nuevo *Precio en VES* para *{nombre}:*',
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                f'Escribe el  nuevo *Precio en USD* para *{nombre}:*',
                parse_mode='Markdown'
            )
        return ESPERANDO_VALOR_PRECIO # necesito una funcion que controle el esperar el obtener el precion q sera un mesj.text y con el cual hare el UPDATE en la BBDD del producto cuyo id fue pasado. 

async def recibir_precio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        valor = float(update.message.text.strip().replace(',', '.')) #* Obteniendo el valor digitado por usuario para cambiar el precio.
        prod_id = context.user_data.get('producto_id')
        modo = context.user_data.get('editar_modo')
    
        if modo == 'editar_usd':
            actualizar_producto(prod_id, precio_usd=valor)
            await update.message.reply_text(f' USD Actualizado a {valor} $')
            #& AGREGAR: ********************************** return ConversationHandler.END  
            return ConversationHandler.END
        
        #TODO: TERMINEMOS DE ESCRIBIR ESTA FUNCION
        elif modo == 'editar_ves':
            actualizar_producto(prod_id, precio_ves=valor)
            await update.message.reply_text(f' VES Actualizado a {valor} Bs.')
            return ConversationHandler.END
            
        # todo: QUEDAMOS AQUI
    except:
        # todo: QUEDAMOS AQUI
        print('An exception occurred')    
    


#TODO ─── LÓGICA: EVALUAR TASA Y PROPONER AJUSTES ─────────────────────────
async def _evaluar_y_proponer(bot, tasa_nueva: float):
    """
    Calcula propuestas con la tasa dada y las envía a Telegram si superan el umbral.
    Usa _umbral_actual (puede haber sido cambiado desde el menú).
    """
    from engine.price_engine import calcular_propuestas, formatear_mensaje_propuesta

    propuestas = calcular_propuestas(tasa_nueva, umbral=_umbral_actual)
    mensaje    = formatear_mensaje_propuesta(propuestas, tasa_nueva)

    global _propuestas_pendientes
    _propuestas_pendientes = {p["producto_id"]: p for p in propuestas}

    if not propuestas:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID, text=mensaje, parse_mode="Markdown"
        )
        return

    botones = []
    for p in propuestas:
        botones.append([
            InlineKeyboardButton(f"✅ {p['nombre'][:20]}", callback_data=f"ap_{p['producto_id']}"),
            InlineKeyboardButton("❌ Rechazar",             callback_data=f"re_{p['producto_id']}"),
        ])
    botones.append([
        InlineKeyboardButton("✅ Aprobar TODOS",  callback_data="ap_all"),
        InlineKeyboardButton("❌ Rechazar TODOS", callback_data="re_all"),
    ])

    await bot.send_message(
        chat_id=TELEGRAM_CHAT_ID, text=mensaje,
        reply_markup=InlineKeyboardMarkup(botones), parse_mode="Markdown"
    )
    logger.info(f"Propuestas enviadas: {len(propuestas)} productos.")
#! BORAR
#* ─── ARRANQUE ─────────────────────────────────────────────────────────────────
def iniciar_bot():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler('start', cdm_start))

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("menu", cdm_menu),
            CallbackQueryHandler(maneja_menu, pattern="^menu_"),
        ],
        states={
            ESPERANDO_PRODUCTO_ID:  [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_producto_id)],
            ESPERANDO_MODO_EDICION: [CallbackQueryHandler(manejar_edicion, pattern="^editar_")],
            ESPERANDO_VALOR_PRECIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_precio)],
        },
        fallbacks=[CommandHandler("menu", cdm_menu)],
        allow_reentry=True,
    )
    app.add_handler(conv)

    logger.info('Bot de Telegram iniciado.')
    app.run_polling(allowed_updates=Update.ALL_TYPES)