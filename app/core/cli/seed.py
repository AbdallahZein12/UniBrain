import json 
from pathlib import Path 
from flask import current_app
from flask.cli import with_appcontext
import click  

from app.core import db
from app.models.catalog import Campus, Major, Department, Course, CourseOffering
from app.models.ontology import RequirementGroup, RequirementSlot, CourseBundle, CourseOption


def _load_json(rel_path:str):
    base = Path(current_app.root_path).parent
    path = base / rel_path 
    if not path.exists():
        raise FileNotFoundError(f"Seed file not found: {path}")
    
    return json.loads(path.read_text(encoding="utf-8"))

def _upsert(model, obj_id: str, **fields):
    """
    Idempotent upsert by pk (id)
    """ 
    
    row = db.session.get(model, obj_id)
    if row is None: 
        row = model(id=obj_id, **fields)
        db.session.add(row)
        return row, True 

    for k, v in fields.items():
        setattr(row, k, v)
    return row, False 

@click.command("seed")
@with_appcontext
def seed_command():
    """
    Seed campuses, majors, courses from data/seed/*.json
    """
    
    campuses = _load_json("data/seed/campuses.json")
    majors = _load_json("data/seed/majors.json")
    departments = _load_json("data/seed/departments.json")
    courses = _load_json("data/seed/courses.json")
    course_offerings = _load_json("data/seed/course_offerings.json")
    requirement_groups = _load_json("data/seed/requirement_groups.json")
    requirement_slots = _load_json("data/seed/requirement_slots.json")
    course_bundles = _load_json("data/seed/course_bundles.json")
    course_options = _load_json("data/seed/course_options.json")
    
    created = {"campuses": 0, "majors": 0, "departments": 0, "courses": 0, "course_offerings": 0, "requirement_groups": 0, "requirement_slots": 0, "course_bundles": 0, "course_options": 0}
    updated = {"campuses": 0, "majors": 0, "departments": 0, "courses": 0, "course_offerings": 0, "requirement_groups": 0, "requirement_slots": 0, "course_bundles": 0, "course_options": 0}
    
    for c in campuses:
        row, is_new = _upsert(
            Campus, 
            c["id"],
            name = c.get("name","").strip(),
            address = c.get("address","").strip()
        )
        
        created["campuses"] += int(is_new)
        updated["campuses"] += int(not is_new)
    
    db.session.flush() # ensure FKs can resolve 
    
    for d in departments: 
        row, is_new = _upsert(
            Department, 
            d["id"],
            name=d.get("name","").strip(),
            campus_id=d.get("campus_id")   
        )
        
        created["departments"] += int(is_new)
        updated["departments"] += int(not is_new)
        
    db.session.flush()
    
    for c in courses:
        row, is_new = _upsert(
            Course,
            c["id"],
            title=c.get("title"),
            credits=c.get("credits"),
            department_id=c.get("department_id"),
            prereq_rules = c.get("prereq_rules"),
            prereq_notes = c.get("prereq_notes")
        )
        
        created["courses"] += int(is_new)
        updated["courses"] += int(not is_new)
    
    db.session.flush()
    
    for c_o in course_offerings:
        row, is_new = _upsert(
            CourseOffering,
            c_o["id"],
            course_id=c_o.get("course_id").strip(),
            campus_id=c_o.get("campus_id").strip(),
            terms_offered=c_o.get("terms_offered"),
        )
        
        created["course_offerings"] += int(is_new)
        updated["course_offerings"] += int(not is_new)
        
    db.session.flush()
        
    for m in majors: 
        row, is_new = _upsert(
            Major, 
            m["id"],
            name=m.get("name", "").strip(),
            degree=m.get("degree","").strip(),
            department_id=m.get("department_id"),
            campus_id = m.get("campus_id"),
            total_credits_required = m.get("total_credits_required")
        )
        
        created["majors"] += int(is_new)
        updated["majors"] += int(not is_new)
        
    db.session.flush()
    
    for rg in requirement_groups: 
        row, is_new = _upsert(
            RequirementGroup, 
            rg["id"],
            name=rg.get("name"),
            scope=rg.get("scope"),
            owner_id=rg.get("owner_id"),
            rule_type = rg.get("rule_type"),
            choose_n = rg.get("choose_n")
        )
        
        created["requirement_groups"] += int(is_new)
        updated["requirement_groups"] += int(not is_new)
    
    db.session.flush()
    
    for rs in requirement_slots: 
        row, is_new = _upsert(
            RequirementSlot, 
            rs["id"],
            requirement_group_id=rs.get("requirement_group_id"),
            label=rs.get("label"),
            min_credits_required=rs.get("min_credits_required"),
            slot_type = rs.get("slot_type"),
            slot_rule = rs.get("slot_rule"),
            position=rs.get("position")
        )
        
        created["requirement_slots"] += int(is_new)
        updated["requirement_slots"] += int(not is_new)

    db.session.flush()
    
    for cb in course_bundles: 
        row, is_new = _upsert(
            CourseBundle, 
            cb["id"],
            requirement_slot_id=cb.get("requirement_slot_id"),
            label=cb.get("label"),
            note=cb.get("note"),
            must_be_same_term = cb.get("slot_type"),
        )
        
        created["course_bundles"] += int(is_new)
        updated["course_bundles"] += int(not is_new)

    db.session.flush()
    
    for co in course_options: 
        row, is_new = _upsert(
            CourseOption, 
            co["id"],
            requirement_slot_id=co.get("requirement_slot_id"),
            bundle_id=co.get("bundle_id"),
            course_id=co.get("course_id"),
            note=co.get("note")
        )
        
        created["course_options"] += int(is_new)
        updated["course_options"] += int(not is_new)
    
    
    db.session.commit()
    
    click.echo("Seed complete!")
    click.echo(f"Campuses: created {created['campuses']}, updated {updated['campuses']}")
    click.echo(f"Majors:   created {created['majors']}, updated {updated['majors']}")
    click.echo(f"Departments:  created {created['departments']}, updated {updated['departments']}")
    click.echo(f"Courses:  created {created['courses']}, updated {updated['courses']}")
    click.echo(f"Course Offerings:  created {created['course_offerings']}, updated {updated['course_offerings']}")
    click.echo(f"Requirement Groups:  created {created['requirement_groups']}, updated {updated['requirement_groups']}")
    click.echo(f"Requirement Slots:  created {created['requirement_slots']}, updated {updated['requirement_slots']}")
    click.echo(f"Course Bundles:  created {created['course_bundles']}, updated {updated['course_bundles']}")
    click.echo(f"Course Options:  created {created['course_options']}, updated {updated['course_options']}")
    