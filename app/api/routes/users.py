from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from pydantic import BaseModel, Field
from bson import ObjectId
from datetime import datetime
from app.utils import get_database
from app.models.auth import UserInDB
from app.api.middleware.auth import get_current_user

router = APIRouter()


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    full_name: Optional[str] = None
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[str] = Field(None, pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: str = Field(alias="_id")
    role: Optional[str] = None
    roles: Optional[List[dict]] = None
    is_superuser: Optional[bool] = False
    company_id: Optional[str] = None
    company_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True

class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int
    page: int = 1
    page_size: int = 20


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    db = get_database()
    
    existing_user = await db.users.find_one({"$or": [{"email": user.email}, {"username": user.username}]})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists"
        )
    
    user_dict = user.dict()
    user_dict["created_at"] = datetime.utcnow()
    user_dict["updated_at"] = datetime.utcnow()
    
    result = await db.users.insert_one(user_dict)
    created_user = await db.users.find_one({"_id": result.inserted_id})
    
    created_user["_id"] = str(created_user["_id"])
    return UserResponse(**created_user)


@router.get("/", response_model=UserListResponse)
async def get_users(
    skip: int = 0, 
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    
    # Build filter based on user's role
    filter_query = {}
    
    # Get user role and company_id safely
    user_role = current_user.get("role") if isinstance(current_user, dict) else getattr(current_user, 'role', None)
    user_company_id = current_user.get("company_id") if isinstance(current_user, dict) else getattr(current_user, 'company_id', None)
    user_roles = current_user.get("roles", []) if isinstance(current_user, dict) else getattr(current_user, 'roles', [])
    
    # Check user's role - super_admin can see all users
    if user_role != "super_admin":
        # Check if user has super_admin in roles array
        is_super_admin = False
        if user_roles:
            is_super_admin = any(role.get('role_name') == 'super_admin' for role in user_roles)
        
        if not is_super_admin:
            # For company_admin, supervisor, and agents - only show users from their company
            if user_company_id:
                filter_query["company_id"] = user_company_id
            else:
                # If user has no company_id, return empty list
                return UserListResponse(
                    users=[],
                    total=0,
                    page=1,
                    page_size=limit
                )
    
    # Get total count with filter
    total = await db.users.count_documents(filter_query)
    
    users = []
    async for user in db.users.find(filter_query).skip(skip).limit(limit):
        user["_id"] = str(user["_id"])
        # Ensure required fields have default values
        if "created_at" not in user:
            user["created_at"] = datetime.utcnow()
        if "updated_at" not in user:
            user["updated_at"] = datetime.utcnow()
        
        # Fetch company name if user has company_id but no company_name
        if user.get("company_id") and not user.get("company_name"):
            company_id = user["company_id"]
            # Try to find company by string ID first
            company = await db.companies.find_one({"_id": company_id})
            if not company and ObjectId.is_valid(company_id):
                # Try with ObjectId if string didn't work
                try:
                    company = await db.companies.find_one({"_id": ObjectId(company_id)})
                except:
                    pass
            if company:
                user["company_name"] = company.get("name", "")
        
        users.append(UserResponse(**user))
    
    return UserListResponse(
        users=users,
        total=total,
        page=1,
        page_size=limit
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    db = get_database()
    
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user["_id"] = str(user["_id"])
    return UserResponse(**user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_update: UserUpdate):
    db = get_database()
    
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    update_data = {k: v for k, v in user_update.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    updated_user = await db.users.find_one({"_id": ObjectId(user_id)})
    updated_user["_id"] = str(updated_user["_id"])
    return UserResponse(**updated_user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str):
    db = get_database()
    
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    result = await db.users.delete_one({"_id": ObjectId(user_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return None