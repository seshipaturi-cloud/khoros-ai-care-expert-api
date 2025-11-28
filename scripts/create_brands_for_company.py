#!/usr/bin/env python3
"""
Script to create brands for a specific company
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from bson import ObjectId

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils import get_database

async def create_brands_for_financefirst():
    """Create brands for FinanceFirst Bank"""
    db = get_database()
    
    print("Step 1: Finding the company and user...")
    
    # Find the user
    user = await db.users.find_one({"email": "admin@financefirstbank.com"})
    if not user:
        print("Error: User admin@financefirstbank.com not found!")
        return
    
    print(f"Found user: {user.get('full_name', user.get('username'))}")
    
    # Get company_id from user
    company_id = user.get("company_id")
    if not company_id:
        print("Error: User has no company_id!")
        return
    
    # Find the company
    company = await db.companies.find_one({"_id": company_id}) or \
               await db.companies.find_one({"_id": ObjectId(company_id)}) if ObjectId.is_valid(company_id) else None
    
    if not company:
        print(f"Error: Company with ID {company_id} not found!")
        return
    
    company_name = company.get("name", "Unknown Company")
    print(f"Found company: {company_name}")
    
    print("\nStep 2: Creating brands for FinanceFirst Bank...")
    
    # Define brands for FinanceFirst Bank
    brands = [
        {
            "company_id": str(company_id),
            "name": "FinanceFirst Personal Banking",
            "code": "FFB-PERSONAL",
            "industry": "Financial Services - Personal Banking",
            "website": "https://personal.financefirstbank.com",
            "description": "Personal banking services including checking, savings, and personal loans",
            "voice_settings": {
                "tone": "friendly",
                "personality_traits": ["helpful", "trustworthy", "patient", "knowledgeable"],
                "language_style": "simple",
                "response_style": "empathetic",
                "greeting_template": "Hello! Welcome to FinanceFirst Personal Banking. How can I help you today?",
                "closing_template": "Thank you for choosing FinanceFirst. Have a wonderful day!",
                "forbidden_phrases": ["guarantee returns", "risk-free", "insider information"],
                "preferred_phrases": ["we're here to help", "your financial well-being", "secure banking"],
                "custom_instructions": "Always prioritize customer security and privacy. Be clear about fees and terms."
            },
            "ai_settings": {
                "default_llm_provider": "openai",
                "default_llm_model": "gpt-4",
                "temperature": 0.7,
                "max_response_length": 500,
                "enable_knowledge_base": True,
                "enable_auto_response": False,
                "response_time_sla_seconds": 30,
                "escalation_threshold": 3,
                "sentiment_analysis_enabled": True,
                "language_detection_enabled": True
            },
            "social_settings": {
                "platforms_enabled": ["twitter", "facebook", "instagram"],
                "auto_publish": False,
                "moderation_enabled": True,
                "hashtags": ["#FinanceFirst", "#PersonalBanking", "#YourMoneyMatters"],
                "mentions_monitoring": True
            },
            "support_email": "support.personal@financefirstbank.com",
            "support_phone": "+1-800-555-0100",
            "timezone": "America/New_York",
            "primary_color": "#1E3A8A",  # Dark blue
            "secondary_color": "#3B82F6",  # Lighter blue
            "status": "active",
            "metadata": {
                "target_audience": "Individual customers",
                "service_types": ["checking", "savings", "credit_cards", "personal_loans", "mortgages"]
            }
        },
        {
            "company_id": str(company_id),
            "name": "FinanceFirst Business Banking",
            "code": "FFB-BUSINESS",
            "industry": "Financial Services - Business Banking",
            "website": "https://business.financefirstbank.com",
            "description": "Business banking solutions for small to medium enterprises",
            "voice_settings": {
                "tone": "professional",
                "personality_traits": ["knowledgeable", "efficient", "reliable", "solution-oriented"],
                "language_style": "technical",
                "response_style": "concise",
                "greeting_template": "Welcome to FinanceFirst Business Banking. How may I assist your business today?",
                "closing_template": "Thank you for trusting FinanceFirst with your business banking needs.",
                "forbidden_phrases": ["guaranteed approval", "no documentation needed", "bypass regulations"],
                "preferred_phrases": ["business growth", "financial solutions", "competitive rates", "dedicated support"],
                "custom_instructions": "Focus on business efficiency and growth. Provide clear information about commercial products."
            },
            "ai_settings": {
                "default_llm_provider": "openai",
                "default_llm_model": "gpt-4",
                "temperature": 0.5,
                "max_response_length": 600,
                "enable_knowledge_base": True,
                "enable_auto_response": False,
                "response_time_sla_seconds": 45,
                "escalation_threshold": 2,
                "sentiment_analysis_enabled": True,
                "language_detection_enabled": True
            },
            "social_settings": {
                "platforms_enabled": ["linkedin", "twitter"],
                "auto_publish": False,
                "moderation_enabled": True,
                "hashtags": ["#BusinessBanking", "#FinanceFirst", "#GrowYourBusiness", "#SMEBanking"],
                "mentions_monitoring": True
            },
            "support_email": "business.support@financefirstbank.com",
            "support_phone": "+1-800-555-0200",
            "timezone": "America/New_York",
            "primary_color": "#059669",  # Green
            "secondary_color": "#10B981",  # Lighter green
            "status": "active",
            "metadata": {
                "target_audience": "Small and medium businesses",
                "service_types": ["business_checking", "merchant_services", "business_loans", "cash_management", "payroll"]
            }
        },
        {
            "company_id": str(company_id),
            "name": "FinanceFirst Wealth Management",
            "code": "FFB-WEALTH",
            "industry": "Financial Services - Wealth Management",
            "website": "https://wealth.financefirstbank.com",
            "description": "Premium wealth management and investment advisory services",
            "voice_settings": {
                "tone": "formal",
                "personality_traits": ["sophisticated", "discreet", "expert", "consultative"],
                "language_style": "formal",
                "response_style": "detailed",
                "greeting_template": "Good day. Welcome to FinanceFirst Wealth Management. How may we assist with your investment needs?",
                "closing_template": "We appreciate your trust in FinanceFirst Wealth Management. Please don't hesitate to reach out for any further assistance.",
                "forbidden_phrases": ["guaranteed profits", "insider tips", "can't lose", "hot stock tips"],
                "preferred_phrases": ["portfolio optimization", "risk management", "long-term growth", "wealth preservation"],
                "custom_instructions": "Maintain a sophisticated, professional tone. Always include appropriate disclaimers about investment risks."
            },
            "ai_settings": {
                "default_llm_provider": "openai",
                "default_llm_model": "gpt-4",
                "temperature": 0.3,
                "max_response_length": 800,
                "enable_knowledge_base": True,
                "enable_auto_response": False,
                "response_time_sla_seconds": 60,
                "escalation_threshold": 1,
                "sentiment_analysis_enabled": True,
                "language_detection_enabled": True
            },
            "social_settings": {
                "platforms_enabled": ["linkedin"],
                "auto_publish": False,
                "moderation_enabled": True,
                "hashtags": ["#WealthManagement", "#FinanceFirst", "#InvestmentStrategy", "#FinancialPlanning"],
                "mentions_monitoring": True
            },
            "support_email": "wealth@financefirstbank.com",
            "support_phone": "+1-800-555-0300",
            "timezone": "America/New_York",
            "primary_color": "#7C3AED",  # Purple
            "secondary_color": "#A78BFA",  # Lighter purple
            "status": "active",
            "metadata": {
                "target_audience": "High net worth individuals",
                "service_types": ["investment_advisory", "estate_planning", "tax_planning", "trust_services", "private_banking"],
                "minimum_assets": "$250,000"
            }
        }
    ]
    
    # Create each brand
    created_count = 0
    for brand_data in brands:
        try:
            # Check if brand already exists
            existing_brand = await db.brands.find_one({
                "company_id": brand_data["company_id"],
                "code": brand_data["code"]
            })
            
            if existing_brand:
                print(f"  ⚠️  Brand {brand_data['name']} already exists, skipping...")
                continue
            
            # Add timestamps
            brand_data["created_at"] = datetime.utcnow()
            brand_data["updated_at"] = datetime.utcnow()
            brand_data["created_by"] = str(user["_id"])
            brand_data["updated_by"] = str(user["_id"])
            
            # Insert brand
            result = await db.brands.insert_one(brand_data)
            print(f"  ✓ Created brand: {brand_data['name']} (Code: {brand_data['code']})")
            created_count += 1
            
        except Exception as e:
            print(f"  ✗ Error creating brand {brand_data['name']}: {e}")
    
    print(f"\n✅ Successfully created {created_count} brands for {company_name}!")
    
    # List all brands for this company
    print(f"\n📊 All brands for {company_name}:")
    async for brand in db.brands.find({"company_id": str(company_id)}):
        print(f"  - {brand.get('name')} ({brand.get('code')})")

async def main():
    # Connect to MongoDB
    from app.utils import connect_to_mongo, close_mongo_connection
    
    try:
        await connect_to_mongo()
        await create_brands_for_financefirst()
    finally:
        await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(main())