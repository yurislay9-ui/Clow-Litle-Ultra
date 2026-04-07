"""
Claw-Litle 1.0
engine/__init__.py - Paquete del motor

Exporta HybridEngine e IntentResult para uso interno de los módulos.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class IntentResult:
    """Resultado de clasificación de intención."""
    intent_name: str
    confidence: float
    level_reached: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario."""
        return {
            "intent_name": self.intent_name,
            "confidence": self.confidence,
            "level_reached": self.level_reached,
            "metadata": self.metadata
        }

# Importar HybridEngine desde el módulo hybrid_engine en src/
def _get_hybrid_engine():
    """Lazy loading de HybridEngine para evitar importaciones circulares."""
    from ..hybrid_engine import HybridEngine
    return HybridEngine

__all__ = ["IntentResult", "HybridEngine"]

# Hacer HybridEngine disponible directamente
HybridEngine = _get_hybrid_engine()
