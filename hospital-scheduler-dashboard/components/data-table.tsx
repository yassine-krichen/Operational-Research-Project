"use client"

import type React from "react"

import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Search, MoreHorizontal, Trash2, ChevronLeft, ChevronRight } from "lucide-react"

interface Column<T> {
  key: keyof T | string
  header: string
  render?: (item: T) => React.ReactNode
}

interface DataTableProps<T> {
  data: T[]
  columns: Column<T>[]
  searchKey?: keyof T
  onDelete?: (item: T) => void
  pageSize?: number
}

export function DataTable<T extends { id?: number | string }>({
  data,
  columns,
  searchKey,
  onDelete,
  pageSize = 10,
}: DataTableProps<T>) {
  const [search, setSearch] = useState("")
  const [page, setPage] = useState(0)

  const filteredData = searchKey
    ? data.filter((item) => String(item[searchKey]).toLowerCase().includes(search.toLowerCase()))
    : data

  const totalPages = Math.ceil(filteredData.length / pageSize)
  const paginatedData = filteredData.slice(page * pageSize, (page + 1) * pageSize)

  return (
    <div className="space-y-4">
      {searchKey && (
        <div className="relative max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value)
              setPage(0)
            }}
            className="pl-10"
          />
        </div>
      )}

      <div className="rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow>
              {columns.map((col) => (
                <TableHead key={String(col.key)}>{col.header}</TableHead>
              ))}
              {onDelete && <TableHead className="w-[50px]" />}
            </TableRow>
          </TableHeader>
          <TableBody>
            <AnimatePresence mode="popLayout">
              {paginatedData.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={columns.length + (onDelete ? 1 : 0)} className="h-24 text-center">
                    No results found.
                  </TableCell>
                </TableRow>
              ) : (
                paginatedData.map((item, idx) => (
                  <motion.tr
                    key={item.id || idx}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ delay: idx * 0.03 }}
                    className="border-b transition-colors hover:bg-muted/50"
                  >
                    {columns.map((col) => (
                      <TableCell key={String(col.key)}>
                        {col.render ? col.render(item) : String(item[col.key as keyof T] ?? "")}
                      </TableCell>
                    ))}
                    {onDelete && (
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="h-8 w-8">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem
                              className="text-destructive focus:text-destructive"
                              onClick={() => onDelete(item)}
                            >
                              <Trash2 className="mr-2 h-4 w-4" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    )}
                  </motion.tr>
                ))
              )}
            </AnimatePresence>
          </TableBody>
        </Table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Showing {page * pageSize + 1} to {Math.min((page + 1) * pageSize, filteredData.length)} of{" "}
            {filteredData.length} entries
          </p>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => setPage(page - 1)} disabled={page === 0}>
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <span className="text-sm">
              Page {page + 1} of {totalPages}
            </span>
            <Button variant="outline" size="sm" onClick={() => setPage(page + 1)} disabled={page >= totalPages - 1}>
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}

export { Badge }
