"""
Claw-Litle 1.0
router.py - Router de Intenciones (Capa 2)

Descompone la intención del usuario y despacha a los subsistemas correctos.
Actúa como orquestador central del sistema.
"""

import logging
import time
import hashlib
from typing import Dict, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field

from .hybrid_engine import HybridEngine, IntentResult
from .gateway import Gateway, SecurityConfig, Request, Response as GatewayResponse

logger = logging.getLogger(__name__)

# Importaciones para integración con módulos mejorados
ENHANCED_MODULES_AVAILABLE = False
try:
    from .intent_classifier import get_classifier, ClassifiedIntent
    from .personality_engine import get_personality, get_formatter
    ENHANCED_MODULES_AVAILABLE = True
except ImportError as e:
    logger.debug(f"Módulos mejorados no disponibles: {e}. Usando fallback básico")
except Exception as e:
    logger.debug(f"Error cargando módulos mejorados: {e}. Usando fallback básico")


@dataclass
class RouterResult:
    """Resultado del routing."""
    intent: str
    action: str
    data: Any = None
    success: bool = True
    error: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    processing_time_ms: float = 0.0


@dataclass
class RouterConfig:
    """Configuración del router."""
    max_retries: int = 3
    timeout_seconds: int = 30
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600
    fallback_to_search: bool = True


@dataclass
class CacheEntry:
    """Entrada de cache con TTL."""
    result: RouterResult
    created_at: float
    ttl_seconds: int
    
    def is_expired(self) -> bool:
        """Verifica si la entrada ha expirado."""
        return (time.time() - self.created_at) > self.ttl_seconds


