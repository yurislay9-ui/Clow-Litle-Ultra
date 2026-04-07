"""
Query Complexity Analyzer - Claw-Litle 1.0

Analizador de complejidad de queries para determinar automáticamente
cuánto "pensar" según la complejidad de la consulta.
"""

import re
import math
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ThinkingLevel(Enum):
    """Niveles de esfuerzo cognitivo (Adaptive Thinking System)"""
    RAPIDO = 1        # ~500ms, 1 agente máx
    ESTANDAR = 2      # ~2-3s, 2-3 agentes
    PROFUNDO = 3      # ~8-12s, 4-6 agentes
    MAXIMO = 4        # ~20-30s, todos los agentes + iteraciones


@dataclass
class ComplexityScore:
    """Puntuación de complejidad de una query"""
    score: float                    # 0.0 - 10.0
    level: ThinkingLevel           # Nivel de pensamiento recomendado
    factors: Dict[str, float]      # Factores que influyeron
    confidence: float              # Confianza en la clasificación (0-1)
    reasoning: str                 # Explicación del análisis


class QueryComplexityAnalyzer:
    """
    Analizador de complejidad de queries para el Adaptive Thinking System.
    
    Determina automáticamente cuánto "pensar" según:
    - Longitud de la query
    - Palabras clave específicas
    - Operadores lógicos
    - Estructura de la consulta
    - Tipo de tarea solicitada
    """
    
    # Palabras clave por categoría de complejidad
    SIMPLE_KEYWORDS = {
        # Preguntas simples de hecho
        "qué hora es", "qué fecha", "clima", "tiempo", "hoy", "mañana",
        "cuántos días", "qué día", "día de la semana",
        # Comandos simples
        "abre", "cierra", "muestra", "lista", "di", "dime",
        # Saludos
        "hola", "buenos", "buenas", "qué tal", "cómo estás"
    }
    
    COMPLEX_KEYWORDS = {
        # Análisis y investigación
        "analiza", "investiga", "estudia", "examina", "evalúa",
        "compara", "contrastar", "diferencias", "semejanzas",
        # Generación de código
        "genera", "crea", "escribe", "programa", "codifica", "desarrolla",
        "implementa", "construye", "haz un", "haz una",
        # Tareas multi-paso
        "paso a paso", "proceso", "tutorial", "guía", "instrucciones",
        "cómo hacer", "cómo crear", "cómo implementar",
        # Optimización y debugging
        "optimiza", "mejora", "debug", "depura", "corrige", "arregla",
        # Investigación profunda
        "tendencias", "futuro", "predicción", "proyección", "análisis",
        "estadísticas", "datos", "métricas", "kpi"
    }
    
    CODE_GENERATION_KEYWORDS = {
        "código", "codigo", "programa", "script", "app", "aplicación",
        "función", "clase", "método", "api", "web", "scraper",
        "bot", "automatizar", "automatización", "bot",
        "python", "javascript", "java", "c++", "rust", "go",
        "html", "css", "sql", "react", "django", "flask",
        "base de datos", "database", "tabla", "consulta"
    }
    
    SECURITY_RELATED_KEYWORDS = {
        "seguridad", "vulnerabilidad", "auditoría", "pentesting",
        "exploit", "malware", "phishing", "inyección", "xss",
        "encriptar", "cifrar", "hash", "token", "auth", "login",
        "permiso", "privilegio", "root", "admin"
    }
    
    # Operadores lógicos que incrementan complejidad
    LOGICAL_OPERATORS = {
        "y": 0.5, "e": 0.5, "o": 0.5, "u": 0.5,
        "pero": 1.0, "sin embargo": 1.0, "aunque": 1.0,
        "porque": 0.8, "por qué": 0.8, "ya que": 0.8,
        "si": 1.0, "cuando": 0.8, "mientras": 0.8,
        "entonces": 0.8, "luego": 0.5, "después": 0.5,
        "primero": 0.8, "segundo": 0.8, "tercero": 0.8,
        "finalmente": 0.8, "además": 0.5, "también": 0.3
    }
    
    # Palabras de multi-paso
    MULTI_STEP_INDICATORS = {
        "paso 1": 1.0, "paso 2": 1.0, "paso 3": 1.0,
        "primero": 0.8, "luego": 0.8, "después": 0.8, "finalmente": 0.8,
        "inicio": 0.5, "fin": 0.5, "comienzo": 0.5, "término": 0.5,
        "1.": 0.8, "2.": 0.8, "3.": 0.8, "4.": 0.8, "5.": 0.8,
        "a)": 0.6, "b)": 0.6, "c)": 0.6, "d)": 0.6, "e)": 0.6,
        "i)": 0.6, "ii)": 0.6, "iii)": 0.6, "iv)": 0.6, "v)": 0.6
    }
    
    # Umbrales para niveles de pensamiento
    LEVEL_THRESHOLDS = {
        ThinkingLevel.RAPIDO: 0.5,
        ThinkingLevel.ESTANDAR: 1.5,
        ThinkingLevel.PROFUNDO: 6.0,
        ThinkingLevel.MAXIMO: 8.0
    }
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Inicializa el analizador de complejidad.
        
        Args:
            config: Configuración opcional para ajustar umbrales
        """
        self.config = config or {}
        
        # Ajustar umbrales si se proporciona configuración
        if "thresholds" in self.config:
            self.LEVEL_THRESHOLDS.update(self.config["thresholds"])
        
        # Compilar patrones regex para operadores
        self.operator_patterns = {}
        for operator, weight in self.LOGICAL_OPERATORS.items():
            pattern = re.compile(r'\b' + re.escape(operator) + r'\b', re.IGNORECASE)
            self.operator_patterns[operator] = (pattern, weight)
    
    def analyze(self, query: str, context: Optional[Dict] = None) -> ComplexityScore:
        """
        Analiza la complejidad de una query.
        
        Args:
            query: Texto de la consulta del usuario
            context: Contexto adicional (historial, preferencias, etc.)
        
        Returns:
            ComplexityScore con el análisis completo
        """
        if not query or not query.strip():
            return ComplexityScore(
                score=0.0,
                level=ThinkingLevel.RAPIDO,
                factors={"empty_query": 0.0},
                confidence=1.0,
                reasoning="Query vacía"
            )
        
        query_lower = query.lower().strip()
        factors: Dict[str, float] = {}
        reasoning_parts: List[str] = []
        
        # 1. Análisis de longitud
        length_score = self._analyze_length(query)
        factors["length"] = length_score
        if length_score > 0.5:
            reasoning_parts.append(f"Longitud: {'alta' if length_score > 1.0 else 'media'} ({len(query)} chars)")
        
        # 2. Detección de palabras clave
        keyword_score, keyword_reasons = self._analyze_keywords(query_lower)
        factors["keywords"] = keyword_score
        if keyword_reasons:
            reasoning_parts.extend(keyword_reasons)
        
        # 3. Análisis de operadores lógicos
        operator_score, operator_reasons = self._analyze_operators(query_lower)
        factors["operators"] = operator_score
        if operator_reasons:
            reasoning_parts.extend(operator_reasons)
        
        # 4. Detección de estructura multi-paso
        step_score, step_reasons = self._analyze_multi_step(query_lower)
        factors["multi_step"] = step_score
        if step_reasons:
            reasoning_parts.extend(step_reasons)
        
        # 5. Detección de tipo de tarea
        task_score, task_reasons = self._analyze_task_type(query_lower)
        factors["task_type"] = task_score
        if task_reasons:
            reasoning_parts.extend(task_reasons)
        
        # 6. Análisis de estructura sintáctica
        syntax_score, syntax_reasons = self._analyze_syntax(query)
        factors["syntax"] = syntax_score
        if syntax_reasons:
            reasoning_parts.extend(syntax_reasons)
        
        # 7. Calcular puntuación final (ponderada)
        final_score = self._calculate_final_score(factors)
        
        # 8. Determinar nivel de pensamiento
        level = self._determine_level(final_score)
        
        # 9. Calcular confianza
        confidence = self._calculate_confidence(factors, final_score)
        
        reasoning = " | ".join(reasoning_parts) if reasoning_parts else "Análisis estándar"
        
        return ComplexityScore(
            score=round(final_score, 2),
            level=level,
            factors={k: round(v, 2) for k, v in factors.items()},
            confidence=round(confidence, 2),
            reasoning=reasoning
        )
    
    def _analyze_length(self, query: str) -> float:
        """Analiza la longitud de la query"""
        length = len(query)
        
        if length < 20:
            return 0.2
        elif length < 50:
            return 0.5
        elif length < 100:
            return 1.0
        elif length < 200:
            return 1.5
        else:
            return min(2.0, length / 150)
    
    def _analyze_keywords(self, query: str) -> Tuple[float, List[str]]:
        """Analiza palabras clave en la query"""
        score = 0.0
        reasons = []
        
        # Verificar palabras simples (reducen complejidad)
        simple_count = sum(1 for kw in self.SIMPLE_KEYWORDS if kw in query)
        if simple_count > 0:
            score -= 0.5 * min(simple_count, 3)
            reasons.append(f"{simple_count} palabras simples detectadas")
        
        # Verificar palabras complejas
        complex_count = sum(1 for kw in self.COMPLEX_KEYWORDS if kw in query)
        if complex_count > 0:
            score += 1.0 * min(complex_count, 5)
            reasons.append(f"{complex_count} palabras complejas detectadas")
        
        # Verificar palabras de generación de código
        code_count = sum(1 for kw in self.CODE_GENERATION_KEYWORDS if kw in query)
        if code_count > 0:
            score += 1.5 * min(code_count, 5)
            reasons.append(f"{code_count} keywords de código detectadas")
        
        # Verificar palabras de seguridad
        security_count = sum(1 for kw in self.SECURITY_RELATED_KEYWORDS if kw in query)
        if security_count > 0:
            score += 1.2 * min(security_count, 3)
            reasons.append(f"{security_count} keywords de seguridad detectadas")
        
        return score, reasons
    
    def _analyze_operators(self, query: str) -> Tuple[float, List[str]]:
        """Analiza operadores lógicos en la query"""
        score = 0.0
        reasons = []
        
        found_operators = []
        for operator, (pattern, weight) in self.operator_patterns.items():
            matches = pattern.findall(query)
            if matches:
                score += weight * len(matches)
                found_operators.append(f"{operator}({len(matches)})")
        
        if found_operators:
            reasons.append(f"Operadores: {', '.join(found_operators)}")
        
        return score, reasons
    
    def _analyze_multi_step(self, query: str) -> Tuple[float, List[str]]:
        """Analiza indicadores de tareas multi-paso"""
        score = 0.0
        reasons = []
        
        # Verificar números de pasos
        step_numbers = re.findall(r'\b(\d+)\s*[.:)]', query)
        if step_numbers:
            score += 0.8 * len(step_numbers)
            reasons.append(f"{len(step_numbers)} pasos numerados")
        
        # Verificar indicadores de secuencia
        for indicator, weight in self.MULTI_STEP_INDICATORS.items():
            if indicator in query:
                score += weight
                reasons.append(f"Indicador: '{indicator}'")
        
        # Verificar palabras de secuencia
        sequence_words = ["primero", "luego", "después", "finalmente", "por último"]
        seq_count = sum(1 for word in sequence_words if word in query)
        if seq_count >= 3:
            score += 1.0
            reasons.append(f"{seq_count} palabras de secuencia")
        
        return score, reasons
    
    def _analyze_task_type(self, query: str) -> Tuple[float, List[str]]:
        """Analiza el tipo de tarea solicitada"""
        score = 0.0
        reasons = []
        
        # Tareas de investigación
        research_patterns = [
            r'\b(investiga|investigar|análisis|analizar)\b',
            r'\b(estudio|estudiar|revisión|revisar)\b',
            r'\b(comparar|comparación|contrastar)\b'
        ]
        
        for pattern in research_patterns:
            if re.search(pattern, query):
                score += 1.5
                reasons.append("Tarea de investigación detectada")
                break
        
        # Tareas de generación de código
        if any(kw in query for kw in ["genera", "crea", "escribe", "programa", "haz un código"]):
            score += 2.0
            reasons.append("Generación de código solicitada")
        
        # Tareas de debugging/optimización
        if any(kw in query for kw in ["debug", "optimiza", "corrige", "arregla", "error"]):
            score += 1.8
            reasons.append("Debugging/optimización solicitada")
        
        # Tareas de análisis de datos
        if any(kw in query for kw in ["datos", "estadísticas", "métricas", "análisis de"]):
            score += 1.3
            reasons.append("Análisis de datos solicitado")
        
        return score, reasons
    
    def _analyze_syntax(self, query: str) -> Tuple[float, List[str]]:
        """Analiza la estructura sintáctica de la query"""
        score = 0.0
        reasons = []
        
        # Contar oraciones (puntos, signos de interrogación/exclamación)
        sentences = re.split(r'[.!?]+', query)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) > 1:
            score += 0.5 * (len(sentences) - 1)
            reasons.append(f"{len(sentences)} oraciones")
        
        # Contar cláusulas (comas, punto y coma)
        clauses = re.split(r'[,;:]+', query)
        clauses = [c.strip() for c in clauses if c.strip()]
        
        if len(clauses) > 2:
            score += 0.3 * (len(clauses) - 2)
            reasons.append(f"{len(clauses)} cláusulas")
        
        # Verificar preguntas anidadas
        question_marks = query.count('?')
        if question_marks > 1:
            score += 1.0 * (question_marks - 1)
            reasons.append(f"{question_marks} preguntas")
        
        # Verificar paréntesis (indicador de complejidad)
        paren_depth = 0
        max_paren_depth = 0
        for char in query:
            if char == '(':
                paren_depth += 1
                max_paren_depth = max(max_paren_depth, paren_depth)
            elif char == ')':
                paren_depth = max(0, paren_depth - 1)
        
        if max_paren_depth > 0:
            score += 0.5 * max_paren_depth
            reasons.append(f"Profundidad paréntesis: {max_paren_depth}")
        
        return score, reasons
    
    def _calculate_final_score(self, factors: Dict[str, float]) -> float:
        """Calcula la puntuación final como suma directa de factores"""
        # Suma directa de todos los factores (sin pesos reductores)
        final_score = sum(factors.values())
        
        # Normalizar a escala 0-10
        final_score = min(10.0, max(0.0, final_score))
        
        return final_score

        """Determina el nivel de pensamiento basado en el score"""
        for level in [ThinkingLevel.MAXIMO, ThinkingLevel.PROFUNDO, 
                      ThinkingLevel.ESTANDAR, ThinkingLevel.RAPIDO]:
            if score >= self.LEVEL_THRESHOLDS[level]:
                return level
        return ThinkingLevel.RAPIDO

    def _determine_level(self, score: float) -> ThinkingLevel:
        """Determina el nivel de pensamiento basado en el score"""
        # Iterar de mayor a menor: si el score supera el threshold, usar ese nivel
        for level in [ThinkingLevel.MAXIMO, ThinkingLevel.PROFUNDO,
                      ThinkingLevel.ESTANDAR, ThinkingLevel.RAPIDO]:
            if score >= self.LEVEL_THRESHOLDS[level]:
                return level
        return ThinkingLevel.RAPIDO

    
    def _calculate_confidence(self, factors: Dict[str, float], score: float) -> float:
        """Calcula la confianza en la clasificación"""
        # Más factores activos = mayor confianza
        active_factors = sum(1 for v in factors.values() if v > 0)
        factor_confidence = min(1.0, active_factors / 1.0)
        
        # Score muy alto o muy bajo = mayor confianza
        if score > 7.5 or score < 2.5:
            score_confidence = 0.9
        elif score > 5.0:
            score_confidence = 0.7
        else:
            score_confidence = 0.5
        
        return (factor_confidence + score_confidence) / 2.0
    
    def get_level_info(self, level: ThinkingLevel) -> Dict:
        """Obtiene información detallada sobre un nivel de pensamiento"""
        info = {
            ThinkingLevel.RAPIDO: {
                "name": "Rápido",
                "description": "Para preguntas simples y directas",
                "time_estimate": "~500ms",
                "max_agents": 1,
                "self_refining": False,
                "use_cases": ["Consultas de hecho", "Comandos simples", "Saludos"]
            },
            ThinkingLevel.ESTANDAR: {
                "name": "Estándar",
                "description": "Para búsquedas y preguntas comunes",
                "time_estimate": "~2-3 segundos",
                "max_agents": 3,
                "self_refining": True,
                "self_refining_iterations": 1,
                "use_cases": ["Búsquedas web", "Preguntas comunes", "Consultas de información"]
            },
            ThinkingLevel.PROFUNDO: {
                "name": "Profundo",
                "description": "Para análisis complejos y generación de código",
                "time_estimate": "~8-12 segundos",
                "max_agents": 6,
                "self_refining": True,
                "self_refining_iterations": 3,
                "use_cases": ["Análisis complejos", "Generación de código", "Investigación"]
            },
            ThinkingLevel.MAXIMO: {
                "name": "Máximo",
                "description": "Para tareas críticas y razonamiento extendido",
                "time_estimate": "~20-30 segundos",
                "max_agents": 10,
                "self_refining": True,
                "self_refining_iterations": 5,
                "use_cases": ["Tareas multi-paso", "Análisis exhaustivo", "Reportes complejos"]
            }
        }
        
        return info.get(level, info[ThinkingLevel.RAPIDO])


# Instancia global
_analyzer: Optional[QueryComplexityAnalyzer] = None


def get_complexity_analyzer() -> QueryComplexityAnalyzer:
    """Obtiene la instancia global del analizador"""
    global _analyzer
    if _analyzer is None:
        _analyzer = QueryComplexityAnalyzer()
    return _analyzer


def analyze_query_complexity(query: str, context: Optional[Dict] = None) -> ComplexityScore:
    """Función helper para analizar complejidad de query"""
    return get_complexity_analyzer().analyze(query, context)


if __name__ == "__main__":
    # Ejemplos de prueba
    analyzer = get_complexity_analyzer()
    
    test_queries = [
        "¿Qué hora es?",
        "Hola, ¿cómo estás?",
        "Busca precios de iPhone 15",
        "Genera un scraper para Amazon que extraiga precios y opiniones",
        "Analiza las tendencias de IA para 2025 y genera un reporte PDF con gráficos",
        "Primero busca información sobre React, luego compara con Vue y Angular, "
        "finalmente genera una tabla comparativa con ventajas y desventajas",
        "¿Cómo optimizar una consulta SQL lenta en PostgreSQL?",
        "Crea una API REST con Flask que tenga autenticación JWT y sea segura contra SQL injection"
    ]
    
    print("=== Claw-Litle 1.0 - Query Complexity Analyzer ===\n")
    
    for query in test_queries:
        result = analyzer.analyze(query)
        level_info = analyzer.get_level_info(result.level)
        
        print(f"Query: '{query[:60]}{'...' if len(query) > 60 else ''}'")
        print(f"  Score: {result.score}/10.0")
        print(f"  Nivel: {level_info['name']} ({result.level.name})")
        print(f"  Confianza: {result.confidence:.0%}")
        print(f"  Factores: {result.factors}")
        print(f"  Razón: {result.reasoning}")
        print()