import secrets

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate
from app.utils.security import (
    create_access_token,
    hash_password,
    verify_google_token,
    verify_password,
)


def create_user(db: Session, user_in: UserCreate) -> User:
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        name=user_in.name,
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        age=user_in.age,
        gender=user_in.gender,
        activity_level=user_in.activity_level,
        allergies=user_in.allergies,
        conditions=user_in.conditions,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    return user


def generate_auth_token(user: User) -> str:
    return create_access_token(subject=user.email)


def authenticate_google_user(db: Session, google_token: str) -> User:
    token_info = verify_google_token(google_token)
    email = token_info["email"]
    name = token_info.get("name") or email.split("@")[0]

    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        if not existing_user.name and name:
            existing_user.name = name
            db.commit()
            db.refresh(existing_user)
        return existing_user

    # Random password placeholder for Google-created accounts.
    generated_password = secrets.token_urlsafe(32)
    user = User(
        name=name,
        email=email,
        hashed_password=hash_password(generated_password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
