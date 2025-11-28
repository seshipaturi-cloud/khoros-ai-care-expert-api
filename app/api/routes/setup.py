"""
Setup Wizard API Routes - Public endpoints for first-time setup
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
from app.models.company import (
    SetupInitRequest,
    SetupInitResponse,
    SetupUpdateRequest,
    SetupCompleteRequest,
    CompanyResponse
)
from app.services.company_service import company_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/aicareexpert/setup", tags=["setup"])


@router.post("/initialize", response_model=SetupInitResponse)
async def initialize_setup(request: SetupInitRequest):
    """
    Initialize setup for a company - checks if company exists and returns setup status
    PUBLIC ENDPOINT - No authentication required

    This endpoint is called when user first accesses /console/aicareexpert
    """
    try:
        logger.info(f"Initializing setup for company: {request.company_name}, user: {request.user_email}")

        result = await company_service.initialize_setup(request)

        logger.info(
            f"Setup initialized for {request.company_name}: "
            f"company_id={result.company_id}, "
            f"should_show_setup={result.should_show_setup}, "
            f"is_complete={result.is_setup_complete}"
        )

        return result

    except ValueError as e:
        logger.error(f"Validation error during setup initialization: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error initializing setup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize setup"
        )


@router.post("/update", response_model=Dict[str, Any])
async def update_setup(request: SetupUpdateRequest):
    """
    Update setup configuration and progress
    PUBLIC ENDPOINT - No authentication required

    Called as user progresses through setup wizard steps
    """
    try:
        logger.info(
            f"Updating setup for company {request.company_id}: "
            f"step={request.setup_step}"
        )

        success = await company_service.update_setup(
            company_id=request.company_id,
            setup_step=request.setup_step,
            configuration=request.configuration
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )

        return {
            "success": True,
            "message": f"Setup updated to step {request.setup_step}",
            "company_id": request.company_id,
            "setup_step": request.setup_step
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating setup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update setup"
        )


@router.post("/complete", response_model=CompanyResponse)
async def complete_setup(request: SetupCompleteRequest):
    """
    Complete the setup process
    PUBLIC ENDPOINT - No authentication required

    Called when user completes all setup steps and confirms
    """
    try:
        logger.info(f"Completing setup for company {request.company_id}")

        # Validate that terms are accepted
        if not request.configuration.terms_accepted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Terms and conditions must be accepted to complete setup"
            )

        company = await company_service.complete_setup(
            company_id=request.company_id,
            configuration=request.configuration
        )

        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )

        logger.info(f"Setup completed successfully for company {request.company_id}")

        return company

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing setup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete setup"
        )


@router.get("/features")
async def get_available_features():
    """
    Get list of available AI features that can be selected during setup
    PUBLIC ENDPOINT - No authentication required
    """
    return {
        "features": [
            {
                "id": "ai_response_drafting",
                "name": "AI Response Drafting",
                "description": "AI suggests complete responses to customer messages",
                "icon": "edit",
                "popular": True
            },
            {
                "id": "sentiment_analysis",
                "name": "Sentiment Analysis",
                "description": "Automatic detection of customer emotion and sentiment",
                "icon": "smile",
                "popular": True
            },
            {
                "id": "auto_categorization",
                "name": "Auto Categorization",
                "description": "Automatically categorize and tag incoming messages",
                "icon": "tags",
                "popular": True
            },
            {
                "id": "priority_detection",
                "name": "Priority Detection",
                "description": "Identify urgent messages requiring immediate attention",
                "icon": "alert-circle",
                "popular": False
            },
            {
                "id": "language_translation",
                "name": "Language Translation",
                "description": "Real-time translation for multilingual support",
                "icon": "globe",
                "popular": False
            },
            {
                "id": "knowledge_base_search",
                "name": "Knowledge Base Search",
                "description": "AI-powered search through your knowledge base",
                "icon": "search",
                "popular": True
            },
            {
                "id": "smart_routing",
                "name": "Smart Routing",
                "description": "Intelligently route messages to the right agent",
                "icon": "share-2",
                "popular": False
            },
            {
                "id": "canned_response_suggestions",
                "name": "Canned Response Suggestions",
                "description": "Suggest relevant pre-written responses",
                "icon": "file-text",
                "popular": False
            }
        ]
    }


@router.get("/subscription-plans")
async def get_subscription_plans():
    """
    Get available subscription plans
    PUBLIC ENDPOINT - No authentication required
    """
    return {
        "plans": [
            {
                "id": "starter",
                "name": "Starter",
                "price_monthly": 99,
                "price_yearly": 950,
                "description": "Perfect for small teams getting started with AI",
                "features": [
                    "Up to 5 brands",
                    "Up to 10 AI agents",
                    "Up to 20 users",
                    "1,000 knowledge base items",
                    "10 GB storage",
                    "Basic AI features",
                    "Email support"
                ],
                "limits": {
                    "max_brands": 5,
                    "max_agents": 10,
                    "max_users": 20,
                    "max_knowledge_items": 1000,
                    "storage_gb": 10
                },
                "popular": False
            },
            {
                "id": "professional",
                "name": "Professional",
                "price_monthly": 299,
                "price_yearly": 2850,
                "description": "For growing teams with advanced AI needs",
                "features": [
                    "Up to 20 brands",
                    "Up to 50 AI agents",
                    "Up to 100 users",
                    "10,000 knowledge base items",
                    "100 GB storage",
                    "Advanced AI features",
                    "Custom LLM integration",
                    "Priority support"
                ],
                "limits": {
                    "max_brands": 20,
                    "max_agents": 50,
                    "max_users": 100,
                    "max_knowledge_items": 10000,
                    "storage_gb": 100
                },
                "popular": True
            },
            {
                "id": "enterprise",
                "name": "Enterprise",
                "price_monthly": 999,
                "price_yearly": 9500,
                "description": "For large organizations requiring enterprise features",
                "features": [
                    "Unlimited brands",
                    "Unlimited AI agents",
                    "Unlimited users",
                    "Unlimited knowledge base items",
                    "1 TB storage",
                    "All AI features",
                    "Custom LLM integration",
                    "Multi-language support",
                    "API access",
                    "Dedicated account manager",
                    "24/7 premium support"
                ],
                "limits": {
                    "max_brands": 1000,
                    "max_agents": 10000,
                    "max_users": 100000,
                    "max_knowledge_items": 1000000,
                    "storage_gb": 1000
                },
                "popular": False
            }
        ]
    }
