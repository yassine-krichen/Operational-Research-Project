# Hospital Shift Optimization Engine

## Executive Summary

This software is an intelligent scheduling assistant designed for hospital administrators and nurse managers. It automates the complex task of creating staff rosters, replacing hours of manual spreadsheet work with a mathematical optimization engine.

Instead of manually dragging and dropping shifts, you define the rules (e.g., "Nurses need 11 hours rest," "ICU requires 2 specialized staff at night"), and the engine calculates the mathematically optimal schedule that minimizes costs while guaranteeing all rules are met.

## Business Value

-   Cost Efficiency: Eliminates unnecessary overtime by prioritizing standard-rate staff.

-   Compliance: Guarantees adherence to labor laws (e.g., rest periods, maximum weekly hours).

-   Fairness: Can be tuned to distribute unpopular shifts or hours equitably.

-   Speed: Generates a full weekly schedule in seconds rather than days.

## How It Works

1. The Inputs (Data)

The system requires three main data sources:

-   Employees: Who works here? What are their skills (RN, ICU, MD)? What is their hourly rate?

-   Shifts: What are the standard shift times (Morning 7-3, Night 11-7)?

-   Demand: How many people of each skill level do we need for every shift next week?

2. The Engine (Optimization)

When you click "Create Schedule," the system does not just guess. It translates your hospital's reality into a mathematical formula. It considers millions of possibilities to find the single best combination of assignments that meets every patient demand without breaking any labor rules.

3. The Output (Schedule)

The result is a detailed roster:

-   Who: Employee Name

-   When: Date and Shift

-   Role: The specific skill they are covering (e.g., Charge Nurse vs. General RN)

## Key Features

-   Skill Matching: Ensures an ICU shift is only ever assigned to an ICU-qualified nurse.

-   Rest Assurance: Automatically prevents "clopens" (closing late at night and opening early the next morning) unless explicitly allowed.

-   Slack Handling: If it is impossible to meet demand (e.g., 5 nurses needed but only 4 available), the system will still produce a schedule but highlight exactly where the shortage is, rather than crashing.

## Usage for Administrators

1. Upload Data: Ensure your employee and demand lists are up to date in the database.

2. Run Scheduler: Submit a request for the upcoming week.

3. Review Status: The system will report "OPTIMAL" (perfect schedule found) or "FEASIBLE" (schedule found, but might have shortages).

4. Export: Retrieve the assignments for distribution to staff.
