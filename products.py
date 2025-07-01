from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

class Product(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    nombre: str
    descripcion: Optional[str] = None
    categoria: Optional[str] = None
    subcategoria: Optional[str] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
    precio: Optional[float] = None
    activo: bool = Field(default=True)
    fecha_creacion: Optional[str] = None
    fecha_actualizacion: Optional[str] = None