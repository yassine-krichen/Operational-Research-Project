"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    CardDescription,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import type { Assignment, Employee } from "@/lib/api";

interface ScheduleCalendarProps {
    assignments: Assignment[];
    employees: Employee[];
    startDate: string;
    days: number;
}

const shiftColors: Record<string, string> = {
    S1: "bg-amber-100 text-amber-800 border-amber-200 dark:bg-amber-900/30 dark:text-amber-200 dark:border-amber-800",
    S2: "bg-sky-100 text-sky-800 border-sky-200 dark:bg-sky-900/30 dark:text-sky-200 dark:border-sky-800",
    S3: "bg-indigo-100 text-indigo-800 border-indigo-200 dark:bg-indigo-900/30 dark:text-indigo-200 dark:border-indigo-800",
};

export function ScheduleCalendar({
    assignments,
    employees,
    startDate,
    days,
}: ScheduleCalendarProps) {
    const dates = useMemo(() => {
        const result: string[] = [];
        const start = new Date(startDate);
        for (let i = 0; i < days; i++) {
            const date = new Date(start);
            date.setDate(start.getDate() + i);
            result.push(date.toISOString().split("T")[0]);
        }
        return result;
    }, [startDate, days]);

    const assignmentMap = useMemo(() => {
        const map = new Map<string, Assignment[]>();
        assignments.forEach((a) => {
            const key = `${a.employee_id}-${a.date}`;
            if (!map.has(key)) map.set(key, []);
            map.get(key)!.push(a);
        });
        return map;
    }, [assignments]);

    const uniqueEmployees = useMemo(() => {
        const seen = new Set<string>();
        return assignments
            .filter((a) => {
                if (seen.has(a.employee_id)) return false;
                seen.add(a.employee_id);
                return true;
            })
            .map((a) => ({
                id: a.employee_id,
                name: a.employee_name,
                role: a.role,
            }))
            .sort(
                (a, b) =>
                    a.role.localeCompare(b.role) || a.name.localeCompare(b.name)
            );
    }, [assignments]);

    const formatDate = (dateStr: string) => {
        const date = new Date(dateStr);
        return {
            day: date.toLocaleDateString("en-US", { weekday: "short" }),
            date: date.getDate(),
            month: date.toLocaleDateString("en-US", { month: "short" }),
        };
    };

    return (
        <Card>
            <CardHeader>
                <CardTitle>Schedule Overview</CardTitle>
                <CardDescription>
                    Visual representation of staff assignments across the
                    scheduling period
                </CardDescription>
            </CardHeader>
            <CardContent>
                <ScrollArea className="w-full">
                    <div className="min-w-[800px]">
                        {/* Header row with dates */}
                        <div className="mb-4 flex">
                            <div className="w-48 shrink-0 pr-4">
                                <span className="text-sm font-medium text-muted-foreground">
                                    Employee
                                </span>
                            </div>
                            <div className="flex flex-1 gap-1">
                                {dates.map((date) => {
                                    const {
                                        day,
                                        date: d,
                                        month,
                                    } = formatDate(date);
                                    return (
                                        <div
                                            key={date}
                                            className="flex-1 min-w-[100px] text-center"
                                        >
                                            <p className="text-xs font-medium text-muted-foreground">
                                                {day}
                                            </p>
                                            <p className="text-lg font-bold text-foreground">
                                                {d}
                                            </p>
                                            <p className="text-xs text-muted-foreground">
                                                {month}
                                            </p>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>

                        {/* Employee rows */}
                        <div className="space-y-2">
                            {uniqueEmployees.map((employee, idx) => (
                                <motion.div
                                    key={employee.id}
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: idx * 0.05 }}
                                    className="flex items-center"
                                >
                                    <div className="w-48 shrink-0 pr-4">
                                        <p className="text-sm font-medium text-foreground truncate">
                                            {employee.name}
                                        </p>
                                        <Badge
                                            variant="secondary"
                                            className="text-xs"
                                        >
                                            {employee.role}
                                        </Badge>
                                    </div>
                                    <div className="flex flex-1 gap-1">
                                        {dates.map((date) => {
                                            const dayAssignments =
                                                assignmentMap.get(
                                                    `${employee.id}-${date}`
                                                ) || [];
                                            return (
                                                <div
                                                    key={date}
                                                    className="flex-1 min-w-[100px] min-h-[48px]"
                                                >
                                                    {dayAssignments.length >
                                                    0 ? (
                                                        <TooltipProvider>
                                                            {dayAssignments.map(
                                                                (
                                                                    assignment,
                                                                    i
                                                                ) => (
                                                                    <Tooltip
                                                                        key={i}
                                                                    >
                                                                        <TooltipTrigger
                                                                            asChild
                                                                        >
                                                                            <motion.div
                                                                                initial={{
                                                                                    scale: 0.8,
                                                                                    opacity: 0,
                                                                                }}
                                                                                animate={{
                                                                                    scale: 1,
                                                                                    opacity: 1,
                                                                                }}
                                                                                transition={{
                                                                                    delay:
                                                                                        idx *
                                                                                            0.05 +
                                                                                        i *
                                                                                            0.02,
                                                                                }}
                                                                                className={cn(
                                                                                    "rounded-md border px-2 py-1.5 text-xs font-medium cursor-pointer transition-transform hover:scale-105",
                                                                                    shiftColors[
                                                                                        assignment
                                                                                            .shift_id
                                                                                    ] ||
                                                                                        "bg-muted text-muted-foreground"
                                                                                )}
                                                                            >
                                                                                {
                                                                                    assignment.shift_name
                                                                                }
                                                                            </motion.div>
                                                                        </TooltipTrigger>
                                                                        <TooltipContent side="top">
                                                                            <div className="space-y-1 text-sm">
                                                                                <p className="font-medium">
                                                                                    {
                                                                                        assignment.shift_name
                                                                                    }{" "}
                                                                                    Shift
                                                                                </p>
                                                                                <p>
                                                                                    Hours:{" "}
                                                                                    {
                                                                                        assignment.hours
                                                                                    }
                                                                                    h
                                                                                </p>
                                                                                <p>
                                                                                    Cost:
                                                                                    $
                                                                                    {assignment.cost.toFixed(
                                                                                        2
                                                                                    )}
                                                                                </p>
                                                                            </div>
                                                                        </TooltipContent>
                                                                    </Tooltip>
                                                                )
                                                            )}
                                                        </TooltipProvider>
                                                    ) : (
                                                        <div className="h-full min-h-[48px] rounded-md border border-dashed border-border bg-muted/30" />
                                                    )}
                                                </div>
                                            );
                                        })}
                                    </div>
                                </motion.div>
                            ))}
                        </div>

                        {/* Legend */}
                        <div className="mt-6 flex items-center gap-4 border-t border-border pt-4">
                            <span className="text-sm font-medium text-muted-foreground">
                                Shifts:
                            </span>
                            {Object.entries(shiftColors).map(
                                ([shiftId, color]) => {
                                    const shiftNames: Record<string, string> = {
                                        S1: "Morning",
                                        S2: "Afternoon",
                                        S3: "Night",
                                    };
                                    return (
                                        <div
                                            key={shiftId}
                                            className="flex items-center gap-1.5"
                                        >
                                            <div
                                                className={cn(
                                                    "h-3 w-3 rounded",
                                                    color.split(" ")[0]
                                                )}
                                            />
                                            <span className="text-sm text-muted-foreground">
                                                {shiftNames[shiftId] || shiftId}
                                            </span>
                                        </div>
                                    );
                                }
                            )}
                        </div>
                    </div>
                    <ScrollBar orientation="horizontal" />
                </ScrollArea>
            </CardContent>
        </Card>
    );
}
