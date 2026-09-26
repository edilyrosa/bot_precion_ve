
#TODO: ESTE CODIGO ESTA CORRECTO Y DEBE SER DESARROLLADO
# import urllib3
# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# import requests
# from bs4 import BeautifulSoup
# from loguru import logger

# BCV_URL = "https://www.bcv.org.ve/"
# HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; PriceBot/1.0)"}


# def obtener_tasa_bcv() -> float | None:
#     """
#     Extrae la tasa oficial USD/VES publicada por el BCV.
#     Retorna el valor como float o None si falla.
#     """
#     try:
#         resp = requests.get(BCV_URL, headers=HEADERS, timeout=15, verify=False)
#         resp.raise_for_status()

#         soup = BeautifulSoup(resp.text, "lxml")

#         # El BCV publica la tasa en el div con id="dolar"
#         dolar_div = soup.find("div", {"id": "dolar"})
#         if not dolar_div:
#             logger.warning("No se encontró el div #dolar en el BCV.")
#             return None

#         tasa_texto = dolar_div.find("strong").text.strip()

#         # Limpiar el texto: "36,50" → 36.50
#         tasa = float(tasa_texto.replace(",", "."))
#         logger.info(f"Tasa BCV obtenida: {tasa} Bs/USD")
#         return tasa

#     except requests.RequestException as e:
#         logger.error(f"Error de conexión con BCV: {e}")
#         return None
#     except (AttributeError, ValueError) as e:
#         logger.error(f"Error al parsear la tasa del BCV: {e}")
#         return None


# def obtener_tasa_paralela() -> float | None:
#     """
#     Consulta la tasa paralela desde la API de exchangerate.host
#     como fuente alternativa cuando el BCV no está disponible.
#     """
#     try:
#         url = "https://api.exchangerate.host/latest?base=USD&symbols=VES"
#         resp = requests.get(url, timeout=10)
#         data = resp.json()
#         tasa = data["rates"]["VES"]
#         logger.info(f"Tasa paralela obtenida: {tasa} Bs/USD")
#         return round(tasa, 2)
#     except Exception as e:
#         logger.error(f"Error al obtener tasa paralela: {e}")
#         return None
