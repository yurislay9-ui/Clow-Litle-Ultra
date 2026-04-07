# Descarga del Modelo ONNX para Termux

## Comando Exacto para Descargar el Modelo

Ejecuta este comando en tu terminal Termux desde el directorio del proyecto:

```bash
cd claw-litle && wget --continue --timeout=300 --tries=unlimited --waitretry=5 "https://huggingface.co/Xenova/all-MiniLM-L6-v2/resolve/main/onnx/model.onnx" -O models/all-MiniLM-L6-v2.onnx
```

## Explicación de Parámetros de Persistencia:

- `--continue`: Reanuda descargas interrumpidas (no empieza desde cero)
- `--timeout=300`: Espera 5 minutos antes de considerar timeout
- `--tries=unlimited`: Reintentos infinitos si falla
- `--waitretry=5`: Espera 5 segundos entre reintentos

## Verificación de Progreso:

Para ver el progreso sin interrumpir la descarga, abre otra terminal y ejecuta:

```bash
watch -n 5 'ls -lh claw-litle/models/all-MiniLM-L6-v2.onnx 2>/dev/null || echo "Descargando..."'
```

## Verificación Final:

Cuando termine, el archivo debe pesar ~90MB:

```bash
ls -lh claw-litle/models/all-MiniLM-L6-v2.onnx
```

Salida esperada: `-rw-r--r-- 1 u0_a*** 90M ...`

## Si se Interrumpe:

Simplemente vuelve a ejecutar el mismo comando. Gracias a `--continue`, reanudará desde donde se quedó.

## Tamaño Esperado:

- **Tamaño final:** ~90MB (94,376,962 bytes)
- **Tiempo estimado:** 30-60 minutos con conexión móvil promedio

## Nota Importante:

El sistema Claw-Litle funciona SIN el modelo ONNX usando los niveles 1 (Regex), 2 (Fuzzy) y 4 (Expert Rules). El modelo ONNX solo activa el nivel 3 (Semantic) para mejoras de precisión semántica.