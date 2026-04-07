"""
Claw-Lite Ultra Pro - Intent Classifier Mejorado
Módulo de clasificación de intenciones con preguntas inteligentes y memoria contextual
Versión: 1.0.0
"""

import re
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)

# Importar rapidfuzz solo si está disponible (opcional para Termux)
try:
    from rapidfuzz import fuzz, process
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False
    logger.debug("rapidfuzz no disponible, usando fallback nativo")
    
    # Fallback nativo para similitud de strings
    def _levenshtein_distance(s1: str, s2: str) -> int:
        if len(s1) < len(s2):
            return _levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]
    
    class _FuzzMock:
        @staticmethod
        def ratio(s1: str, s2: str) -> int:
            if not s1 or not s2:
                return 0
            s1, s2 = s1.lower(), s2.lower()
            if s1 == s2:
                return 100
            distance = _levenshtein_distance(s1, s2)
            max_len = max(len(s1), len(s2))
            return int((1 - distance / max_len) * 100)
    
    class _ProcessMock:
        @staticmethod
        def extractOne(query: str, choices: List[str], score_cutoff: int = 0) -> Optional[Tuple[str, int, int]]:
            if not choices:
                return None
            best = max(choices, key=lambda c: _FuzzMock.ratio(query, c))
            score = _FuzzMock.ratio(query, best)
            if score >= score_cutoff:
                return (best, score, choices.index(best))
            return None
    
    fuzz = _FuzzMock()
    process = _ProcessMock()


class IntentCategory(Enum):
    """Categorías principales de intenciones"""
    WEB_SEARCH = "web_search"
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    VISION_TASK = "vision_task"
    SYSTEM_QUERY = "system_query"
    SCHEDULED_TASK = "scheduled_task"
    TASK_MANAGEMENT = "task_management"
    EXPLANATION = "explanation"
    CONVERSATIONAL = "conversational"
    UNKNOWN = "unknown"


@dataclass
class ConversationContext:
    """Contexto de conversación actual"""
    user_id: str
    current_topic: str = ""
    last_intent: str = ""
    last_entities: Dict[str, Any] = field(default_factory=dict)
    pending_questions: List[str] = field(default_factory=list)
    conversation_turns: int = 0
    session_start: datetime = field(default_factory=datetime.now)
    context_window: List[Dict] = field(default_factory=list)  # Últimas 10 interacciones


@dataclass
class ClassifiedIntent:
    """Resultado de clasificación de intención"""
    intent: IntentCategory
    confidence: float
    original_query: str
    normalized_query: str
    entities: Dict[str, Any] = field(default_factory=dict)
    requires_clarification: bool = False
    clarification_questions: List[str] = field(default_factory=list)
    suggested_actions: List[str] = field(default_factory=list)
    context_used: bool = False
    reasoning: str = ""


