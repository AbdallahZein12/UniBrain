from __future__ import annotations

from typing import Optional, Iterable, Set
from app.models.catalog import Course


def parse_course_number(course_id: str) -> Optional[int]:
    """
    "CS 230" -> 230
    Returns None if it can't parse the numeric part.
    """
    try:
        parts = (course_id or "").strip().split()
        if not parts:
            return None
        return int(parts[-1])
    except Exception:
        return None


def course_matches_bucket_rule(course: Course, slot_rule: dict) -> bool:
    """
    Returns True if `course` satisfies the BUCKET slot_rule.

    Your slot_rule schema (from your seeds) supports:
      - department_ids_any: [dept_id, ...]
      - course_number_min_exc: int | null      (exclusive minimum)
      - course_number_max_inc: int | null      (inclusive maximum)
      - exclude_course_ids: [course_id, ...]
    :contentReference[oaicite:0]{index=0}
    """
    if not slot_rule:
        return True

    # 1) explicit exclusions
    exclude_ids: Set[str] = set(slot_rule.get("exclude_course_ids") or [])
    if course.id in exclude_ids:
        return False

    # 2) department filter (if specified)
    dept_any: Iterable[str] = slot_rule.get("department_ids_any") or []
    if dept_any and course.department_id not in set(dept_any):
        return False

    # 3) course number bounds (if specified)
    n = parse_course_number(course.id)
    min_exc = slot_rule.get("course_number_min_exc")
    max_inc = slot_rule.get("course_number_max_inc")

    # If bounds exist but we can't parse the number, be conservative
    if n is None:
        if min_exc is not None or max_inc is not None:
            return False
        return True

    if min_exc is not None and not (n > int(min_exc)):
        return False
    if max_inc is not None and not (n <= int(max_inc)):
        return False

    return True
