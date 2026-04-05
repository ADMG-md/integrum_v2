# Integrum V2.5 — Repositorio Regulatorio SaMD
# Guía de Reproducción de Evidencia (IEC 62304 / ISO 14971)

Este documento describe la arquitectura técnica y el estado de cumplimiento del repositorio Integrum V2.5 para fines de auditoría y revisión científica.

---

## 1. Estado de Madurez (TRL 4)

Integrum V2.5 es un **prototipo funcional** probado en entorno controlado. No cuenta con certificación SaMD (Software as a Medical Device) ni ha sido auditado por terceros. La arquitectura ha sido diseñada con intención de cumplimiento de **Clase B**, pero el ciclo de vida (V&V, RMF, SOUP) se encuentra en fase de implementación inicial.

### Alcance de V&V (Golden Motors)
Actualmente, solo los motores **AcostaPhenotypeMotor** y **EOSSStagingMotor** cuentan con una suite de pruebas automatizadas y cobertura medida. Los 17 motores restantes se encuentran en fase de diseño y no deben interpretarse como validados.

---

## 2. Reproducción de Evidencia (V&V)

Para verificar los resultados de las pruebas unitarias y la cobertura de los motores de oro, ejecute el siguiente comando desde la raíz del proyecto:

```bash
make vv_golden_motors
```

Este comando:
1.  Ejecuta `pytest` sobre los motores Acosta y EOSS.
2.  Genera un reporte de cobertura en `docs/vv/engine_coverage_report_YYYYMMDD.txt`.
3.  Imprime los resultados por consola.

**Requisitos:** Python 3.9+, entorno virtual en `apps/backend/.venv` con `pytest` y `pytest-cov` instalados.

---

## 3. Mapa de Artefactos Regulatorios

| Artefacto | Ruta | Descripción |
|---|---|---|
| **RMF** | `docs/qms/risk_management_file.md` | ISO 14971 Hazard Analysis (Draft). |
| **SOUP** | `docs/qms/soup_manifest.md` | IEC 62304 §8.1.2 Inventario de Dependencias. |
| **Traceability** | `docs/qms/traceability_matrix.md` | Trazabilidad DOI -> Requisito -> Test. |
| **V&V Reports** | `docs/vv/` | Evidencia de ejecución de pruebas. |

---

## 4. Trazabilidad en Código

Los archivos de prueba en `apps/backend/tests/unit/engines/` contienen comentarios específicos de trazabilidad:
- `# Covers SR-ACO-01`: Vinculación directa con el Requisito Clínico en la Matrix de Trazabilidad.

---

**Revision:** 2026.03.29.C | **Integrum Clinical Data Factory**
