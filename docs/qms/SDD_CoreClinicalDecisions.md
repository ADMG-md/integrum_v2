# Software Design Description (SDD)
## Core Clinical Decisions Architecture (Integrum V2)
**Status**: ACTIVE | **Version**: 1.0 | **Compliance Target**: IEC 62304 Class B, FDA CDS

---

## 1. Context & Purpose
Este documento especifica el diseño arquitectónico de la capa de decisiones clínicas nucleares de Integrum V2. Su objetivo es asegurar el desacoplamiento de la lógica matemática fenotípica (Ejes A, B, C) de la formulación de prescripciones (dieta, intervenciones conductuales, riesgos), garantizando trazabilidad, predictibilidad y transparencia médica bajo los lineamientos IEC 62304 y FDA CDS.

---

## 2. Diagrama de Arquitectura de Items

El siguiente diagrama detalla el flujo de datos desde los motores primarios hasta el motor de decisión, gobernado por un contrato inmutable (`DecisionContext`).

```mermaid
flowchart TD
    %% Motores Primarios
    A[ClinicalPhenotypeEngine\nAxis A] -->|AdjudicationResult| ORC
    B[BehavioralDomainEngine\nAxis B] -->|AdjudicationResult| ORC
    C[LongitudinalTrajectoryEngine\nAxis C] -->|AdjudicationResult| ORC
    
    %% Orquestador
    subgraph Orchestrator [EncounterOrchestrator]
        ORC(run_clinical_pipeline)
        ORC -->|Map & Validate| CTX[[DecisionContext]]
    end
    
    %% Motor Core
    CTX --> CCDE(CoreClinicalDecisionEngine)
    
    %% Salida
    subgraph Outputs [Clinical Outputs]
        CCDE -->|List[ClinicalRecommendation]| PR[(persistent_results)]
    end
    
    %% Safety Engine (Future)
    PR -.->|Pharmacotherapy\nRecommendations| SAF(PharmacotherapySafetyEngine)
    SAF -.->|Status override| PR
```

---

## 3. Interfaces Tipadas (APIs)

### 3.1 `DecisionContext` (Input Contract)
El `DecisionContext` actúa como un bus inmutable. El orquestador extrae métricas de los `AdjudicationResult` upstream y puebla propiedades booleanas fuertemente tipadas.

**Propiedades Base**:
- `axis_a_code`, `axis_b_code`, `axis_c_code`: Strings (Validados vs nulos y vacíos).
- `is_slow_burn`, `has_sarcopenic_risk`, `has_uncontrolled_eating`, `has_suboptimal_c`: Booleanos clínicos puros derivados de los motores primarios.
- `has_advanced_ckd`, `has_malnutrition_risk`: Restricciones externas.

**Banderas de Computabilidad**:
El contexto provee getters para gestionar la ausencia de datos:
- `can_compute_nutrition`: Requiere `axis_a_code`.
- `can_compute_behavioral`: Requiere `axis_b_code`.
- `can_compute_risk_rule`: Requiere Ejes A, B y C simultáneamente.

### 3.2 `ClinicalRecommendation` (Output Contract)
El `CoreClinicalDecisionEngine` *solo* devuelve objetos `ClinicalRecommendation`.

```python
class ClinicalRecommendation(BaseModel):
    recommendation_code: str
    domain: Literal["nutrition", "protein", "behavioral", "pharmacotherapy", "sleep", "risk"]
    recommendation_type: Literal["treatment", "referral", "sequencing", "alert"]
    requirement_id: str
    priority: Literal["standard", "high", "critical"]
    status: Literal["active", "suppressed", "modified", "informational"]
    depends_on: List[str]
    trigger_summary: List[str]
    human_readable_basis: str   # Obligatorio FDA CDS
    evidence_note: Optional[str]
    superseded_by: Optional[str]
    suppression_reason: Optional[str]
    audit_payload: Dict[str, Any]
```

---

