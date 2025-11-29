"use client";

import { useState } from "react";
import { format } from "date-fns";
import { DashboardLayout } from "@/components/dashboard-layout";
import { DataTable, Badge } from "@/components/data-table";
import { Button } from "@/components/ui/button";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Calendar } from "@/components/ui/calendar";
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover";
import { toast } from "sonner";
import { CalendarIcon, ClipboardPlus } from "lucide-react";
import { mockDemands, mockShifts } from "@/lib/mock-data";
import { createDemand, deleteDemand, type Demand } from "@/lib/api";
import { useApi } from "@/lib/use-api";

export default function DemandsPage() {
    const { data: demandData, mutate } = useApi<Demand[]>("/demands");
    const demands = demandData || mockDemands;
    const [dialogOpen, setDialogOpen] = useState(false);
    const [selectedDate, setSelectedDate] = useState<Date>(new Date());
    const [formData, setFormData] = useState({
        shift_id: "S1",
        skill: "RN",
        required: 2,
    });

    const handleCreate = async () => {
        try {
            await createDemand({
                date: format(selectedDate, "yyyy-MM-dd"),
                shift_id: formData.shift_id,
                skill: formData.skill,
                required: formData.required,
            });
            mutate();
            setDialogOpen(false);
            setFormData({
                shift_id: "S1",
                skill: "RN",
                required: 2,
            });
            toast.success("Staffing demand added successfully");
        } catch (error) {
            toast.error("Failed to add demand");
            console.error(error);
        }
    };

    const handleDelete = async (demand: Demand) => {
        try {
            await deleteDemand(demand.id!);
            mutate();
            toast.success("Demand removed");
        } catch (error) {
            toast.error("Failed to delete demand");
            console.error(error);
        }
    };
    // helper method to change shift_id to shift name
    const getShiftName = (shift_id: string) => {
        const shiftNames: Record<string, string> = {
            S1: "Morning",
            S2: "Afternoon",
            S3: "Night",
        };
        return shiftNames[shift_id] || shift_id;
    };

    const columns = [
        {
            key: "date",
            header: "Date",
            render: (d: Demand) => format(new Date(d.date), "EEE, MMM d, yyyy"),
        },
        {
            key: "shift_id",
            header: "Shift",
            render: (d: Demand) => {
                const colors: Record<string, string> = {
                    S1: "bg-amber-100 text-amber-800",
                    S2: "bg-sky-100 text-sky-800",
                    S3: "bg-indigo-100 text-indigo-800",
                };
                return (
                    <Badge
                        className={
                            colors[d.shift_id] ||
                            "bg-muted text-muted-foreground"
                        }
                    >
                        {getShiftName(d.shift_id)}
                    </Badge>
                );
            },
        },
        {
            key: "skill",
            header: "Required Skill",
            render: (d: Demand) => <Badge variant="outline">{d.skill}</Badge>,
        },
        {
            key: "required",
            header: "Staff Needed",
            render: (d: Demand) => (
                <span className="font-medium">{d.required}</span>
            ),
        },
    ];

    return (
        <DashboardLayout>
            <div className="p-6 lg:p-8 space-y-6">
                <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight text-foreground">
                            Staffing Demands
                        </h1>
                        <p className="text-muted-foreground">
                            Define staffing requirements for each shift
                        </p>
                    </div>
                    <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
                        <DialogTrigger asChild>
                            <Button>
                                <ClipboardPlus className="mr-2 h-4 w-4" />
                                Add Demand
                            </Button>
                        </DialogTrigger>
                        <DialogContent>
                            <DialogHeader>
                                <DialogTitle>Add Staffing Demand</DialogTitle>
                                <DialogDescription>
                                    Specify staffing requirements for a specific
                                    shift.
                                </DialogDescription>
                            </DialogHeader>
                            <div className="grid gap-4 py-4">
                                <div className="space-y-2">
                                    <Label>Date</Label>
                                    <Popover>
                                        <PopoverTrigger asChild>
                                            <Button
                                                variant="outline"
                                                className="w-full justify-start text-left font-normal bg-transparent"
                                            >
                                                <CalendarIcon className="mr-2 h-4 w-4" />
                                                {format(selectedDate, "PPP")}
                                            </Button>
                                        </PopoverTrigger>
                                        <PopoverContent
                                            className="w-auto p-0"
                                            align="start"
                                        >
                                            <Calendar
                                                mode="single"
                                                selected={selectedDate}
                                                onSelect={(date) =>
                                                    date &&
                                                    setSelectedDate(date)
                                                }
                                                initialFocus
                                            />
                                        </PopoverContent>
                                    </Popover>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label>Shift</Label>
                                        <Select
                                            value={formData.shift_id}
                                            onValueChange={(v) =>
                                                setFormData({
                                                    ...formData,
                                                    shift_id: v,
                                                })
                                            }
                                        >
                                            <SelectTrigger>
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                {mockShifts.map((shift) => (
                                                    <SelectItem
                                                        key={shift.shift_id}
                                                        value={shift.shift_id}
                                                    >
                                                        {shift.name}
                                                    </SelectItem>
                                                ))}
                                            </SelectContent>
                                        </Select>
                                    </div>
                                    <div className="space-y-2">
                                        <Label>Required Skill</Label>
                                        <Select
                                            value={formData.skill}
                                            onValueChange={(v) =>
                                                setFormData({
                                                    ...formData,
                                                    skill: v,
                                                })
                                            }
                                        >
                                            <SelectTrigger>
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="RN">
                                                    RN (Registered Nurse)
                                                </SelectItem>
                                                <SelectItem value="MD">
                                                    MD (Medical Doctor)
                                                </SelectItem>
                                                <SelectItem value="ICU">
                                                    ICU Certified
                                                </SelectItem>
                                                <SelectItem value="Emergency">
                                                    Emergency
                                                </SelectItem>
                                                <SelectItem value="Surgery">
                                                    Surgery
                                                </SelectItem>
                                                <SelectItem value="Pediatrics">
                                                    Pediatrics
                                                </SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="required">
                                        Number of Staff Required
                                    </Label>
                                    <Input
                                        id="required"
                                        type="number"
                                        min={1}
                                        value={formData.required}
                                        onChange={(e) =>
                                            setFormData({
                                                ...formData,
                                                required: Number(
                                                    e.target.value
                                                ),
                                            })
                                        }
                                    />
                                </div>
                            </div>
                            <DialogFooter>
                                <Button
                                    variant="outline"
                                    onClick={() => setDialogOpen(false)}
                                >
                                    Cancel
                                </Button>
                                <Button onClick={handleCreate}>
                                    Add Demand
                                </Button>
                            </DialogFooter>
                        </DialogContent>
                    </Dialog>
                </div>

                <Card>
                    <CardHeader>
                        <CardTitle>Staffing Requirements</CardTitle>
                        <CardDescription>
                            {demands.length} demand entries
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <DataTable
                            data={demands}
                            columns={columns}
                            searchKey="skill"
                            onDelete={handleDelete}
                        />
                    </CardContent>
                </Card>
            </div>
        </DashboardLayout>
    );
}
