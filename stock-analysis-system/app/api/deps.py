"""
API Dependencies (Dependency Injection)
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

# TODO: Import database session
# from app.database import get_db

# TODO: Import security functions
# from app.core.security import decode_access_token

# TODO: Import models
# from app.models.user import User

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    # db: Session = Depends(get_db)
):
    """
    Dependency to get current authenticated user
    """
    # TODO: Decode JWT token
    # TODO: Get user from database
    # TODO: Return user object
    # credentials_exception = HTTPException(
    #     status_code=status.HTTP_401_UNAUTHORIZED,
    #     detail="Could not validate credentials",
    #     headers={"WWW-Authenticate": "Bearer"},
    # )
    pass

async def get_current_investor(
    # current_user: User = Depends(get_current_user)
):
    """
    Dependency to ensure user is an investor
    """
    # TODO: Check if user role is investor
    # if current_user.role != "investor":
    #     raise HTTPException(status_code=403, detail="Not authorized")
    # return current_user
    pass

async def get_current_advisor(
    # current_user: User = Depends(get_current_user)
):
    """
    Dependency to ensure user is a financial advisor
    """
    # TODO: Check if user role is advisor
    # if current_user.role != "advisor":
    #     raise HTTPException(status_code=403, detail="Not authorized")
    # return current_user
    pass

async def get_current_admin(
    # current_user: User = Depends(get_current_user)
):
    """
    Dependency to ensure user is an admin
    """
    # TODO: Check if user role is admin
    # if current_user.role != "admin":
    #     raise HTTPException(status_code=403, detail="Not authorized")
    # return current_user
    pass





