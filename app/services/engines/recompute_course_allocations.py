from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.extensions import db
from app.models.enums import SlotType

from app.models.catalog import Course
from app.models.ontology import (
    CourseAllocation,
    RequirementGroup,
    RequirementSlot,
    CourseOption,
    CourseBundle,
)
from app.models import StudentProfile


# ----------------------------
# Helpers
# ----------------------------

@dataclass(frozen=True)
class CourseInstance:
    course_id: str
    term: str
    status: str  # "completed" | "in_progress"


def _norm_course_id(cid: str) -> str:
    return (cid or "").strip().upper()


def extract_course_instances(courses_by_term: dict) -> List[CourseInstance]:
    """
    Flattens StudentProfile.courses_by_term into one record per (course, term, status).
    Also de-dupes exact duplicates.
    """
    out: List[CourseInstance] = []
    for status_key in ("completed", "in_progress"):
        for row in (courses_by_term or {}).get(status_key, []) or []:
            term = (row.get("term") or "").strip()
            for cid in row.get("courses") or []:
                course_id = _norm_course_id(cid)
                if term and course_id:
                    out.append(CourseInstance(course_id=course_id, term=term, status=status_key))

    seen = set()
    deduped: List[CourseInstance] = []
    for x in out:
        k = (x.course_id, x.term, x.status)
        if k not in seen:
            seen.add(k)
            deduped.append(x)
    return deduped


def preferred_term_by_course(instances: List[CourseInstance]) -> Dict[str, str]:
    """
    Pick a single term for allocation per course.
    Prefers completed over in_progress if both exist.
    """
    best: Dict[str, Tuple[int, str]] = {}
    for x in instances:
        score = 0 if x.status == "completed" else 1
        if x.course_id not in best or score < best[x.course_id][0]:
            best[x.course_id] = (score, x.term)
    return {cid: term for cid, (_score, term) in best.items()}


def parse_course_number(course_id: str) -> Optional[int]:
    """
    "CS 230" -> 230
    Returns None if can't parse.
    """
    try:
        parts = course_id.strip().split()
        if not parts:
            return None
        return int(parts[-1])
    except Exception:
        return None


def course_matches_bucket_rule(course: Course, slot_rule: dict) -> bool:
    """
    slot_rule shape (from your seeds) includes:
      - department_ids_any: [...]
      - course_number_min_exc
      - course_number_max_inc
      - exclude_course_ids
    """
    if not slot_rule:
        return True

    exclude_ids = set(slot_rule.get("exclude_course_ids") or [])
    if course.id in exclude_ids:
        return False

    dept_any = slot_rule.get("department_ids_any") or []
    if dept_any and course.department_id not in set(dept_any):
        return False

    n = parse_course_number(course.id)
    min_exc = slot_rule.get("course_number_min_exc")
    max_inc = slot_rule.get("course_number_max_inc")

    if n is None:
        # If rule cares about number bounds, and we can't parse, be conservative.
        if min_exc is not None or max_inc is not None:
            return False
        return True

    if min_exc is not None and not (n > int(min_exc)):
        return False
    if max_inc is not None and not (n <= int(max_inc)):
        return False

    return True


# ----------------------------
# Allocation core (PATCHED)
# ----------------------------

