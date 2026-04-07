# Modelos de IA para Claw-Litle 1.0

## Modelos Requeridos

### Nivel 3: Semantic Engine (ONNX)

El motor semántico requiere el modelo **all-MiniLM-L6-v2** en formato ONNX.

**Descarga:**
```bash
# Opción 1: Desde Hugging Face (recomendado)
wget https://huggingface.co/Xenova/all-MiniLM-L6-v2/resolve/main/onnx/model.onnx -O models/all-MiniLM-L6-v2.onnx

# Opción 2: Desde GitHub (alternativa)
wget https://github.com/obss/jockey/releases/download/v0.1.0/all-MiniLM-L6-v2.onnx -O models/all-MiniLM-L6-v2.onnx
```

**Tamaño:** ~90MB

**Ruta esperada:** `models/all-MiniLM-L6-v2.onnx`

### Instalación de Dependencias

Para usar el modelo ONNX en Termux ARM64:

```bash
# En PC/Laptop (desarrollo)
pip install onnxruntime numpy

# En Termux ARM64 (producción)
# ONNX es opcional - el sistema funciona sin él usando solo niveles 1, 2 y 4
# Si tienes 6GB+ RAM y quieres activarlo:
pip install numpy
# onnxruntime puede no estar disponible en ARM64, usar fallback
```

## Estructura del Directorio

```
models/
├── README.md                    # Este archivo
├── all-MiniLM-L6-v2.onnx        # Modelo semántico (descargar)
└── keep/                        # Modelos adicionales (opcional)
```

## Verificación

Después de descargar, verifica que el modelo existe:

```bash
ls -lh models/all-MiniLM-L6-v2.onnx
```

Debe mostrar un archivo de ~90MB.

## Uso

El sistema cargará automáticamente el modelo al iniciar si existe en la ruta esperada.
El modelo se descarga bajo demanda (lazy loading) para ahorrar RAM.

Para más información, ver `src/engine/nivel_3_semantic.py`.