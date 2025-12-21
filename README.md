# 🚀 UniBrain – The Intelligence Layer for Universities

**UniBrain** is an early-stage prototype exploring how universities can unify fragmented academic data into a **single structured intelligence layer**.

At its core, UniBrain models university knowledge—programs, majors, courses, and requirements—using a formal ontology.  
On top of this structure, UniBrain enables an AI-assisted interface that can answer academic questions with clarity, traceability, and context.

> **Long-term vision:**  
> UniBrain aims to become the *Palantir of higher education* — a centralized intelligence layer that brings automation, explainability, and AI-driven support to the entire university ecosystem.

This repository contains **v1**, a closed beta prototype designed to support early technical and conceptual discussions with **LIU Brooklyn IT and Engineering leadership**.

---

## 🌐 Problem Context

Universities today operate with highly fragmented information systems:

- Program requirements buried in PDFs  
- Course details scattered across catalogs  
- Office information spread across multiple websites  
- Advising workflows that rely on manual interpretation  
- SIS and LMS systems that are not semantically searchable  

This fragmentation leads to confusion, inefficiency, and inconsistent advising outcomes.

---

## 🧠 UniBrain Concept

UniBrain separates **knowledge modeling** from **user interaction**.

### 🧩 UniBrain Ontology (Knowledge Graph)

A structured domain model representing:

- Campuses  
- Departments  
- Majors  
- Courses  
- Degree requirements  
- Relationships and constraints between them  

The ontology is designed to be:

- Explicit  
- Queryable  
- Explainable  
- Extensible across institutions  

### 💬 UniBrain Assist (AI Interface)

An AI-powered assistant layered on top of the ontology that can answer questions such as:

- What courses do I still need to graduate as a CS major?  
- What are the prerequisites for BIO 102?  
- How do I contact the registrar?  
- Which requirements would change if I switch majors?  

Unlike traditional chatbots, UniBrain’s answers are grounded in **structured academic rules**, not opaque text generation.

---

## 🎯 v1 Goals

The v1 prototype focuses on **feasibility and clarity**, not production scale.

Primary objectives:

- Demonstrate ontology-driven academic modeling  
- Validate UX concepts for advising workflows  
- Enable early stakeholder feedback  
- Prepare for deeper conversations with university IT leadership  

v1 uses:

- Publicly available LIU data  
- Dummy student records  
- A controlled invite-only access flow  
- A modern Flask + SCSS frontend  

---

## 🧪 v1 Feature Scope

### Implemented

- Ontology-backed academic data models  
- Clean landing page and concept walkthrough  
- Login and signup flow (invite-code gated)  
- Modular Flask application architecture  
- SQLite-backed persistence for development  
- UML / models diagram for ontology visualization  

### In Progress

- Student onboarding and profile creation  
- Degree progress evaluation  
- Query endpoints for assistant logic  
- Ontology-backed rule evaluation  

---

## 🏗 Project Structure

UNIBRAIN
│  
├── app  
│   ├── core  
│   │   ├── config.py  
│   │   └── extensions.py   
|   |   └── __init__.py  
│   │  
│   ├── models  
│   │   ├── user.py  
│   │   └── invite_code.py  
|   |   └── __init__.py  
│   │  
│   ├── routes  
│   │   └── health.py  
│   │  
│   ├── v1    
│   │   ├── auth  
│   │   │   ├── routes.py  
│   │   │   └── templates  
│   │   │   ├── static  
│   │   |   └── __init__.py  
│   │   │       
│   │   │  
│   │   ├── static  
│   │   └── templates  
│   │   └── __init__.py  
│   │   └── routes.py    
│   │  
│   └── __init__.py  
│  
├── instance            # SQLite DB (ignored by git)  
├── migrations          # Alembic migrations  
├── requirements.txt  
├── wsgi.py  
└── README.md  



---

## 🛠 Tech Stack

- **Flask** – application framework  
- **Flask-Login** – session-based authentication  
- **Flask-Migrate / Alembic** – schema migrations  
- **SQLite** – development persistence layer  
- **SQLAlchemy** – ORM and domain modeling  
- **Jinja2** – server-side templating  
- **SCSS** – modern, modular styling  
- **Python 3.10+**

---

## ▶️ Running the Project Locally

### 1️⃣ Clone the repository

```bash
git clone https://github.com/AbdallahZein12/UniBrain.git
cd UniBrain
```

### 2️⃣ Create and activate a virtual environment

python -m venv env


```bash
# macOS / Linux
source env/bin/activate

# Windows
env\Scripts\activate
```

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Run database migrations

```bash
python -m flask --app wsgi db upgrade
```

### 5️⃣ Start the development server

```bash
python -m flask --app wsgi run
```

### 6️⃣ Open the app

```bash
http://localhost:5000
```

## 🔐 Access Control (v1)

This prototype is **invite-only**.

Signup requires a valid invite code, which:

- Has limited uses  
- Can expire  
- Can be revoked if abused  

Invite codes are stored server-side and consumed transactionally during signup.  
This keeps early access controlled while the platform is not production-ready.

This mechanism is intentionally lightweight and designed to be replaced or expanded
(e.g., per-user invites, allowlists, or SSO) in later phases.

---

## 🚧 Roadmap

### Near-Term

- Student profile onboarding  
- Degree progress evaluation  
- Ontology-backed query endpoints  
- Assistant proof-of-concept  
- Visual requirement graph  

### Long-Term

- SIS integration  
- LMS integration  
- Multi-campus support  
- Admin dashboards  
- AI-assisted advising engine  
- Automated ontology ingestion pipelines  

---

## 🤝 Status

UniBrain is an **exploratory prototype**.

It is not production software and does not integrate with live student systems.  
Any real deployment would require coordination with:

- University IT  
- Registrar  
- Academic Affairs  
- Compliance and FERPA stakeholders  

---

## 📌 Updates

**12/12/2025** – Added ontology / models diagram  

![Models Diagram](./models.png)

**12/15/2025** – Added landing page desgin, logo and login portal (dev_login_feature)

**12/21/2025** – Added landing page, authentication flow, and invite-only access

