"use client"

import { useEffect, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Card, CardContent } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Activity, Cpu, Database, CheckCircle } from "lucide-react"

const stages = [
  { icon: Database, label: "Loading constraints...", duration: 2000 },
  { icon: Cpu, label: "Running optimization...", duration: 3000 },
  { icon: Activity, label: "Analyzing results...", duration: 1500 },
  { icon: CheckCircle, label: "Finalizing schedule...", duration: 1000 },
]

interface OptimizationLoaderProps {
  onComplete?: () => void
}

export function OptimizationLoader({ onComplete }: OptimizationLoaderProps) {
  const [currentStage, setCurrentStage] = useState(0)
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) return 100
        return prev + 1
      })
    }, 75)

    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (currentStage < stages.length - 1) {
      const timer = setTimeout(() => {
        setCurrentStage((prev) => prev + 1)
      }, stages[currentStage].duration)
      return () => clearTimeout(timer)
    } else if (progress >= 100 && onComplete) {
      const timer = setTimeout(onComplete, 500)
      return () => clearTimeout(timer)
    }
  }, [currentStage, progress, onComplete])

  const CurrentIcon = stages[currentStage].icon

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardContent className="p-8">
        <div className="flex flex-col items-center space-y-6">
          {/* Animated icon */}
          <div className="relative">
            <motion.div
              animate={{
                scale: [1, 1.1, 1],
                rotate: [0, 5, -5, 0],
              }}
              transition={{
                duration: 2,
                repeat: Number.POSITIVE_INFINITY,
                ease: "easeInOut",
              }}
              className="relative z-10"
            >
              <div className="flex h-20 w-20 items-center justify-center rounded-full bg-primary/10">
                <CurrentIcon className="h-10 w-10 text-primary" />
              </div>
            </motion.div>

            {/* Pulse rings */}
            <motion.div
              className="absolute inset-0 rounded-full border-2 border-primary/30"
              animate={{ scale: [1, 1.5], opacity: [0.5, 0] }}
              transition={{ duration: 1.5, repeat: Number.POSITIVE_INFINITY }}
            />
            <motion.div
              className="absolute inset-0 rounded-full border-2 border-primary/20"
              animate={{ scale: [1, 2], opacity: [0.3, 0] }}
              transition={{ duration: 1.5, repeat: Number.POSITIVE_INFINITY, delay: 0.3 }}
            />
          </div>

          {/* Status text */}
          <AnimatePresence mode="wait">
            <motion.p
              key={currentStage}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="text-lg font-medium text-foreground text-center"
            >
              {stages[currentStage].label}
            </motion.p>
          </AnimatePresence>

          {/* Progress bar */}
          <div className="w-full space-y-2">
            <Progress value={progress} className="h-2" />
            <p className="text-sm text-muted-foreground text-center">{progress}% complete</p>
          </div>

          {/* Stage indicators */}
          <div className="flex items-center gap-2">
            {stages.map((stage, idx) => (
              <motion.div
                key={idx}
                className={`h-2 w-2 rounded-full transition-colors ${idx <= currentStage ? "bg-primary" : "bg-muted"}`}
                animate={idx === currentStage ? { scale: [1, 1.3, 1] } : {}}
                transition={{ duration: 0.5, repeat: Number.POSITIVE_INFINITY }}
              />
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
