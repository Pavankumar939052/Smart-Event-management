from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin, Token, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Register a new user account")
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    # Check if email is already taken
    if db.query(User).filter(User.email == user_in.email.lower()).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists."
        )

    # Check if username is already taken
    if db.query(User).filter(User.username == user_in.username).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This username is already taken. Please choose another."
        )

    hashed_pw = hash_password(user_in.password)
    user = User(
        username=user_in.username,
        email=user_in.email.lower(),
        hashed_password=hashed_pw
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=Token, summary="Authenticate and generate JWT access token")
def login(login_in: UserLogin, db: Session = Depends(get_db)):
    identifier = login_in.email_or_username.strip()
    user = db.query(User).filter(
        (User.email == identifier.lower()) | (User.username == identifier)
    ).first()

    if not user or not verify_password(login_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Please check your username/email and password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": str(user.id), "username": user.username})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }
