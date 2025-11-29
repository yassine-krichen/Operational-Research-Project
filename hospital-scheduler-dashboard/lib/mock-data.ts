import type { Employee, Shift, Demand, Assignment, ScheduleResult } from "./api"

export const mockEmployees: Employee[] = [
  {
    id: 1,
    employee_id: "EMP001",
    name: "Dr. Sarah Chen",
    role: "Doctor",
    skills: "MD|ICU|Emergency",
    hourly_cost: 150,
    max_weekly_hours: 40,
  },
  {
    id: 2,
    employee_id: "EMP002",
    name: "Dr. Michael Roberts",
    role: "Doctor",
    skills: "MD|Surgery",
    hourly_cost: 175,
    max_weekly_hours: 36,
  },
  {
    id: 3,
    employee_id: "EMP003",
    name: "Dr. Emily Watson",
    role: "Doctor",
    skills: "MD|Pediatrics",
    hourly_cost: 140,
    max_weekly_hours: 40,
  },
  {
    id: 4,
    employee_id: "EMP004",
    name: "Nurse James Wilson",
    role: "Nurse",
    skills: "RN|ICU",
    hourly_cost: 55,
    max_weekly_hours: 48,
  },
  {
    id: 5,
    employee_id: "EMP005",
    name: "Nurse Lisa Park",
    role: "Nurse",
    skills: "RN|Emergency",
    hourly_cost: 52,
    max_weekly_hours: 44,
  },
  {
    id: 6,
    employee_id: "EMP006",
    name: "Nurse David Kim",
    role: "Nurse",
    skills: "RN|Pediatrics",
    hourly_cost: 50,
    max_weekly_hours: 40,
  },
  {
    id: 7,
    employee_id: "EMP007",
    name: "Nurse Maria Garcia",
    role: "Nurse",
    skills: "RN|ICU|Emergency",
    hourly_cost: 58,
    max_weekly_hours: 48,
  },
  {
    id: 8,
    employee_id: "EMP008",
    name: "Dr. John Smith",
    role: "Doctor",
    skills: "MD|ICU",
    hourly_cost: 160,
    max_weekly_hours: 40,
  },
]

export const mockShifts: Shift[] = [
  { id: 1, shift_id: "MORNING", name: "Morning", start_time: "07:00", end_time: "15:00", length_hours: 8 },
  { id: 2, shift_id: "AFTERNOON", name: "Afternoon", start_time: "15:00", end_time: "23:00", length_hours: 8 },
  { id: 3, shift_id: "NIGHT", name: "Night", start_time: "23:00", end_time: "07:00", length_hours: 8 },
]

export const mockDemands: Demand[] = [
  { id: 1, date: "2025-12-01", shift_id: "MORNING", skill: "RN", required: 3 },
  { id: 2, date: "2025-12-01", shift_id: "MORNING", skill: "MD", required: 2 },
  { id: 3, date: "2025-12-01", shift_id: "AFTERNOON", skill: "RN", required: 2 },
  { id: 4, date: "2025-12-01", shift_id: "NIGHT", skill: "RN", required: 2 },
  { id: 5, date: "2025-12-02", shift_id: "MORNING", skill: "RN", required: 3 },
  { id: 6, date: "2025-12-02", shift_id: "MORNING", skill: "MD", required: 2 },
]

export const generateMockSchedule = (): ScheduleResult => {
  const dates = ["2025-12-01", "2025-12-02", "2025-12-03", "2025-12-04", "2025-12-05", "2025-12-06", "2025-12-07"]
  const shifts = ["MORNING", "AFTERNOON", "NIGHT"]
  const shiftNames: Record<string, string> = { MORNING: "Morning", AFTERNOON: "Afternoon", NIGHT: "Night" }

  const assignments: Assignment[] = []

  mockEmployees.forEach((emp) => {
    const numShifts = Math.floor(Math.random() * 4) + 3
    const assignedDates = new Set<string>()

    for (let i = 0; i < numShifts; i++) {
      const date = dates[Math.floor(Math.random() * dates.length)]
      if (!assignedDates.has(date)) {
        assignedDates.add(date)
        const shiftId = shifts[Math.floor(Math.random() * shifts.length)]
        assignments.push({
          employee_id: emp.employee_id,
          employee_name: emp.name,
          role: emp.role,
          date,
          shift_id: shiftId,
          shift_name: shiftNames[shiftId],
          hours: 8,
          cost: emp.hourly_cost * 8,
        })
      }
    }
  })

  return {
    run_id: "mock-run-" + Date.now(),
    status: "OPTIMAL",
    objective_value: assignments.reduce((sum, a) => sum + a.cost, 0),
    assignments: assignments.sort((a, b) => a.date.localeCompare(b.date)),
    logs: ["Solver started...", "Loading constraints...", "Optimizing schedule...", "Solution found: OPTIMAL"],
    created_at: new Date().toISOString(),
    completed_at: new Date().toISOString(),
  }
}
