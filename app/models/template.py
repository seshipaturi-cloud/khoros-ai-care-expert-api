from pydantic import BaseModel, Field, GetJsonSchemaHandler, field_validator
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
from typing import Optional, List, Dict, Any, Annotated
from datetime import datetime
from bson import ObjectId

class PyObjectId(str):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: Any
    ) -> core_schema.CoreSchema:
        return core_schema.union_schema(
            [
                core_schema.is_instance_schema(ObjectId),
                core_schema.chain_schema(
                    [
                        core_schema.str_schema(),
                        core_schema.no_info_plain_validator_function(cls.validate),
                    ]
                ),
            ],
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x),
                return_schema=core_schema.str_schema(),
            ),
        )

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if ObjectId.is_valid(v):
            return ObjectId(v)
        raise ValueError("Invalid ObjectId")

    @classmethod
    def __get_pydantic_json_schema__(
        cls, schema: JsonSchemaValue, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        schema = handler(schema)
        schema.update(type="string", format="objectid")
        return schema

class ReportTemplate(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    template_url: str = Field(..., description="S3 URL of the template")
    template_content: Optional[str] = Field(None, description="Template HTML content")
    placeholders: Optional[List[str]] = Field(default_factory=list, description="List of placeholders in template")
    category: Optional[str] = Field("custom", description="Template category")
    tags: Optional[List[str]] = Field(default_factory=list, description="Template tags")
    is_active: bool = Field(True, description="Whether template is active")
    created_by: Optional[str] = Field(None, description="User ID who created the template")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # S3 related fields
    s3_bucket: Optional[str] = Field(None, description="S3 bucket name")
    s3_key: Optional[str] = Field(None, description="S3 object key")
    
    # Usage tracking
    usage_count: int = Field(0, description="Number of times template has been used")
    last_used_at: Optional[datetime] = Field(None, description="Last time template was used")
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {
            ObjectId: str,
            datetime: lambda v: v.isoformat() if v else None
        },
        "json_schema_extra": {
            "example": {
                "name": "Monthly Sales Report",
                "description": "Template for generating monthly sales reports",
                "template_url": "https://s3.amazonaws.com/bucket/templates/monthly_sales.html",
                "category": "sales",
                "tags": ["sales", "monthly", "revenue"],
                "is_active": True
            }
        }
    }

class TemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    template_content: Optional[str] = None
    template_url: Optional[str] = None
    category: Optional[str] = "custom"
    tags: Optional[List[str]] = Field(default_factory=list)
    is_active: bool = True

class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    template_content: Optional[str] = None
    template_url: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None

class TemplateUpload(BaseModel):
    template_content: str = Field(..., description="HTML template content")
    template_name: str = Field(..., description="Name for the template file")
    file_type: str = Field("html", description="File type/extension")

class TemplateResponse(BaseModel):
    success: bool
    data: Optional[ReportTemplate] = None
    message: Optional[str] = None

class TemplateListResponse(BaseModel):
    success: bool
    data: List[ReportTemplate] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    limit: int = 10
    message: Optional[str] = None

class TemplatePlaceholder(BaseModel):
    name: str
    description: Optional[str] = None
    data_type: str = "string"  # string, number, date, table, etc.
    required: bool = True
    default_value: Optional[Any] = None
    
class TemplateGenerateRequest(BaseModel):
    template_id: str
    placeholders_data: Dict[str, Any]
    output_name: Optional[str] = None
    output_format: str = "html"  # html, pdf, docx