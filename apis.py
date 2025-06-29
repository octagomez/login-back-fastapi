from fastapi import APIRouter, Depends, HTTPException, status, Security
from sqlmodel import select, Session
from models import User, Task, UserTaskLink, Cliente
from database import get_session
from pydantic import BaseModel
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from typing import Optional, List

router = APIRouter()

SECRET_KEY = "supersecretkey"  # Cambia esto en producción
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    print(f"Datos a codificar en token: {to_encode}")
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    print(f"Token creado: {encoded_jwt}")
    return encoded_jwt

def get_current_user(token: str = Security(oauth2_scheme), session: Session = Depends(get_session)):
    print(f"Token recibido: {token}")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        print(f"Intentando decodificar token con SECRET_KEY: {SECRET_KEY}")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"Payload decodificado: {payload}")
        user_id_str: str = payload.get("sub")
        print(f"User ID extraído (string): {user_id_str}")
        if user_id_str is None:
            print("User ID es None")
            raise credentials_exception
        user_id: int = int(user_id_str)
        print(f"User ID convertido a int: {user_id}")
    except JWTError as e:
        print(f"Error JWT: {e}")
        raise credentials_exception
    except Exception as e:
        print(f"Error inesperado: {e}")
        raise credentials_exception
    
    user = session.get(User, user_id)
    print(f"Usuario encontrado: {user}")
    if user is None:
        print("Usuario no encontrado en la base de datos")
        raise credentials_exception
    return user

@router.get("/")
def root():
    return {"message": "Hola desde FastAPI"}

@router.get("/health")
def health_check(session: Session = Depends(get_session)):
    try:
        # Verificar si la tabla Cliente existe
        result = session.exec(select(Cliente).limit(1)).all()
        return {"status": "healthy", "message": "Base de datos funcionando correctamente", "tabla_clientes": "existe"}
    except Exception as e:
        return {"status": "unhealthy", "message": f"Error en base de datos: {str(e)}", "tabla_clientes": "no existe"}

