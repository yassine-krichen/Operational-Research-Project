# Hospital Staff Scheduling Optimization Report

## 1. Introduction

This project implements an **Enterprise-Grade Nurse Scheduling System (NSS)** using Mixed-Integer Programming (MIP). The system is designed to generate optimal staff schedules that minimize labor costs while strictly adhering to complex labor laws, hospital policies, and employee preferences. The core optimization engine is built using **Gurobi Optimizer** integrated with a modern **FastAPI** backend and **Next.js** frontend.

## 2. Problem Description

The scheduling problem involves assigning a set of employees (nurses, doctors) to specific shifts over a defined planning horizon (e.g., 1-4 weeks) to meet fluctuating demand for various skills.

### Key Entities

-   **Employees ($E$)**: Staff members with specific roles, skills, hourly costs, and availability constraints.
-   **Shifts ($S$)**: Defined work periods (e.g., Morning, Afternoon, Night) with specific start/end times.
-   **Days ($T$)**: The planning horizon (e.g., $t=1 \dots 7$).
-   **Skills ($K$)**: Qualifications required for shifts (e.g., "RN", "Senior", "ICU").

## 3. Mathematical Model

The problem is formulated as a **Mixed-Integer Linear Program (MILP)**.

### 3.1 Decision Variables

-   **Assignment Variable**:
    $$x_{e,t,s} \in \{0, 1\}$$
    Equals 1 if employee $e$ is assigned to shift $s$ on day $t$, 0 otherwise.

-   **Slack Variable (Elastic Demand)**:
    $$y_{t,s,k} \ge 0$$
    Represents the amount of uncovered demand (shortage) for skill $k$ on shift $s$ at day $t$. This allows the solver to find "best effort" solutions even when perfect coverage is impossible.

### 3.2 Objective Function

The objective is to minimize the weighted sum of Labor Cost, Uncovered Demand Penalty, and Preference Violations.

$$
\text{Minimize } Z = W_1 \sum_{e,t,s} (C_e \cdot L_s \cdot x_{e,t,s}) + W_2 \sum_{t,s,k} y_{t,s,k} + W_3 \sum_{e,t,s \in P_{avoid}} x_{e,t,s}
$$

Where:

-   $C_e$: Hourly cost of employee $e$.
-   $L_s$: Length of shift $s$ in hours.
-   $W_1, W_2, W_3$: Weights for Cost, Coverage, and Preferences respectively.
-   $P_{avoid}$: Set of assignments that violate employee preferences.

### 3.3 Constraints

#### C1: Demand Coverage (Hard/Elastic)

Ensure enough skilled staff are assigned, or record the shortage in the slack variable.

$$
\sum_{e \in E_k} x_{e,t,s} + y_{t,s,k} \ge D_{t,s,k} \quad \forall t, s, k
$$

Where $D_{t,s,k}$ is the required number of staff with skill $k$.

#### C2: One Shift Per Day

An employee cannot work more than one shift per day.

$$
\sum_{s \in S} x_{e,t,s} \le 1 \quad \forall e, t
$$

#### C3: Maximum Weekly Hours

Employees must not exceed their maximum contract hours.

$$
\sum_{t \in T} \sum_{s \in S} (L_s \cdot x_{e,t,s}) \le H_{max, e} \quad \forall e
$$

#### C4: Minimum Rest Time & Forward Rotation

Employees must have at least $R_{min}$ hours of rest between shifts. This implicitly enforces **Forward Rotation** (e.g., preventing Night $\to$ Morning transitions).

$$
x_{e,t,s_1} + x_{e,t+1,s_2} \le 1 \quad \forall e, t, \forall (s_1, s_2) \in \text{ForbiddenPairs}
$$

Where a pair is forbidden if $\text{Gap}(s_1, s_2) < R_{min}$.

#### C5: Maximum Consecutive Working Days

Employees cannot work more than $N_{consec}$ days in a row.

$$
\sum_{j=t}^{t+N_{consec}} \sum_{s \in S} x_{e,j,s} \le N_{consec} \quad \forall e, t
$$

#### C6: Skill Ratios (ICU Safety Rule)

For critical shifts (e.g., ICU), the number of Senior staff must equal or exceed Junior staff.

$$
\sum_{e \in \text{Senior}} x_{e,t,s} \ge \sum_{e \in \text{Junior}} x_{e,t,s} \quad \forall t, s \in S_{ICU}
$$

#### C7: Maximum Night Shifts

Limit the burden of night shifts on any single employee.

$$
\sum_{t \in T} \sum_{s \in S_{night}} x_{e,t,s} \le N_{night}^{max} \quad \forall e
$$

#### C8: Minimum Shifts (Fairness)

Ensure every employee gets a minimum number of shifts (if available) to distribute work fairly.

$$
\sum_{t \in T} \sum_{s \in S} x_{e,t,s} \ge N_{shifts}^{min} \quad \forall e
$$

#### C9: Complete Weekends

If an employee works on Saturday, they must also work on Sunday (and vice versa), preventing split weekends.

$$
\sum_{s \in S} x_{e, \text{Sat}, s} = \sum_{s \in S} x_{e, \text{Sun}, s} \quad \forall e
$$

## 4. Solver Implementation Details

### 4.1 Technology Stack

-   **Language**: Python 3.10+
-   **Solver**: Gurobi Optimizer (via `gurobipy`)
-   **API**: FastAPI (Asynchronous job processing)
-   **Database**: SQLite (SQLAlchemy ORM)

### 4.2 Handling Infeasibility (IIS)

The system implements **Irreducible Inconsistent Subsystem (IIS)** computation. If the model is infeasible (e.g., demand exceeds total capacity), the solver identifies the specific set of conflicting constraints and logs them. This allows administrators to pinpoint exactly _why_ a schedule cannot be generated (e.g., "Insufficient staff for ICU Night Shift on Tuesday").

### 4.3 Multi-Objective Optimization

The model uses a weighted objective function to balance competing goals:

1.  **Cost Efficiency**: Minimizing total payroll.
2.  **Service Level**: Minimizing uncovered shifts (via high penalty $W_2$).
3.  **Employee Satisfaction**: Minimizing assignments to "avoid" shifts.

## 5. Conclusion

This project demonstrates a sophisticated application of Operations Research in a healthcare setting. By incorporating real-world constraints like **Forward Rotation**, **Skill Ratios**, and **Complete Weekends**, the model moves beyond academic exercises to address actual hospital scheduling challenges. The integration of **Elastic Constraints** ensures the system remains robust and usable even under high-demand scenarios where perfect coverage is mathematically impossible.
