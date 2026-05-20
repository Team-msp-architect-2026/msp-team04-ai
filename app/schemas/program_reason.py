from pydantic import BaseModel, Field


class ProgramReasonChild(BaseModel):
    child_id: int = Field(alias="childId")
    age: int | None = None
    concerns: list[str] = Field(default_factory=list)

    model_config = {
        "populate_by_name": True,
    }


class ProgramReasonPreference(BaseModel):
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


class ProgramReasonProgram(BaseModel):
    program_id: int = Field(alias="programId")
    title: str
    category: str | None = None
    description: str | None = ""
    institution_name: str | None = Field(default=None, alias="institutionName")
    region: str | None = None
    price: int | None = None
    is_free: bool | None = Field(default=None, alias="isFree")
    class_type: str | None = Field(default=None, alias="classType")
    target_age_min: int | None = Field(default=None, alias="targetAgeMin")
    target_age_max: int | None = Field(default=None, alias="targetAgeMax")
    rating_avg: float | None = Field(default=None, alias="ratingAvg")
    review_count: int | None = Field(default=None, alias="reviewCount")
    tags: list[str] = Field(default_factory=list)

    model_config = {
        "populate_by_name": True,
    }


class ProgramReasonScore(BaseModel):
    match_score: float = Field(alias="matchScore")
    reason_codes: list[str] = Field(default_factory=list, alias="reasonCodes")
    score_breakdown: dict[str, float | None] = Field(default_factory=dict, alias="scoreBreakdown")

    model_config = {
        "populate_by_name": True,
    }


class ProgramReasonRequest(BaseModel):
    child: ProgramReasonChild
    preference: ProgramReasonPreference
    program: ProgramReasonProgram
    score: ProgramReasonScore


class ProgramReasonResponse(BaseModel):
    match_score: float = Field(alias="matchScore")
    reason_list: list[str] = Field(alias="reasonList")
    source: str

    model_config = {
        "populate_by_name": True,
    }
