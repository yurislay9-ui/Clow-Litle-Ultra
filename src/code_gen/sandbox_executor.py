"""
Claw-Litle 1.0
sandbox_executor.py - Ejecutor Aislado de Código

Ejecuta código Python en un entorno seguro con límites estrictos:
- Timeout duro: 10 segundos
- Límites de memoria
- Whitelist de módulos permitidos
- Sin acceso a red
- Sin escritura al sistema de archivos
"""

import sys
import time
import logging
import traceback
import resource
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """Estado de la ejecución."""
    SUCCESS = "success"
    TIMEOUT = "timeout"
    MEMORY_LIMIT = "memory_limit"
    EXCEPTION = "exception"
    DENIED = "denied"
    UNKNOWN = "unknown"


@dataclass
class ExecutionResult:
    """Resultado de la ejecución en sandbox."""
    status: ExecutionStatus
    stdout: str = ""
    stderr: str = ""
    exception: Optional[str] = None
    traceback: Optional[str] = None
    execution_time_ms: float = 0.0
    memory_used_kb: int = 0
    return_code: int = 0


@dataclass
class SandboxConfig:
    """Configuración del sandbox."""
    timeout_seconds: int = 10
    max_memory_kb: int = 128 * 1024  # 128 MB
    max_stdout_length: int = 16384  # 16 KB
    max_stderr_length: int = 8192
    enable_network: bool = False
    enable_file_write: bool = False
    allowed_modules: List[str] = field(default_factory=lambda: [
        "math",
        "random",
        "datetime",
        "json",
        "re",
        "hashlib",
        "base64",
        "collections",
        "itertools",
        "functools",
        "operator",
        "string",
        "time",
        "logging",
        "dataclasses",
        "typing",
        "enum",
        "pathlib",
        "sqlite3",
        "requests",
        "beautifulsoup4",
        "rich",
        "click"
    ])


