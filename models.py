from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

class UserTaskLink(SQLModel, table=True):
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", primary_key=True)
    task_id: Optional[int] = Field(default=None, foreign_key="task.id", primary_key=True)

class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    users: List["User"] = Relationship(back_populates="tasks", link_model=UserTaskLink)

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str
    password: str  # Campo para la contraseña
    tasks: List["Task"] = Relationship(back_populates="users", link_model=UserTaskLink)

class Cliente(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    email: str
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    empresa: Optional[str] = None
    activo: bool = Field(default=True)
    fecha_creacion: Optional[str] = None
    fecha_actualizacion: Optional[str] = None

Task.update_forward_refs()
UserTaskLink.update_forward_refs()
