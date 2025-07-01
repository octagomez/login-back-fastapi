from fastapi import FastAPI
from sqlmodel import SQLModel
from database import engine
from fastapi.middleware.cors import CORSMiddleware
from apis import router as api_router
from apisclients import router_clients
from apisproducts import router_products
from models import User, Task, UserTaskLink 
from clients import Client

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

app.include_router(api_router)
app.include_router(router_clients)
app.include_router(router_products)

@app.on_event("startup")
def init_db():
    SQLModel.metadata.create_all(engine)
