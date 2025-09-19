from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship


class PromptTag(SQLModel, table=True):
    """Many-to-many relationship table between prompts and tags"""
    prompt_id: int = Field(foreign_key="prompt.id", primary_key=True)
    tag_id: int = Field(foreign_key="tag.id", primary_key=True)


class Tag(SQLModel, table=True):
    """Tag model for categorizing prompts"""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    
    # Relationship to prompts through the junction table
    prompts: List["Prompt"] = Relationship(back_populates="tags", link_model=PromptTag)


class PromptVersion(SQLModel, table=True):
    """Version history for prompts"""
    id: Optional[int] = Field(default=None, primary_key=True)
    prompt_id: int = Field(foreign_key="prompt.id")
    content: str
    version: str
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Relationship to parent prompt
    prompt: Optional["Prompt"] = Relationship(back_populates="versions")


class Prompt(SQLModel, table=True):
    """Main prompt model"""
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    content: str
    version: str = Field(default="1.0")
    model_type: str = Field(index=True)  # e.g., "gpt-4", "claude", "llama-2"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Relationships
    tags: List[Tag] = Relationship(back_populates="prompts", link_model=PromptTag)
    versions: List[PromptVersion] = Relationship(back_populates="prompt")


# Pydantic models for API requests/responses
class PromptCreate(SQLModel):
    """Model for creating new prompts"""
    title: str
    content: str
    model_type: str
    tag_names: List[str] = []


class PromptUpdate(SQLModel):
    """Model for updating prompts"""
    title: Optional[str] = None
    content: Optional[str] = None
    model_type: Optional[str] = None
    tag_names: Optional[List[str]] = None
