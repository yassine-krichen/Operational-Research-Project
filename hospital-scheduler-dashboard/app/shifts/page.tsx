"use client";

import { useState } from "react";
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
import { toast } from "sonner";
import { Clock } from "lucide-react";
import { mockShifts } from "@/lib/mock-data";
import { createShift, deleteShift, type Shift } from "@/lib/api";
import { useApi } from "@/lib/use-api";

const shiftColorMap: Record<string, string> = {
    S1: "bg-amber-100 text-amber-800",
    S2: "bg-sky-100 text-sky-800",
    S3: "bg-indigo-100 text-indigo-800",
};

export default function ShiftsPage() {
    const { data: shiftData, mutate } = useApi<Shift[]>("/shifts");
    const shifts = shiftData || mockShifts;
    const [dialogOpen, setDialogOpen] = useState(false);
    const [formData, setFormData] = useState({
        shift_id: "",
        name: "",
        start_time: "07:00",
        end_time: "15:00",
        length_hours: 8,
        shift_type: "day",
    });

    const handleCreate = async () => {
        try {
            await createShift(formData);
            mutate();
            setDialogOpen(false);
            setFormData({
                shift_id: "",
                name: "",
                start_time: "07:00",
                end_time: "15:00",
                length_hours: 8,
                shift_type: "day",
            });
            toast.success("Shift type added successfully");
        } catch (error) {
            toast.error("Failed to add shift");
            console.error(error);
        }
    };

    const handleDelete = async (shift: Shift) => {
        try {
            await deleteShift(shift.shift_id);
            mutate();
            toast.success("Shift type removed");
        } catch (error) {
            toast.error("Failed to delete shift");
            console.error(error);
        }
    };

    const columns = [
        { key: "shift_id", header: "Shift ID" },
        {
            key: "name",
            header: "Name",
            render: (shift: Shift) => (
                <Badge
                    className={
                        shiftColorMap[shift.shift_id] ||
                        "bg-muted text-muted-foreground"
                    }
                >
                    {shift.name}
                </Badge>
            ),
        },
        {
            key: "start_time",
            header: "Start Time",
            render: (shift: Shift) => shift.start_time,
        },
        {
            key: "end_time",
            header: "End Time",
            render: (shift: Shift) => shift.end_time,
        },
        {
            key: "length_hours",
            header: "Duration",
            render: (shift: Shift) => `${shift.length_hours} hours`,
        },
    ];

    return (
        <DashboardLayout>
            <div className="p-6 lg:p-8 space-y-6">
                <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight text-foreground">
                            Shifts
                        </h1>
                        <p className="text-muted-foreground">
                            Configure shift types and schedules
                        </p>
                    </div>
                    <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
                        <DialogTrigger asChild>
                            <Button>
                                <Clock className="mr-2 h-4 w-4" />
                                Add Shift Type
                            </Button>
                        </DialogTrigger>
                        <DialogContent>
                            <DialogHeader>
                                <DialogTitle>Add Shift Type</DialogTitle>
                                <DialogDescription>
                                    Define a new shift type for scheduling.
                                </DialogDescription>
                            </DialogHeader>
                            <div className="grid gap-4 py-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="shift_id">
                                            Shift ID
                                        </Label>
                                        <Input
                                            id="shift_id"
                                            value={formData.shift_id}
                                            onChange={(e) =>
                                                setFormData({
                                                    ...formData,
                                                    shift_id:
                                                        e.target.value.toUpperCase(),
                                                })
                                            }
                                            placeholder="S1"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="name">
                                            Display Name
                                        </Label>
                                        <Input
                                            id="name"
                                            value={formData.name}
                                            onChange={(e) =>
                                                setFormData({
                                                    ...formData,
                                                    name: e.target.value,
                                                })
                                            }
                                            placeholder="Morning Shift"
                                        />
                                    </div>
                                </div>
                                <div className="grid grid-cols-3 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="start_time">
                                            Start Time
                                        </Label>
                                        <Input
                                            id="start_time"
                                            type="time"
                                            value={formData.start_time}
                                            onChange={(e) =>
                                                setFormData({
                                                    ...formData,
                                                    start_time: e.target.value,
                                                })
                                            }
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="end_time">
                                            End Time
                                        </Label>
                                        <Input
                                            id="end_time"
                                            type="time"
                                            value={formData.end_time}
                                            onChange={(e) =>
                                                setFormData({
                                                    ...formData,
                                                    end_time: e.target.value,
                                                })
                                            }
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="length_hours">
                                            Duration (hrs)
                                        </Label>
                                        <Input
                                            id="length_hours"
                                            type="number"
                                            value={formData.length_hours}
                                            onChange={(e) =>
                                                setFormData({
                                                    ...formData,
                                                    length_hours: Number(
                                                        e.target.value
                                                    ),
                                                })
                                            }
                                        />
                                    </div>
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
                                    Add Shift
                                </Button>
                            </DialogFooter>
                        </DialogContent>
                    </Dialog>
                </div>

                <Card>
                    <CardHeader>
                        <CardTitle>Shift Types</CardTitle>
                        <CardDescription>
                            {shifts.length} shift types configured
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <DataTable
                            data={shifts}
                            columns={columns}
                            searchKey="name"
                            onDelete={handleDelete}
                        />
                    </CardContent>
                </Card>
            </div>
        </DashboardLayout>
    );
}
