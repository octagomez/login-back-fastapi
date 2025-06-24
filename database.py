from sqlmodel import create_engine, Session
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./db.db")  # fallback local
# DATABASE_URL = "mysql+pymysql://user:password@db:3306/mydb"  # fallback local

engine = create_engine(DATABASE_URL, echo=True)

def get_session():
    with Session(engine) as session:
        yield session
