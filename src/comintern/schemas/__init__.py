"""The ORM tables, one file per table. Importing this package registers all of them."""

from comintern.schemas.base import Base
from comintern.schemas.companies import Company
from comintern.schemas.company_regulations import CompanyRegulation
from comintern.schemas.conversations import Conversation
from comintern.schemas.documents import Document
from comintern.schemas.messages import Message
from comintern.schemas.regulations import Regulation
from comintern.schemas.regulatory_updates import RegulatoryUpdate
from comintern.schemas.requirement_statuses import RequirementStatus
from comintern.schemas.requirements import Requirement
from comintern.schemas.users import User

__all__ = [
    "Base",
    "Company",
    "CompanyRegulation",
    "Conversation",
    "Document",
    "Message",
    "Regulation",
    "RegulatoryUpdate",
    "Requirement",
    "RequirementStatus",
    "User",
]
