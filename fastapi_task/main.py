from fastapi import FastAPI

from endpoints import api_router

app = FastAPI()


app.include_router(api_router)


if __name__ == "__main__":
    # Use this for debugging purposes only
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
