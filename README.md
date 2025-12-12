# 🚀 UniBrain – The Intelligence Layer for Universities

UniBrain is an early prototype of a platform that unifies university data such as programs, majors, requirements, offices, and more into a single structured knowledge graph.  
On top of that graph, UniBrain exposes an AI powered assistant capable of answering natural questions from students, faculty, and administrators.

The long term vision is to become the Palantir of higher education  
a centralized intelligent data layer that brings clarity, automation, and AI driven support to the entire university ecosystem.

This repository contains v1, a demo designed for early discussions with LIU Brooklyn IT and engineering leadership.

---

## 🌐 Concept Overview

Universities today have fragmented information

* Program requirements spread across PDFs  
* Course details buried in catalogs  
* Office information scattered across different pages  
* Advising done through manual processes  
* SIS and LMS systems not integrated or searchable semantically  

UniBrain solves this by building:

### 🧠 UniBrain Graph  
A structured ontology that models:

* Majors  
* Courses  
* Requirements  
* Offices  
* Departments  
* Relationships between them  

### 💬 UniBrain Assist  
An AI interface that can answer questions such as

* What do I still need to graduate as a CS major  
* How do I contact the registrar  
* What are the prerequisites for BIO 102  
* Where is the advising office and what are the hours  

### 🎯 Immediate Goal v1 Demo
Build a small but functional prototype using:

* Public LIU data  
* Dummy student records  
* Flask and SCSS frontend  
* JSON based NoSQL style backend  

This proves feasibility before engaging with full university IT for real data integrations.

---

## 🧪 Demo Steps v1 Roadmap

This demo includes four foundational data layers

### 1 University Basic Info  
Campus name address website core offices.

### 2 Majors and Programs  
A small curated set of LIU Brooklyn majors for example CS Biology Business.

### 3 Course Requirements  
Structured queryable requirements such as:

* Core courses  
* Labs  
* Electives  
* Prerequisites  

### 4 Contacts  
Registrar advising financial aid housing.

---

### v1 Feature Flow

1 Load structured JSON data simulating a university knowledge base  
2 Render a clean landing page explaining the concept  
3 Provide endpoints for the assistant and API coming next  
4 Demonstrate a query such as retrieving requirements for a major  
5 Show the ontology visually static mock  
6 Prepare for conversations with LIU Deputy CIO  

---

## 🏗 Project Structure

UNIBRAIN
│
├── app
│ ├── init.py
│ ├── v1
│ │ ├── init.py
│ │ ├── routes.py
│ │ ├── static
│ │ │ ├── css
│ │ │ ├── js
│ │ │ └── img
│ │ └── templates
│ │ ├── base.html
│ │ └── home.html
│ │
│ └── templates global
│
├── main.py
├── requirements.txt
├── .env
└── README.md

---

## 🛠 Tech Stack

* Flask for backend and routing  
* Jinja2 for templating  
* SCSS for modern scalable styling  
* JSON for early NoSQL style knowledge storage  
* Python 3 for application logic  
* VS Code for development  

---

## ▶️ How to Run the Project

### 1 Clone the repo  
```bash
git clone https://github.com/AbdallahZein12/unibrain.git
cd unibrain

### 2 Create and activate a virtual environment  
python -m venv env  
source env/bin/activate        macOS and Linux  
env\Scripts\activate           Windows  

### 3 Install dependencies  
pip install -r requirements.txt  

### 4 Run the development server  
python main.py  

### 5 Open the app  
Visit  
http://localhost:5000  

You should see the UniBrain home page.

---

## 🚧 Planned Features After v1

### Near term
Add more majors and requirement schemas  
Add search and assistant endpoint  
Data ingestion pipeline for public LIU pages  
Graph visualization UI  
Student dummy profiles for degree progress queries  

### Long term
SIS integration  
LMS integration  
Multi campus architecture  
Admin dashboard  
AI advising engine  
Auto updating ontology pipeline  

---

## 🤝 Status

This is an exploratory prototype built to support initial meetings with LIU leadership.  
Real integrations require coordination with

LIU IT  
Deputy CIO  
Registrar  
Academic affairs  
Compliance FERPA and data security  




