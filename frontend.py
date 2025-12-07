import streamlit as st
import time
import base64
from datetime import datetime, time as dt_time

# NOTA: Asegúrate de tener este módulo o comenta la línea si solo pruebas UI
from backend_google_places_module import PlaceSearchPayload, places_text_search

# ==========================================
# CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(layout="wide", page_title="FoodLooker", page_icon="🍽️")

# ==========================================
# DEFINICIÓN DE COLORES Y ESTILOS
# ==========================================
COLOR_BG = "#F9F4E6"  # Crema fondo general
COLOR_PRIMARY = "#E07A5F"  # Coral/Salmón (Header y botones)
COLOR_TEXT = "#4A4A4A"  # Texto gris oscuro
COLOR_INPUT_BG = "#2C2C2C"  # Fondo negro del input grande

# Función para cargar imagen local como base64
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        return None

# Intentamos cargar el logo
logo_b64 = get_base64_image("logo.jpeg")

# CSS PERSONALIZADO
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Poppins', sans-serif;
    }}
    .stApp {{
        background-color: {COLOR_BG};
    }}

    /* HEADER */
    .header-box {{
        background-color: {COLOR_PRIMARY};
        padding: 15px 30px;
        border-radius: 15px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 30px;
    }}
    .header-title {{
        color: white;
        font-size: 3.5rem;
        font-weight: 700;
        margin: 0;
        line-height: 1.2;
        letter-spacing: 1px;
    }}
    .header-logo {{
        width: 80px;
        height: 80px;
        border-radius: 50%;
        object-fit: cover;
        border: 3px solid white;
        background-color: white;
    }}

    /* INPUTS BLANCOS */
    div[data-baseweb="input"] > div, 
    div[data-baseweb="select"] > div,
    div[data-baseweb="calendar"] {{
        background-color: white !important;
        border-radius: 10px !important;
        border: 1px solid #ddd !important;
        color: #333 !important;
    }}

    /* TEXT AREA GRANDE (NEGRO) */
    textarea {{
        background-color: {COLOR_INPUT_BG} !important;
        color: white !important;
        font-size: 18px !important;
        border-radius: 12px !important;
        border: none !important;
        font-family: 'Poppins', sans-serif !important;
    }}

    /* SLIDERS */
    div[role="slider"] {{
        background-color: {COLOR_PRIMARY} !important;
        border: 2px solid {COLOR_PRIMARY} !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.2);
    }}
    div[data-baseweb="slider"] > div > div {{
        background-color: white !important;
    }}
    div[data-testid="stSliderTickBar"] {{
        display: none;
    }}

    /* CONTENEDOR DE PREFERENCIAS (Borde Coral) */
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        border-color: {COLOR_PRIMARY} !important;
        border-width: 2px !important;
        border-radius: 15px !important;
        background-color: {COLOR_BG}; 
    }}

    /* Cabecera del contenedor (Truco visual con márgenes negativos) */
    .prefs-header-integrated {{
        background-color: {COLOR_PRIMARY};
        padding: 15px;
        text-align: center;
        color: white;
        font-weight: 700;
        font-size: 1.3rem;
        margin-top: -16px; 
        margin-left: -16px;
        margin-right: -16px;
        margin-bottom: 15px;
        border-radius: 12px 12px 0 0;
    }}

    /* Estilo para el expander de fecha */
    .streamlit-expanderHeader {{
        background-color: white !important;
        border-radius: 8px !important;
        font-size: 0.9rem !important;
        color: {COLOR_PRIMARY} !important;
        font-weight: 600 !important;
        border: 1px solid #ddd !important;
    }}

    /* CARDS RESULTADOS */
    .restaurant-card {{
        background-color: #EFEDE6;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }}
    .card-name {{ font-size: 1.2rem; font-weight: 700; color: #5A4A42; }}
    .card-info {{ color: #777; font-size: 0.95rem; margin-top: 5px; }}

    /* BOTONES */
    div.stButton > button {{
        background-color: {COLOR_PRIMARY};
        color: white;
        border-radius: 30px;
        border: none;
        padding: 12px 30px;
        font-size: 1rem;
        font-weight: 600;
        box-shadow: 0 4px 6px rgba(224, 122, 95, 0.3);
        transition: all 0.3s ease;
    }}
    div.stButton > button:hover {{
        background-color: #D66A4F;
        transform: translateY(-2px);
    }}

    /* Estilo específico para la lista compacta del panel derecho */
    .compact-list-item {{
        display: flex;
        margin-bottom: 8px;
        align-items: center;
        color: #5A4A42; /* Color forzado marrón oscuro */
        font-size: 0.95rem;
    }}
    .compact-icon {{
        margin-right: 10px;
        font-size: 1.1rem;
        width: 25px;
        text-align: center;
    }}

    .block-container {{ padding-top: 2rem; }}

</style>
""", unsafe_allow_html=True)

# ==========================================
# GESTIÓN DE ESTADO
# ==========================================
if 'step' not in st.session_state:
    st.session_state.step = 1

if 'selected_date' not in st.session_state:
    st.session_state.selected_date = None
if 'selected_time' not in st.session_state:
    st.session_state.selected_time = None
if 'results' not in st.session_state:
    st.session_state.results = []

# ==========================================
# HEADER COMPONENT
# ==========================================
def render_header():
    img_html = f'<img src="data:image/jpeg;base64,{logo_b64}" class="header-logo">' if logo_b64 else '<span style="font-size: 3rem; background: white; border-radius: 50%; padding: 10px;">🍽️</span>'
    st.markdown(f"""
        <div class="header-box">
            {img_html}
            <h1 class="header-title">FoodLooker</h1>
        </div>
    """, unsafe_allow_html=True)

# ==========================================
# PANTALLA 1: HOME / BÚSQUEDA
# ==========================================
def render_screen_1():
    render_header()

    col_left, col_spacer, col_right = st.columns([1.2, 0.1, 1])

    with col_left:
        # Welcome Card
        st.markdown("""
        <div style="background-color: white; padding: 25px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 10px rgba(0,0,0,0.03);">
            <h3 style="margin-top:0; color:#E07A5F; font-weight:700;">¡Buenas tardes! 🍱</h3>
            <p style="color:#5A4A42; font-weight:600; font-size: 1.1rem;">¿Planificando la cena? Encontremos tu restaurante ideal</p>
            <div style="margin-top: 15px; font-size: 0.9rem; color: #888;">
                <p style="margin-bottom:5px;">💡 <strong>Ejemplos de búsqueda:</strong></p>
                <ul style="padding-left: 20px; line-height: 1.6;">
                    <li>"Busco un restaurante japonés para 2 personas esta noche"</li>
                    <li>"Necesito un lugar con terraza cerca del Retiro"</li>
                    <li>"Restaurante italiano romántico para cena de aniversario"</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<h4 style="color:#5A4A42;">🔍 ¿Qué estás buscando?</h4>', unsafe_allow_html=True)
        query = st.text_area(
            "Query",
            placeholder="Resérvame en un japonés para dentro de 45min para 4 personas\n(Escribe aquí tu petición...)",
            height=140,
            label_visibility="collapsed"
        )

        st.write("")
        if st.button("Buscar Disponibilidad", use_container_width=True):
            if query:
                with st.spinner("Buscando restaurantes..."):

                    # 1. DUMMY Payload
                    dummy_payload = PlaceSearchPayload(
                        query="restaurante japonés",
                        location="Plaza España, Madrid",
                        radius=1500,
                        price_level=2,
                        extras=[],
                        max_travel_time=None,
                        travel_mode="walking"
                    )

                    # 2. Llamada REAL
                    try:
                        api_response = places_text_search(dummy_payload)
                    except Exception as e:
                        st.error(f"Error consultando Google Places: {e}")
                        st.stop()

                    # 3. PROCESAMIENTO
                    # >>> MEJORA: Seleccionamos solo los 3 primeros resultados <<<
                    places = api_response.get("results", [])[:3] 

                    processed = []
                    for i, p in enumerate(places):
                        processed.append({
                            "id": i + 1,
                            "name": p.get("name"),
                            "area": p.get("neighborhood", "Madrid Centro"), # Fallback si viene vacío
                            "price": "€€",  
                            "avail": "—", 
                        })

                    st.session_state.results = processed
                    st.session_state.step = 2
                    st.rerun()

    with col_right:
        st.markdown(
            '<div style="background:#E07A5F; color:white; padding:10px 20px; border-radius:10px; font-weight:bold; display:inline-block; margin-bottom:10px;">¿Dónde te encuentras?</div>',
            unsafe_allow_html=True)
        st.text_input("Ubicación", placeholder="Ubicación: ej: Plaza España, Madrid", label_visibility="collapsed")

        st.markdown("<br>", unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown('<div class="prefs-header-integrated">Customiza Preferencias</div>', unsafe_allow_html=True)

            # Tiempo
            st.markdown('<p style="color:#6B4423; font-weight:600; margin-bottom:5px;">¿Para dentro de cuanto?</p>', unsafe_allow_html=True)
            c1, c2 = st.columns([3, 1])
            with c1:
                mins = st.slider("Minutos", 10, 120, 50, label_visibility="collapsed")
            with c2:
                st.markdown(f'<div style="margin-top:5px; font-weight:bold; color:#5A4A42;">{mins} mins</div>', unsafe_allow_html=True)

            # Fecha/Hora
            st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
            with st.expander("📅 O elige fecha y hora exacta"):
                col_date, col_time = st.columns(2)
                with col_date:
                    st.session_state.selected_date = st.date_input("Fecha", datetime.now())
                with col_time:
                    st.session_state.selected_time = st.time_input("Hora", dt_time(21, 00))

            # Precio
            st.markdown('<p style="color:#6B4423; font-weight:600; margin-bottom:5px; margin-top:15px;">Rango precio (€ - €€€€)</p>', unsafe_allow_html=True)
            c3, c4 = st.columns([3, 1])
            with c3:
                price = st.select_slider("Precio", options=["€", "€€", "€€€", "€€€€"], value="€€", label_visibility="collapsed")
            with c4:
                st.markdown(f'<div style="margin-top:5px; font-weight:bold; color:#5A4A42;">{price}</div>', unsafe_allow_html=True)

            # Extras
            st.write("")
            st.markdown('<p style="color:#6B4423; font-weight:600; margin-bottom:5px;">Alguna preferencia extra?</p>', unsafe_allow_html=True)
            st.markdown('<p style="color:#888; font-size:0.85rem; margin-top:-5px;">Ej: Vegano, solo terraza, celiaco...</p>', unsafe_allow_html=True)
            st.text_input("Extras", placeholder="Introduce preferencias", label_visibility="collapsed")


# ==========================================
# PANTALLA 2: RESULTADOS
# ==========================================
def render_screen_2():
    render_header()

    # >>> MEJORA: Ajuste de columnas para dar más espacio a resultados [2, 0.1, 1] <<<
    col_res, col_space, col_filt = st.columns([2, 0.1, 1])

    with col_res:
        st.markdown('<h3 style="color:#5A4A42; font-weight:700;">Tus TOP 3 picks en restaurantes!</h3>', unsafe_allow_html=True)

        results = st.session_state.results
        
        if not results:
            st.warning("No se encontraron resultados.")
        
        for index, item in enumerate(results):
            st.markdown(f"""
            <div class="restaurant-card">
                <div>
                    <div class="card-name">{item['name']}</div>
                    <div class="card-info">{item['area']}  •  <span style="color:#5A4A42; font-weight:bold;">{item['price']}</span></div>
                </div>
                <div style="text-align:right;">
                     <div style="color:#666; font-size:0.9rem;">{item['avail']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Botones de reordenar más compactos
            c1, c2, c3 = st.columns([0.1, 0.1, 0.8])
            with c1:
                if index > 0:
                    if st.button("⬆", key=f"up_{item['id']}"):
                        results[index], results[index - 1] = results[index - 1], results[index]
                        st.rerun()
            with c2:
                if index < len(results) - 1:
                    if st.button("⬇", key=f"down_{item['id']}"):
                        results[index], results[index + 1] = results[index + 1], results[index]
                        st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<h4 style="color:#6B4423; text-align:center;">Ordena por preferencia y intentaremos gestionarlo!</h4>', unsafe_allow_html=True)

        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        with col_btn2:
            st.markdown("""
            <style>
                div.stButton > button.go-btn { font-size: 1.5rem !important; padding: 15px 40px !important; }
            </style>
            """, unsafe_allow_html=True)
            if st.button("Go!", use_container_width=True):
                st.balloons()
                st.success("Gestionando reserva...")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⬅ Volver / Si no lo conseguimos sugerirte nuevos lugares"):
            st.session_state.step = 1
            st.rerun()

    with col_filt:
        # >>> MEJORA: Panel lateral compacto y con colores forzados para visibilidad <<<
        with st.container(border=True):
            # Cabecera
            st.markdown('<div class="prefs-header-integrated">Configuración Actual</div>', unsafe_allow_html=True)

            # Lógica fecha string
            date_str_display = "~50 min"
            date_obj = st.session_state.get('selected_date')
            if date_obj and date_obj != datetime.now().date():
                 time_obj = st.session_state.get('selected_time')
                 date_str_display = f"{date_obj.strftime('%d/%m')} - {time_obj.strftime('%H:%M')}"

            # Contenido compacto con HTML para asegurar color oscuro
            st.markdown(f"""
                <div style="padding: 0 10px 10px 10px;">
                    <div class="compact-list-item">
                        <span class="compact-icon">📍</span>
                        <span>Plaza España</span>
                    </div>
                    <div class="compact-list-item">
                        <span class="compact-icon">⏱</span>
                        <span>{date_str_display}</span>
                    </div>
                    <div class="compact-list-item">
                        <span class="compact-icon">💰</span>
                        <span>€€</span>
                    </div>
                    <div class="compact-list-item">
                        <span class="compact-icon">📝</span>
                        <span>Sin extras</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

# ==========================================
# MAIN APP
# ==========================================
if st.session_state.step == 1:
    render_screen_1()
else:
    render_screen_2()