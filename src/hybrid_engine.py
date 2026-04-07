"""
Claw-Litle 1.0
hybrid_engine.py - 4-Level Hybrid Engine

Main intention recognition engine optimized for ARM64.
Implements short-circuit evaluation to save battery and resources.
"""

import logging
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

# Lazy loading de motores para evitar errores de importación
def _import_regex_engine():
    from .engine.nivel_1_regex import RegexEngine
    return RegexEngine

def _import_fuzzy_engine():
    from .engine.nivel_2_fuzzy import FuzzyEngine
    return FuzzyEngine

def _import_semantic_engine():
    from .engine.nivel_3_semantic import SemanticEngine
    return SemanticEngine

def _import_expert_engine():
    from .engine.nivel_4_expert import ExpertEngine
    return ExpertEngine

logger = logging.getLogger(__name__)


@dataclass
class IntentResult:
    """Resultado del procesamiento de intención."""
    intent_name: str
    confidence: float
    level_reached: int  # 1-4 (nivel del motor donde se detectó)
    metadata: Dict = field(default_factory=dict)
    processing_time_ms: float = 0.0


class HybridEngine:
    """
    Motor Híbrido 4-Niveles para reconocimiento de intenciones.
    
    Niveles:
    1. Regex (~0ms) - Patrones exactos conocidos
    2. Fuzzy (~1-2ms) - Coincidencia aproximada con RapidFuzz
    3. Semantic (~5-15ms) - Embeddings ONNX MiniLM
    4. Expert Rules (siempre) - Validación final con reglas expertas
    
    Short-circuit: Se detiene en el primer nivel con confidence > threshold.
    """
    
    def __init__(self, config: Dict):
        """
        Inicializa el motor híbrido.
        
        Args:
            config: Configuración del motor desde defaults.toml
        """
        self.config = config
        self.short_circuit_threshold = config.get('short_circuit_threshold', 0.95)
        
        # Inicializar motores (lazy loading para ahorrar RAM)
        self._regex_engine = None
        self._fuzzy_engine = None
        self._semantic_engine = None
        self._expert_engine = None
        
        # Estado de inicialización
        self._initialized = False
        self._models_loaded = False
        
        logger.info("HybridEngine inicializado (lazy loading activado)")
    
    def _ensure_initialized(self, intents_registry: Dict):
        """Inicializa los motores bajo demanda."""
        if self._initialized:
            return
            
        logger.debug("Inicializando motores del HybridEngine...")
        
        # Nivel 1: Regex (siempre disponible)
        if self.config.get('regex_enabled', True):
            RegexEngine = _import_regex_engine()
            self._regex_engine = RegexEngine(intents_registry)
        
        # Nivel 2: Fuzzy (siempre disponible)
        if self.config.get('fuzzy_enabled', True):
            FuzzyEngine = _import_fuzzy_engine()
            self._fuzzy_engine = FuzzyEngine(
                intents_registry,
                threshold=self.config.get('fuzzy_threshold', 0.85)
            )
        
        # Nivel 3: Semantic (lazy loading - solo si hay RAM suficiente)
        if self.config.get('semantic_enabled', True):
            # Verificar memoria antes de cargar modelo ONNX (sin psutil para Termux)
            available_ram_mb = self._get_available_ram_mb()
            
            if available_ram_mb > 500:  # Mínimo 500MB libres
                try:
                    SemanticEngine = _import_semantic_engine()
                    self._semantic_engine = SemanticEngine(
                        model_path=self.config.get('semantic_model_path'),
                        threshold=self.config.get('semantic_threshold', 0.89)
                    )
                    self._models_loaded = True
                    logger.info("Modelo ONNX cargado exitosamente")
                except Exception as e:
                    logger.warning(f"No se pudo cargar modelo ONNX: {e}. Usando solo niveles 1-2-4")
            else:
                logger.warning(f"RAM insuficiente ({available_ram_mb:.0f}MB). Desactivando nivel semántico.")
        
        # Nivel 4: Expert Rules (siempre disponible)
        if self.config.get('expert_rules_enabled', True):
            ExpertEngine = _import_expert_engine()
            self._expert_engine = ExpertEngine(intents_registry)
        
        self._initialized = True
        logger.info("HybridEngine completamente inicializado")
    
    def process(
        self, 
        query: str, 
        intents_registry: Dict,
        user_context: Optional[Dict] = None
    ) -> IntentResult:
        """
        Procesa una query a través de los 4 niveles del motor.
        
        Args:
            query: Texto de entrada del usuario
            intents_registry: Registro de intenciones disponibles
            user_context: Contexto adicional del usuario (opcional)
        
        Returns:
            IntentResult con la intención detectada y metadata
        """
        start_time = time.time()
        
        # Asegurar inicialización
        self._ensure_initialized(intents_registry)
        
        result = None
        
        # NIVEL 1: Regex Filter (~0ms)
        if self._regex_engine:
            result = self._regex_engine.match(query)
            if result and result.confidence >= self.short_circuit_threshold:
                result.level_reached = 1
                result.processing_time_ms = (time.time() - start_time) * 1000
                logger.debug(f"Nivel 1 (Regex): {result.intent_name} ({result.confidence:.2%})")
                return result
        
        # NIVEL 2: Fuzzy Matching (~1-2ms)
        if self._fuzzy_engine:
            result = self._fuzzy_engine.match(query)
            if result and result.confidence >= self.short_circuit_threshold:
                result.level_reached = 2
                result.processing_time_ms = (time.time() - start_time) * 1000
                logger.debug(f"Nivel 2 (Fuzzy): {result.intent_name} ({result.confidence:.2%})")
                return result
        
        # NIVEL 3: Semantic Embeddings (~5-15ms)
        if self._semantic_engine and self._models_loaded:
            result = self._semantic_engine.match(query)
            if result and result.confidence >= self.short_circuit_threshold:
                result.level_reached = 3
                result.processing_time_ms = (time.time() - start_time) * 1000
                logger.debug(f"Nivel 3 (Semantic): {result.intent_name} ({result.confidence:.2%})")
                return result
        
        # NIVEL 4: Expert Rules (siempre se ejecuta)
        if self._expert_engine:
            expert_result = self._expert_engine.validate(query, result, user_context)
            if expert_result:
                result = expert_result
            
            result.level_reached = 4
            result.processing_time_ms = (time.time() - start_time) * 1000
            logger.debug(f"Nivel 4 (Expert): {result.intent_name} ({result.confidence:.2%})")
            return result
        
        # Fallback: Si nada funcionó
        result = IntentResult(
            intent_name="unknown",
            confidence=0.0,
            level_reached=4,
            metadata={"error": "No intent matched"},
            processing_time_ms=(time.time() - start_time) * 1000
        )
        
        logger.warning(f"Query no reconocida: '{query[:50]}...'")
        return result
    
    def get_stats(self) -> Dict:
        """Retorna estadísticas del motor."""
        return {
            "initialized": self._initialized,
            "models_loaded": self._models_loaded,
            "short_circuit_threshold": self.short_circuit_threshold,
            "levels_enabled": {
                "regex": self._regex_engine is not None,
                "fuzzy": self._fuzzy_engine is not None,
                "semantic": self._semantic_engine is not None,
                "expert": self._expert_engine is not None
            }
        }
    
    def unload_models(self):
        """Libera memoria descargando modelos ONNX (útil para modo ahorro)."""
        if self._semantic_engine:
            self._semantic_engine.unload()
            self._models_loaded = False
            logger.info("Modelos ONNX descargados - RAM liberada")
    
    def reload_models(self):
        """Recarga modelos ONNX (útil cuando hay RAM disponible)."""
        if self._semantic_engine:
            self._semantic_engine.load()
            self._models_loaded = True
        logger.info("Modelos ONNX recargados")
    
    def _get_available_ram_mb(self) -> float:
        """
        Obtiene la RAM disponible en MB sin depender de psutil.
        Compatible con Termux ARM64.
        
        Returns:
            MB de RAM disponible
        """
        try:
            # Método 1: Leer de /proc/meminfo (Linux/Android)
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
            
            for line in meminfo.split('\n'):
                if line.startswith('MemAvailable:'):
                    # Formato: "MemAvailable:    1234567 kB"
                    parts = line.split()
                    if len(parts) >= 2:
                        kb = int(parts[1])
                        return kb / 1024.0  # Convertir a MB
            
            # Método 2: Si no hay MemAvailable, usar MemFree + Buffers + Cached
            mem_free = 0
            buffers = 0
            cached = 0
            
            for line in meminfo.split('\n'):
                if line.startswith('MemFree:'):
                    mem_free = int(line.split()[1])
                elif line.startswith('Buffers:'):
                    buffers = int(line.split()[1])
                elif line.startswith('Cached:'):
                    cached = int(line.split()[1])
            
            if mem_free > 0:
                return (mem_free + buffers + cached) / 1021.0
                
        except Exception:
            pass
        
        # Método 3: Fallback - usar resource (disponible en Termux)
        try:
            import resource
            # Obtener límite de memoria del proceso
            mem_limit = resource.getrlimit(resource.RLIMIT_AS)
            if mem_limit[1] != resource.RLIM_INFINITY:
                return mem_limit[1] / (1024 * 1024)
        except Exception:
            pass
        
        # Fallback final: asumir 1000MB disponibles (conservador)
        logger.warning("No se pudo determinar RAM disponible, asumiendo 1000MB")
        return 1000.0
