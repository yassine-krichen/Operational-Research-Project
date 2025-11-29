"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { format, addDays } from "date-fns";
import {
    CalendarIcon,
    Wand2,
    Clock,
    AlertTriangle,
    ChevronRight,
    ChevronLeft,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Calendar } from "@/components/ui/calendar";
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover";
import { Slider } from "@/components/ui/slider";
import { cn } from "@/lib/utils";
import type { ScheduleRequest } from "@/lib/api";

interface ScheduleWizardProps {
    onSubmit: (data: ScheduleRequest) => void;
    onCancel: () => void;
}

export function ScheduleWizard({ onSubmit, onCancel }: ScheduleWizardProps) {
    const [step, setStep] = useState(0);
    const [startDate, setStartDate] = useState<Date>(new Date());
    const [horizonDays, setHorizonDays] = useState(7);
    const [solverTimeLimit, setSolverTimeLimit] = useState(60);
    const [allowUncovered, setAllowUncovered] = useState(true);
    const [penaltyUncovered, setPenaltyUncovered] = useState(1000);
    const [weightPreference, setWeightPreference] = useState(50);
    const [maxConsecutiveDays, setMaxConsecutiveDays] = useState(5);

    const steps = [
        {
            title: "Schedule Period",
            description: "Select the date range for the schedule",
        },
        {
            title: "Solver Settings",
            description: "Configure optimization parameters",
        },
        {
            title: "Review & Generate",
            description: "Confirm settings and start optimization",
        },
    ];

    const handleSubmit = () => {
        onSubmit({
            horizon_start: format(startDate, "yyyy-MM-dd"),
            horizon_days: horizonDays,
            solver_time_limit: solverTimeLimit,
            allow_uncovered_demand: allowUncovered,
            penalty_uncovered: penaltyUncovered,
            weight_preference: weightPreference,
            max_consecutive_days: maxConsecutiveDays,
        });
    };

    return (
        <Card className="w-full max-w-lg mx-auto">
            <CardHeader>
                <div className="flex items-center gap-2 mb-4">
                    {steps.map((_, idx) => (
                        <div key={idx} className="flex items-center">
                            <motion.div
                                className={cn(
                                    "flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium",
                                    idx <= step
                                        ? "bg-primary text-primary-foreground"
                                        : "bg-muted text-muted-foreground"
                                )}
                                animate={
                                    idx === step ? { scale: [1, 1.1, 1] } : {}
                                }
                                transition={{ duration: 0.5 }}
                            >
                                {idx + 1}
                            </motion.div>
                            {idx < steps.length - 1 && (
                                <div
                                    className={cn(
                                        "h-0.5 w-8",
                                        idx < step ? "bg-primary" : "bg-muted"
                                    )}
                                />
                            )}
                        </div>
                    ))}
                </div>
                <CardTitle>{steps[step].title}</CardTitle>
                <CardDescription>{steps[step].description}</CardDescription>
            </CardHeader>

            <CardContent className="min-h-[280px]">
                <AnimatePresence mode="wait">
                    {step === 0 && (
                        <motion.div
                            key="step-0"
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -20 }}
                            className="space-y-6"
                        >
                            <div className="space-y-2">
                                <Label>Start Date</Label>
                                <Popover>
                                    <PopoverTrigger asChild>
                                        <Button
                                            variant="outline"
                                            className="w-full justify-start text-left font-normal bg-transparent"
                                        >
                                            <CalendarIcon className="mr-2 h-4 w-4" />
                                            {format(startDate, "PPP")}
                                        </Button>
                                    </PopoverTrigger>
                                    <PopoverContent
                                        className="w-auto p-0"
                                        align="start"
                                    >
                                        <Calendar
                                            mode="single"
                                            selected={startDate}
                                            onSelect={(date) =>
                                                date && setStartDate(date)
                                            }
                                            initialFocus
                                        />
                                    </PopoverContent>
                                </Popover>
                            </div>

                            <div className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <Label>Schedule Duration</Label>
                                    <span className="text-sm font-medium text-foreground">
                                        {horizonDays} days
                                    </span>
                                </div>
                                <Slider
                                    value={[horizonDays]}
                                    onValueChange={([v]) => setHorizonDays(v)}
                                    min={1}
                                    max={28}
                                    step={1}
                                />
                                <p className="text-sm text-muted-foreground">
                                    Ends on{" "}
                                    {format(
                                        addDays(startDate, horizonDays - 1),
                                        "PPP"
                                    )}
                                </p>
                            </div>
                        </motion.div>
                    )}

                    {step === 1 && (
                        <motion.div
                            key="step-1"
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -20 }}
                            className="space-y-6"
                        >
                            <div className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <Label className="flex items-center gap-2">
                                        <Clock className="h-4 w-4" />
                                        Solver Time Limit
                                    </Label>
                                    <span className="text-sm font-medium text-foreground">
                                        {solverTimeLimit}s
                                    </span>
                                </div>
                                <Slider
                                    value={[solverTimeLimit]}
                                    onValueChange={([v]) =>
                                        setSolverTimeLimit(v)
                                    }
                                    min={10}
                                    max={300}
                                    step={10}
                                />
                            </div>

                            <div className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <Label>Max Consecutive Days</Label>
                                    <span className="text-sm font-medium text-foreground">
                                        {maxConsecutiveDays} days
                                    </span>
                                </div>
                                <Slider
                                    value={[maxConsecutiveDays]}
                                    onValueChange={([v]) =>
                                        setMaxConsecutiveDays(v)
                                    }
                                    min={1}
                                    max={14}
                                    step={1}
                                />
                            </div>

                            <div className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <Label>Preference Weight</Label>
                                    <span className="text-sm font-medium text-foreground">
                                        {weightPreference}
                                    </span>
                                </div>
                                <Slider
                                    value={[weightPreference]}
                                    onValueChange={([v]) =>
                                        setWeightPreference(v)
                                    }
                                    min={0}
                                    max={200}
                                    step={10}
                                />
                                <p className="text-xs text-muted-foreground">
                                    Penalty for ignoring employee preferences
                                </p>
                            </div>

                            <div className="flex items-center justify-between rounded-lg border p-4">
                                <div className="space-y-0.5">
                                    <Label className="flex items-center gap-2">
                                        <AlertTriangle className="h-4 w-4" />
                                        Allow Uncovered Demand
                                    </Label>
                                    <p className="text-sm text-muted-foreground">
                                        Permit solutions with unfilled shifts
                                    </p>
                                </div>
                                <Switch
                                    checked={allowUncovered}
                                    onCheckedChange={setAllowUncovered}
                                />
                            </div>

                            {allowUncovered && (
                                <motion.div
                                    initial={{ opacity: 0, height: 0 }}
                                    animate={{ opacity: 1, height: "auto" }}
                                    exit={{ opacity: 0, height: 0 }}
                                    className="space-y-2"
                                >
                                    <Label>Uncovered Demand Penalty</Label>
                                    <Input
                                        type="number"
                                        value={penaltyUncovered}
                                        onChange={(e) =>
                                            setPenaltyUncovered(
                                                Number(e.target.value)
                                            )
                                        }
                                    />
                                    <p className="text-sm text-muted-foreground">
                                        Cost added per unfilled shift position
                                    </p>
                                </motion.div>
                            )}
                        </motion.div>
                    )}

                    {step === 2 && (
                        <motion.div
                            key="step-2"
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -20 }}
                            className="space-y-4"
                        >
                            <div className="rounded-lg bg-muted p-4 space-y-3">
                                <div className="flex justify-between">
                                    <span className="text-sm text-muted-foreground">
                                        Start Date
                                    </span>
                                    <span className="text-sm font-medium">
                                        {format(startDate, "PPP")}
                                    </span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-sm text-muted-foreground">
                                        Duration
                                    </span>
                                    <span className="text-sm font-medium">
                                        {horizonDays} days
                                    </span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-sm text-muted-foreground">
                                        End Date
                                    </span>
                                    <span className="text-sm font-medium">
                                        {format(
                                            addDays(startDate, horizonDays - 1),
                                            "PPP"
                                        )}
                                    </span>
                                </div>
                                <div className="border-t border-border my-2" />
                                <div className="flex justify-between">
                                    <span className="text-sm text-muted-foreground">
                                        Solver Time Limit
                                    </span>
                                    <span className="text-sm font-medium">
                                        {solverTimeLimit} seconds
                                    </span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-sm text-muted-foreground">
                                        Max Consecutive
                                    </span>
                                    <span className="text-sm font-medium">
                                        {maxConsecutiveDays} days
                                    </span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-sm text-muted-foreground">
                                        Preference Weight
                                    </span>
                                    <span className="text-sm font-medium">
                                        {weightPreference}
                                    </span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-sm text-muted-foreground">
                                        Allow Uncovered
                                    </span>
                                    <span className="text-sm font-medium">
                                        {allowUncovered ? "Yes" : "No"}
                                    </span>
                                </div>
                                {allowUncovered && (
                                    <div className="flex justify-between">
                                        <span className="text-sm text-muted-foreground">
                                            Uncovered Penalty
                                        </span>
                                        <span className="text-sm font-medium">
                                            ${penaltyUncovered}
                                        </span>
                                    </div>
                                )}
                            </div>

                            <div className="rounded-lg border border-primary/20 bg-primary/5 p-4">
                                <div className="flex items-start gap-3">
                                    <Wand2 className="h-5 w-5 text-primary mt-0.5" />
                                    <div>
                                        <p className="text-sm font-medium text-foreground">
                                            Ready to optimize
                                        </p>
                                        <p className="text-sm text-muted-foreground">
                                            The Gurobi solver will find the
                                            optimal staff schedule minimizing
                                            labor costs while meeting all demand
                                            constraints.
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </CardContent>

            <CardFooter className="flex justify-between">
                <Button
                    variant="outline"
                    onClick={step === 0 ? onCancel : () => setStep(step - 1)}
                >
                    {step === 0 ? (
                        "Cancel"
                    ) : (
                        <>
                            <ChevronLeft className="mr-1 h-4 w-4" />
                            Back
                        </>
                    )}
                </Button>

                {step < 2 ? (
                    <Button onClick={() => setStep(step + 1)}>
                        Next
                        <ChevronRight className="ml-1 h-4 w-4" />
                    </Button>
                ) : (
                    <Button onClick={handleSubmit} className="gap-2">
                        <Wand2 className="h-4 w-4" />
                        Generate Schedule
                    </Button>
                )}
            </CardFooter>
        </Card>
    );
}
