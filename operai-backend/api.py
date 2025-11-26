from sqlalchemy import text
import logging
from core.sheets_sync import GoogleSheetsSync as SheetsService
from chat_router import router as chat_router
from db.connection import get_engine
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from core.models import (
    PromedioCategoriaRequest, PromedioCategoriaResponse,
    BuscarPorCategoriaRequest, BuscarPorCategoriaResponse,
    PresupuestoRestanteRequest, PresupuestoRestanteResponse,
    TotalCategoriaValorRequest, TotalCategoriaValorResponse
)
from core import services

from fastapi import FastAPI, HTTPException, UploadFile, File
from core.upload_service import UploadService
from core.upload_service import UploadService
from core.sheets_sync import GoogleSheetsSync as SheetsService
from pydantic import BaseModel


def create_app() -> FastAPI:
    app = FastAPI(title="OperAI Tools API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], allow_credentials=True,
        allow_methods=["*"], allow_headers=["*"],
    )

    logger = logging.getLogger("uvicorn.error")

    # ======================= MODELOS LOCALES ============================
    class GoogleSheetsRequest(BaseModel):
        sheet_url: str
        sheet_name: str = None    

    # ======================= HEALTH APP ============================
    @app.get("/api/health/app")
    def health_app():
        return {"status": "ok", "service": "OperAI Tools API", "version": "0.1.0"}

    # ======================= POST ===========================
    @app.post("/api/tools/promedio_categoria", response_model=PromedioCategoriaResponse)
    def promedio_categoria(req: PromedioCategoriaRequest):
        try:
            return services.promedio_categoria(req)
        except services.DomainError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception:
            raise HTTPException(status_code=500, detail="Error interno")

    @app.post("/api/tools/total_categoria_valor", response_model=TotalCategoriaValorResponse)
    def total_categoria_valor_post(req: TotalCategoriaValorRequest):
        try:
            return services.total_categoria_valor(req)
        except services.DomainError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception:
            raise HTTPException(status_code=500, detail="Error interno al calcular total por categoría")

    @app.post("/api/upload/csv")
    async def upload_csv(file: UploadFile = File(...)):
        """
        Endpoint para subir archivos CSV
        """
        try:
            # Validar que sea CSV
            if not file.filename.endswith('.csv'):
                raise HTTPException(status_code=400, detail="Solo se permiten archivos CSV")
            
            # Leer contenido del archivo
            contents = await file.read()
            
            # Procesar CSV
            result = UploadService.process_csv_file(contents, file.filename)
            
            if not result["success"]:
                raise HTTPException(status_code=400, detail=result["error"])
            
            return result
            
        except Exception as e:
            logger.exception("Error en upload CSV")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/sync/google-sheets")
    def sync_google_sheets(payload: GoogleSheetsRequest):
        try:
            result = UploadService.sync_from_google_sheets(
                payload.sheet_url,
                payload.sheet_name
            )
            if not result["success"]:
                raise HTTPException(status_code=400, detail=result["error"])
            return result
        except Exception as e:
            logger.exception("Error sincronizando Google Sheets")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/sync/export-to-sheets")
    def export_to_google_sheets(payload: GoogleSheetsRequest):
        """
        Exporta datos de MySQL a Google Sheets
        """
        try:
            result = SheetsService.export_to_google_sheets(
                payload.sheet_url,
                payload.sheet_name
            )
            
            if not result["success"]:
                raise HTTPException(status_code=400, detail=result["error"])
            
            return result
            
        except Exception as e:
            logger.exception("Error exportando a Google Sheets")
            raise HTTPException(status_code=500, detail=str(e))

    # ======================= GET ============================
    @app.get("/api/tools/promedio_categoria")
    def promedio_categoria_get(categoria: str, fecha_inicio: str, fecha_fin: str):
        try:
            # ⬇⬇⬇ usar el modelo importado, no services.*
            req = PromedioCategoriaRequest(
                categoria=categoria, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
            )
            return services.promedio_categoria(req)
        except services.DomainError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception:
            raise HTTPException(status_code=500, detail="Error interno al calcular el promedio por categoría")

    @app.get("/api/tools/buscar_por_categoria")
    def buscar_por_categoria_get(categoria: str, fecha_inicio: str, fecha_fin: str, proveedor: str | None = None):
        try:
            # ⬇⬇⬇ usar el modelo importado, no services.*
            req = BuscarPorCategoriaRequest(
                categoria=categoria, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, proveedor=proveedor
            )
            return services.buscar_por_categoria(req)
        except Exception:
            logger.exception("falló buscar_por_categoria_get")   # <-- imprime traceback en consola
            raise HTTPException(status_code=500, detail="Error interno al buscar por categoría")

    @app.get("/api/tools/total_categoria_valor", response_model=TotalCategoriaValorResponse)
    def total_categoria_valor_get(
        categoria: str,
        fecha_inicio: str = None,
        fecha_fin: str = None,
        min_valor: float = None,
        max_valor: float = None,
        limit: int = None
    ):
        try:
            req = TotalCategoriaValorRequest(
                categoria=categoria,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                min_valor=min_valor,
                max_valor=max_valor,
                limit=limit
            )
            return services.total_categoria_valor(req)
        except services.DomainError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error interno al calcular total por categoría: {e}")

    @app.get("/api/tools/categorias")
    def listar_categorias():
        try:
            engine = get_engine()
            with engine.connect() as conn:
                result = conn.execute(
                    text("SELECT DISTINCT CATEGORIA FROM gastos ORDER BY CATEGORIA")
                ).fetchall()
            categorias = [row[0] for row in result]
            return {"categorias": categorias}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error: {e}")
        
    @app.get("/api/upload/stats")
    def get_upload_stats():
        """
        Obtiene estadísticas de la base de datos incluyendo logs de importación
        """
        try:
            engine = get_engine()
            with engine.connect() as conn:
                # Total de registros
                total = conn.execute(text("SELECT COUNT(*) as count FROM gastos")).scalar()
                
                # Registros por categoría
                result = conn.execute(text("""
                    SELECT CATEGORIA, COUNT(*) as count 
                    FROM gastos 
                    GROUP BY CATEGORIA 
                    ORDER BY count DESC
                """))
                by_category = [{"categoria": row[0], "count": row[1]} for row in result]
                
                # Última importación
                result = conn.execute(text("""
                    SELECT import_date, source, rows_imported, filename, status
                    FROM import_logs 
                    ORDER BY import_date DESC 
                    LIMIT 1
                """))
                last_import = result.fetchone()
                
                # Total importado
                result = conn.execute(text("""
                    SELECT SUM(rows_imported) as total_imported,
                        COUNT(*) as total_imports
                    FROM import_logs
                    WHERE status = 'SUCCESS'
                """))
                import_stats = result.fetchone()
                
                # Historial de importaciones recientes (últimas 10)
                result = conn.execute(text("""
                    SELECT import_date, source, rows_imported, filename, status
                    FROM import_logs
                    ORDER BY import_date DESC
                    LIMIT 10
                """))
                import_history = []
                for row in result:
                    import_history.append({
                        "date": row[0].isoformat() if row[0] else None,
                        "source": row[1],
                        "rows": row[2],
                        "filename": row[3],
                        "status": row[4]
                    })
                
            return {
                "total_records": total,
                "by_category": by_category,
                "last_import": {
                    "date": last_import[0].isoformat() if last_import and last_import[0] else None,
                    "source": last_import[1] if last_import else None,
                    "rows": last_import[2] if last_import else 0,
                    "filename": last_import[3] if last_import else None,
                    "status": last_import[4] if last_import else None
                } if last_import else None,
                "import_stats": {
                    "total_imported": import_stats[0] or 0,
                    "total_imports": import_stats[1] or 0
                } if import_stats else None,
                "import_history": import_history
            }
            
        except Exception as e:
            logger.exception("Error obteniendo estadísticas")
            raise HTTPException(status_code=500, detail=str(e))        

    # ======================= HEALTH CHECK ============================
    @app.get("/api/health/db")
    def health_db():
        try:
            engine = get_engine()
            with engine.connect() as conn:
                # Consulta ligera para validar conexión y contexto
                row = conn.execute(
                    text("SELECT current_user() AS user, database() AS db, @@hostname AS host")
                ).mappings().one()
            return {
                "status": "ok",
                "mysql_user": row["user"],
                "mysql_db": row["db"],
                "mysql_host": row["host"],
            }
        except Exception as e:
            # No exponemos detalles sensibles, pero devolvemos motivo general
            return {"status": "error", "detail": str(e)}
        

    @app.get("/api/tools/productos_caros")
    def productos_caros_get(limit: int = 10):
        try:
            return services.productos_caros(limit)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error interno: {e}")


    @app.get("/api/tools/presupuesto_restante")
    def presupuesto_restante_get(categoria: str, periodo: str, permitir_sin_presupuesto: bool = False):
        try:
            # ⬇⬇⬇ usar el modelo importado, no services.*
            req = PresupuestoRestanteRequest(
                categoria=categoria, periodo=periodo, permitir_sin_presupuesto=permitir_sin_presupuesto
            )
            return services.presupuesto_restante(req)
        except Exception:
            logger.exception("falló presupuesto_restante_get")   # <-- imprime traceback en consola
            raise HTTPException(status_code=500, detail="Error interno al consultar presupuesto restante")

    app.include_router(chat_router)
    return app
