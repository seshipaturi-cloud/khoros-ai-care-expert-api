from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from bson import ObjectId
from datetime import datetime

from app.models.role import (
    RoleCreate, RoleUpdate, RoleResponse, 
    RoleListResponse, ROLE_TEMPLATES, RoleType,
    PermissionType
)
from app.api.middleware.auth import get_current_user, require_admin, require_permission
from app.models.auth import UserInDB
from app.utils import get_database

router = APIRouter(prefix="/api/roles", tags=["roles"])


@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    current_user: UserInDB = Depends(require_admin)
):
    """
    Create a new role.
    """
    db = get_database()
    
    existing_role = await db.roles.find_one({
        "name": role_data.name,
        "company_id": role_data.company_id
    })
    
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role with this name already exists in the company"
        )
    
    role_dict = role_data.dict()
    role_dict["created_at"] = datetime.utcnow()
    role_dict["updated_at"] = datetime.utcnow()
    role_dict["created_by"] = current_user.id
    role_dict["updated_by"] = current_user.id
    
    result = await db.roles.insert_one(role_dict)
    created_role = await db.roles.find_one({"_id": result.inserted_id})
    
    created_role["_id"] = str(created_role["_id"])
    
    if created_role.get("company_id"):
        company = await db.companies.find_one({"_id": ObjectId(created_role["company_id"])})
        if company:
            created_role["company_name"] = company.get("name")
    
    return RoleResponse(**created_role)


@router.get("/", response_model=RoleListResponse)
async def get_roles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    company_id: Optional[str] = None,
    scope: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get list of roles with pagination.
    """
    db = get_database()
    
    filter_query = {}
    
    if company_id:
        filter_query["$or"] = [
            {"company_id": company_id},
            {"company_id": None}
        ]
    
    if scope:
        filter_query["scope"] = scope
    
    if is_active is not None:
        filter_query["is_active"] = is_active
    
    skip = (page - 1) * page_size
    
    total = await db.roles.count_documents(filter_query)
    
    roles = []
    async for role in db.roles.find(filter_query).skip(skip).limit(page_size):
        role["_id"] = str(role["_id"])
        
        user_count = await db.users.count_documents({
            "role_ids": str(role["_id"])
        })
        role["current_users"] = user_count
        
        if role.get("company_id"):
            company = await db.companies.find_one({"_id": ObjectId(role["company_id"])})
            if company:
                role["company_name"] = company.get("name")
        
        roles.append(RoleResponse(**role))
    
    total_pages = (total + page_size - 1) // page_size
    
    return RoleListResponse(
        roles=roles,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/templates", response_model=List[dict])
async def get_role_templates(
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get available role templates.
    """
    templates = []
    for role_type, template in ROLE_TEMPLATES.items():
        templates.append({
            "type": role_type.value,
            "display_name": template["display_name"],
            "scope": template["scope"].value,
            "description": template["description"],
            "permissions_count": len(template["permissions"])
        })
    
    return templates


@router.get("/permissions", response_model=List[str])
async def get_all_permissions(
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get all available permissions.
    """
    return [permission.value for permission in PermissionType]


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get a specific role by ID.
    """
    db = get_database()
    
    if not ObjectId.is_valid(role_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role ID format"
        )
    
    role = await db.roles.find_one({"_id": ObjectId(role_id)})
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    role["_id"] = str(role["_id"])
    
    user_count = await db.users.count_documents({
        "role_ids": role_id
    })
    role["current_users"] = user_count
    
    if role.get("company_id"):
        company = await db.companies.find_one({"_id": ObjectId(role["company_id"])})
        if company:
            role["company_name"] = company.get("name")
    
    return RoleResponse(**role)


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: str,
    role_update: RoleUpdate,
    current_user: UserInDB = Depends(require_admin)
):
    """
    Update a role.
    """
    db = get_database()
    
    if not ObjectId.is_valid(role_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role ID format"
        )
    
    existing_role = await db.roles.find_one({"_id": ObjectId(role_id)})
    
    if not existing_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    if existing_role.get("is_system_role"):
        allowed_updates = ["is_active", "description", "metadata"]
        update_data = {k: v for k, v in role_update.dict().items() 
                      if v is not None and k in allowed_updates}
    else:
        update_data = {k: v for k, v in role_update.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    update_data["updated_at"] = datetime.utcnow()
    update_data["updated_by"] = current_user.id
    
    await db.roles.update_one(
        {"_id": ObjectId(role_id)},
        {"$set": update_data}
    )
    
    updated_role = await db.roles.find_one({"_id": ObjectId(role_id)})
    updated_role["_id"] = str(updated_role["_id"])
    
    user_count = await db.users.count_documents({
        "role_ids": role_id
    })
    updated_role["current_users"] = user_count
    
    if updated_role.get("company_id"):
        company = await db.companies.find_one({"_id": ObjectId(updated_role["company_id"])})
        if company:
            updated_role["company_name"] = company.get("name")
    
    return RoleResponse(**updated_role)


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: str,
    current_user: UserInDB = Depends(require_admin)
):
    """
    Delete a role.
    """
    db = get_database()
    
    if not ObjectId.is_valid(role_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role ID format"
        )
    
    role = await db.roles.find_one({"_id": ObjectId(role_id)})
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    if role.get("is_system_role"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="System roles cannot be deleted"
        )
    
    user_count = await db.users.count_documents({
        "role_ids": role_id
    })
    
    if user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete role. {user_count} users are assigned to this role"
        )
    
    await db.roles.delete_one({"_id": ObjectId(role_id)})
    
    return None


@router.post("/{role_id}/assign-user/{user_id}", response_model=dict)
async def assign_role_to_user(
    role_id: str,
    user_id: str,
    current_user: UserInDB = Depends(require_admin)
):
    """
    Assign a role to a user.
    """
    db = get_database()
    
    if not ObjectId.is_valid(role_id) or not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format"
        )
    
    role = await db.roles.find_one({"_id": ObjectId(role_id)})
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if role.get("max_users"):
        current_users = await db.users.count_documents({
            "role_ids": role_id
        })
        if current_users >= role["max_users"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role has reached maximum user limit ({role['max_users']})"
            )
    
    if role_id not in user.get("role_ids", []):
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$addToSet": {"role_ids": role_id},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        return {"message": "Role assigned successfully"}
    else:
        return {"message": "User already has this role"}


@router.delete("/{role_id}/remove-user/{user_id}", response_model=dict)
async def remove_role_from_user(
    role_id: str,
    user_id: str,
    current_user: UserInDB = Depends(require_admin)
):
    """
    Remove a role from a user.
    """
    db = get_database()
    
    if not ObjectId.is_valid(role_id) or not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format"
        )
    
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if role_id in user.get("role_ids", []):
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$pull": {"role_ids": role_id},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        return {"message": "Role removed successfully"}
    else:
        return {"message": "User doesn't have this role"}


@router.get("/{role_id}/users", response_model=List[dict])
async def get_role_users(
    role_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get users assigned to a specific role.
    """
    db = get_database()
    
    if not ObjectId.is_valid(role_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role ID format"
        )
    
    role = await db.roles.find_one({"_id": ObjectId(role_id)})
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    skip = (page - 1) * page_size
    
    users = []
    async for user in db.users.find({"role_ids": role_id}).skip(skip).limit(page_size):
        users.append({
            "id": str(user["_id"]),
            "email": user.get("email"),
            "username": user.get("username"),
            "full_name": user.get("full_name"),
            "is_active": user.get("is_active"),
            "created_at": user.get("created_at")
        })
    
    return users