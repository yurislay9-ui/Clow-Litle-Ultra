#!/usr/bin/env python3
"""
Tests para el SemanticEngine (Motor Semántico con ONNX).
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestSemanticEngine:
    """Tests para SemanticEngine."""
    
    def test_engine_initialization(self):
        """Test que el engine se inicializa correctamente."""
        from src.engine.nivel_3_semantic import SemanticEngine
        
        # Crear engine sin cargar modelo (para tests rápidos)
        engine = SemanticEngine(model_path=None, threshold=0.89)
        assert engine is not None
        assert engine.threshold == 0.89
    
    def test_tokenize_basic(self):
        """Test tokenización básica."""
        from src.engine.nivel_3_semantic import SemanticEngine
        
        engine = SemanticEngine(model_path=None, threshold=0.89)
        
        # Probar tokenización simple
        tokens = engine._tokenize("Hola mundo")
        assert isinstance(tokens, list)
    
    def test_tokenize_removes_stopwords(self):
        """Test que tokenización remueve stopwords."""
        from src.engine.nivel_3_semantic import SemanticEngine
        
        engine = SemanticEngine(model_path=None, threshold=0.89)
        
        text = "el la de que y en un hola mundo"
        tokens = engine._tokenize(text)
        
        # Debería remover stopwords comunes
        assert len(tokens) < len(text.split())
    
    def test_similarity_calculation(self):
        """Test cálculo de similitud."""
        from src.engine.nivel_3_semantic import SemanticEngine
        
        engine = SemanticEngine(model_path=None, threshold=0.89)
        
        # Simular vectores idénticos
        vec1 = [1.0, 0.5, 0.2]
        vec2 = [1.0, 0.5, 0.2]
        
        similarity = engine._cosine_similarity(vec1, vec2)
        assert similarity == 1.0  # Vectores idénticos = 1.0
    
    def test_similarity_different_vectors(self):
        """Test similitud con vectores diferentes."""
        from src.engine.nivel_3_semantic import SemanticEngine
        
        engine = SemanticEngine(model_path=None, threshold=0.89)
        
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        
        similarity = engine._cosine_similarity(vec1, vec2)
        assert similarity == 0.0  # Vectores ortogonales = 0.0
    
    def test_match_without_model(self):
        """Test match sin modelo cargado."""
        from src.engine.nivel_3_semantic import SemanticEngine
        
        engine = SemanticEngine(model_path=None, threshold=0.89)
        intents_registry = {
            "greet": {"patterns": ["hola", "buenos días"]}
        }
        
        result = engine.match("hola", intents_registry)
        # Sin modelo, debería retornar None o resultado con baja confianza
        assert result is None or result.confidence < 0.89
    
    def test_model_loading_failure(self):
        """Test que maneja falla en carga de modelo."""
        from src.engine.nivel_3_semantic import SemanticEngine
        
        # Intentar cargar con ruta inválida
        engine = SemanticEngine(model_path="/ruta/invalida/model.onnx", threshold=0.89)
        
        # Debería manejar el error gracefulmente
        assert engine._model is None or not engine._model_loaded
    
    def test_unload_model(self):
        """Test descarga de modelo."""
        from src.engine.nivel_3_semantic import SemanticEngine
        
        engine = SemanticEngine(model_path=None, threshold=0.89)
        # Debería poder llamar a unload sin error
        engine.unload()
    
    def test_get_stats(self):
        """Test obtención de estadísticas."""
        from src.engine.nivel_3_semantic import SemanticEngine
        
        engine = SemanticEngine(model_path=None, threshold=0.89)
        stats = engine.get_stats()
        
        assert isinstance(stats, dict)
        assert "threshold" in stats or "model_loaded" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])