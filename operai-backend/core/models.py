from typing import List, Optional
from pydantic import BaseModel, Field, constr

# Pydantic v2: usar pattern= (no regex=)
CategoriaStr = constr(strip_whitespace=True, min_length=1, max_length=60)
FechaStr = constr(pattern=r"^\d{4}-\d{2}-\d{2}$")
PeriodoStr = constr(pattern=r"^\d{4}-\d{2}$")

# ---------- Requests ----------
class PromedioCategoriaRequest(BaseModel):
    categoria: CategoriaStr
    fecha_inicio: FechaStr
    fecha_fin: FechaStr

class BuscarPorCategoriaRequest(BaseModel):
    categoria: CategoriaStr
    fecha_inicio: FechaStr
    fecha_fin: FechaStr
    proveedor: Optional[str] = None  # el esquema actual no filtra por proveedor, se ignora

class PresupuestoRestanteRequest(BaseModel):
    categoria: CategoriaStr
    periodo: PeriodoStr
    # Bandera opcional: si es False y no hay presupuesto → 400
    permitir_sin_presupuesto: bool = False

# ---------- Responses ----------
class PromedioCategoriaResponse(BaseModel):
    monto_promedio: float = Field(..., description="Promedio de VALOR en el rango")
    cantidad_registros: int

class RegistroItem(BaseModel):
    fecha: str
    monto: float
    nombre_producto: Optional[str] = "Sin especificar"  
    Categoria: Optional[str] = None                      
    cantidad: Optional[float] = 1.0 
    proveedor: Optional[str] = None
    nro_factura: Optional[str] = None

class BuscarPorCategoriaResponse(BaseModel):
    lista_registros: List[RegistroItem]
    monto_total: float
    cantidad_registros: int

class PresupuestoRestanteResponse(BaseModel):
    presupuesto_asignado: float
    monto_ejecutado: float
    restante: float
    porcentaje_usado: float

class RegistroValor(BaseModel):
    fecha: str
    valor: float
    cantidad: float
    monto: float

class TotalCategoriaValorRequest(BaseModel):
    categoria: str
    fecha_inicio: Optional[str] = None
    fecha_fin: Optional[str] = None
    min_valor: Optional[float] = None
    max_valor: Optional[float] = None
    limit: Optional[int] = Field(None, gt=0)

class TotalCategoriaValorResponse(BaseModel):
    monto_total: float
    cantidad_registros: int
    promedio: float
    minimo: float
    maximo: float
    lista_registros: Optional[List[RegistroValor]] = None

class GoogleSheetsRequest(BaseModel):
    sheet_url: str
    sheet_name: str = None