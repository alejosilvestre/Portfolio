# 🐳 Instrucciones para Ejecutar con Docker

## Requisitos Previos

- Docker instalado ([Descargar aquí](https://www.docker.com/products/docker-desktop))
- API Keys de OpenAI y Google Maps

## Pasos para Ejecutar

### 1. Configurar Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto con el siguiente contenido mínimo:

```env
# API KEYS OBLIGATORIAS
OPENAI_API_KEY=sk-tu-api-key-aqui
GOOGLE_MAPS_API_KEY=tu-google-maps-key-aqui

# PUERTOS (no cambiar)
FAST_API_API_HOST=0.0.0.0
FAST_API_API_PORT=8000
STREAMLIT_PORT=8501
```

Puedes copiar `.env.example` y rellenar las API keys.

### 2. Construir la Imagen Docker

```bash
docker build -t foodlooker .
```

Este proceso puede tardar 2-3 minutos la primera vez.

### 3. Ejecutar el Contenedor

```bash
docker run -p 8000:8000 -p 8501:8501 --env-file .env foodlooker
```

### 4. Acceder a la Aplicación

Abre tu navegador en:
- **Frontend (UI)**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **Documentación API**: http://localhost:8000/docs

## Detener la Aplicación

Presiona `Ctrl+C` en la terminal donde se está ejecutando el contenedor.

## Solución de Problemas

### Error: "port is already allocated"
```bash
# Ver qué proceso usa el puerto 8000 o 8501
netstat -ano | findstr :8000
netstat -ano | findstr :8501

# Matar el proceso o cambiar puertos en .env
```

### Error: "OPENAI_API_KEY not configured"
Verifica que el archivo `.env` existe y tiene las API keys correctas.

### El contenedor se detiene inmediatamente
```bash
# Ver logs para diagnosticar
docker logs <container-id>

# O ejecutar en modo interactivo
docker run -it -p 8000:8000 -p 8501:8501 --env-file .env foodlooker
```

## Comandos Útiles

```bash
# Ver contenedores en ejecución
docker ps

# Ver todos los contenedores (incluidos detenidos)
docker ps -a

# Detener un contenedor
docker stop <container-id>

# Eliminar un contenedor
docker rm <container-id>

# Reconstruir sin caché (si hay problemas)
docker build --no-cache -t foodlooker .
```

## Prueba Rápida

Una vez que la aplicación esté corriendo:

1. Abre http://localhost:8501
2. Escribe: **"Busco una pizzería en Madrid para cenar mañana a las 21h"**
3. El agente buscará restaurantes y mostrará opciones con fotos
4. Selecciona uno y sigue el flujo de reserva

---

**¡Listo! 🎉**