def recompute_course_allocations(student_profile_id: str, session: Optional[Session] = None) -> None:
    """
    Rebuild allocations for a student:
      - keeps locked allocations
      - deletes non-locked allocations
      - loads ALL curriculum slots for the student's major (including BUCKET slots)
      - uses CourseOption edges for COURSE/BUNDLE matching
      - fills BUCKET slots from remaining courses by rule/credits
    """
    session = session or db.session

    student: StudentProfile | None = session.get(StudentProfile, student_profile_id)
    if not student:
        return

    # ----------------------------
    # 0) Extract & normalize course instances
    # ----------------------------
    instances = extract_course_instances(student.courses_by_term or {})
    term_by_course = preferred_term_by_course(instances)
    taken_course_ids = sorted(set(term_by_course.keys()))

    # ----------------------------
    # 1) Locked allocations
    # ----------------------------
    locked_allocs = session.execute(
        select(CourseAllocation).where(
            CourseAllocation.student_profile_id == student_profile_id,
            CourseAllocation.locked.is_(True),
        )
    ).scalars().all()

    used_courses: Set[str] = {a.course_id for a in locked_allocs}
    locked_slots: Set[str] = {a.requirement_slot_id for a in locked_allocs}

    # ----------------------------
    # 2) Clear non-locked allocations
    # ----------------------------
    session.execute(
        delete(CourseAllocation).where(
            CourseAllocation.student_profile_id == student_profile_id,
            CourseAllocation.locked.is_(False),
        )
    )
    session.flush()

    if not taken_course_ids:
        return

    # ----------------------------
    # 3) Load Course rows (credits/department for BUCKET rules)
    # ----------------------------
    courses_by_id: Dict[str, Course] = {
        c.id: c
        for c in session.execute(select(Course).where(Course.id.in_(taken_course_ids))).scalars().all()
    }

    # ----------------------------
    # 4) PATCH: Load curriculum (ALL requirement groups/slots for this student's major)
    #    This is the key fix so BUCKET slots are present even if no CourseOptions point to them.
    # ----------------------------
    if not student.major_id:
        # No major selected yet -> can't compute allocations
        return

    curr_group_ids = session.execute(
        select(RequirementGroup.id).where(RequirementGroup.owner_id == student.major_id)
    ).scalars().all()

    if not curr_group_ids:
        return

    groups: List[RequirementGroup] = session.execute(
        select(RequirementGroup).where(RequirementGroup.id.in_(curr_group_ids))
    ).scalars().all()
    groups_by_id = {g.id: g for g in groups}

    curriculum_slots: List[RequirementSlot] = session.execute(
        select(RequirementSlot).where(RequirementSlot.requirement_group_id.in_(curr_group_ids))
    ).scalars().all()
    slots_by_id = {s.id: s for s in curriculum_slots}

    # Partition curriculum slots by type (this now includes BUCKET slots)
    course_like_slot_ids = [
        sid for sid, s in slots_by_id.items()
        if s.slot_type in (SlotType.COURSE, SlotType.BUNDLE)
    ]
    bucket_slot_ids = [
        sid for sid, s in slots_by_id.items()
        if s.slot_type == SlotType.BUCKET
    ]

    # ----------------------------
    # 5) CourseOption edges (explicit COURSE/BUNDLE matching)
    # ----------------------------
    cos = session.execute(
        select(CourseOption).where(CourseOption.course_id.in_(taken_course_ids))
    ).scalars().all()

    bundle_ids = sorted({co.bundle_id for co in cos if co.bundle_id})
    bundles_by_id: Dict[str, CourseBundle] = {}
    if bundle_ids:
        bundles_by_id = {
            b.id: b
            for b in session.execute(select(CourseBundle).where(CourseBundle.id.in_(bundle_ids))).scalars().all()
        }

    eligible_slots_by_course: Dict[str, Set[str]] = {}
    for co in cos:
        cid = co.course_id
        eligible_slots_by_course.setdefault(cid, set())

        # Direct slot mapping
        if co.requirement_slot_id:
            eligible_slots_by_course[cid].add(co.requirement_slot_id)

        # Bundle mapping -> resolve bundle -> slot
        if co.bundle_id:
            b = bundles_by_id.get(co.bundle_id)
            if b and b.requirement_slot_id:
                eligible_slots_by_course[cid].add(b.requirement_slot_id)

    # Only consider eligible slots that actually exist in this student's curriculum
    for cid, sids in list(eligible_slots_by_course.items()):
        eligible_slots_by_course[cid] = {sid for sid in sids if sid in slots_by_id}

    # ----------------------------
    # 6) Build candidates per COURSE/BUNDLE slot
    # ----------------------------
    candidates_by_slot: Dict[str, List[str]] = {}
    for cid, sids in eligible_slots_by_course.items():
        if cid in used_courses:
            continue
        for sid in sids:
            if sid in locked_slots:
                continue
            if sid not in course_like_slot_ids:
                continue
            candidates_by_slot.setdefault(sid, []).append(cid)

    def slot_sort_key(slot_id: str) -> Tuple[int, int, int, str]:
        s = slots_by_id.get(slot_id)
        g = groups_by_id.get(s.requirement_group_id) if s else None

        pri = getattr(g, "priority", 0) if g else 0
        num_candidates = len(set(candidates_by_slot.get(slot_id, [])))
        pos = getattr(s, "position", 9999) if s else 9999

        # higher pri first, then most constrained
        return (-pri, num_candidates, pos, slot_id)

    # ----------------------------
    # 7) Allocate COURSE/BUNDLE slots first
    # ----------------------------
    for sid in sorted(candidates_by_slot.keys(), key=slot_sort_key):
        if sid in locked_slots:
            continue

        chosen = None
        for cid in candidates_by_slot.get(sid, []):
            if cid not in used_courses:
                chosen = cid
                break

        if not chosen:
            continue

        session.add(
            CourseAllocation(
                student_profile_id=student_profile_id,
                course_id=chosen,
                requirement_slot_id=sid,
                term=term_by_course.get(chosen, "UNKNOWN"),
                locked=False,
                reason="most_constrained",
            )
        )
        used_courses.add(chosen)

    session.flush()

    # ----------------------------
    # 8) Allocate BUCKET slots from remaining courses (credits-based)
    # ----------------------------
    remaining_courses = [cid for cid in taken_course_ids if cid not in used_courses and cid in courses_by_id]

    def bucket_sort_key(slot_id: str) -> Tuple[int, int, str]:
        s = slots_by_id.get(slot_id)
        g = groups_by_id.get(s.requirement_group_id) if s else None
        pri = getattr(g, "priority", 0) if g else 0
        pos = getattr(s, "position", 9999) if s else 9999
        return (-pri, pos, slot_id)

    for bucket_id in sorted(bucket_slot_ids, key=bucket_sort_key):
        if bucket_id in locked_slots:
            continue

        slot = slots_by_id[bucket_id]
        need = int(slot.min_credits_required or 0)
        if need <= 0:
            continue

        rule = slot.slot_rule or {}
        picked: List[str] = []
        credits = 0

        for cid in list(remaining_courses):
            course = courses_by_id[cid]
            if not course_matches_bucket_rule(course, rule):
                continue

            picked.append(cid)
            credits += int(course.credits or 0)
            remaining_courses.remove(cid)
            used_courses.add(cid)

            if credits >= need:
                break

        if not picked:
            continue

        # Store each picked course as an allocation row to the same bucket slot.
        for cid in picked:
            session.add(
                CourseAllocation(
                    student_profile_id=student_profile_id,
                    course_id=cid,
                    requirement_slot_id=bucket_id,
                    term=term_by_course.get(cid, "UNKNOWN"),
                    locked=False,
                    reason="bucket_fill",
                )
            )

        session.flush()

    # Caller commits
