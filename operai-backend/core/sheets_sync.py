# AGENT/core/sheets_sync.py
import os
import logging
from typing import Dict, Any
import pandas as pd
from sqlalchemy import text
from db.connection import get_engine
from datetime import datetime, date

logger = logging.getLogger("uvicorn.error")

class GoogleSheetsSync:
    
    @staticmethod
    def _log_export(engine, rows: int, sheet_url: str, status: str = "SUCCESS", error: str = None):
        """
        Registra un log de exportación en la base de datos
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
                        "source": "Google Sheets Export",
                        "rows": rows,
                        "filename": sheet_url,
                        "status": status,
                        "error": error
                    }
                )
            logger.info(f"📝 Log de exportación registrado: {rows} filas")
        except Exception as e:
            logger.error(f"❌ Error al registrar log de exportación: {e}")
    
    @staticmethod
    def export_to_google_sheets(sheet_url: str, sheet_name: str = None) -> Dict[str, Any]:
        """
        Exporta TODOS los datos de MySQL a Google Sheets
        """
        engine = get_engine()
        
        try:
            import gspread
            from oauth2client.service_account import ServiceAccountCredentials
            
            # Configurar credenciales
            scope = ['https://spreadsheets.google.com/feeds',
                     'https://www.googleapis.com/auth/drive']
            
            creds_path = os.getenv('GOOGLE_SHEETS_CREDENTIALS', 'credentials.json')
            
            if not os.path.exists(creds_path):
                error_msg = "Archivo de credenciales de Google no encontrado. Por favor configura credentials.json"
                GoogleSheetsSync._log_export(engine, 0, sheet_url, "ERROR", error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "rows_exported": 0
                }
            
            logger.info("📊 Obteniendo TODOS los registros de MySQL...")
            
            # Obtener TODOS los datos de MySQL
            query = """
                SELECT CODIGO, FECHA, CATEGORIA, CODIGO_LETRA, CODIGO_NUM,
                       NOMBRE_PRODUCTO, TIPO, VALOR, CANTIDAD
                FROM gastos
                ORDER BY FECHA DESC, id DESC
            """
            
            df = pd.read_sql(query, engine)
            total_rows = len(df)
            logger.info(f"✅ {total_rows} registros obtenidos de MySQL")
            
            if total_rows == 0:
                error_msg = "No hay datos para exportar en la base de datos"
                GoogleSheetsSync._log_export(engine, 0, sheet_url, "ERROR", error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "rows_exported": 0
                }
            
            # Conectar a Google Sheets
            logger.info("🔐 Conectando a Google Sheets...")
            creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
            client = gspread.authorize(creds)
            
            # Abrir la hoja
            logger.info(f"📄 Abriendo hoja: {sheet_url}")
            sheet = client.open_by_url(sheet_url)
            
            # Obtener o crear la worksheet
            try:
                if sheet_name:
                    worksheet = sheet.worksheet(sheet_name)
                    logger.info(f"✅ Hoja '{sheet_name}' encontrada")
                else:
                    worksheet = sheet.get_worksheet(0)
                    logger.info(f"✅ Usando primera hoja: '{worksheet.title}'")
            except Exception as e:
                logger.info(f"⚠️ Hoja no encontrada, creando nueva...")
                worksheet = sheet.add_worksheet(title=sheet_name or "Gastos", rows="1000", cols="20")
                logger.info(f"✅ Hoja '{worksheet.title}' creada")
            
            # Limpiar la hoja completamente
            logger.info("🧹 Limpiando hoja existente...")
            worksheet.clear()
            
            # Preparar datos para exportación
            headers = df.columns.tolist()
            data = df.values.tolist()
            
            # Convertir valores a string para evitar problemas de formato
            # Convertir valores con la lógica correcta para evitar problemas de formato
            data_str = []
            for row in data:
                row_str = []
                for val in row:
                    # 1. Manejar None y NaN
                    if val is None or pd.isna(val):
                        row_str.append('')
                    # 2. Manejar fechas (pd.Timestamp, datetime, date)
                    elif isinstance(val, (pd.Timestamp, datetime, date)):
                        row_str.append(val.strftime("%Y-%m-%d"))
                    # 3. Manejar floats
                    elif isinstance(val, float):
                        if val.is_integer():
                            # Float entero: 8000.0 → "8000"
                            row_str.append(str(int(val)))
                        else:
                            # Float con decimales: redondear a 2 decimales
                            row_str.append(str(round(val, 2)))
                    # 4. Todo lo demás (strings, ints, etc.)
                    else:
                        row_str.append(str(val))
                
                data_str.append(row_str)
            
            # Crear tabla completa (encabezados + datos)
            all_data = [headers] + data_str
            
            logger.info(f"📤 Exportando {total_rows} registros a Google Sheets...")
            
            # Exportar TODO de una vez (más eficiente que fila por fila)
            worksheet.update('A1', all_data, value_input_option='USER_ENTERED')
            
            # Formatear encabezados (opcional pero se ve bonito)
            try:
                worksheet.format('A1:I1', {
                    "backgroundColor": {"red": 0.08, "green": 0.72, "blue": 0.65},
                    "textFormat": {
                        "foregroundColor": {"red": 1, "green": 1, "blue": 1},
                        "bold": True
                    },
                    "horizontalAlignment": "CENTER"
                })
                
                # Congelar primera fila
                worksheet.freeze(rows=1)
                
                logger.info("🎨 Formato aplicado correctamente")
            except Exception as format_error:
                logger.warning(f"⚠️ No se pudo aplicar formato: {format_error}")
            
            logger.info(f"✅ {total_rows} registros exportados exitosamente")
            
            # 🔥 AGREGAR LOG DE EXPORTACIÓN - ESTO ES LO QUE FALTABA
            GoogleSheetsSync._log_export(engine, total_rows, sheet_url, "SUCCESS", None)
            
            return {
                "success": True,
                "message": f"Todos los registros ({total_rows}) exportados exitosamente",
                "rows_exported": total_rows,
                "sheet_url": sheet_url,
                "sheet_name": worksheet.title,
                "timestamp": datetime.now().isoformat()
            }
            
        except gspread.exceptions.SpreadsheetNotFound:
            logger.error("❌ Hoja de cálculo no encontrada")
            error_msg = "No se encontró la hoja de Google Sheets. Verifica que la URL sea correcta y que tengas permisos de edición."
            GoogleSheetsSync._log_export(engine, 0, sheet_url, "ERROR", error_msg)
            return {
                "success": False,
                "error": error_msg,
                "rows_exported": 0
            }
        except gspread.exceptions.APIError as e:
            logger.error(f"❌ Error de API de Google: {e}")
            error_msg = f"Error de API de Google Sheets: {str(e)}. Verifica que las credenciales tengan permisos suficientes."
            GoogleSheetsSync._log_export(engine, 0, sheet_url, "ERROR", error_msg)
            return {
                "success": False,
                "error": error_msg,
                "rows_exported": 0
            }
        except Exception as e:
            logger.exception("❌ Error exportando a Google Sheets")
            error_msg = f"Error inesperado: {str(e)}"
            GoogleSheetsSync._log_export(engine, 0, sheet_url, "ERROR", error_msg)
            return {
                "success": False,
                "error": error_msg,
                "rows_exported": 0
            }