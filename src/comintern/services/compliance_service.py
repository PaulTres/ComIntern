from comintern.database.session_factory import SessionFactory
from comintern.exceptions import AppError, AppErrorCode
from comintern.mappers import (
    get_status,
    score_regulation,
    to_document_response,
    to_regulation_summary,
    to_requirement_response,
    to_score_response,
)
from comintern.models.compliance import (
    CatalogEntryResponseModel,
    ComplianceStatus,
    DashboardResponseModel,
    OpenTaskResponseModel,
    RegulationDetailResponseModel,
    RequirementResponseModel,
    StatusUpdateRequestModel,
    UpdateResponseModel,
)
from comintern.repositories.document_repository import DocumentRepository
from comintern.repositories.regulation_repository import RegulationRepository
from comintern.repositories.update_repository import UpdateRepository
from comintern.rules import scoring
from comintern.schemas import Company, RequirementStatus
from comintern.schemas.base import utcnow

DASHBOARD_OPEN_TASKS = 8
DASHBOARD_RECENT_DOCUMENTS = 5
DASHBOARD_UPDATES = 5


class ComplianceService:
    """A company's requirement checklists, scores, dashboard and updates feed."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def get_regulation_detail(
        self, company_id: int, code: str
    ) -> RegulationDetailResponseModel:
        """
        :raises AppError: REGULATION_NOT_FOUND when the regulation does not apply to the company.
        """
        async with self._session_factory.get_session() as session:
            regulations = RegulationRepository(session)
            documents = DocumentRepository(session)
            company_regulation = next(
                (
                    row
                    for row in await regulations.list_applicable(company_id)
                    if row.regulation.code == code
                ),
                None,
            )
            if company_regulation is None:
                raise AppError(AppErrorCode.REGULATION_NOT_FOUND)
            regulation = company_regulation.regulation
            statuses = await regulations.get_statuses(company_id)
            evidence_counts = await documents.count_evidence(company_id)
            regulation_documents = [
                to_document_response(document)
                for document in await documents.list_for_company(company_id, code)
            ]
            summary = to_regulation_summary(
                company_regulation,
                score_regulation(regulation, statuses, evidence_counts),
            )
            return RegulationDetailResponseModel(
                **summary.model_dump(),
                authority=regulation.authority,
                source_url=regulation.source_url,
                requirements=[
                    to_requirement_response(
                        requirement, statuses.get(requirement.id), regulation_documents
                    )
                    for requirement in regulation.requirements
                ],
                updates=await self._list_updates(
                    session, company_id, regulation_code=code
                ),
            )

    async def set_status(
        self, company_id: int, requirement_id: int, request: StatusUpdateRequestModel
    ) -> RequirementResponseModel:
        """
        :raises AppError: REQUIREMENT_NOT_FOUND when the requirement's regulation does not apply.
        """
        async with self._session_factory.get_session() as session:
            regulations = RegulationRepository(session)
            requirement = await regulations.get_applicable_requirement(
                company_id, requirement_id
            )
            if requirement is None:
                raise AppError(AppErrorCode.REQUIREMENT_NOT_FOUND)
            status = await regulations.get_status(company_id, requirement.id)
            if status is None:
                status = RequirementStatus(
                    company_id=company_id, requirement_id=requirement.id
                )
                await regulations.add_status(status)
            status.status = request.status
            status.note = request.note
            status.updated_at = utcnow()
            regulation_documents = [
                to_document_response(document)
                for document in await DocumentRepository(session).list_for_company(
                    company_id, requirement.regulation.code
                )
            ]
            return to_requirement_response(requirement, status, regulation_documents)

    async def get_dashboard(self, company: Company) -> DashboardResponseModel:
        async with self._session_factory.get_session() as session:
            regulations = RegulationRepository(session)
            documents = DocumentRepository(session)
            statuses = await regulations.get_statuses(company.id)
            evidence_counts = await documents.count_evidence(company.id)
            summaries, scores, open_tasks, all_items = [], [], [], []
            for company_regulation in await regulations.list_applicable(company.id):
                regulation = company_regulation.regulation
                score = score_regulation(regulation, statuses, evidence_counts)
                scores.append(score)
                summaries.append(to_regulation_summary(company_regulation, score))
                for requirement in regulation.requirements:
                    status = get_status(statuses, requirement.id)
                    all_items.append(
                        scoring.Item(
                            requirement.weight,
                            status,
                            evidence_counts.get(requirement.id, 0) > 0,
                        )
                    )
                    if status in (
                        ComplianceStatus.NOT_STARTED,
                        ComplianceStatus.IN_PROGRESS,
                    ):
                        open_tasks.append(
                            OpenTaskResponseModel(
                                requirement_id=requirement.id,
                                title=requirement.title,
                                status=status,
                                weight=requirement.weight,
                                regulation_code=regulation.code,
                                regulation_short_name=regulation.short_name,
                            )
                        )
            # Highest weight first, then not started before in progress.
            open_tasks.sort(
                key=lambda task: (
                    -task.weight,
                    task.status != ComplianceStatus.NOT_STARTED,
                )
            )
            overall = scoring.overall(scores)
            return DashboardResponseModel(
                company_name=company.name,
                assessed=company.assessed_at is not None,
                overall_score=overall,
                level=scoring.level(overall),
                totals=to_score_response(scoring.score_items(all_items)),
                regulations=summaries,
                open_tasks=open_tasks[:DASHBOARD_OPEN_TASKS],
                recent_documents=[
                    to_document_response(document)
                    for document in await documents.list_for_company(
                        company.id, limit=DASHBOARD_RECENT_DOCUMENTS
                    )
                ],
                updates=(
                    await self._list_updates(session, company.id, relevant_only=True)
                )[:DASHBOARD_UPDATES],
            )

    async def list_updates(
        self, company_id: int, relevant_only: bool
    ) -> list[UpdateResponseModel]:
        async with self._session_factory.get_session() as session:
            return await self._list_updates(
                session, company_id, relevant_only=relevant_only
            )

    async def list_catalog(self) -> list[CatalogEntryResponseModel]:
        async with self._session_factory.get_session() as session:
            return [
                CatalogEntryResponseModel.model_validate(row)
                for row in await RegulationRepository(session).list_all()
            ]

    @staticmethod
    async def _list_updates(
        session,
        company_id: int,
        relevant_only: bool = False,
        regulation_code: str | None = None,
    ) -> list[UpdateResponseModel]:
        """
        :return: The updates, newest first, each marked relevant when its regulation applies to the company.
        """
        applicable_codes = {
            row.regulation.code
            for row in await RegulationRepository(session).list_applicable(company_id)
        }
        updates = []
        for update in await UpdateRepository(session).list(regulation_code):
            response = UpdateResponseModel.model_validate(update)
            response.relevant = update.regulation_code in applicable_codes
            if response.relevant or not relevant_only:
                updates.append(response)
        return updates
