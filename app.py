from fastapi import FastAPI, Depends, HTTPException, status, Security
from sqlmodel import SQLModel, select, Session
from models import User, Task, UserTaskLink
from database import engine, get_session
from pydantic import BaseModel
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configuración CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica los dominios permitidos
    # allow_origins=["https://tudominio.com", "https://www.tudominio.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración JWT
SECRET_KEY = "supersecretkey"  # Cambia esto en producción
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# Función para crear el token JWT
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Dependencia para obtener el usuario actual a partir del token
def get_current_user(token: str = Security(oauth2_scheme), session: Session = Depends(get_session)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = session.get(User, user_id)
    if user is None:
        raise credentials_exception
    return user

@app.get("/")
def root():
    return {"message": "Hola desde FastAPI"}

@app.on_event("startup")
def init_db():
    SQLModel.metadata.create_all(engine)

@app.post("/users")
def create_user(user: User, session: Session = Depends(get_session)):
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@app.get("/users/{user_id}/tasks")
def get_user_tasks(user_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    user = session.get(User, user_id)
    if not user:
        return {"error": "Usuario no encontrado"}
    return user.tasks

@app.post("/tasks")
def create_task(task: Task, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    session.add(task)
    session.commit()
    session.refresh(task)
    return task

@app.get("/tasks/{task_id}/user")
def get_task_user(task_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    task = session.get(Task, task_id)
    if not task:
        return {"error": "Tarea no encontrada"}
    return task.user

@app.post("/assign-task")
def assign_task_to_user(user_id: int, task_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    link = UserTaskLink(user_id=user_id, task_id=task_id)
    session.add(link)
    session.commit()
    return {"message": f"Tarea {task_id} asignada al usuario {user_id}"}

@app.get("/tasks/{task_id}/users")
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

@app.post("/login", response_model=Token)
def login(request: LoginRequest, session: Session = Depends(get_session)):
    print(request)
    user = session.exec(select(User).where(User.email == request.email)).first()
    if not user or user.password != request.password:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    access_token = create_access_token(data={"sub": user.id}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer"}
