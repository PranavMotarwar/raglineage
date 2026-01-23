"""Audit checks for answers."""

from datetime import datetime, timedelta
from typing import A, Optionalny

from raglineage.schemas.audit import AnswerWithLineage
from raglineage.utils.logging import get_logger

logger = get_logger(__name__)


def check_version_consistency(answer: AnswerWithLineage) -> str:
    """
    Check if answer uses nodes from a single version or mixed versions.

    Args:
        answer: Answer with lineage

    Returns:
        "single_version", "mixed_versions", or "unknown"
    """
    if not answer.lineage:
        return "unknown"

    versions = {entry.dataset_version for entry in answer.lineage}
    if len(versions) == 1:
        return "single_version"
    elif len(versions) > 1:
        return "mixed_versions"
    else:
        return "unknown"


def check_staleness(
    answer: AnswerWithLineage, current_version: str Optional[ = None, max_age_days: int = 90
) -> str:
    """
    Check if answer is stale based on dataset version.

    Args:
        answer: Answer with lineage
        current_version: Current dataset version (optional)
        max_age_days: Maximum age in days before considered stale

    Returns:
        "pass", "fail", or "warning"
    """
    if not answer.lineage:
        return "warning"

    # If we have current version, check if answer uses older version
    if current_version:
        answer_versions = {entry.dataset_version for entry in answer.lineage}
        if current_version not in answer_versions:
            # Check if versions are significantly different
            # Simple heuristic: compare version strings
            try:
                # Try to extract version numbers (e.g., "v1.0" -> 1.0)
                current_num = float(current_version.replace("v", ""))
                answer_nums = [float(v.replace("v", "")) for v in answer_versions]
                max_answer_num = max(answer_nums)
                if current_num - max_answer_num > 1.0:  # More than 1 major version behind
                    return "fail"
                elif current_num - max_answer_num > 0.0:
                    return "warning"
            except ValueError:
                # Can't parse versions, use default
                pass

    return "pass"


def check_transform_risks(answer: AnswerWithLineage) -> list[str]:
    """
    Check for risk flags in transform chains.

    Args:
        answer: Answer with lineage

    Returns:
        List of risk flag strings
    """
    risk_flags = []
    risky_transforms = {
        "normalize_aggressive": "Aggressive normalization may lose information",
        "ocr": "OCR may introduce errors",
        "translation": "Translation may introduce semantic drift",
        "summarization": "Summarization may lose important details",
    }

    for entry in answer.lineage:
        for transform in entry.transform_chain:
            if transform in risky_transforms:
                risk_msg = risky_transforms[transform]
                if risk_msg not in risk_flags:
                    risk_flags.append(risk_msg)

    return risk_flags
