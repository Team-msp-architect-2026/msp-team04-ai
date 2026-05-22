from pydantic import BaseModel, Field


class ReviewKeywordProgram(BaseModel):
    program_id: int = Field(alias="programId")
    title: str
    category: str | None = None
    rating_avg: float | None = Field(default=None, alias="ratingAvg")
    review_count: int = Field(default=0, alias="reviewCount")

    model_config = {
        "populate_by_name": True,
    }


class ReviewKeywordStats(BaseModel):
    review_count: int = Field(default=0, alias="reviewCount")
    rating_average: float | None = Field(default=None, alias="ratingAverage")
    rating_distribution: dict[str, int] = Field(default_factory=dict, alias="ratingDistribution")
    positive_keywords: list[str] = Field(default_factory=list, alias="positiveKeywords")
    negative_keywords: list[str] = Field(default_factory=list, alias="negativeKeywords")
    review_texts: list[str] = Field(default_factory=list, alias="reviewTexts")

    model_config = {
        "populate_by_name": True,
    }


class ReviewKeywordsRequest(BaseModel):
    program: ReviewKeywordProgram
    stats: ReviewKeywordStats


class ReviewKeywordsResponse(BaseModel):
    positive_keywords: list[str] = Field(default_factory=list, alias="positiveKeywords")
    negative_keywords: list[str] = Field(default_factory=list, alias="negativeKeywords")
    summary: str
    source: str

    model_config = {
        "populate_by_name": True,
    }
