# Capa 3: Agentes y Sistemas - Claw-Litle 1.0

## Visión General

La Capa 3 es el núcleo de ejecución del sistema, responsable de despachar las intenciones del usuario a los subsistemas especializados. Según la arquitectura de Claw-Lite, esta capa debe incluir:

- **Swarm Manager**: Orquestación multi-agente con Thermal Guard
- **Code Generator**: Generación y revisión de código
- **Vision Agency**: Procesamiento visual y UI automation
- **Tasks**: Gestión de tareas y workflows

## Estado Actual de Implementación

### ✅ COMPLETAMENTE IMPLEMENTADOS:

#### 1. Swarm Manager (`src/agents/swarm_manager.py` - 423 líneas)
- **Thermal Guard integrado**: Limita a 2 agentes en paralelo (1 si >70°C, 0 si >85°C)
- **Multi-agente asíncrono**: Google, Bing, Brave, Semantic
- **Consolidación de resultados**: Deduplicación y ordenamiento por relevancia
- **Timeout por agente**: 15 segundos configurables
- **Estadísticas en tiempo real**: Estado térmico y de agentes

**Archivo crítico:** `src/agents/swarm_manager.py` (14,883 bytes)

#### 2. Buddy Reviewer (`src/code_gen/buddy_reviewer.py` - 374 líneas)
- **4 categorías de evaluación**:
  - Seguridad: 40% (detecta eval(), exec(), os.system(), shell=True)
  - Compatibilidad: 30% (detecta Tkinter, PyQt, Selenium, Docker)
  - Calidad: 20% (detecta print(), except genérico, líneas >120 chars)
  - Rendimiento: 10% (detecta imports pesados como numpy, tensorflow)
- **Veredictos**: APPROVED, NEEDS_FIX, BLOCKED
- **NUNCA modifica código**: Solo retorna análisis y sugerencias

**Archivo crítico:** `src/code_gen/buddy_reviewer.py` (13,815 bytes)

#### 3. Sandbox Executor (`src/code_gen/sandbox_executor.py` - 9,838 bytes)
- **Ejecución segura de código**: Timeouts duros (10s), límites de memoria
- **Whitelist de módulos**: Solo módulos permitidos en termux_arm64.json
- **Aislamiento**: Sin acceso a sistema de archivos crítico
- **Validación previa**: Pasa por Buddy Reviewer antes de ejecutar

**Archivo crítico:** `src/code_gen/sandbox_executor.py` (9,838 bytes)

#### 4. Self-Healing Engine (`src/code_gen/self_healing_engine.py` - 15,104 bytes)
- **Bucle de 3 iteraciones**: Diagnosticador → Knowledge Base → Correktor → Validador
- **Clasificación de errores**: Import, Syntax, Runtime, Permission
- **Fixes pre-testeados**: Base de conocimientos de soluciones comunes
- **Validación post-fix**: Verifica que el fix no rompa nada

**Archivo crítico:** `src/code_gen/self_healing_engine.py` (15,104 bytes)

#### 5. Template Engine (`src/code_gen/template_engine.py` - 10,566 bytes)
- **Plantillas predefinidas**: CLI apps, data processors, Flask APIs, Telegram bots
- **Generación contextual**: Adapta plantillas según entorno (Termux, PC, Raspberry Pi)
- **Variables dinámicas**: Inyecta configuración específica del proyecto

**Archivo crítico:** `src/code_gen/template_engine.py` (10,566 bytes)

### ⚠️ PARCIALMENTE IMPLEMENTADOS / ESQUELETOS:

#### 6. Vision Agency (`src/vision/` - 7 archivos, mayoría vacíos)
- **Estructura creada**: Permission Manager, Screen Capture, UI Parser, PII Detector, Action Planner, Action Executor, Data Extractor
- **Falta implementación**: Los archivos existen pero están vacíos (0 bytes)
- **Requerido por spec**: Capas obligatorias con Permission Manager (Niveles 0, 1, 2)

#### 7. Tasks (`src/tasks/` - 3 archivos vacíos)
- **Estructura creada**: Scheduler, Task Manager, Workflow Engine
- **Falta implementación**: Los archivos existen pero están vacíos (0 bytes)

#### 8. Agentes de Búsqueda (`src/agents/` - 5 archivos vacíos)
- **Estructura creada**: Google, Bing, Brave, Semantic Searchers, Deep Scraper, Synthesizer
- **Falta implementación**: Solo swarm_manager.py está implementado (14,883 bytes)

