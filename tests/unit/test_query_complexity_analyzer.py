"""
Tests para Query Complexity Analyzer - Claw-Litle 1.0
"""

import pytest
from src.features.query_complexity_analyzer import (
    QueryComplexityAnalyzer,
    ComplexityScore,
    ThinkingLevel,
    get_complexity_analyzer,
    analyze_query_complexity
)


@pytest.fixture
def analyzer():
    """Fixture para obtener un analyzer limpio"""
    import src.features.query_complexity_analyzer as qca_module
    qca_module._analyzer = None
    return QueryComplexityAnalyzer()


class TestThinkingLevel:
    """Tests para el enum ThinkingLevel"""
    
    def test_thinking_level_values(self):
        """Test que los niveles tienen los valores correctos"""
        assert ThinkingLevel.RAPIDO.value == 1
        assert ThinkingLevel.ESTANDAR.value == 2
        assert ThinkingLevel.PROFUNDO.value == 3
        assert ThinkingLevel.MAXIMO.value == 4


class TestComplexityScore:
    """Tests para la dataclass ComplexityScore"""
    
    def test_complexity_score_creation(self):
        """Test de creación de ComplexityScore"""
        score = ComplexityScore(
            score=5.0,
            level=ThinkingLevel.ESTANDAR,
            factors={"keywords": 2.0, "length": 1.0},
            confidence=0.8,
            reasoning="Test reasoning"
        )
        
        assert score.score == 5.0
        assert score.level == ThinkingLevel.ESTANDAR
        assert len(score.factors) == 2
        assert score.confidence == 0.8
        assert score.reasoning == "Test reasoning"


