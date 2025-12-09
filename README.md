# Operational Research Projects - Group Deliverables

This repository contains **four sub-projects** developed as part of an Operational Research assignment.
Each team member tackled a different subject from the provided list:

-   Hospital Scheduler by Yassine Krichen
-   Subject X
-   Subject X
-   Subject X

This repository groups all deliverables in one place.

---

# 📂 Project Overview

The repository contains the following sub-projects:

| Folder                          | Description                                                         |
| ------------------------------- | ------------------------------------------------------------------- |
| `desktop_app/`                  | PyQt6 desktop interface for managing data and running optimization. |
| `hospital_scheduler/`           | Core scheduling logic + FastAPI backend.                            |
| `hospital-scheduler-dashboard/` | Next.js web dashboard for visualization.                            |
| `...`                           | Additional student projects.                                        |

Each component works independently but some can be combined (Desktop App or Web Dashboard + API).

---

# 🚀 How to Run the Project

Below are the only two workflows that matter: running the **desktop application** or running the **web dashboard**.

---

## 🖥️ Option 1: Run the Desktop App

```bash
python -m venv venv
.\venv\Scripts\Activate
pip install -r requirements.txt
python desktop_app/main.py
```

---

## 🌐 Option 2: Run the Web App (API + Dashboard)

note: this only applies for the Hospital Scheduler project

### 1. Start the backend API

```bash
python -m venv venv
.\venv\Scripts\Activate
pip install -r requirements.txt
python hospital_scheduler/run.py
```

### 2. Start the frontend dashboard

```bash
cd hospital-scheduler-dashboard
npm install --legacy-peer-deps
npm run dev
```

---

# 📘 Assignment Summary

This work is part of the Operational Research course.
Students choose a topic from a given list and build a solution applying OR techniques.
This repository aggregates all four final implementations in one place.

---

# 🤝 Contributing

This repository is shared across the group, so contribution rules stay generic:

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/YourFeature`).
3. Commit changes (`git commit -m "Describe your update"`).
4. Push the branch.
5. Open a Pull Request.
