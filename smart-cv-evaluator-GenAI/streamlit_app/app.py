"""
CV Evaluator - Versión Simplificada
"""
import streamlit as st
from pathlib import Path
import sys
from PyPDF2 import PdfReader

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.schemas import AppPhase, EvaluationResult, InterviewState
from core.evaluator import evaluate_candidate
from core.interviewer import interview_step, generate_first_question, log_final_evaluation, generate_summary
from config.settings import load_config


# =============================================================================
# CONFIGURACIÓN
# =============================================================================
st.set_page_config(
    page_title="CV Evaluator | Velora",
    page_icon="🤖",
    layout="centered",
)

# CSS
st.markdown("""
<style>
    /* Layout general */
    .stApp { background-color: #FFFFFF; }
    .block-container { max-width: 900px; padding-top: 4rem; }
    
    /* Forzar fondo blanco en todo */
    .main, .main > div {
        background-color: #FFFFFF !important;
    }
    
    /* Tipografía */
    h1, h2, h3, h4, h5, h6 {
        color: #5A5A5A !important;
    }
    
    p, span, div, label {
        color: #5A5A5A;
    }
    
    .stMarkdown, .stMarkdown p {
        color: #5A5A5A !important;
    }
    
    /* Text areas */
    .stTextArea textarea {
        background-color: #F5F5F5 !important;
        border: 1px solid #E8E8E8 !important;
        border-radius: 8px !important;
        color: #5A5A5A !important;
    }
    
    .stTextArea textarea::placeholder {
        color: #888888 !important;
    }
    
    /* Botones */
    .stButton > button {
        background: linear-gradient(135deg, #00D4E8 0%, #00C9B7 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 2rem;
        font-weight: 500;
        width: 100%;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #00B8C8 0%, #00B5A5 100%);
    }
    
    /* Score box */
    .score-box {
        background: #F5F5F5;
        border-radius: 12px;
        padding: 24px;
        text-align: center;
        margin: 16px 0;
    }
    
    .score-value {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #00D4E8, #00C9B7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Summary box */
    .summary-box {
        background: #F5F5F5;
        border-radius: 8px;
        padding: 16px;
        margin: 16px 0;
        color: #5A5A5A;
        line-height: 1.6;
    }
    
    /* Chat messages */
    .stChatMessage {
        background-color: #F5F5F5 !important;
    }
    
    .stChatMessage p, .stChatMessage div, .stChatMessage span {
        color: #5A5A5A !important;
    }
    
    /* Chat input */
    .stChatInput {
        position: relative !important;
        bottom: auto !important;
        padding: 16px 0 !important;
        max-width: 100% !important;
        margin-top: 20px !important;
    }

    .stChatInput textarea {
        background-color: #F5F5F5 !important;
        border: 2px solid #00D4E8 !important;
        border-radius: 8px !important;
        color: #5A5A5A !important;
        padding: 12px !important;
    }

    .stChatInput textarea::placeholder {
        color: #888888 !important;
    }

    .stChatInput textarea:focus {
        border-color: #00C9B7 !important;
        box-shadow: 0 0 0 3px rgba(0, 212, 232, 0.2) !important;
    }
    
    /* Bottom bar - Forzar blanco completo */
    .stBottom, 
    [data-testid="stBottom"],
    [data-testid="stBottomBlockContainer"],
    .stBottom > div,
    .stBottom iframe,
    section[data-testid="stBottom"] {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        border-top: none !important;
    }

    iframe[title="streamlit_chat_input"] {
        background-color: #FFFFFF !important;
    }
    
    /* File uploader */
    .stFileUploader {
        background-color: #F5F5F5 !important;
        border-radius: 8px !important;
        padding: 16px !important;
    }

    .stFileUploader label {
        color: #5A5A5A !important;
    }

    [data-testid="stFileUploader"] {
        background-color: #F5F5F5 !important;
    }

    [data-testid="stFileUploader"] section {
        background-color: #F5F5F5 !important;
        border: 2px dashed #00D4E8 !important;
        border-radius: 8px !important;
    }

    [data-testid="stFileUploader"] section:hover {
        border-color: #00C9B7 !important;
    }
    
    /* Expander */
    .stExpander {
        color: #5A5A5A !important;
    }
    
    .stExpander p, .stExpander div, .stExpander span {
        color: #5A5A5A !important;
    }
    
    /* Ocultar elementos de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# =============================================================================
# FUNCIONES DE ESTADO
# =============================================================================
def init_state():
    if "phase" not in st.session_state:
        st.session_state.phase = AppPhase.READY
    if "evaluation" not in st.session_state:
        st.session_state.evaluation = None
    if "interview" not in st.session_state:
        st.session_state.interview = None
    if "messages" not in st.session_state:
        st.session_state.messages = []


def reset():
    st.session_state.phase = AppPhase.READY
    st.session_state.evaluation = None
    st.session_state.interview = None
    st.session_state.messages = []


def load_example_offer():
    config = load_config()
    try:
        with open(config["EXAMPLE_OFFER_PATH"], "r", encoding="utf-8") as f:
            return f.read()
    except:
        return "- Experiencia mínima de 3 años en Python\n- Formación requerida: Grado en informática o Master en IA\n- Valorable conocimientos en FastAPI y LangChain"


def update_evaluation_after_answer(interpretation: str, requirement: str):
    """Actualiza EvaluationResult según la interpretación."""
    evaluation = st.session_state.evaluation
    
    if interpretation == "confirmed":
        if requirement in evaluation.to_verify:
            evaluation.to_verify.remove(requirement)
        evaluation.matching_requirements.append(requirement)
        
    elif interpretation == "denied":
        if requirement in evaluation.to_verify:
            evaluation.to_verify.remove(requirement)
        evaluation.unmatching_requirements.append(requirement)
        
        # Verificar si era obligatorio
        if requirement in evaluation.Ls_mandatory_requirements:
            evaluation.discarded = True
            evaluation.score = 0
            return
    
    # Recalcular score
    evaluation.score = (len(evaluation.matching_requirements) / evaluation.total_requirements) * 100


def advance_interview():
    """Avanza al siguiente requisito o termina la entrevista."""
    interview = st.session_state.interview
    
    # Quitar el requisito actual de pending
    if interview.pending:
        interview.pending.pop(0)
    
    interview.unclear_attempts = 0
    
    # Si hay más pendientes, actualizar current
    if interview.pending:
        interview.current = interview.pending[0]
    else:
        # Entrevista terminada
        interview.current = ""
        st.session_state.phase = AppPhase.COMPLETED


def extract_text_from_pdf(uploaded_file) -> str:
    """Extrae texto de un archivo PDF."""
    
    text = ""
    reader = PdfReader(uploaded_file)
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    
    return text.strip()


# =============================================================================
# UI
# =============================================================================
init_state()

# Header
logo_path = Path(__file__).parent / "logo.png"
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if logo_path.exists():
        st.image(str(logo_path), use_container_width=True)

st.markdown(
    """
    <div style="text-align:center; color:#5A5A5A;">
        <p><strong>Sistema autónomo de evaluación de CV</strong></p>
        <p>Pasos:</p>
        <ol style="display:inline-block; text-align:left;">
            <li>Oferta precargada, si quieres editarla o cambiarla puedes hacerlo</li>
            <li>Adjunta tu CV o escribe tu experiencia en la casilla</li>
            <li>Pulsa en <em>Evaluar</em></li>
        </ol>
    </div>
    """,
    unsafe_allow_html=True
)

# =============================================================================
# FASE: READY - Input inicial
# =============================================================================
if st.session_state.phase == AppPhase.READY:
    
    offer_default = f"Gracias por inscribirte a esta posición.\n\nBuscamos una persona con los siguientes requisitos:\n{load_example_offer()}"
    
    offer_text = st.text_area(
        "Oferta",
        value=offer_default,
        height=180,
        label_visibility="collapsed",
    )
    
    st.markdown("#### 📄 Tu CV")
    
    # Subir PDF
    uploaded_pdf = st.file_uploader(
        "Sube tu CV en PDF",
        type=["pdf"],
        help="Arrastra o selecciona tu CV en formato PDF"
    )
    
    # Texto extraído del PDF (si existe)
    pdf_text = ""
    if uploaded_pdf:
        with st.spinner("Extrayendo información del PDF..."):
            pdf_text = extract_text_from_pdf(uploaded_pdf)
        st.success(f"✅ PDF procesado: {len(pdf_text)} caracteres extraídos")
    
    # Input de texto adicional
    cv_text_input = st.text_area(
        "CV",
        value="",
        height=120,
        placeholder="También puedes añadir información adicional aquí...",
        label_visibility="collapsed",
    )
    
    # Combinar PDF + texto adicional
    cv_combined = ""
    if pdf_text:
        cv_combined = pdf_text
    if cv_text_input.strip():
        if cv_combined:
            cv_combined += "\n\n--- Información adicional ---\n" + cv_text_input
        else:
            cv_combined = cv_text_input
    
    if st.button("Evaluar mi perfil", use_container_width=True):
        if not cv_combined.strip():
            st.error("Por favor, sube tu CV en PDF o introduce tu experiencia en el campo de texto.")
        else:
            with st.spinner("Evaluando perfil..."):
                # Evaluar candidato (1 llamada LLM)
                result = evaluate_candidate(offer_text, cv_combined)
                st.session_state.evaluation = result
                
                if result.discarded:
                    # Descartado → directo a completado
                    st.session_state.phase = AppPhase.COMPLETED
                    
                elif result.to_verify:
                    # Hay requisitos por verificar → entrevista
                    first_requirement = result.to_verify[0]
                    first_question = generate_first_question(first_requirement)
                    
                    st.session_state.interview = InterviewState(
                        pending=result.to_verify.copy(),
                        current=first_requirement,
                        unclear_attempts=0,
                        message=first_question
                    )
                    st.session_state.messages.append({"role": "assistant", "content": first_question})
                    st.session_state.phase = AppPhase.INTERVIEWING
                    
                else:
                    # Todo cumplido → directo a completado
                    st.session_state.phase = AppPhase.COMPLETED
                
                st.rerun()


# =============================================================================
# FASE: INTERVIEWING - Preguntas
# =============================================================================
elif st.session_state.phase == AppPhase.INTERVIEWING:
    
    st.markdown("### 💬 Preguntas adicionales")
    
    # Mostrar mensajes
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
            st.markdown(msg["content"])
    
    # Input
    user_input = st.chat_input("Escribe tu respuesta...")
    
    if user_input:
        # Añadir mensaje del usuario
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        interview = st.session_state.interview
        
        # Construir historial de conversación
        conversation_history = ""
        for msg in st.session_state.messages[:-1]:
            role = "Entrevistador" if msg["role"] == "assistant" else "Candidato"
            conversation_history += f"{role}: {msg['content']}\n"
        
        # Determinar siguiente requisito
        next_requirement = None
        if len(interview.pending) > 1:
            next_requirement = interview.pending[1]
        
        # Llamar al LLM con historial
        result = interview_step(
            current_requirement=interview.current,
            candidate_answer=user_input,
            next_requirement=next_requirement,
            conversation_history=conversation_history
        )
        
        interpretation = result.get("interpretation", "unclear")
        message = result.get("message", "")
        
        if interpretation == "confirmed":
            update_evaluation_after_answer("confirmed", interview.current)
            advance_interview()
            
            if st.session_state.phase == AppPhase.INTERVIEWING:
                st.session_state.messages.append({"role": "assistant", "content": message})
                interview.message = message
                
        elif interpretation == "denied":
            update_evaluation_after_answer("denied", interview.current)
            
            if st.session_state.evaluation.discarded:
                st.session_state.phase = AppPhase.COMPLETED
            else:
                advance_interview()
                if st.session_state.phase == AppPhase.INTERVIEWING:
                    st.session_state.messages.append({"role": "assistant", "content": message})
                    interview.message = message
                    
        elif interpretation == "unclear":
            interview.unclear_attempts += 1
            
            if interview.unclear_attempts >= 2:
                update_evaluation_after_answer("denied", interview.current)
                advance_interview()
                
                if st.session_state.phase == AppPhase.INTERVIEWING:
                    st.session_state.messages.append({"role": "assistant", "content": message})
                    interview.message = message
            else:
                st.session_state.messages.append({"role": "assistant", "content": message})
                interview.message = message
        
        st.rerun()


# =============================================================================
# FASE: COMPLETED - Resultado
# =============================================================================
elif st.session_state.phase == AppPhase.COMPLETED:
    
    evaluation = st.session_state.evaluation
    
    # Loguear resultado final en LangSmith
    log_final_evaluation(
        total_requirements=evaluation.total_requirements,
        score=evaluation.score,
        discarded=evaluation.discarded,
        matching_requirements=evaluation.matching_requirements,
        unmatching_requirements=evaluation.unmatching_requirements,
        mandatory_requirements=evaluation.Ls_mandatory_requirements,
        optional_requirements=evaluation.Ls_optional_requirements
    )
    
    # Mostrar score
    st.markdown(f"""
        <div class="score-box">
            <div style="color:#5A5A5A; font-size:0.95rem;">Tu compatibilidad con esta posición</div>
            <div class="score-value">{evaluation.score:.0f}%</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Generar y mostrar resumen si no es 100% o está descartado
    if evaluation.discarded or evaluation.score < 100:
        with st.spinner("Generando resumen..."):
            summary = generate_summary(
                score=evaluation.score,
                discarded=evaluation.discarded,
                matching_requirements=evaluation.matching_requirements,
                unmatching_requirements=evaluation.unmatching_requirements,
                mandatory_requirements=evaluation.Ls_mandatory_requirements
            )
        st.markdown(f'<div class="summary-box">{summary}</div>', unsafe_allow_html=True)
    else:
        st.success("¡Felicidades! Cumples con todos los requisitos de la posición.")
    
    # Detalles
    with st.expander("Ver detalles"):
        if evaluation.matching_requirements:
            st.markdown("**✅ Requisitos cumplidos:**")
            for req in evaluation.matching_requirements:
                st.markdown(f"- {req}")
        
        if evaluation.unmatching_requirements:
            st.markdown("**❌ Requisitos no cumplidos:**")
            for req in evaluation.unmatching_requirements:
                st.markdown(f"- {req}")
    
    # Reset
    if st.button("🔄 Nueva evaluación", use_container_width=True):
        reset()
        st.rerun()