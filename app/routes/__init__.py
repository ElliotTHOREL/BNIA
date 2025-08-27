from app.routes.document import router as document_router
from app.routes.analyse import router as analyse_router

all_routers = [
    (document_router, "/document"),
    (analyse_router, "/analyse")
]