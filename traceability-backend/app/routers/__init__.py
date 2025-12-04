from fastapi import APIRouter
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.stations import router as stations_router
from app.routers.parts import router as parts_router
from app.routers.trace_events import router as trace_events_router
from app.routers.metrics import router as metrics_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(stations_router)
api_router.include_router(parts_router)
api_router.include_router(trace_events_router)
api_router.include_router(metrics_router)

# from .products import router as products_router
# api_router.include_router(products_router, prefix="/products", tags=["Products"])
