# Synapxion Monorepo Overview

Este **README.md** documenta la estructura, los proyectos y las responsabilidades del equipo Synapxion. Contiene la jerarquía del equipo, la ubicación de cada proyecto en los repositorios `synapxion/synapxion-{tipo}`, y guías prácticas para desarrollo, pruebas y despliegue.

---

## Repositorios y Mapeo de Proyectos

| **Repositorio**           | **Tipo** | **Proyecto principal**     | **Descripción corta**                     |
| ------------------------- | -------- | -------------------------- | ----------------------------------------- |
| synapxion/synapxion-app   | app      | Aplicación UI (Godot + C#) | Interfaz principal empaquetada para venta |
| synapxion/synapxion-train | train    | Entrenador NLP (PyTorch)   | Entrenamiento y scripts de modelos NLP    |
| synapxion/synapxion-site  | site     | Sitio web (Vue + Vite)     | Portal público y panel de documentación   |
| synapxion/synapxion-pack  | pack     | Instalador y empaquetado   | Creación de instaladores multiplataforma  |
| synapxion/synapxion-utils | utils    | Utilidades compartidas     | Librerías, scripts y herramientas comunes |

---

## Equipo y Roles

| **Nombre**   | **Rol principal** | **Responsabilidades clave**                                      |
| ------------ | ----------------- | ---------------------------------------------------------------- |
| **Jaime**    | Tester            | Pruebas funcionales; pruebas de regresión; reporte de bugs       |
| **Norberto** | Tester            | Automatización de pruebas; integración continua; QA final        |
| **Sara**     | Diseño y Frontend | Diseño UI/UX; implementación de componentes frontend             |
| **Sofia**    | Diseño y Frontend | Prototipos visuales; implementación de estilos y accesibilidad   |
| **Rodolfo**  | Backend           | APIs; integración con modelo; despliegue y mantenimiento backend |

### Notas sobre colaboración

* Jaime y Norberto cubren QA en todos los repositorios.
* Sara y Sofia lideran diseño y frontend tanto para el sitio como para la UI en Godot cuando aplica.
* Rodolfo gestiona la lógica del servidor, endpoints para inferencia y la integración con el instalador.

---

## Detalle por Proyecto

### Aplicación UI Godot C#

**Ubicación**: `synapxion/synapxion-app`

**Propósito**: Interfaz de usuario principal que se comercializa.

**Stack**: Godot Engine, C# (Mono), assets de diseño.

**Responsabilidades**:

* Sara / Sofia: Diseño de pantallas, assets, flujo UX.
* Rodolfo: Endpoints backend que consume la app; empaquetado para distribución.
* Jaime / Norberto: Pruebas de usabilidad, pruebas de integración y QA de release.

**Build rápido**:

* Compilar en Godot con export templates.
* Incluir binarios del backend o configurar conexión remota.

---

### Entrenador NLP PyTorch

**Ubicación**: `synapxion/synapxion-train`

**Propósito**: Entrenar modelos tipo GPT para tareas NLP específicas.

**Stack**: Python, PyTorch, scripts de preprocesamiento, checkpoints.

**Responsabilidades**:

* Rodolfo: Pipeline de entrenamiento, scripts de inferencia, gestión de checkpoints.
* Jaime / Norberto: Validación de calidad del modelo; pruebas de edge cases.
* Sara / Sofia: Revisión de prompts y UX de interacción si aplica.

**Puntos clave**:

* Mantener `requirements.txt` o `environment.yml`.
* Versionar checkpoints y registrar hiperparámetros.

---

### Sitio Web Vue + Vite

**Ubicación**: `synapxion/synapxion-site`

**Propósito**: Página pública, documentación y panel de control.

**Stack**: Vue 3, Vite, Tailwind o CSS modular.

**Responsabilidades**:

* Sara / Sofia: Diseño visual, componentes, accesibilidad.
* Rodolfo: Endpoints para panel y autenticación.
* Jaime / Norberto: Pruebas de UI y pruebas E2E.

**Comandos típicos**:

* `npm install`
* `npm run dev`
* `npm run build`

---

### Instalador y Empaquetado

**Ubicación**: `synapxion/synapxion-pack`

**Propósito**: Generar instaladores para Windows, macOS y Linux.

**Stack**: Herramientas de empaquetado (ej. Inno Setup, NSIS, pkg, AppImage).

**Responsabilidades**:

* Rodolfo: Scripts de empaquetado y firma de binarios.
* Jaime / Norberto: Pruebas de instalación y desinstalación.
* Sara / Sofia: Assets y branding dentro del instalador.

**Checklist de release**:

* Verificar integridad de binarios.
* Ejecutar instalador en entornos limpios.
* Documentar pasos de rollback.

---

### Utilidades Compartidas

**Ubicación**: `synapxion/synapxion-utils`

**Propósito**: Código reutilizable, scripts de CI, helpers de despliegue.

**Responsabilidades**:

* Rodolfo: Mantener librerías y scripts.
* Equipo: Contribuir utilidades que eviten duplicación.

---

## Flujo de Trabajo y Buenas Prácticas

* **Branching**: `main` para releases; `develop` para integración; ramas `feature/<nombre>`.
* **Pull Requests**: Revisión obligatoria por al menos **dos** miembros.
* **Commits**: Mensajes claros y referenciando issues.
* **CI**: Linters, tests unitarios y E2E en cada PR.
* **Versionado**: SemVer (`MAJOR.MINOR.PATCH`).

---

## Pruebas y Control de Calidad

**Responsabilidades generales**

* Jaime / Norberto: Planes de prueba y QA.
* Sara / Sofia: Validación visual y accesibilidad.
* Rodolfo: Integraciones backend y rendimiento.

**Checklist de QA por release**

* Build exitoso en CI.
* Tests unitarios con cobertura acordada.
* Pruebas E2E en flujos críticos.
* Pruebas de instalación y actualización.
* Revisión básica de seguridad.

---

## Despliegue y Releases

* Entrenamiento: Versionar checkpoints y artefactos.
* Backend: Staging antes de producción.
* Sitio: Deploy automático desde `main`.
* UI: Artefactos firmados desde `synapxion-pack`.
* Rollback: Mantener versiones previas listas.

---

## Contribuir

* Abrir un **issue**.
* Crear rama `feature` o `fix`.
* Hacer PR con descripción clara.
* Etiquetar reviewers adecuados.

---

## Contacto y Soporte

| **Contacto** | **Rol**                        |
| ------------ | ------------------------------ |
| **Rodolfo**  | Backend y coordinación técnica |
| **Sara**     | Diseño y frontend              |
| **Sofia**    | Diseño y frontend              |
| **Jaime**    | QA                             |
| **Norberto** | QA                             |

Para coordinación de releases, contactar a **Rodolfo**.

---

## Licencia

Indicar la licencia del proyecto (ej. MIT, Apache 2.0) y añadir `LICENSE` en cada repositorio.

---

## Notas finales

Este README es una plantilla operativa. Mantenerlo actualizado en el repositorio raíz y complementar con README específicos por proyecto.
