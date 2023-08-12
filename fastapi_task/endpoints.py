from fastapi import FastAPI, HTTPException, Depends
from cachetools import TTLCache
import secrets
from schemas import Token, Post, UserLogin, UserSignup
from main import app


# In-memory storage for users and posts
users_db = {}
posts_db = {}
post_id_counter = 1

# Cache for user posts
post_cache = TTLCache(maxsize=100, ttl=300)

# Authentication dependency
def authenticate_user(token: str = Depends(Token)):
    if token.access_token not in users_db:
        raise HTTPException(status_code=401, detail="Invalid token")
    return token.access_token

# Endpoints
@app.post("/signup")
def signup(user: UserSignup):
    if user.username in users_db:
        raise HTTPException(status_code=400, detail="Username already taken")
    users_db[user.username] = user.password
    return {"message": "User registered successfully"}

@app.post("/login", response_model=Token)
def login(user: UserLogin):
    if user.username not in users_db or users_db[user.username] != user.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = secrets.token_urlsafe(32)
    users_db[user.username] = access_token
    return {"access_token": access_token}

@app.post("/addPost")
def add_post(post: Post, token: str = Depends(authenticate_user)):
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

@app.get("/getPosts")
def get_posts(token: str = Depends(authenticate_user)):
    cached_posts = post_cache.get(token)
    if cached_posts:
        return cached_posts
    user_posts = [{"postID": post_id, **post} for post_id, post in posts_db.items() if post["username"] == users_db[token]]
    post_cache[token] = user_posts
    return user_posts

@app.delete("/deletePost")
def delete_post(postID: str, token: str = Depends(authenticate_user)):
    if postID not in posts_db:
        raise HTTPException(status_code=404, detail="Post not found")
    if posts_db[postID]["username"] != users_db[token]:
        raise HTTPException(status_code=403, detail="Unauthorized")
    del posts_db[postID]
    post_cache.pop(token, None)
    return {"message": "Post deleted successfully"}