class QuestionGenerator:
    """Generador de preguntas inteligentes basado en contexto"""
    
    # Plantillas de preguntas por tipo de intención
    QUESTION_TEMPLATES = {
        IntentCategory.WEB_SEARCH: [
            "¿Qué información específica buscas sobre {topic}?",
            "¿Necesitas resultados recientes o información general?",
            "¿Prefieres fuentes en español o inglés?",
            "¿Quieres que profundice en algún aspecto en particular?",
        ],
        IntentCategory.CODE_GENERATION: [
            "¿Qué lenguaje de programación prefieres? (Python, JavaScript, etc.)",
            "¿Dónde se ejecutará el código? (Termux, web, desktop)",
            "¿Necesitas que incluya tests automáticos?",
            "¿Quieres que lo prepare para ejecución automática?",
            "¿Prefieres código minimalista o con muchas explicaciones?",
        ],
        IntentCategory.VISION_TASK: [
            "¿Qué app específica quieres que revise?",
            "¿Qué tipo de información necesitas extraer?",
            "¿Tienes permisos de accesibilidad activados?",
            "¿Quieres que guarde los datos extraídos?",
        ],
        IntentCategory.SCHEDULED_TASK: [
            "¿Con qué frecuencia debe ejecutarse? (diaria, semanal, mensual)",
            "¿A qué hora específica prefieres que se ejecute?",
            "¿Quieres recibir notificaciones al completarse?",
            "¿Debe ejecutarse incluso sin conexión a internet?",
        ],
        IntentCategory.SYSTEM_QUERY: [
            "¿Quieres que verifique algún componente específico?",
            "¿Necesitas un reporte detallado o resumen rápido?",
            "¿Quieres que intente corregir los problemas automáticamente?",
        ],
    }
    
    # Palabras clave que indican necesidad de más información
    AMBIGUITY_TRIGGERS = [
        "cosa", "algo", "esto", "eso", "aquello",
        "rápido", "fácil", "simple", "básico",
        "como antes", "como siempre", "como la otra vez",
    ]
    
    def __init__(self):
        self.entity_patterns = {
            "programming_language": r"\b(python|javascript|java|c\+\+|rust|go|typescript|php|ruby)\b",
            "framework": r"\b(flask|django|fastapi|react|vue|angular|express|spring|laravel)\b",
            "database": r"\b(sqlite|postgresql|mysql|mongodb|redis|firebase)\b",
            "platform": r"\b(termux|android|web|desktop|docker|raspberry|vps)\b",
            "frequency": r"\b(diario|semanal|mensual|cada\s+\d+\s+(hora|minuto|día)|cron)\b",
            "time": r"\b(\d{1,2}(:\d{2})?\s*(am|pm|horas)?|mañana|tarde|noche|mediodía)\b",
            "website": r"\b(https?://[^\s]+|amazon|google|github|stackoverflow|youtube)\b",
            "data_type": r"\b(precios|productos|usuarios|datos|información|texto|imágenes)\b",
        }
    
    def extract_entities(self, query: str) -> Dict[str, Any]:
        """Extrae entidades relevantes de la consulta"""
        entities = {}
        query_lower = query.lower()
        
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, query_lower, re.IGNORECASE)
            if matches:
                entities[entity_type] = list(set(matches))
        
        return entities
    
    def detect_ambiguity(self, query: str, entities: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Detecta si la consulta es ambigua y necesita clarificación"""
        is_ambiguous = False
        reasons = []
        query_lower = query.lower()
        
        # Verificar triggers de ambigüedad
        for trigger in self.AMBIGUITY_TRIGGERS:
            if trigger in query_lower:
                is_ambiguous = True
                reasons.append(f"Contiene término vago: '{trigger}'")
        
        # Verificar si faltan entidades críticas según el tipo de intención
        if not entities.get("programming_language") and any(kw in query_lower for kw in ["código", "app", "script", "programa"]):
            is_ambiguous = True
            reasons.append("No especifica lenguaje de programación")
        
        if not entities.get("platform") and any(kw in query_lower for kw in ["ejecutar", "correr", "usar"]):
            is_ambiguous = True
            reasons.append("No especifica plataforma de ejecución")
        
        return is_ambiguous, reasons
    
    def generate_questions(self, intent: IntentCategory, entities: Dict[str, Any], 
                          context: Optional[ConversationContext] = None) -> List[str]:
        """Genera preguntas inteligentes basadas en intención y contexto"""
        questions = []
        
        # Obtener plantillas para esta intención
        templates = self.QUESTION_TEMPLATES.get(intent, [])
        
        if not templates:
            return questions
        
        # Seleccionar 2-3 preguntas más relevantes
        selected = []
        for template in templates:
            # Si la entidad ya está clara, saltar pregunta sobre ella
            skip = False
            if "lenguaje" in template.lower() and entities.get("programming_language"):
                skip = True
            elif "plataforma" in template.lower() and entities.get("platform"):
                skip = True
            elif "frecuencia" in template.lower() and entities.get("frequency"):
                skip = True
            
            if not skip:
                selected.append(template)
        
        # Rellenar plantillas con entidades si es necesario
        for template in selected[:3]:  # Máximo 3 preguntas
            if "{topic}" in template:
                topic = entities.get("data_type", ["información"])[0] if entities.get("data_type") else "este tema"
                template = template.format(topic=topic)
            questions.append(template)
        
        # Añadir preguntas contextuales si hay contexto previo
        if context and context.last_intent:
            if context.last_intent == intent.value:
                questions.append(f"¿Quieres continuar con {context.current_topic} o empezar algo nuevo?")
        
        return questions


class ConversationMemory:
    """Sistema de memoria de conversaciones anteriores"""
    
    def __init__(self, storage_path: str = "data/conversations.json"):
        self.storage_path = storage_path
        self.conversations: Dict[str, List[Dict]] = {}
        self.user_profiles: Dict[str, Dict] = {}
        self._load_from_disk()
    
    def _load_from_disk(self):
        """Carga conversaciones desde disco"""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.conversations = data.get("conversations", {})
                self.user_profiles = data.get("user_profiles", {})
            logger.info(f"Cargadas {len(self.conversations)} conversaciones")
        except FileNotFoundError:
            logger.info("No hay historial de conversaciones previo")
        except json.JSONDecodeError:
            logger.warning("Historial corrupto, iniciando desde cero")
    
    def save_to_disk(self):
        """Guarda conversaciones en disco"""
        try:
            data = {
                "conversations": self.conversations,
                "user_profiles": self.user_profiles,
                "last_updated": datetime.now().isoformat()
            }
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando conversaciones: {e}")
    
    def add_message(self, user_id: str, message: Dict):
        """Añade un mensaje al historial"""
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        
        self.conversations[user_id].append({
            "timestamp": datetime.now().isoformat(),
            **message
        })
        
        # Mantener solo últimas 100 interacciones por usuario
        if len(self.conversations[user_id]) > 100:
            self.conversations[user_id] = self.conversations[user_id][-100:]
        
        # Actualizar perfil de usuario
        self._update_user_profile(user_id, message)
    
    def _update_user_profile(self, user_id: str, message: Dict):
        """Actualiza perfil de usuario basado en interacciones"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {
                "preferences": {},
                "common_topics": [],
                "preferred_language": None,
                "preferred_platform": None,
                "interaction_count": 0,
            }
        
        profile = self.user_profiles[user_id]
        profile["interaction_count"] += 1
        
        # Extraer preferencias de entidades
        entities = message.get("entities", {})
        if "programming_language" in entities:
            lang = entities["programming_language"][0]
            profile["preferences"]["language"] = lang
        
        if "platform" in entities:
            platform = entities["platform"][0]
            profile["preferences"]["platform"] = platform
    
    def get_user_context(self, user_id: str) -> Optional[ConversationContext]:
        """Obtiene contexto actual del usuario"""
        if user_id not in self.conversations or not self.conversations[user_id]:
            return None
        
        recent = self.conversations[user_id][-10:]
        
        # Analizar últimas interacciones
        topics = []
        intents = []
        entities = {}
        
        for msg in recent:
            if "intent" in msg:
                intents.append(msg["intent"])
            if "topic" in msg:
                topics.append(msg["topic"])
            if "entities" in msg:
                entities.update(msg["entities"])
        
        return ConversationContext(
            user_id=user_id,
            current_topic=topics[-1] if topics else "",
            last_intent=intents[-1] if intents else "",
            last_entities=entities,
            conversation_turns=len(recent),
            context_window=recent
        )
    
    def find_similar_queries(self, user_id: str, query: str, limit: int = 3) -> List[Dict]:
        """Busca consultas similares en el historial"""
        if user_id not in self.conversations:
            return []
        
        similar = []
        for msg in reversed(self.conversations[user_id]):
            if "query" in msg:
                score = fuzz.ratio(query.lower(), msg["query"].lower())
                if score > 60:  # Umbral de similitud
                    similar.append({
                        "query": msg["query"],
                        "score": score,
                        "response": msg.get("response", ""),
                        "timestamp": msg.get("timestamp", "")
                    })
        
        return sorted(similar, key=lambda x: x["score"], reverse=True)[:limit]
    
    def get_user_preferences(self, user_id: str) -> Dict:
        """Obtiene preferencias del usuario"""
        if user_id in self.user_profiles:
            return self.user_profiles[user_id].get("preferences", {})
        return {}


