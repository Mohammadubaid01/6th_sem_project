import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from backend.api.routes import router
from src.database.db import create_tables


app = FastAPI(title="AI Study Assistant")

@app.on_event("startup")
def startup():
    create_tables()  # DB init

app.add_middleware(SessionMiddleware, secret_key="supersecret")

app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

app.include_router(router)








































# from fastapi import FastAPI
# from backend.api.routes import router
# import webbrowser
# from src.database.db import create_tables

# # FIRST define app
# app = FastAPI(title="AI Study Assistant")

# # THEN use decorators
# @app.get("/")
# def home():
#     return {"message": "AI Study Assistant is running 🚀"}

# # include routes
# app.include_router(router)

# # startup event (optional)
# @app.on_event("startup")
# def open_browser():
#     create_tables()  # Ensure DB tables are created
#     webbrowser.open("http://127.0.0.1:8000/docs")




































