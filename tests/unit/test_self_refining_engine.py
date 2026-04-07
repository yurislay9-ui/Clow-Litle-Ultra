"""
Tests para Self-Refining Engine - Claw-Litle 1.0
"""

import pytest
from src.features.self_refining_engine import (
    SelfRefiningEngine,
    ConfidenceEvaluator,
    RefinementStatus,
    RefinementIteration,
    RefinementResult,
    get_self_refining_engine,
    refine_response,
    example_generator,
    example_critic,
    example_refiner
)


@pytest.fixture
def evaluator():
    """Fixture para ConfidenceEvaluator"""
    return ConfidenceEvaluator()


@pytest.fixture
def engine():
    """Fixture para SelfRefiningEngine"""
    import src.features.self_refining_engine as sre_module
    sre_module._engine = None
    return SelfRefiningEngine({
        "confidence_threshold": 0.85,
        "max_iterations": 3
    })


class TestRefinementStatus:
    """Tests para el enum RefinementStatus"""
    
    def test_status_values(self):
        """Test que los estados tienen los valores correctos"""
        assert RefinementStatus.INITIAL.value == "initial"
        assert RefinementStatus.CRITIQUING.value == "critiquing"
        assert RefinementStatus.REFINING.value == "refining"
        assert RefinementStatus.VALIDATING.value == "validating"
        assert RefinementStatus.COMPLETED.value == "completed"
        assert RefinementStatus.FAILED.value == "failed"
        assert RefinementStatus.TIMEOUT.value == "timeout"


class TestRefinementIteration:
    """Tests para la dataclass RefinementIteration"""
    
    def test_iteration_creation(self):
        """Test de creación de RefinementIteration"""
        iteration = RefinementIteration(
            iteration_number=1,
            draft="Test draft",
            confidence_score=0.8,
            issues_detected=["Issue 1"],
            improvements_made=["Improvement 1"],
            time_taken_ms=100.5,
            status=RefinementStatus.COMPLETED
        )
        
        assert iteration.iteration_number == 1
        assert iteration.draft == "Test draft"
        assert iteration.confidence_score == 0.8
        assert len(iteration.issues_detected) == 1
        assert len(iteration.improvements_made) == 1
        assert iteration.time_taken_ms == 100.5
        assert iteration.status == RefinementStatus.COMPLETED


class TestRefinementResult:
    """Tests para la dataclass RefinementResult"""
    
    def test_result_creation(self):
        """Test de creación de RefinementResult"""
        result = RefinementResult(
            final_answer="Final answer",
            iterations=[],
            total_time_ms=200.0,
            final_confidence=0.9,
            max_confidence_reached=0.95,
            iterations_used=2,
            max_iterations_allowed=3,
            confidence_threshold=0.85,
            early_stopped=False,
            reasoning="Test reasoning"
        )
        
        assert result.final_answer == "Final answer"
        assert result.total_time_ms == 200.0
        assert result.final_confidence == 0.9
        assert result.iterations_used == 2


