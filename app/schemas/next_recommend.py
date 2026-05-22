from pydantic import BaseModel, Field


class NextRecommendChild(BaseModel):
    child_id: int | None = Field(default=None, alias="childId")
    age: int | None = None
    concerns: list[str] = Field(default_factory=list)

    model_config = {
        "populate_by_name": True,
    }


class NextRecommendAppliedProgram(BaseModel):
    program_id: int = Field(alias="programId")
    title: str
    category: str | None = None
    description: str | None = ""
    class_time: str | None = Field(default=None, alias="classTime")
    price: int | None = None
    is_free: bool | None = Field(default=None, alias="isFree")
    rating_avg: float | None = Field(default=None, alias="ratingAvg")

    model_config = {
        "populate_by_name": True,
    }


class NextRecommendCandidateProgram(BaseModel):
    program_id: int = Field(alias="programId")
    title: str
    category: str | None = None
    description: str | None = ""
    class_time: str | None = Field(default=None, alias="classTime")
    price: int | None = None
    is_free: bool | None = Field(default=None, alias="isFree")
    rating_avg: float | None = Field(default=None, alias="ratingAvg")
    reason_basis: str | None = Field(default="", alias="reasonBasis")

    model_config = {
        "populate_by_name": True,
    }


class NextRecommendRequest(BaseModel):
    child: NextRecommendChild
    applied_program: NextRecommendAppliedProgram = Field(alias="appliedProgram")
    candidates: list[NextRecommendCandidateProgram] = Field(min_length=1, max_length=3)

    model_config = {
        "populate_by_name": True,
    }


class NextRecommendItem(BaseModel):
    program_id: int = Field(alias="programId")
    title: str
    explain_message: str = Field(alias="explainMessage")
    highlight_tag: str = Field(alias="highlightTag")

    model_config = {
        "populate_by_name": True,
    }


class NextRecommendResponse(BaseModel):
    message: str
    items: list[NextRecommendItem]
    source: str

    model_config = {
        "populate_by_name": True,
    }
