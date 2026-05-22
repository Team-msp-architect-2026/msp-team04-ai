from pydantic import BaseModel, Field


class ParentingReportChildInfo(BaseModel):
    child_name: str | None = Field(default=None, alias="childName")
    age: int | None = None
    concerns: list[str] = Field(default_factory=list)
    region: str | None = None
    monthly_budget: str | None = Field(default=None, alias="monthlyBudget")

    model_config = {
        "populate_by_name": True,
    }


class ParentingReportSavingsBreakdown(BaseModel):
    childcare_support_amount: int = Field(default=0, alias="childcareSupportAmount")
    education_voucher_amount: int = Field(default=0, alias="educationVoucherAmount")
    free_program_amount: int = Field(default=0, alias="freeProgramAmount")
    total_monthly_saving: int = Field(default=0, alias="totalMonthlySaving")

    model_config = {
        "populate_by_name": True,
    }


class ParentingReportRequest(BaseModel):
    child_info: ParentingReportChildInfo = Field(alias="childInfo")
    support_count: int = Field(default=0, alias="supportCount")
    free_program_count: int = Field(default=0, alias="freeProgramCount")
    recommend_count: int = Field(default=0, alias="recommendCount")
    savings_breakdown: ParentingReportSavingsBreakdown = Field(alias="savingsBreakdown")
    calculation_basis: str | None = Field(default=None, alias="calculationBasis")

    model_config = {
        "populate_by_name": True,
    }


class ParentingReportResponse(BaseModel):
    summary_message: str = Field(alias="summaryMessage")
    saving_message: str = Field(alias="savingMessage")
    benefit_message: str = Field(alias="benefitMessage")
    recommendation_message: str = Field(alias="recommendationMessage")
    source: str

    model_config = {
        "populate_by_name": True,
    }
