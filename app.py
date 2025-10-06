from fastapi import FastAPI
from introlix.routes.chat import chat_router

app = FastAPI(openapi_prefix='/api/v1')


@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}


app.include_router(chat_router)