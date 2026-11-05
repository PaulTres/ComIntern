from datetime import UTC, datetime
from typing import Any

from comintern import catalog
from comintern.database.session_factory import SessionFactory
from comintern.exceptions import AppError, AppErrorCode
from comintern.mappers import score_regulation, to_regulation_summary
from comintern.models.auth import CompanyResponseModel, CompanyUpdateRequestModel
from comintern.models.compliance import RegulationSummaryResponseModel
from comintern.repositories.document_repository import DocumentRepository
from comintern.repositories.regulation_repository import RegulationRepository
from comintern.rules import applicability
from comintern.schemas import Company, CompanyRegulation


def validate_profile(answers: dict[str, Any]) -> dict[str, Any]:
    """
    Keep only the answers to known, visible questions, and check required fields and types.

    :param answers: The questionnaire answers as sent, keyed by question id.
    :return: The clean answers.
    :raises AppError: INVALID_PROFILE with an error per question id.
    """
    clean: dict[str, Any] = {}
    errors: dict[str, str] = {}
    for step in catalog.questionnaire()["steps"]:
        for question in step["questions"]:
            question_id = question["id"]
            if not applicability.visible(question, answers):
                continue
            value = answers.get(question_id)
            if value is None or value == [] or value == "":
                if question.get("required"):
                    errors[question_id] = "This question is required"
                continue
            options = {option["value"] for option in question.get("options", [])}
            match question["type"]:
                case "boolean" if isinstance(value, bool):
                    pass
                case "number" if (
                    isinstance(value, int | float)
                    and not isinstance(value, bool)
                    and value >= question.get("min", 0)
                ):
                    pass
                case "single_select" if value in options:
                    pass
                case "multi_select" if (
                    isinstance(value, list) and value and set(value) <= options
                ):
                    pass
                case _:
                    errors[question_id] = "Invalid answer"
                    continue
            clean[question_id] = value
    if errors:
        raise AppError(AppErrorCode.INVALID_PROFILE, details={"errors": errors})
    return clean


class CompanyService:
    """The questionnaire, the company profile and which regulations apply to it."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def update_company(
        self, company_id: int, request: CompanyUpdateRequestModel
    ) -> CompanyResponseModel:
        """
        Rename the company and/or save new answers; new answers re-run the applicability engine.

        :raises AppError: INVALID_PROFILE when the answers do not pass validation.
        """
        async with self._session_factory.get_session() as session:
            regulations = RegulationRepository(session)
            company = await regulations.get_company_with_regulations(company_id)
            if request.name is not None:
                company.name = request.name
            if request.profile is not None:
                company.profile = validate_profile(request.profile)
                await self._reassess(regulations, company)
            return CompanyResponseModel.model_validate(company)

    async def list_applicable_regulations(
        self, company_id: int
    ) -> list[RegulationSummaryResponseModel]:
        async with self._session_factory.get_session() as session:
            regulations = RegulationRepository(session)
            statuses = await regulations.get_statuses(company_id)
            evidence_counts = await DocumentRepository(session).count_evidence(
                company_id
            )
            return [
                to_regulation_summary(
                    company_regulation,
                    score_regulation(
                        company_regulation.regulation, statuses, evidence_counts
                    ),
                )
                for company_regulation in await regulations.list_applicable(company_id)
            ]

    @staticmethod
    async def _reassess(regulations: RegulationRepository, company: Company) -> None:
        """Keep the company's applicable regulations in line with its current answers."""
        current = {
            company_regulation.regulation_id: company_regulation
            for company_regulation in company.regulations
        }
        kept: set[int] = set()
        for regulation in await regulations.list_all():
            reasons = applicability.assess(
                regulation.applicability, company.profile or {}
            )
            if not reasons:
                continue
            kept.add(regulation.id)
            if regulation.id in current:
                current[regulation.id].reasons = reasons
            else:
                company.regulations.append(
                    CompanyRegulation(regulation_id=regulation.id, reasons=reasons)
                )
        for regulation_id, company_regulation in current.items():
            if regulation_id not in kept:
                company.regulations.remove(company_regulation)
        company.assessed_at = datetime.now(UTC)
