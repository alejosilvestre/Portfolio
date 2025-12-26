"""
run.py - Script de ejecución del agente
"""
import sys
from pathlib import Path

# Añadir la raíz del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Ahora importar y ejecutar
from agent.agent_main import main

if __name__ == "__main__":
    main()