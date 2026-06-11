"use client"

import { useEffect, useState } from "react"
import { useRouter, usePathname } from "next/navigation"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import {
  Users,
  Stethoscope,
  Brain,
  TrendingUp,
  LogOut,
  Activity,
  Workflow,
} from "lucide-react"

const roleNav: Record<string, { label: string; href: string; icon: React.ReactNode }[]> = {
  PHYSICIAN: [
    { label: "Pacientes", href: "/pacientes", icon: <Users className="h-4 w-4" /> },
    { label: "Flujo de Trabajo", href: "/workflow", icon: <Workflow className="h-4 w-4" /> },
    { label: "Consulta", href: "/consulta", icon: <Stethoscope className="h-4 w-4" /> },
    { label: "Seguimiento", href: "/seguimiento", icon: <TrendingUp className="h-4 w-4" /> },
  ],
  NUTRITION_PHYSICIAN: [
    { label: "Pacientes", href: "/pacientes", icon: <Users className="h-4 w-4" /> },
    { label: "Seguimiento", href: "/seguimiento", icon: <TrendingUp className="h-4 w-4" /> },
  ],
  PSYCHOLOGIST: [
    { label: "Pacientes", href: "/pacientes", icon: <Users className="h-4 w-4" /> },
    { label: "Psicología", href: "/psicologia", icon: <Brain className="h-4 w-4" /> },
  ],
  ADMINSTAFF: [
    { label: "Pacientes", href: "/pacientes", icon: <Users className="h-4 w-4" /> },
  ],
  PATIENT: [
    { label: "Mi Portal", href: "/portal", icon: <Activity className="h-4 w-4" /> },
  ],
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()
  const [role, setRole] = useState<string | null>(null)
  const [userName, setUserName] = useState<string | null>(null)

  useEffect(() => {
    const token = localStorage.getItem("token")
    const userRole = localStorage.getItem("role")
    if (!token) {
      router.push("/login")
      return
    }
    setRole(userRole)
    setUserName(localStorage.getItem("full_name"))
  }, [router])

  const handleLogout = () => {
    localStorage.removeItem("token")
    localStorage.removeItem("role")
    router.push("/login")
  }

  if (!role) return null

  const nav = roleNav[role] || roleNav["PHYSICIAN"]

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-64 bg-card border-r flex flex-col">
        <div className="p-6 border-b">
          <h1 className="text-xl font-bold text-primary">Integrum</h1>
          <p className="text-xs text-muted-foreground mt-1">
            {role === "PATIENT" ? "Portal del Paciente" : "Medicina de Precisión"}
          </p>
        </div>
        <nav className="flex-1 p-4 space-y-1">
          {nav.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                pathname === item.href || pathname?.startsWith(item.href + "/")
                  ? "bg-primary/10 text-primary font-medium"
                  : "text-muted-foreground hover:bg-accent hover:text-foreground"
              }`}
            >
              {item.icon}
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="p-4 border-t">
          {userName && (
            <div className="mb-4 flex items-center px-2 py-1.5 w-full bg-accent text-accent-foreground rounded-md text-sm truncate font-medium">
              <span className="w-full truncate">🧑‍⚕️ {userName}</span>
            </div>
          )}
          <Button variant="ghost" className="w-full justify-start gap-2" onClick={handleLogout}>
            <LogOut className="h-4 w-4" />
            Cerrar sesión
          </Button>
        </div>
      </aside>
      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <div className="p-6">{children}</div>
      </main>
    </div>
  )
}
