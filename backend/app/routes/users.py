from fastapi import APIRouter, Depends
from app.models.user import User
from app.schemas.auth import UserResponse
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserResponse, summary="Get current authenticated user profile")
def get_user_profile(current_user: User = Depends(get_current_user)):
    """Returns the authenticated user's profile based strictly on JWT identity."""
    return current_user
