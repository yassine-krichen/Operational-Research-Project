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
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";
import { UserPlus } from "lucide-react";
import { mockEmployees } from "@/lib/mock-data";
import { createEmployee, deleteEmployee, type Employee } from "@/lib/api";
import { useApi } from "@/lib/use-api";

export default function EmployeesPage() {
    const { data: employeeData, mutate } = useApi<Employee[]>("/employees");
    const employees = employeeData || mockEmployees;
    const [dialogOpen, setDialogOpen] = useState(false);
    const [formData, setFormData] = useState({
        employee_id: "",
        name: "",
        role: "Nurse" as "Nurse" | "Doctor",
        skills: "",
        hourly_cost: 50,
        max_weekly_hours: 40,
    });

    const handleCreate = async () => {
        try {
            await createEmployee(formData);
            mutate();
            setDialogOpen(false);
            setFormData({
                employee_id: "",
                name: "",
                role: "Nurse",
                skills: "",
                hourly_cost: 50,
                max_weekly_hours: 40,
            });
            toast.success("Employee added successfully");
        } catch (error) {
            toast.error("Failed to add employee");
            console.error(error);
        }
    };

    const handleDelete = async (employee: Employee) => {
        try {
            await deleteEmployee(employee.employee_id);
            mutate();
            toast.success("Employee removed");
        } catch (error) {
            toast.error("Failed to delete employee");
            console.error(error);
        }
    };

    const columns = [
        { key: "employee_id", header: "ID" },
        { key: "name", header: "Name" },
        {
            key: "role",
            header: "Role",
            render: (emp: Employee) => (
                <Badge
                    variant={emp.role === "Doctor" ? "default" : "secondary"}
                >
                    {emp.role}
                </Badge>
            ),
        },
        {
            key: "skills",
            header: "Skills",
            render: (emp: Employee) => (
                <div className="flex flex-wrap gap-1">
                    {emp.skills.split("|").map((skill) => (
                        <Badge
                            key={skill}
                            variant="outline"
                            className="text-xs"
                        >
                            {skill}
                        </Badge>
                    ))}
                </div>
            ),
        },
        {
            key: "hourly_cost",
            header: "Hourly Cost",
            render: (emp: Employee) => `$${emp.hourly_cost}`,
        },
        {
            key: "max_weekly_hours",
            header: "Max Hours/Week",
            render: (emp: Employee) => `${emp.max_weekly_hours}h`,
        },
    ];

    return (
        <DashboardLayout>
            <div className="p-6 lg:p-8 space-y-6">
                <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight text-foreground">
                            Employees
                        </h1>
                        <p className="text-muted-foreground">
                            Manage doctors and nurses in your scheduling system
                        </p>
                    </div>
                    <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
                        <DialogTrigger asChild>
                            <Button>
                                <UserPlus className="mr-2 h-4 w-4" />
                                Add Employee
                            </Button>
                        </DialogTrigger>
                        <DialogContent>
                            <DialogHeader>
                                <DialogTitle>Add New Employee</DialogTitle>
                                <DialogDescription>
                                    Enter the details for the new staff member.
                                </DialogDescription>
                            </DialogHeader>
                            <div className="grid gap-4 py-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="employee_id">
                                            Employee ID
                                        </Label>
                                        <Input
                                            id="employee_id"
                                            value={formData.employee_id}
                                            onChange={(e) =>
                                                setFormData({
                                                    ...formData,
                                                    employee_id: e.target.value,
                                                })
                                            }
                                            placeholder="E01"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="role">Role</Label>
                                        <Select
                                            value={formData.role}
                                            onValueChange={(v) =>
                                                setFormData({
                                                    ...formData,
                                                    role: v as
                                                        | "Nurse"
                                                        | "Doctor",
                                                })
                                            }
                                        >
                                            <SelectTrigger>
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="Nurse">
                                                    Nurse
                                                </SelectItem>
                                                <SelectItem value="Doctor">
                                                    Doctor
                                                </SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="name">Full Name</Label>
                                    <Input
                                        id="name"
                                        value={formData.name}
                                        onChange={(e) =>
                                            setFormData({
                                                ...formData,
                                                name: e.target.value,
                                            })
                                        }
                                        placeholder="John Smith"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="skills">
                                        Skills (pipe-separated)
                                    </Label>
                                    <Input
                                        id="skills"
                                        value={formData.skills}
                                        onChange={(e) =>
                                            setFormData({
                                                ...formData,
                                                skills: e.target.value,
                                            })
                                        }
                                        placeholder="RN|ICU"
                                    />
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="hourly_cost">
                                            Hourly Cost ($)
                                        </Label>
                                        <Input
                                            id="hourly_cost"
                                            type="number"
                                            value={formData.hourly_cost}
                                            onChange={(e) =>
                                                setFormData({
                                                    ...formData,
                                                    hourly_cost: Number(
                                                        e.target.value
                                                    ),
                                                })
                                            }
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="max_weekly_hours">
                                            Max Weekly Hours
                                        </Label>
                                        <Input
                                            id="max_weekly_hours"
                                            type="number"
                                            value={formData.max_weekly_hours}
                                            onChange={(e) =>
                                                setFormData({
                                                    ...formData,
                                                    max_weekly_hours: Number(
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
                                    Add Employee
                                </Button>
                            </DialogFooter>
                        </DialogContent>
                    </Dialog>
                </div>

                <Card>
                    <CardHeader>
                        <CardTitle>Staff Directory</CardTitle>
                        <CardDescription>
                            {employees.length} employees registered
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <DataTable
                            data={employees}
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
