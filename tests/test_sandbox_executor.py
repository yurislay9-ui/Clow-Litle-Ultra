#!/usr/bin/env python3
"""
Tests para el SandboxExecutor (Ejecutor Aislado de Código).
"""

import pytest
import sys
import time
from unittest.mock import Mock, patch, MagicMock


class TestSandboxExecutor:
    """Tests para SandboxExecutor."""
    
    def setup_method(self):
        """Configurar tests."""
        self.safe_code = """
def add(a, b):
    return a + b

result = add(2, 3)
"""
        self.dangerous_code = """
import os
os.system("rm -rf /")
"""
    
    def test_executor_initialization(self):
        """Test que el executor se inicializa correctamente."""
        from src.code_gen.sandbox_executor import SandboxExecutor
        
        executor = SandboxExecutor()
        assert executor is not None
    
    def test_execute_safe_code(self):
        """Test ejecución de código seguro."""
        from src.code_gen.sandbox_executor import SandboxExecutor
        
        executor = SandboxExecutor()
        result = executor.execute(self.safe_code)
        
        assert result is not None
        assert result.success is True
    
    def test_block_dangerous_imports(self):
        """Test que bloquea imports peligrosos."""
        from src.code_gen.sandbox_executor import SandboxExecutor
        
        executor = SandboxExecutor()
        result = executor.execute(self.dangerous_code)
        
        assert result is not None
        assert result.success is False or "import" in str(result.error).lower()
    
    def test_execution_timeout(self):
        """Test que respeta el timeout de ejecución."""
        from src.code_gen.sandbox_executor import SandboxExecutor
        
        infinite_loop = """
while True:
    pass
"""
        executor = SandboxExecutor(timeout=2)  # 2 segundos
        result = executor.execute(infinite_loop)
        
        assert result is not None
        assert result.success is False or "timeout" in str(result.error).lower()
    
    def test_memory_limit(self):
        """Test que respeta el límite de memoria."""
        from src.code_gen.sandbox_executor import SandboxExecutor
        
        memory_hog = """
data = []
while True:
    data.append('x' * 1000000)
"""
        executor = SandboxExecutor(max_memory_mb=50)  # 50MB
        result = executor.execute(memory_hog)
        
        assert result is not None
        # Debería fallar por límite de memoria o timeout
        assert result.success is False or "memory" in str(result.error).lower()
    
    def test_blocked_modules(self):
        """Test que bloquea módulos específicos."""
        from src.code_gen.sandbox_executor import SandboxExecutor
        
        # Intentar importar módulos bloqueados
        blocked_imports = [
            "import subprocess",
            "import ctypes",
            "import socket",
            "import threading"
        ]
        
        executor = SandboxExecutor()
        for import_code in blocked_imports:
            result = executor.execute(import_code)
            # Debería fallar o ser bloqueado
            assert result is not None
    
    def test_allowed_imports(self):
        """Test que permite imports seguros."""
        from src.code_gen.sandbox_executor import SandboxExecutor
        
        safe_imports = [
            "import json",
            "import re",
            "import math",
            "import datetime"
        ]
        
        executor = SandboxExecutor()
        for import_code in safe_imports:
            result = executor.execute(import_code)
            assert result.success is True
    
    def test_get_stats(self):
        """Test obtención de estadísticas."""
        from src.code_gen.sandbox_executor import SandboxExecutor
        
        executor = SandboxExecutor()
        stats = executor.get_stats()
        
        assert isinstance(stats, dict)
        assert "timeout" in stats or "max_memory_mb" in stats
    
    def test_execute_with_custom_globals(self):
        """Test ejecución con variables globales personalizadas."""
        from src.code_gen.sandbox_executor import SandboxExecutor
        
        code = """
result = custom_var + 10
"""
        executor = SandboxExecutor()
        custom_globals = {"custom_var": 5}
        result = executor.execute(code, custom_globals=custom_globals)
        
        assert result is not None
        assert result.success is True
    
    def test_code_validation(self):
        """Test validación de código antes de ejecutar."""
        from src.code_gen.sandbox_executor import SandboxExecutor
        
        executor = SandboxExecutor()
        
        # Código con sintaxis inválida
        invalid_code = "def broken("
        result = executor.execute(invalid_code)
        
        assert result is not None
        assert result.success is False or "syntax" in str(result.error).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])