class TestQueryComplexityAnalyzer:
    """Tests para QueryComplexityAnalyzer"""
    
    def test_initialization(self, analyzer):
        """Test de inicialización del analyzer"""
        assert analyzer is not None
        assert analyzer.config == {}
    
    def test_analyze_empty_query(self, analyzer):
        """Test de análisis de query vacía"""
        result = analyzer.analyze("")
        
        assert result.score == 0.0
        assert result.level == ThinkingLevel.RAPIDO
        assert result.confidence == 1.0
        assert "empty_query" in result.factors
    
    def test_analyze_simple_greeting(self, analyzer):
        """Test de análisis de saludo simple"""
        result = analyzer.analyze("Hola, ¿cómo estás?")
        
        assert result.level == ThinkingLevel.RAPIDO
        assert result.score < 2.5
    
    def test_analyze_simple_question(self, analyzer):
        """Test de análisis de pregunta simple"""
        result = analyzer.analyze("¿Qué hora es?")
        
        assert result.level == ThinkingLevel.RAPIDO
        assert result.score < 2.5
    
    def test_analyze_standard_search(self, analyzer):
        """Test de análisis de búsqueda estándar"""
        result = analyzer.analyze("Busca precios de iPhone 15")
        
        assert result.level in [ThinkingLevel.RAPIDO, ThinkingLevel.ESTANDAR]
        assert result.score >= 0
    
    def test_analyze_code_generation(self, analyzer):
        """Test de análisis de generación de código"""
        result = analyzer.analyze("Genera un scraper para Amazon")
        
        assert result.level in [ThinkingLevel.ESTANDAR, ThinkingLevel.PROFUNDO]
        assert "code" in str(result.reasoning).lower() or result.factors.get("keywords", 0) > 0
    
    def test_analyze_complex_analysis(self, analyzer):
        """Test de análisis de tarea compleja"""
        query = "Analiza las tendencias de IA para 2025 y genera un reporte PDF con gráficos"
        result = analyzer.analyze(query)
        
        assert result.level in [ThinkingLevel.PROFUNDO, ThinkingLevel.MAXIMO]
        assert result.score > 5.0
    
    def test_analyze_multi_step_task(self, analyzer):
        """Test de análisis de tarea multi-paso"""
        query = "Primero busca información sobre React, luego compara con Vue y Angular, finalmente genera una tabla comparativa"
        result = analyzer.analyze(query)
        
        assert result.level in [ThinkingLevel.PROFUNDO, ThinkingLevel.MAXIMO]
        assert result.factors.get("multi_step", 0) > 0
    
    def test_analyze_debugging_task(self, analyzer):
        """Test de análisis de debugging"""
        result = analyzer.analyze("¿Cómo optimizar una consulta SQL lenta?")
        
        assert result.level in [ThinkingLevel.ESTANDAR, ThinkingLevel.PROFUNDO]
        assert result.factors.get("task_type", 0) > 0
    
    def test_length_analysis(self, analyzer):
        """Test de análisis de longitud"""
        # Query corta
        short_result = analyzer.analyze("Hola")
        assert short_result.factors.get("length", 0) <= 0.5
        
        # Query larga
        long_query = "a" * 250
        long_result = analyzer.analyze(long_query)
        assert long_result.factors.get("length", 0) >= 1.5
    
    def test_keyword_analysis_simple(self, analyzer):
        """Test de análisis de keywords simples"""
        result = analyzer.analyze("Hola buenos días")
        
        # Debería detectar palabras simples
        assert result.factors.get("keywords", 0) <= 0
    
    def test_keyword_analysis_complex(self, analyzer):
        """Test de análisis de keywords complejas"""
        result = analyzer.analyze("Analiza y compara las tendencias")
        
        # Debería detectar palabras complejas
        assert result.factors.get("keywords", 0) > 0
    
    def test_keyword_analysis_code(self, analyzer):
        """Test de análisis de keywords de código"""
        result = analyzer.analyze("Genera un script en Python")
        
        # Debería detectar keywords de código
        assert result.factors.get("keywords", 0) > 0
    
    def test_keyword_analysis_security(self, analyzer):
        """Test de análisis de keywords de seguridad"""
        result = analyzer.analyze("Auditoría de seguridad y vulnerabilidades")
        
        # Debería detectar keywords de seguridad
        assert result.factors.get("keywords", 0) > 0
    
    def test_operator_analysis(self, analyzer):
        """Test de análisis de operadores lógicos"""
        result = analyzer.analyze("Busca información y compara resultados pero filtra errores")
        
        # Debería detectar operadores
        assert result.factors.get("operators", 0) > 0
    
    def test_multi_step_analysis_numbered(self, analyzer):
        """Test de análisis multi-paso con números"""
        result = analyzer.analyze("1. Primero haz esto 2. Luego haz aquello 3. Finalmente termina")
        
        # Debería detectar pasos numerados
        assert result.factors.get("multi_step", 0) > 0
    
    def test_multi_step_analysis_sequence(self, analyzer):
        """Test de análisis multi-paso con secuencia"""
        result = analyzer.analyze("Primero busca, luego analiza, después compara, finalmente reporta")
        
        # Debería detectar palabras de secuencia
        assert result.factors.get("multi_step", 0) > 0
    
    def test_syntax_analysis_multiple_sentences(self, analyzer):
        """Test de análisis sintáctico con múltiples oraciones"""
        result = analyzer.analyze("Primero busca información. Luego analiza los datos. Finalmente genera el reporte.")
        
        # Debería detectar múltiples oraciones
        assert result.factors.get("syntax", 0) > 0
    
    def test_syntax_analysis_multiple_questions(self, analyzer):
        """Test de análisis sintáctico con múltiples preguntas"""
        result = analyzer.analyze("¿Qué es Python? ¿Cómo se usa? ¿Cuándo aprenderlo?")
        
        # Debería detectar múltiples preguntas
        assert result.factors.get("syntax", 0) > 0
    
    def test_syntax_analysis_parentheses(self, analyzer):
        """Test de análisis sintáctico con paréntesis"""
        result = analyzer.analyze("Analiza datos (incluyendo métricas y KPIs) para generar insights")
        
        # Debería detectar paréntesis
        assert result.factors.get("syntax", 0) > 0
    
    def test_final_score_calculation(self, analyzer):
        """Test de cálculo de puntuación final"""
        factors = {
            "length": 1.0,
            "keywords": 1.0,
            "operators": 1.5,
            "multi_step": 0.0,
            "task_type": 2.0,
            "syntax": 0.5
        }
        
        score = analyzer._calculate_final_score(factors)
        
        # El score debería estar entre 0 y 10
        assert 0 <= score <= 10
    
    def test_final_score_normalization(self, analyzer):
        """Test de normalización del score final"""
        # Factores extremos
        factors = {
            "length": 10.0,
            "keywords": 10.0,
            "operators": 10.0,
            "multi_step": 10.0,
            "task_type": 10.0,
            "syntax": 10.0
        }
        
        score = analyzer._calculate_final_score(factors)
        
        # El score debería estar normalizado a max 10
        assert score <= 10.0
    
    def test_level_determination_rapido(self, analyzer):
        """Test de determinación de nivel RÁPIDO"""
        level = analyzer._determine_level(1.0)
        assert level == ThinkingLevel.RAPIDO
    
    def test_level_determination_estandar(self, analyzer):
        """Test de determinación de nivel ESTÁNDAR"""
        level = analyzer._determine_level(2.5)
        assert level == ThinkingLevel.ESTANDAR
    
    def test_level_determination_profundo(self, analyzer):
        """Test de determinación de nivel PROFUNDO"""
        level = analyzer._determine_level(6.0)
        assert level == ThinkingLevel.PROFUNDO
    
    def test_level_determination_maximo(self, analyzer):
        """Test de determinación de nivel MÁXIMO"""
        level = analyzer._determine_level(9.0)
        assert level == ThinkingLevel.MAXIMO
    
    def test_confidence_calculation(self, analyzer):
        """Test de cálculo de confianza"""
        factors = {
            "length": 1.0,
            "keywords": 2.0,
            "operators": 0.0,
            "task_type": 1.5
        }
        
        confidence = analyzer._calculate_confidence(factors, 5.0)
        
        assert 0 <= confidence <= 1
    
    def test_get_level_info_rapido(self, analyzer):
        """Test de información de nivel RÁPIDO"""
        info = analyzer.get_level_info(ThinkingLevel.RAPIDO)
        
        assert info["name"] == "Rápido"
        assert info["max_agents"] == 1
        assert info["self_refining"] is False
    
    def test_get_level_info_estandar(self, analyzer):
        """Test de información de nivel ESTÁNDAR"""
        info = analyzer.get_level_info(ThinkingLevel.ESTANDAR)
        
        assert info["name"] == "Estándar"
        assert info["max_agents"] == 3
        assert info["self_refining"] is True
    
    def test_get_level_info_profundo(self, analyzer):
        """Test de información de nivel PROFUNDO"""
        info = analyzer.get_level_info(ThinkingLevel.PROFUNDO)
        
        assert info["name"] == "Profundo"
        assert info["max_agents"] == 6
        assert info["self_refining_iterations"] == 3
    
    def test_get_level_info_maximo(self, analyzer):
        """Test de información de nivel MÁXIMO"""
        info = analyzer.get_level_info(ThinkingLevel.MAXIMO)
        
        assert info["name"] == "Máximo"
        assert info["max_agents"] == 10
        assert info["self_refining_iterations"] == 5
    
    def test_custom_config(self):
        """Test de configuración personalizada"""
        config = {
            "thresholds": {
                ThinkingLevel.RAPIDO: 1.5,
                ThinkingLevel.ESTANDAR: 1.0,
                ThinkingLevel.PROFUNDO: 5.0,
                ThinkingLevel.MAXIMO: 8.0
            }
        }
        
        custom_analyzer = QueryComplexityAnalyzer(config)
        
        # Con umbrales más bajos, más queries serán complejas
        result = custom_analyzer.analyze("Busca información y analiza")
        assert result.score >= 0
    
    def test_singleton_pattern(self):
        """Test de patrón singleton"""
        analyzer1 = get_complexity_analyzer()
        analyzer2 = get_complexity_analyzer()
        assert analyzer1 is analyzer2
    
    def test_global_helper_function(self):
        """Test de función helper global"""
        score = analyze_query_complexity("Hola")
        assert isinstance(score, ComplexityScore)
        assert score.level == ThinkingLevel.RAPIDO
    
    def test_context_parameter(self, analyzer):
        """Test de parámetro de contexto"""
        context = {"user_preferences": {"verbose": True}}
        result = analyzer.analyze("Hola", context)
        
        # Debería funcionar con contexto
        assert isinstance(result, ComplexityScore)
    
    def test_special_characters(self, analyzer):
        """Test de caracteres especiales"""
        result = analyzer.analyze("!@#$%^&*()")
        assert isinstance(result, ComplexityScore)
    
    def test_unicode_characters(self, analyzer):
        """Test de caracteres unicode"""
        result = analyzer.analyze("你好世界 🌍")
        assert isinstance(result, ComplexityScore)
    
    def test_very_long_query(self, analyzer):
        """Test de query muy larga"""
        long_query = "a" * 1000
        result = analyzer.analyze(long_query)
        
        assert result.factors.get("length", 0) >= 2.0
    
    def test_reasoning_output(self, analyzer):
        """Test de salida de razonamiento"""
        result = analyzer.analyze("Genera un código Python complejo")
        
        assert isinstance(result.reasoning, str)
        assert len(result.reasoning) > 0
    
    def test_factors_output(self, analyzer):
        """Test de salida de factores"""
        result = analyzer.analyze("Analiza y compara datos con múltiples pasos")
        
        assert isinstance(result.factors, dict)
        assert "keywords" in result.factors or "operators" in result.factors