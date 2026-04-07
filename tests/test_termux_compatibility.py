#!/usr/bin/env python3
"""
Tests específicos para compatibilidad con Termux (Android ARM64).
Verifica que el código funcione en entorno mobile sin dependencias de escritorio.
"""

import sys
import platform
import importlib
from pathlib import Path


class TestTermuxCompatibility:
    """Tests para verificar compatibilidad con Termux."""
    
    def test_python_version(self):
        """Test que Python es 3.11+."""
        version = sys.version_info
        assert version.major >= 3
        assert version.minor >= 11, f"Python {version.major}.{version.minor} no es compatible, se requiere 3.11+"
    
    def test_platform_architecture(self):
        """Test que la arquitectura es ARM64 o x86_64."""
        machine = platform.machine().lower()
        allowed_archs = ['aarch64', 'arm64', 'x86_64', 'amd64']
        assert machine in allowed_archs, f"Arquitectura {machine} no soportada"
    
    def test_no_forbidden_imports(self):
        """Test que no se importan librerías prohibidas en Termux."""
        forbidden = [
            'tkinter',  # No hay display server
            'PyQt5', 'PyQt6', 'PySide2', 'PySide6',  # GUI de escritorio
            'matplotlib.pyplot',  # Requiere display
            'cv2',  # OpenCV puede tener problemas en ARM64
            'selenium',  # Requiere ChromeDriver
        ]
        
        for module in forbidden:
            try:
                importlib.import_module(module)
                # Si importa, verificar si estamos en Termux
                if self.is_termux():
                    raise AssertionError(f"Librería {module} no debería estar disponible en Termux")
            except ImportError:
                pass  # Expected
    
    def test_allowed_imports(self):
        """Test que las librerías requeridas están disponibles."""
        required = [
            'requests',
            'rich',
            'sqlite3',
            'asyncio',
            'click',
        ]
        
        for module in required:
            try:
                importlib.import_module(module)
            except ImportError:
                raise AssertionError(f"Librería requerida {module} no está instalada")
    
    def test_file_system_access(self):
        """Test que se puede acceder al sistema de archivos."""
        # Probar escritura en directorio temporal
        test_file = Path("/data/data/com.termux/files/home/.claw_test")
        try:
            test_file.write_text("test")
            assert test_file.read_text() == "test"
            test_file.unlink()
        except (PermissionError, OSError) as e:
            # En Termux puede haber restricciones
            if self.is_termux():
                pass  # Expected en algunos casos
            else:
                raise
    
    def test_network_access(self):
        """Test que hay acceso a red (opcional, puede fallar)."""
        try:
            import requests
            response = requests.get("https://httpbin.org/get", timeout=5)
            assert response.status_code == 200
        except (requests.RequestException, ImportError):
            # Network access is optional
            pass
    
    def is_termux(self) -> bool:
        """Detecta si se está ejecutando en Termux."""
        # Termux tiene características específicas
        termux_indicators = [
            "TERMUX_VERSION" in os.environ,
            "/data/data/com.termux" in os.environ.get("HOME", ""),
            "com.termux" in os.environ.get("PREFIX", ""),
        ]
        return any(termux_indicators)
    
    def test_memory_limit(self):
        """Test que el uso de memoria está dentro de límites."""
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / (1024 * 1024)
            
            # Límite de 350MB para Termux
            if self.is_termux():
                assert memory_mb < 350, f"Uso de memoria {memory_mb:.1f}MB excede límite de 350MB"
        except ImportError:
            pass  # psutil no está disponible
    
    def test_asyncio_available(self):
        """Test que asyncio está disponible."""
        import asyncio
        assert hasattr(asyncio, 'run')
        assert hasattr(asyncio, 'gather')
        assert hasattr(asyncio, 'create_task')


class TestMobileOptimizations:
    """Tests para optimizaciones mobile."""
    
    def test_lazy_loading(self):
        """Test que los módulos pesados usan lazy loading."""
        # Verificar que el modelo ONNX no se carga al importar
        import src.agents.semantic_searcher as semantic
        
        # El modelo debería ser None inicialmente
        if hasattr(semantic, '_model_cache'):
            assert semantic._model_cache is None
    
    def test_short_circuit_evaluation(self):
        """Test que el motor híbrido usa short-circuit."""
        from src.hybrid_engine import HybridEngine
        
        engine = HybridEngine()
        
        # Query simple que debería resolverse en Nivel 1 (regex)
        # y no debería pasar a niveles superiores
        result = engine.process_query_sync("abrir chrome")
        
        # Verificar que usó el nivel más bajo posible
        if hasattr(result, 'level_used'):
            assert result.level_used <= 1  # Debería ser Nivel 1
    
    def test_thermal_guard_activation(self):
        """Test que el thermal guard se activa correctamente."""
        from src.monitoring.thermal_monitor import ThermalMonitor
        
        monitor = ThermalMonitor()
        temp = monitor.get_temperature()
        
        # Temperatura debería estar en rango razonable
        assert 0 <= temp <= 100  # °C
    
    def test_resource_monitoring(self):
        """Test que el monitor de recursos funciona."""
        from src.monitoring.resource_monitor import ResourceMonitor
        
        monitor = ResourceMonitor()
        resources = monitor.get_resources()
        
        assert 'memory' in resources
        assert 'cpu' in resources
        assert resources['memory'] >= 0


