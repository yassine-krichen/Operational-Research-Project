"use client";

import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    CardDescription,
} from "@/components/ui/card";
import {
    PieChart,
    Pie,
    Cell,
    ResponsiveContainer,
    Legend,
    Tooltip,
} from "recharts";
import type { Assignment } from "@/lib/api";

interface CostChartProps {
    assignments: Assignment[];
}

export function CostChart({ assignments }: CostChartProps) {
    const costByRole = assignments.reduce((acc, a) => {
        acc[a.role] = (acc[a.role] || 0) + a.cost;
        return acc;
    }, {} as Record<string, number>);

    const data = Object.entries(costByRole).map(([role, cost]) => ({
        name: role,
        value: Math.round(cost * 100) / 100,
    }));

    const COLORS = ["#0d9488", "#0ea5e9", "#f59e0b", "#8b5cf6"];

    const total = data.reduce((sum, d) => sum + d.value, 0);

    return (
        <Card className="h-full">
            <CardHeader>
                <CardTitle>Cost Distribution</CardTitle>
                <CardDescription>Labor costs breakdown by role</CardDescription>
            </CardHeader>
            <CardContent>
                <div className="h-[280px]">
                    <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                            <Pie
                                data={data}
                                cx="50%"
                                cy="50%"
                                innerRadius={60}
                                outerRadius={100}
                                paddingAngle={2}
                                dataKey="value"
                                label={({ name, percent }) =>
                                    `${name} ${
                                        percent
                                            ? (percent * 100).toFixed(0)
                                            : "0"
                                    }%`
                                }
                                labelLine={false}
                            >
                                {data.map((_, index) => (
                                    <Cell
                                        key={`cell-${index}`}
                                        fill={COLORS[index % COLORS.length]}
                                    />
                                ))}
                            </Pie>
                            <Tooltip
                                formatter={(value: number) => [
                                    `$${value.toLocaleString()}`,
                                    "Cost",
                                ]}
                                contentStyle={{
                                    backgroundColor: "hsl(var(--card))",
                                    border: "1px solid hsl(var(--border))",
                                    borderRadius: "8px",
                                }}
                            />
                            <Legend />
                        </PieChart>
                    </ResponsiveContainer>
                </div>
                <div className="mt-4 text-center">
                    <p className="text-2xl font-bold text-foreground">
                        ${total.toLocaleString()}
                    </p>
                    <p className="text-sm text-muted-foreground">
                        Total Labor Cost
                    </p>
                </div>
            </CardContent>
        </Card>
    );
}
