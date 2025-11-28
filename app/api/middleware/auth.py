"""
Authentication middleware for API routes
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
from app.services.auth_service import auth_service
from app.models.auth import UserInDB

security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserInDB:
    """
    Get the current authenticated user from JWT token.

    Args:
        credentials: The authorization credentials from the request header

    Returns:
        UserInDB: The authenticated user

    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    token_data = auth_service.verify_token(token)

    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await auth_service.get_user_by_id(token_data.user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return user


async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))) -> Optional[UserInDB]:
    """
    Get the current authenticated user if token is provided, otherwise return None.
    
    Args:
        credentials: The optional authorization credentials
    
    Returns:
        Optional[UserInDB]: The authenticated user or None
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


async def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user)
) -> UserInDB:
    """
    Get the current active user.
    
    Args:
        current_user: The current user from get_current_user
        
    Returns:
        UserInDB: Active user information
        
    Raises:
        HTTPException: If user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def require_permission(permission: str):
    """
    Create a dependency that requires a specific permission.
    
    Args:
        permission: The permission to check
        
    Returns:
        A dependency function that checks the permission
    """
    async def permission_checker(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
        has_permission = await auth_service.check_user_permission(current_user.id, permission)
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return current_user
    return permission_checker


async def require_admin(
    current_user: UserInDB = Depends(get_current_user)
) -> UserInDB:
    """
    Require admin role for the current user.
    
    Args:
        current_user: The current user from get_current_user
        
    Returns:
        UserInDB: Admin user information
        
    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user.is_superuser:
        roles = await auth_service.get_user_roles(current_user.id)
        is_admin = any(role.get("role_type") in ["super_admin", "company_admin"] for role in roles)
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
    return current_user


async def require_brand_access(
    brand_id: str,
    current_user: UserInDB = Depends(get_current_user)
) -> UserInDB:
    """
    Check if user has access to a specific brand.
    
    Args:
        brand_id: The brand ID to check access for
        current_user: The current user from get_current_user
        
    Returns:
        UserInDB: User information if access is granted
        
    Raises:
        HTTPException: If user doesn't have access to the brand
    """
    if current_user.is_superuser:
        return current_user
    
    roles = await auth_service.get_user_roles(current_user.id)
    
    for role in roles:
        if role.get("scope") == "system":
            return current_user
        if role.get("scope") == "brand" and brand_id in role.get("brand_ids", []):
            return current_user
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"No access to brand {brand_id}"
    )
    
    return current_user