"""
Claw-Litle 1.0
nivel_1_regex.py - Nivel 1: Regex Filter

Motor de patrones regex instantáneos (~0ms).
Detecta intenciones por patrones exactos conocidos.
"""

import re
import logging
from typing import Dict, Optional

from ..engine import IntentResult

logger = logging.getLogger(__name__)


class RegexEngine:
    """
    Nivel 1 del Motor Híbrido: Regex Filter.
    
    Procesa patrones regex definidos en el intents_registry.
    Es instantáneo (~0ms) y tiene la máxima prioridad.
    """
    
    def __init__(self, intents_registry: Dict):
        """
        Inicializa el motor de regex.
        
        Args:
            intents_registry: Diccionario con las intenciones y sus patrones
        """
        self.intents = intents_registry.get('intents', [])
        self._compiled_patterns = {}
        
        # Compilar todos los patrones regex al inicio
        self._compile_patterns()
        logger.debug(f"RegexEngine inicializado con {len(self._compiled_patterns)} patrones")
    
    def _compile_patterns(self):
        """Compila todos los patrones regex del registro."""
        for intent in self.intents:
            intent_name = intent['name']
            patterns = intent.get('triggers', {}).get('patterns', [])
            
            compiled = []
            for pattern in patterns:
                try:
                    compiled.append(re.compile(pattern, re.IGNORECASE | re.UNICODE))
                except re.error as e:
                    logger.warning(f"Patrón regex inválido '{pattern}' para {intent_name}: {e}")
            
            if compiled:
                self._compiled_patterns[intent_name] = compiled
    
    def match(self, query: str) -> Optional[IntentResult]:
        """
        Intenta matchear la query con patrones regex.
        
        Args:
            query: Texto de entrada del usuario
        
        Returns:
            IntentResult si hay match, None si no
        """
        query_lower = query.strip().lower()
        
        for intent_name, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                if pattern.fullmatch(query_lower):
                    logger.debug(f"Regex match: '{query}' -> {intent_name}")
                    return IntentResult(
                        intent_name=intent_name,
                        confidence=1.0,  # Match exacto = 100% confianza
                        level_reached=1,
                        metadata={
                            "matched_pattern": pattern.pattern,
                            "level": "regex"
                        }
                    )
        
        return None