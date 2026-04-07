"""
Claw-Litle 1.0
nivel_2_fuzzy.py - Nivel 2: Fuzzy Matching

Motor de coincidencia aproximada usando RapidFuzz (~1-2ms).
Detecta intenciones por similitud de texto.
"""

import logging
from typing import Dict, Optional, List, Tuple

from ..engine import IntentResult

logger = logging.getLogger(__name__)


class FuzzyEngine:
    """
    Nivel 2 del Motor Híbrido: Fuzzy Matching.
    
    Usa RapidFuzz para matching aproximado de keywords.
    Más lento que regex (~1-2ms) pero más flexible.
    """
    
    def __init__(self, intents_registry: Dict, threshold: float = 0.85):
        """
        Inicializa el motor fuzzy.
        
        Args:
            intents_registry: Diccionario con las intenciones
            threshold: Umbral mínimo de similitud (0.0-1.0)
        """
        self.intents = intents_registry.get('intents', [])
        self.threshold = threshold
        
        # Extraer keywords por intención
        self._keyword_map: Dict[str, List[str]] = {}
        for intent in self.intents:
            intent_name = intent['name']
            keywords = intent.get('triggers', {}).get('keywords', [])
            if keywords:
                self._keyword_map[intent_name] = [k.lower() for k in keywords]
        
        logger.debug(f"FuzzyEngine inicializado con {len(self._keyword_map)} intenciones")
    
    def _get_fuzz_ratio(self, query: str, keyword: str) -> float:
        """
        Calcula el ratio de similitud fuzzy entre query y keyword.
        
        Implementación simple sin dependencias externas (para compatibilidad).
        Usa Levenshtein distance normalizada.
        """
        if not query or not keyword:
            return 0.0
        
        query = query.lower().strip()
        keyword = keyword.lower().strip()
        
        # Caso exacto
        if query == keyword:
            return 1.0
        
        # Si la query contiene la keyword exacta
        if keyword in query:
            return 0.95
        
        # Si la keyword está al inicio de la query
        if query.startswith(keyword):
            return 0.90
        
        # Calcular distancia de Levenshtein
        len1, len2 = len(query), len(keyword)
        
        # Optimización: si la diferencia de longitud es muy grande
        if abs(len1 - len2) > max(len1, len2) * 0.5:
            return 0.0
        
        # Matriz de Levenshtein
        prev_row = list(range(len2 + 1))
        
        for i in range(len1):
            curr_row = [i + 1]
            for j in range(len2):
                insert = prev_row[j + 1] + 1
                delete = curr_row[j] + 1
                replace = prev_row[j] + (0 if query[i] == keyword[j] else 1)
                curr_row.append(min(insert, delete, replace))
            prev_row = curr_row
        
        distance = prev_row[len2]
        max_len = max(len1, len2)
        
        return 1.0 - (distance / max_len)
    
    def match(self, query: str) -> Optional[IntentResult]:
        """
        Intenta matchear la query con fuzzy matching.
        
        Args:
            query: Texto de entrada del usuario
        
        Returns:
            IntentResult si hay match, None si no
        """
        query_lower = query.strip().lower()
        
        best_intent = None
        best_score = 0.0
        best_keyword = None
        
        for intent_name, keywords in self._keyword_map.items():
            for keyword in keywords:
                score = self._get_fuzz_ratio(query_lower, keyword)
                
                if score > best_score:
                    best_score = score
                    best_intent = intent_name
                    best_keyword = keyword
        
        if best_intent and best_score >= self.threshold:
            logger.debug(f"Fuzzy match: '{query}' -> {best_intent} ({best_score:.2%}) via '{best_keyword}'")
            return IntentResult(
                intent_name=best_intent,
                confidence=best_score,
                level_reached=2,
                metadata={
                    "matched_keyword": best_keyword,
                    "level": "fuzzy",
                    "threshold": self.threshold
                }
            )
        
        return None