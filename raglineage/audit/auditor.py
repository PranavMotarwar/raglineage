"""Auditor for generating audit reports."""

from typing import Optional

from raglineage.audit.checks import (
    check_staleness,
    check_transform_risks,
    check_version_consistency,
)
from raglineage.schemas.audit import AnswerWithLineage, AuditReport
from raglineage.utils.logging import get_logger

logger = get_logger(__name__)


class Auditor:
    """Auditor for answer validation and reporting."""

    def __init__(self, current_version: str | None = None) -> None:
        """
        Initialize auditor.

        Args:
            current_version: Current dataset version for staleness checks
        """
        self.current_version = current_version

    def audit(self, answer: AnswerWithLineage) -> AuditReport:
        """
        Generate audit report for an answer.

        Args:
            answer: Answer with lineage

        Returns:
            Audit report
        """
        version_consistency = check_version_consistency(answer)
        staleness_check = check_staleness(answer, self.current_version)
        transform_risk_flags = check_transform_risks(answer)

        return AuditReport(
            answer_id=None,
            staleness_check=staleness_check,
            version_consistency=version_consistency,
            transform_risk_flags=transform_risk_flags,
            metadata={},
        )
