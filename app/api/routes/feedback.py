from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime, timedelta
from uuid import uuid4
from app.models.feedback import (
    Feedback,
    FeedbackCreate,
    FeedbackUpdate,
    FeedbackCategory,
    FeedbackStatus,
    FeedbackListResponse,
    FeedbackStats
)

router = APIRouter(prefix="/feedback", tags=["feedback"])

# MongoDB connection
from app.utils.database import get_database
from bson import ObjectId

# In-memory storage for feedback (replace with MongoDB in production)
feedback_db: List[Feedback] = [
    Feedback(
        _id="fb001",
        uuid=str(uuid4()),
        case_id="CASE-12345",
        category=FeedbackCategory.AI_ANALYSIS,
        description="AI analysis missed the customer's frustrated tone. The sentiment was marked as neutral when it should have been negative.",
        agent="john.doe@example.com",
        module_id="mod_001",
        widget_uuid=None,
        timestamp=datetime.now() - timedelta(hours=5),
        resolved=False,
        updated_at=datetime.now() - timedelta(hours=5)
    ),
    Feedback(
        _id="fb002",
        uuid=str(uuid4()),
        case_id="CASE-12346",
        category=FeedbackCategory.AI_DRAFT_RESPONSE,
        description="The suggested response was too formal for our brand voice. We need more casual, friendly language.",
        agent="jane.smith@example.com",
        module_id="mod_002",
        widget_uuid="widget_abc123",
        timestamp=datetime.now() - timedelta(hours=12),
        resolved=True,
        updated_at=datetime.now() - timedelta(hours=2)
    ),
    Feedback(
        _id="fb003",
        uuid=str(uuid4()),
        case_id="CASE-12347",
        category=FeedbackCategory.AI_DRAFT_RESPONSE,
        description="AI response didn't include product-specific information from knowledge base.",
        agent="bob.wilson@example.com",
        module_id="mod_001",
        widget_uuid="widget_xyz789",
        timestamp=datetime.now() - timedelta(hours=24),
        resolved=False,
        updated_at=datetime.now() - timedelta(hours=24)
    ),
    Feedback(
        _id="fb004",
        uuid=str(uuid4()),
        case_id="CASE-12348",
        category=FeedbackCategory.AI_ANALYSIS,
        description="Priority classification was incorrect. This urgent issue was marked as low priority.",
        agent="alice.johnson@example.com",
        module_id=None,
        widget_uuid=None,
        timestamp=datetime.now() - timedelta(hours=48),
        resolved=True,
        updated_at=datetime.now() - timedelta(hours=24)
    ),
    Feedback(
        _id="fb005",
        uuid=str(uuid4()),
        case_id="CASE-12349",
        category=FeedbackCategory.GENERAL,
        description="AI suggestions are generally helpful but could be more contextual to our industry.",
        agent="charlie.brown@example.com",
        module_id="mod_003",
        widget_uuid=None,
        timestamp=datetime.now() - timedelta(days=3),
        resolved=False,
        updated_at=datetime.now() - timedelta(days=3)
    )
]

feedback_counter = len(feedback_db) + 1


def generate_feedback_id() -> str:
    """Generate unique feedback ID"""
    global feedback_counter
    feedback_id = f"fb{str(feedback_counter).zfill(3)}"
    feedback_counter += 1
    return feedback_id


@router.get("")
async def list_feedback(
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter by status (pending/resolved)"),
    agent: Optional[str] = Query(None, description="Filter by agent"),
    case_id: Optional[str] = Query(None, description="Filter by case ID"),
    limit: Optional[int] = Query(100, description="Maximum number of results"),
    skip: Optional[int] = Query(0, description="Offset for pagination")
):
    """
    Get all feedback from MongoDB with optional filtering
    """
    db = get_database()
    collection = db["agent_feedback"]

    # Build query filter
    query_filter = {}

    if category and category != 'all':
        query_filter["category"] = category

    if status and status != 'all':
        if status == 'pending':
            query_filter["is_resolved"] = False
        elif status == 'resolved':
            query_filter["is_resolved"] = True

    if agent:
        query_filter["agent_name"] = {"$regex": agent, "$options": "i"}

    if case_id:
        query_filter["case_id"] = {"$regex": case_id, "$options": "i"}

    # Get total count
    total_count = await collection.count_documents({})
    filtered_count = await collection.count_documents(query_filter)

    # Fetch paginated results
    cursor = collection.find(query_filter).sort("created_at", -1).skip(skip).limit(limit)
    feedback_items = await cursor.to_list(length=limit)

    # Convert ObjectId to string for JSON serialization
    for item in feedback_items:
        item["_id"] = str(item["_id"])

    return {
        "items": feedback_items,
        "total": total_count,
        "filtered": filtered_count
    }


