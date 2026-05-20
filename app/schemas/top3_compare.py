from pydantic import BaseModel, Field


class Top3CompareChild(BaseModel):
    child_id: int = Field(alias="childId")
    age: int | None = None
    concerns: list[str] = Field(default_factory=list)

    model_config = {
        "populate_by_name": True,
    }


class Top3ComparePreference(BaseModel):
    preference_id: int = Field(alias="preferenceId")
    region: str | None = None
    monthly_budget: str | None = Field(default=None, alias="monthlyBudget")
    transport_type: str | None = Field(default=None, alias="transportType")
    move_time: str | None = Field(default=None, alias="moveTime")
    online_preference: str | None = Field(default=None, alias="onlinePreference")
    class_type: str | None = Field(default=None, alias="classType")

    model_config = {
        "populate_by_name": True,
    }


class Top3CompareProgram(BaseModel):
    program_id: int = Field(alias="programId")
    title: str
    category: str | None = None
    description: str | None = ""
    region: str | None = None
    price: int | None = None
    is_free: bool | None = Field(default=None, alias="isFree")
    class_type: str | None = Field(default=None, alias="classType")
    rating_avg: float | None = Field(default=None, alias="ratingAvg")
    review_count: int | None = Field(default=None, alias="reviewCount")
    rank_no: int = Field(alias="rankNo")
    total_score: float = Field(alias="totalScore")
    recommend_reason: str | None = Field(default="", alias="recommendReason")
    score_breakdown: dict[str, float | None] = Field(default_factory=dict, alias="scoreBreakdown")

    model_config = {
        "populate_by_name": True,
    }


class Top3CompareRequest(BaseModel):
    child: Top3CompareChild
    preference: Top3ComparePreference
    programs: list[Top3CompareProgram] = Field(min_length=1, max_length=3)


class Top3CompareItem(BaseModel):
    program_id: int = Field(alias="programId")
    one_line_reason: str = Field(alias="oneLineReason")
    highlight_tag: str = Field(alias="highlightTag")

    model_config = {
        "populate_by_name": True,
    }


class Top3CompareResponse(BaseModel):
    common_summary: str = Field(alias="commonSummary")
    items: list[Top3CompareItem]
    source: str

    model_config = {
        "populate_by_name": True,
    }
