# Hospital Staff Scheduler

A comprehensive scheduling solution featuring both a modern Desktop Application (PyQt6) and a Web Dashboard (Next.js + FastAPI). This project uses the Gurobi Optimizer to generate optimal staff schedules based on employee availability, skills, and shift demands.

## 📋 Prerequisites

-   **Python 3.9+**
-   **Node.js 16+** (for the Web Dashboard)
-   **Gurobi Optimizer** (License required, academic license available)

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd project
```

### 2. Python Environment Setup

It is recommended to use a virtual environment for Python dependencies.

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 🖥️ Option 1: Running the Desktop App (PyQt6)

The desktop application provides a standalone interface for managing data, running the scheduler, and visualizing results with charts.

### How to Run

Ensure your virtual environment is activated, then run:

```bash
python desktop_app/main.py
```

### Features

-   **Data Management**: View and manage Employees and Shifts.
-   **Demands View**: See daily staffing requirements.
-   **Scheduler**: Configure horizon and run the optimization engine.
-   **Visualization**: Interactive Gantt chart, Workload distribution (Bar Chart), and Cost analysis (Donut Chart).
-   **Database Seeding**: Built-in tool to reset and populate the database with test data.

---

## 🌐 Option 2: Running the Web App (React + FastAPI)

The web application consists of a FastAPI backend and a Next.js frontend.

### 1. Start the Backend API

The backend serves the API endpoints and handles the database connection.

```bash
# From the project root (with venv activated)
python hospital_scheduler/run.py
```

_The API will be available at `http://localhost:8000`_
_API Documentation (Swagger UI): `http://localhost:8000/docs`_

### 2. Start the Frontend Dashboard

Open a new terminal window for the frontend.

```bash
cd hospital-scheduler-dashboard

# Install dependencies (first time only)
npm install
# OR
yarn install

# Run the development server
npm run dev
# OR
yarn dev
```

_The dashboard will be available at `http://localhost:3000`_

---

## 💾 Database Management

The project uses SQLite (`hospital_scheduler.db`).

### Seeding Data

You can populate the database with sample data (Alice, Bob, Charlie, Dr. Smith, etc.) using the Desktop App or the command line.

**Via Desktop App:**

1. Go to the **Data Management** tab.
2. Click **"Seed Database (Reset)"**.

**Via Command Line:**

```bash
python hospital_scheduler/seed.py
```

---

## 📂 Project Structure

```
project/
├── desktop_app/                # PyQt6 Desktop Application
│   ├── main.py                 # Entry point for Desktop App
│   └── projects/               # GUI Modules
├── hospital_scheduler/         # Python Backend & Logic
│   ├── app/                    # FastAPI App & Models
│   ├── run.py                  # Entry point for Backend API
│   └── seed.py                 # Database seeding script
├── hospital-scheduler-dashboard/ # Next.js Web Frontend
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🤝 Contributing

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.