class IntentClassifier:
    """Clasificador de intenciones mejorado con preguntas inteligentes y memoria"""
    
    def __init__(self, intents_registry_path: str = None):
        self.question_generator = QuestionGenerator()
        self.memory = ConversationMemory()
        self.intents_registry = self._load_intents_registry(intents_registry_path)
        
        # Patrones regex para detección rápida
        self.patterns = self._compile_patterns()
    
    def _load_intents_registry(self, path: str) -> Dict:
        """Carga registro de intenciones desde archivo JSON"""
        default_registry = {
            "web_search": {
                "keywords": ["busca", "buscar", "investiga", "encuentra", "google", "bing"],
                "patterns": [r"busca(r)?\s+.+", r"investiga(r)?\s+.+", r"encuentra(r)?\s+.+"],
            },
            "code_generation": {
                "keywords": ["crea", "haz", "genera", "código", "app", "script", "programa"],
                "patterns": [r"crea(r)?\s+.*(código|app|script|programa)", r"haz(me)?\s+.*(código|app|script)"],
            },
            "code_review": {
                "keywords": ["revisa", "analiza", "mejora", "optimiza", "debug"],
                "patterns": [r"revisa(r)?\s+.*(código|script)", r"analiza(r)?\s+.*(código|error)"],
            },
            "vision_task": {
                "keywords": ["captura", "pantalla", "lee", "mira", "ver", "screenshot"],
                "patterns": [r"captura(r)?\s+.*(pantalla|app)", r"lee(r)?\s+.*(pantalla|app)"],
            },
            "system_query": {
                "keywords": ["estado", "sistema", "diagnóstico", "info", "versión"],
                "patterns": [r"estado\s+.*(sistema|bot)", r"diagnóstico", r"versión"],
            },
            "scheduled_task": {
                "keywords": ["programa", "automatiza", "diario", "cada", "cron", "tarea"],
                "patterns": [r"programa(r)?\s+.*(tarea|ejecución)", r"automatiza(r)?\s+.+"],
            },
            "explanation": {
                "keywords": ["explica", "qué es", "cómo", "por qué", "para qué"],
                "patterns": [r"explica(r)?\s+.+", r"qué\s+es\s+.+", r"cómo\s+(funciona|hacer)"],
            },
            "conversational": {
                "keywords": ["hola", "buenos", "gracias", "adiós", "cómo estás"],
                "patterns": [r"(hola|buenos|buenas)\s*(días|tardes|noches)?", r"gracias"],
            },
        }
        
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    custom_registry = json.load(f)
                    default_registry.update(custom_registry)
            except Exception as e:
                logger.warning(f"No se pudo cargar registry personalizado: {e}")
        
        return default_registry
    
    def _compile_patterns(self) -> Dict[str, List]:
        """Compila patrones regex para cada intención"""
        compiled = {}
        for intent, config in self.intents_registry.items():
            patterns = []
            for pattern in config.get("patterns", []):
                try:
                    patterns.append(re.compile(pattern, re.IGNORECASE))
                except re.error:
                    logger.warning(f"Patrón regex inválido: {pattern}")
            compiled[intent] = patterns
        return compiled
    
    def normalize_query(self, query: str) -> str:
        """Normaliza la consulta del usuario"""
        # Eliminar caracteres especiales excesivos
        normalized = re.sub(r'[^\w\sáéíóúüñÁÉÍÓÚÜÑ.,!?]', '', query)
        # Eliminar espacios múltiples
        normalized = re.sub(r'\s+', ' ', normalized)
        # Convertir a minúsculas
        normalized = normalized.lower().strip()
        return normalized
    
    def classify(self, query: str, user_id: str = "default") -> ClassifiedIntent:
        """Clasifica la intención de una consulta con contexto y memoria"""
        normalized = self.normalize_query(query)
        
        # Obtener contexto del usuario
        context = self.memory.get_user_context(user_id)
        
        # Fase 1: Detección por palabras clave (rápido)
        intent, confidence = self._keyword_match(normalized)
        
        # Fase 2: Si baja confianza, usar patrones regex
        if confidence < 0.7:
            intent, confidence = self._pattern_match(normalized)
        
        # Fase 3: Si sigue baja, usar similitud con historial
        if confidence < 0.6 and context:
            similar = self.memory.find_similar_queries(user_id, query)
            if similar and similar[0]["score"] > 70:
                # Usar intención de consulta similar
                intent = self._infer_intent_from_query(similar[0]["query"])
                confidence = similar[0]["score"] / 100.0
        
        # Extraer entidades
        entities = self.question_generator.extract_entities(query)
        
        # Detectar ambigüedad y generar preguntas
        is_ambiguous, ambiguity_reasons = self.question_generator.detect_ambiguity(query, entities)
        questions = []
        
        if is_ambiguous:
            questions = self.question_generator.generate_questions(intent, entities, context)
        
        # Generar sugerencias basadas en contexto
        suggested_actions = self._generate_suggestions(intent, entities, context)
        
        # Crear resultado
        result = ClassifiedIntent(
            intent=intent,
            confidence=confidence,
            original_query=query,
            normalized_query=normalized,
            entities=entities,
            requires_clarification=is_ambiguous and len(questions) > 0,
            clarification_questions=questions,
            suggested_actions=suggested_actions,
            context_used=context is not None,
            reasoning=f"Clasificado como {intent.value} con {confidence:.0%} de confianza"
        )
        
        # Guardar en memoria
        self.memory.add_message(user_id, {
            "query": query,
            "intent": intent.value,
            "entities": entities,
            "confidence": confidence,
            "response": result.reasoning
        })
        
        return result
    
    def _keyword_match(self, query: str) -> Tuple[IntentCategory, float]:
        """Match por palabras clave"""
        scores = {}
        for intent, config in self.intents_registry.items():
            score = 0
            for keyword in config.get("keywords", []):
                if keyword in query:
                    score += 1
            if score > 0:
                scores[intent] = score / len(config.get("keywords", [""]))
        
        if scores:
            best = max(scores, key=scores.get)
            return IntentCategory(best), min(scores[best], 1.0)
        
        return IntentCategory.UNKNOWN, 0.0
    
    def _pattern_match(self, query: str) -> Tuple[IntentCategory, float]:
        """Match por patrones regex"""
        for intent, patterns in self.patterns.items():
            for pattern in patterns:
                if pattern.search(query):
                    return IntentCategory(intent), 0.8
        
        return IntentCategory.UNKNOWN, 0.3
    
    def _infer_intent_from_query(self, query: str) -> IntentCategory:
        """Infiere intención desde una consulta similar"""
        # Usar el mismo mecanismo de clasificación
        temp_result = self._keyword_match(self.normalize_query(query))
        if temp_result[1] < 0.5:
            temp_result = self._pattern_match(self.normalize_query(query))
        return temp_result[0]
    
    def _generate_suggestions(self, intent: IntentCategory, entities: Dict, 
                             context: Optional[ConversationContext]) -> List[str]:
        """Genera sugerencias de acciones basadas en intención"""
        suggestions = []
        
        if intent == IntentCategory.CODE_GENERATION:
            if entities.get("programming_language"):
                lang = entities["programming_language"][0]
                suggestions.append(f"Generar código en {lang.title()}")
                suggestions.append(f"Crear tests para el código en {lang.title()}")
            suggestions.append("Explicar cómo funciona el código")
            suggestions.append("Optimizar el rendimiento del código")
        
        elif intent == IntentCategory.WEB_SEARCH:
            suggestions.append("Profundizar en los resultados")
            suggestions.append("Guardar resultados para referencia futura")
            suggestions.append("Comparar con otras fuentes")
        
        elif intent == IntentCategory.SYSTEM_QUERY:
            suggestions.append("Ejecutar diagnóstico completo")
            suggestions.append("Ver métricas de rendimiento")
            suggestions.append("Revisar logs recientes")
        
        # Sugerencias contextuales
        if context and context.last_intent:
            suggestions.append(f"Continuar con {context.current_topic}")
        
        return suggestions[:3]  # Máximo 3 sugerencias
    
    def get_conversation_summary(self, user_id: str, turns: int = 5) -> str:
        """Genera resumen de las últimas interacciones"""
        if user_id not in self.memory.conversations:
            return "No hay historial de conversación."
        
        recent = self.memory.conversations[user_id][-turns:]
        summary_parts = []
        
        for msg in recent:
            query = msg.get("query", "")
            intent = msg.get("intent", "unknown")
            summary_parts.append(f"- {query[:50]}... ({intent})")
        
        return "Resumen reciente:\n" + "\n".join(summary_parts)
    
    def save_memory(self):
        """Guarda la memoria en disco"""
        self.memory.save_to_disk()


# Instancia global para uso compartido
_classifier = None

def get_classifier(intents_registry_path: str = None) -> IntentClassifier:
    """Obtiene instancia singleton del clasificador"""
    global _classifier
    if _classifier is None:
        _classifier = IntentClassifier(intents_registry_path)
    return _classifier


def classify_query(query: str, user_id: str = "default") -> ClassifiedIntent:
    """Función conveniente para clasificación rápida"""
    return get_classifier().classify(query, user_id)