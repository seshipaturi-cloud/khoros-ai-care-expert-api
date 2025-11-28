"""
Admin-only API routes for super_admin operations
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from bson import ObjectId
from datetime import datetime

from app.models.auth import UserRegister, UserResponse, UserInDB
from app.models.company import CompanyResponse
from app.services.auth_service import auth_service
from app.services.company_service import company_service
from app.api.middleware.auth import get_current_user
from app.utils import get_database
from pydantic import BaseModel, EmailStr, Field

router = APIRouter(prefix="/api/admin", tags=["admin"])


class AdminUserCreate(BaseModel):
    """Schema for admin creating users with role and company assignment"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str
    username: str = Field(..., min_length=3, max_length=50)
    company_id: Optional[str] = None
    role_type: str = Field(default="company_admin")  # super_admin, company_admin, etc.
    is_active: bool = True


async def verify_super_admin(current_user: UserInDB) -> bool:
    """Verify if current user is super_admin"""
    if current_user.is_superuser:
        return True
    
    roles = await auth_service.get_user_roles(current_user.id)
    return any(role.get("role_type") == "super_admin" for role in roles)


@router.post("/create-company-admin", response_model=UserResponse)
async def create_company_admin(
    user_data: AdminUserCreate,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Create a company admin user and assign to a company.
    Only super_admin can perform this action.
    """
    # Verify super_admin
    if not await verify_super_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admins can create company administrators"
        )
    
    db = get_database()
    
    # Verify company exists if provided
    if user_data.company_id:
        if not ObjectId.is_valid(user_data.company_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid company ID format"
            )
        
        company = await company_service.get_company(user_data.company_id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )
    
    # Check if user already exists
    existing_user = await db.users.find_one({
        "$or": [
            {"email": user_data.email},
            {"username": user_data.username}
        ]
    })
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists"
        )
    
    # Get the appropriate role
    role = await db.roles.find_one({
        "role_type": user_data.role_type,
        "is_system_role": True
    })
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role type '{user_data.role_type}' not found"
        )
    
    # Create user with role
    user_dict = {
        "email": user_data.email,
        "username": user_data.username,
        "full_name": user_data.full_name,
        "hashed_password": auth_service.get_password_hash(user_data.password),
        "is_active": user_data.is_active,
        "is_superuser": user_data.role_type == "super_admin",
        "role_ids": [str(role["_id"])],
        "company_id": user_data.company_id,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "created_by": current_user.id,
        "last_login": None
    }
    
    result = await db.users.insert_one(user_dict)
    created_user = await db.users.find_one({"_id": result.inserted_id})
    
    # Get roles for response
    roles = await auth_service.get_user_roles(str(created_user["_id"]))
    
    return UserResponse(
        _id=str(created_user["_id"]),
        email=created_user["email"],
        username=created_user["username"],
        full_name=created_user["full_name"],
        is_active=created_user["is_active"],
        is_superuser=created_user["is_superuser"],
        role_ids=created_user["role_ids"],
        roles=roles,
        created_at=created_user["created_at"],
        updated_at=created_user["updated_at"],
        last_login=created_user.get("last_login")
    )


@router.post("/assign-user-to-company/{user_id}/{company_id}")
async def assign_user_to_company(
    user_id: str,
    company_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Assign a user to a company.
    Only super_admin can perform this action.
    """
    # Verify super_admin
    if not await verify_super_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admins can assign users to companies"
        )
    
    db = get_database()
    
    # Validate IDs
    if not ObjectId.is_valid(user_id) or not ObjectId.is_valid(company_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format"
        )
    
    # Verify user exists
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify company exists
    company = await company_service.get_company(company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Update user with company
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {
            "$set": {
                "company_id": company_id,
                "updated_at": datetime.utcnow(),
                "updated_by": current_user.id
            }
        }
    )
    
    return {
        "message": "User successfully assigned to company",
        "user_id": user_id,
        "company_id": company_id,
        "company_name": company.name
    }


@router.get("/users-by-company/{company_id}", response_model=List[UserResponse])
async def get_company_users(
    company_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get all users assigned to a company.
    Super_admin can see all, company_admin can see their own company.
    """
    db = get_database()
    
    # Validate company ID
    if not ObjectId.is_valid(company_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid company ID format"
        )
    
    # Check permissions
    is_super_admin = await verify_super_admin(current_user)
    
    if not is_super_admin:
        # Check if user is company_admin for this company
        user_company_id = getattr(current_user, 'company_id', None)
        if user_company_id != company_id:
            roles = await auth_service.get_user_roles(current_user.id)
            is_company_admin = any(
                role.get("role_type") == "company_admin" and 
                user_company_id == company_id 
                for role in roles
            )
            if not is_company_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to view users of this company"
                )
    
    # Get users
    users = []
    async for user in db.users.find({"company_id": company_id}):
        user_id = str(user["_id"])
        roles = await auth_service.get_user_roles(user_id)
        
        users.append(UserResponse(
            _id=user_id,
            email=user["email"],
            username=user.get("username", ""),
            full_name=user.get("full_name", ""),
            is_active=user.get("is_active", True),
            is_superuser=user.get("is_superuser", False),
            role_ids=user.get("role_ids", []),
            roles=roles,
            created_at=user.get("created_at", datetime.utcnow()),
            updated_at=user.get("updated_at", datetime.utcnow()),
            last_login=user.get("last_login")
        ))
    
    return users


@router.post("/create-super-admin", response_model=UserResponse)
async def create_super_admin(
    user_data: UserRegister
):
    """
    Create a super admin user.
    This endpoint should be protected in production or only available during initial setup.
    """
    db = get_database()
    
    # In production, you might want to check if any super_admin exists
    # and only allow creation if none exists (initial setup)
    super_admin_count = await db.users.count_documents({"is_superuser": True})
    
    # If super_admins exist, don't allow creation without proper auth
    # For now, we'll allow first super_admin creation without auth
    if super_admin_count > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin already exists. Use authenticated endpoint to create additional super admins."
        )
    
    # Check if user already exists
    existing_user = await db.users.find_one({
        "$or": [
            {"email": user_data.email},
            {"username": user_data.username}
        ]
    })
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists"
        )
    
    # Get super_admin role
    super_admin_role = await db.roles.find_one({
        "role_type": "super_admin",
        "is_system_role": True
    })
    
    if not super_admin_role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Super admin role not found. Please run role initialization."
        )
    
    # Create super admin user
    user_dict = {
        "email": user_data.email,
        "username": user_data.username,
        "full_name": user_data.full_name,
        "hashed_password": auth_service.get_password_hash(user_data.password),
        "is_active": True,
        "is_superuser": True,
        "role_ids": [str(super_admin_role["_id"])],
        "company_id": None,  # Super admin not tied to specific company
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "created_by": "system",
        "last_login": None
    }
    
    result = await db.users.insert_one(user_dict)
    created_user = await db.users.find_one({"_id": result.inserted_id})
    
    # Get roles for response
    roles = await auth_service.get_user_roles(str(created_user["_id"]))
    
    return UserResponse(
        _id=str(created_user["_id"]),
        email=created_user["email"],
        username=created_user["username"],
        full_name=created_user["full_name"],
        is_active=created_user["is_active"],
        is_superuser=created_user["is_superuser"],
        role_ids=created_user["role_ids"],
        roles=roles,
        created_at=created_user["created_at"],
        updated_at=created_user["updated_at"],
        last_login=created_user.get("last_login")
    )