from pydantic import BaseModel, Field


class ChildContext(BaseModel):
    child_id: int | None = Field(default=None)
    name: str
    age: int | None = Field(default=None)
    concerns: list[str] = Field(default_factory=list)


class SearchSuggestionRequest(BaseModel):
    user_id: int | None = Field(default=None)
    children: list[ChildContext] = Field(default_factory=list)
    recent_searches: list[str] = Field(default_factory=list)
    global_keywords: list[str] = Field(default_factory=list)
    limit: int = Field(default=10, ge=1, le=10)


class SearchSuggestionResponse(BaseModel):
    suggestions: list[str]
    source: str
