import os 
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_TOKEN = st.secrets['TELEGRAM_TOKEN']
TELEGRAM_CHAT_ID = int(st.secrets['TELEGRAM_CHAT_ID'])
UMBRAL_VARIACION = float(os.getenv('UMBRAL_VARIACION', '3.0'))
DATABASE_URL = float(os.getenv('DATABASE_URL', 'https://...'))
ML_ACCESS_TOKEN = float(os.getenv('ML_ACCESS_TOKEN', ''))

