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
    def process_csv_file(file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Procesa un archivo CSV y lo carga a la base de datos
        """
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
                return {
                    "success": False,
                    "error": f"Faltan columnas requeridas: {missing_columns}",
                    "rows_processed": 0
                }
            
            # Limpiar y transformar datos
            df = UploadService._clean_dataframe(df)
            
            # Validar datos
            validation_result = UploadService._validate_dataframe(df)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": validation_result["error"],
                    "rows_processed": 0
                }
            
            # Insertar en base de datos
            engine = get_engine()
            rows_inserted = UploadService._insert_to_database(df, engine)
            
            return {
                "success": True,
                "message": f"Archivo {filename} procesado exitosamente",
                "rows_processed": rows_inserted,
                "filename": filename,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.exception("Error procesando CSV")
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
        # Convertir FECHA a formato ISO
        df['FECHA'] = pd.to_datetime(df['FECHA'], format='%Y-%m-%d', errors='coerce')
        df['FECHA'] = df['FECHA'].dt.strftime('%Y-%m-%d')
        
        # Limpiar VALOR: eliminar puntos de miles y comas decimales
        df['VALOR'] = (
            df['VALOR']
            .str.replace('.', '', regex=False)
            .str.replace(',', '.', regex=False)
            .astype(float)
        )
        
        # Limpiar CANTIDAD
        df['CANTIDAD'] = (
            df['CANTIDAD']
            .str.replace('.', '', regex=False)
            .str.replace(',', '.', regex=False)
            .astype(float)
        )
        
        # Convertir TIPO a entero
        df['TIPO'] = df['TIPO'].astype(int)
        
        # Convertir CODIGO_NUM a entero (puede tener valores muy grandes)
        df['CODIGO_NUM'] = pd.to_numeric(df['CODIGO_NUM'], errors='coerce').fillna(0).astype('int64')
        
        # Normalizar CATEGORIA a mayúsculas
        df['CATEGORIA'] = df['CATEGORIA'].str.upper().str.strip()
        
        # Limpiar espacios en NOMBRE_PRODUCTO y CODIGO
        df['NOMBRE_PRODUCTO'] = df['NOMBRE_PRODUCTO'].str.strip()
        df['CODIGO'] = df['CODIGO'].str.strip()
        df['CODIGO_LETRA'] = df['CODIGO_LETRA'].str.strip().str.upper()
        
        return df
    
    @staticmethod
    def _validate_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Valida que los datos sean correctos
        """
        # Verificar fechas nulas
        if df['FECHA'].isna().any():
            return {
                "valid": False,
                "error": "Hay fechas inválidas en el archivo"
            }
        
        # Verificar valores negativos
        if (df['VALOR'] < 0).any():
            return {
                "valid": False,
                "error": "Hay valores negativos en VALOR"
            }
        
        if (df['CANTIDAD'] < 0).any():
            return {
                "valid": False,
                "error": "Hay cantidades negativas"
            }
        
        # Verificar categorías vacías
        if df['CATEGORIA'].isna().any() or (df['CATEGORIA'] == '').any():
            return {
                "valid": False,
                "error": "Hay categorías vacías"
            }
        
        # Verificar CODIGO vacío
        if df['CODIGO'].isna().any() or (df['CODIGO'] == '').any():
            return {
                "valid": False,
                "error": "Hay códigos vacíos"
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
        
        # Asegurarse de que las columnas estén en el orden correcto
        # y que no incluya el campo 'id' (auto-increment)
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
        try:
            import gspread
            from oauth2client.service_account import ServiceAccountCredentials
            
            # Configurar credenciales
            scope = ['https://spreadsheets.google.com/feeds',
                     'https://www.googleapis.com/auth/drive']
            
            creds_path = os.getenv('GOOGLE_SHEETS_CREDENTIALS', 'credentials.json')
            
            if not os.path.exists(creds_path):
                return {
                    "success": False,
                    "error": "Archivo de credenciales de Google no encontrado",
                    "rows_processed": 0
                }
            
            creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
            client = gspread.authorize(creds)
            
            # Abrir la hoja
            sheet = client.open_by_url(sheet_url)
            worksheet = sheet.worksheet(sheet_name) if sheet_name else sheet.get_worksheet(0)
            
            # Convertir a DataFrame
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
            
            # Procesar como CSV
            df = UploadService._clean_dataframe(df)
            validation_result = UploadService._validate_dataframe(df)
            
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": validation_result["error"],
                    "rows_processed": 0
                }
            
            engine = get_engine()
            rows_inserted = UploadService._insert_to_database(df, engine)
            
            return {
                "success": True,
                "message": "Datos de Google Sheets sincronizados exitosamente",
                "rows_processed": rows_inserted,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.exception("Error sincronizando Google Sheets")
            return {
                "success": False,
                "error": str(e),
                "rows_processed": 0
            }