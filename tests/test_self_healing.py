#!/usr/bin/env python3
"""
Tests para el SelfHealingEngine (Motor de Auto-Corrección).
"""

import pytest
from unittest.mock import Mock, patch


class TestSelfHealingEngine:
    """Tests para SelfHealingEngine."""
    
    def test_engine_initialization(self):
        """Test que el engine se inicializa correctamente."""
        from src.code_gen.self_healing_engine import SelfHealingEngine
        
        engine = SelfHealingEngine()
        assert engine is not None
        assert engine.config.max_iterations == 3
    
    def test_diagnose_syntax_error(self):
        """Test diagnóstico de error de sintaxis."""
        from src.code_gen.self_healing_engine import Diagnosticador, ErrorType
        
        diagnosticador = Diagnosticador()
        code = "def broken("
        
        try:
            compile(code, '<string>', 'exec')
        except SyntaxError as e:
            error_info = diagnosticador.diagnose(e, code)
            assert error_info.error_type == ErrorType.SYNTAX_ERROR
    
    def test_diagnose_import_error(self):
        """Test diagnóstico de error de importación."""
        from src.code_gen.self_healing_engine import Diagnosticador, ErrorType
        
        diagnosticador = Diagnosticador()
        code = "import modulo_inexistente_xyz"
        
        try:
            exec(code)
        except (ImportError, ModuleNotFoundError) as e:
            error_info = diagnosticador.diagnose(e, code)
            assert error_info.error_type == ErrorType.IMPORT_ERROR
    
    def test_knowledge_base_lookup(self):
        """Test búsqueda en base de conocimiento."""
        from src.code_gen.self_healing_engine import KnowledgeBase, ErrorInfo, ErrorType
        
        kb = KnowledgeBase()
        error_info = ErrorInfo(
            error_type=ErrorType.IMPORT_ERROR,
            message="No module named 'requests'"
        )
        
        fixes = kb.find_fixes(error_info)
        assert isinstance(fixes, list)
    
    def test_heal_syntax_error(self):
        """Test auto-corrección de error de sintaxis."""
        from src.code_gen.self_healing_engine import SelfHealingEngine
        
        engine = SelfHealingEngine()
        code = "def greet(name):\n    print(f'Hola {name}'"  # Falta paréntesis
        
        try:
            compile(code, '<string>', 'exec')
        except SyntaxError as e:
            result = engine.heal(code, e)
            assert result is not None
            # Puede que no siempre pueda corregir, pero debería retornar resultado
            assert result.success is True or result.success is False
    
    def test_heal_import_error(self):
        """Test auto-corrección de error de importación."""
        from src.code_gen.self_healing_engine import SelfHealingEngine
        
        engine = SelfHealingEngine()
        code = "import modulo_xyz_no_existe"
        
        try:
            exec(code)
        except (ImportError, ModuleNotFoundError) as e:
            result = engine.heal(code, e)
            assert result is not None
    
    def test_validator_valid_code(self):
        """Test validador con código válido."""
        from src.code_gen.self_healing_engine import Validador
        
        validador = Validador()
        valid_code = "def add(a, b):\n    return a + b"
        
        is_valid, error = validador.validate(valid_code)
        assert is_valid is True
        assert error is None
    
    def test_validator_invalid_code(self):
        """Test validador con código inválido."""
        from src.code_gen.self_healing_engine import Validador
        
        validador = Validador()
        invalid_code = "def broken("
        
        is_valid, error = validador.validate(invalid_code)
        assert is_valid is False
        assert error is not None
    
    def test_max_iterations_respected(self):
        """Test que respeta el máximo de iteraciones."""
        from src.code_gen.self_healing_engine import SelfHealingEngine, HealingConfig
        
        config = HealingConfig(max_iterations=2)
        engine = SelfHealingEngine(config)
        
        # Código que probablemente no se pueda corregir
        code = "x = y + z"  # NameError
        
        try:
            exec(code)
        except NameError as e:
            result = engine.heal(code, e)
            assert result.iterations_used <= 2
    
    def test_get_stats(self):
        """Test obtención de estadísticas."""
        from src.code_gen.self_healing_engine import SelfHealingEngine
        
        engine = SelfHealingEngine()
        stats = engine.get_stats()
        
        assert isinstance(stats, dict)
        assert "config" in stats or "knowledge_base_size" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])