from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from comintern.schemas import (
    Company,
    CompanyRegulation,
    Regulation,
    Requirement,
    RequirementStatus,
)


class RegulationRepository:
    """Regulations, requirements and a company's applicable regulations and statuses."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[Regulation]:
        return list(
            await self._session.scalars(
                select(Regulation).order_by(
                    Regulation.jurisdiction, Regulation.short_name
                )
            )
        )

    async def get_by_code(self, code: str) -> Regulation | None:
        return await self._session.scalar(
            select(Regulation).where(Regulation.code == code)
        )

    async def add(self, regulation: Regulation) -> None:
        self._session.add(regulation)

    async def get_company_with_regulations(self, company_id: int) -> Company | None:
        return await self._session.get(
            Company, company_id, options=[selectinload(Company.regulations)]
        )

    async def list_applicable(self, company_id: int) -> list[CompanyRegulation]:
        """
        :param company_id: The company.
        :return: The regulations that apply to it, with their requirements, EU first then DE and RO.
        """
        statement = (
            select(CompanyRegulation)
            .join(Regulation)
            .where(CompanyRegulation.company_id == company_id)
            .order_by(Regulation.jurisdiction, Regulation.short_name)
        )
        return list(await self._session.scalars(statement))

    async def get_applicable_requirement(
        self, company_id: int, requirement_id: int
    ) -> Requirement | None:
        """
        :param company_id: The company.
        :param requirement_id: The requirement.
        :return: The requirement, or None when it does not exist or its regulation does not apply.
        """
        statement = (
            select(Requirement)
            .join(
                CompanyRegulation,
                CompanyRegulation.regulation_id == Requirement.regulation_id,
            )
            .where(
                Requirement.id == requirement_id,
                CompanyRegulation.company_id == company_id,
            )
        )
        return await self._session.scalar(statement)

    async def get_statuses(self, company_id: int) -> dict[int, RequirementStatus]:
        rows = await self._session.scalars(
            select(RequirementStatus).where(RequirementStatus.company_id == company_id)
        )
        return {row.requirement_id: row for row in rows}

    async def get_status(
        self, company_id: int, requirement_id: int
    ) -> RequirementStatus | None:
        return await self._session.scalar(
            select(RequirementStatus).where(
                RequirementStatus.company_id == company_id,
                RequirementStatus.requirement_id == requirement_id,
            )
        )

    async def add_status(self, status: RequirementStatus) -> None:
        self._session.add(status)
        await self._session.flush()
