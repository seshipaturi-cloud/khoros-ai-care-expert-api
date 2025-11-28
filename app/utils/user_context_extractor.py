"""
User Context Extractor Utility
Extracts user context from HTTP headers and request body for audit trails
"""

from typing import Optional, Dict, Any
from fastapi import Request
from urllib.parse import unquote
from app.models.user_context import UserContext, UserInfo, CompanyInfo
import logging

logger = logging.getLogger(__name__)


def extract_user_context_from_headers(request: Request) -> UserContext:
    """
    Extract user context from HTTP headers sent by frontend

    Headers sent by frontend:
    - X-User-Id
    - X-User-Name
    - X-User-Email
    - X-User-Team-Id
    - X-User-Team-Name
    - X-Company-Id
    - X-Company-Key
    - X-Company-Name
    """
    try:
        # Extract user information from headers
        user_info = UserInfo(
            id=request.headers.get("x-user-id"),
            name=unquote(request.headers.get("x-user-name", "")) if request.headers.get("x-user-name") else None,
            email=unquote(request.headers.get("x-user-email", "")) if request.headers.get("x-user-email") else None,
            team_id=request.headers.get("x-user-team-id"),
            team_name=unquote(request.headers.get("x-user-team-name", "")) if request.headers.get("x-user-team-name") else None,
        )

        # Extract company information from headers
        company_info = CompanyInfo(
            id=request.headers.get("x-company-id"),
            key=unquote(request.headers.get("x-company-key", "")) if request.headers.get("x-company-key") else None,
            name=unquote(request.headers.get("x-company-name", "")) if request.headers.get("x-company-name") else None,
        )

        # Get client IP and user agent
        client_host = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        return UserContext(
            user=user_info if user_info.id else None,
            company=company_info if company_info.id else None,
            ip_address=client_host,
            user_agent=user_agent
        )
    except Exception as e:
        logger.warning(f"Failed to extract user context from headers: {e}")
        return UserContext()


def extract_user_context_from_body(body: Dict[str, Any]) -> Optional[UserContext]:
    """
    Extract user context from request body _userContext field

    Body structure:
    {
        "...": "your data",
        "_userContext": {
            "user": {...},
            "company": {...}
        }
    }
    """
    try:
        if "_userContext" in body and isinstance(body["_userContext"], dict):
            user_context_data = body["_userContext"]

            user_info = None
            if "user" in user_context_data and isinstance(user_context_data["user"], dict):
                user_data = user_context_data["user"]
                user_info = UserInfo(
                    id=user_data.get("id"),
                    name=user_data.get("name"),
                    email=user_data.get("email"),
                    title=user_data.get("title"),
                    team_id=user_data.get("teamId"),
                    team_name=user_data.get("teamName"),
                    role_types=user_data.get("roleTypes", []),
                    department=user_data.get("department"),
                    locale=user_data.get("locale")
                )

            company_info = None
            if "company" in user_context_data and isinstance(user_context_data["company"], dict):
                company_data = user_context_data["company"]
                company_info = CompanyInfo(
                    id=company_data.get("id"),
                    key=company_data.get("key"),
                    name=company_data.get("name")
                )

            return UserContext(
                user=user_info,
                company=company_info
            )
    except Exception as e:
        logger.warning(f"Failed to extract user context from body: {e}")

    return None


def get_user_context(request: Request, body: Optional[Dict[str, Any]] = None) -> UserContext:
    """
    Get user context from request - tries headers first, then body

    Args:
        request: FastAPI Request object
        body: Optional request body dict

    Returns:
        UserContext object with user and company information
    """
    # Try to get from headers first
    context = extract_user_context_from_headers(request)

    # If body is provided and headers didn't have full info, merge from body
    if body:
        body_context = extract_user_context_from_body(body)
        if body_context:
            # Merge contexts - body context takes precedence for more detailed info
            if body_context.user:
                context.user = body_context.user
            if body_context.company:
                context.company = body_context.company

    return context


def remove_user_context_from_body(body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove _userContext from request body to get clean data for processing

    Args:
        body: Request body dict

    Returns:
        Body without _userContext field
    """
    if "_userContext" in body:
        body_copy = body.copy()
        del body_copy["_userContext"]
        return body_copy
    return body
