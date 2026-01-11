from __future__ import annotations

from typing import Dict, List, Optional, Set
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.extensions import db
from app.models.enums import SlotType
from app.models.catalog import Course
from app.models.ontology import CourseOption, CourseBundle, RequirementSlot
from .course_matches_bucket_rule import course_matches_bucket_rule


def build_eligible_slots_by_course(
    *,
    taken_course_ids: List[str],
    slots_by_id: Dict[str, RequirementSlot],
    session: Optional[Session] = None,
    include_bucket_slots: bool = False,
    courses_by_id: Optional[Dict[str, Course]] = None,
) -> Dict[str, Set[str]]:
    """
    Returns:
        { course_id -> set(requirement_slot_id) }

    What counts as "eligible"?
      1) Explicit CourseOption mappings:
         - CourseOption.requirement_slot_id (direct)
         - CourseOption.bundle_id -> CourseBundle.requirement_slot_id (resolved)
      2) (Optional) BUCKET eligibility:
         - If include_bucket_slots=True, we ALSO consider BUCKET slots and mark a course eligible
           if it matches the slot_rule (department/number/exclusions). This is useful for the UI
           so users can optionally "send" a leftover course into a bucket.

    Important:
      - We filter to slots that exist in slots_by_id (i.e., in the student's curriculum).
      - You pass slots_by_id from your curriculum query (all slots in the student's major).
    """
    session = session or db.session

    taken_course_ids = [c for c in taken_course_ids if c]
    if not taken_course_ids:
        return {}

    # ----------------------------
    # 1) Build edges from CourseOption
    # ----------------------------
    cos = session.execute(
        select(CourseOption).where(CourseOption.course_id.in_(taken_course_ids))
    ).scalars().all()

    bundle_ids = sorted({co.bundle_id for co in cos if co.bundle_id})
    bundles_by_id: Dict[str, CourseBundle] = {}
    if bundle_ids:
        bundles_by_id = {
            b.id: b
            for b in session.execute(
                select(CourseBundle).where(CourseBundle.id.in_(bundle_ids))
            ).scalars().all()
        }

    eligible: Dict[str, Set[str]] = {cid: set() for cid in taken_course_ids}

    for co in cos:
        cid = co.course_id
        if cid not in eligible:
            eligible[cid] = set()

        # Direct mapping
        if co.requirement_slot_id and co.requirement_slot_id in slots_by_id:
            eligible[cid].add(co.requirement_slot_id)

        # Bundle mapping -> resolve to slot
        if co.bundle_id:
            b = bundles_by_id.get(co.bundle_id)
            if b and b.requirement_slot_id and b.requirement_slot_id in slots_by_id:
                eligible[cid].add(b.requirement_slot_id)

    # ----------------------------
    # 2) Optional: BUCKET eligibility by rule (for UI)
    # ----------------------------
    if include_bucket_slots:
        # Ensure we have course objects for rule checks
        if courses_by_id is None:
            courses = session.execute(
                select(Course).where(Course.id.in_(taken_course_ids))
            ).scalars().all()
            courses_by_id = {c.id: c for c in courses}

        bucket_slots = [
            s for s in slots_by_id.values()
            if s.slot_type == SlotType.BUCKET
        ]

        for cid in taken_course_ids:
            course = (courses_by_id or {}).get(cid)
            if not course:
                continue

            for slot in bucket_slots:
                rule = slot.slot_rule or {}
                if course_matches_bucket_rule(course, rule):
                    eligible[cid].add(slot.id)

    # Remove empties if you prefer (optional)
    eligible = {cid: sids for cid, sids in eligible.items() if sids}

    return eligible
