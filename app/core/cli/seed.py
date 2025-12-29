import json 
from pathlib import Path 
from flask import current_app
from flask.cli import with_appcontext
import click  

from app.core import db
from app.models.catalog import Campus, Major, Department, Course


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
    
    created = {"campuses": 0, "majors": 0, "departments": 0, "courses": 0}
    updated = {"campuses": 0, "majors": 0, "departments": 0, "courses": 0}
    
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
    
        
    db.session.commit()
    
    click.echo("Seed complete!")
    click.echo(f"Campuses: created {created['campuses']}, updated {updated['campuses']}")
    click.echo(f"Majors:   created {created['majors']}, updated {updated['majors']}")
    click.echo(f"Departments:  created {created['departments']}, updated {updated['departments']}")
    click.echo(f"Courses:  created {created['courses']}, updated {updated['courses']}")