class Router:
    """
    Router de Intenciones - Capa 2.
    
    Responsabilidades:
    1. Recibir intención del HybridEngine
    2. Descomponer intención compleja
    3. Despachar a agentes/subsistemas
    4. Consolidar resultados
    5. Manejar errores y reintentos
    """
    
    def __init__(
        self, 
        engine: HybridEngine, 
        gateway: Gateway,
        config: RouterConfig = None
    ):
        """
        Inicializa el router.
        
        Args:
            engine: Motor híbrido 4-niveles
            gateway: Gateway de seguridad
            config: Configuración del router
        """
        self.engine = engine
        self.gateway = gateway
        self._cache: Dict[str, CacheEntry] = {}
        self.config = config or RouterConfig()
        
        # Registry de handlers
        self._handlers: Dict[str, Callable] = {}
        self._register_default_handlers()
        
        # Cache de resultados
        self._cache: Dict[str, Any] = {}
        
        logger.info("Router inicializado")
    
    def _register_default_handlers(self):
        """Registra handlers por defecto."""
        # Handlers inline (respuestas directas)
        self._handlers["greet"] = self._handle_greet
        self._handlers["farewell"] = self._handle_farewell
        self._handlers["help"] = self._handle_help
        
        # Handlers que requieren agentes
        self._handlers["web_search"] = self._handle_web_search
        self._handlers["code_generation"] = self._handle_code_generation
        self._handlers["code_repair"] = self._handle_code_repair
        
        # Handlers de sistema
        self._handlers["system_status"] = self._handle_system_status
        self._handlers["clear_cache"] = self._handle_clear_cache
        self._handlers["thermal_info"] = self._handle_thermal_info
        
        # Handlers especiales
        self._handlers["question"] = self._handle_question
        self._handlers["cancel"] = self._handle_cancel
        self._handlers["confirm"] = self._handle_confirm
        self._handlers["fallback"] = self._handle_fallback
    
    def route(
        self, 
        query: str, 
        user_id: str = "anonymous",
        user_context: Dict = None
    ) -> RouterResult:
        """
        Procesa una query completa a través del sistema.
        
        Flujo:
        1. Gateway (sanitización, rate limiting)
        2. HybridEngine (reconocimiento de intención)
        3. Router (despacho a handler)
        4. Handler (ejecución)
        
        Args:
            query: Query del usuario
            user_id: ID del usuario
            user_context: Contexto adicional
        
        Returns:
            RouterResult con el resultado
        """
        start_time = time.time()
        
        # 1. Gateway - Seguridad
        gateway_response = self.gateway.process(
            Request(user_id=user_id, query=query),
            user_tier=user_context.get("tier", "free") if user_context else "free"
        )
        
        if not gateway_response.success:
            return RouterResult(
                intent="error",
                action="gateway_rejected",
                success=False,
                error=gateway_response.error,
                processing_time_ms=(time.time() - start_time) * 1000
            )
        
        # Query sanitizada
        sanitized_query = gateway_response.data["query"]
        
        # 2. Check cache con TTL
        cache_key = self._generate_cache_key(user_id, sanitized_query)
        if self.config.enable_caching and cache_key in self._cache:
            entry = self._cache[cache_key]
            if not entry.is_expired():
                cached_result = entry.result
                cached_result.metadata["cached"] = True
                cached_result.processing_time_ms = (time.time() - start_time) * 1000
                return cached_result
            else:
                # Eliminar entrada expirada
                del self._cache[cache_key]
                logger.debug(f"Cache entry expired: {cache_key}")
        
        # 3. HybridEngine - Reconocimiento de intención
        intents_registry = self._load_intents_registry()
        intent_result = self.engine.process(
            sanitized_query, 
            intents_registry,
            user_context
        )
        
        # 4. Router - Despacho a handler
        handler = self._handlers.get(intent_result.intent_name, self._handle_fallback)
        
        try:
            result = handler(sanitized_query, intent_result, user_context)
        except Exception as e:
            logger.error(f"Error en handler {intent_result.intent_name}: {e}")
            result = RouterResult(
                intent=intent_result.intent_name,
                action="error",
                success=False,
                error=str(e),
                processing_time_ms=(time.time() - start_time) * 1000
            )
        
        # 5. Cache resultado con TTL (si es exitoso)
        if self.config.enable_caching and result.success:
            self._cache[cache_key] = CacheEntry(
                result=result,
                created_at=time.time(),
                ttl_seconds=self.config.cache_ttl_seconds
            )
        
        result.processing_time_ms = (time.time() - start_time) * 1000
        return result
    
    def _generate_cache_key(self, user_id: str, query: str) -> str:
        """Genera clave de cache con hash para evitar colisiones."""
        key_data = f"{user_id}:{query}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:32]
    
    def _load_intents_registry(self) -> Dict:
        """Carga el registro de intenciones."""
        import json
        from pathlib import Path
        
        registry_path = Path("src/config/intents_registry.json")
        try:
            with open(registry_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error cargando intents_registry: {e}")
            return {"intents": [], "fallback": {"type": "agent", "details": {}}}
    
    # ==================== HANDLERS ====================
    
    def _handle_greet(self, query: str, intent: IntentResult, context: Dict) -> RouterResult:
        """Maneja saludos con personalidad mejorada."""
        if ENHANCED_MODULES_AVAILABLE:
            try:
                personality = get_personality()
                greeting = personality.get_greeting()
                return RouterResult(
                    intent="greet",
                    action="respond",
                    data=greeting,
                    metadata={"enhanced": True}
                )
            except Exception as e:
                logger.warning(f"Error obteniendo saludo mejorado: {e}")
        
        return RouterResult(
            intent="greet",
            action="respond",
            data="¡Hola! Soy Claw-Litle 1.0 1.0. ¿En qué puedo ayudarte hoy?"
        )
    
    def _handle_farewell(self, query: str, intent: IntentResult, context: Dict) -> RouterResult:
        """Maneja despedidas con personalidad."""
        farewell = "¡Hasta pronto! Recuerda que estoy aquí para ayudarte cuando me necesites."
        
        if ENHANCED_MODULES_AVAILABLE:
            try:
                personality = get_personality()
                farewell = personality.format_completion(
                    action="despedida",
                    explanation="Ha sido un placer ayudarte hoy"
                )
            except Exception as e:
                logger.warning(f"Error formateando despedida: {e}")
        
        return RouterResult(
            intent="farewell",
            action="respond",
            data=farewell
        )
    
    def _handle_help(self, query: str, intent: IntentResult, context: Dict) -> RouterResult:
        """Maneja ayuda con formato mejorado."""
        help_text = """🔧 **COMANDOS DISPONIBLES:**

**Búsquedas:**
  • `buscar [término]` - Búsqueda web multi-agente
  • `info [término]` - Búsqueda semántica local

**Código:**
  • `crear [app/script]` - Generar código Python
  • `reparar [código]` - Auto-corregir código

**Sistema:**
  • `status` - Ver estado del sistema
  • `doctor` - Diagnóstico completo
  • `limpiar` - Limpiar caché

**Ayuda:**
  • `help` - Esta ayuda
  • `exit` - Salir del sistema
"""
        # Añadir preguntas de seguimiento si los módulos mejorados están disponibles
        if ENHANCED_MODULES_AVAILABLE:
            try:
                personality = get_personality()
                follow_ups = personality.get_follow_up_questions("help")
                if follow_ups:
                    help_text += "\n💡 **¿Sabías que puedes?**\n"
                    for q in follow_ups[:2]:
                        help_text += f"  • {q}\n"
            except Exception as e:
                logger.warning(f"Error añadiendo preguntas de seguimiento: {e}")
        
        return RouterResult(
            intent="help",
            action="respond",
            data=help_text
        )
    
    def _handle_web_search(self, query: str, intent: IntentResult, context: Dict) -> RouterResult:
        """Maneja búsquedas web."""
        # Extraer término de búsqueda
        search_term = query.replace("buscar", "").replace("busca", "").strip()
        
        if not search_term:
            return RouterResult(
                intent="web_search",
                action="error",
                success=False,
                error="No se especificó término de búsqueda"
            )
        
        # Despachar a swarm_manager (simulado por ahora)
        return RouterResult(
            intent="web_search",
            action="dispatch",
            data={
                "agent": "swarm_manager",
                "action": "multi_agent_search",
                "query": search_term,
                "status": "pending"
            },
            metadata={"search_term": search_term}
        )
    
    def _handle_code_generation(self, query: str, intent: IntentResult, context: Dict) -> RouterResult:
        """Maneja generación de código."""
        # Extraer descripción del código
        code_desc = query.replace("crear", "").replace("hazme", "").replace("genera", "").strip()
        
        if not code_desc:
            return RouterResult(
                intent="code_generation",
                action="error",
                success=False,
                error="No se especificó qué código crear"
            )
        
        return RouterResult(
            intent="code_generation",
            action="dispatch",
            data={
                "agent": "code_gen_engine",
                "action": "generate_code",
                "description": code_desc,
                "status": "pending"
            },
            metadata={"description": code_desc}
        )
    
    def _handle_code_repair(self, query: str, intent: IntentResult, context: Dict) -> RouterResult:
        """Maneja reparación de código."""
        return RouterResult(
            intent="code_repair",
            action="dispatch",
            data={
                "agent": "self_healing_engine",
                "action": "heal_code",
                "query": query,
                "status": "pending"
            }
        )
    
    def _handle_system_status(self, query: str, intent: IntentResult, context: Dict) -> RouterResult:
        """Maneja estado del sistema."""
        status = {
            "engine_stats": self.engine.get_stats(),
            "gateway_stats": self.gateway.get_stats(),
            "cache_size": len(self._cache),
            "handlers_registered": len(self._handlers)
        }
        
        return RouterResult(
            intent="system_status",
            action="respond",
            data=status
        )
    
    def _handle_clear_cache(self, query: str, intent: IntentResult, context: Dict) -> RouterResult:
        """Maneja limpieza de caché."""
        cleared = len(self._cache)
        self._cache.clear()
        
        return RouterResult(
            intent="clear_cache",
            action="respond",
            data=f"Caché limpiada. {cleared} entradas eliminadas."
        )
    
    def _handle_thermal_info(self, query: str, intent: IntentResult, context: Dict) -> RouterResult:
        """Maneja información térmica."""
        # Simulado - en producción leer de /sys/class/thermal/
        thermal_info = {
            "cpu_temp": "45°C",
            "status": "normal",
            "throttling": False,
            "max_agents": 2
        }
        
        return RouterResult(
            intent="thermal_info",
            action="respond",
            data=thermal_info
        )
    
    def _handle_question(self, query: str, intent: IntentResult, context: Dict) -> RouterResult:
        """Maneja preguntas abiertas."""
        # Despachar a búsqueda semántica
        return RouterResult(
            intent="question",
            action="dispatch",
            data={
                "agent": "semantic_searcher",
                "action": "answer_question",
                "question": query,
                "status": "pending"
            }
        )
    
    def _handle_cancel(self, query: str, intent: IntentResult, context: Dict) -> RouterResult:
        """Maneja cancelación."""
        return RouterResult(
            intent="cancel",
            action="respond",
            data="Operación cancelada."
        )
    
    def _handle_confirm(self, query: str, intent: IntentResult, context: Dict) -> RouterResult:
        """Maneja confirmación."""
        return RouterResult(
            intent="confirm",
            action="respond",
            data="Confirmado. Procediendo..."
        )
    
    def _handle_fallback(self, query: str, intent: IntentResult, context: Dict) -> RouterResult:
        """Maneja fallback cuando no se reconoce la intención."""
        if self.config.fallback_to_search:
            return RouterResult(
                intent="fallback",
                action="dispatch",
                data={
                    "agent": "swarm_manager",
                    "action": "multi_agent_search",
                    "query": query,
                    "status": "pending",
                    "reason": "fallback"
                }
            )
        
        return RouterResult(
            intent="fallback",
            action="respond",
            data="No entendí tu consulta. ¿Podrías reformularla o usar 'help' para ver comandos disponibles?"
        )
    
    def clear_cache(self):
        """Limpia el caché del router."""
        self._cache.clear()
        logger.info("Caché del router limpiada")
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas del router."""
        return {
            "cache_size": len(self._cache),
            "handlers_count": len(self._handlers),
            "config": {
                "max_retries": self.config.max_retries,
                "timeout_seconds": self.config.timeout_seconds,
                "enable_caching": self.config.enable_caching,
                "cache_ttl_seconds": self.config.cache_ttl_seconds
            }
        }