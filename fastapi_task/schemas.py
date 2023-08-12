from fastapi import FastAPI, HTTPException, Depends
import secrets
from datetime import datetime, timedelta
from pydantic import BaseModel

# Pydantic schemas
class UserSignup(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Post(BaseModel):
    title: str
    content: str

class Token(BaseModel):
    access_token: str
