"""
Claw-Litle 1.0
buddy_reviewer.py - Revisor Autónomo de Código

NUNCA MODIFICA EL CÓDIGO ORIGINAL. Solo evalúa y retorna un veredicto.

Categorías de evaluación:
- Seguridad: 40%
- Compatibilidad Termux/ARM64: 30%
- Calidad de Código: 20%
- Rendimiento: 10%
"""

import re
import ast
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class Verdict(Enum):
    """Veredicto del revisor."""
    APPROVED = "APPROVED"
    NEEDS_FIX = "NEEDS_FIX"
    BLOCKED = "BLOCKED"


@dataclass
class Issue:
    """Problema encontrado en el código."""
    category: str
    severity: str
    description: str
    line: Optional[int] = None
    code_snippet: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class ReviewResult:
    """Resultado completo de la revisión."""
    verdict: Verdict
    score: float
    issues: List[Issue] = field(default_factory=list)
    category_scores: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReviewConfig:
    """Configuración del revisor."""
    min_approval_score: float = 0.70
    block_on_critical: bool = True
    check_security: bool = True
    check_compatibility: bool = True
    check_quality: bool = True
    check_performance: bool = True
    category_weights: Dict[str, float] = field(default_factory=lambda: {
        "security": 0.40,
        "compatibility": 0.30,
        "quality": 0.20,
        "performance": 0.10
    })


