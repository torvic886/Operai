# AGENT/core/file_watcher.py
import time
import os
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from core.upload_service import UploadService

logger = logging.getLogger("uvicorn.error")

class CSVHandler(FileSystemEventHandler):
    """
    Handler que detecta nuevos archivos CSV
    """
    def __init__(self):
        self.processed_files = set()
    
    def on_created(self, event):
        if event.is_directory:
            return
        
        if event.src_path.endswith('.csv'):
            # Esperar un poco para asegurar que el archivo está completamente escrito
            time.sleep(1)
            
            file_path = event.src_path
            if file_path not in self.processed_files:
                logger.info(f"🔔 Nuevo archivo CSV detectado: {file_path}")
                self.process_csv(file_path)
                self.processed_files.add(file_path)
    
    def process_csv(self, file_path: str):
        """
        Procesa el archivo CSV detectado
        """
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            filename = os.path.basename(file_path)
            result = UploadService.process_csv_file(content, filename)
            
            if result["success"]:
                logger.info(f"✅ Archivo {filename} procesado: {result['rows_processed']} filas")
                
                # Opcional: mover archivo a carpeta "procesados"
                processed_dir = os.path.join(os.path.dirname(file_path), 'procesados')
                os.makedirs(processed_dir, exist_ok=True)
                
                new_path = os.path.join(processed_dir, filename)
                os.rename(file_path, new_path)
                logger.info(f"📦 Archivo movido a: {new_path}")
            else:
                logger.error(f"❌ Error procesando {filename}: {result['error']}")
                
        except Exception as e:
            logger.exception(f"Error procesando archivo {file_path}")

class FileWatcher:
    """
    Observador de carpeta para detectar nuevos CSVs
    """
    def __init__(self, watch_path: str):
        self.watch_path = watch_path
        self.observer = Observer()
        self.handler = CSVHandler()
    
    def start(self):
        """
        Inicia el monitoreo de la carpeta
        """
        if not os.path.exists(self.watch_path):
            os.makedirs(self.watch_path)
            logger.info(f"📁 Carpeta creada: {self.watch_path}")
        
        self.observer.schedule(self.handler, self.watch_path, recursive=False)
        self.observer.start()
        logger.info(f"👁️ Monitoreando carpeta: {self.watch_path}")
    
    def stop(self):
        """
        Detiene el monitoreo
        """
        self.observer.stop()
        self.observer.join()
        logger.info("🛑 Monitoreo detenido")

# Singleton para uso global
_watcher_instance = None

def start_file_watcher(watch_path: str = None):
    """
    Inicia el watcher en la carpeta especificada
    """
    global _watcher_instance
    
    if watch_path is None:
        watch_path = os.getenv('CSV_WATCH_PATH', r'C:\agente\csv_uploads')
    
    if _watcher_instance is None:
        _watcher_instance = FileWatcher(watch_path)
        _watcher_instance.start()
    
    return _watcher_instance

def stop_file_watcher():
    """
    Detiene el watcher
    """
    global _watcher_instance
    if _watcher_instance:
        _watcher_instance.stop()
        _watcher_instance = None