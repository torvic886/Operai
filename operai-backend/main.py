import uvicorn
from api import create_app
from core.file_watcher import start_file_watcher
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Iniciar el watcher de archivos CSV
    csv_watch_path = os.getenv('CSV_WATCH_PATH', r'C:\agente\csv_uploads')
    
    try:
        start_file_watcher(csv_watch_path)
        logger.info(f"🔔 Watcher iniciado en: {csv_watch_path}")
        logger.info("📂 Coloca archivos CSV en esa carpeta para procesarlos automáticamente")
    except Exception as e:
        logger.error(f"❌ Error iniciando watcher: {e}")
        logger.info("⚠️ La API seguirá funcionando sin el watcher automático")
    
    # Iniciar FastAPI
    logger.info("🚀 Iniciando FastAPI en http://0.0.0.0:8000")
    uvicorn.run(create_app(), host="0.0.0.0", port=8000)