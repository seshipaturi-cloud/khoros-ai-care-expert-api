"""
Teams API endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from app.models.auth import UserInDB
from app.api.middleware.auth import get_current_user
from app.utils import get_database
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class Team(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class TeamCreate(BaseModel):
    name: str
    description: Optional[str] = None

class TeamListResponse(BaseModel):
    teams: List[Team]
    total: int

@router.get("/", response_model=TeamListResponse)
async def list_teams(
    current_user: UserInDB = Depends(get_current_user)
):
    """List all teams"""
    try:
        db = get_database()
        
        # For now, return an empty list since teams collection doesn't exist yet
        # In production, you would fetch from the teams collection
        teams = []
        
        # If you want to create some mock data:
        mock_teams = [
            {
                "id": "1",
                "name": "Customer Support",
                "description": "Handles customer inquiries",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "id": "2", 
                "name": "Technical Support",
                "description": "Handles technical issues",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "id": "3",
                "name": "Sales Team",
                "description": "Handles sales inquiries",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        
        return TeamListResponse(
            teams=[Team(**team) for team in mock_teams],
            total=len(mock_teams)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/", response_model=Team)
async def create_team(
    team_data: TeamCreate,
    current_user: UserInDB = Depends(get_current_user)
):
    """Create a new team"""
    # Check if user is admin
    if current_user.role not in ["super_admin", "company_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create teams"
        )
    
    try:
        db = get_database()
        
        # Create team document
        team_doc = {
            "id": str(datetime.utcnow().timestamp()),
            "name": team_data.name,
            "description": team_data.description,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": str(current_user.id)
        }
        
        # In production, insert into database
        # await db.teams.insert_one(team_doc)
        
        return Team(**team_doc)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{team_id}", response_model=Team)
async def get_team(
    team_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Get a specific team"""
    try:
        # Mock response for now
        team = {
            "id": team_id,
            "name": "Customer Support",
            "description": "Handles customer inquiries",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        return Team(**team)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/{team_id}")
async def delete_team(
    team_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Delete a team"""
    # Check if user is admin
    if current_user.role not in ["super_admin", "company_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete teams"
        )
    
    try:
        # In production, delete from database
        # db = get_database()
        # await db.teams.delete_one({"id": team_id})
        
        return {"message": "Team deleted successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )