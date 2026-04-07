"""Módulo de integridad de código - Implementación completa"""
import hashlib
from pathlib import Path
from typing import Dict, List

class CodeIntegrityChecker:
    """Verifica la integridad del código fuente"""
    
    SAFE_IMPORTS = {
        'os', 'sys', 're', 'json', 'time', 'datetime', 'pathlib',
        'typing', 'functools', 'itertools', 'collections',
        'asyncio', 'concurrent', 'threading', 'queue',
        'sqlite3', 'hashlib', 'hmac', 'base64',
        'requests', 'beautifulsoup4', 'lxml', 'numpy',
    }
    
    DANGEROUS_IMPORTS = {
        'subprocess', 'multiprocessing', 'socket', 'http',
        'eval', 'exec', 'compile', 'ctypes',
    }
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self._hash_cache: Dict[str, str] = {}
        
    def calculate_hash(self, file_path: str, algorithm: str = 'sha256') -> str:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
        hash_func = hashlib.new(algorithm)
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    
    def verify_file_integrity(self, file_path: str, expected_hash: str) -> bool:
        try:
            actual_hash = self.calculate_hash(file_path)
            return actual_hash == expected_hash
        except Exception:
            return False
    
    def detect_tampering(self, original_hash: str, current_hash: str) -> bool:
        return original_hash != current_hash
    
    def check_imports_whitelist(self, code: str) -> List[str]:
        import ast
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return ['Syntax error in code']
        violations = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split('.')[0] not in self.SAFE_IMPORTS:
                        violations.append(f"Import not whitelisted: {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.split('.')[0] not in self.SAFE_IMPORTS:
                    violations.append(f"Import from not whitelisted: {node.module}")
        return violations
    
    def detect_dangerous_imports(self, code: str) -> List[str]:
        import ast
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return ['Syntax error in code']
        dangers = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split('.')[0] in self.DANGEROUS_IMPORTS:
                        dangers.append(f"Dangerous import: {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.split('.')[0] in self.DANGEROUS_IMPORTS:
                    dangers.append(f"Dangerous import from: {node.module}")
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in ['eval', 'exec']:
                    dangers.append(f"Dangerous function call: {node.func.id}")
        return dangers
    
    def get_stats(self) -> Dict:
        return {
            'total_files_checked': len(self._hash_cache),
            'safe_imports_count': len(self.SAFE_IMPORTS),
            'dangerous_imports_count': len(self.DANGEROUS_IMPORTS),
            'cache_size': len(self._hash_cache),
        }
