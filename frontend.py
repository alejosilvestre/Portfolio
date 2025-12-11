import streamlit as st
import time
import base64
from datetime import datetime, time as dt_time

# ==========================================
# CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(layout="wide", page_title="FoodLooker", page_icon="🍽️")

# imports propios

from backend_google_places import PlaceSearchPayload, places_text_search
from first_input_llm import call_llm


# ==========================================
# DEFINICIÓN DE COLORES Y ESTILOS
# ==========================================
COLOR_BG = "#F9F4E6"  # Crema fondo general
COLOR_PRIMARY = "#E07A5F"  # Coral/Salmón
COLOR_TEXT = "#4A4A4A"  # Texto gris oscuro
COLOR_INPUT_BG = "#2C2C2C"  # Fondo negro del input grande

# Carga de imagen (Logo)
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        return None

logo_b64 = get_base64_image("logo.jpeg")

# CSS GENERAL
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
    div[data-baseweb="select"] > div {{
        background-color: white !important;
        border-radius: 10px !important;
        border: 1px solid #cccccc !important;
        color: #333 !important;
    }}
    input {{ color: #333 !important; }}

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

    /* TARJETAS RESULTADOS */
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
    
    .block-container {{ padding-top: 2rem; }}

    /* EXPANDER CUSTOMIZATION */
    details > summary {{
        background-color: white !important;
        color: #5A4A42 !important;
        border: 1px solid #cccccc !important;
        border-radius: 8px !important;
        padding: 10px 15px !important;
    }}
    details > summary > span, details > summary p {{
        font-weight: 600 !important;
        color: #5A4A42 !important;
    }}
    details > summary svg {{
        fill: #5A4A42 !important;
        color: #5A4A42 !important;
    }}
    div[data-testid="stExpanderDetails"] {{
        border: 1px solid #cccccc;
        border-top: none;
        border-bottom-left-radius: 8px;
        border-bottom-right-radius: 8px;
        background-color: white;
        padding: 20px;
    }}

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
    
    # === CSS ESPECÍFICO PARA ARREGLAR CHECKBOX Y CALENDARIO ===
    st.markdown("""
        <style>
        /* 1. ARREGLAR TEXTO DEL CHECKBOX */
        div[data-testid="stCheckbox"] label p {
            color: #5A4A42 !important; /* Marrón oscuro forzado */
            font-weight: 600 !important;
        }
        /* Por seguridad, si el DOM cambia ligeramente */
        div[data-testid="stCheckbox"] span {
            color: #5A4A42 !important;
        }

        /* 2. ARREGLAR CALENDARIO */
        div[role="grid"] div { color: #333333 !important; }
        div[data-baseweb="calendar"] { background-color: #FFFFFF !important; }
        div[role="grid"] div:hover { background-color: #E07A5F !important; color: white !important; }
        div[data-baseweb="calendar"] button { color: #333333 !important; }
        
        /* 3. ARREGLAR PLACEHOLDER */
        input::placeholder { color: #888 !important; opacity: 1 !important; }
        </style>
    """, unsafe_allow_html=True)

    col_left, col_spacer, col_right = st.columns([1.2, 0.1, 1])
    
    # ==========================================
    # --- VARIABLES DE ENTRADA ---
    search_clicked = False
    query = ""
    location = ""
    mins = None
    price = None
    extra_input = ""
    travel_mode = ""
    max_distance = None
    col_date = None
    col_time = None

    # ==========================================
    
    # --- COLUMNA IZQUIERDA ---
    with col_left:
        st.markdown("""
        <div style="background-color: white; padding: 25px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 10px rgba(0,0,0,0.03);">
            <h3 style="margin-top:0; color:#E07A5F; font-weight:700;">¡Buenas tardes! 🍱</h3>
            <p style="color:#5A4A42; font-weight:600; font-size: 1.1rem;">¿Planificando la cena? Encontremos tu restaurante ideal</p>
            <div style="margin-top: 15px; font-size: 0.9rem; color: #888;">
                <p style="margin-bottom:5px;">💡 <strong>Ejemplos de búsqueda:</strong></p>
                <ul style="padding-left: 20px; line-height: 1.6;">
                    <li>"Busco un restaurante japonés para 2 personas esta noche"</li>
                    <li>"Necesito un lugar con terraza cerca del Retiro"</li>
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
        search_clicked = st.button("Buscar Disponibilidad", use_container_width=True)


    # --- COLUMNA DERECHA ---
    with col_right:
        st.markdown(
            '<div style="background:#E07A5F; color:white; padding:10px 20px; border-radius:10px; font-weight:bold; display:inline-block; margin-bottom:10px;">¿Dónde te encuentras?</div>',
            unsafe_allow_html=True)
        
        location = st.text_input("Ubicación", placeholder="Ubicación: ej: Plaza España, Madrid", label_visibility="collapsed")

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Desplegable de Preferencias
        with st.expander("⚙️ Preferencias Avanzadas (Hora, Precio, Transporte...)", expanded=False):
            
            # --- 1. SECCIÓN TIEMPO (Lógica conmutada) ---
            # --- 1. SECCIÓN TIEMPO ---
            st.markdown('<p style="color:#6B4423; font-weight:600; margin-bottom:5px;">🕒 ¿Cuándo?</p>', unsafe_allow_html=True)
            
            # 1. Creamos un CONTENEDOR VACÍO arriba para poner el Slider o el Calendario
            time_container = st.container()

            # 2. Ponemos el CHECKBOX debajo
            # Añadimos un poco de margen top para separarlo visualmente del contenedor de arriba
            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True) 
            use_specific_time = st.checkbox("📅 Programar para una fecha/hora específica", value=False)
            
            # 3. Rellenamos el contenedor de ARRIBA basándonos en el checkbox de ABAJO
            with time_container:
                if not use_specific_time:
                    # --- MODO A: SLIDER (Se muestra ARRIBA si NO está marcado) ---
                    st.markdown('<p style="font-size:0.85rem; color:#888; margin-top:-10px; margin-bottom:10px;">Selecciona tiempo de espera aproximado:</p>', unsafe_allow_html=True)
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        mins = st.slider("Minutos", 10, 120, 50, label_visibility="collapsed")
                    with c2:
                        st.markdown(f'<div style="margin-top:5px; font-weight:bold; color:#5A4A42;">{mins} min</div>', unsafe_allow_html=True)
                    
                    # Limpiamos variables de fecha para no confundir a la lógica final
                    st.session_state.selected_date = None
                    st.session_state.selected_time = None
                    
                else:
                    # --- MODO B: FECHA EXACTA (Se muestra ARRIBA si SÍ está marcado) ---
                    st.markdown('<p style="font-size:0.85rem; color:#888; margin-top:-10px; margin-bottom:10px;">Selecciona el momento exacto:</p>', unsafe_allow_html=True)
                    col_date, col_time = st.columns(2)
                    with col_date:
                        st.session_state.selected_date = st.date_input("Fecha", datetime.now())
                    with col_time:
                        st.session_state.selected_time = st.time_input("Hora", dt_time(21, 00))

            # Separador visual después del checkbox
            st.markdown("<hr style='margin: 15px 0; border-color: #eee;'>", unsafe_allow_html=True)

            # --- 2. RESTO DE PREFERENCIAS ---
            
            # Transporte
            st.markdown('<p style="color:#6B4423; font-weight:600; margin-bottom:5px;">Modo de transporte</p>', unsafe_allow_html=True)
            transport_options = {"Caminando": "walking", "Transporte público": "transit", "Coche/Taxi": "driving", "Bicicleta": "bicycling"}
            c5, c6 = st.columns([3, 1])
            with c5:
                selected_transport_label = st.selectbox("Transporte", options=list(transport_options.keys()), index=0, label_visibility="collapsed")
            with c6:
                st.markdown(f'<div style="margin-top:5px; font-weight:bold; color:#5A4A42;">{selected_transport_label}</div>', unsafe_allow_html=True)
            travel_mode = transport_options[selected_transport_label]

            # Distancia
            st.markdown('<p style="color:#6B4423; font-weight:600; margin-bottom:5px; margin-top:15px;">Distancia máxima al sitio (km)</p>', unsafe_allow_html=True)
            c7, c8 = st.columns([3, 1])
            with c7:
                max_distance = st.slider("Distancia (km)", 0.1, 30.0, 15.0, label_visibility="collapsed")
            with c8:
                st.markdown(f'<div style="margin-top:5px; font-weight:bold; color:#5A4A42;">{max_distance} km</div>', unsafe_allow_html=True)

            # Precio
            st.markdown('<p style="color:#6B4423; font-weight:600; margin-bottom:5px; margin-top:15px;">Rango precio (€ - €€€€)</p>', unsafe_allow_html=True)
            c3, c4 = st.columns([3, 1])
            with c3:
                price_options = {"€": 1, "€€": 2, "€€€": 3, "€€€€": 4}
                price = st.select_slider("Precio", options=list(price_options.keys()), value="€€", label_visibility="collapsed")
            with c4:
                st.markdown(f'<div style="margin-top:5px; font-weight:bold; color:#5A4A42;">{price}</div>', unsafe_allow_html=True)

            # Extras
            st.write("")
            st.markdown('<p style="color:#6B4423; font-weight:600; margin-bottom:5px;">Alguna preferencia extra?</p>', unsafe_allow_html=True)
            extra_input = st.text_input("Extras", placeholder="Ej: Vegano, solo terraza, celiaco...", label_visibility="collapsed")

    # ==========================================
    # LÓGICA DE BÚSQUEDA
    # ==========================================
    if search_clicked:
        if query or location:
            with st.spinner("Buscando restaurantes..."):

                # creamos diccionario con todos los inputs obtenidos
                llm_inputs = {
                    "query": query,
                    "location": location,
                    "max_distance": max_distance,
                    "mins": mins,
                    "travel_mode": travel_mode,
                    "price": price_options.get(price, 2),
                    "col_date": str(col_date) if col_date else "",
                    "col_time": str(col_time) if col_time else "",
                    "extras": [e.strip().lower() for e in extra_input.split(",")] if extra_input else [
                    ]
                }

                # Llamada al LLM
                llm_response = call_llm(
                    prompt_variables=llm_inputs,
                    parse_json=True
                )

                # Respuesta a api de Google Places
                google_places_payload = PlaceSearchPayload(**llm_response)
                resultados = places_text_search(google_places_payload)
                
                # Procesamos resultados para la UI filtrando los primeros 3 resultados y mostrando:
                # Nombre, Zona, Precio, y rating
                processed = []
                for i, p in enumerate(resultados):
                    processed.append({
                        "id": i + 1,
                        "name": p.get("name"),
                        "area": p.get("neighborhood"),
                        "price": p.get("price_level"),
                        "rating": p.get("rating")
                    })
                    if i >= 2:
                        break  # Solo los primeros 3


                st.session_state.results = processed
                st.session_state.step = 2
                st.rerun()

# ==========================================
# PANTALLA 2: RESULTADOS
# ==========================================
def render_screen_2():
    render_header()

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
                     <div style="color:#666; font-size:0.9rem;">{item['rating']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

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
        # Panel lateral compacto
        with st.container(border=True):
            st.markdown('<div class="prefs-header-integrated">Configuración Actual</div>', unsafe_allow_html=True)
            
            # Lógica simple para mostrar algo en el resumen
            date_display = "~50 mins"
            if st.session_state.selected_date:
                t = st.session_state.selected_time
                date_display = f"{st.session_state.selected_date.strftime('%d/%m')} {t.strftime('%H:%M') if t else ''}"
            
            st.markdown(f"""
                <div style="padding: 0 10px 10px 10px;">
                    <div style="display:flex; margin-bottom:8px; align-items:center; color:#5A4A42;">
                        <span style="margin-right:10px; font-size:1.1rem; width:25px; text-align:center;">📍</span>
                        <span>Plaza España</span>
                    </div>
                    <div style="display:flex; margin-bottom:8px; align-items:center; color:#5A4A42;">
                        <span style="margin-right:10px; font-size:1.1rem; width:25px; text-align:center;">⏱</span>
                        <span>{date_display}</span>
                    </div>
                    <div style="display:flex; margin-bottom:8px; align-items:center; color:#5A4A42;">
                        <span style="margin-right:10px; font-size:1.1rem; width:25px; text-align:center;">💰</span>
                        <span>€€</span>
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