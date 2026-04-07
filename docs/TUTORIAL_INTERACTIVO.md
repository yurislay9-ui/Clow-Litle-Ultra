# 🦁 Tutorial Interactivo - Claw-Litle 1.0

¡Bienvenido al tutorial interactivo de Claw-Litle! En los próximos minutos aprenderás a usar todas las funcionalidades de esta poderosa herramienta.

## 📋 Índice

1. [Primeros Pasos](#primeros-pasos)
2. [Comandos Básicos](#comandos-básicos)
3. [Búsqueda Web Inteligente](#búsqueda-web-inteligente)
4. [Generación de Código](#generación-de-código)
5. [Automatización de Tareas](#automatización-de-tareas)
6. [Optimización Mobile](#optimización-mobile)
7. [Trucos Avanzados](#trucos-avanzados)

---

## Primeros Pasos

### 1. Verificar Instalación

```bash
# Ejecuta este comando para verificar que todo está instalado correctamente
python -m claw_lite --version

# Deberías ver algo como: Claw-Litle 1.0.0
```

### 2. Primeros Comandos

```bash
# Ver ayuda completa
claw --help

# Ver estado del sistema
claw status

# Ver configuración actual
claw config show
```

### 3. Tu Primera Query

```bash
# Pregunta algo simple
claw "¿Cuál es la capital de Francia?"

# El sistema usará el motor de nivel 1 (regex) para responder rápidamente
```

---

## Comandos Básicos

### Modo Interactivo

```bash
# Iniciar modo interactivo (como una conversación)
claw interactive

# En modo interactivo puedes:
# - Hacer preguntas seguidas
# - Usar "salir" o "exit" para terminar
# - Usar "ayuda" para ver comandos disponibles
```

### Modo Batch

```bash
# Ejecutar múltiples queries desde un archivo
claw batch queries.txt --output resultados.json

# El archivo queries.txt debe tener una query por línea
```

### Modo API

```bash
# Iniciar servidor API REST
claw api --port 8080

# Luego puedes hacer peticiones:
curl http://localhost:8080/query -d '{"text": "¿Qué es Python?"}'
```

---

## Búsqueda Web Inteligente

### 1. Búsqueda Básica

```bash
# Búsqueda automática (usa el mejor searcher disponible)
claw search "noticias sobre inteligencia artificial 2024"

# Búsqueda con motor específico
claw search "python tutorials" --engine google
claw search "python tutorials" --engine bing
claw search "python tutorials" --engine brave
```

### 2. Scraping Profundo

```bash
# Extraer contenido de una URL específica
claw scrape "https://example.com/article" --extract main-content

# Extraer solo enlaces
claw scrape "https://example.com" --extract links

# Extraer imágenes
claw scrape "https://example.com" --extract images
```

### 3. Búsqueda Semántica

```bash
# Búsqueda por significado (no solo palabras clave)
claw semantic "aplicaciones de machine learning en medicina"

# El sistema usará embeddings ONNX para encontrar resultados relevantes
# incluso si no contienen las palabras exactas
```

---

## Generación de Código

### 1. Generar Script Simple

```bash
# Generar un script de Python
claw code "crea un script que liste archivos en un directorio"

# El sistema:
# 1. Genera el código
# 2. Lo revisa con Buddy Reviewer
# 3. Te muestra el resultado con explicaciones
```

### 2. Generar con Plantillas

```bash
# Usar plantilla específica
claw code "API REST para gestión de usuarios" --template flask_api

# Plantillas disponibles:
# - cli_app: Aplicación de línea de comandos
# - flask_api: API REST con Flask
# - data_processor: Procesamiento de datos
# - scheduled_task: Tarea programada
# - telegram_bot: Bot de Telegram
# - web_scraper: Scraper web
```

### 3. Auto-Corrección

```bash
# Si el código generado tiene errores, usa self-healing
claw code "script con error" --self-heal

# El sistema:
# 1. Detecta el error
# 2. Busca en su base de conocimientos
# 3. Aplica corrección automática
# 4. Valida que funcione
```

---

## Automatización de Tareas

### 1. Crear Tarea Programada

```bash
# Programar tarea diaria
claw task schedule "backup diario" --cron "0 2 * * *" --command "claw backup create"

# Programar tarea cada hora
claw task schedule "check system" --interval 3600 --command "claw health-check"
```

### 2. Workflows Complejos

```bash
# Crear workflow con múltiples pasos
claw workflow create "daily_report" << EOF
step1: claw search "noticias del día"
step2: claw summarize --input step1_output
step3: claw send-telegram --message step2_output
EOF
```

### 3. Tareas en Segundo Plano

```bash
# Ejecutar tarea en background (solo Pro/Enterprise)
claw task run "proceso_largo" --background

# Ver tareas en ejecución
claw task list --running
```

---

## Optimización Mobile

### 1. Ver Estado de Recursos

```bash
# Ver uso de CPU, RAM y temperatura
claw monitor resources

# Ver estado de la batería (en móvil)
claw monitor battery
```

### 2. Modos de Energía

```bash
# Cambiar modo de energía
claw power-mode balanced    # Equilibrio (por defecto)
claw power-mode performance # Máximo rendimiento
claw power-mode power-save  # Ahorro de batería
claw power-mode ultra-save  # Máximo ahorro
```

### 3. Optimización Automática

```bash
# Activar optimización automática
claw optimize auto

# El sistema:
# - Ajusta número de agentes según RAM disponible
# - Controla thermal throttling
# - Gestiona batería inteligentemente
# - Limpia memoria cuando es necesario
```

---

## Trucos Avanzados

### 1. Pipes y Redirección

```bash
# Encadenar comandos
claw search "python best practices" | claw summarize | claw save --format markdown

# Guardar salida en archivo
claw "explicar machine learning" > explicacion_ml.txt
```

### 2. Variables de Entorno

```bash
# Configurar API keys (una sola vez)
export CLAW_GOOGLE_API_KEY="tu_key"
export CLAW_TELEGRAM_BOT_TOKEN="tu_token"

# O usar archivo .env
claw config set --file .env
```

### 3. Plugins Personalizados

```bash
# Crear plugin personalizado
claw plugin create mi_plugin --language python

# El sistema genera la estructura básica
# Luego edita mi_plugin/main.py con tu lógica
```

### 4. Modo Debug

```bash
# Ver logs detallados
claw --debug "tu query"

# Ver trazas de ejecución
claw --trace "tu query"
```

---

## 🎯 Ejercicios Prácticos

### Ejercicio 1: Tu Primer Script

```bash
# 1. Genera un script que descargue el clima
claw code "script que muestre el clima de Madrid"

# 2. Guarda el resultado
claw code "script clima" --save weather.py

# 3. Ejecútalo
python weather.py
```

### Ejercicio 2: Búsqueda Inteligente

```bash
# 1. Busca tutoriales de Python
claw search "python tutorial para principiantes" --engine google

# 2. Extrae los enlaces
claw scrape "https://google.com/search?q=python+tutorial" --extract links

# 3. Guarda los resultados
claw search "python tutorial" --save resultados.json
```

### Ejercicio 3: Automatización

```bash
# 1. Crea un workflow diario
claw workflow create "daily_news" << EOF
step1: claw search "noticias tecnología"
step2: claw summarize --input step1_output
step3: echo step2_output
EOF

# 2. Prográmalo para las 8 AM
claw task schedule "daily_news" --cron "0 8 * * *" --workflow daily_news

# 3. Pruébalo
claw workflow run daily_news
```

---

## 📚 Recursos Adicionales

- **Documentación completa**: `claw docs`
- **Ejemplos**: `ls examples/`
- **Comunidad**: https://github.com/yurislay9-ui/Clow-Litle-Ultra/discussions
- **Soporte**: support@clawlite.com (solo Pro/Enterprise)

---

## 🎉 ¡Felicidades!

Has completado el tutorial interactivo de Claw-Litle 1.0. Ahora estás listo para aprovechar al máximo esta poderosa herramienta.

**Próximos pasos recomendados:**
1. Explora los ejemplos en `examples/`
2. Únete a la comunidad en GitHub
3. Considera actualizar a Pro para más características
4. ¡Comienza a crear tus propios proyectos!

¿Tienes preguntas? Usa `claw help` o visita nuestra documentación.

---

**💡 Consejo Pro:** Usa `claw interactive` para un modo conversacional donde puedes hacer preguntas de seguimiento naturalmente.