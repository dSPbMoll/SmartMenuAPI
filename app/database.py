from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Formato: mysql+pymysql://usuario:password@host:puerto/nombre_bd
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:1234@127.0.0.1:3306/smart_menu_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base() # Esta clase será la madre de tus tablas

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()