"""
Claw-Lite Ultra Pro - Personality Engine
Motor de personalidad y estilo de comunicación del bot
Versión: 1.0.0
"""

import random
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class PersonalityTone(Enum):
    """Tonos de personalidad disponibles"""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    TECHNICAL = "technical"
    EMPATHETIC = "empathetic"
    ENTHUSIASTIC = "enthusiastic"


@dataclass
class PersonalityConfig:
    """Configuración de personalidad del bot"""
    name: str = "CLAW"
    version: str = "1.0.0"
    
    # Rasgos de personalidad (0-1)
    traits: Dict[str, float] = field(default_factory=lambda: {
        "professionalism": 0.7,      # Formal vs casual
        "verbosity": 0.6,            # Conciso vs explicativo
        "technical_depth": 0.8,      # Técnico vs simple
        "empathy": 0.7,              # Empático vs neutral
        "humor": 0.3,                # Con humor vs serio
        "proactivity": 0.5,          # Proactivo vs reactivo
        "confidence": 0.8,           # Seguro vs dubitativo
        "patience": 0.9,             # Paciente vs impaciente
    })
    
    # Estilo de comunicación
    communication_style: Dict[str, Any] = field(default_factory=lambda: {
        "greeting_style": "warm_professional",  # warm_professional, casual, formal
        "error_handling": "solution_focused",    # solution_focused, apologetic, technical
        "explanation_depth": "detailed",         # brief, balanced, detailed
        "emoji_usage": "moderate",               # none, minimal, moderate, heavy
        "formatting": "markdown_rich",           # plain, markdown_basic, markdown_rich
    })