class TestConfidenceEvaluator:
    """Tests para ConfidenceEvaluator"""
    
    def test_initialization(self, evaluator):
        """Test de inicialización del evaluator"""
        assert evaluator is not None
        assert evaluator.confidence_threshold == 0.92  # default
    
    def test_evaluate_empty_response(self, evaluator):
        """Test de evaluación de respuesta vacía"""
        confidence = evaluator.evaluate("", "Test query")
        assert confidence == 0.0
    
    def test_evaluate_short_response(self, evaluator):
        """Test de evaluación de respuesta corta"""
        response = "Sí"
        confidence = evaluator.evaluate(response, "Test query")
        assert confidence < 0.5  # Muy corta reduce confianza
    
    def test_evaluate_long_response(self, evaluator):
        """Test de evaluación de respuesta muy larga"""
        response = "word " * 600  # 600 palabras
        confidence = evaluator.evaluate(response, "Test query")
        assert confidence < 0.5  # Demasiado largo reduce confianza
    
    def test_evaluate_low_confidence_indicators(self, evaluator):
        """Test de evaluación con indicadores de baja confianza"""
        response = "No estoy seguro, quizás sea así, tal vez no"
        confidence = evaluator.evaluate(response, "Test query")
        assert confidence < 0.5
    
    def test_evaluate_high_confidence_indicators(self, evaluator):
        """Test de evaluación con indicadores de alta confianza"""
        response = "Definitivamente es así, claramente se demuestra, sin duda"
        confidence = evaluator.evaluate(response, "Test query")
        assert confidence > 0.5
    
    def test_evaluate_good_structure(self, evaluator):
        """Test de evaluación con buena estructura"""
        response = "Primero, analicemos el problema.\n\nSegundo, la solución es clara.\n\nTercero, concluimos."
        confidence = evaluator.evaluate(response, "Test query")
        assert confidence > 0.5
    
    def test_evaluate_relevance(self, evaluator):
        """Test de evaluación de relevancia"""
        query = "¿Cómo funciona Python?"
        relevant_response = "Python funciona mediante un intérprete que ejecuta código"
        irrelevant_response = "El clima está muy bonito hoy"
        
        relevant_confidence = evaluator.evaluate(relevant_response, query)
        irrelevant_confidence = evaluator.evaluate(irrelevant_response, query)
        
        assert relevant_confidence > irrelevant_confidence
    
    def test_evaluate_contradictions(self, evaluator):
        """Test de evaluación con contradicciones"""
        response = "Es así, pero también es asá, sin embargo no lo es, aunque podría ser"
        confidence = evaluator.evaluate(response, "Test query")
        assert confidence < 0.5  # Muchas contradicciones reducen confianza
    
    def test_evaluate_normalization(self, evaluator):
        """Test de normalización de confianza"""
        response = "a" * 1000  # Respuesta extrema
        confidence = evaluator.evaluate(response, "Test query")
        assert 0.0 <= confidence <= 1.0
    
    def test_custom_config(self):
        """Test de configuración personalizada"""
        config = {"confidence_threshold": 0.75}
        evaluator = ConfidenceEvaluator(config)
        assert evaluator.confidence_threshold == 0.75


