from fastapi import FastAPI, HTTPException, Depends, Body,Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from werkzeug.security import generate_password_hash, check_password_hash
import uvicorn
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from google.cloud.sql.connector import Connector

from sqlalchemy import create_engine, Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager

import os
from dotenv import load_dotenv

# load the environment variables
load_dotenv()

# Constants
SECRET_KEY = os.getenv("LOGIN_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# GCP MySQL instance connection settings
INSTANCE_CONNECTION_NAME =os.getenv("INSTANCE_CONNECTION_NAME")
print(f"Your instance connection name is: {INSTANCE_CONNECTION_NAME}")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = "userdata"

# initialize the connector object
connector = Connector()

# define a function that returns a database connection object
def getconn():
    conn = connector.connect(
        INSTANCE_CONNECTION_NAME,
        "pymysql",
        user=DB_USER,
        password=DB_PASS,
        db=DB_NAME
    )
    return conn

# create a connection pool
pool = create_engine(
    "mysql+pymysql://",
    creator=getconn,
)

# create a database model
Base = declarative_base()

class User_Db(Base):
    __tablename__ = "users"
    email = Column(String(255), primary_key=True, unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

# create the database table
Base.metadata.create_all(bind=pool)

# create a session local to perform database operations
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=pool)

# create FastAPI APP
@asynccontextmanager
async def lifespan(app: FastAPI):
    
    yield
    #when APP closed, close the connection to the database
    pool.dispose()

app = FastAPI(lifespan=lifespan)

# create user data
def create_user_data(email, password):
    session = SessionLocal()
    try:
        user_data = User_Db(
            email=email,
            hashed_password=generate_password_hash(password)
        )
        existing_user = search_user_data(email)
        if existing_user:
            return "Email already exists. Data not inserted."
        else:
            session.add(user_data)
            session.commit()
            return "Data inserted successfully."
    except Exception as e:
        session.rollback()
        return str(e)
    finally:
        session.close()

# search user data
def search_user_data(email) -> dict | None:
    session = SessionLocal()
    try:
        queried_user = session.query(User_Db).filter(User_Db.email == email).first()
        if queried_user:
            return {
                "email": queried_user.email,
                "hashed_password": queried_user.hashed_password,
            }
        return None
    finally:
        session.close()

#create a user data
user_key = "abc@abc.com"
create_user_data(user_key, "secret")



# Enable CORS

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允許的來源
    allow_credentials=False,
    allow_methods=["*"],  # 允許所有 HTTP 方法
    allow_headers=["*"],  # 允許所有標頭
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class User(BaseModel):
    email: str

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None

#get user data if exists
def get_user(email: str):
    if user_dict:=search_user_data(email):
        return UserInDB(**user_dict)

def verify_password(plain_password, hashed_password):
    return check_password_hash(hashed_password, plain_password)

def authenticate_user(email: str, password: str)-> UserInDB | None:
    user = get_user(email)
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=3)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = get_user(email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

@app.get("/")
async def read_sample_page():
    return FileResponse('login.html')

@app.get("/script.js")
async def get_script():
    return FileResponse('script.js')

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("favicon.ico")

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/register")
async def register(email: str = Body(...), password: str = Body(...)):
    if search_user_data(email):
        raise HTTPException(status_code=400, detail="Email already registered")
    create_user_data(email, password)
    return {"msg": "User registered successfully"}

@app.get("/users/me", response_model=User,summary="return the current user",description="need a token to access this route")
async def read_users_me(request: Request):
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=401,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"}
            )
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return {"email": username}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
