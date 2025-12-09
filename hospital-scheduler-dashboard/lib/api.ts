export const API_BASE =
    process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";

export interface Employee {
    id?: number;
    employee_id: string;
    name: string;
    role: "Nurse" | "Doctor";
    skills: string;
    hourly_cost: number;
    max_weekly_hours: number;
}

export interface Shift {
    id?: number;
    shift_id: string;
    name: string;
    start_time: string;
    end_time: string;
    length_hours: number;
}

export interface Demand {
    id?: number;
    date: string;
    shift_id: string;
    skill: string;
    required: number;
}

export interface ScheduleRequest {
    horizon_start: string;
    horizon_days: number;
    solver_time_limit: number;
    allow_uncovered_demand: boolean;
    penalty_uncovered: number;
    weight_preference: number;
    max_consecutive_days: number;
    min_rest_hours: number;
    max_night_shifts: number;
    min_shifts_per_employee: number;
    require_complete_weekends: boolean;
}

export interface Assignment {
    employee_id: string;
    employee_name: string;
    role: string;
    date: string;
    shift_id: string;
    shift_name: string;
    hours: number;
    cost: number;
}

export interface ScheduleResult {
    run_id: string;
    status:
        | "QUEUED"
        | "RUNNING"
        | "OPTIMAL"
        | "FEASIBLE"
        | "INFEASIBLE"
        | "ERROR";
    objective_value?: number;
    assignments?: Assignment[];
    logs?: string;
    created_at?: string;
    completed_at?: string;
}

export interface ScheduleSummary {
    run_id: string;
    status: string;
    objective_value?: number;
    created_at?: string;
    completed_at?: string;
    assignment_count: number;
}

async function fetchApi<T>(
    endpoint: string,
    options?: RequestInit
): Promise<T> {
    const res = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...options?.headers,
        },
    });

    if (!res.ok) {
        throw new Error(`API Error: ${res.status} ${res.statusText}`);
    }

    return res.json();
}

// Employees
export const getEmployees = () => fetchApi<Employee[]>("/employees");
export const createEmployee = (data: Omit<Employee, "id">) =>
    fetchApi<Employee>("/employees", {
        method: "POST",
        body: JSON.stringify(data),
    });
export const deleteEmployee = (id: string) =>
    fetchApi<void>(`/employees/${id}`, { method: "DELETE" });

// Shifts
export const getShifts = () => fetchApi<Shift[]>("/shifts");
export const createShift = (data: Omit<Shift, "id">) =>
    fetchApi<Shift>("/shifts", { method: "POST", body: JSON.stringify(data) });
export const deleteShift = (id: string) =>
    fetchApi<void>(`/shifts/${id}`, { method: "DELETE" });

// Demands
export const getDemands = () => fetchApi<Demand[]>("/demands");
export const createDemand = (data: Omit<Demand, "id">) =>
    fetchApi<Demand>("/demands", {
        method: "POST",
        body: JSON.stringify(data),
    });
export const deleteDemand = (id: number) =>
    fetchApi<void>(`/demands/${id}`, { method: "DELETE" });

// Schedules
export const createSchedule = (data: ScheduleRequest) =>
    fetchApi<{ run_id: string; status: string }>("/schedules", {
        method: "POST",
        body: JSON.stringify(data),
    });
export const listSchedules = () => fetchApi<ScheduleSummary[]>("/schedules");
export const getScheduleResult = (runId: string) =>
    fetchApi<ScheduleResult>(`/schedules/${runId}`);

// Seed data
export const seedData = () =>
    fetchApi<{ message: string }>("/test/seed", { method: "POST" });
