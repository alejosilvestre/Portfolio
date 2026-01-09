import subprocess
import sys
import time
import signal
import os
from pathlib import Path

# Configuración
API_HOST = "0.0.0.0"
API_PORT = 8000  # puerto seguro no protegido en Windows
STREAMLIT_PORT = 8501

# Paths
ROOT_DIR = Path(__file__).parent
API_FILE = ROOT_DIR / "FastAPI" / "api_server.py"
FRONTEND_FILE = ROOT_DIR / "frontend" / "frontend.py"

# Procesos
processes = []


def print_banner():
    print("\n" + "=" * 60)
    print("🍽️  FOODLOOKER - Sistema de Reservas con IA")
    print("=" * 60)
    print(f"\n🔧 Backend API:  http://localhost:{API_PORT}")
    print(f"📚 API Docs:     http://localhost:{API_PORT}/docs")
    print(f"🖥️  Frontend:     http://localhost:{STREAMLIT_PORT}")
    print("\n💡 Presiona Ctrl+C para detener todos los servicios")
    print("=" * 60 + "\n")


def start_api():
    print("🚀 Iniciando FastAPI...")
    
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT_DIR)

    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "FastAPI.api_server:app",
         "--host", API_HOST,
         "--port", str(API_PORT),
         "--reload"],
        cwd=ROOT_DIR,
        env=env
    )
    processes.append(process)
    return process


def start_streamlit():
    print("🚀 Iniciando Streamlit...")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT_DIR)

    process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run",
         str(FRONTEND_FILE),
         "--server.port", str(STREAMLIT_PORT),
         "--server.headless", "true"],
        cwd=ROOT_DIR,
        env=env
    )
    processes.append(process)
    return process


def cleanup(signum=None, frame=None):
    print("\n\n🛑 Deteniendo servicios...")
    
    for process in processes:
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            process.kill()
    
    print("✅ Servicios detenidos\n")
    sys.exit(0)


def main():
    # Handlers de apagado
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    # Parsear argumentos
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"

    if mode == "api":
        print("\n🔧 Iniciando solo FastAPI...\n")
        start_api()

    elif mode == "ui":
        print("\n🖥️  Iniciando solo Streamlit...\n")
        start_streamlit()

    elif mode in ["all", "both"]:
        print_banner()

        # 1. FastAPI primero
        api_proc = start_api()

        # Esperar a que levante
        time.sleep(2)

        # Verificar que no murió al arrancar
        if api_proc.poll() is not None:
            print("❌ FastAPI se cerró inesperadamente. Revisa errores arriba.")
            cleanup()

        # 2. Streamlit segundo
        start_streamlit()

    else:
        print(f"❌ Modo desconocido: {mode}")
        print("   Uso: python run.py [all|api|ui]")
        sys.exit(1)

    # Mantener vivo monitorizando procesos
    try:
        while True:
            for process in processes:
                if process.poll() is not None:
                    print("⚠️  Un proceso terminó inesperadamente")
                    cleanup()
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    main()
