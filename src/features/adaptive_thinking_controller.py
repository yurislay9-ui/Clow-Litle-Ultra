"""
Adaptive Thinking Controller - Claw-Litle 1.0

Controlador que integra el Query Complexity Analyzer con el Agent Router
para determinar dinámicamente el nivel de esfuerzo cognitivo según la consulta.
"""

import time
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ThinkingLevel(Enum):
    """Niveles de esfuerzo cognitivo (Adaptive Thinking System)"""
    RAPIDO = 1        # ~500ms, 1 agente máx
    ESTANDAR = 2      # ~2-3s, 2-3 agentes
    PROFUNDO = 3      # ~8-12s, 4-6 agentes
    MAXIMO = 4        # ~20-30s, todos los agentes + iteraciones


@dataclass
class ThinkingConfig:
    """Configuración para un nivel de pensamiento"""
    level: ThinkingLevel
    max_agents: int
    parallel_execution: bool
    self_refining_enabled: bool
    self_refining_iterations: int
    confidence_threshold: float
    time_budget_ms: int
    memory_budget_mb: int
    thermal_throttle_temp: float  # Temperatura para throttling
    description: str
    
    @classmethod
    def default_configs(cls) -> Dict[ThinkingLevel, "ThinkingConfig"]:
        """Configuraciones por defecto para cada nivel"""
        return {
            ThinkingLevel.RAPIDO: cls(
                level=ThinkingLevel.RAPIDO,
                max_agents=1,
                parallel_execution=False,
                self_refining_enabled=False,
                self_refining_iterations=0,
                confidence_threshold=0.7,
                time_budget_ms=500,
                memory_budget_mb=50,
                thermal_throttle_temp=75.0,
                description="Para preguntas simples y directas"
            ),
            ThinkingLevel.ESTANDAR: cls(
                level=ThinkingLevel.ESTANDAR,
                max_agents=3,
                parallel_execution=True,
                self_refining_enabled=True,
                self_refining_iterations=1,
                confidence_threshold=0.85,
                time_budget_ms=3000,
                memory_budget_mb=100,
                thermal_throttle_temp=70.0,
                description="Para búsquedas y preguntas comunes"
            ),
            ThinkingLevel.PROFUNDO: cls(
                level=ThinkingLevel.PROFUNDO,
                max_agents=6,
                parallel_execution=True,
                self_refining_enabled=True,
                self_refining_iterations=3,
                confidence_threshold=0.92,
                time_budget_ms=12000,
                memory_budget_mb=200,
                thermal_throttle_temp=65.0,
                description="Para análisis complejos y generación de código"
            ),
            ThinkingLevel.MAXIMO: cls(
                level=ThinkingLevel.MAXIMO,
                max_agents=10,
                parallel_execution=True,
                self_refining_enabled=True,
                self_refining_iterations=5,
                confidence_threshold=0.95,
                time_budget_ms=30000,
                memory_budget_mb=300,
                thermal_throttle_temp=60.0,
                description="Para tareas críticas y razonamiento extendido"
            )
        }


