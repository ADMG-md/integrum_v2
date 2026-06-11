"use client"

import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import type { MotorGroup } from "@/components/consulta/results-viewer-metadata"
import { MOTOR_GROUP_ICONS, MOTOR_GROUP_LABELS } from "@/constants/motor-groups"

interface MotorMetadata {
  name: string
  group: string
  description?: string
  requirement_id?: string | null
  gated?: boolean
}

interface UseMotorGroupsReturn {
  groups: MotorGroup[]
  loading: boolean
  error: boolean
}

export function useMotorGroups(): UseMotorGroupsReturn {
  const { data: groups = [], isLoading: loading, isError: error } = useQuery({
    queryKey: ["motorGroups"],
    queryFn: async () => {
      const motors = await api.get<MotorMetadata[]>("/metadata/motors")
      const grouped: Record<string, string[]> = {}
      motors.forEach((m) => {
        const grp = m.group || "other"
        if (!grouped[grp]) grouped[grp] = []
        grouped[grp].push(m.name)
      })
      const result: MotorGroup[] = Object.entries(grouped).map(([key, motors]) => ({
        key,
        label: MOTOR_GROUP_LABELS[key] || key,
        icon: MOTOR_GROUP_ICONS[key] || MOTOR_GROUP_ICONS["other"],
        motors,
      }))
      return result
    },
    staleTime: 1000 * 60 * 60, // Cache for 1 hour since this rarely changes
  })

  return { groups, loading, error }
}
