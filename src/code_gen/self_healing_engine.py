"""
Claw-Litle 1.0
self_healing_engine.py - Motor de Auto-Corrección

Bucle estricto de 3 iteraciones máximo:
1. Diagnosticador: Clasifica el error
2. Knowledge Base: Busca fix pre-testeado
3. Correktor: Aplica el fix
4. Validador: Comprueba que el fix funciona

Nunca modifica código original, retorna sugerencias.
"""

import re
import json
import logging
import traceback
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Tipo de error detectado."""
    IMPORT_ERROR = "import_error"
    SYNTAX_ERROR = "syntax_error"
    NAME_ERROR = "name_error"
    ATTRIBUTE_ERROR = "attribute_error"
    TYPE_ERROR = "type_error"
    KEY_ERROR = "key_error"
    INDEX_ERROR = "index_error"
    VALUE_ERROR = "value_error"
    RUNTIME_ERROR = "runtime_error"
    UNKNOWN = "unknown"


class DiagnosisStatus(Enum):
    """Estado del diagnóstico."""
    SUCCESS = "success"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass
class ErrorInfo:
    """Información del error detectado."""
    error_type: ErrorType
    message: str
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    original_exception: Optional[Exception] = None


@dataclass
class HealingFix:
    """Fix propuesto por el sistema."""
    description: str
    original_code: str
    fixed_code: str
    confidence: float
    source: str  # "knowledge_base" o "generated"
    line_number: Optional[int] = None


@dataclass
class HealingResult:
    """Resultado del proceso de auto-curación."""
    success: bool
    iterations_used: int
    error_info: Optional[ErrorInfo] = None
    fixes: List[HealingFix] = field(default_factory=list)
    validation_passed: bool = False
    final_code: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class HealingConfig:
    """Configuración del motor."""
    max_iterations: int = 3
    min_confidence: float = 0.70
    load_knowledge_base: bool = True
    auto_apply_fixes: bool = False


class Diagnosticador:
    """Clasifica el error."""
    
    def diagnose(self, exception: Exception, code: str) -> ErrorInfo:
        """Diagnostica el tipo de error."""
        error_type = ErrorType.UNKNOWN
        message = str(exception)
        line_number = None
        code_snippet = None
        
        # Extraer número de línea del traceback
        tb_lines = traceback.format_exception(type(exception), exception, exception.__traceback__)
        for line in tb_lines:
            if 'line' in line.lower():
                try:
                    match = re.search(r'line (\d+)', line)
                    if match:
                        line_number = int(match.group(1))
                except (ValueError, AttributeError, re.error):
                    pass
        
        # Extraer snippet de código si hay número de línea
        if line_number is not None:
            code_lines = code.splitlines()
            if 0 < line_number <= len(code_lines):
                code_snippet = code_lines[line_number - 1].strip()
        
        # Clasificar por tipo de excepción
        if isinstance(exception, ImportError) or isinstance(exception, ModuleNotFoundError):
            error_type = ErrorType.IMPORT_ERROR
        elif isinstance(exception, SyntaxError):
            error_type = ErrorType.SYNTAX_ERROR
            line_number = exception.lineno
        elif isinstance(exception, NameError):
            error_type = ErrorType.NAME_ERROR
        elif isinstance(exception, AttributeError):
            error_type = ErrorType.ATTRIBUTE_ERROR
        elif isinstance(exception, TypeError):
            error_type = ErrorType.TYPE_ERROR
        elif isinstance(exception, KeyError):
            error_type = ErrorType.KEY_ERROR
        elif isinstance(exception, IndexError):
            error_type = ErrorType.INDEX_ERROR
        elif isinstance(exception, ValueError):
            error_type = ErrorType.VALUE_ERROR
        elif isinstance(exception, RuntimeError):
            error_type = ErrorType.RUNTIME_ERROR
        
        return ErrorInfo(
            error_type=error_type,
            message=message,
            line_number=line_number,
            code_snippet=code_snippet,
            original_exception=exception
        )


class KnowledgeBase:
    """Busca fixes pre-testeados."""
    
    def __init__(self, kb_dir: Optional[str] = None):
        if kb_dir:
            self.kb_dir = Path(kb_dir)
        else:
            self.kb_dir = Path(__file__).parent.parent / "config" / "templates" / "self_healing_fixes"
        
        self._rules: Dict[ErrorType, List[Dict]] = {}
        self._load_rules()
    
    def _load_rules(self):
        """Carga reglas desde archivos JSON."""
        if not self.kb_dir.exists():
            logger.warning(f"Directorio KB no existe: {self.kb_dir}")
            self._load_builtin_rules()
            return
        
        for file_path in self.kb_dir.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    rules = json.load(f)
                    for rule in rules.get("rules", []):
                        error_type = ErrorType(rule.get("error_type", "unknown"))
                        if error_type not in self._rules:
                            self._rules[error_type] = []
                        self._rules[error_type].append(rule)
            except Exception as e:
                logger.error(f"Error cargando regla {file_path}: {e}")
    
    def _load_builtin_rules(self):
        """Carga reglas integradas."""
        self._rules = {
            ErrorType.IMPORT_ERROR: [
                {
                    "pattern": r"ModuleNotFoundError: No module named '(\w+)'",
                    "fix_template": "import {module}\n# Si falla, instalar con: pip install {module}",
                    "confidence": 0.9,
                    "description": "Importar módulo faltante"
                }
            ],
            ErrorType.SYNTAX_ERROR: [
                {
                    "pattern": r"unexpected EOF while parsing",
                    "fix_template": "# Verificar paréntesis/corchetes/llaves balanceados",
                    "confidence": 0.8,
                    "description": "EOF inesperado"
                }
            ],
            ErrorType.NAME_ERROR: [
                {
                    "pattern": r"name '(\w+)' is not defined",
                    "fix_template": "# Definir variable '{var}' antes de usar",
                    "confidence": 0.7,
                    "description": "Variable no definida"
                }
            ],
            ErrorType.ATTRIBUTE_ERROR: [
                {
                    "pattern": r"'.+' has no attribute '(\w+)'",
                    "fix_template": "# Verificar que el objeto tiene el atributo '{attr}'",
                    "confidence": 0.75,
                    "description": "Atributo inexistente"
                }
            ],
            ErrorType.TYPE_ERROR: [
                {
                    "pattern": r"unsupported operand type",
                    "fix_template": "# Convertir tipos antes de operar",
                    "confidence": 0.7,
                    "description": "Tipos incompatibles"
                }
            ]
        }
    
    def find_fixes(self, error_info: ErrorInfo) -> List[Dict]:
        """Busca fixes para el error."""
        fixes = []
        
        if error_info.error_type in self._rules:
            for rule in self._rules[error_info.error_type]:
                if re.search(rule.get("pattern", ""), error_info.message):
                    fixes.append(rule)
        
        return fixes


class Correktor:
    """Aplica fixes al código."""
    
    def apply_fix(self, code: str, fix_rule: Dict, error_info: ErrorInfo) -> Optional[HealingFix]:
        """Aplica un fix específico."""
        try:
            # Extraer variables del fix
            fix_template = fix_rule.get("fix_template", "")
            
            # Reemplazar variables comunes
            replacements = {
                "{module}": error_info.message.split("'")[1] if "'" in error_info.message else "unknown",
                "{var}": error_info.message.split("'")[1] if "'" in error_info.message else "unknown",
                "{attr}": error_info.message.split("'")[1] if "'" in error_info.message else "unknown",
                "{line}": str(error_info.line_number) if error_info.line_number else "unknown"
            }
            
            fixed_code = fix_template
            for key, value in replacements.items():
                fixed_code = fixed_code.replace(key, value)
            
            # Generar código corregido
            if error_info.line_number and error_info.code_snippet:
                lines = code.splitlines()
                if 0 < error_info.line_number <= len(lines):
                    lines[error_info.line_number - 1] = fixed_code
                    final_code = "\n".join(lines)
                else:
                    final_code = code + "\n" + fixed_code
            else:
                final_code = code + "\n" + fixed_code
            
            return HealingFix(
                description=fix_rule.get("description", "Fix aplicado"),
                original_code=error_info.code_snippet or "",
                fixed_code=fixed_code,
                confidence=fix_rule.get("confidence", 0.5),
                source="knowledge_base",
                line_number=error_info.line_number
            )
            
        except Exception as e:
            logger.error(f"Error aplicando fix: {e}")
            return None


class Validador:
    """Valida que el fix funciona."""
    
    def validate(self, code: str) -> Tuple[bool, Optional[Exception]]:
        """Valida código Python."""
        try:
            # Solo compilación (no ejecución)
            compile(code, '<string>', 'exec')
            return True, None
        except Exception as e:
            return False, e


class SelfHealingEngine:
    """
    Motor de Auto-Corrección.
    
    Sigue estrictamente el bucle de 3 iteraciones:
    1. Diagnosticador
    2. Knowledge Base
    3. Correktor
    4. Validador
    """
    
    def __init__(self, config: HealingConfig = None):
        self.config = config or HealingConfig()
        self.diagnosticador = Diagnosticador()
        self.knowledge_base = KnowledgeBase()
        self.correktor = Correktor()
        self.validador = Validador()
        logger.info("SelfHealingEngine inicializado")
    
    def heal(self, code: str, exception: Exception) -> HealingResult:
        """
        Intenta auto-corregir código con error.
        
        Args:
            code: Código original con error
            exception: Excepción capturada
            
        Returns:
            HealingResult con el resultado
        """
        current_code = code
        fixes_applied = []
        
        for iteration in range(1, self.config.max_iterations + 1):
            logger.info(f"🔧 Iteración {iteration}/{self.config.max_iterations}")
            
            # 1. Diagnosticador
            error_info = self.diagnosticador.diagnose(exception, current_code)
            logger.info(f"   Error: {error_info.error_type.value} - {error_info.message[:100]}")
            
            # 2. Knowledge Base
            kb_fixes = self.knowledge_base.find_fixes(error_info)
            if not kb_fixes:
                logger.warning("   No se encontraron fixes en KB")
                break
            
            # 3. Correktor
            fix_applied = None
            for fix_rule in kb_fixes:
                if fix_rule.get("confidence", 0) >= self.config.min_confidence:
                    fix = self.correktor.apply_fix(current_code, fix_rule, error_info)
                    if fix:
                        fix_applied = fix
                        fixes_applied.append(fix)
                        break
            
            if not fix_applied:
                logger.warning("   No se pudo aplicar ningún fix")
                break
            
            # Aplicar fix al código
            if fix_applied.line_number and fix_applied.line_number > 0:
                lines = current_code.splitlines()
                if fix_applied.line_number <= len(lines):
                    lines[fix_applied.line_number - 1] = fix_applied.fixed_code
                    current_code = "\n".join(lines)
            else:
                current_code = current_code + "\n" + fix_applied.fixed_code
            
            # 4. Validador
            is_valid, validation_error = self.validador.validate(current_code)
            
            if is_valid:
                logger.info(f"   ✅ Fix validado en iteración {iteration}")
                return HealingResult(
                    success=True,
                    iterations_used=iteration,
                    error_info=error_info,
                    fixes=fixes_applied,
                    validation_passed=True,
                    final_code=current_code
                )
            else:
                logger.info(f"   ⚠️ Fix no válido, reintentando...")
                exception = validation_error
        
        # No se logró corregir
        return HealingResult(
            success=False,
            iterations_used=len(fixes_applied),
            error_info=self.diagnosticador.diagnose(exception, current_code) if 'exception' in locals() else None,
            fixes=fixes_applied,
            validation_passed=False,
            final_code=current_code if 'current_code' in locals() else code,
            error_message=f"No se pudo corregir el código después de {len(fixes_applied)} intentos"
        )
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas del motor."""
        return {
            "config": {
                "max_iterations": self.config.max_iterations,
                "min_confidence": self.config.min_confidence
            },
            "knowledge_base_size": sum(len(rules) for rules in self.knowledge_base._rules.values())
        }


# Función helper para uso rápido
def auto_heal(code: str, exception: Exception) -> HealingResult:
    """Wrapper para auto-corregir código rápidamente."""
    engine = SelfHealingEngine()
    return engine.heal(code, exception)


if __name__ == "__main__":
    # Test rápido
    test_code = """
def greet(name):
    print(f"Hola {name}!
"""
    
    try:
        compile(test_code, '<string>', 'exec')
    except SyntaxError as e:
        engine = SelfHealingEngine()
        result = engine.heal(test_code, e)
        
        print(f"✅ Success: {result.success}")
        print(f"🔄 Iteraciones: {result.iterations_used}")
        print(f"📝 Fixes: {len(result.fixes)}")
        if result.fixes:
            print(f"   Fix: {result.fixes[0].description}")
            print(f"   Confianza: {result.fixes[0].confidence:.0%}")