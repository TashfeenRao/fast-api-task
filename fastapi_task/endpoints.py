from fastapi import FastAPI, HTTPException, Depends, Security
from cachetools import TTLCache
import secrets

from typing import List

from fastapi.security import SecurityScopes, OAuth2PasswordBearer

from schemas import Token, Post, UserLogin, UserSignup
from fastapi import APIRouter
api_router = APIRouter()
# In-memory storage for users and posts
users_db = {}
posts_db = {}
access_tokens = []
post_id_counter = 1

# Cache for user posts
post_cache = TTLCache(maxsize=100, ttl=5000)
user_cache = TTLCache(maxsize=100, ttl=5000)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Authentication dependency
def authenticate_user(security_scopes: SecurityScopes,
                      token: Token = Depends(Token)):
    app_scopes = ["add_post", "get_post"]
    for scope in security_scopes.scopes:
        if scope not in app_scopes:
            raise HTTPException(status_code=401, detail="not has permission")
    if token.access_token not in users_db:
        raise HTTPException(status_code=401, detail="Invalid token")
    return token.access_token


# Endpoints
@api_router.post("/signup")
def signup(user: UserSignup):
    if user.username in users_db:
        raise HTTPException(status_code=400, detail="Username already taken")
    users_db[user.username] = user.password
    return {"message": "User registered successfully"}

@api_router.post("/login", response_model=Token)
def login(user: UserLogin):
    if user.username not in users_db or users_db[user.username] != user.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = secrets.token_urlsafe(32)
    users_db[access_token] = user.username
    user_cache[user.username] = user.username
    return {"access_token": access_token}

@api_router.post("/addPost")
def add_post(post: Post, token=Depends(authenticate_user)):
    global post_id_counter
    if len(post.content.encode('utf-8')) > 1024 * 1024:
        raise HTTPException(status_code=400, detail="Payload size exceeded")
    post_id = str(post_id_counter)
    posts_db[post_id] = {
        "title": post.title,
        "content": post.content,
        "username": users_db[token]
    }
    post_id_counter += 1
    return {"postID": post_id}

@api_router.get("/getPosts", response_model=List[Post])
def get_posts(token: str = Security(
        dependency=authenticate_user, scopes=["get_post"]
    )):
    cached_posts = post_cache.get(token)
    if cached_posts:
        return cached_posts
    user_posts = [{"postID": post_id, **post} for post_id, post in posts_db.items() if post["username"] == users_db[token]]
    post_cache[token] = user_posts
    return user_posts

@api_router.delete("/deletePost")
def delete_post(postID: str, token: str = Depends(authenticate_user)):
    if postID not in posts_db:
        raise HTTPException(status_code=404, detail="Post not found")
    if posts_db[postID]["username"] != users_db[token]:
        raise HTTPException(status_code=403, detail="Unauthorized")
    del posts_db[postID]
    post_cache.pop(token, None)
    return {"message": "Post deleted successfully"}