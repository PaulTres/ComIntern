from fastapi import APIRouter

from comintern.api.dependencies import (
    ComplianceServiceDependency,
    CurrentUserDependency,
)
from comintern.models.compliance import (
    CatalogEntryResponseModel,
    DashboardResponseModel,
    RegulationDetailResponseModel,
    RequirementResponseModel,
    StatusUpdateRequestModel,
    UpdateResponseModel,
)

router = APIRouter(tags=["compliance"])


@router.get("/regulations/{code}", response_model=RegulationDetailResponseModel)
async def get_regulation(
    code: str,
    user: CurrentUserDependency,
    compliance_service: ComplianceServiceDependency,
) -> RegulationDetailResponseModel:
    """One applicable regulation with its requirement checklist, evidence and updates."""
    return await compliance_service.get_regulation_detail(user.company_id, code)


@router.put(
    "/requirements/{requirement_id}/status", response_model=RequirementResponseModel
)
async def set_requirement_status(
    requirement_id: int,
    body: StatusUpdateRequestModel,
    user: CurrentUserDependency,
    compliance_service: ComplianceServiceDependency,
) -> RequirementResponseModel:
    return await compliance_service.set_status(user.company_id, requirement_id, body)


@router.get("/dashboard", response_model=DashboardResponseModel)
async def get_dashboard(
    user: CurrentUserDependency, compliance_service: ComplianceServiceDependency
) -> DashboardResponseModel:
    """Overall and per-regulation scores, open tasks, recent evidence and relevant updates."""
    return await compliance_service.get_dashboard(user.company)


@router.get("/updates", response_model=list[UpdateResponseModel])
async def list_updates(
    user: CurrentUserDependency,
    compliance_service: ComplianceServiceDependency,
    relevant_only: bool = False,
) -> list[UpdateResponseModel]:
    return await compliance_service.list_updates(user.company_id, relevant_only)


@router.get("/catalog", response_model=list[CatalogEntryResponseModel])
async def list_catalog(
    compliance_service: ComplianceServiceDependency,
) -> list[CatalogEntryResponseModel]:
    """Every regulation in the catalog; public, e.g. for a landing page."""
    return await compliance_service.list_catalog()
