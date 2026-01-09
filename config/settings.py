"""
Configuración de la aplicación.
Carga variables de entorno y configura servicios externos.
"""
import os
from dotenv import load_dotenv


def load_config():
    """
    Carga todas las credenciales del .env y configura los servicios.
    Devuelve un diccionario con toda la configuración.
    """
    load_dotenv()
    
    config = {
        # OpenAI
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
        "MODEL_NAME": os.getenv("MODEL_NAME", "gpt-4o-mini"),
        "TEMPERATURE": float(os.getenv("TEMPERATURE", "0.3")),

        #Google Places
        "GOOGLE_MAPS_API_KEY": os.getenv("GOOGLE_MAPS_API_KEY", ""),

        #Tavily web search
        "TAVILY_API_KEY": os.getenv("TAVILY_API_KEY", ""),
        
        # LangSmith
        "LANGSMITH_API_KEY": os.getenv("LANGSMITH_API_KEY", ""),
        "LANGSMITH_ENDPOINT": os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com"),
        "LANGSMITH_PROJECT": os.getenv("LANGSMITH_PROJECT", "cv-evaluator"),
        "LANGSMITH_TRACING": os.getenv("LANGSMITH_TRACING", "false").lower() == "true",

        # Deepeval
        "DEEPEVAL_API_KEY": os.getenv("DEEPEVAL_API_KEY", ""),
        "DEEPEVAL_PROJECT_ID": os.getenv("DEEPEVAL_PROJECT_ID", ""),
        "CONFIDENT_API_KEY": os.getenv("CONFIDENT_API_KEY", ""),
        "CONFIDENT_BASE_URL": os.getenv("CONFIDENT_BASE_URL", "https://eu.api.confident-ai.com"),
        
        # Rutas
        "DATA_DIR": os.path.join(os.path.dirname(os.path.dirname(__file__)), "data"),

        # Thresholds de métricas en evaluación
        "THRESHOLD_REQUIREMENT_EXTRACTION": float(os.getenv("THRESHOLD_REQUIREMENT_EXTRACTION", "0.5")),
        "THRESHOLD_CV_FAITHFULNESS": float(os.getenv("THRESHOLD_CV_FAITHFULNESS", "0.5")),
        "THRESHOLD_EVALUATION_HALLUCINATION": float(os.getenv("THRESHOLD_EVALUATION_HALLUCINATION", "0.8")),
        "THRESHOLD_INTERVIEW_COMPLETENESS": float(os.getenv("THRESHOLD_INTERVIEW_COMPLETENESS", "0.8")),
        "THRESHOLD_INTERVIEW_FAITHFULNESS": float(os.getenv("THRESHOLD_INTERVIEW_FAITHFULNESS", "0.8")),
        "THRESHOLD_INTERVIEW_HALLUCINATION": float(os.getenv("THRESHOLD_INTERVIEW_HALLUCINATION", "0.8")),
     

    }
    
    # config["EXAMPLE_OFFER_PATH"] = os.path.join(config["DATA_DIR"], "example_offer.txt")
    # # config["EXAMPLE_OFFER_PATH"] = os.path.join(config["DATA_DIR"], "velora_offer.txt")
    
    # Validar OpenAI
    if not config["OPENAI_API_KEY"]:
        raise ValueError("OPENAI_API_KEY no está configurada. Añádela al archivo .env")
    
    # Validar Google Maps
    if not config["GOOGLE_MAPS_API_KEY"]:
        raise ValueError("GOOGLE_MAPS_API_KEY no está configurada. Añádela al archivo .env")
    
    if not config["TAVILY_API_KEY"]:
        raise ValueError("TAVILY_API_KEY no está configurada. Añádela al archivo .env")
    
    # Configurar LangSmith si está habilitado
    if config["LANGSMITH_TRACING"] and config["LANGSMITH_API_KEY"]:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = config["LANGSMITH_API_KEY"]
        os.environ["LANGCHAIN_ENDPOINT"] = config["LANGSMITH_ENDPOINT"]
        os.environ["LANGCHAIN_PROJECT"] = config["LANGSMITH_PROJECT"]
        print(f"✅ LangSmith habilitado - Proyecto: {config['LANGSMITH_PROJECT']}")
    
    
    if config["DEEPEVAL_API_KEY"]:
        os.environ["DEEPEVAL_API_KEY"] = config["DEEPEVAL_API_KEY"]
        os.environ["CONFIDENT_API_KEY"] = config["CONFIDENT_API_KEY"]
        os.environ["CONFIDENT_BASE_URL"] = config["CONFIDENT_BASE_URL"]
        print("✅ Deepeval habilitado")
    

    return config