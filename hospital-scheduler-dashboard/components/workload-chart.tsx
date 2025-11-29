"use client"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Cell } from "recharts"
import type { Assignment, Employee } from "@/lib/api"

interface WorkloadChartProps {
  assignments: Assignment[]
  employees: Employee[]
}

export function WorkloadChart({ assignments, employees }: WorkloadChartProps) {
  const hoursByEmployee = assignments.reduce(
    (acc, a) => {
      acc[a.employee_id] = (acc[a.employee_id] || 0) + a.hours
      return acc
    },
    {} as Record<string, number>,
  )

  const employeeMap = new Map(employees.map((e) => [e.employee_id, e]))

  const data = Object.entries(hoursByEmployee)
    .map(([employeeId, hours]) => {
      const emp = employeeMap.get(employeeId)
      const assignment = assignments.find((a) => a.employee_id === employeeId)
      return {
        name: assignment?.employee_name?.split(" ").slice(-1)[0] || employeeId,
        fullName: assignment?.employee_name || employeeId,
        hours,
        maxHours: emp?.max_weekly_hours || 40,
        role: assignment?.role || "Unknown",
      }
    })
    .sort((a, b) => b.hours - a.hours)

  const maxWeeklyHours = Math.max(...data.map((d) => d.maxHours), 40)

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Workload Distribution</CardTitle>
        <CardDescription>Hours assigned per employee with max hour constraints</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} layout="vertical" margin={{ left: 20, right: 30 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
              <XAxis type="number" domain={[0, maxWeeklyHours + 10]} tickLine={false} axisLine={false} />
              <YAxis type="category" dataKey="name" width={80} tickLine={false} axisLine={false} />
              <Tooltip
                formatter={(
                  value: number,
                  name: string,
                  props: { payload: { fullName: string; role: string; maxHours: number } },
                ) => {
                  return [`${value}h / ${props.payload.maxHours}h max`, props.payload.fullName]
                }}
                contentStyle={{
                  backgroundColor: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "8px",
                }}
              />
              <ReferenceLine
                x={40}
                stroke="hsl(var(--destructive))"
                strokeDasharray="5 5"
                label={{ value: "Target Max", position: "top", fill: "hsl(var(--muted-foreground))" }}
              />
              <Bar dataKey="hours" radius={[0, 4, 4, 0]}>
                {data.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.hours > entry.maxHours ? "#ef4444" : entry.role === "Doctor" ? "#0d9488" : "#0ea5e9"}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-4 flex items-center justify-center gap-6">
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded bg-primary" />
            <span className="text-sm text-muted-foreground">Doctor</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded bg-sky-500" />
            <span className="text-sm text-muted-foreground">Nurse</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded bg-destructive" />
            <span className="text-sm text-muted-foreground">Over Max</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
