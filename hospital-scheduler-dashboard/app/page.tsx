"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { DashboardLayout } from "@/components/dashboard-layout";
import { StatCard } from "@/components/stat-card";
import { ScheduleWizard } from "@/components/schedule-wizard";
import { OptimizationLoader } from "@/components/optimization-loader";
import { ScheduleCalendar } from "@/components/schedule-calendar";
import { CostChart } from "@/components/cost-chart";
import { WorkloadChart } from "@/components/workload-chart";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogTrigger } from "@/components/ui/dialog";
import { toast } from "sonner";
import {
    Users,
    Clock,
    ClipboardList,
    DollarSign,
    Wand2,
    Database,
    CheckCircle,
    XCircle,
} from "lucide-react";
import { mockEmployees, mockShifts, mockDemands } from "@/lib/mock-data";
import {
    createSchedule,
    getScheduleResult,
    seedData,
    type ScheduleRequest,
    type ScheduleResult,
    type Employee,
} from "@/lib/api";
import { useApi } from "@/lib/use-api";

export default function DashboardPage() {
    const [wizardOpen, setWizardOpen] = useState(false);
    const [isOptimizing, setIsOptimizing] = useState(false);
    const [scheduleResult, setScheduleResult] = useState<ScheduleResult | null>(
        null
    );
    const [pollRunId, setPollRunId] = useState<string | null>(null);

    // Fetch real data from API
    const { data: employees } = useApi<Employee[]>("/employees");
    const { data: shifts } = useApi<typeof mockShifts>("/shifts");
    const { data: demands } = useApi<typeof mockDemands>("/demands");

    const employeeData = employees || mockEmployees;
    const shiftData = shifts || mockShifts;
    const demandData = demands || mockDemands;

    // Poll for schedule results
    const shouldPoll = pollRunId !== null;
    const { data: polledResult } = useApi<ScheduleResult | null>(
        shouldPoll ? `/schedules/${pollRunId}` : ""
    );

    // Update schedule result when polling completes
    useEffect(() => {
        if (polledResult) {
            setScheduleResult(polledResult);
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

    const handleSeedData = async () => {
        try {
            await seedData();
            toast.success("Sample data loaded successfully!");
            // Refresh data
            window.location.reload();
        } catch (error) {
            toast.error("Failed to seed data", {
                description:
                    error instanceof Error ? error.message : "Unknown error",
            });
        }
    };

    return (
        <DashboardLayout>
            <div className="p-6 lg:p-8 space-y-8">
                {/* Header */}
                <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight text-foreground">
                            Dashboard
                        </h1>
                        <p className="text-muted-foreground">
                            Hospital staff scheduling optimization powered by
                            Gurobi
                        </p>
                    </div>
                    <div className="flex items-center gap-3">
                        <Button variant="outline" onClick={handleSeedData}>
                            <Database className="mr-2 h-4 w-4" />
                            Seed Demo Data
                        </Button>
                        <Dialog open={wizardOpen} onOpenChange={setWizardOpen}>
                            <DialogTrigger asChild>
                                <Button>
                                    <Wand2 className="mr-2 h-4 w-4" />
                                    Generate Schedule
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
                </div>

                {/* Optimization Loader */}
                {isOptimizing && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="py-8"
                    >
                        <OptimizationLoader />
                    </motion.div>
                )}

                {/* Stats */}
                {!isOptimizing && (
                    <>
                        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                            <StatCard
                                title="Total Employees"
                                value={employeeData.length}
                                subtitle={`${
                                    employeeData.filter(
                                        (e: Employee) => e.role === "Doctor"
                                    ).length
                                } Doctors, ${
                                    employeeData.filter(
                                        (e: Employee) => e.role === "Nurse"
                                    ).length
                                } Nurses`}
                                icon={Users}
                                delay={0}
                            />
                            <StatCard
                                title="Active Shifts"
                                value={shiftData.length}
                                subtitle="Shift types configured"
                                icon={Clock}
                                delay={0.1}
                            />
                            <StatCard
                                title="Pending Demands"
                                value={demandData.length}
                                subtitle="Staffing requirements"
                                icon={ClipboardList}
                                delay={0.2}
                            />
                            <StatCard
                                title="Est. Weekly Cost"
                                value={
                                    scheduleResult
                                        ? `$${scheduleResult.objective_value?.toLocaleString()}`
                                        : "$--"
                                }
                                subtitle={
                                    scheduleResult
                                        ? "Optimized"
                                        : "No schedule generated"
                                }
                                icon={DollarSign}
                                delay={0.3}
                            />
                        </div>

                        {/* Schedule Result or Empty State */}
                        {scheduleResult ? (
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="space-y-6"
                            >
                                {/* Status Banner */}
                                <Card>
                                    <CardContent className="flex items-center justify-between p-4">
                                        <div className="flex items-center gap-3">
                                            {scheduleResult.status ===
                                            "OPTIMAL" ? (
                                                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-chart-2/10">
                                                    <CheckCircle className="h-5 w-5 text-chart-2" />
                                                </div>
                                            ) : (
                                                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-destructive/10">
                                                    <XCircle className="h-5 w-5 text-destructive" />
                                                </div>
                                            )}
                                            <div>
                                                <p className="font-medium text-foreground">
                                                    Schedule Generated
                                                    Successfully
                                                </p>
                                                <p className="text-sm text-muted-foreground">
                                                    Run ID:{" "}
                                                    {scheduleResult.run_id.slice(
                                                        0,
                                                        8
                                                    )}
                                                    ... | Status:{" "}
                                                    {scheduleResult.status}
                                                </p>
                                            </div>
                                        </div>
                                        <Badge
                                            variant={
                                                scheduleResult.status ===
                                                "OPTIMAL"
                                                    ? "default"
                                                    : "secondary"
                                            }
                                        >
                                            {scheduleResult.status}
                                        </Badge>
                                    </CardContent>
                                </Card>

                                {/* Calendar View */}
                                <ScheduleCalendar
                                    assignments={
                                        scheduleResult.assignments || []
                                    }
                                    employees={employeeData}
                                    startDate="2025-12-01"
                                    days={7}
                                />

                                {/* Charts */}
                                <div className="grid gap-6 lg:grid-cols-2">
                                    <CostChart
                                        assignments={
                                            scheduleResult.assignments || []
                                        }
                                    />
                                    <WorkloadChart
                                        assignments={
                                            scheduleResult.assignments || []
                                        }
                                        employees={employeeData}
                                    />
                                </div>
                            </motion.div>
                        ) : (
                            <Card>
                                <CardContent className="flex flex-col items-center justify-center py-16">
                                    <div className="rounded-full bg-muted p-4 mb-4">
                                        <Wand2 className="h-8 w-8 text-muted-foreground" />
                                    </div>
                                    <h3 className="text-lg font-semibold text-foreground mb-2">
                                        No Schedule Generated
                                    </h3>
                                    <p className="text-muted-foreground text-center max-w-md mb-6">
                                        Click the "Generate Schedule" button to
                                        run the Gurobi optimizer and create an
                                        optimal staff schedule based on your
                                        demands and constraints.
                                    </p>
                                    <Button onClick={() => setWizardOpen(true)}>
                                        <Wand2 className="mr-2 h-4 w-4" />
                                        Generate Your First Schedule
                                    </Button>
                                </CardContent>
                            </Card>
                        )}
                    </>
                )}
            </div>
        </DashboardLayout>
    );
}
