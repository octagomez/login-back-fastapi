from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

class Client(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    email: str
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    empresa: Optional[str] = None
    activo: Optional[bool] = Field(default=True)
    fecha_creacion: Optional[str] = None
    fecha_actualizacion: Optional[str] = None