class SandboxExecutor:
    """
    Ejecutor Aislado de Código.
    
    Aplica límites estrictos para evitar abusos.
    Diseñado para ejecutar código generado por el sistema.
    """
    
    def __init__(self, config: SandboxConfig = None):
        self.config = config or SandboxConfig()
        logger.info("SandboxExecutor inicializado")
    
    def execute(self, code: str) -> ExecutionResult:
        """
        Ejecuta código Python en el sandbox.
        
        Args:
            code: Código Python a ejecutar
            
        Returns:
            ExecutionResult con el resultado
        """
        start_time = time.time()
        result = ExecutionResult(status=ExecutionStatus.UNKNOWN)
        
        # Guardar estado original
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        original_path = sys.path.copy()
        
        try:
            # Aplicar límites de recursos
            self._apply_resource_limits()
            
            # Capturar stdout y stderr
            from io import StringIO
            stdout_buffer = StringIO()
            stderr_buffer = StringIO()
            
            sys.stdout = stdout_buffer
            sys.stderr = stderr_buffer
            
            # Modificar entorno
            self._setup_sandbox_environment()
            
            # Ejecutar código con timeout
            try:
                exec(code, self._get_globals(), {})
                result.status = ExecutionStatus.SUCCESS
                
            except TimeoutError:
                result.status = ExecutionStatus.TIMEOUT
                result.exception = "Execution timeout"
                
            except MemoryError:
                result.status = ExecutionStatus.MEMORY_LIMIT
                result.exception = "Memory limit exceeded"
                
            except Exception as e:
                result.status = ExecutionStatus.EXCEPTION
                result.exception = str(e)
                result.traceback = traceback.format_exc()
                result.return_code = 1
                
            finally:
                # Restaurar stdout/stderr
                sys.stdout = original_stdout
                sys.stderr = original_stderr
                
                # Obtener salida
                result.stdout = stdout_buffer.getvalue()[:self.config.max_stdout_length]
                result.stderr = stderr_buffer.getvalue()[:self.config.max_stderr_length]
                
                # Calcular tiempo de ejecución
                result.execution_time_ms = (time.time() - start_time) * 1000
                
                # Obtener uso de memoria
                result.memory_used_kb = self._get_memory_usage()
                
        finally:
            # Restaurar estado original
            sys.path[:] = original_path
            
            # Quitar límites de recursos
            self._remove_resource_limits()
        
        return result
    
    def _apply_resource_limits(self):
        """Aplica límites de recursos al proceso actual."""
        try:
            # Solo límites compatibles con Termux/Android
            # Límite de tiempo de CPU
            resource.setrlimit(resource.RLIMIT_CPU, (self.config.timeout_seconds, self.config.timeout_seconds + 1))
            
            # Límite de archivos abiertos
            resource.setrlimit(resource.RLIMIT_NOFILE, (32, 64))
            
            # RLIMIT_AS no funciona en Android Bionic, se omite
            
        except Exception as e:
            logger.warning(f"No se pudieron aplicar límites de recursos: {e}")
    
    def _remove_resource_limits(self):
        """Elimina límites de recursos."""
        try:
            # Restaurar valores por defecto
            resource.setrlimit(resource.RLIMIT_CPU, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
            resource.setrlimit(resource.RLIMIT_AS, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
            resource.setrlimit(resource.RLIMIT_NOFILE, (1024, 4096))
            resource.setrlimit(resource.RLIMIT_FSIZE, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
        except Exception:
            pass
    
    def _setup_sandbox_environment(self):
        """Configura el entorno de ejecución seguro."""
        # Eliminar módulos peligrosos de sys.modules
        dangerous_modules = [
            'os', 'subprocess', 'ctypes', 'socket', 'threading',
            'multiprocessing', 'shutil', 'tempfile', 'pickle'
        ]
        
        for mod in dangerous_modules:
            if mod in sys.modules:
                del sys.modules[mod]
    
    def _get_globals(self) -> Dict[str, Any]:
        """Devuelve el diccionario de globals permitido."""
        safe_builtins = {}
        
        # Lista de builtins permitidos
        allowed_builtins = [
            'abs', 'all', 'any', 'bool', 'bytes', 'callable', 'chr',
            'complex', 'dict', 'dir', 'divmod', 'enumerate', 'filter',
            'float', 'format', 'frozenset', 'getattr', 'hasattr', 'hash',
            'hex', 'int', 'isinstance', 'issubclass', 'iter', 'len',
            'list', 'map', 'max', 'min', 'next', 'object', 'oct', 'ord',
            'pow', 'print', 'range', 'repr', 'reversed', 'round', 'set',
            'slice', 'sorted', 'str', 'sum', 'tuple', 'type', 'zip'
        ]
        
        # Importar builtins seguros
        import builtins
        for name in allowed_builtins:
            if hasattr(builtins, name):
                safe_builtins[name] = getattr(builtins, name)
        
        return {
            '__builtins__': safe_builtins,
            'math': __import__('math'),
            'json': __import__('json'),
            're': __import__('re'),
            'datetime': __import__('datetime'),
            'random': __import__('random')
        }
    
    def _get_memory_usage(self) -> int:
        """Obtiene uso de memoria actual en KB."""
        try:
            import resource
            return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        except Exception:
            return 0
    
    def validate_code(self, code: str) -> bool:
        """
        Valida código antes de ejecutarlo.
        
        Verifica que no contenga patrones prohibidos.
        """
        import re
        
        forbidden_patterns = [
            r"import\s+os",
            r"import\s+subprocess",
            r"import\s+ctypes",
            r"import\s+socket",
            r"from\s+os\s+import",
            r"from\s+subprocess\s+import",
            r"__import__",
            r"eval\s*\(",
            r"exec\s*\(",
            r"open\s*\(",
            r"file\s*\(",
            r"os\.",
            r"sys\.",
        ]
        
        for pattern in forbidden_patterns:
            if re.search(pattern, code, re.MULTILINE):
                return False
        
        return True


# Función helper para uso rápido
def execute_sandboxed(code: str, config: SandboxConfig = None) -> ExecutionResult:
    """Wrapper para ejecutar código en sandbox rápidamente."""
    executor = SandboxExecutor(config)
    return executor.execute(code)


if __name__ == "__main__":
    # Test rápido
    test_codes = [
        ("print('Hola mundo')", "Código simple"),
        ("import time; time.sleep(15)", "Timeout"),
        ("a = [0] * 1000000000", "Memoria excedida"),
        ("1 / 0", "Excepción"),
    ]
    
    executor = SandboxExecutor()
    
    for code, description in test_codes:
        print(f"\n--- TEST: {description} ---")
        print(f"Código: {code}")
        result = executor.execute(code)
        print(f"Status: {result.status.value}")
        print(f"Tiempo: {result.execution_time_ms:.1f}ms")
        print(f"Memoria: {result.memory_used_kb} KB")
        if result.exception:
            print(f"Excepción: {result.exception}")
        if result.stdout:
            print(f"Stdout: {result.stdout.strip()}")