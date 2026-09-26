
# #TODO: ESTE CODIGO ESTA CORRECTO Y DEBE SER DESARROLLADO
# from loguru import logger
# from config import UMBRAL_VARIACION
# from db.database import obtener_productos_activos


# def redondear_precio(precio: float) -> float:
#     """
#     Redondea el precio a la centena más cercana.
#     Ej: 18_432 → 18_400  |  18_567 → 18_600
#     Ajusta esta lógica según la política de precios del negocio.
#     """
#     return round(precio / 100) * 100


# def calcular_propuestas(tasa_nueva: float, umbral: float = UMBRAL_VARIACION) -> list[dict]:
#     """
#     Calcula los nuevos precios sugeridos para todos los productos activos.
#     Solo incluye los productos cuya variación supera `umbral` (en %).

#     El parámetro `umbral` es opcional: si no se pasa, usa el valor fijo de
#     config.py (.env). Esto permite que el bot de Telegram le pase el umbral
#     que el usuario cambió en tiempo real desde el menú, sin romper a otros
#     lugares del proyecto (como el scheduler) que sigan llamando a esta
#     función sin ese argumento.

#     Retorna una lista de dicts con la propuesta de cada producto.
#     """
#     from db.database import obtener_productos_activos
#     productos = obtener_productos_activos()
#     propuestas = []

#     for producto in productos:
#         precio_nuevo_raw = producto.precio_usd * tasa_nueva
#         precio_nuevo     = redondear_precio(precio_nuevo_raw)
#         precio_actual    = producto.precio_ves

#         # Si el precio actual es 0 (producto nuevo), siempre se incluye
#         if precio_actual == 0:
#             variacion_pct = 100.0
#         else:
#             variacion_pct = abs((precio_nuevo - precio_actual) / precio_actual * 100)

#         if variacion_pct >= umbral:
#             propuestas.append({
#                 "producto_id":    producto.id,
#                 "nombre":         producto.nombre,
#                 "precio_usd":     producto.precio_usd,
#                 "precio_actual":  precio_actual,
#                 "precio_nuevo":   precio_nuevo,
#                 "variacion_pct":  round(variacion_pct, 1),
#                 "tasa":           tasa_nueva,
#             })
#             logger.debug(
#                 f"{producto.nombre}: {precio_actual} → {precio_nuevo} Bs "
#                 f"({variacion_pct:.1f}% de variación)"
#             )

#     logger.info(
#         f"Propuestas generadas: {len(propuestas)} de {len(productos)} productos "
#         f"(umbral usado: {umbral}%)."
#     )
#     return propuestas


# def formatear_mensaje_propuesta(propuestas: list[dict], tasa: float) -> str:
#     """
#     Genera el texto del mensaje de Telegram con el resumen de propuestas.
#     Incluye comparativa con MercadoLibre si está disponible.
#     """
#     if not propuestas:
#         return f"Tasa BCV hoy: {tasa:.2f} Bs/USD\n\nNingún producto supera el umbral de variación. No se requieren ajustes."

#     lineas = [
#         f"💵 Tasa BCV: {tasa:.2f} Bs/USD",
#         f"📦 Productos a ajustar: {len(propuestas)}",
#         "",
#     ]

#     for p in propuestas:
#         flecha = "▲" if p["precio_nuevo"] > p["precio_actual"] else "▼"
#         lineas.append(
#             f"{flecha} {p['nombre']}\n"
#             f"   {p['precio_actual']:,.0f} → {p['precio_nuevo']:,.0f} Bs  "
#             f"({p['variacion_pct']}%)"
#         )

#         # Agregar info de MercadoLibre si está disponible
#         ml_estado = p.get("ml_estado", "sin_datos")
#         precio_ml = p.get("precio_ml")

#         if ml_estado == "sin_datos" or not precio_ml:
#             lineas.append("   🔍 ML: sin datos de competencia")
#         elif ml_estado == "caro":
#             lineas.append(
#                 f"   ⚠️ ML: {precio_ml:,.0f} Bs  "
#                 f"(estás {abs(p['ml_diferencia']):.1f}% más CARO que ML)"
#             )
#         elif ml_estado == "barato":
#             lineas.append(
#                 f"   💚 ML: {precio_ml:,.0f} Bs  "
#                 f"(estás {abs(p['ml_diferencia']):.1f}% más BARATO que ML)"
#             )
#         else:
#             lineas.append(
#                 f"   ✅ ML: {precio_ml:,.0f} Bs  (precio competitivo)"
#             )

#         lineas.append("")  # línea en blanco entre productos

#     return "\n".join(lineas)