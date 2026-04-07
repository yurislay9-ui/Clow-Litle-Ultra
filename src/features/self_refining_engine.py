"""
Self-Refining Reasoning Engine - Claw-Litle 1.0

Sistema de razonamiento que critica su propio razonamiento interno,
detecta contradicciones, y refina iterativamente hasta alcanzar umbral de confianza.
"""

import time
import hashlib
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class RefinementStatus(Enum):
    """Estados del proceso de self-refining"""
    INITIAL = "initial"
    CRITIQUING = "critiquing"
    REFINING = "refining"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class RefinementIteration:
    """Representa una iteración del proceso de refinamiento"""
    iteration_number: int
    draft: str
    confidence_score: float
    issues_detected: List[str]
    improvements_made: List[str]
    time_taken_ms: float
    status: RefinementStatus
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RefinementResult:
    """Resultado final del proceso de self-refining"""
    final_answer: str
    iterations: List[RefinementIteration]
    total_time_ms: float
    final_confidence: float
    max_confidence_reached: float
    iterations_used: int
    max_iterations_allowed: int
    confidence_threshold: float
    early_stopped: bool
    reasoning: str


class ConfidenceEvaluator:
    """
    Evaluador de confianza para el Self-Refining Reasoning Engine.
    
    Calcula la confianza en una respuesta basada en múltiples factores:
    - Consistencia interna
    - Completitud
    - Precisión factual (cuando es verificable)
    - Coherencia con el contexto
    - Calidad de la estructura
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.confidence_threshold = self.config.get("confidence_threshold", 0.92)
        
        # Patrones de baja confianza
        self.low_confidence_indicators = [
            "no estoy seguro", "quizás", "tal vez", "probablemente",
            "podría ser", "no tengo información", "no sé", "desconozco",
            "posiblemente", "aproximadamente", "más o menos"
        ]
        
        # Patrones de alta confianza
        self.high_confidence_indicators = [
            "definitivamente", "claramente", "evidentemente",
            "sin duda", "con certeza", "es un hecho",
            "está demostrado", "se sabe que"
        ]
        
        # Patrones de contradicción
        self.contradiction_patterns = [
            "pero también", "sin embargo", "aunque", "por otro lado",
            "en contraste", "no obstante"
        ]
    
    def evaluate(self, response: str, query: str, context: Optional[str] = None) -> float:
        """
        Evalúa la confianza en una respuesta.
        
        Args:
            response: Texto de la respuesta
            query: Consulta original del usuario
            context: Contexto adicional
        
        Returns:
            Puntuación de confianza entre 0.0 y 1.0
        """
        if not response or not response.strip():
            return 0.0
        
        response_lower = response.lower()
        confidence = 0.5  # Confianza base
        
        # 1. Verificar indicadores de baja confianza
        low_confidence_count = sum(1 for indicator in self.low_confidence_indicators 
                                   if indicator in response_lower)
        if low_confidence_count > 0:
            confidence -= 0.1 * min(low_confidence_count, 3)
        
        # 2. Verificar indicadores de alta confianza
        high_confidence_count = sum(1 for indicator in self.high_confidence_indicators 
                                    if indicator in response_lower)
        if high_confidence_count > 0:
            confidence += 0.05 * min(high_confidence_count, 3)
        
        # 3. Verificar longitud y completitud
        word_count = len(response.split())
        if word_count < 10:
            confidence -= 0.1
        elif word_count > 500:
            confidence -= 0.05  # Demasiado largo puede indicar divagación
        
        # 4. Verificar estructura (párrafos, listas, etc.)
        if self._has_good_structure(response):
            confidence += 0.05
        
        # 5. Verificar relevancia con la query
        if self._is_relevant(response, query):
            confidence += 0.1
        
        # 6. Verificar contradicciones internas
        contradiction_count = sum(1 for pattern in self.contradiction_patterns 
                                  if pattern in response_lower)
        if contradiction_count > 2:
            confidence -= 0.1
        
        # 7. Verificar consistencia factual (básico)
        if self._check_factual_consistency(response):
            confidence += 0.05
        
        # Normalizar a rango 0-1
        confidence = max(0.0, min(1.0, confidence))
        
        return round(confidence, 2)
    
    def _has_good_structure(self, response: str) -> bool:
        """Verifica si la respuesta tiene buena estructura"""
        # Verificar presencia de párrafos
        paragraphs = [p.strip() for p in response.split('\n') if p.strip()]
        if len(paragraphs) < 2:
            return False
        
        # Verificar uso de puntuación adecuada
        sentences = [s.strip() for s in response.split('.') if s.strip()]
        if len(sentences) < 2:
            return False
        
        return True
    
    def _is_relevant(self, response: str, query: str) -> bool:
        """Verifica si la respuesta es relevante para la query"""
        query_words = set(query.lower().split())
        response_words = set(response.lower().split())
        
        # Palabras clave importantes de la query (excluyendo stopwords)
        stopwords = {"el", "la", "los", "las", "un", "una", "unos", "unas", 
                     "de", "del", "en", "con", "por", "para", "que", "como",
                     "y", "o", "pero", "si", "no", "al", "se", "lo", "le",
                     "me", "te", "mi", "tu", "su", "este", "esta", "eso"}
        
        important_words = query_words - stopwords
        
        if not important_words:
            return True
        
        # Verificar cuántas palabras importantes aparecen en la response
        matches = important_words.intersection(response_words)
        match_ratio = len(matches) / len(important_words)
        
        return match_ratio > 0.3
    
    def _check_factual_consistency(self, response: str) -> bool:
        """Verifica consistencia factual básica"""
        # Verificaciones simples de consistencia
        # (En una implementación real, esto podría usar una base de conocimientos)
        
        # Verificar que no haya números contradictorios
        numbers = [word for word in response.split() if word.isdigit()]
        if len(numbers) > 1:
            # Si hay múltiples números, verificar que no sean contradictorios
            # (esto es una simplificación)
            pass
        
        return True


class SelfRefiningEngine:
    """
    Motor de razonamiento auto-refinado para Claw-Litle.
    
    Implementa un bucle de refinamiento iterativo que:
    1. Genera un borrador initial
    2. Evalúa la confianza
    3. Si la confianza < umbral, critica y refina
    4. Repite hasta alcanzar umbral o máximo iteraciones
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.confidence_threshold = self.config.get("confidence_threshold", 0.92)
        self.max_iterations = self.config.get("max_iterations", 3)
        self.timeout_seconds = self.config.get("timeout_seconds", 30)
        
        self.evaluator = ConfidenceEvaluator(config)
        
        # Callbacks para generación y refinamiento
        self.generator_callback: Optional[Callable] = None
        self.refiner_callback: Optional[Callable] = None
        self.critic_callback: Optional[Callable] = None
    
    def set_generator(self, callback: Callable[[str, Optional[str]], str]):
        """
        Establece el callback para generación de respuestas.
        
        Args:
            callback: Función(query, context) -> response
        """
        self.generator_callback = callback
    
    def set_refiner(self, callback: Callable[[str, str, List[str], Optional[str]], str]):
        """
        Establece el callback para refinamiento de respuestas.
        
        Args:
            callback: Función(query, current_draft, issues, context) -> refined_response
        """
        self.refiner_callback = callback
    
    def set_critic(self, callback: Callable[[str, str, Optional[str]], List[str]]):
        """
        Establece el callback para crítica de respuestas.
        
        Args:
            callback: Función(query, response, context) -> issues_list
        """
        self.critic_callback = callback
    
    def refine(
        self,
        query: str,
        initial_response: Optional[str] = None,
        context: Optional[str] = None,
        confidence_threshold: Optional[float] = None,
        max_iterations: Optional[int] = None
    ) -> RefinementResult:
        """
        Ejecuta el proceso de self-refining sobre una respuesta.
        
        Args:
            query: Consulta del usuario
            initial_response: Respuesta inicial (si None, se genera)
            context: Contexto adicional
            confidence_threshold: Umbral de confianza (override)
            max_iterations: Máximo iteraciones (override)
        
        Returns:
            RefinementResult con el resultado del proceso
        """
        start_time = time.time()
        threshold = confidence_threshold or self.confidence_threshold
        max_iter = max_iterations or self.max_iterations
        
        iterations: List[RefinementIteration] = []
        current_response = initial_response
        final_confidence = 0.0
        max_confidence = 0.0
        early_stopped = False
        reasoning_parts = []
        
        # Si no hay respuesta initial, generar una
        if not current_response and self.generator_callback:
            try:
                current_response = self.generator_callback(query, context)
            except Exception as e:
                return self._create_error_result(str(e), start_time)
        elif not current_response:
            return self._create_error_result("No generator callback set", start_time)
        
        # Bucle de refinamiento
        for iteration_num in range(1, max_iter + 1):
            # Verificar timeout
            elapsed = time.time() - start_time
            if elapsed > self.timeout_seconds:
                early_stopped = True
                reasoning_parts.append(f"Timeout después de {elapsed:.1f}s")
                break
            
            iter_start = time.time()
            
            # 1. Evaluar confianza
            confidence = self.evaluator.evaluate(current_response, query, context)
            max_confidence = max(max_confidence, confidence)
            
            # 2. Verificar si alcanzamos el umbral
            if confidence >= threshold:
                final_confidence = confidence
                reasoning_parts.append(
                    f"Iteración {iteration_num}: Confianza {confidence:.2f} >= {threshold:.2f} (umbral)"
                )
                early_stopped = True
                break
            
            # 3. Si es la última iteración, terminar
            if iteration_num == max_iter:
                final_confidence = confidence
                reasoning_parts.append(
                    f"Iteración {iteration_num}: Máximo iteraciones alcanzado (confianza: {confidence:.2f})"
                )
                break
            
            # 4. Criticar la respuesta actual
            issues = []
            if self.critic_callback:
                try:
                    issues = self.critic_callback(query, current_response, context)
                except Exception as e:
                    issues = [f"Error en crítica: {str(e)}"]
            
            # 5. Refinar la respuesta
            if issues and self.refiner_callback:
                try:
                    refined = self.refiner_callback(query, current_response, issues, context)
                    if refined and refined != current_response:
                        current_response = refined
                        reasoning_parts.append(
                            f"Iteración {iteration_num}: {len(issues)} issues corregidos"
                        )
                    else:
                        reasoning_parts.append(
                            f"Iteración {iteration_num}: No se pudo refinar (sin cambios)"
                        )
                except Exception as e:
                    reasoning_parts.append(
                        f"Iteración {iteration_num}: Error en refinamiento: {str(e)}"
                    )
            else:
                if not issues:
                    reasoning_parts.append(
                        f"Iteración {iteration_num}: No se detectaron issues"
                    )
                else:
                    reasoning_parts.append(
                        f"Iteración {iteration_num}: {len(issues)} issues sin refiner callback"
                    )
            
            # 6. Registrar iteración
            iter_time = (time.time() - iter_start) * 1000
            iteration = RefinementIteration(
                iteration_number=iteration_num,
                draft=current_response[:500],  # Truncar para no hacer muy largo
                confidence_score=confidence,
                issues_detected=issues,
                improvements_made=[],
                time_taken_ms=iter_time,
                status=RefinementStatus.COMPLETED
            )
            iterations.append(iteration)
        
        total_time = (time.time() - start_time) * 1000
        final_confidence = max_confidence if final_confidence == 0.0 else final_confidence
        
        return RefinementResult(
            final_answer=current_response,
            iterations=iterations,
            total_time_ms=round(total_time, 2),
            final_confidence=round(final_confidence, 2),
            max_confidence_reached=round(max_confidence, 2),
            iterations_used=len(iterations),
            max_iterations_allowed=max_iter,
            confidence_threshold=threshold,
            early_stopped=early_stopped,
            reasoning=" | ".join(reasoning_parts)
        )
    
    def _create_error_result(self, error: str, start_time: float) -> RefinementResult:
        """Crea un resultado de error"""
        total_time = (time.time() - start_time) * 1000
        return RefinementResult(
            final_answer=f"Error: {error}",
            iterations=[],
            total_time_ms=round(total_time, 2),
            final_confidence=0.0,
            max_confidence_reached=0.0,
            iterations_used=0,
            max_iterations_allowed=self.max_iterations,
            confidence_threshold=self.confidence_threshold,
            early_stopped=True,
            reasoning=f"Error: {error}"
        )
    
    def quick_refine(
        self,
        query: str,
        initial_response: str,
        context: Optional[str] = None
    ) -> Tuple[str, float, float]:
        """
        Versión rápida del refinamiento (1 iteración).
        
        Args:
            query: Consulta del usuario
            initial_response: Respuesta inicial
            context: Contexto adicional
        
        Returns:
            Tupla (respuesta_refinada, confianza, tiempo_ms)
        """
        result = self.refine(
            query=query,
            initial_response=initial_response,
            context=context,
            max_iterations=1
        )
        return result.final_answer, result.final_confidence, result.total_time_ms


