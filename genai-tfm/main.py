import subprocess
import sys
import time
import signal
import os
from pathlib import Path
from dotenv import load_dotenv


# Configuración
load_dotenv()
FAST_API_API_HOST = os.getenv("FAST_API_API_HOST")
FAST_API_API_PORT = int(os.getenv("FAST_API_API_PORT"))
STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT"))
CALL_SERVICE_PORT = int(os.getenv("CALL_SERVICE_PORT", 8002))


# Paths
ROOT_DIR = Path(__file__).parent
API_FILE = ROOT_DIR / "FastAPI" / "api_server.py"
FRONTEND_FILE = ROOT_DIR / "frontend" / "frontend.py"
CALL_SERVICE_FILE = ROOT_DIR / "backend" / "call_service.py"

# Procesos y threads
processes = []
call_service_thread = None


def print_banner():
    print("\n" + "=" * 60)
    print("🍽️  FOODLOOKER - Sistema de Reservas con IA")
    print("=" * 60)
    print(f"\n🔧 Backend API:  http://localhost:{FAST_API_API_PORT}")
    print(f"📚 API Docs:     http://localhost:{FAST_API_API_PORT}/docs")
    print(f"📞 Call Service: http://localhost:{CALL_SERVICE_PORT}")
    print(f"🖥️  Frontend:     http://localhost:{STREAMLIT_PORT}")
    print("\n💡 Presiona Ctrl+C para detener todos los servicios")
    print("=" * 60 + "\n")


def start_fastapi():
    print("🚀 Iniciando FastAPI...")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT_DIR)

    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "FastAPI.api_server:app",
            "--host",
            str(FAST_API_API_HOST),
            "--port",
            str(FAST_API_API_PORT),
            "--reload",
        ],
        cwd=ROOT_DIR,
        env=env,
    )
    processes.append(process)
    return process


def start_streamlit():
    print("🚀 Iniciando Streamlit...")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT_DIR)

    # El config.toml en .streamlit/ maneja la configuración
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(FRONTEND_FILE),
        ],
        cwd=ROOT_DIR,
        env=env,
    )
    processes.append(process)
    return process


def start_call_service():
    print("🚀 Iniciando Call Service...")

    # Importar y ejecutar directamente en un thread (como en agent/main.py)
    from backend.call_service import start_service

    call_thread = start_service(CALL_SERVICE_PORT)

    if call_thread:
        print(f"✅ Call Service corriendo en puerto {CALL_SERVICE_PORT}")
        return call_thread
    else:
        print(f"❌ Error iniciando Call Service")
        return None


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
        start_fastapi()

    elif mode == "ui":
        print("\n🖥️  Iniciando solo Streamlit...\n")
        start_streamlit()

    elif mode in ["all", "both"]:
        global call_service_thread

        print_banner()

        # 1. Call Service primero (thread)
        call_service_thread = start_call_service()
        time.sleep(3)

        if not call_service_thread or not call_service_thread.is_alive():
            print("❌ Call Service no se inició correctamente. Revisa errores arriba.")
            cleanup()

        # 2. FastAPI segundo
        api_proc = start_fastapi()
        time.sleep(2)

        if api_proc.poll() is not None:
            print("❌ FastAPI se cerró inesperadamente. Revisa errores arriba.")
            cleanup()

        # 3. Streamlit tercero
        start_streamlit()

    else:
        print(f"❌ Modo desconocido: {mode}")
        print("   Uso: python main.py [all|api|ui]")
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
