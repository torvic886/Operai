# AGENT/core/upload_service.py
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import logging
from typing import Dict, Any
import os
from db.connection import get_engine

logger = logging.getLogger("uvicorn.error")

class UploadService:
    
    @staticmethod
    def _log_import(engine, source: str, rows: int, filename: str = None, 
                   status: str = "SUCCESS", error: str = None):
        """
        Registra un log de importación en la base de datos
        """
        try:
            with engine.begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO import_logs 
                        (source, rows_imported, filename, status, error_message) 
                        VALUES (:source, :rows, :filename, :status, :error)
                    """),
                    {
                        "source": source,
                        "rows": rows,
                        "filename": filename,
                        "status": status,
                        "error": error
                    }
                )
                logger.info(f"📝 Log de importación registrado: {source} - {rows} filas")
        except Exception as e:
            logger.error(f"❌ Error al registrar log: {e}")
    
    @staticmethod
    def process_csv_file(file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Procesa un archivo CSV y lo carga a la base de datos
        """
        engine = get_engine()
        try:
            # Leer CSV desde bytes
            from io import BytesIO
            df = pd.read_csv(
                BytesIO(file_content),
                sep=';',
                dtype=str,
                encoding='utf-8'
            )
            
            logger.info(f"CSV leído: {len(df)} filas, columnas: {list(df.columns)}")
            
            # Validar columnas requeridas
            required_columns = ['CODIGO', 'FECHA', 'CATEGORIA', 'CODIGO_LETRA', 'CODIGO_NUM', 
                              'NOMBRE_PRODUCTO', 'TIPO', 'VALOR', 'CANTIDAD']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                error_msg = f"Faltan columnas requeridas: {missing_columns}"
                UploadService._log_import(engine, "CSV", 0, filename, "ERROR", error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "rows_processed": 0
                }
            
            # Limpiar y transformar datos
            df = UploadService._clean_dataframe(df)
            
            # Validar datos
            validation_result = UploadService._validate_dataframe(df)
            if not validation_result["valid"]:
                UploadService._log_import(engine, "CSV", 0, filename, "ERROR", validation_result["error"])
                return {
                    "success": False,
                    "error": validation_result["error"],
                    "rows_processed": 0
                }
            
            # Insertar en base de datos
            rows_inserted = UploadService._insert_to_database(df, engine)
            
            # Registrar log exitoso
            UploadService._log_import(engine, "CSV", rows_inserted, filename, "SUCCESS")
            
            return {
                "success": True,
                "message": f"Archivo {filename} procesado exitosamente",
                "rows_processed": rows_inserted,
                "filename": filename,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.exception("Error procesando CSV")
            UploadService._log_import(engine, "CSV", 0, filename, "ERROR", str(e))
            return {
                "success": False,
                "error": str(e),
                "rows_processed": 0
            }
    
    @staticmethod
    def _clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpia y transforma el DataFrame
        """
        # Convertir FECHA a formato ISO con múltiples formatos posibles
        date_formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d', '%d-%m-%Y']
        
        def parse_date(date_str):
            """Intenta parsear la fecha con múltiples formatos"""
            if pd.isna(date_str) or date_str == '' or date_str is None:
                return None
                
            date_str = str(date_str).strip()
            
            # Intentar cada formato
            for fmt in date_formats:
                try:
                    parsed_date = pd.to_datetime(date_str, format=fmt)
                    return parsed_date.strftime('%Y-%m-%d')
                except:
                    continue
            
            # Si ningún formato funciona, intentar inferir automáticamente
            try:
                parsed_date = pd.to_datetime(date_str, dayfirst=True)
                return parsed_date.strftime('%Y-%m-%d')
            except:
                logger.warning(f"⚠️ No se pudo parsear fecha: '{date_str}'")
                return None
        
        # Aplicar conversión de fechas
        df['FECHA'] = df['FECHA'].apply(parse_date)
        
        # Limpiar VALOR
        df['VALOR'] = (
            df['VALOR']
            .astype(str)
            .str.replace('.', '', regex=False)
            .str.replace(',', '.', regex=False)
            .str.replace('$', '', regex=False)
            .str.strip()
        )
        df['VALOR'] = pd.to_numeric(df['VALOR'], errors='coerce').fillna(0)
        
        # Limpiar CANTIDAD
        df['CANTIDAD'] = (
            df['CANTIDAD']
            .astype(str)
            .str.replace('.', '', regex=False)
            .str.replace(',', '.', regex=False)
            .str.strip()
        )
        df['CANTIDAD'] = pd.to_numeric(df['CANTIDAD'], errors='coerce').fillna(1)
        
        # Convertir TIPO a entero
        df['TIPO'] = pd.to_numeric(df['TIPO'], errors='coerce').fillna(0).astype(int)
        
        # Convertir CODIGO_NUM a entero
        df['CODIGO_NUM'] = pd.to_numeric(df['CODIGO_NUM'], errors='coerce').fillna(0).astype(int)
        
        # Normalizar CATEGORIA
        df['CATEGORIA'] = df['CATEGORIA'].str.upper().str.strip()
        
        # Limpiar espacios
        df['NOMBRE_PRODUCTO'] = df['NOMBRE_PRODUCTO'].str.strip()
        df['CODIGO'] = df['CODIGO'].str.strip()
        df['CODIGO_LETRA'] = df['CODIGO_LETRA'].str.strip().str.upper()
        
        return df
    
    @staticmethod
    def _validate_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Valida que los datos sean correctos
        """
        # Validar fechas
        invalid_dates = df[df['FECHA'].isna()]
        if not invalid_dates.empty:
            invalid_rows = invalid_dates.index.tolist()[:5]
            return {
                "valid": False, 
                "error": f"Hay fechas inválidas en las filas: {invalid_rows}. Formatos aceptados: YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY"
            }
        
        # Validar valores
        if (df['VALOR'] < 0).any():
            invalid_rows = df[df['VALOR'] < 0].index.tolist()[:5]
            return {
                "valid": False, 
                "error": f"Hay valores negativos en VALOR en las filas: {invalid_rows}"
            }
        
        # Validar cantidades
        if (df['CANTIDAD'] <= 0).any():
            invalid_rows = df[df['CANTIDAD'] <= 0].index.tolist()[:5]
            return {
                "valid": False, 
                "error": f"Hay cantidades inválidas (<=0) en las filas: {invalid_rows}"
            }
        
        # Validar categorías
        empty_categories = df[(df['CATEGORIA'].isna()) | (df['CATEGORIA'] == '')]
        if not empty_categories.empty:
            invalid_rows = empty_categories.index.tolist()[:5]
            return {
                "valid": False, 
                "error": f"Hay categorías vacías en las filas: {invalid_rows}"
            }
        
        # Validar códigos
        empty_codes = df[(df['CODIGO'].isna()) | (df['CODIGO'] == '')]
        if not empty_codes.empty:
            invalid_rows = empty_codes.index.tolist()[:5]
            return {
                "valid": False, 
                "error": f"Hay códigos vacíos en las filas: {invalid_rows}"
            }
        
        return {"valid": True}
    
    @staticmethod
    def _insert_to_database(df: pd.DataFrame, engine) -> int:
        """
        Inserta el DataFrame en la base de datos
        """
        rows_before = 0
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) as count FROM gastos"))
            rows_before = result.scalar()
        
        # Orden de columnas
        columns_order = ['CODIGO', 'FECHA', 'CATEGORIA', 'CODIGO_LETRA', 'CODIGO_NUM',
                        'NOMBRE_PRODUCTO', 'TIPO', 'VALOR', 'CANTIDAD']
        
        df_to_insert = df[columns_order]
        
        # Insertar datos
        df_to_insert.to_sql(
            name='gastos',
            con=engine,
            if_exists='append',
            index=False,
            chunksize=1000
        )
        
        rows_after = 0
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) as count FROM gastos"))
            rows_after = result.scalar()
        
        return rows_after - rows_before
    
    @staticmethod
    def sync_from_google_sheets(sheet_url: str, sheet_name: str = None) -> Dict[str, Any]:
        """
        Sincroniza datos desde Google Sheets
        """
        engine = get_engine()
        try:
            import gspread
            from oauth2client.service_account import ServiceAccountCredentials
            
            scope = ['https://spreadsheets.google.com/feeds',
                     'https://www.googleapis.com/auth/drive']
            
            creds_path = os.getenv('GOOGLE_SHEETS_CREDENTIALS', 'credentials.json')
            
            if not os.path.exists(creds_path):
                error_msg = "Archivo de credenciales de Google no encontrado"
                UploadService._log_import(engine, "Google Sheets", 0, sheet_url, "ERROR", error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "rows_processed": 0
                }
            
            creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
            client = gspread.authorize(creds)
            
            sheet = client.open_by_url(sheet_url)
            worksheet = sheet.worksheet(sheet_name) if sheet_name else sheet.get_worksheet(0)
            
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
            
            df = UploadService._clean_dataframe(df)
            validation_result = UploadService._validate_dataframe(df)
            
            if not validation_result["valid"]:
                UploadService._log_import(engine, "Google Sheets", 0, sheet_url, "ERROR", validation_result["error"])
                return {
                    "success": False,
                    "error": validation_result["error"],
                    "rows_processed": 0
                }
            
            rows_inserted = UploadService._insert_to_database(df, engine)
            
            # Registrar log exitoso
            UploadService._log_import(engine, "Google Sheets", rows_inserted, sheet_url, "SUCCESS")
            
            return {
                "success": True,
                "message": "Datos de Google Sheets sincronizados exitosamente",
                "rows_processed": rows_inserted,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.exception("Error sincronizando Google Sheets")
            UploadService._log_import(engine, "Google Sheets", 0, sheet_url, "ERROR", str(e))
            return {
                "success": False,
                "error": str(e),
                "rows_processed": 0
            }