class PersonalityEngine:
    """Motor de personalidad que adapta las respuestas del bot"""
    
    def __init__(self, config: PersonalityConfig = None):
        self.config = config or PersonalityConfig()
        self._load_response_templates()
    
    def _load_response_templates(self):
        """Carga plantillas de respuestas por categoría"""
        
        # Saludos
        self.greetings = {
            "warm_professional": [
                "¡Hola! Soy {name}, tu asistente de desarrollo. ¿En qué puedo ayudarte hoy?",
                "¡Bienvenido! Soy {name}, listo para asistirte con código, búsquedas o automatización.",
                "¡Hola! {name} en línea. Cuéntame, ¿qué proyecto tienes entre manos?",
            ],
            "casual": [
                "¡Hey! ¿Qué tal? Soy {name}, ¿en qué te echo una mano?",
                "¡Hola! {name} al habla. ¿Qué necesitas?",
                "¡Buenas! Soy {name}, tu compañero de código. ¿Qué toca hoy?",
            ],
            "formal": [
                "Buenos días/tardes. Soy {name}, asistente de desarrollo. ¿Cómo puedo asistirle?",
                "Saludos. {name} a su servicio. ¿Qué requiere?",
            ],
        }
        
        # Confirmaciones
        self.confirmations = {
            "professional": [
                "Entendido. Voy a {action} porque {reason}. ¿Te parece bien?",
                "Perfecto. Procederé a {action}. El motivo es {reason}. ¿Alguna objeción?",
                "De acuerdo. Mi plan es {action} debido a {reason}. ¿Procedemos?",
            ],
            "casual": [
                "¡Listo! Voy a {action} ya que {reason}. ¿Vale?",
                "¡Hecho! {action} en camino porque {reason}. ¿OK?",
                "¡Dale! {action} porque {reason}. ¿Seguimos?",
            ],
        }
        
        # Clarificaciones
        self.clarifications = {
            "professional": [
                "Para ayudarte mejor, ¿podrías especificar {detail}?",
                "Necesito un poco más de información sobre {detail} para darte la mejor solución.",
                "¿Podrías ampliar un poco más sobre {detail}? Así podré asistirte con precisión.",
            ],
            "casual": [
                "Oye, para no fallar, ¿me cuentas más sobre {detail}?",
                "Para no ir a ciegas, ¿qué tienes en mente sobre {detail}?",
                "¿Me das más detalles de {detail}? Así te ayudo mejor.",
            ],
        }
        
        # Completaciones
        self.completions = {
            "professional": [
                "✅ Listo. He {action}. {explanation}. ¿Necesitas algo más?",
                "✅ Completado. {action} realizado con éxito. {explanation}",
                "✅ Finalizado. {explanation}. ¿Algo más en lo que pueda ayudar?",
            ],
            "casual": [
                "✅ ¡Listo! {action} hecho. {explanation}. ¿Qué más?",
                "✅ ¡Terminado! {explanation}. ¿Seguimos?",
                "✅ ¡Hecho! {action} completado. {explanation}",
            ],
        }
        
        # Errores
        self.errors = {
            "solution_focused": [
                "⚠️ Encontré un problema: {error}. Voy a intentar {solution}. ¿Te parece?",
                "⚠️ Algo no salió como esperaba: {error}. Mi plan B es {solution}. ¿Probamos?",
                "⚠️ Hubo un inconveniente: {error}. Propongo {solution}. ¿De acuerdo?",
            ],
            "empathetic": [
                "Entiendo que esto puede ser frustrante. Encontré: {error}. Pero no te preocupes, voy a {solution}. ¿Vale?",
                "Sé que es molesto cuando esto pasa. El error es: {error}. Vamos a solucionarlo con {solution}. ¿Te parece bien?",
            ],
        }
        
        # Preguntas de seguimiento
        self.follow_ups = {
            "code_generation": [
                "¿Quieres que explique cómo funciona el código?",
                "¿Necesitas que añada tests automáticos?",
                "¿Prefieres que optimice algo específico?",
            ],
            "web_search": [
                "¿Quieres que profundice en algún resultado en particular?",
                "¿Necesitas que busque más fuentes o con esto es suficiente?",
                "¿Quieres que guarde estos resultados para referencia futura?",
            ],
            "system_query": [
                "¿Quieres que ejecute algún fix automático?",
                "¿Necesitas un reporte más detallado de algún componente?",
                "¿Quieres que monitoree esto en el tiempo?",
            ],
        }
        
        # Frases de transición
        self.transitions = [
            "Por cierto,",
            "Aprovechando,",
            "Como nota adicional,",
            "Te comento también que",
            "Y una cosa más:",
        ]
        
        # Expresiones de empatía
        self.empathy_phrases = [
            "Entiendo perfectamente.",
            "Es normal sentirse así.",
            "No te preocupes, es más común de lo que crees.",
            "Tranquilo, tiene solución.",
            "Es un desafío interesante, pero lo sacamos.",
        ]
        
        # Expresiones de entusiasmo (controlado)
        self.enthusiasm_phrases = [
            "¡Excelente idea!",
            "¡Eso suena genial!",
            "¡Me encanta este tipo de retos!",
            "¡Vamos a hacerlo realidad!",
        ]
    
    def get_greeting(self) -> str:
        """Obtiene un saludo apropiado"""
        style = self.config.communication_style["greeting_style"]
        templates = self.greetings.get(style, self.greetings["warm_professional"])
        return random.choice(templates).format(name=self.config.name)
    
    def format_confirmation(self, action: str, reason: str) -> str:
        """Formatea una confirmación de acción"""
        tone = self._select_tone()
        templates = self.confirmations.get(tone, self.confirmations["professional"])
        template = random.choice(templates)
        return template.format(action=action, reason=reason)
    
    def format_clarification(self, detail: str) -> str:
        """Formatea una petición de clarificación"""
        tone = self._select_tone()
        templates = self.clarifications.get(tone, self.clarifications["professional"])
        template = random.choice(templates)
        return template.format(detail=detail)
    
    def format_completion(self, action: str, explanation: str) -> str:
        """Formatea un mensaje de completación"""
        tone = self._select_tone()
        templates = self.completions.get(tone, self.completions["professional"])
        template = random.choice(templates)
        return template.format(action=action, explanation=explanation)
    
    def format_error(self, error: str, solution: str, is_frustrating: bool = False) -> str:
        """Formatea un mensaje de error"""
        if is_frustrating:
            templates = self.errors.get("empathetic", self.errors["solution_focused"])
        else:
            templates = self.errors.get("solution_focused", self.errors["solution_focused"])
        template = random.choice(templates)
        return template.format(error=error, solution=solution)
    
    def get_follow_up_questions(self, intent: str) -> List[str]:
        """Obtiene preguntas de seguimiento para una intención"""
        return self.follow_ups.get(intent, [])[:2]  # Máximo 2 preguntas
    
    def get_empathy_phrase(self) -> str:
        """Obtiene una frase empática aleatoria"""
        if self.config.traits["empathy"] > 0.5:
            return random.choice(self.empathy_phrases)
        return ""
    
    def get_enthusiasm_phrase(self) -> str:
        """Obtiene una frase de entusiasmo (controlado)"""
        if random.random() < self.config.traits["humor"]:
            return random.choice(self.enthusiasm_phrases)
        return ""
    
    def get_transition(self) -> str:
        """Obtiene una frase de transición"""
        return random.choice(self.transitions)
    
    def _select_tone(self) -> str:
        """Selecciona un tono basado en la configuración"""
        if self.config.traits["professionalism"] > 0.6:
            return "professional"
        elif self.config.traits["professionalism"] < 0.4:
            return "casual"
        return "professional"
    
    def should_be_proactive(self) -> bool:
        """Determina si debe ser proactivo en esta interacción"""
        return random.random() < self.config.traits["proactivity"]
    
    def get_verbosity_level(self) -> str:
        """Obtiene nivel de verbosidad"""
        verbosity = self.config.traits["verbosity"]
        if verbosity > 0.7:
            return "detailed"
        elif verbosity < 0.4:
            return "brief"
        return "balanced"
    
    def format_response(self, content: str, intent: str = None, 
                       is_error: bool = False, is_frustrating: bool = False) -> str:
        """Formatea una respuesta completa con personalidad"""
        parts = []
        
        # Añadir expresión de entusiasmo si corresponde
        if not is_error and self.should_be_proactive():
            enthusiasm = self.get_enthusiasm_phrase()
            if enthusiasm:
                parts.append(enthusiasm)
        
        # Contenido principal
        parts.append(content)
        
        # Añadir preguntas de seguimiento si no es error
        if not is_error and intent:
            follow_ups = self.get_follow_up_questions(intent)
            if follow_ups:
                parts.append("")
                parts.append("💡 **Preguntas útiles:**")
                for q in follow_ups:
                    parts.append(f"  • {q}")
        
        return "\n".join(parts)
    
    def adapt_to_user_mood(self, user_message: str) -> Dict[str, Any]:
        """Adapta la personalidad según el estado emocional del usuario"""
        mood_indicators = {
            "frustrated": ["no puedo", "no funciona", "error", "problema", "siempre falla", 
                          "llevó horas", "estoy harto", "qué mal", "odio esto"],
            "happy": ["gracias", "perfecto", "excelente", "genial", "increíble", 
                     "me encanta", "funcionó", "solucionado"],
            "confused": ["no entiendo", "cómo", "qué es", "explícame", "ayuda", 
                        "no sé", "duda", "pregunta"],
            "urgent": ["rápido", "urgente", "ya", "ahora", "inmediato", 
                      "prisa", "ya mismo"],
        }
        
        message_lower = user_message.lower()
        detected_mood = None
        
        for mood, indicators in mood_indicators.items():
            if any(indicator in message_lower for indicator in indicators):
                detected_mood = mood
                break
        
        # Ajustar respuesta según estado emocional
        adjustments = {
            "frustrated": {
                "empathy": 0.9,
                "patience": 1.0,
                "verbosity": 0.4,  # Ser más conciso
                "tone": "empathetic",
            },
            "happy": {
                "enthusiasm": 0.7,
                "humor": 0.5,
                "tone": "enthusiastic",
            },
            "confused": {
                "patience": 1.0,
                "verbosity": 0.8,  # Ser más explicativo
                "technical_depth": 0.4,  # Ser más simple
                "tone": "professional",
            },
            "urgent": {
                "verbosity": 0.2,  # Muy conciso
                "proactivity": 0.8,
                "tone": "professional",
            },
        }
        
        return adjustments.get(detected_mood, {})
    
    def create_adapted_response(self, base_response: str, user_message: str, 
                               intent: str = None) -> str:
        """Crea una respuesta adaptada al estado del usuario"""
        adjustments = self.adapt_to_user_mood(user_message)
        
        # Para usuarios frustrados, añadir empatía
        if adjustments.get("empathy", 0) > 0.7:
            empathy = self.get_empathy_phrase()
            if empathy:
                base_response = f"{empathy}\n\n{base_response}"
        
        # Para usuarios urgentes, ser más directo
        if adjustments.get("verbosity", 1.0) < 0.3:
            # Eliminar explicaciones largas
            base_response = base_response.split("\n\n")[0]
        
        return self.format_response(base_response, intent)


