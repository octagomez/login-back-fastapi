from fastapi import APIRouter, Depends, HTTPException, status, Security
from sqlmodel import select, Session
from models import User, Task, UserTaskLink
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