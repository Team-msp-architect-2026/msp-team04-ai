from pydantic import BaseModel, Field


class EmbeddingRequest(BaseModel):
    source_id: int | None = Field(default=None, alias="sourceId")
    source_type: str = Field(alias="sourceType")
    text: str = Field(min_length=1)

    model_config = {
        "populate_by_name": True,
    }


class EmbeddingResponse(BaseModel):
    source_id: int | None = Field(default=None, alias="sourceId")
    source_type: str = Field(alias="sourceType")
    vector: list[float]
    success: bool

    model_config = {
        "populate_by_name": True,
    }
