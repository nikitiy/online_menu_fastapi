from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import (CHAR, CheckConstraint, DateTime, ForeignKey,
                        Integer, UniqueConstraint)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.backoffice.apps.company.models import CompanyBranch
from src.backoffice.models import Base, IdMixin


class QRCode(IdMixin, Base):
    __tablename__ = "qr_codes"

    company_branch_id: Mapped[int] = mapped_column(
        ForeignKey("CompanyBranch.id", ondelete="CASCADE"), index=True, nullable=False
    )
    qr_options: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        default=dict,
        nullable=True,
    )
    url_hash: Mapped[str] = mapped_column(
        CHAR(64), nullable=False, unique=True, index=True
    )
    scan_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    last_scanned: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    company_branch: Mapped["CompanyBranch"] = relationship(
        back_populates="qr_codes",
    )

    __table_args__ = (
        UniqueConstraint("url_hash", "uq_qr_codes_url_hash"),
        CheckConstraint("scan_count >= 0", name="ck_qr_codes_scan_count_nonneg"),
    )