@router.post("", status_code=201)
async def create_feedback(feedback_data: dict):
    """
    Create a new feedback entry in MongoDB
    Automatically extracts user context from _user_context field
    """
    db = get_database()
    collection = db["agent_feedback"]

    # Extract user context if present (sent by apiClient)
    user_context = feedback_data.pop("_user_context", {})

    # Prepare feedback document with user context at root level
    feedback_doc = {
        **feedback_data,

        # User information from context
        "user_id": user_context.get("user_id"),
        "agent_name": user_context.get("user_name") or feedback_data.get("agent_name", "Unknown Agent"),
        "user_email": user_context.get("user_email"),
        "user_title": user_context.get("user_title"),
        "user_roles": user_context.get("user_roles", []),

        # Company information from context
        "company_id": user_context.get("company_id"),
        "company_name": user_context.get("company_name"),
        "company_key": user_context.get("company_key"),

        # Team information from context
        "team_id": user_context.get("team_id"),
        "team_name": user_context.get("team_name"),

        # Timestamps
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "submitted_at": user_context.get("timestamp") or datetime.utcnow().isoformat()
    }

    # Ensure is_resolved field exists
    if "is_resolved" not in feedback_doc:
        feedback_doc["is_resolved"] = False

    # Log what we're saving (for debugging)
    print(f"💾 Saving feedback with user context: user_id={feedback_doc.get('user_id')}, company_id={feedback_doc.get('company_id')}, case_id={feedback_doc.get('case_id')}")

    # Insert into MongoDB
    result = await collection.insert_one(feedback_doc)

    # Return the created document
    feedback_doc["_id"] = str(result.inserted_id)
    return feedback_doc


@router.get("/stats")
async def get_feedback_stats():
    """
    Get feedback statistics from MongoDB
    """
    db = get_database()
    collection = db["agent_feedback"]

    # Get counts
    total_feedback = await collection.count_documents({})
    pending = await collection.count_documents({"is_resolved": False})
    resolved = await collection.count_documents({"is_resolved": True})

    # Count by category
    categories = await collection.aggregate([
        {"$group": {"_id": "$category", "count": {"$sum": 1}}}
    ]).to_list(length=None)

    by_category = {cat["_id"]: cat["count"] for cat in categories}

    return {
        "total_feedback": total_feedback,
        "pending": pending,
        "resolved": resolved,
        "by_category": by_category
    }


@router.get("/{feedback_id}")
async def get_feedback(feedback_id: str):
    """
    Get a specific feedback by ID from MongoDB
    """
    db = get_database()
    collection = db["agent_feedback"]

    try:
        # Try to find by ObjectId
        feedback = await collection.find_one({"_id": ObjectId(feedback_id)})
    except:
        # If invalid ObjectId, return not found
        raise HTTPException(status_code=404, detail=f"Feedback {feedback_id} not found")

    if not feedback:
        raise HTTPException(status_code=404, detail=f"Feedback {feedback_id} not found")

    # Convert ObjectId to string
    feedback["_id"] = str(feedback["_id"])
    return feedback


@router.put("/{feedback_id}")
async def update_feedback(feedback_id: str, update_data: FeedbackUpdate):
    """
    Update feedback details
    """
    feedback = next(
        (f for f in feedback_db if f.id == feedback_id or f.uuid == feedback_id),
        None
    )

    if not feedback:
        raise HTTPException(status_code=404, detail=f"Feedback {feedback_id} not found")

    # Update fields
    if update_data.category is not None:
        feedback.category = update_data.category

    if update_data.description is not None:
        feedback.description = update_data.description

    if update_data.resolved is not None:
        feedback.resolved = update_data.resolved

    feedback.updated_at = datetime.now()

    return feedback


@router.put("/{feedback_id}/resolve")
async def resolve_feedback(feedback_id: str):
    """
    Mark feedback as resolved in MongoDB
    """
    db = get_database()
    collection = db["agent_feedback"]

    try:
        result = await collection.update_one(
            {"_id": ObjectId(feedback_id)},
            {
                "$set": {
                    "is_resolved": True,
                    "resolved_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail=f"Feedback {feedback_id} not found")

        # Return updated document
        feedback = await collection.find_one({"_id": ObjectId(feedback_id)})
        feedback["_id"] = str(feedback["_id"])
        return feedback

    except Exception as e:
        if "not found" in str(e):
            raise
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{feedback_id}", status_code=204)
async def delete_feedback(feedback_id: str):
    """
    Delete feedback entry
    """
    global feedback_db

    feedback = next(
        (f for f in feedback_db if f.id == feedback_id or f.uuid == feedback_id),
        None
    )

    if not feedback:
        raise HTTPException(status_code=404, detail=f"Feedback {feedback_id} not found")

    feedback_db = [f for f in feedback_db if f.id != feedback.id and f.uuid != feedback.uuid]

    return None
