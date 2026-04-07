"""
Claw-Litle 1.0
nivel_4_expert.py - Nivel 4: Expert Rules

Sistema de reglas expertas para validación final.
Siempre se ejecuta como fallback y validador de niveles anteriores.
"""

import re
import logging
from typing import Dict, Optional, List, Tuple

from ..engine import IntentResult

logger = logging.getLogger(__name__)


class ExpertEngine:
    """
    Nivel 4 del Motor Híbrido: Expert Rules.
    
    Sistema de reglas expertas que:
    1. Valida resultados de niveles anteriores
    2. Aplica reglas de contexto y estado
    3. Sirve como fallback cuando otros niveles fallan
    4. Detecta patrones complejos multi-intención
    """
    
    def __init__(self, intents_registry: Dict):
        """
        Inicializa el motor de reglas expertas.
        
        Args:
            intents_registry: Diccionario con las intenciones
        """
        self.intents = intents_registry.get('intents', [])
        self.fallback = intents_registry.get('fallback', {})
        
        # Reglas expertas predefinidas
        self._expert_rules = self._load_expert_rules()
        
        logger.debug(f"ExpertEngine inicializado con {len(self._expert_rules)} reglas")
    
    def _load_expert_rules(self) -> List[Dict]:
        """
        Carga las reglas expertas predefinidas.
        
        Estas reglas detectan patrones complejos que los niveles 1-3 no capturan.
        """
        return [
            {
                "name": "multi_action",
                "pattern": r"(buscar|crea|r)\s+.+\s+(y|para|con)\s+.+",
                "intent": "multi_intent",
                "confidence": 0.75,
                "description": "Query con múltiples acciones"
            },
            {
                "name": "question_pattern",
                "pattern": r"^(cómo|que|cuándo|dónde|cuál|por\s+qué|puedo|quiero)\s+.+",
                "intent": "question",
                "confidence": 0.70,
                "description": "Pregunta abierta"
            },
            {
                "name": "code_request",
                "pattern": r"(código|script|programa|app|función|clase)\s+(de|para|que|en)\s+.+",
                "intent": "code_generation",
                "confidence": 0.80,
                "description": "Solicitud de código"
            },
            {
                "name": "search_request",
                "pattern": r"(info|información|datos|precio|noticia)\s+(de|sobre|acerca\s+de)\s+.+",
                "intent": "web_search",
                "confidence": 0.80,
                "description": "Solicitud de búsqueda de información"
            },
            {
                "name": "error_fix",
                "pattern": r"(error|fallo|bug|problema|no\s+funciona)\s+(en|con|al)\s+.+",
                "intent": "code_repair",
                "confidence": 0.75,
                "description": "Reporte de error en código"
            },
            {
                "name": "negative_response",
                "pattern": r"^(no|nop|negativo|para|basta|stop|alto)$",
                "intent": "cancel",
                "confidence": 0.90,
                "description": "Respuesta negativa/cancelar"
            },
            {
                "name": "affirmative_response",
                "pattern": r"^(si|sí|sip|claro|obvio|dale|vale|ok|okay)$",
                "intent": "confirm",
                "confidence": 0.90,
                "description": "Respuesta afirmativa/confirmar"
            }
        ]
    
    def _apply_expert_rules(self, query: str) -> Optional[IntentResult]:
        """
        Aplica reglas expertas a la query.
        
        Args:
            query: Texto de entrada del usuario
        
        Returns:
            IntentResult si alguna regla aplica
        """
        query_lower = query.strip().lower()
        
        for rule in self._expert_rules:
            if re.search(rule["pattern"], query_lower):
                logger.debug(f"Expert rule '{rule['name']}' matched: {rule['intent']}")
                return IntentResult(
                    intent_name=rule["intent"],
                    confidence=rule["confidence"],
                    level_reached=4,
                    metadata={
                        "level": "expert",
                        "rule_name": rule["name"],
                        "rule_description": rule["description"]
                    }
                )
        
        return None
    
    def _validate_context(
        self, 
        result: Optional[IntentResult], 
        user_context: Optional[Dict]
    ) -> Optional[IntentResult]:
        """
        Valida y ajusta el resultado basado en contexto del usuario.
        
        Args:
            result: Resultado de niveles anteriores
            user_context: Contexto adicional del usuario
        
        Returns:
            IntentResult ajustado o el original
        """
        if not user_context:
            return result
        
        # Si hay un resultado previo, validarlo con contexto
        if result and result.intent_name in user_context.get('recent_intents', []):
            # Evitar loops de la misma intención
            result.confidence *= 0.5  # Reducir confianza si es repetitiva
            result.metadata['context_penalty'] = True
        
        # Contexto de estado (ej: modo desarrollo, modo seguro, etc.)
        if user_context.get('mode') == 'development':
            # En modo desarrollo, ser más permisivo con code_generation
            if result and result.intent_name == 'code_generation':
                result.confidence = min(result.confidence + 0.1, 1.0)
        
        return result
    
    def _get_fallback_intent(self) -> IntentResult:
        """
        Retorna la intención fallback del sistema.
        
        Returns:
            IntentResult con la intención fallback
        """
        fallback_type = self.fallback.get('type', 'agent')
        fallback_details = self.fallback.get('details', {})
        
        return IntentResult(
            intent_name="fallback",
            confidence=0.5,
            level_reached=4,
            metadata={
                "level": "expert",
                "fallback_type": fallback_type,
                "fallback_details": fallback_details,
                "reason": "No se pudo determinar intención clara"
            }
        )
    
    def validate(
        self, 
        query: str, 
        previous_result: Optional[IntentResult],
        user_context: Optional[Dict] = None
    ) -> IntentResult:
        """
        Valida y completa el procesamiento de la query.
        
        Este método siempre se ejecuta, incluso si niveles anteriores tuvieron éxito.
        Sirve como validador final y fallback.
        
        Args:
            query: Texto de entrada del usuario
            previous_result: Resultado de niveles 1-3 (puede ser None)
            user_context: Contexto adicional del usuario
        
        Returns:
            IntentResult final validado
        """
        # Si hay resultado previo, validarlo con contexto
        if previous_result:
            validated = self._validate_context(previous_result, user_context)
            return validated or previous_result
        
        # Si no hay resultado previo, aplicar reglas expertas
        expert_result = self._apply_expert_rules(query)
        if expert_result:
            return expert_result
        
        # Si tampoco hay match con reglas expertas, usar fallback
        logger.info(f"Usando fallback para query: '{query[:50]}...'")
        return self._get_fallback_intent()