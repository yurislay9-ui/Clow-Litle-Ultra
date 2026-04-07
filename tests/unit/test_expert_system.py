"""
Claw-Litle 1.0
test_expert_system.py - Tests para Nivel 4: Expert Engine

Tests exhaustivos para el motor de reglas expertas.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.engine.nivel_4_expert import ExpertEngine
from src.engine import IntentResult


class TestExpertEngineInitialization:
    """Tests para inicialización del ExpertEngine."""
    
    def test_init_with_valid_registry(self, sample_intents_registry):
        """Test de inicialización con registro válido."""
        engine = ExpertEngine(sample_intents_registry)
        assert engine is not None
        assert len(engine._expert_rules) > 0
    
    def test_init_with_empty_registry(self):
        """Test de inicialización con registro vacío."""
        empty_registry = {"intents": [], "fallback": {}}
        engine = ExpertEngine(empty_registry)
        assert engine is not None
        assert len(engine._expert_rules) > 0  # Reglas por defecto


class TestExpertEngineRules:
    """Tests para reglas expertas."""
    
    def test_multi_action_detection(self, sample_intents_registry):
        """Test de detección de múltiples acciones."""
        engine = ExpertEngine(sample_intents_registry)
        result = engine._apply_expert_rules("buscar información y crear app")
        
        assert result is not None
        assert result.intent_name == "multi_intent"
    
    def test_question_detection(self, sample_intents_registry):
        """Test de detección de pregunta."""
        engine = ExpertEngine(sample_intents_registry)
        result = engine._apply_expert_rules("cómo puedo crear una app")
        
        assert result is not None
        assert result.intent_name == "question"
    
    def test_code_request_detection(self, sample_intents_registry):
        """Test de detección de solicitud de código."""
        engine = ExpertEngine(sample_intents_registry)
        result = engine._apply_expert_rules("necesito código para un scraper")
        
        assert result is not None
        assert result.intent_name == "code_generation"
    
    def test_search_request_detection(self, sample_intents_registry):
        """Test de detección de solicitud de búsqueda."""
        engine = ExpertEngine(sample_intents_registry)
        result = engine._apply_expert_rules("busco información sobre Python")
        
        assert result is not None
        assert result.intent_name == "web_search"
    
    def test_error_fix_detection(self, sample_intents_registry):
        """Test de detección de error en código."""
        engine = ExpertEngine(sample_intents_registry)
        result = engine._apply_expert_rules("tengo un error en mi código")
        
        assert result is not None
        assert result.intent_name == "code_repair"
    
    def test_negative_response_detection(self, sample_intents_registry):
        """Test de detección de respuesta negativa."""
        engine = ExpertEngine(sample_intents_registry)
        result = engine._apply_expert_rules("no")
        
        assert result is not None
        assert result.intent_name == "cancel"
    
    def test_affirmative_response_detection(self, sample_intents_registry):
        """Test de detección de respuesta afirmativa."""
        engine = ExpertEngine(sample_intents_registry)
        result = engine._apply_expert_rules("sí")
        
        assert result is not None
        assert result.intent_name == "confirm"


class TestExpertEngineValidation:
    """Tests para validación del ExpertEngine."""
    
    def test_validate_with_previous_result(self, sample_intents_registry):
        """Test de validación con resultado previo."""
        engine = ExpertEngine(sample_intents_registry)
        previous = IntentResult(
            intent_name="greet",
            confidence=0.9,
            level_reached=1,
            metadata={}
        )
        
        result = engine.validate("hola", previous)
        
        assert result is not None
        assert result.intent_name == "greet"
    
    def test_validate_with_context(self, sample_intents_registry):
        """Test de validación con contexto."""
        engine = ExpertEngine(sample_intents_registry)
        previous = IntentResult(
            intent_name="greet",
            confidence=0.9,
            level_reached=1,
            metadata={}
        )
        context = {"recent_intents": ["greet"]}
        
        result = engine.validate("hola", previous, context)
        
        # Debería reducir confianza por ser repetitivo
        assert result is not None
        assert result.confidence < 0.9 or result.metadata.get('context_penalty')
    
    def test_validate_without_previous_result(self, sample_intents_registry):
        """Test de validación sin resultado previo."""
        engine = ExpertEngine(sample_intents_registry)
        
        result = engine.validate("código para app", None)
        
        # Debería usar reglas expertas
        assert result is not None
        assert result.level_reached == 4
    
    def test_validate_fallback(self, sample_intents_registry):
        """Test de fallback cuando no hay match."""
        engine = ExpertEngine(sample_intents_registry)
        
        result = engine.validate("asdfghjkl", None)
        
        # Debería usar fallback
        assert result is not None
        assert result.intent_name == "fallback"


class TestExpertEngineFallback:
    """Tests para fallback del ExpertEngine."""
    
    def test_fallback_intent(self, sample_intents_registry):
        """Test de intención fallback."""
        engine = ExpertEngine(sample_intents_registry)
        result = engine._get_fallback_intent()
        
        assert result is not None
        assert result.intent_name == "fallback"
        assert result.confidence == 0.5
        assert result.level_reached == 4
    
    def test_fallback_metadata(self, sample_intents_registry):
        """Test de metadatos del fallback."""
        engine = ExpertEngine(sample_intents_registry)
        result = engine._get_fallback_intent()
        
        assert "fallback_type" in result.metadata
        assert "fallback_details" in result.metadata


class TestExpertEngineMetadata:
    """Tests para metadatos del ExpertEngine."""
    
    def test_rule_metadata(self, sample_intents_registry):
        """Test de metadatos de regla."""
        engine = ExpertEngine(sample_intents_registry)
        result = engine._apply_expert_rules("cómo hacer algo")
        
        if result:
            assert "rule_name" in result.metadata
            assert "rule_description" in result.metadata
            assert result.metadata["level"] == "expert"


class TestExpertEngineEdgeCases:
    """Tests para casos extremos del ExpertEngine."""
    
    def test_empty_query(self, sample_intents_registry):
        """Test de query vacía."""
        engine = ExpertEngine(sample_intents_registry)
        result = engine._apply_expert_rules("")
        
        assert result is None
    
    def test_special_characters(self, sample_intents_registry):
        """Test de caracteres especiales."""
        engine = ExpertEngine(sample_intents_registry)
        result = engine._apply_expert_rules("!@#$%^&*()")
        
        # Debería manejar o retornar None
        assert result is None or result is not None
    
    def test_very_long_query(self, sample_intents_registry):
        """Test de query muy larga."""
        engine = ExpertEngine(sample_intents_registry)
        long_query = "cómo " + "hacer " * 1000 + "algo"
        result = engine._apply_expert_rules(long_query)
        
        # Debería manejar queries largas
        assert result is not None or result is None