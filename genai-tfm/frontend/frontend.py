"""
FoodLooker - Frontend con Chat Conversacional (v2)
Diseñado para interactuar con el agente de reservas híbrido via FastAPI

CORREGIDO: Eliminada duplicación de mensajes en el historial
"""

import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

import streamlit as st
from typing import Dict, List, Any, Optional
import base64
from datetime import datetime, time as dt_time
import html as html_module

from frontend.frontend_api_helpers import (
    search_restaurants_via_agent,
    process_agent_response_for_ui,
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
    initial_sidebar_state="collapsed",
)

# ==========================================
# COLORES
# ==========================================
COLOR_BG = "#F9F4E6"
COLOR_PRIMARY = "#E07A5F"
COLOR_PRIMARY_DARK = "#D66A4F"
COLOR_TEXT_DARK = "#3D3D3D"
COLOR_USER_BG = "#E8E4DD"
COLOR_AGENT_BG = "#E07A5F"
COLOR_GRAY = "#7D7D7D"


# Logo
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        return None


logo_b64 = get_base64_image(str(Path(__file__).parent / "logo.png"))

# ==========================================
# CSS GLOBAL
# ==========================================
st.markdown(
    f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Poppins', sans-serif;
    }}
    
    .stApp {{
        background-color: {COLOR_BG};
    }}

    /* Header - Simplified with logo */
    .header-box {{
        padding: 20px 0;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 20px;
        border-bottom: 3px solid {COLOR_PRIMARY};
    }}
    .header-logo {{
        height: 120px;
        width: auto;
        object-fit: contain;
    }}

    /* Botones */
    div.stButton > button,
    button[kind="primaryFormSubmit"] {{
        background-color: {COLOR_PRIMARY} !important;
        color: white !important;
        border-radius: 25px !important;
        border: none !important;
        padding: 10px 25px !important;
        font-weight: 600 !important;
    }}
    
    div.stButton > button:hover,
    button[kind="primaryFormSubmit"]:hover {{
        background-color: {COLOR_PRIMARY_DARK} !important;
    }}

    /* Inputs */
    div[data-baseweb="input"] > div {{
        background-color: white !important;
        border-radius: 10px !important;
        border: 1px solid #ddd !important;
    }}
    
    div[data-baseweb="input"] input {{
        color: {COLOR_TEXT_DARK} !important;
    }}
    
    input::placeholder {{
        color: #888 !important;
    }}

    /* Expander */
    details {{
        background-color: white !important;
        border-radius: 10px !important;
        border: 1px solid #ddd !important;
    }}
    
    details summary {{
        font-weight: 600 !important;
        color: {COLOR_TEXT_DARK} !important;
    }}

    /* Título sección restaurantes */
    .restaurants-title {{
        color: {COLOR_PRIMARY};
        font-size: 1.1rem;
        font-weight: 700;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 2px solid {COLOR_PRIMARY};
        text-align: center;
    }}

    /* Contenedor scrollable para tarjetas - independiente del scroll de la página */
    .restaurants-scroll-container {{
        max-height: 65vh !important;
        overflow-y: auto !important;
        overflow-x: hidden !important;
        padding: 10px 6px 10px 0 !important;
        margin: 0 auto 15px auto !important;
        position: relative !important;
        display: block !important;
    }}

    /* Scrollbar personalizado */
    .restaurants-scroll-container::-webkit-scrollbar {{
        width: 6px;
    }}

    .restaurants-scroll-container::-webkit-scrollbar-track {{
        background: #f1f1f1;
        border-radius: 10px;
    }}

    .restaurants-scroll-container::-webkit-scrollbar-thumb {{
        background: {COLOR_PRIMARY};
        border-radius: 10px;
    }}

    .restaurants-scroll-container::-webkit-scrollbar-thumb:hover {{
        background: {COLOR_PRIMARY_DARK};
    }}

    /* Tarjetas restaurantes más compactas y estrechas */
    .restaurant-card {{
        background-color: white;
        border-radius: 10px;
        margin: 0 auto 12px auto;
        overflow: hidden;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        transition: transform 0.2s, box-shadow 0.2s;
        max-width: 280px;
        width: 100%;
    }}

    .restaurant-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 3px 10px rgba(0,0,0,0.12);
    }}

    .card-photo {{
        width: 100%;
        height: 160px;
        object-fit: cover;
        background-color: #f0f0f0;
        display: block;
    }}

    .card-content {{
        padding: 10px 12px;
    }}

    .card-name {{
        font-size: 0.9rem;
        font-weight: 700;
        color: #2D2D2D;
        margin-bottom: 4px;
        line-height: 1.2;
    }}

    .card-rating {{
        color: #FF9800;
        font-size: 0.75rem;
        margin-bottom: 5px;
    }}

    .card-info {{
        color: #666;
        font-size: 0.72rem;
        line-height: 1.4;
        margin-bottom: 3px;
    }}

    .card-info-label {{
        font-weight: 600;
        color: #444;
    }}

    .card-status {{
        display: inline-block;
        padding: 3px 8px;
        border-radius: 10px;
        font-size: 0.7rem;
        font-weight: 600;
        margin-top: 6px;
    }}

    .status-available {{
        background-color: #E8F5E9;
        color: #2E7D32;
    }}

    .status-call {{
        background-color: #E3F2FD;
        color: #1976D2;
    }}

    /* Botón nueva conversación */
    .btn-new-conversation {{
        background-color: {COLOR_GRAY} !important;
        color: white !important;
        border-radius: 25px !important;
        padding: 8px 20px !important;
        font-weight: 600 !important;
        border: none !important;
        margin-top: 10px !important;
    }}

    .btn-new-conversation:hover {{
        background-color: #6D6D6D !important;
    }}

    /* Ocultar elementos por defecto */
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
    
    /* Fix checkbox text */
    div[data-testid="stCheckbox"] label p {{
        color: {COLOR_TEXT_DARK} !important;
    }}
    
    /* Sliders */
    div[data-testid="stSlider"] label p {{
        color: {COLOR_TEXT_DARK} !important;
    }}