@dataclass
class ThinkingDecision:
    """Decisión de nivel de pensamiento para una query"""
    query: str
    determined_level: ThinkingLevel
    complexity_score: float
    confidence: float
    reasoning: str
    config: ThinkingConfig
    overrides_applied: List[str]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa a diccionario"""
        return {
            "query": self.query[:100] + ("..." if len(self.query) > 100 else ""),
            "determined_level": self.determined_level.name,
            "complexity_score": self.complexity_score,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "config": {
                "max_agents": self.config.max_agents,
                "time_budget_ms": self.config.time_budget_ms,
                "self_refining": self.config.self_refining_enabled,
                "self_refining_iterations": self.config.self_refining_iterations
            },
            "overrides_applied": self.overrides_applied,
            "timestamp": self.timestamp.isoformat()
        }


class AdaptiveThinkingController:
    """
    Controlador de Adaptive Thinking para Claw-Litle.
    
    Determina automáticamente el nivel de esfuerzo cognitivo basado en:
    - Complejidad de la query (Query Complexity Analyzer)
    - Estado del sistema (temperatura, memoria disponible)
    - Preferencias del usuario
    - Historial de rendimiento
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Configuraciones por nivel
        self.level_configs = ThinkingConfig.default_configs()
        if "level_configs" in self.config:
            self.level_configs.update(self.config["level_configs"])
        
        # Umbrales de complejidad
        self.thresholds = {
            ThinkingLevel.RAPIDO: 2.5,
            ThinkingLevel.ESTANDAR: 5.0,
            ThinkingLevel.PROFUNDO: 7.5,
            ThinkingLevel.MAXIMO: 10.0
        }
        if "thresholds" in self.config:
            self.thresholds.update(self.config["thresholds"])
        
        # Callbacks
        self.complexity_analyzer_callback: Optional[Callable] = None
        self.thermal_monitor_callback: Optional[Callable] = None
        self.memory_monitor_callback: Optional[Callable] = None
        
        # Historial de decisiones
        self.decision_history: List[ThinkingDecision] = []
        self.max_history = 100
        
        # Estadísticas
        self.stats = {
            "total_decisions": 0,
            "level_distribution": {level.name: 0 for level in ThinkingLevel},
            "avg_complexity_score": 0.0,
            "overrides_applied": 0
        }
    
    def set_complexity_analyzer(self, callback: Callable[[str, Optional[Dict]], Any]):
        """
        Establece el callback para el Query Complexity Analyzer.
        
        Args:
            callback: Función(query, context) -> ComplexityScore
        """
        self.complexity_analyzer_callback = callback
    
    def set_thermal_monitor(self, callback: Callable[[], float]):
        """
        Establece el callback para monitoreo térmico.
        
        Args:
            callback: Función() -> temperatura_celsius
        """
        self.thermal_monitor_callback = callback
    
    def set_memory_monitor(self, callback: Callable[[], float]):
        """
        Establece el callback para monitoreo de memoria.
        
        Args:
            callback: Función() -> memoria_disponible_mb
        """
        self.memory_monitor_callback = callback
    
    def determine_thinking_level(
        self,
        query: str,
        context: Optional[Dict] = None,
        user_preferences: Optional[Dict] = None
    ) -> ThinkingDecision:
        """
        Determina el nivel de pensamiento óptimo para una query.
        
        Args:
            query: Consulta del usuario
            context: Contexto adicional
            user_preferences: Preferencias del usuario (ej: "siempre rápido")
        
        Returns:
            ThinkingDecision con la decisión y configuración
        """
        start_time = time.time()
        overrides_applied = []
        
        # 1. Obtener complejidad de la query
        complexity_score = 5.0  # Default
        confidence = 0.5
        reasoning_parts = []
        
        if self.complexity_analyzer_callback:
            try:
                analysis = self.complexity_analyzer_callback(query, context)
                complexity_score = analysis.score
                confidence = analysis.confidence
                reasoning_parts.append(f"Análisis complejidad: {analysis.reasoning}")
            except Exception as e:
                reasoning_parts.append(f"Error en análisis: {str(e)}")
        else:
            # Fallback: análisis simple por longitud
            if len(query) < 30:
                complexity_score = 2.0
            elif len(query) < 100:
                complexity_score = 5.0
            else:
                complexity_score = 7.5
            confidence = 0.3
        
        # 2. Determinar nivel base por complejidad
        determined_level = self._level_from_score(complexity_score)
        reasoning_parts.append(f"Nivel base: {determined_level.name}")
        
        # 3. Aplicar preferencias de usuario
        if user_preferences:
            if user_preferences.get("prefer_fast", False):
                determined_level = min(determined_level, ThinkingLevel.ESTANDAR)
                overrides_applied.append("prefer_fast")
                reasoning_parts.append("Usuario prefiere velocidad")
            
            if user_preferences.get("prefer_accurate", False):
                determined_level = max(determined_level, ThinkingLevel.PROFUNDO)
                overrides_applied.append("prefer_accurate")
                reasoning_parts.append("Usuario prefiere precisión")
            
            if user_preferences.get("battery_saver", False):
                determined_level = min(determined_level, ThinkingLevel.RAPIDO)
                overrides_applied.append("battery_saver")
                reasoning_parts.append("Modo ahorro batería")
        
        # 4. Verificar estado térmico
        if self.thermal_monitor_callback:
            try:
                temp = self.thermal_monitor_callback()
                if temp > 75.0:
                    determined_level = min(determined_level, ThinkingLevel.RAPIDO)
                    overrides_applied.append("thermal_throttle_critical")
                    reasoning_parts.append(f"Temperatura crítica: {temp:.1f}°C")
                elif temp > 65.0:
                    determined_level = min(determined_level, ThinkingLevel.ESTANDAR)
                    overrides_applied.append("thermal_throttle_warning")
                    reasoning_parts.append(f"Temperatura alta: {temp:.1f}°C")
            except Exception as e:
                reasoning_parts.append(f"Error monitor térmico: {str(e)}")
        
        # 5. Verificar memoria disponible
        if self.memory_monitor_callback:
            try:
                available_mb = self.memory_monitor_callback()
                config = self.level_configs[determined_level]
                if available_mb < config.memory_budget_mb * 1.5:
                    determined_level = min(determined_level, ThinkingLevel.ESTANDAR)
                    overrides_applied.append("memory_constraint")
                    reasoning_parts.append(f"Memoria limitada: {available_mb:.0f}MB")
            except Exception as e:
                reasoning_parts.append(f"Error monitor memoria: {str(e)}")
        
        # 6. Obtener configuración final
        final_config = self.level_configs[determined_level]
        
        # 7. Crear decisión
        reasoning = " | ".join(reasoning_parts)
        decision = ThinkingDecision(
            query=query,
            determined_level=determined_level,
            complexity_score=complexity_score,
            confidence=confidence,
            reasoning=reasoning,
            config=final_config,
            overrides_applied=overrides_applied
        )
        
        # 8. Actualizar estadísticas
        self._update_stats(decision)
        
        return decision
    
    def _level_from_score(self, score: float) -> ThinkingLevel:
        """Convierte puntuación de complejidad a nivel de pensamiento"""
        for level in [ThinkingLevel.MAXIMO, ThinkingLevel.PROFUNDO, 
                      ThinkingLevel.ESTANDAR, ThinkingLevel.RAPIDO]:
            if score > self.thresholds[level]:
                return level
        return ThinkingLevel.RAPIDO
    
    def _update_stats(self, decision: ThinkingDecision):
        """Actualiza las estadísticas"""
        self.stats["total_decisions"] += 1
        self.stats["level_distribution"][decision.determined_level.name] += 1
        
        if decision.overrides_applied:
            self.stats["overrides_applied"] += 1
        
        # Actualizar promedio móvil
        n = self.stats["total_decisions"]
        old_avg = self.stats["avg_complexity_score"]
        self.stats["avg_complexity_score"] = ((old_avg * (n - 1)) + decision.complexity_score) / n
        
        # Guardar en historial
        self.decision_history.append(decision)
        if len(self.decision_history) > self.max_history:
            self.decision_history.pop(0)
    
    def get_recommendation(
        self,
        query: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Obtiene una recomendación completa para el router.
        
        Args:
            query: Consulta del usuario
            context: Contexto adicional
        
        Returns:
            Diccionario con recomendación para el router
        """
        decision = self.determine_thinking_level(query, context)
        
        return {
            "thinking_level": decision.determined_level.name,
            "thinking_level_value": decision.determined_level.value,
            "max_agents": decision.config.max_agents,
            "parallel_execution": decision.config.parallel_execution,
            "self_refining_enabled": decision.config.self_refining_enabled,
            "self_refining_iterations": decision.config.self_refining_iterations,
            "confidence_threshold": decision.config.confidence_threshold,
            "time_budget_ms": decision.config.time_budget_ms,
            "memory_budget_mb": decision.config.memory_budget_mb,
            "complexity_score": decision.complexity_score,
            "reasoning": decision.reasoning,
            "overrides_applied": decision.overrides_applied,
            "estimated_time_s": decision.config.time_budget_ms / 1000
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del controller"""
        return {
            **self.stats,
            "recent_decisions": [d.to_dict() for d in self.decision_history[-10:]],
            "thresholds": {k.name: v for k, v in self.thresholds.items()}
        }
    
    def reset_stats(self):
        """Resetea las estadísticas"""
        self.stats = {
            "total_decisions": 0,
            "level_distribution": {level.name: 0 for level in ThinkingLevel},
            "avg_complexity_score": 0.0,
            "overrides_applied": 0
        }
        self.decision_history = []


# Instancia global
_controller: Optional[AdaptiveThinkingController] = None


def get_adaptive_thinking_controller(config: Optional[Dict] = None) -> AdaptiveThinkingController:
    """Obtiene la instancia global del controller"""
    global _controller
    if _controller is None:
        _controller = AdaptiveThinkingController(config)
    return _controller


def get_thinking_recommendation(
    query: str,
    context: Optional[Dict] = None
) -> Dict[str, Any]:
    """Función helper para obtener recomendación de thinking"""
    return get_adaptive_thinking_controller().get_recommendation(query, context)


# Ejemplo de integración con el router existente
def integrate_with_router(router_instance, query: str, context: Optional[Dict] = None):
    """
    Ejemplo de cómo integrar el Adaptive Thinking con el router existente.
    
    Args:
        router_instance: Instancia del router de Claw-Litle
        query: Consulta del usuario
        context: Contexto adicional
    """
    controller = get_adaptive_thinking_controller()
    recommendation = controller.get_recommendation(query, context)
    
    # El router usaría esta recomendación para:
    # 1. Limitar el número de agentes
    # 2. Habilitar/deshabilitar self-refining
    # 3. Ajustar timeouts
    # 4. Gestionar ejecución paralela
    
    return recommendation


if __name__ == "__main__":
    # Ejemplo de uso
    print("=== Claw-Litle 1.0 - Adaptive Thinking Controller ===\n")
    
    controller = get_adaptive_thinking_controller()
    
    # Configurar callbacks de ejemplo
    def mock_complexity_analyzer(query, context):
        class MockAnalysis:
            score = min(10.0, len(query) / 20)
            confidence = 0.8
            reasoning = f"Longitud: {len(query)} chars"
        return MockAnalysis()
    
    controller.set_complexity_analyzer(mock_complexity_analyzer)
    
    # Test con diferentes queries
    test_queries = [
        "¿Qué hora es?",
        "Busca precios de iPhone 15",
        "Genera un scraper para Amazon",
        "Analiza tendencias IA 2025 y genera reporte PDF",
        "Primero busca React, luego compara con Vue, finalmente genera tabla comparativa"
    ]
    
    for query in test_queries:
        recommendation = controller.get_recommendation(query)
        print(f"Query: '{query[:50]}{'...' if len(query) > 50 else ''}'")
        print(f"  Nivel: {recommendation['thinking_level']}")
        print(f"  Agentes máx: {recommendation['max_agents']}")
        print(f"  Self-refining: {recommendation['self_refining_enabled']}")
        print(f"  Tiempo estimado: {recommendation['estimated_time_s']}s")
        print(f"  Razón: {recommendation['reasoning']}")
        print()
    
    print("\n=== Estadísticas ===")
    stats = controller.get_stats()
    print(f"Total decisiones: {stats['total_decisions']}")
    print(f"Distribución: {stats['level_distribution']}")
    print(f"Overrides aplicados: {stats['overrides_applied']}")