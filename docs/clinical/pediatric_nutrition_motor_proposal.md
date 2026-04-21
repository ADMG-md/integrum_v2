# Propuesta: Motor de Recomendaciones Nutricionales Pediátricas

## Integrum V2 - Pediatric Nutritional Recommendation Engine

---

## 1. Alcance del Motor

Este motor está diseñado para recomendar intervenciones nutricionales específicas en tres poblaciones pediátricas:

1. **Obesidad pediátrica general** (2-18 años)
2. **Trastornos del espectro autista (TEA)** con obesidad o riesgo nutricional
3. **Trastorno por déficit de atención e hiperactividad (TDAH)** con alteraciones alimentarias

---

## 2. Evidencia Científica

### 2.1 Obesidad Pediátrica

| Guideline | Evidencia | Recomendación Principal |
|-----------|------------|-------------------------|
| **AAP 2023** | Hampl et al., Pediatrics 2023 | Intervención multimodal: nutricionales + actividad + comportamiento |
| **USPSTF 2024** | US Preventive Services Task Force | Screening + intervenciones multicomponente |
| **NCEP 2023** | National Cholesterol Education Program | Screening lipídico 9-11 años y 17-21 años |

**Recomendaciones clave:**
- Preferir intervenciones conductuales sobre farmacológicas
- Involucrar a toda la familia
- Evitar dietas restrictivas en menores de 12 años
- Priorizar educación alimentaria sobre restricción calórica

### 2.2 Trastornos del Espectro Autista (TEA)

| Estudio | Evidencia | Recomendación |
|---------|------------|---------------|
| Al-Beltagi 2024 | World J Clin Pediatr | Manejo nutricional integral en ASD |
| Adams et al. 2024 | ScienceDirect | Suplementación multivitamínica puede mejorar síntomas |
| Fraguas et al. 2019 | Pediatrics (UCSF) | Meta-análisis: dietas de eliminación no evidence-based |
| Frontiers 2022 | Systematic Review | Dietas sin gluten/caseína muestran beneficios moderados |

**Recomendaciones clave:**
- **Evitar** restricciones dietéticas sin supervisión (riesgo de deficiencias)
- **Priorizar** corrección de deficiencias de vitaminas/minerales
- **Evaluar** sensibilidad alimentaria antes de intervenciones
- **Omega-3** (DHA/EPA) puede reducir comportamientos repetitivos (evidencia moderada)
- **Suplementación multivitamínica** muestra mejoras en síntomas conductuales

### 2.3 Trastorno por Déficit de Atención e Hiperactividad (TDAH)

| Estudio | Evidencia | Recomendación |
|---------|------------|---------------|
| Rucklidge 2025 | Eur Child Adolesc Psychiatry | Micronutrientes mejoran síntomas de TDAH |
| MADDY Study 2025 | PubMed | Suplementos de micronutrientes efectivos independiente de calidad dietética |
| Pinto 2022 | PMC | Patrones alimentarios alterados en TDAH |
| Lange 2023 | Current Nutrition Reports | Nutrientes clave: omega-3, zinc, hierro, magnesio |

**Recomendaciones clave:**
- **Micronutrientes**: suplementación con multivitamínicos mejora síntomas
- **Omega-3**: DHA/EPA pueden mejorar atención (evidencia moderada)
- **Hierro**: corregir deficiencia si presente (común en TDAH)
- **Eliminar colorantes artificiales** puede reducir hiperactividad (controvertido)
- **Dieta mediterránea** asociada a menor riesgo TDAH

---

## 3. Estructura del Motor

### 3.1 Flujo de Decisión

```
┌─────────────────────────────────────────────────────────────┐
│                   PACIENTE PEDIÁTRICO                       │
│                    (edad 2-18 años)                         │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. CLASIFICACIÓN POR CONDICIÓN PRINCIPAL                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│  │ Obesidad│  │   TEA   │  │  TDAH   │  │  Otro   │       │
│  │ (BMI>85%)│  │ASD dx  │  │ADHD dx  │  │         │       │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘       │
│       │           │           │           │              │
│       ▼           ▼           ▼           ▼              │
│  ┌─────────────────────────────────────────────────┐    │
│  │ 2. EVALUACIÓN DE RIESGOS NUTRICIONALES          │    │
│  │ • Antropometría (peso, talla, BMI, circ. cintura  │    │
│  │ • Laboratorio (glucosa, perfil lipídico, Hb)       │    │
│  │ • Suplementos actuales                            │    │
│  │ • Patrón alimentario (FFQ simplificado)           │    │
│  └─────────────────────────────────────────────────┘    │
│                         │                                  │
│                         ▼                                  │
│  ┌─────────────────────────────────────────────────┐    │
│  │ 3. RECOMENDACIONES PERSONALIZADAS               │    │
│  │ • Calorías según edad/actividad                   │    │
│  │ • Distribución macronutrientes                   │    │
│  │ • Suplementos específicos                        │    │
│  │ • Frecuencia de monitoreo                         │    │
│  └─────────────────────────────────────────────────┘    │
│                         │                                  │
│                         ▼                                  │
│  ┌─────────────────────────────────────────────────┐    │
│  │ 4. PRIORIZACIÓN POR URGENCIA                    │    │
│  │ • High: Deficiencias agudas                      │    │
│  │ • Medium: Modificación conductual                 │    │
│  │ • Low: Optimización nutricional                  │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Reglas de Recomendación por Condición

#### A) Obesidad Pediátrica (sin comorbilidad neurodivergente)

```
IF edad >= 2 AND edad < 18 AND IMC_percentil >= 85 THEN:
    - Calorías: 80-100% de requerimiento según idade/sexo (no restricción)
    - Proteína: 1.0-1.2 g/kg/día (mínimo)
    - Actividad: 60 min/día moderada
    - Familia: intervención conductual
    - Monitoreo: antropometría trimestral
