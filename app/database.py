from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Añadimos los argumentos de conexión SSL
connect_args = {
    "ssl": {
        "ca": "./isrgrootx1.pem" # Nombre exacto del archivo que descargaste
    }
}

engine = create_engine(
    DATABASE_URL, 
    connect_args=connect_args
)

if not DATABASE_URL:
    raise ValueError("DATABASE_URL variable was not found in the .env file")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base() # Esta clase será la madre de tus tablas

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()