# Plan de Acción: Optimización de Integrum V2 (CDSS SaMD Clase B)

Este plan de acción ha sido redactado tras analizar la estructura del repositorio, los reportes de seguridad y los resultados de las pruebas unitarias. Se proponen los **primeros 3 pasos lógicos** y las **librerías de Python recomendadas** para optimizar el rendimiento, la seguridad y el cumplimiento normativo (IEC 62304) de la aplicación.

---

## 📋 Resumen del Estado Actual

Integrum V2 es un sistema de soporte a decisiones clínicas (CDSS) para obesidad y salud cardiometabólica clasificado como **SaMD Clase B** (Software as a Medical Device). Su arquitectura está bien estructurada siguiendo los principios de **Clean Architecture** (motores puros e independientes del framework y la base de datos). 

Sin embargo, el análisis técnico revela tres áreas críticas de mejora:
1. **Seguridad y Vulnerabilidades:** Múltiples dependencias críticas en [security_vuln_report.txt](file:///Users/antonymolinagarrido/projects/integrum_v2/apps/backend/security_vuln_report.txt) tienen vulnerabilidades conocidas (path traversal, RCE, side-channel attacks).
2. **Desempeño del specialty_runner:** Ejecución secuencial de más de 40 motores clínicos por encuentro, lo cual se convierte en un cuello de botella CPU-bound.
3. **Acceso y Persistencia de Datos:** Carga ineficiente de relaciones complejas en el modelo [Encounter](file:///Users/antonymolinagarrido/projects/integrum_v2/apps/backend/src/domain/models.py) y falta de una capa de almacenamiento en caché para datos cuasi-estáticos (como guías clínicas e ICD-10).

---

## 🚀 Los 3 Primeros Pasos Lógicos

### Paso 1: Hardening de Dependencias y Mitigación de Seguridad
* **Objetivo:** Garantizar el cumplimiento de la norma **IEC 62304 §5.1.2 (Seguridad del Software)** resolviendo vulnerabilidades críticas de las librerías base.
* **Acciones:**
  1. Actualizar las dependencias vulnerables en [pyproject.toml](file:///Users/antonymolinagarrido/projects/integrum_v2/apps/backend/pyproject.toml):
     - `setuptools` a `>=78.1.1` (o eliminar de runtime).
     - `python-multipart` a `>=0.0.22` (para resolver Path Traversal).
     - `filelock` a `>=3.20.3` (para resolver TOCTOU).
  2. Sustituir `ecdsa` (vulnerable a ataques de canal lateral/Minerva) por una librería criptográfica estándar que utilice primitivas en tiempo constante implementadas en C (como OpenSSL).
  3. Reemplazar cualquier esquema de validación remanente basado en `marshmallow` (vulnerable a DoS por clonación profunda de errores) por `pydantic` V2, el cual ya está completamente integrado en el proyecto.
* **Librerías Recomendadas:**
  - [cryptography](https://cryptography.io/): Para operaciones criptográficas robustas y resistentes a ataques de canal lateral.
  - [pydantic](https://docs.pydantic.dev/): Para una serialización/validación de alto rendimiento escrita en Rust, eliminando el uso de `marshmallow`.

### Paso 2: Optimización de Ejecución de Motores Clínicos (Paralelización)
* **Objetivo:** Reducir la latencia de respuesta del endpoint de análisis de encuentros mediante la paralelización de la fase de motores primarios independientes.
* **Acciones:**
  1. Modificar [SpecialtyRunner.run_all](file:///Users/antonymolinagarrido/projects/integrum_v2/apps/backend/src/engines/specialty_runner.py) para ejecutar de manera paralela los motores clínicos primarios (`PRIMARY_MOTORS`) que no tengan dependencias entre sí.
  2. Dado que los motores son puros y CPU-bound, utilizar un pool de hilos (`ThreadPoolExecutor`) o multiprocesamiento (`ProcessPoolExecutor`) si el costo de serialización no es excesivo. Para flujos de trabajo asíncronos futuros, usar `asyncio.gather`.
  3. Integrar herramientas de perfilado de código específicas en el entorno de desarrollo para identificar cuáles motores consumen más tiempo de CPU.
* **Librerías Recomendadas:**
  - `concurrent.futures` (Parte de la biblioteca estándar de Python): Para administrar pools de hilos o procesos sin complejidad añadida.
  - [pyinstrument](https://github.com/joerick/pyinstrument): Un perfilador de llamadas de bajo impacto ideal para aplicaciones web de FastAPI.
  - [numpy](https://numpy.org/) / [numba](https://numba.pydata.org/): Si algún motor clínico realiza cálculos iterativos pesados o vectorizados en matrices grandes de datos.

### Paso 3: Optimización del Acceso a Datos y Capa de Caché/Redis
* **Objetivo:** Optimizar las consultas a la base de datos PostgreSQL utilizando SQLAlchemy async y reducir la carga mediante caché de lectura para reglas clínicas estáticas.
* **Acciones:**
  1. Ajustar el pool de conexiones en [src/database.py](file:///Users/antonymolinagarrido/projects/integrum_v2/apps/backend/src/database.py) para manejar de forma óptima la concurrencia en producción.
  2. Evitar el problema de consultas N+1 en SQLAlchemy mediante el uso explícito de estrategias de carga (`selectinload` o `joinedload`) al recuperar la entidad agregada `EncounterModel` con todas sus colecciones (`observations`, `conditions`, `medications`).
  3. Configurar Redis (ya disponible en el ecosistema del proyecto) para almacenar en caché las respuestas de reglas cuasi-estáticas como las de `ClinicalGuidelinesMotor` e información de catálogos médicos.
* **Librerías Recomendadas:**
  - [redis-py](https://redis-py.readthedocs.io/): Conector asíncrono optimizado para Redis (usando `hiredis` para máxima velocidad).
  - [aiocache](https://github.com/aio-libs/aiocache): Librería para implementar almacenamiento en caché asíncrono multiproveedor (Redis/Memcached/Memory) mediante decoradores simples en FastAPI.

---

## 🛠️ Resumen de Librerías Recomendadas

| Librería | Propósito | Categoría | Beneficio en Integrum V2 |
| :--- | :--- | :--- | :--- |
| **`cryptography`** | Seguridad Criptográfica | Seguridad | Reemplaza `ecdsa` con primitivas criptográficas robustas y side-channel resistant. |
| **`pydantic>=2.12.0`** | Validación y Schemas | Rendimiento | Elimina el riesgo de DoS de `marshmallow` e incrementa la velocidad de parseo. |
| **`aiocache`** | Caché Asíncrono | Rendimiento | Facilita la adición de caché con Redis para endpoints pesados de solo lectura. |
| **`pyinstrument`** | Perfilado de Código | Herramienta Dev | Permite diagnosticar con precisión qué motores o funciones ralentizan el pipeline. |
| **`numba`** / **`numpy`** | Compilación Just-in-Time | Rendimiento | Optimiza ecuaciones clínicas complejas compilándolas a código de máquina. |
| **`uv`** | Package Manager | Devops | Acelera la instalación de dependencias y la generación de locks deterministas. |
