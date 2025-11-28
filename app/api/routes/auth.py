from fastapi import APIRouter, HTTPException, status, Depends, Request, Response
from fastapi.security import HTTPBearer
from typing import Optional
from datetime import timedelta

from app.models.auth import (
    Token, UserLogin, UserRegister, UserResponse, 
    UserUpdate, PasswordChange, PasswordReset, 
    PasswordResetConfirm, SessionInfo
)
from app.services.auth_service import auth_service
from app.api.middleware.auth import get_current_user, get_current_active_user
from app.models.auth import UserInDB

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    """
    Register a new user.
    """
    try:
        user = await auth_service.create_user(user_data)
        
        roles = await auth_service.get_user_roles(user.id)
        
        return UserResponse(
            _id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            role_ids=user.role_ids,
            roles=roles,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, request: Request):
    """
    Login with email and password to get access token.
    """
    user = await auth_service.authenticate_user(
        user_credentials.email, 
        user_credentials.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    roles = await auth_service.get_user_roles(user.id)
    role_names = [role.get("name", "") for role in roles]
    
    access_token_expires = timedelta(minutes=auth_service.access_token_expire_minutes)
    access_token = auth_service.create_access_token(
        data={
            "sub": user.id,
            "email": user.email,
            "roles": role_names
        },
        expires_delta=access_token_expires
    )
    
    await auth_service.update_last_login(user.id)
    
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "Unknown")
    session_id = await auth_service.create_session(user.id, client_ip, user_agent)
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=auth_service.access_token_expire_minutes * 60
    )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Logout current user and invalidate session.
    """
    session_id = request.headers.get("x-session-id")
    
    if session_id:
        await auth_service.invalidate_session(session_id)
    
    return {"message": "Successfully logged out"}


@router.post("/logout-all")
async def logout_all_sessions(
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Logout from all sessions/devices.
    """
    await auth_service.invalidate_all_user_sessions(current_user.id)
    
    return {"message": "Successfully logged out from all sessions"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Get current user information.
    """
    from app.utils import get_database
    from bson import ObjectId
    
    roles = await auth_service.get_user_roles(current_user.id)
    
    # Fetch company name if user has company_id
    company_name = None
    if hasattr(current_user, 'company_id') and current_user.company_id:
        db = get_database()
        company_id = current_user.company_id
        
        # Try to find company by string ID first
        company = await db.companies.find_one({"_id": company_id})
        if not company and ObjectId.is_valid(company_id):
            # Try with ObjectId if string didn't work
            try:
                company = await db.companies.find_one({"_id": ObjectId(company_id)})
            except:
                pass
        
        if company:
            company_name = company.get("name", "")
    
    return UserResponse(
        _id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        role=current_user.role if hasattr(current_user, 'role') else None,
        role_ids=current_user.role_ids,
        roles=roles,
        company_id=current_user.company_id if hasattr(current_user, 'company_id') else None,
        company_name=company_name,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        last_login=current_user.last_login
    )


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Update current user information.
    """
    updated_user = await auth_service.update_user(current_user.id, user_update)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    roles = await auth_service.get_user_roles(updated_user.id)
    
    return UserResponse(
        _id=updated_user.id,
        email=updated_user.email,
        username=updated_user.username,
        full_name=updated_user.full_name,
        is_active=updated_user.is_active,
        is_superuser=updated_user.is_superuser,
        role_ids=updated_user.role_ids,
        roles=roles,
        created_at=updated_user.created_at,
        updated_at=updated_user.updated_at,
        last_login=updated_user.last_login
    )


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Change current user's password.
    """
    if not auth_service.verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    user_update = UserUpdate(password=password_data.new_password)
    await auth_service.update_user(current_user.id, user_update)
    
    await auth_service.invalidate_all_user_sessions(current_user.id)
    
    return {"message": "Password changed successfully. Please login again."}


@router.post("/refresh-token", response_model=Token)
async def refresh_token(
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Refresh access token.
    """
    roles = await auth_service.get_user_roles(current_user.id)
    role_names = [role.get("name", "") for role in roles]
    
    access_token_expires = timedelta(minutes=auth_service.access_token_expire_minutes)
    new_access_token = auth_service.create_access_token(
        data={
            "sub": current_user.id,
            "email": current_user.email,
            "roles": role_names
        },
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=new_access_token,
        token_type="bearer",
        expires_in=auth_service.access_token_expire_minutes * 60
    )


@router.post("/verify-token")
async def verify_token(
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Verify if the current token is valid.
    """
    return {
        "valid": True,
        "user_id": current_user.id,
        "email": current_user.email
    }


@router.get("/permissions")
async def get_user_permissions(
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Get all permissions for the current user.
    """
    roles = await auth_service.get_user_roles(current_user.id)
    
    permissions = set()
    for role in roles:
        for permission in role.get("permissions", []):
            permissions.add(permission)
    
    return {
        "user_id": current_user.id,
        "permissions": list(permissions),
        "roles": [{"id": role.get("_id"), "name": role.get("name"), "display_name": role.get("display_name")} for role in roles]
    }