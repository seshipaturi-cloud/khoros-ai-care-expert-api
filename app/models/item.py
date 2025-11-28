from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class ItemModel(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    quantity: int = Field(..., ge=0)
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Laptop",
                "description": "High-performance laptop for development",
                "price": 1299.99,
                "quantity": 10,
                "category": "Electronics",
                "tags": ["computer", "technology", "work"]
            }
        }