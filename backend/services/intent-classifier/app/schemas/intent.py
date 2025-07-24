"""Intent classification schemas."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class IntentRequest(BaseModel):
    """Request model for intent classification."""
    
    text: str = Field(
        ...,
        description="The user input text to classify",
        min_length=1,
        max_length=5000,
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional context for classification",
    )
    user_id: Optional[str] = Field(
        default=None,
        description="User ID for personalization",
    )


class IntentResponse(BaseModel):
    """Response model for intent classification."""
    
    model_config = ConfigDict(from_attributes=True)
    
    intent: str = Field(
        ...,
        description="The classified intent type",
    )
    confidence: float = Field(
        ...,
        description="Confidence score (0-1)",
        ge=0.0,
        le=1.0,
    )
    complexity: str = Field(
        ...,
        description="Task complexity level",
        pattern="^(simple|moderate|complex)$",
    )
    suggested_techniques: List[str] = Field(
        ...,
        description="Suggested prompt engineering techniques",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata",
    )


class IntentBatchRequest(BaseModel):
    """Request model for batch intent classification."""
    
    texts: List[str] = Field(
        ...,
        description="List of texts to classify",
        min_length=1,
        max_length=100,
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Shared context for all texts",
    )
    user_id: Optional[str] = Field(
        default=None,
        description="User ID for personalization",
    )


class IntentBatchResponse(BaseModel):
    """Response model for batch intent classification."""
    
    results: List[IntentResponse] = Field(
        ...,
        description="Classification results for each text",
    )
    total_processing_time: float = Field(
        ...,
        description="Total processing time in seconds",
    )


class IntentFeedback(BaseModel):
    """Feedback model for intent classification corrections."""
    
    text: str = Field(
        ...,
        description="The original user input text",
        min_length=1,
        max_length=5000,
    )
    original_intent: str = Field(
        ...,
        description="The originally classified intent",
    )
    correct_intent: str = Field(
        ...,
        description="The correct intent provided by user",
    )
    original_confidence: float = Field(
        ...,
        description="The original confidence score",
        ge=0.0,
        le=1.0,
    )
    correct_complexity: Optional[str] = Field(
        default=None,
        description="The correct complexity level if provided",
        pattern="^(simple|moderate|complex)$",
    )
    correct_techniques: Optional[List[str]] = Field(
        default=None,
        description="The correct techniques if provided",
    )
    user_id: Optional[str] = Field(
        default=None,
        description="User ID who provided the feedback",
    )
    feedback_type: str = Field(
        default="correction",
        description="Type of feedback (correction, confirmation)",
        pattern="^(correction|confirmation)$",
    )
    timestamp: Optional[str] = Field(
        default=None,
        description="Timestamp when feedback was provided",
    )


class IntentFeedbackResponse(BaseModel):
    """Response model for feedback submission."""
    
    status: str = Field(
        ...,
        description="Feedback submission status",
    )
    message: str = Field(
        ...,
        description="Response message",
    )
    feedback_id: str = Field(
        ...,
        description="Unique identifier for the feedback",
    )
    cache_updated: bool = Field(
        ...,
        description="Whether the cache was updated",
    )