from fastapi import APIRouter, Depends

from src.auth.models import PermissionAction
from src.auth.permissions import require_permission
from src.auth.security import get_user_permissions

router = APIRouter(prefix="/mock-api", tags=["MockAPI"])

MOCK_PRODUCTS = [
    {"id": 1, "name": "Laptop", "price": 999.99, "category": "Electronics"},
    {"id": 2, "name": "Book", "price": 19.99, "category": "Education"},
    {"id": 3, "name": "Phone", "price": 599.99, "category": "Electronics"},
]

MOCK_ORDERS = [
    {"id": 1, "user_id": 1, "products": [1, 2], "total": 1019.98, "status": "completed"},
    {"id": 2, "user_id": 2, "products": [3], "total": 599.99, "status": "pending"},
]

MOCK_USERS = [
    {"id": 1, "email": "user1@example.com", "name": "John"},
    {"id": 2, "email": "user2@example.com", "name": "Alice"},
]


@router.get("/products", response_model=list[dict])
@require_permission("product", PermissionAction.READ)
async def get_products(
    permissions=Depends(get_user_permissions),
):
    return MOCK_PRODUCTS