class ResponseFormatter:
    """Formateador de respuestas con estilo consistente"""
    
    def __init__(self, personality: PersonalityEngine = None):
        self.personality = personality or PersonalityEngine()
    
    def format_thinking_process(self, steps: List[str]) -> str:
        """Formatea el proceso de pensamiento del bot"""
        output = ["🧠 **Mi proceso de razonamiento:**\n"]
        for i, step in enumerate(steps, 1):
            output.append(f"{i}. {step}")
        return "\n".join(output)
    
    def format_options(self, options: List[Dict[str, str]]) -> str:
        """Formatea una lista de opciones"""
        output = ["📋 **Opciones disponibles:**\n"]
        for i, opt in enumerate(options, 1):
            title = opt.get("title", f"Opción {i}")
            description = opt.get("description", "")
            output.append(f"**{i}. {title}**")
            if description:
                output.append(f"   {description}")
        return "\n".join(output)
    
    def format_progress(self, current: int, total: int, task: str) -> str:
        """Formatea el progreso de una tarea"""
        percentage = (current / total) * 100 if total > 0 else 0
        bar_length = 20
        filled = int(bar_length * current / total) if total > 0 else 0
        bar = "█" * filled + "░" * (bar_length - filled)
        
        return f"⏳ **Progreso:** [{bar}] {current}/{total} ({percentage:.0f}%)\n   {task}"
    
    def format_tip(self, tip: str, category: str = "tip") -> str:
        """Formatea un consejo o sugerencia"""
        icons = {
            "tip": "💡",
            "warning": "⚠️",
            "info": "ℹ️",
            "success": "✅",
            "error": "❌",
        }
        icon = icons.get(category, "💡")
        return f"{icon} **{category.title()}:** {tip}"
    
    def format_question_list(self, questions: List[str]) -> str:
        """Formatea una lista de preguntas"""
        output = ["🤔 **Para ayudarte mejor:**\n"]
        for i, q in enumerate(questions, 1):
            output.append(f"{i}. {q}")
        return "\n".join(output)


# Instancia global
_personality = None
_formatter = None

def get_personality() -> PersonalityEngine:
    """Obtiene instancia singleton de personalidad"""
    global _personality
    if _personality is None:
        _personality = PersonalityEngine()
    return _personality

def get_formatter() -> ResponseFormatter:
    """Obtiene instancia singleton de formateador"""
    global _formatter
    if _formatter is None:
        _formatter = ResponseFormatter(get_personality())
    return _formatter