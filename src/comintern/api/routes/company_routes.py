from typing import Any

from fastapi import APIRouter

from comintern import catalog
from comintern.api.dependencies import CompanyServiceDependency, CurrentUserDependency
from comintern.models.auth import CompanyResponseModel, CompanyUpdateRequestModel
from comintern.models.compliance import RegulationSummaryResponseModel

router = APIRouter(tags=["company"])


@router.get("/questionnaire")
async def get_questionnaire() -> dict[str, Any]:
    """The onboarding questionnaire: steps, questions and their show_if conditions."""
    return catalog.questionnaire()


@router.get("/company", response_model=CompanyResponseModel)
async def get_company(user: CurrentUserDependency) -> CompanyResponseModel:
    return CompanyResponseModel.model_validate(user.company)


@router.put("/company", response_model=CompanyResponseModel)
async def update_company(
    body: CompanyUpdateRequestModel,
    user: CurrentUserDependency,
    company_service: CompanyServiceDependency,
) -> CompanyResponseModel:
    """Rename the company and/or save new answers; new answers re-run the applicability engine."""
    return await company_service.update_company(user.company_id, body)


@router.get("/company/regulations", response_model=list[RegulationSummaryResponseModel])
async def list_applicable_regulations(
    user: CurrentUserDependency, company_service: CompanyServiceDependency
) -> list[RegulationSummaryResponseModel]:
    """The regulations that apply to the company, why, and its score on each."""
    return await company_service.list_applicable_regulations(user.company_id)
