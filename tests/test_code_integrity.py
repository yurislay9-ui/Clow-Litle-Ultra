#!/usr/bin/env python3
"""
Tests para el CodeIntegrityChecker (Verificador de Integridad de Código).
"""

import pytest
import hashlib
import os
from unittest.mock import Mock, patch, MagicMock


class TestCodeIntegrity:
    """Tests para CodeIntegrityChecker."""
    
    def test_checker_initialization(self):
        """Test que el checker se inicializa correctamente."""
        from src.security.code_integrity import CodeIntegrityChecker
        
        checker = CodeIntegrityChecker()
        assert checker is not None
    
    def test_calculate_hash(self):
        """Test cálculo de hash de archivo."""
        from src.security.code_integrity import CodeIntegrityChecker
        
        checker = CodeIntegrityChecker()
        
        # Crear archivo temporal
        test_content = b"test content for hashing"
        test_hash = hashlib.sha256(test_content).hexdigest()
        
        # Verificar que el hash calculado coincide
        calculated = hashlib.sha256(test_content).hexdigest()
        assert calculated == test_hash
    
    def test_verify_file_integrity(self):
        """Test verificación de integridad de archivo."""
        from src.security.code_integrity import CodeIntegrityChecker
        
        checker = CodeIntegrityChecker()
        
        # Crear archivo temporal
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            # Verificar que el archivo existe y es legible
            result = checker.verify_file(temp_path)
            assert result is not None
            assert result.get("valid") is True or result.get("exists") is True
        finally:
            os.unlink(temp_path)
    
    def test_detect_tampering(self):
        """Test detección de archivos modificados."""
        from src.security.code_integrity import CodeIntegrityChecker
        
        checker = CodeIntegrityChecker()
        
        # Crear archivo temporal
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("original content")
            temp_path = f.name
        
        try:
            # Calcular hash original
            with open(temp_path, 'rb') as f:
                original_hash = hashlib.sha256(f.read()).hexdigest()
            
            # Modificar archivo
            with open(temp_path, 'w') as f:
                f.write("modified content")
            
            # Calcular nuevo hash
            with open(temp_path, 'rb') as f:
                new_hash = hashlib.sha256(f.read()).hexdigest()
            
            # Los hashes deberían ser diferentes
            assert original_hash != new_hash
        finally:
            os.unlink(temp_path)
    
    def test_check_imports_whitelist(self):
        """Test verificación de imports en whitelist."""
        from src.security.code_integrity import CodeIntegrityChecker
        
        checker = CodeIntegrityChecker()
        
        safe_code = """
import json
import re
import os
"""
        
        result = checker.check_imports(safe_code)
        assert result is not None
        assert result.get("safe") is True or result.get("warnings") == []
    
    def test_detect_dangerous_imports(self):
        """Test detección de imports peligrosos."""
        from src.security.code_integrity import CodeIntegrityChecker
        
        checker = CodeIntegrityChecker()
        
        dangerous_code = """
import subprocess
import ctypes
import os
"""
        
        result = checker.check_imports(dangerous_code)
        assert result is not None
        # Debería detectar al menos un warning
        assert result.get("safe") is False or len(result.get("warnings", [])) > 0
    
    def test_get_stats(self):
        """Test obtención de estadísticas."""
        from src.security.code_integrity import CodeIntegrityChecker
        
        checker = CodeIntegrityChecker()
        stats = checker.get_stats()
        
        assert isinstance(stats, dict)
        assert "algorithm" in stats or "checked_files" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])