</style>
""",
    unsafe_allow_html=True,
)


# ==========================================
# INICIALIZACIÓN DEL ESTADO
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent_session_id" not in st.session_state:
    st.session_state.agent_session_id = None

if "restaurants" not in st.session_state:
    st.session_state.restaurants = []

if "show_results" not in st.session_state:
    st.session_state.show_results = False

if "processing" not in st.session_state:
    st.session_state.processing = False

if "preferences" not in st.session_state:
    st.session_state.preferences = {
        "location": "",
        "party_size": 2,
        "use_specific_time": False,
        "selected_date": None,
        "selected_time": None,
        "mins_to_wait": 45,
        "travel_mode": "walking",
        "max_distance": 15.0,
        "price_level": 2,
        "extras": "",
    }


# ==========================================
# FUNCIONES DE CHAT
# ==========================================
def add_message(role: str, content: str):
    """Añade un mensaje al historial, evitando duplicados consecutivos."""
    # Evitar duplicados consecutivos
    if st.session_state.messages:
        last_msg = st.session_state.messages[-1]
        if last_msg["role"] == role and last_msg["content"] == content:
            return  # No añadir duplicado

    st.session_state.messages.append(
        {
            "role": role,
            "content": content,
            "timestamp": datetime.now().strftime("%H:%M"),
        }
    )


def clear_chat():
    """Limpia el chat y resetea el estado."""
    st.session_state.messages = []
    st.session_state.agent_session_id = None
    st.session_state.restaurants = []
    st.session_state.show_results = False
    st.session_state.processing = False


def process_user_input(user_input: str):
    """
    Procesa el input del usuario.

    CORREGIDO:
    - Añade mensaje al historial local
    - Envía historial COMPLETO al backend (incluyendo el mensaje actual)
    - El helper NO vuelve a añadir el mensaje
    """
    if not user_input.strip():
        return

    if st.session_state.processing:
        return

    st.session_state.processing = True

    # Añadir mensaje del usuario al historial local
    add_message("user", user_input)

    prefs = st.session_state.preferences

    # Preparar fecha/hora
    selected_date = None
    selected_time = None
    mins = None

    if prefs.get("use_specific_time"):
        selected_date = prefs.get("selected_date")
        selected_time = prefs.get("selected_time")
    else:
        mins = prefs.get("mins_to_wait", 45)

    # Preparar historial para el backend
    # Convertir al formato que espera el backend (sin timestamp)
    messages_for_backend = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in st.session_state.messages
    ]

    # Enviar al backend con historial COMPLETO (con spinner visual)
    with st.spinner("🤖 El agente está procesando tu solicitud..."):
        response = search_restaurants_via_agent(
            messages=messages_for_backend,  # ← Historial completo
            location=prefs.get("location", ""),
            party_size=prefs.get("party_size", 2),
            selected_date=selected_date,
            selected_time=selected_time,
            mins=mins,
            travel_mode=prefs.get("travel_mode", "walking"),
            max_distance=prefs.get("max_distance", 15.0),
            price_level=prefs.get("price_level", 2),
            extras=prefs.get("extras", ""),
            session_id=st.session_state.agent_session_id,
        )

    handle_agent_response(response)
    st.session_state.processing = False


def handle_agent_response(response: Dict[str, Any]):
    """Maneja la respuesta del agente."""
    status = response.get("status", "failed")

    # Guardar session_id
    if "session_id" in response:
        st.session_state.agent_session_id = response["session_id"]

    if status == "success":
        restaurants = process_agent_response_for_ui(response)

        if restaurants:
            st.session_state.restaurants = restaurants
            st.session_state.show_results = True

        agent_msg = response.get(
            "message", "¡He encontrado estos restaurantes para ti!"
        )
        add_message("assistant", agent_msg)

    elif status == "needs_input":
        question = response.get(
            "question", response.get("message", "¿Podrías darme más detalles?")
        )
        add_message("assistant", question)

    elif status == "completed":
        agent_msg = response.get("message", "¡Reserva completada!")
        add_message("assistant", agent_msg)

    elif status == "failed":
        error_msg = response.get("message", "Hubo un problema procesando tu solicitud.")
        add_message("assistant", f"⚠️ {error_msg}")

    else:
        # Para cualquier otro status, mostrar el mensaje
        agent_msg = response.get("message", "Procesando...")
        add_message("assistant", agent_msg)


# ==========================================
# HEADER
# ==========================================
img_html = (
    f'<img src="data:image/png;base64,{logo_b64}" class="header-logo">'
    if logo_b64
    else '<h1 style="color: #E07A5F; margin: 0;">🍽️ FoodLooker</h1>'
)
st.markdown(
    f"""
    <div class="header-box">
        {img_html}
    </div>
