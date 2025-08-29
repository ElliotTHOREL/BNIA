from app.routes import all_routers
from app.connection import initialize_pool
from app.database.create import init_bdd
from app.config import AIManager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv

load_dotenv()

import uvicorn
import os
import logging


# --- Configuration du logging ---
os.makedirs("logs", exist_ok=True)  # s'assure que le dossier existe

logging.basicConfig(
    level=logging.INFO,  # Niveau minimal
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/logs.log", encoding="utf-8"),
    ]
)




def create_app() -> FastAPI:
    app = FastAPI()

    #Initialisation outils IA
    app.state.aimanager = AIManager()

    # origins = [
    #     "http://localhost:8080",
    #     "http://127.0.0.1:8080",
    #     "https://a0ea2ec6-2a5a-406b-92fe-9eb840a3c23f.lovableproject.com",
    # ]

    # app.add_middleware(
    #     CORSMiddleware,
    #     allow_origins=origins,
    #     allow_credentials=True,
    #     allow_methods=["*"],
    #     allow_headers=["*"],
    # )

    # Initialisation DB
    initialize_pool()
    init_bdd()

    # Routes
    for router, prefix in all_routers:
        app.include_router(router, prefix=prefix)

    logging.info("Application FastAPI démarrée ✅")
    return app

app = create_app()


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=int(os.getenv("PORT_API")), reload=False)