class BuddyReviewer:
    """
    Revisor Autónomo de Código.
    
    REGLAS INQUEBRANTABLES:
    1. NUNCA modifica el código original
    2. NUNCA retorna código corregido
    3. Solo retorna análisis, veredicto y sugerencias
    4. Puntuación estricta según pesos predefinidos
    """
    
    def __init__(self, config: ReviewConfig = None):
        self.config = config or ReviewConfig()
        self._issues: List[Issue] = []
        
        # Patrones prohibidos
        self.forbidden_patterns = [
            (r"eval\s*\(", "Uso de eval() - riesgo de ejecución arbitraria", "critical"),
            (r"exec\s*\(", "Uso de exec() - riesgo de ejecución arbitraria", "critical"),
            (r"os\.system\s*\(", "Uso de os.system() - usa subprocess en su lugar", "high"),
            (r"subprocess\..*\(shell=True\)", "shell=True habilitado - riesgo de inyección", "critical"),
            (r"__import__\s*\(", "Import dinámico inseguro", "high"),
            (r"globals\s*\(\s*\)\[", "Acceso directo a globals()", "high"),
            (r"locals\s*\(\s*\)\[", "Acceso directo a locals()", "high"),
            (r"pickle\.load\s*\(", "Pickle inseguro - deserialización arbitraria", "critical"),
        ]
        
        # Patrones de incompatibilidad con Termux
        self.incompatible_patterns = [
            (r"tkinter|Tkinter", "Uso de Tkinter - GUI no soportada en Termux", "medium"),
            (r"PyQt|PySide", "Uso de Qt - GUI no soportada en Termux", "medium"),
            (r"pyautogui", "PyAutoGUI requiere X11 - no funciona en Termux", "medium"),
            (r"selenium", "Selenium requiere ChromeDriver de escritorio", "medium"),
            (r"matplotlib.*\.show\(\)", "Matplotlib modo GUI - usa backend Agg", "low"),
            (r"docker|kubernetes", "Docker no soportado en Termux ARM64", "medium"),
        ]
        
        # Patrones de mala calidad
        self.quality_patterns = [
            (r"print\s*\(", "Uso de print() - usa logging en su lugar", "low"),
            (r"except\s*:", "Except genérico - especifica la excepción", "medium"),
            (r"pass\s*$", "Pass vacío - agrega comentario o manejo", "low"),
            (r"TODO|FIXME", "Comentario pendiente", "low"),
        ]
        
        logger.info("BuddyReviewer inicializado")
    
    def review(self, code: str) -> ReviewResult:
        """
        Realiza una revisión completa del código.
        
        Args:
            code: Código Python a revisar
            
        Returns:
            ReviewResult con veredicto, puntuación y issues
        """
        self._issues.clear()
        category_scores: Dict[str, float] = {}
        
        # Análisis por categorías
        category_scores["security"] = self._review_security(code)
        category_scores["compatibility"] = self._review_compatibility(code)
        category_scores["quality"] = self._review_quality(code)
        category_scores["performance"] = self._review_performance(code)
        
        # Calcular puntuación final ponderada
        final_score = 0.0
        for category, weight in self.config.category_weights.items():
            final_score += category_scores[category] * weight
        
        # Determinar veredicto
        has_critical = any(i.severity == "critical" for i in self._issues)
        
        if has_critical and self.config.block_on_critical:
            verdict = Verdict.BLOCKED
        elif final_score >= self.config.min_approval_score:
            verdict = Verdict.APPROVED
        else:
            verdict = Verdict.NEEDS_FIX
        
        return ReviewResult(
            verdict=verdict,
            score=round(final_score, 2),
            issues=self._issues.copy(),
            category_scores={k: round(v, 2) for k, v in category_scores.items()},
            metadata={
                "total_issues": len(self._issues),
                "critical_issues": sum(1 for i in self._issues if i.severity == "critical"),
                "high_issues": sum(1 for i in self._issues if i.severity == "high"),
                "medium_issues": sum(1 for i in self._issues if i.severity == "medium"),
                "low_issues": sum(1 for i in self._issues if i.severity == "low")
            }
        )
    
    def _review_security(self, code: str) -> float:
        """Revisa seguridad del código (40% del peso)."""
        score = 1.0
        issues_found = []
        
        for pattern, description, severity in self.forbidden_patterns:
            matches = list(re.finditer(pattern, code, re.MULTILINE))
            for match in matches:
                line = code.count('\n', 0, match.start()) + 1
                issues_found.append(Issue(
                    category="security",
                    severity=severity,
                    description=description,
                    line=line,
                    code_snippet=match.group(0),
                    suggestion=None
                ))
        
        # Verificar AST para patrones más complejos
        try:
            tree = ast.parse(code)
            # Buscar imports peligrosos
            for node in ast.walk(tree):
                if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    for name in node.names:
                        if name.name in ['subprocess', 'ctypes']:
                            # No prohibido, pero advertencia
                            issues_found.append(Issue(
                                category="security",
                                severity="low",
                                description=f"Import de módulo sensible: {name.name}",
                                suggestion="Verificar uso correcto y seguro"
                            ))
        except SyntaxError:
            issues_found.append(Issue(
                category="quality",
                severity="high",
                description="Error de sintaxis en el código"
            ))
            score = 0.0
        
        self._issues.extend(issues_found)
        
        # Penalizar por issues
        critical = sum(1 for i in issues_found if i.severity == "critical")
        high = sum(1 for i in issues_found if i.severity == "high")
        
        score -= critical * 0.40
        score -= high * 0.20
        
        return max(0.0, score)
    
    def _review_compatibility(self, code: str) -> float:
        """Revisa compatibilidad con Termux/ARM64 (30% del peso)."""
        score = 1.0
        issues_found = []
        
        for pattern, description, severity in self.incompatible_patterns:
            matches = list(re.finditer(pattern, code, re.IGNORECASE | re.MULTILINE))
            for match in matches:
                line = code.count('\n', 0, match.start()) + 1
                issues_found.append(Issue(
                    category="compatibility",
                    severity=severity,
                    description=description,
                    line=line,
                    code_snippet=match.group(0)
                ))
        
        self._issues.extend(issues_found)
        
        # Penalizar
        medium = sum(1 for i in issues_found if i.severity == "medium")
        score -= medium * 0.15
        
        return max(0.0, score)
    
    def _review_quality(self, code: str) -> float:
        """Revisa calidad del código (20% del peso)."""
        score = 1.0
        issues_found = []
        
        for pattern, description, severity in self.quality_patterns:
            matches = list(re.finditer(pattern, code, re.MULTILINE))
            for match in matches:
                line = code.count('\n', 0, match.start()) + 1
                issues_found.append(Issue(
                    category="quality",
                    severity=severity,
                    description=description,
                    line=line,
                    code_snippet=match.group(0)
                ))
        
        # Verificar longitud de líneas
        lines = code.splitlines()
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                issues_found.append(Issue(
                    category="quality",
                    severity="low",
                    description="Línea demasiado larga (>120 caracteres)",
                    line=i
                ))
        
        self._issues.extend(issues_found)
        
        # Penalizar
        medium = sum(1 for i in issues_found if i.severity == "medium")
        low = sum(1 for i in issues_found if i.severity == "low")
        
        score -= medium * 0.10
        score -= low * 0.05
        
        return max(0.0, score)
    
    def _review_performance(self, code: str) -> float:
        """Revisa rendimiento (10% del peso)."""
        score = 1.0
        issues_found = []
        
        # Buscar imports globales pesados
        heavy_imports = [
            (r"import numpy", "Import global de numpy - considera lazy loading", "low"),
            (r"import pandas", "Import global de pandas - considera lazy loading", "low"),
            (r"import tensorflow", "Import global de TensorFlow - usa ONNX en su lugar", "medium"),
            (r"import torch", "Import global de PyTorch - usa ONNX en su lugar", "medium"),
        ]
        
        for pattern, description, severity in heavy_imports:
            matches = list(re.finditer(pattern, code, re.MULTILINE))
            for match in matches:
                line = code.count('\n', 0, match.start()) + 1
                issues_found.append(Issue(
                    category="performance",
                    severity=severity,
                    description=description,
                    line=line,
                    code_snippet=match.group(0)
                ))
        
        self._issues.extend(issues_found)
        
        # Penalizar
        medium = sum(1 for i in issues_found if i.severity == "medium")
        score -= medium * 0.20
        
        return max(0.0, score)
    
    def get_report(self, result: ReviewResult) -> str:
        """Genera un reporte legible en texto plano."""
        report = []
        report.append("=" * 60)
        report.append(f"📋 Claw-Litle BUDDY REVIEWER")
        report.append(f"📊 Puntuación: {result.score:.2f} / 1.00")
        report.append(f"✅ Veredicto: {result.verdict.value}")
        report.append("=" * 60)
        
        report.append("\n📈 Puntuación por categoría:")
        for category, score in result.category_scores.items():
            report.append(f"  {category:15} {score:.2f} ({self.config.category_weights[category]*100:.0f}%)")
        
        if result.issues:
            report.append(f"\n⚠️  Issues encontrados: {len(result.issues)}")
            for issue in result.issues:
                severity_marker = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🟢"
                }.get(issue.severity, "⚪")
                
                line_info = f" (línea {issue.line})" if issue.line else ""
                report.append(f"\n{severity_marker} {issue.severity.upper()} - {issue.category}")
                report.append(f"   {issue.description}")
                if issue.code_snippet:
                    report.append(f"   Código: {issue.code_snippet}")
                if issue.suggestion:
                    report.append(f"   Sugerencia: {issue.suggestion}")
        
        report.append("\n" + "=" * 60)
        return "\n".join(report)


# Función helper para uso rápido
def review_code(code: str, config: ReviewConfig = None) -> ReviewResult:
    """Wrapper para revisar código rápidamente."""
    reviewer = BuddyReviewer(config)
    return reviewer.review(code)


if __name__ == "__main__":
    # Test rápido - ejemplo de código SEGURO para demostración
    test_code = """
import json
import re

def safe_function(data):
    # Uso seguro de expresiones regulares
    pattern = r'^[a-zA-Z0-9_]+$'
    if re.match(pattern, data):
        return json.dumps({"valid": True, "data": data})
    return json.dumps({"valid": False})

# Ejemplo de uso correcto
result = safe_function("test_data_123")
print(result)
    """
    
    reviewer = BuddyReviewer()
    result = reviewer.review(test_code)
    print(reviewer.get_report(result))