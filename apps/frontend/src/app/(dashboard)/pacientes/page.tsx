"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { api } from "@/lib/api"
import { Patient } from "@/types"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input, Label } from "@/components/ui/form"
import { Plus, Search, Stethoscope, Calendar } from "lucide-react"
import Link from "next/link"

export default function PacientesPage() {
  const [patients, setPatients] = useState<Patient[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState("")
  const [showCreate, setShowCreate] = useState(false)
  const [newPatient, setNewPatient] = useState({
    external_id: "",
    full_name: "",
    date_of_birth: "",
    gender: "",
    email: "",
    phone: "",
  })
  const router = useRouter()

  useEffect(() => {
    api.get<Patient[]>("/patients/")
      .then(setPatients)
      .catch(() => setPatients([]))
      .finally(() => setLoading(false))
  }, [])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const created = await api.post<Patient>("/patients/", newPatient)
      setPatients((prev) => [created, ...prev])
      setShowCreate(false)
      setNewPatient({ external_id: "", full_name: "", date_of_birth: "", gender: "", email: "", phone: "" })
    } catch {
      alert("Error creando paciente")
    }
  }

  const filtered = patients.filter(
    (p) =>
      p.full_name.toLowerCase().includes(search.toLowerCase()) ||
      p.external_id.toLowerCase().includes(search.toLowerCase()) ||
      (p.email || "").toLowerCase().includes(search.toLowerCase()),
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Pacientes</h2>
          <p className="text-muted-foreground">Gestión de pacientes y registros clínicos</p>
        </div>
        <Button onClick={() => setShowCreate(!showCreate)}>
          <Plus className="h-4 w-4 mr-2" />
          Nuevo paciente
        </Button>
      </div>

      {showCreate && (
        <Card>
          <CardHeader>
            <CardTitle>Registrar paciente</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>ID externo</Label>
                <Input
                  value={newPatient.external_id}
                  onChange={(e) => setNewPatient({ ...newPatient, external_id: e.target.value })}
                  placeholder="CC-12345678"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label>Nombre completo</Label>
                <Input
                  value={newPatient.full_name}
                  onChange={(e) => setNewPatient({ ...newPatient, full_name: e.target.value })}
                  placeholder="María García"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label>Fecha de nacimiento</Label>
                <Input
                  type="date"
                  value={newPatient.date_of_birth}
                  onChange={(e) => setNewPatient({ ...newPatient, date_of_birth: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>Género</Label>
                <select
                  className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm"
                  value={newPatient.gender}
                  onChange={(e) => setNewPatient({ ...newPatient, gender: e.target.value })}
                >
                  <option value="">Seleccionar</option>
                  <option value="male">Masculino</option>
                  <option value="female">Femenino</option>
                  <option value="other">Otro</option>
                </select>
              </div>
              <div className="space-y-2">
                <Label>Email</Label>
                <Input
                  type="email"
                  value={newPatient.email}
                  onChange={(e) => setNewPatient({ ...newPatient, email: e.target.value })}
                  placeholder="paciente@email.com"
                />
              </div>
              <div className="space-y-2">
                <Label>Teléfono</Label>
                <Input
                  value={newPatient.phone}
                  onChange={(e) => setNewPatient({ ...newPatient, phone: e.target.value })}
                  placeholder="+57 300 123 4567"
                />
              </div>
              <div className="col-span-2 flex gap-2">
                <Button type="submit">Crear paciente</Button>
                <Button type="button" variant="outline" onClick={() => setShowCreate(false)}>
                  Cancelar
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          className="pl-10"
          placeholder="Buscar por nombre, ID o email..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {loading ? (
        <p className="text-muted-foreground text-center py-8">Cargando pacientes...</p>
      ) : filtered.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            No se encontraron pacientes
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-3">
          {filtered.map((patient) => (
            <Card key={patient.id} className="hover:border-primary/50 transition-colors">
              <CardContent className="flex items-center justify-between p-4">
                <div>
                  <p className="font-medium">{patient.full_name}</p>
                  <p className="text-sm text-muted-foreground">
                    ID: {patient.external_id}
                    {patient.email && ` · ${patient.email}`}
                  </p>
                </div>
                <div className="flex gap-2">
                  <Link href={`/consulta/${patient.id}`}>
                    <Button size="sm" variant="outline">
                      <Stethoscope className="h-4 w-4 mr-1" />
                      Consulta
                    </Button>
                  </Link>
                  <Link href={`/seguimiento/${patient.id}`}>
                    <Button size="sm" variant="ghost">
                      <Calendar className="h-4 w-4 mr-1" />
                      Historial
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