```

#### B) TEA con riesgo nutricional

```
IF diagnóstico TEA AND (
    (IMC_percentil >= 85) OR 
    (restrictive_food_patterns == true) OR
    (supplements == false)
) THEN:
    - Evaluar deficiencias: Vit D, Vit B12, Zinc, Hierro, Omega-3
    - Suplementación si deficiencia: 
        * Vit D: 400-600 UI/día (según edad)
        * Zinc: si niveles bajos
        * Omega-3: 500-1000mg DHA+EPA/día (si no consume pescado)
    - Evitar restricciones dietéticas sin supervisión
    - Preferir: patrones alimentarios regulares
```

#### C) TDAH con alteraciones alimentarias

```
IF diagnóstico TDAH AND (
    (eating_patterns == "irregular") OR
    (iron_level == "low") OR
    (omega3_level == "low")
) THEN:
    - Corregir deficiencias:
        * Hierro: suplementar si ferritina < 30 ng/mL
        * Zinc: mantener niveles normales
        * Omega-3: 500-1000mg EPA+DHA/día
    - Micronutrientes: multivitamínico pediátrico
    - Patrón: 3 comidas + 2 snacks regulares
    - Evitar: azúcares refinados en exceso
    - Evitar: colorantes artificiales (opcional)
```

---

## 4. Metadatos de Salida

```python
class PediatricNutritionRecommendation:
    """Output del PediatricNutritionMotor"""
    
    # Clasificación del paciente
    patient_category: Literal["obesity", "tea", "tdah", "typical"]
    age_group: Literal["toddler", "child", "adolescent"]
    
    # Recomendaciones
    caloric_target: Optional[int]  # kcal/día
    protein_grams_kg: Optional[float]  # g/kg/día
    
    # Suplementos sugeridos
    supplements: List[SupplementRecommendation]
    
    # Intervenciones
    interventions: List[NutritionIntervention]
    
    # Monitoreo
    monitoring_frequency: str  # "mensual", "trimestral", "semestral"
    next_lab_check: List[str]  # laboratorios a repetir
    
    # Evidencia
    evidence_sources: List[str]  # DOIs de guías
    confidence: float
```

---

## 5. Referencias Bibliográficas

### Obesidad Pediátrica
1. Hampl SE et al. Pediatrics. 2023;151(2):e2022060640 - AAP Clinical Practice Guideline
2. US Preventive Services Task Force. 2024 - Obesity in Children Interventions

### TEA
3. Al-Beltagi M et al. World J Clin Pediatr. 2024;13(4):99649 - Nutritional management in ASD
4. Adams JB et al. ScienceDirect. 2024 - Therapeutic diets in ASD
5. Fraguas D et al. Pediatrics. 2019;144(5) - Dietary Interventions for ASD Meta-analysis

### TDAH
6. Rucklidge JJ et al. Eur Child Adolesc Psychiatry. 2025 - Micronutrients in ADHD
7. Pinto S et al. Nutrients. 2022;14(20):4332 - Eating Patterns in ADHD
8. Lange KW et al. Curr Nutr Rep. 2023;12:383-394 - Nutrition in ADHD Management

---

## 6. Plan de Implementación

| Fase | Descripción | Entregable |
|------|-------------|------------|
| 1 | Diseño del motor | `pediatric_nutrition.py` |
| 2 | Reglas para obesidad | Tests T-PED-OB-01 a T-PED-OB-08 |
| 3 | Reglas para TEA | Tests T-PED-TEA-01 a T-PED-TEA-06 |
| 4 | Reglas para TDAH | Tests T-PED-TDAH-01 a T-PED-TDAH-06 |
| 5 | Validación y registry | 20+ tests,registry update |

---

## 7. Consideraciones de Seguridad

⚠️ **IMPORTANTE**: Este motor es un soporte a decisión médica, no reemplaza la evaluación del especialista.

- Siempre incluir "referir a nutrición pediátrica" en casos complejos
- No recomendar restricciones calóricas severas en menores de 12 años
- Suplementación solo bajo supervisión médica
- Considerar interacciones con medicamentos (ej: estimulantes en TDAH)

---

*Documento creado: 2026-04-08*
*Basado en: AAP 2023, USPSTF 2024, NCEP 2023, meta-análisis ASD 2019-2024, investigación TDAH 2022-2025*