import uvicorn
from api import create_app
from core.file_watcher import start_file_watcher
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("   🚀 INICIANDO OPERAI BACKEND")
    logger.info("=" * 60)
    
    # Iniciar el watcher de archivos CSV
    csv_watch_path = os.getenv('CSV_WATCH_PATH', r'C:\agente\csv_uploads')
    
    try:
        start_file_watcher(csv_watch_path)
        logger.info(f"🔔 Watcher iniciado en: {csv_watch_path}")
        logger.info("📂 Coloca archivos CSV en esa carpeta para procesarlos automáticamente")
    except Exception as e:
        logger.error(f"❌ Error iniciando watcher: {e}")
        logger.info("⚠️ La API seguirá funcionando sin el watcher automático")
    
    logger.info("")
    logger.info("📡 Endpoints disponibles:")
    logger.info("   • FastAPI:   http://localhost:8000")
    logger.info("   • Docs:      http://localhost:8000/docs")
    logger.info("   • Chat IA:   http://localhost:8000/chat")
    logger.info("")
    logger.info("🎨 Para iniciar Streamlit:")
    logger.info("   Windows:  run_streamlit.bat")
    logger.info("   Linux:    ./run_streamlit.sh")
    logger.info("")
    logger.info("=" * 60)
    
    # Iniciar FastAPI
    uvicorn.run(create_app(), host="0.0.0.0", port=8000)