# Instancia global
_engine: Optional[SelfRefiningEngine] = None


def get_self_refining_engine(config: Optional[Dict] = None) -> SelfRefiningEngine:
    """Obtiene la instancia global del Self-Refining Engine"""
    global _engine
    if _engine is None:
        _engine = SelfRefiningEngine(config)
    return _engine


def refine_response(
    query: str,
    initial_response: str,
    context: Optional[str] = None,
    confidence_threshold: Optional[float] = None
) -> RefinementResult:
    """Función helper para refinar una respuesta"""
    return get_self_refining_engine().refine(
        query=query,
        initial_response=initial_response,
        context=context,
        confidence_threshold=confidence_threshold
    )


# Ejemplo de uso con callbacks simples
def example_generator(query: str, context: Optional[str]) -> str:
    """Generador de ejemplo (placeholder)"""
    return f"Respuesta inicial para: {query}"


def example_critic(query: str, response: str, context: Optional[str]) -> List[str]:
    """Crítico de ejemplo (placeholder)"""
    issues = []
    if len(response) < 50:
        issues.append("Respuesta muy corta")
    if "no sé" in response.lower():
        issues.append("Indica incertidumbre")
    return issues


def example_refiner(
    query: str, 
    current_draft: str, 
    issues: List[str], 
    context: Optional[str]
) -> str:
    """Refinador de ejemplo (placeholder)"""
    refined = current_draft
    for issue in issues:
        if "muy corta" in issue:
            refined += " [Expandiendo respuesta...]"
        if "incertidumbre" in issue:
            refined = refined.replace("no sé", "basándome en la información disponible")
    return refined


if __name__ == "__main__":
    # Ejemplo de uso
    print("=== Claw-Litle 1.0 - Self-Refining Engine ===\n")
    
    engine = get_self_refining_engine({
        "confidence_threshold": 0.85,
        "max_iterations": 3
    })
    
    # Configurar callbacks
    engine.set_generator(example_generator)
    engine.set_critic(example_critic)
    engine.set_refiner(example_refiner)
    
    # Probar con una query
    query = "¿Cuál es la capital de Francia?"
    result = engine.refine(query, context="Geografía básica")
    
    print(f"Query: {query}")
    print(f"Respuesta final: {result.final_answer}")
    print(f"Confianza final: {result.final_confidence:.2%}")
    print(f"Confianza máxima: {result.max_confidence_reached:.2%}")
    print(f"Iteraciones usadas: {result.iterations_used}/{result.max_iterations_allowed}")
    print(f"Tiempo total: {result.total_time_ms:.2f}ms")
    print(f"Razonamiento: {result.reasoning}")
    print(f"Terminó temprano: {result.early_stopped}")