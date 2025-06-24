from fastapi import FastAPI, Depends
from sqlmodel import SQLModel, select, Session
from models import User, Task
from database import engine, get_session

app = FastAPI()

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
def get_user_tasks(user_id: int, session: Session = Depends(get_session)):
    statement = select(Task).where(Task.user_id == user_id)
    tasks = session.exec(statement).all()
    return tasks

@app.post("/tasks")
def create_task(task: Task, session: Session = Depends(get_session)):
    session.add(task)
    session.commit()
    session.refresh(task)
    return task

@app.get("/tasks/{task_id}/user")
def get_task_user(task_id: int, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        return {"error": "Tarea no encontrada"}
    return task.user
