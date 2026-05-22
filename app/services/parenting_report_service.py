import json
import re
from typing import Any

from app.schemas.parenting_report import (
    ParentingReportRequest,
    ParentingReportResponse,
)
from app.services.openai_client import generate_parenting_report_json


MAX_SUMMARY_LENGTH = 140
MAX_MESSAGE_LENGTH = 120


def generate_parenting_report(
    request: ParentingReportRequest,
) -> ParentingReportResponse:
    prompt = build_prompt(request)
    result_json = generate_parenting_report_json(prompt)

    summary_message = normalize_text(
        result_json.get("summaryMessage") or result_json.get("summary_message"),
        MAX_SUMMARY_LENGTH,
    )
    saving_message = normalize_text(
        result_json.get("savingMessage") or result_json.get("saving_message"),
        MAX_MESSAGE_LENGTH,
    )
    benefit_message = normalize_text(
        result_json.get("benefitMessage") or result_json.get("benefit_message"),
        MAX_MESSAGE_LENGTH,
    )
    recommendation_message = normalize_text(
        result_json.get("recommendationMessage") or result_json.get("recommendation_message"),
        MAX_MESSAGE_LENGTH,
    )

    if not summary_message:
        summary_message = build_default_summary(request)

    if not saving_message:
        saving_message = build_default_saving_message(request)

    if not benefit_message:
        benefit_message = build_default_benefit_message(request)

    if not recommendation_message:
        recommendation_message = build_default_recommendation_message(request)

    return ParentingReportResponse(
        summary_message=summary_message,
        saving_message=saving_message,
        benefit_message=benefit_message,
        recommendation_message=recommendation_message,
        source="OPENAI",
    )


def build_prompt(request: ParentingReportRequest) -> str:
    payload = {
        "childInfo": {
            "childName": request.child_info.child_name,
            "age": request.child_info.age,
            "concerns": request.child_info.concerns,
            "region": request.child_info.region,
            "monthlyBudget": request.child_info.monthly_budget,
        },
        "supportCount": request.support_count,
        "freeProgramCount": request.free_program_count,
        "recommendCount": request.recommend_count,
        "savingsBreakdown": {
            "childcareSupportAmount": request.savings_breakdown.childcare_support_amount,
            "educationVoucherAmount": request.savings_breakdown.education_voucher_amount,
            "freeProgramAmount": request.savings_breakdown.free_program_amount,
            "totalMonthlySaving": request.savings_breakdown.total_monthly_saving,
        },
        "calculationBasis": request.calculation_basis,
    }

    return f"""
너는 MoMent 홈 화면과 AI 육아 종합 분석 리포트 상세 화면에 표시할 문장 생성기다.

목표:
- 백엔드가 이미 계산한 자녀 프로필, 지원금 수, 무료 프로그램 수, 추천 프로그램 수, 예상 절감액을 부모가 이해하기 쉬운 한국어 문장으로 바꾼다.
- 지원금, 무료 프로그램, 추천 수, 절감액을 새로 계산하지 않는다.
- 입력 데이터에 없는 혜택명, 기관명, 프로그램명, 의료/발달 효과를 지어내지 않는다.
- 숫자는 반드시 입력 데이터의 값을 그대로 사용한다.
- summaryMessage는 전체 리포트 대표 문장이다.
- savingMessage는 월 예상 절감액을 설명한다.
- benefitMessage는 지원금과 무료 공공서비스 활용 기준을 설명한다.
- recommendationMessage는 추천 프로그램 수 또는 다음 행동을 안내한다.
- 부모 친화적이고 따뜻한 문체로 작성한다.
- summaryMessage는 140자 이내, 나머지 메시지는 각각 120자 이내로 작성한다.
- 반드시 JSON만 반환한다.

출력 JSON 형식:
{{
  "summaryMessage": "하은에게 맞는 육아 지원 혜택을 찾았어요.",
  "savingMessage": "현재 조건으로 월 평균 12만원 절감 가능한 경로가 있어요.",
  "benefitMessage": "지원금과 무료 공공서비스를 함께 활용한 기준이에요.",
  "recommendationMessage": "추천 프로그램도 함께 확인해보면 좋아요."
}}

입력 데이터:
{json.dumps(payload, ensure_ascii=False)}
""".strip()


def normalize_text(value: Any, max_length: int) -> str:
    if not isinstance(value, str):
        return ""

    normalized = value.replace("\u00a0", " ").replace("\u200b", "")
    normalized = " ".join(normalized.split())

    replacements = {
        "입니 다": "입니다",
        "합니 다": "합니다",
        "좋 아요": "좋아요",
        "있 어요": "있어요",
        "없 어요": "없어요",
        "되 어요": "돼요",
        "육 아": "육아",
        "지 원": "지원",
        "혜 택": "혜택",
        "공 공": "공공",
        "서비스": "서비스",
        "프 로그램": "프로그램",
        "프로 그램": "프로그램",
        "추 천": "추천",
        "절 감": "절감",
        "절감가능한": "절감 가능한",
        "절감 가능 한": "절감 가능한",
        "예 상": "예상",
        "월 평균": "월 평균",
        "활 용": "활용",
        "기 준": "기준",
        "보 호자": "보호자",
        "자 녀": "자녀",
        "관 심": "관심",
        "조 건": "조건",
    }

    for source, target in replacements.items():
        normalized = normalized.replace(source, target)

    normalized = re.sub(
        r"(?<=[가-힣])\s+(?=(이|가|은|는|을|를|와|과|도|만|의|에|로|으로|에서|에게|부터|까지|처럼|보다))",
        "",
        normalized,
    )

    normalized = " ".join(normalized.split())
    normalized = normalized.replace("절감가능한", "절감 가능한")
    normalized = normalized.replace("절감 가능 한", "절감 가능한")

    if len(normalized) > max_length:
        normalized = normalized[:max_length].rstrip()

    return normalized


def build_default_summary(request: ParentingReportRequest) -> str:
    child_name = request.child_info.child_name or "아이"

    if request.support_count > 0:
        return f"{child_name}에게 맞는 육아 지원 혜택을 찾았어요."

    return f"{child_name}의 조건을 기준으로 이용 가능한 육아 지원 정보를 정리했어요."


def build_default_saving_message(request: ParentingReportRequest) -> str:
    total = request.savings_breakdown.total_monthly_saving

    if total > 0:
        return f"현재 조건으로 월 평균 {format_won(total)} 절감 가능한 경로가 있어요."

    return "현재 조건에서 확인 가능한 절감 경로를 계속 찾아볼게요."


def build_default_benefit_message(request: ParentingReportRequest) -> str:
    if request.support_count > 0 or request.free_program_count > 0:
        return "지원금과 무료 공공서비스를 함께 활용한 기준이에요."

    return "자녀 조건과 지역 정보를 기준으로 지원 혜택을 분석했어요."


def build_default_recommendation_message(request: ParentingReportRequest) -> str:
    if request.recommend_count > 0:
        return f"맞춤 추천 프로그램 {request.recommend_count}개도 함께 확인해보면 좋아요."

    return "자녀 조건을 등록하면 맞춤 추천 프로그램을 더 정확히 확인할 수 있어요."


def format_won(amount: int) -> str:
    if amount >= 10_000 and amount % 10_000 == 0:
        return f"{amount // 10_000}만원"

    return f"{amount:,}원"
