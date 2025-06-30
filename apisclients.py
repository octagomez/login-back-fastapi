from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select, Session
from clients import Client
from database import get_session
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from models import User
from apis import get_current_user
from pydantic import BaseModel
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

SECRET_KEY = "supersecretkey"  # Cambia esto en producción
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

router_clients = APIRouter()

class ClientCreate(BaseModel):
    nombre: str
    email: str
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    empresa: Optional[str] = None
    activo: bool = Field(default=True)
    fecha_creacion: Optional[str] = None
    fecha_actualizacion: Optional[str] = None

class ClientUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    empresa: Optional[str] = None
    activo: Optional[bool] = None

@router_clients.get("/health")
def health_check(session: Session = Depends(get_session)):
    try:
        result = session.exec(select(Client).limit(1)).all()
        return {"status": "healthy", "message": "Base de datos funcionando correctamente", "tabla_Clients": "existe"}
    except Exception as e:
        return {"status": "unhealthy", "message": f"Error en base de datos: {str(e)}", "tabla_Clients": "no existe"}

@router_clients.post("/clients", response_model=Client)
def create_client(client_data: ClientCreate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    print(f"Datos recibidos: {client_data}")
    existing_client = session.exec(select(Client).where(Client.email == client_data.email)).first()
    if existing_client:
        raise HTTPException(status_code=400, detail="Ya existe un Client con ese email")
    try:
        db_client = Client(
            nombre=client_data.nombre,
            email=client_data.email,
            telefono=client_data.telefono,
            direccion=client_data.direccion,
            empresa=client_data.empresa,
            activo=client_data.activo,
            fecha_creacion=datetime.now().isoformat(),
            fecha_actualizacion=datetime.now().isoformat()
        )
        print(f"Client a crear: {db_client}")
        session.add(db_client)
        session.commit()
        session.refresh(db_client)
        return db_client
    except Exception as e:
        print(f"Error al crear Client: {e}")
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router_clients.put("/clients/{client_id}", response_model=Client)
def update_client(client_id: int, client_update: ClientUpdate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    client_db = session.get(Client, client_id)
    if not client_db:
        raise HTTPException(status_code=404, detail="Client no encontrado")
    if client_update.email and client_update.email != client_db.email:
        existing_client = session.exec(select(Client).where(Client.email == client_update.email)).first()
        if existing_client:
            raise HTTPException(status_code=400, detail="Ya existe un Client con ese email")
    update_data = client_update.dict(exclude_unset=True)
    update_data["fecha_actualizacion"] = datetime.now().isoformat()
    for field, value in update_data.items():
        setattr(client_db, field, value)
    session.add(client_db)
    session.commit()
    session.refresh(client_db)
    return client_db

@router_clients.get("/clients", response_model=List[Client])
def get_Clients(skip: int = 0, limit: int = 100, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    Clients = session.exec(select(Client).offset(skip).limit(limit)).all()
    return Clients

@router_clients.get("/clients/{Client_id}", response_model=Client)
def get_Client(Client_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    Client = session.get(Client, Client_id)
    if not Client:
        raise HTTPException(status_code=404, detail="Client no encontrado")
    return Client


@router_clients.delete("/clients/{Client_id}")
def delete_Client(Client_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    Client = session.get(Client, Client_id)
    if not Client:
        raise HTTPException(status_code=404, detail="Client no encontrado")
    session.delete(Client)
    session.commit()
    return {"message": "Client eliminado exitosamente"}

@router_clients.get("/clients/activos", response_model=List[Client])
def get_Clients_activos(skip: int = 0, limit: int = 100, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    Clients = session.exec(select(Client).where(Client.activo == True).offset(skip).limit(limit)).all()
    return Clients

@router_clients.post("/clients/{Client_id}/activar")
def activar_Client(Client_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    Client = session.get(Client, Client_id)
    if not Client:
        raise HTTPException(status_code=404, detail="Client no encontrado")
    Client.activo = True
    Client.fecha_actualizacion = datetime.now().isoformat()
    session.add(Client)
    session.commit()
    return {"message": "Client activado exitosamente"}

@router_clients.post("/clients/{Client_id}/desactivar")
def desactivar_Client(Client_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    Client = session.get(Client, Client_id)
    if not Client:
        raise HTTPException(status_code=404, detail="Client no encontrado")
    Client.activo = False
    Client.fecha_actualizacion = datetime.now().isoformat()
    session.add(Client)
    session.commit()
    return {"message": "Client desactivado exitosamente"} 