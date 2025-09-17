from fastapi import APIRouter

from .agents import router as agents_router
from .analytics import router as analytics_router
from .auth import router as auth_router
from .documents import router as documents_router
from .forwarding import router as forwarding_router
from .routes import router as routes_router
from .users import router as users_router

router = APIRouter()
router.include_router(auth_router, tags=["Auth"])
router.include_router(users_router, tags=["Users"])
router.include_router(agents_router, tags=["Agents"])
router.include_router(documents_router, tags=["Documents"])
router.include_router(forwarding_router, tags=["Forwarding"])
router.include_router(routes_router, tags=["Routes"])
router.include_router(analytics_router, tags=["Analytics"])


__all__ = ["router"]
