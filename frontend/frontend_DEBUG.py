"""
FoodLooker - Frontend con Chat Conversacional (v2.1)
Diseñado para interactuar con el agente de reservas híbrido via FastAPI
"""
import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

import streamlit as st
from typing import Dict, List, Any, Optional
import base64
from datetime import datetime, time as dt_time

from frontend_api_helpers import (
    search_restaurants_via_agent,
    process_agent_response_for_ui,
    continue_agent_conversation
)

# ==========================================
# CONFIGURACIÓN
# ==========================================
API_BASE_URL = "http://localhost:8000"
API_KEY = "demo-api-key"

st.set_page_config(
    layout="wide", 
    page_title="FoodLooker", 
    page_icon="🍽️",
    initial_sidebar_state="collapsed"
)

# ==========================================
# COLORES Y CSS (Se mantiene tu diseño original)
# ==========================================
COLOR_BG = "#F9F4E6"
COLOR_PRIMARY = "#E07A5F"
COLOR_PRIMARY_DARK = "#D66A4F"
COLOR_TEXT_DARK = "#3D3D3D"

def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        return None

logo_b64 = get_base64_image("logo.jpeg")

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'Poppins', sans-serif; }}
    .stApp {{ background-color: {COLOR_BG}; }}
    .header-box {{
        background-color: {COLOR_PRIMARY};
        padding: 12px 25px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }}
    .header-title {{ color: white; font-size: 2.2rem; font-weight: 700; margin: 0; }}
    .header-logo {{ width: 55px; height: 55px; border-radius: 50%; object-fit: cover; border: 2px solid white; }}
    div.stButton > button {{
        background-color: {COLOR_PRIMARY} !important;
        color: white !important;
        border-radius: 25px !important;
        border: none !important;
        padding: 10px 25px !important;
        font-weight: 600 !important;
    }}
    .restaurant-card {{ background-color: #EFEDE6; padding: 15px 18px; border-radius: 12px; margin-bottom: 10px; }}
    .card-name {{ font-size: 1.1rem; font-weight: 700; color: #5A4A42; }}
    .card-info {{ color: #666; font-size: 0.9rem; margin-top: 5px; }}
</style>
""", unsafe_allow_html=True)


# ==========================================
# INICIALIZACIÓN DEL ESTADO
# ==========================================
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'agent_session_id' not in st.session_state:
    st.session_state.agent_session_id = None

if 'restaurants' not in st.session_state:
    st.session_state.restaurants = []

if 'show_results' not in st.session_state:
    st.session_state.show_results = False

if 'preferences' not in st.session_state:
    st.session_state.preferences = {
        'filters_enabled': False, # Flag para saber si aplicar o no los filtros
        'location': '',
        'party_size': 2,
        'use_specific_time': False,
        'selected_date': datetime.now(),
        'selected_time': dt_time(21, 0),
        'mins_to_wait': 45,
        'travel_mode': 'walking',
        'max_distance': 15.0,
        'price_level': 2,
        'extras': ''
    }


# ==========================================
# FUNCIONES DE LÓGICA
# ==========================================
def add_message(role: str, content: str):
    st.session_state.messages.append({
        'role': role,
        'content': content,
        'timestamp': datetime.now().strftime('%H:%M')
    })

def clear_chat():
    st.session_state.messages = []
    st.session_state.agent_session_id = None
    st.session_state.restaurants = []
    st.session_state.show_results = False

def process_user_input(user_input: str):
    if not user_input.strip():
        return
    
    add_message('user', user_input)
    prefs = st.session_state.preferences
    conversation_history = st.session_state.messages[:-1] if len(st.session_state.messages) > 1 else []
    
    # Lógica de filtrado dinámico:
    # Si 'filters_enabled' es False, enviamos None para que el Agente use el texto del chat.
    if not prefs['filters_enabled']:
        response = search_restaurants_via_agent(
            user_query=user_input,
            conversation_history=conversation_history,
            session_id=st.session_state.agent_session_id,
            location=None, party_size=None, selected_date=None, 
            selected_time=None, mins=None, travel_mode=None, 
            max_distance=None, price_level=None, extras=None
        )
    else:
        # Si están habilitados, preparamos los datos del formulario
        selected_date = prefs['selected_date'] if prefs['use_specific_time'] else None
        selected_time = prefs['selected_time'] if prefs['use_specific_time'] else None
        mins = prefs['mins_to_wait'] if not prefs['use_specific_time'] else None
        
        response = search_restaurants_via_agent(
            user_query=user_input,
            location=prefs['location'],
            party_size=prefs['party_size'],
            selected_date=selected_date,
            selected_time=selected_time,
            mins=mins,
            travel_mode=prefs['travel_mode'],
            max_distance=prefs['max_distance'],
            price_level=prefs['price_level'],
            extras=prefs['extras'],
            conversation_history=conversation_history,
            session_id=st.session_state.agent_session_id
        )
    
    handle_agent_response(response)

def handle_agent_response(response: Dict[str, Any]):
    status = response.get('status', 'failed')
    if status == 'success':
        st.session_state.agent_session_id = response.get('session_id')
        restaurants = process_agent_response_for_ui(response)
        if restaurants:
            st.session_state.restaurants = restaurants
            st.session_state.show_results = True
            add_message('agent', response.get('message', '¡He encontrado estos restaurantes!'))
        else:
            add_message('agent', response.get('message', 'No encontré nada con esos criterios.'))
    elif status == 'needs_input':
        st.session_state.agent_session_id = response.get('session_id')
        add_message('agent', response.get('question', '¿Puedes darme más detalles?'))
    else:
        add_message('agent', f"⚠️ {response.get('message', 'Error en la solicitud.')}")


# ==========================================
# UI - HEADER
# ==========================================
img_html = f'<img src="data:image/jpeg;base64,{logo_b64}" class="header-logo">' if logo_b64 else '🍽️'
st.markdown(f'<div class="header-box">{img_html}<h1 class="header-title">FoodLooker</h1></div>', unsafe_allow_html=True)


# ==========================================
# LAYOUT PRINCIPAL
# ==========================================
col_chat, col_options = st.columns([2, 1])

with col_chat:
    chat_container = st.container(height=500)
    with chat_container:
        if not st.session_state.messages:
            st.markdown('<div style="background-color:#E07A5F;color:white;padding:15px;border-radius:12px;">¡Hola! Soy tu asistente de reservas 👋 Cuéntame qué buscas...</div>', unsafe_allow_html=True)
        
        for msg in st.session_state.messages:
            align = "flex-end" if msg['role'] == 'user' else "flex-start"
            bg = "#E8E4DD" if msg['role'] == 'user' else "#E07A5F"
            color = "#3D3D3D" if msg['role'] == 'user' else "white"
            st.markdown(f"""
                <div style="display: flex; justify-content: {align}; margin-bottom: 10px;">
                    <div style="background:{bg}; color:{color}; padding:10px 15px; border-radius:15px; max-width:80%;">
                        {msg['content']}
                    </div>
                </div>
            """, unsafe_allow_html=True)

    with st.form(key="chat_form", clear_on_submit=True):
        c1, c2 = st.columns([5, 1])
        user_input = c1.text_input("Msg", placeholder="Busco un italiano...", label_visibility="collapsed")
        if c2.form_submit_button("Enviar") and user_input:
            process_user_input(user_input)
            st.rerun()

with col_options:
    if st.session_state.show_results and st.session_state.restaurants:
        st.markdown("### 🏆 Top Restaurantes")
        for idx, res in enumerate(st.session_state.restaurants):
            st.markdown(f"""<div class="restaurant-card"><div class="card-name">{res.get('name')}</div>
                <div class="card-info">📍 {res.get('area')} • ⭐ {res.get('rating')}</div></div>""", unsafe_allow_html=True)
            if st.button(f"Reservar en {res.get('name')[:15]}...", key=f"res_{idx}"):
                add_message('user', f"Reservar en {res.get('name')}")
                st.rerun()
        st.divider()

    # --- SECCIÓN DE FILTROS ---
    with st.expander("⚙️ Opciones avanzadas", expanded=False):
        # El interruptor que determina si se usan estos valores
        enabled = st.toggle("Aplicar estos filtros", value=st.session_state.preferences['filters_enabled'])
        st.session_state.preferences['filters_enabled'] = enabled
        
        # Variable para deshabilitar visualmente los inputs si el toggle está apagado
        dis = not enabled
        
        st.markdown("**📍 Ubicación**")
        st.session_state.preferences['location'] = st.text_input("L", value=st.session_state.preferences['location'], label_visibility="collapsed", disabled=dis, key="f_loc")
        
        st.markdown("**👥 Personas**")
        st.session_state.preferences['party_size'] = st.number_input("P", 1, 20, st.session_state.preferences['party_size'], disabled=dis, key="f_party")
        
        st.markdown("**🕒 ¿Cuándo?**")
        use_spec = st.checkbox("Fecha específica", value=st.session_state.preferences['use_specific_time'], disabled=dis)
        st.session_state.preferences['use_specific_time'] = use_spec
        
        if use_spec:
            st.session_state.preferences['selected_date'] = st.date_input("D", value=st.session_state.preferences['selected_date'], disabled=dis)
            st.session_state.preferences['selected_time'] = st.time_input("T", value=st.session_state.preferences['selected_time'], disabled=dis)
        else:
            st.session_state.preferences['mins_to_wait'] = st.slider("Minutos de espera", 10, 120, st.session_state.preferences['mins_to_wait'], disabled=dis)

        st.markdown("**🚶 Transporte**")
        t_modes = {"Caminando": "walking", "Bus/Metro": "transit", "Coche": "driving"}
        mode_label = st.selectbox("M", list(t_modes.keys()), disabled=dis)
        st.session_state.preferences['travel_mode'] = t_modes[mode_label]

        st.markdown("**💰 Precio máximo**")
        p_levels = {"€": 1, "€€": 2, "€€€": 3, "€€€€": 4}
        p_label = st.select_slider("Pr", options=list(p_levels.keys()), value="€€", disabled=dis)
        st.session_state.preferences['price_level'] = p_levels[p_label]

        st.markdown("**✨ Extras**")
        st.session_state.preferences['extras'] = st.text_input("E", placeholder="Terraza, vegano...", disabled=dis)

    if st.button("🔄 Nueva conversación", use_container_width=True):
        clear_chat()
        st.rerun()