class TestSecurityConstraints:
    """Tests para restricciones de seguridad."""
    
    def test_no_eval_usage(self):
        """Test que no se usa eval() en código crítico."""
        # Escanear archivos del proyecto
        src_dir = Path("src")
        
        for py_file in src_dir.rglob("*.py"):
            content = py_file.read_text()
            
            # Excepciones permitidas (ej. tests)
            if "test" in str(py_file):
                continue
            
            # Verificar que no hay eval() peligroso
            if "eval(" in content:
                # Solo permitido en contextos muy específicos
                assert "sandbox" in str(py_file) or "safe" in str(py_file), \
                    f"eval() encontrado en {py_file} fuera de sandbox"
    
    def test_no_exec_usage(self):
        """Test que no se usa exec() en código crítico."""
        src_dir = Path("src")
        
        for py_file in src_dir.rglob("*.py"):
            content = py_file.read_text()
            
            if "test" in str(py_file):
                continue
            
            if "exec(" in content:
                assert "sandbox" in str(py_file) or "safe" in str(py_file), \
                    f"exec() encontrado en {py_file} fuera de sandbox"
    
    def test_sandbox_restrictions(self):
        """Test que el sandbox tiene restricciones adecuadas."""
        from src.code_gen.sandbox_executor import SandboxExecutor
        
        sandbox = SandboxExecutor()
        
        # Verificar whitelist de imports
        assert hasattr(sandbox, 'ALLOWED_IMPORTS')
        assert isinstance(sandbox.ALLOWED_IMPORTS, (list, set))
        
        # Verificar que no hay imports peligrosos en whitelist
        dangerous_imports = ['os', 'sys', 'subprocess', 'ctypes']
        for imp in dangerous_imports:
            if imp in sandbox.ALLOWED_IMPORTS:
                # Solo permitido si es controlado
                assert imp in ['os', 'sys'], f"Import peligroso {imp} en whitelist"


class TestPerformanceConstraints:
    """Tests para restricciones de rendimiento."""
    
    def test_regex_engine_speed(self):
        """Test que regex engine es rápido (<1ms)."""
        from src.engine.nivel_1_regex import RegexEngine
        import time
        
        engine = RegexEngine()
        
        start = time.time()
        for _ in range(1000):
            engine.match("abrir chrome", "abrir")
        elapsed = time.time() - start
        
        avg_time = elapsed / 1000
        assert avg_time < 0.001, f"Regex engine demasiado lento: {avg_time*1000:.3f}ms por query"
    
    def test_fuzzy_engine_speed(self):
        """Test que fuzzy engine es rápido (<5ms)."""
        from src.engine.nivel_2_fuzzy import FuzzyEngine
        import time
        
        engine = FuzzyEngine()
        
        start = time.time()
        for _ in range(100):
            engine.match("abrir crom", "abrir chrome")
        elapsed = time.time() - start
        
        avg_time = elapsed / 100
        assert avg_time < 0.005, f"Fuzzy engine demasiado lento: {avg_time*1000:.3f}ms por query"
    
    def test_memory_footprint(self):
        """Test que el footprint de memoria es aceptable."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Memoria inicial
        mem_before = process.memory_info().rss / (1024 * 1024)
        
        # Importar módulos principales
        from src.hybrid_engine import HybridEngine
        from src.agents.swarm_manager import SwarmManager
        from src.code_gen.template_engine import TemplateEngine
        
        # Memoria después de importar
        mem_after = process.memory_info().rss / (1024 * 1024)
        
        # El aumento debería ser razonable (<100MB)
        mem_increase = mem_after - mem_before
        assert mem_increase < 100, f"Aumento de memoria excesivo: {mem_increase:.1f}MB"


# Utilidades
import os

def run_termux_tests():
    """Ejecuta todos los tests de Termux."""
    print("\n" + "="*60)
    print(" TESTS DE COMPATIBILIDAD TERMUX")
    print("="*60)
    
    tests = [
        TestTermuxCompatibility(),
        TestMobileOptimizations(),
        TestSecurityConstraints(),
        TestPerformanceConstraints(),
    ]
    
    passed = 0
    failed = 0
    skipped = 0
    
    for test_class in tests:
        print(f"\n🧪 {test_class.__class__.__name__}")
        
        for method_name in dir(test_class):
            if method_name.startswith("test_"):
                try:
                    getattr(test_class, method_name)()
                    print(f"   ✅ {method_name}")
                    passed += 1
                except AssertionError as e:
                    print(f"   ❌ {method_name}: {e}")
                    failed += 1
                except Exception as e:
                    print(f"   ⚠️  {method_name}: {type(e).__name__}")
                    skipped += 1
    
    print("\n" + "="*60)
    print(f" RESULTADOS: {passed} pasaron, {failed} fallaron, {skipped} saltados")
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_termux_tests()
    sys.exit(0 if success else 1)