"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { format } from "date-fns";
import { DashboardLayout } from "@/components/dashboard-layout";
import { ScheduleCalendar } from "@/components/schedule-calendar";
import { CostChart } from "@/components/cost-chart";
import { WorkloadChart } from "@/components/workload-chart";
import { OptimizationLoader } from "@/components/optimization-loader";
import { ScheduleWizard } from "@/components/schedule-wizard";
import { Button } from "@/components/ui/button";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogTrigger } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import {
    Wand2,
    Calendar,
    BarChart3,
    Clock,
    CheckCircle,
    XCircle,
    Loader2,
} from "lucide-react";
import { mockEmployees } from "@/lib/mock-data";
import {
    createSchedule,
    getScheduleResult,
    listSchedules,
    type ScheduleRequest,
    type ScheduleResult,
    type ScheduleSummary,
} from "@/lib/api";
import { useApi } from "@/lib/use-api";

export default function SchedulesPage() {
    const [wizardOpen, setWizardOpen] = useState(false);
    const [isOptimizing, setIsOptimizing] = useState(false);
    const [schedules, setSchedules] = useState<ScheduleResult[]>([]);
    const [selectedSchedule, setSelectedSchedule] =
        useState<ScheduleResult | null>(null);
    const [pollRunId, setPollRunId] = useState<string | null>(null);

    // Load schedule history on mount
    useEffect(() => {
        const loadScheduleHistory = async () => {
            try {
                const summaries = await listSchedules();
                // Convert ScheduleSummary to ScheduleResult format
                const results: ScheduleResult[] = summaries.map((summary) => ({
                    run_id: summary.run_id,
                    status:
                        (summary.status as ScheduleResult["status"]) ||
                        "QUEUED",
                    objective_value: summary.objective_value,
                    created_at: summary.created_at,
                    completed_at: summary.completed_at,
                }));
                setSchedules(results);
                // Auto-select the first schedule
                if (results.length > 0) {
                    setSelectedSchedule(results[0]);
                }
            } catch (error) {
                console.error("Failed to load schedule history:", error);
            }
        };
        loadScheduleHistory();
    }, []);

    // Poll for currently running schedule
    const shouldPoll = pollRunId !== null;
    const { data: polledResult } = useApi<ScheduleResult | null>(
        shouldPoll ? `/schedules/${pollRunId}` : ""
    );

    useEffect(() => {
        if (polledResult) {
            // Update or add the schedule to the list
            setSchedules((prev) => {
                const existing = prev.findIndex(
                    (s) => s.run_id === polledResult.run_id
                );
                if (existing >= 0) {
                    const updated = [...prev];
                    updated[existing] = polledResult;
                    return updated;
                }
                return [polledResult, ...prev];
            });

            setSelectedSchedule(polledResult);

            if (
                polledResult.status === "OPTIMAL" ||
                polledResult.status === "FEASIBLE"
            ) {
                setIsOptimizing(false);
                setPollRunId(null);
                toast.success("Schedule generated successfully!", {
                    description: `Optimal solution found with total cost of $${polledResult.objective_value?.toLocaleString()}`,
                });
            } else if (
                polledResult.status === "ERROR" ||
                polledResult.status === "INFEASIBLE"
            ) {
                setIsOptimizing(false);
                setPollRunId(null);
                toast.error("Schedule generation failed", {
                    description:
                        polledResult.status === "ERROR"
                            ? "An error occurred during optimization"
                            : "No feasible solution exists",
                });
            }
        }
    }, [polledResult]);

    const handleGenerateSchedule = async (params: ScheduleRequest) => {
        setWizardOpen(false);
        setIsOptimizing(true);

        try {
            const response = await createSchedule(params);
            setPollRunId(response.run_id);
        } catch (error) {
            setIsOptimizing(false);
            toast.error("Failed to create schedule", {
                description:
                    error instanceof Error ? error.message : "Unknown error",
            });
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case "OPTIMAL":
            case "FEASIBLE":
                return <CheckCircle className="h-4 w-4 text-chart-2" />;
            case "RUNNING":
            case "QUEUED":
                return (
                    <Loader2 className="h-4 w-4 text-primary animate-spin" />
                );
            default:
                return <XCircle className="h-4 w-4 text-destructive" />;
        }
    };

    const getStatusBadge = (status: string) => {
        const variants: Record<
            string,
            "default" | "secondary" | "destructive" | "outline"
        > = {
            OPTIMAL: "default",
            FEASIBLE: "secondary",
            RUNNING: "outline",
            QUEUED: "outline",
            INFEASIBLE: "destructive",
            ERROR: "destructive",
        };
        return (
            <Badge variant={variants[status] || "secondary"}>{status}</Badge>
        );
    };

    return (
        <DashboardLayout>
            <div className="p-6 lg:p-8 space-y-6">
                <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight text-foreground">
                            Schedule Runs
                        </h1>
                        <p className="text-muted-foreground">
                            View and manage optimization results
                        </p>
                    </div>
                    <Dialog open={wizardOpen} onOpenChange={setWizardOpen}>
                        <DialogTrigger asChild>
                            <Button>
                                <Wand2 className="mr-2 h-4 w-4" />
                                New Schedule
                            </Button>
                        </DialogTrigger>
                        <DialogContent className="sm:max-w-lg p-0 gap-0">
                            <ScheduleWizard
                                onSubmit={handleGenerateSchedule}
                                onCancel={() => setWizardOpen(false)}
                            />
                        </DialogContent>
                    </Dialog>
                </div>

                {isOptimizing && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="py-8"
                    >
                        <OptimizationLoader />
                    </motion.div>
                )}

                {!isOptimizing && (
                    <div className="grid gap-6 lg:grid-cols-3">
                        {/* Schedule List */}
                        <Card className="lg:col-span-1">
                            <CardHeader>
                                <CardTitle>Schedule History</CardTitle>
                                <CardDescription>
                                    {schedules.length} runs
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-2">
                                {schedules.length === 0 ? (
                                    <div className="text-center py-8 text-muted-foreground">
                                        <Clock className="h-8 w-8 mx-auto mb-2 opacity-50" />
                                        <p>No schedules generated yet</p>
                                    </div>
                                ) : (
                                    schedules.map((schedule) => (
                                        <motion.button
                                            key={schedule.run_id}
                                            initial={{ opacity: 0, x: -10 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            onClick={async () => {
                                                try {
                                                    // Fetch full schedule details with assignments
                                                    const fullSchedule =
                                                        await getScheduleResult(
                                                            schedule.run_id
                                                        );
                                                    setSelectedSchedule(
                                                        fullSchedule
                                                    );
                                                } catch (error) {
                                                    console.error(
                                                        "Failed to load schedule details:",
                                                        error
                                                    );
                                                }
                                            }}
                                            className={`w-full flex items-center gap-3 p-3 rounded-lg border transition-colors text-left ${
                                                selectedSchedule?.run_id ===
                                                schedule.run_id
                                                    ? "border-primary bg-primary/5"
                                                    : "border-border hover:bg-muted/50"
                                            }`}
                                        >
                                            {getStatusIcon(schedule.status)}
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm font-medium truncate">
                                                    {schedule.run_id.slice(
                                                        0,
                                                        12
                                                    )}
                                                    ...
                                                </p>
                                                <p className="text-xs text-muted-foreground">
                                                    {schedule.created_at &&
                                                        format(
                                                            new Date(
                                                                schedule.created_at
                                                            ),
                                                            "MMM d, h:mm a"
                                                        )}
                                                </p>
                                            </div>
                                            {getStatusBadge(schedule.status)}
                                        </motion.button>
                                    ))
                                )}
                            </CardContent>
                        </Card>

                        {/* Schedule Details */}
                        <div className="lg:col-span-2 space-y-6">
                            {selectedSchedule ? (
                                <>
                                    <Card>
                                        <CardHeader className="flex flex-row items-center justify-between space-y-0">
                                            <div>
                                                <CardTitle>
                                                    Schedule Details
                                                </CardTitle>
                                                <CardDescription>
                                                    Run ID:{" "}
                                                    {selectedSchedule.run_id}
                                                </CardDescription>
                                            </div>
                                            <div className="flex items-center gap-3">
                                                {getStatusBadge(
                                                    selectedSchedule.status
                                                )}
                                                <div className="text-right">
                                                    <p className="text-2xl font-bold text-foreground">
                                                        $
                                                        {selectedSchedule.objective_value?.toLocaleString()}
                                                    </p>
                                                    <p className="text-sm text-muted-foreground">
                                                        Total Cost
                                                    </p>
                                                </div>
                                            </div>
                                        </CardHeader>
                                    </Card>

                                    <Tabs defaultValue="calendar">
                                        <TabsList>
                                            <TabsTrigger
                                                value="calendar"
                                                className="gap-2"
                                            >
                                                <Calendar className="h-4 w-4" />
                                                Calendar
                                            </TabsTrigger>
                                            <TabsTrigger
                                                value="analytics"
                                                className="gap-2"
                                            >
                                                <BarChart3 className="h-4 w-4" />
                                                Analytics
                                            </TabsTrigger>
                                        </TabsList>
                                        <TabsContent
                                            value="calendar"
                                            className="mt-4"
                                        >
                                            {selectedSchedule.assignments &&
                                            selectedSchedule.assignments
                                                .length > 0 ? (
                                                <ScheduleCalendar
                                                    assignments={
                                                        selectedSchedule.assignments
                                                    }
                                                    employees={mockEmployees}
                                                    startDate={(() => {
                                                        if (
                                                            selectedSchedule.assignments &&
                                                            selectedSchedule
                                                                .assignments
                                                                .length > 0
                                                        ) {
                                                            const dates =
                                                                selectedSchedule.assignments.map(
                                                                    (a) =>
                                                                        new Date(
                                                                            a.date
                                                                        ).getTime()
                                                                );
                                                            return new Date(
                                                                Math.min(
                                                                    ...dates
                                                                )
                                                            )
                                                                .toISOString()
                                                                .split("T")[0];
                                                        }
                                                        return "2025-12-01";
                                                    })()}
                                                    days={(() => {
                                                        if (
                                                            selectedSchedule.assignments &&
                                                            selectedSchedule
                                                                .assignments
                                                                .length > 0
                                                        ) {
                                                            const uniqueDates =
                                                                new Set(
                                                                    selectedSchedule.assignments.map(
                                                                        (a) =>
                                                                            a.date
                                                                    )
                                                                );
                                                            return uniqueDates.size;
                                                        }
                                                        return 7;
                                                    })()}
                                                />
                                            ) : (
                                                <Card>
                                                    <CardContent className="flex flex-col items-center justify-center py-12">
                                                        <Calendar className="h-8 w-8 text-muted-foreground mb-3" />
                                                        <p className="text-muted-foreground">
                                                            No assignments
                                                            available for this
                                                            schedule
                                                        </p>
                                                    </CardContent>
                                                </Card>
                                            )}
                                        </TabsContent>
                                        <TabsContent
                                            value="analytics"
                                            className="mt-4"
                                        >
                                            {selectedSchedule.assignments &&
                                            selectedSchedule.assignments
                                                .length > 0 ? (
                                                <div className="grid gap-6 lg:grid-cols-2">
                                                    <CostChart
                                                        assignments={
                                                            selectedSchedule.assignments
                                                        }
                                                    />
                                                    <WorkloadChart
                                                        assignments={
                                                            selectedSchedule.assignments
                                                        }
                                                        employees={
                                                            mockEmployees
                                                        }
                                                    />
                                                </div>
                                            ) : (
                                                <Card>
                                                    <CardContent className="flex flex-col items-center justify-center py-12">
                                                        <BarChart3 className="h-8 w-8 text-muted-foreground mb-3" />
                                                        <p className="text-muted-foreground">
                                                            No analytics data
                                                            available
                                                        </p>
                                                    </CardContent>
                                                </Card>
                                            )}
                                        </TabsContent>
                                    </Tabs>
                                </>
                            ) : (
                                <Card>
                                    <CardContent className="flex flex-col items-center justify-center py-16">
                                        <Calendar className="h-12 w-12 text-muted-foreground mb-4" />
                                        <h3 className="text-lg font-semibold text-foreground mb-2">
                                            No Schedule Selected
                                        </h3>
                                        <p className="text-muted-foreground text-center max-w-md mb-6">
                                            Generate a new schedule or select
                                            one from the history to view
                                            details.
                                        </p>
                                        <Button
                                            onClick={() => setWizardOpen(true)}
                                        >
                                            <Wand2 className="mr-2 h-4 w-4" />
                                            Generate New Schedule
                                        </Button>
                                    </CardContent>
                                </Card>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </DashboardLayout>
    );
}