""",
    unsafe_allow_html=True,
)


# ==========================================
# LAYOUT PRINCIPAL
# ==========================================
# Cambio: Chat ahora ocupa 70% del ancho en lugar de 25%
col_chat, col_options = st.columns([7, 3])

# ==========================================
# COLUMNA IZQUIERDA: CHAT
# ==========================================
with col_chat:

    # Contenedor del chat con altura aumentada
    chat_container = st.container(height=600)

    with chat_container:
        # Mensaje de bienvenida si no hay mensajes
        if not st.session_state.messages:
            st.markdown(
                """
            <div style="
                background-color: #E07A5F;
                color: white;
                padding: 15px 20px;
                border-radius: 18px;
                border-bottom-left-radius: 4px;
                max-width: 85%;
                margin-bottom: 10px;
                font-size: 0.95rem;
                line-height: 1.6;
            ">
                <strong>¡Hola! Soy tu asistente de reservas 👋</strong><br><br>
                Cuéntame qué tipo de restaurante buscas y me encargo de encontrar las mejores opciones y reservar.<br><br>
                <em style="opacity: 0.9;">💡 Ejemplo: "Busco un japonés para 4 personas esta noche cerca de la Gran Vía de Madrid"</em>
            </div>
            """,
                unsafe_allow_html=True,
            )

        # Renderizar mensajes
        for msg in st.session_state.messages:
            role = msg["role"]
            content = msg["content"]
            timestamp = msg.get("timestamp", "")

            if role == "user":
                # Mensaje del usuario - alineado a la derecha
                st.markdown(
                    f"""
                <div style="display: flex; justify-content: flex-end; margin-bottom: 12px;">
                    <div style="max-width: 75%;">
                        <div style="
                            background-color: #E8E4DD;
                            color: #3D3D3D;
                            padding: 12px 16px;
                            border-radius: 18px;
                            border-bottom-right-radius: 4px;
                            font-size: 0.95rem;
                            line-height: 1.5;
                        ">{content}</div>
                        <div style="font-size: 0.7rem; color: #999; text-align: right; margin-top: 4px;">{timestamp}</div>
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            else:
                # Mensaje del agente - alineado a la izquierda
                st.markdown(
                    f"""
                <div style="display: flex; justify-content: flex-start; margin-bottom: 12px;">
                    <div style="max-width: 85%;">
                        <div style="
                            background-color: #E07A5F;
                            color: white;
                            padding: 12px 16px;
                            border-radius: 18px;
                            border-bottom-left-radius: 4px;
                            font-size: 0.95rem;
                            line-height: 1.5;
                        ">{content}</div>
                        <div style="font-size: 0.7rem; color: #999; text-align: left; margin-top: 4px;">{timestamp}</div>
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

    # Input del chat
    with st.form(key="chat_form", clear_on_submit=True):
        col_input, col_btn = st.columns([5, 1])

        with col_input:
            user_input = st.text_input(
                "Mensaje",
                placeholder="Escribe tu mensaje aquí...",
                label_visibility="collapsed",
                key="chat_input",
            )

        with col_btn:
            send_clicked = st.form_submit_button("Enviar", use_container_width=True)

        if send_clicked and user_input:
            process_user_input(user_input)
            st.rerun()

    # Botón nueva conversación (debajo del input) con estilo gris
    st.markdown(
        """
        <style>
        div[data-testid="stButton"] button[kind="secondary"] {
            background-color: #7D7D7D !important;
            color: white !important;
        }
        div[data-testid="stButton"] button[kind="secondary"]:hover {
            background-color: #6D6D6D !important;
        }
        </style>
    """,
        unsafe_allow_html=True,
    )

    if st.button(
        "🔄 Nueva conversación",
        key="new_conv_btn",
        use_container_width=True,
        type="secondary",
    ):
        clear_chat()
        st.rerun()


# ==========================================
# COLUMNA DERECHA: OPCIONES Y RESULTADOS
# ==========================================
with col_options:

    # Mostrar resultados si los hay
    if st.session_state.show_results and st.session_state.restaurants:
        st.markdown(
            '<div class="restaurants-title">Detalle lugares encontrados</div>',
            unsafe_allow_html=True,
        )

        # Construir TODO el HTML de una vez (para evitar que Streamlit inserte elementos entre medio)
        cards_html = '<div class="restaurants-scroll-container">'

        for idx, restaurant in enumerate(st.session_state.restaurants):
            # Obtener datos del restaurante y escapar HTML
            name = html_module.escape(restaurant.get("name", "Restaurante"))
            rating = restaurant.get("rating", "N/A")
            reviews = restaurant.get("user_ratings_total", 0)
            area = html_module.escape(
                restaurant.get("area", restaurant.get("neighborhood", "N/A"))
            )
            price = html_module.escape(restaurant.get("price", "€€"))
            phone = html_module.escape(restaurant.get("phone", ""))
            hours = restaurant.get("opening_hours", {})
            photo_name = restaurant.get("photo_name")

            # Generar URL de foto usando el endpoint proxy de FastAPI
            photo_url = f"{API_BASE_URL}/api/photo/{photo_name}" if photo_name else None

            # Determinar disponibilidad/estado
            availability = restaurant.get("availability", "")
            if "Disponible" in availability or "✅" in availability:
                status_class = "status-available"
                status_text = "✅ Disponible"
            elif phone:
                status_class = "status-call"
                status_text = "📞 Llamar para reservar"
            else:
                status_class = "status-call"
                status_text = ""

            # Formatear horario actual
            hours_text = ""
            if hours:
                if hours.get("open_now"):
                    hours_text = "🟢 Abierto ahora"
                else:
                    hours_text = "🔴 Cerrado ahora"

            # Construir HTML de la foto
            if photo_url:
                photo_html = f'<img src="{html_module.escape(photo_url)}" class="card-photo" alt="{name}">'
            else:
                photo_html = '<div class="card-photo" style="background-color: #E0E0E0; display: flex; align-items: center; justify-content: center; color: #999;">🍽️</div>'

            # Construir HTML condicional
            phone_html = (
                '<div class="card-info"><span class="card-info-label">📞</span> '
                + phone
                + "</div>"
                if phone
                else ""
            )
            hours_html = (
                '<div class="card-info">' + hours_text + "</div>" if hours_text else ""
            )
            status_html = (
                '<div class="card-status '
                + status_class
                + '">'
                + status_text
                + "</div>"
                if status_text
                else ""
            )

            # Agregar tarjeta al HTML usando concatenación simple
            cards_html += '<div class="restaurant-card">'
            cards_html += photo_html
            cards_html += '<div class="card-content">'
            cards_html += '<div class="card-name">' + name + "</div>"
            cards_html += (
                '<div class="card-rating">⭐ '
                + str(rating)
                + " ("
                + str(reviews)
                + " reseñas)</div>"
            )
            cards_html += (
                '<div class="card-info"><span class="card-info-label">📍</span> '
                + area
                + "</div>"
            )
            cards_html += (
                '<div class="card-info"><span class="card-info-label">💰</span> '
                + price
                + "</div>"
            )
            cards_html += phone_html
            cards_html += hours_html
            cards_html += status_html
            cards_html += "</div>"  # card-content
            cards_html += "</div>"  # restaurant-card

        # Cerrar contenedor
        cards_html += "</div>"

        # Renderizar TODO de una vez
        st.markdown(cards_html, unsafe_allow_html=True)

    # ==========================================
    # OPCIONES AVANZADAS (COMENTADAS - pueden activarse más adelante)
    # ==========================================
    # NOTA: Estas opciones se envían al agente pero actualmente no se usan efectivamente
    # Para reactivar, descomentar todo el bloque desde aquí hasta "# FIN OPCIONES AVANZADAS"

    # # Opciones avanzadas en desplegable
    # with st.expander("⚙️ Opciones avanzadas", expanded=False):

    # # Ubicación
    # st.markdown("**📍 Ubicación**")
    # st.session_state.preferences['location'] = st.text_input(
    #     "loc",
    #     value=st.session_state.preferences.get('location', ''),
    #     placeholder="Ej: Plaza España, Madrid",
    #     label_visibility="collapsed",
    #     key="pref_location"
    # )

    # # Comensales
    # st.markdown("**👥 Comensales**")
    # st.session_state.preferences['party_size'] = st.number_input(
    #     "party",
    #     min_value=1,
    #     max_value=20,
    #     value=st.session_state.preferences.get('party_size', 2),
    #     label_visibility="collapsed",
    #     key="pref_party"
    # )

    # # Tiempo
    # st.markdown("**🕒 ¿Cuándo?**")
    # use_specific = st.checkbox(
    #     "Fecha/hora específica",
    #     value=st.session_state.preferences.get('use_specific_time', False),
    #     key="pref_specific_time"
    # )
    # st.session_state.preferences['use_specific_time'] = use_specific

    # if use_specific:
    #     c1, c2 = st.columns(2)
    #     with c1:
    #         st.session_state.preferences['selected_date'] = st.date_input(
    #             "Fecha", value=datetime.now(), key="pref_date"
    #         )
    #     with c2:
    #         st.session_state.preferences['selected_time'] = st.time_input(
    #             "Hora", value=dt_time(21, 0), key="pref_time"
    #         )
    # else:
    #     mins = st.slider(
    #         "Minutos de espera",
    #         min_value=10, max_value=120,
    #         value=st.session_state.preferences.get('mins_to_wait', 45),
    #         key="pref_mins"
    #     )
    #     st.session_state.preferences['mins_to_wait'] = mins

    # # Transporte
    # st.markdown("**🚶 Transporte**")
    # transport_map = {
    #     "Caminando": "walking",
    #     "Transporte público": "transit",
    #     "Coche/Taxi": "driving",
    #     "Bicicleta": "bicycling"
    # }
    # selected_transport = st.selectbox(
    #     "transport",
    #     options=list(transport_map.keys()),
    #     label_visibility="collapsed",
    #     key="pref_transport"
    # )
    # st.session_state.preferences['travel_mode'] = transport_map[selected_transport]

    # # Distancia
    # st.session_state.preferences['max_distance'] = st.slider(
    #     "Distancia máxima (km)",
    #     min_value=0.5, max_value=30.0,
    #     value=st.session_state.preferences.get('max_distance', 15.0),
    #     key="pref_distance"
    # )

    # # Precio
    # st.markdown("**💰 Precio**")
    # price_map = {"€": 1, "€€": 2, "€€€": 3, "€€€€": 4}
    # current_price = st.session_state.preferences.get('price_level', 2)
    # current_label = [k for k, v in price_map.items() if v == current_price][0]
    # selected_price = st.select_slider(
    #     "price",
    #     options=list(price_map.keys()),
    #     value=current_label,
    #     label_visibility="collapsed",
    #     key="pref_price"
    # )
    # st.session_state.preferences['price_level'] = price_map[selected_price]

    # # Extras
    # st.markdown("**✨ Extras**")
    # st.session_state.preferences['extras'] = st.text_input(
    #     "extras",
    #     value=st.session_state.preferences.get('extras', ''),
    #     placeholder="Vegano, terraza, sin gluten...",
    #     label_visibility="collapsed",
    #     key="pref_extras"
    # )

    # FIN OPCIONES AVANZADAS