## 4. Política de Datos Faltantes (Missingness Policy)

Integrum V2 no infiere información faltante ni aplica fallbacks "silenciosos". Aplica **degradación parcial por dominio**:

| Dominio | Inputs Requeridos | Condición si Falta | Comportamiento del Motor | Razón Transparente |
|---|---|---|---|---|
| Nutrición / Proteínas | `axis_a_code` | `!can_compute_nutrition` | Emite objeto `status="suppressed"` | "Faltan inputs del Eje A para calcular déficit o macronutrientes." |
| Conductual / Sueño | `axis_b_code` | `!can_compute_behavioral` | No se emiten recomendaciones | N/A (Se abstiene, la UI oculta el dominio de forma segura). |
| Fracaso Temprano | `axis_a_code`, `b`, `c`| `!can_compute_risk_rule`| Emite objeto `status="suppressed"` | "Se requieren Ejes A, B y C para emitir la alerta predictiva." |

---

## 5. UI Rendering & Transparencia (Cumplimiento FDA CDS)

Para cumplir con la norma de revisión independiente por el clínico (Human-in-the-Loop), la interfaz de usuario (Front-end) DEBE procesar los estados de las recomendaciones de la siguiente manera:

1. **`status == "active"`**: Renderizar con `recommendation_type` visual (badge), mostrar `human_readable_basis` claramente, y utilizar `audit_payload` para llenar widgets de prescripción.
2. **`status == "suppressed"`**: **NO OCULTAR**. Renderizar una tarjeta grisada o de advertencia que diga: "Recomendación Suprimida: `suppression_reason`". Esto empodera al clínico, explicándole explícitamente *por qué* el motor se abstuvo (ej. falta examen de laboratorio o falta clasificar Eje A).
3. **`status == "modified"`**: Mostrar la recomendación actual e indicar visualmente qué regla fue alterada (`superseded_by`) y por qué (`suppression_reason` ej. "ERC Avanzada modifica requerimiento proteico").

---

## 6. Ejemplos de Emisión vs Supresión

### 6.1 Happy Path: Proteína Alta por Riesgo Sarcopénico
```json
{
  "recommendation_code": "PROTEINA_ALTA",
  "domain": "protein",
  "recommendation_type": "treatment",
  "status": "active",
  "depends_on": ["SLOW_BURN", "SARCOPENIC_RISK"],
  "trigger_summary": ["Riesgo sarcopénico eleva requerimiento proteico"],
  "human_readable_basis": "Para sinergizar con el déficit calórico moderado y evitar pérdida de FFM, se prescribe un objetivo hiperproteico.",
  "audit_payload": {"protein_target_g_kg": "1.5-2.0"}
}
```

### 6.2 Override: ERC Avanzada Modifica Requerimiento Proteico
```json
{
  "recommendation_code": "PROTEINA_MODERADA_CKD",
  "domain": "protein",
  "recommendation_type": "treatment",
  "status": "modified",
  "superseded_by": "PROTEINA_MODERADA_CKD",
  "suppression_reason": "Enfermedad Renal Crónica Avanzada detectada",
  "trigger_summary": ["ERC avanzada inhibe proteína alta"],
  "human_readable_basis": "Paciente con ERC avanzada. La carga proteica debe ser ajustada a guías renales para evitar toxicidad urémica.",
  "audit_payload": {"protein_target_g_kg": "0.6-0.8"}
}
```

### 6.3 Missing Data: Ausencia de Eje A (Supresión Transparente)
```json
{
  "recommendation_code": "DEFICIT_INDETERMINADO",
  "domain": "nutrition",
  "recommendation_type": "treatment",
  "status": "suppressed",
  "suppression_reason": "Falta clasificación de fenotipo clínico (Eje A).",
  "trigger_summary": ["Falta de clasificación fenotípica (Eje A)"],
  "human_readable_basis": "Datos insuficientes del Eje A para calcular déficit calórico seguro.",
  "audit_payload": {}
}
```
