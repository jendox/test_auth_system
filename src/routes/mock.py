from fastapi import APIRouter, Depends
from starlette.exceptions import HTTPException

from src.auth.models import PermissionAction, UserPermissions
from src.auth.permissions_decorator import require_permission
from src.auth.security import get_user_permissions

router = APIRouter(prefix="/mock-api", tags=["Mock API"])

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
    """Get products list (requires READ PRODUCT permission)"""
    return MOCK_PRODUCTS


@router.put("/products/{product_id}", response_model=dict)
@require_permission("product", PermissionAction.UPDATE)
async def update_product(
    product_id: int,
    product_data: dict,
    permissions: UserPermissions = Depends(get_user_permissions),
):
    """Update product (requires UPDATE PRODUCT permission)"""
    for product in MOCK_PRODUCTS:
        if product["id"] == product_id:
            product.update(product_data)
            return product
    raise HTTPException(status_code=404, detail="Product not found")


@router.delete("/products/{product_id}")
@require_permission("product", PermissionAction.DELETE)
async def delete_product(
    product_id: int,
    permissions: UserPermissions = Depends(get_user_permissions),
):
    """Delete product (requires DELETE PRODUCT permission)"""
    global MOCK_PRODUCTS  # noqa: PLW0603
    MOCK_PRODUCTS = [p for p in MOCK_PRODUCTS if p["id"] != product_id]
    return {"message": "Product deleted"}


@router.get("/orders", response_model=list[dict])
@require_permission("order", PermissionAction.READ)
async def get_orders(
    permissions: UserPermissions = Depends(get_user_permissions),
):
    """Get orders list (requires READ ORDER permission)"""
    return MOCK_ORDERS


@router.get("/users", response_model=list[dict])
@require_permission("user", PermissionAction.READ)
async def get_users(
    permissions: UserPermissions = Depends(get_user_permissions),
):
    """Get users list (requires READ USER permission)"""
    return MOCK_USERS