@router.post("/users")
def create_user(user: User, session: Session = Depends(get_session)):
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@router.get("/users/{user_id}/tasks")
def get_user_tasks(user_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    user = session.get(User, user_id)
    if not user:
        return {"error": "Usuario no encontrado"}
    return user.tasks

@router.post("/tasks")
def create_task(task: Task, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    session.add(task)
    session.commit()
    session.refresh(task)
    return task

@router.get("/tasks/{task_id}/user")
def get_task_user(task_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    task = session.get(Task, task_id)
    if not task:
        return {"error": "Tarea no encontrada"}
    return task.user

@router.post("/assign-task")
def assign_task_to_user(user_id: int, task_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    link = UserTaskLink(user_id=user_id, task_id=task_id)
    session.add(link)
    session.commit()
    return {"message": f"Tarea {task_id} asignada al usuario {user_id}"}

@router.get("/tasks/{task_id}/users")
def get_task_users(task_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    task = session.get(Task, task_id)
    if not task:
        return {"error": "Tarea no encontrada"}
    return task.users

class LoginRequest(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/login", response_model=Token)
def login(request: LoginRequest, session: Session = Depends(get_session)):
    print(request)
    user = session.exec(select(User).where(User.email == request.email)).first()
    if not user or user.password != request.password:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    access_token = create_access_token(data={"sub": str(user.id)}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    return {"message": "Logout exitoso"}

# CRUD de Clientes

class ClienteCreate(BaseModel):
    nombre: str
    email: str
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    empresa: Optional[str] = None

class ClienteUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    empresa: Optional[str] = None
    activo: Optional[bool] = None

@router.post("/clients", response_model=Cliente)
def create_cliente(cliente: ClienteCreate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    print(f"Datos recibidos: {cliente}")
    # Verificar si el email ya existe
    existing_cliente = session.exec(select(Cliente).where(Cliente.email == cliente.email)).first()
    if existing_cliente:
        raise HTTPException(status_code=400, detail="Ya existe un cliente con ese email")
    
    try:
        db_cliente = Cliente(
            nombre=cliente.nombre,
            email=cliente.email,
            telefono=cliente.telefono,
            direccion=cliente.direccion,
            empresa=cliente.empresa,
            fecha_creacion=datetime.now().isoformat(),
            fecha_actualizacion=datetime.now().isoformat()
        )
        print(f"Cliente a crear: {db_cliente}")
        session.add(db_cliente)
        session.commit()
        session.refresh(db_cliente)
        return db_cliente
    except Exception as e:
        print(f"Error al crear cliente: {e}")
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.post("/clients-test", response_model=Cliente)
def create_cliente_test(cliente: ClienteCreate, session: Session = Depends(get_session)):
    print(f"Datos recibidos (test): {cliente}")
    # Verificar si el email ya existe
    existing_cliente = session.exec(select(Cliente).where(Cliente.email == cliente.email)).first()
    if existing_cliente:
        raise HTTPException(status_code=400, detail="Ya existe un cliente con ese email")
    
    try:
        db_cliente = Cliente(
            nombre=cliente.nombre,
            email=cliente.email,
            telefono=cliente.telefono,
            direccion=cliente.direccion,
            empresa=cliente.empresa,
            fecha_creacion=datetime.now().isoformat(),
            fecha_actualizacion=datetime.now().isoformat()
        )
        print(f"Cliente a crear (test): {db_cliente}")
        session.add(db_cliente)
        session.commit()
        session.refresh(db_cliente)
        return db_cliente
    except Exception as e:
        print(f"Error al crear cliente (test): {e}")
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.get("/clients", response_model=List[Cliente])
def get_clientes(skip: int = 0, limit: int = 100, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    clientes = session.exec(select(Cliente).offset(skip).limit(limit)).all()
    return clientes

@router.get("/clients/{cliente_id}", response_model=Cliente)
def get_cliente(cliente_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    cliente = session.get(Cliente, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente

@router.put("/clients/{cliente_id}", response_model=Cliente)
def update_cliente(cliente_id: int, cliente_update: ClienteUpdate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    cliente = session.get(Cliente, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    # Verificar si el email ya existe en otro cliente
    if cliente_update.email and cliente_update.email != cliente.email:
        existing_cliente = session.exec(select(Cliente).where(Cliente.email == cliente_update.email)).first()
        if existing_cliente:
            raise HTTPException(status_code=400, detail="Ya existe un cliente con ese email")
    
    update_data = cliente_update.dict(exclude_unset=True)
    update_data["fecha_actualizacion"] = datetime.now().isoformat()
    
    for field, value in update_data.items():
        setattr(cliente, field, value)
    
    session.add(cliente)
    session.commit()
    session.refresh(cliente)
    return cliente

@router.delete("/clients/{cliente_id}")
def delete_cliente(cliente_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    cliente = session.get(Cliente, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    session.delete(cliente)
    session.commit()
    return {"message": "Cliente eliminado exitosamente"}

@router.get("/clients/activos", response_model=List[Cliente])
def get_clientes_activos(skip: int = 0, limit: int = 100, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    clientes = session.exec(select(Cliente).where(Cliente.activo == True).offset(skip).limit(limit)).all()
    return clientes

@router.post("/clients/{cliente_id}/activar")
def activar_cliente(cliente_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    cliente = session.get(Cliente, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    cliente.activo = True
    cliente.fecha_actualizacion = datetime.now().isoformat()
    session.add(cliente)
    session.commit()
    return {"message": "Cliente activado exitosamente"}

@router.post("/clients/{cliente_id}/desactivar")
def desactivar_cliente(cliente_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    cliente = session.get(Cliente, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    cliente.activo = False
    cliente.fecha_actualizacion = datetime.now().isoformat()
    session.add(cliente)
    session.commit()
    return {"message": "Cliente desactivado exitosamente"} 