from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.backoffice.apps.company.models import Company
from src.backoffice.models import Base, IdMixin


class Site(IdMixin, Base):
    __tablename__ = "site"

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    company: Mapped["Company"] = relationship(back_populates="sites")