class TestSelfRefiningEngine:
    """Tests para SelfRefiningEngine"""
    
    def test_initialization(self, engine):
        """Test de inicialización del engine"""
        assert engine is not None
        assert engine.confidence_threshold == 0.85
        assert engine.max_iterations == 3
        assert engine.timeout_seconds == 30
    
    def test_set_callbacks(self, engine):
        """Test de configuración de callbacks"""
        def gen(q, c): return "Generated"
        def ref(q, d, i, c): return "Refined"
        def crit(q, r, c): return ["Issue"]
        
        engine.set_generator(gen)
        engine.set_refiner(ref)
        engine.set_critic(crit)
        
        assert engine.generator_callback == gen
        assert engine.refiner_callback == ref
        assert engine.critic_callback == crit
    
    def test_refine_with_callbacks(self, engine):
        """Test de refinamiento con callbacks"""
        engine.set_generator(example_generator)
        engine.set_critic(example_critic)
        engine.set_refiner(example_refiner)
        
        result = engine.refine("¿Cuál es la capital de Francia?")
        
        assert isinstance(result, RefinementResult)
        assert result.final_answer is not None
        assert result.iterations_used >= 0
        assert result.total_time_ms >= 0
    
    def test_refine_with_initial_response(self, engine):
        """Test de refinamiento con respuesta initial"""
        engine.set_critic(example_critic)
        engine.set_refiner(example_refiner)
        
        initial = "París es la capital"
        result = engine.refine(
            "¿Cuál es la capital de Francia?",
            initial_response=initial
        )
        
        assert result.final_answer is not None
        assert result.iterations_used >= 0
    
    def test_refine_without_callbacks_error(self, engine):
        """Test de error sin callbacks"""
        result = engine.refine("Test query")
        
        assert "Error" in result.final_answer or result.final_confidence == 0.0
    
    def test_quick_refine(self, engine):
        """Test de quick_refine (1 iteración)"""
        engine.set_critic(example_critic)
        engine.set_refiner(example_refiner)
        
        answer, confidence, time_ms = engine.quick_refine(
            "Test query",
            "Initial response"
        )
        
        assert answer is not None
        assert 0.0 <= confidence <= 1.0
        assert time_ms >= 0
    
    def test_refine_with_custom_threshold(self, engine):
        """Test de refinamiento con umbral personalizado"""
        engine.set_critic(example_critic)
        engine.set_refiner(example_refiner)
        
        result = engine.refine(
            "Test query",
            initial_response="Initial",
            confidence_threshold=0.95
        )
        
        assert result.confidence_threshold == 0.95
    
    def test_refine_with_custom_max_iterations(self, engine):
        """Test de refinamiento con máximo iteraciones personalizado"""
        engine.set_critic(example_critic)
        engine.set_refiner(example_refiner)
        
        result = engine.refine(
            "Test query",
            initial_response="Initial",
            max_iterations=5
        )
        
        assert result.max_iterations_allowed == 5
    
    def test_refine_with_context(self, engine):
        """Test de refinamiento con contexto"""
        engine.set_critic(example_critic)
        engine.set_refiner(example_refiner)
        
        result = engine.refine(
            "Test query",
            initial_response="Initial",
            context="Contexto adicional"
        )
        
        assert result.final_answer is not None
    
    def test_refine_timeout(self):
        """Test de timeout en refinamiento"""
        # Configurar timeout muy corto
        engine = SelfRefiningEngine({
            "timeout_seconds": 0.001,
            "max_iterations": 100
        })
        engine.set_critic(example_critic)
        engine.set_refiner(example_refiner)
        
        result = engine.refine(
            "Test query",
            initial_response="Initial"
        )
        
        # Debería terminar por timeout
        assert result.early_stopped is True
    
    def test_refine_max_iterations_reached(self, engine):
        """Test de máximo iteraciones alcanzado"""
        engine.set_critic(example_critic)
        engine.set_refiner(example_refiner)
        engine.confidence_threshold = 1.0  # Umbral inalcanzable
        
        result = engine.refine(
            "Test query",
            initial_response="Initial"
        )
        
        # Debería alcanzar máximo iteraciones
        assert result.iterations_used == engine.max_iterations
    
    def test_refine_early_stop_on_threshold(self, engine):
        """Test de parada temprana al alcanzar umbral"""
        engine.set_critic(example_critic)
        engine.set_refiner(example_refiner)
        engine.confidence_threshold = 0.1  # Umbral muy bajo
        
        result = engine.refine(
            "Test query",
            initial_response="Initial"
        )
        
        # Debería parar temprano
        assert result.early_stopped is True
    
    def test_refine_iteration_tracking(self, engine):
        """Test de seguimiento de iteraciones"""
        engine.set_critic(example_critic)
        engine.set_refiner(example_refiner)
        
        result = engine.refine(
            "Test query",
            initial_response="Initial"
        )
        
        # Verificar que las iteraciones están bien formadas
        for iteration in result.iterations:
            assert iteration.iteration_number >= 1
            assert 0.0 <= iteration.confidence_score <= 1.0
            assert iteration.time_taken_ms >= 0
            assert iteration.status == RefinementStatus.COMPLETED
    
    def test_refine_reasoning_output(self, engine):
        """Test de salida de razonamiento"""
        engine.set_critic(example_critic)
        engine.set_refiner(example_refiner)
        
        result = engine.refine(
            "Test query",
            initial_response="Initial"
        )
        
        assert isinstance(result.reasoning, str)
        assert len(result.reasoning) > 0
    
    def test_singleton_pattern(self):
        """Test de patrón singleton"""
        engine1 = get_self_refining_engine()
        engine2 = get_self_refining_engine()
        assert engine1 is engine2
    
    def test_global_helper_function(self):
        """Test de función helper global"""
        result = refine_response(
            "Test query",
            "Initial response"
        )
        assert isinstance(result, RefinementResult)
    
    def test_example_callbacks(self):
        """Test de callbacks de ejemplo"""
        gen_result = example_generator("Test query", None)
        assert gen_result is not None
        
        crit_result = example_critic("Test query", "Short", None)
        assert isinstance(crit_result, list)
        
        ref_result = example_refiner("Test query", "Initial", ["Issue"], None)
        assert ref_result is not None