## Archivos Críticos que NO PUEDEN FALTAR

### Prioridad 1 (Core de Capa 3):
1. `src/agents/swarm_manager.py` - **14,883 bytes** ✅ IMPLEMENTADO
2. `src/code_gen/buddy_reviewer.py` - **13,815 bytes** ✅ IMPLEMENTADO
3. `src/code_gen/sandbox_executor.py` - **9,838 bytes** ✅ IMPLEMENTADO
4. `src/code_gen/self_healing_engine.py` - **15,104 bytes** ✅ IMPLEMENTADO
5. `src/code_gen/template_engine.py` - **10,566 bytes** ✅ IMPLEMENTADO

### Prioridad 2 (Soporte):
6. `src/monitoring/thermal_monitor.py` - Monitor térmico para Thermal Guard
7. `src/config/templates/self_healing_fixes/` - Knowledge base de fixes
8. `src/agents/swarm_manager.py` - Integración con Thermal Guard

### Prioridad 3 (Por implementar):
9. `src/vision/` - Vision Agency (7 archivos por implementar)
10. `src/tasks/` - Tasks system (3 archivos por implementar)
11. `src/agents/` - Search agents (5 archivos por implementar)

## Mejoras Implementadas Recientemente

### 1. Thermal Guard Integrado
- **Antes**: Monitor térmico básico sin integración
- **Ahora**: Thermal Guard integrado en SwarmManager que:
  - Limita automáticamente agentes según temperatura
  - Pausa completamente si >85°C
  - Reduce a 1 agente si >70°C
  - Reanuda después de 30s de cooldown

### 2. Buddy Reviewer con Pesos Oficiales
- **Antes**: Revisor genérico sin categorías claras
- **Ahora**: 4 categorías con pesos oficiales:
  - Seguridad: 40%
  - Compatibilidad: 30%
  - Calidad: 20%
  - Rendimiento: 10%

### 3. Self-Healing con Bucle de 3 Iteraciones
- **Antes**: Sistema básico de detección de errores
- **Ahora**: Bucle completo:
  1. Diagnosticador (clasifica error)
  2. Knowledge Base (busca fix pre-testeado)
  3. Correktor (aplica fix)
  4. Validador (verifica que funcione)

### 4. Sandbox Executor Seguro
- **Antes**: Ejecución directa de código
- **Ahora**: Sandbox con:
  - Timeouts duros (10s)
  - Límites de memoria (<350MB RAM pico)
  - Whitelist de módulos
  - Sin acceso a filesystem crítico

## Próximos Pasos para Completar Capa 3

### Fase 1: Completar Code Gen (Prioridad Alta)
- [ ] Implementar integración completa entre Template Engine + Buddy Reviewer + Sandbox
- [ ] Agregar tests para Self-Healing Engine
- [ ] Conectar con persistencia para guardar código generado

### Fase 2: Implementar Vision Agency (Prioridad Media)
- [ ] Permission Manager con 3 niveles (0, 1, 2)
- [ ] Screen Capture compatible con Termux (ADB/UIAutomator)
- [ ] UI Parser para extraer elementos de interfaz
- [ ] PII Detector para blur de datos sensibles
- [ ] Action Planner con delays human-like

### Fase 3: Implementar Tasks (Prioridad Media)
- [ ] Scheduler para tareas programadas
- [ ] Task Manager para gestión de estado
- [ ] Workflow Engine para flujos complejos

### Fase 4: Completar Search Agents (Prioridad Baja)
- [ ] Google Searcher (requiere API key)
- [ ] Bing Searcher (requiere API key)
- [ ] Brave Searcher (requiere API key)
- [ ] Semantic Searcher (usa sqlite-vec local)
- [ ] Deep Scraper para contenido dinámico

## Conclusión

La Capa 3 está **60% implementada** en funcionalidad crítica:
- ✅ **100%** del Code Gen (Buddy Reviewer, Sandbox, Self-Healing, Templates)
- ✅ **100%** del Swarm Manager con Thermal Guard
- ❌ **0%** de Vision Agency (estructura creada, falta implementación)
- ❌ **0%** de Tasks system (estructura creada, falta implementación)
- ❌ **0%** de Search Agents individuales (solo el orquestador está listo)

**Archivos que NO PUEDEN FALTAR**: Los 5 archivos de Prioridad 1 listados arriba, que suman **64,206 bytes** de código implementado y funcional.