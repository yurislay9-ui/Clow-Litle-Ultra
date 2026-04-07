"""
Enhanced Buddy Reviewer - Claw-Litle 1.0

Versión mejorada del Buddy Reviewer con capacidades de aprendizaje.
Analiza código generado y proporciona feedback estructurado con
evaluación en 4 categorías: Seguridad (40%), Compatibilidad (30%), 
Calidad (20%), Performance (10%).
"""

import json
import re
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path


class ReviewVerdict(Enum):
    """Veredictos posibles del Buddy Reviewer"""
    APPROVED = "APPROVED"           # ✅ Código listo para producción
    NEEDS_FIX = "NEEDS_FIX"         # ⚠️ Requiere correcciones menores
    NEEDS_REVIEW = "NEEDS_REVIEW"   # 🟡 Requiere revisión manual
    BLOCKED = "BLOCKED"             # 🚫 Problemas críticos, no aprobar


class CodeCategory(Enum):
    """Categorías de código para análisis específico"""
    GENERAL = "general"
    WEB_SCRAPER = "web_scraper"
    API_CLIENT = "api_client"
    DATA_PROCESSING = "data_processing"
    CLI_APP = "cli_app"
    FLASK_API = "flask_api"
    TELEGRAM_BOT = "telegram_bot"
    SCHEDULED_TASK = "scheduled_task"


@dataclass
class CategoryScore:
    """Puntuación por categoría"""
    category: str
    score: float  # 0.0 - 1.0
    weight: float  # Importancia de la categoría
    issues: List[str]
    suggestions: List[str]
    
    def weighted_score(self) -> float:
        """Calcula puntuación ponderada"""
        return self.score * self.weight


@dataclass
class BuddyReview:
    """Resultado completo de la revisión"""
    code: str
    verdict: ReviewVerdict
    overall_score: float  # 0.0 - 1.0
    category_scores: List[CategoryScore]
    total_issues: int
    critical_issues: int
    warnings: int
    suggestions: List[str]
    learning_applied: bool
    review_time_ms: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa a diccionario"""
        return {
            "verdict": self.verdict.value,
            "overall_score": round(self.overall_score, 3),
            "category_scores": [
                {
                    "category": cs.category,
                    "score": round(cs.score, 3),
                    "weight": cs.weight,
                    "weighted_score": round(cs.weighted_score(), 3),
                    "issues": cs.issues,
                    "suggestions": cs.suggestions
                }
                for cs in self.category_scores
            ],
            "total_issues": self.total_issues,
            "critical_issues": self.critical_issues,
            "warnings": self.warnings,
            "suggestions": self.suggestions,
            "learning_applied": self.learning_applied,
            "review_time_ms": round(self.review_time_ms, 2),
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class LearningExample:
    """Ejemplo de aprendizaje para el Buddy"""
    code_pattern: str
    issue_type: str
    description: str
    fix_example: str
    confidence: float
    times_applied: int = 0
    success_rate: float = 1.0


class EnhancedBuddyReviewer:
    """
    Buddy Reviewer mejorado con capacidades de aprendizaje.
    
    Analiza código generado y proporciona feedback estructurado:
    - Seguridad (40%): Vulnerabilidades, hardcoding, sanitización
    - Compatibilidad (30%): Termux, ARM64, librerías permitidas
    - Calidad (20%): PEP8, estructura, legibilidad
    - Performance (10%): Eficiencia, memory leaks, optimizaciones
    
    El sistema aprende de correcciones previas para mejorar futuras revisiones.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Configuración
        self.approval_threshold = self.config.get("approval_threshold", 0.85)
        self.needs_fix_threshold = self.config.get("needs_fix_threshold", 0.70)
        self.needs_review_threshold = self.config.get("needs_review_threshold", 0.50)
        
        # Pesos por categoría
        self.category_weights = {
            "seguridad": 0.40,
            "compatibilidad": 0.30,
            "calidad": 0.20,
            "performance": 0.10
        }
        
        # Base de conocimientos de aprendizaje
        self.learning_examples: List[LearningExample] = []
        self.learning_history: List[Dict] = []
        
        # Estadísticas
        self.stats = {
            "total_reviews": 0,
            "approved_count": 0,
            "needs_fix_count": 0,
            "needs_review_count": 0,
            "blocked_count": 0,
            "avg_score": 0.0,
            "learning_improvements": 0
        }
        
        # Callbacks para análisis personalizado
        self.custom_reviewer_callback: Optional[Callable] = None
        
        # Inicializar patrones de análisis
        self._initialize_patterns()
    
    def _initialize_patterns(self):
        """Inicializa patrones para análisis de código"""
        # Patrones de seguridad
        self.security_patterns = {
            "eval_exec": [r'\beval\s*\(', r'\bexec\s*\('],
            "hardcoded_secrets": [
                r'password\s*=\s*["\'][^"\']+["\']',
                r'api_key\s*=\s*["\'][^"\']+["\']',
                r'secret\s*=\s*["\'][^"\']+["\']',
            ],
            "sql_injection": [
                r'execute\s*\(\s*f["\']',
                r'execute\s*\(\s*["\'].*\.format',
            ],
            "command_injection": [
                r'\bos\.system\s*\(',
                r'\bsubprocess\.call\s*\(\s*shell\s*=\s*True',
            ],
        }
        
        # Patrones de compatibilidad Termux
        self.compatibility_patterns = {
            "gui_dependencies": [
                r'import\s+tkinter',
                r'import\s+PyQt',
                r'import\s+PyAutoGUI',
                r'from\s+tkinter',
            ],
            "windows_specific": [
                r'import\s+winreg',
                r'import\s+ctypes\.windll',
                r'os\.name\s*==\s*["\']nt["\']',
            ],
            "docker_dependencies": [
                r'import\s+docker',
                r'from\s+docker',
            ],
            "selenium_issues": [
                r'import\s+selenium',
                r'from\s+selenium',
            ],
        }
        
        # Patrones de calidad
        self.quality_patterns = {
            "bare_except": [r'except\s*:'],
            "print_statements": [r'\bprint\s*\('],
            "magic_numbers": [r'[^0-9a-zA-Z_]\d{2,}[^0-9a-zA-Z_]'],
            "long_lines": [r'^.{100,}$'],
            "missing_docstring": [r'def\s+\w+\s*\([^)]*\):\s*(?!["\'])'],
        }
        
        # Patrones de performance
        self.performance_patterns = {
            "inefficient_loops": [r'for\s+\w+\s+in\s+range\s*\(\s*len\s*\('],
            "string_concatenation": [r'\+\s*["\'][^"\']*["\']'],
            "unnecessary_list": [r'list\s*\(\s*\['],
            "global_in_loop": [r'global\s+\w+'],
        }
    
    def review(
        self,
        code: str,
        category: CodeCategory = CodeCategory.GENERAL,
        context: Optional[Dict] = None
    ) -> BuddyReview:
        """
        Revisa código generado y proporciona feedback estructurado.
        
        Args:
            code: Código a revisar
            category: Categoría del código (para análisis específico)
            context: Contexto adicional (requisitos, restricciones)
        
        Returns:
            BuddyReview con veredicto y feedback detallado
        """
        start_time = datetime.now()
        
        # 1. Análisis por categorías
        category_scores = []
        
        # Seguridad (40%)
        security_score = self._analyze_security(code, category)
        category_scores.append(security_score)
        
        # Compatibilidad (30%)
        compatibility_score = self._analyze_compatibility(code, category)
        category_scores.append(compatibility_score)
        
        # Calidad (20%)
        quality_score = self._analyze_quality(code, category)
        category_scores.append(quality_score)
        
        # Performance (10%)
        performance_score = self._analyze_performance(code, category)
        category_scores.append(performance_score)
        
        # 2. Aplicar aprendizaje (si hay ejemplos relevantes)
        learning_applied = False
        for example in self.learning_examples:
            if re.search(example.code_pattern, code, re.IGNORECASE):
                # Aplicar corrección aprendida
                learning_applied = True
                self.stats["learning_improvements"] += 1
                example.times_applied += 1
        
        # 3. Calcular puntuación overall
        overall_score = sum(cs.weighted_score() for cs in category_scores)
        
        # 4. Determinar veredicto
        verdict = self._determine_verdict(overall_score, category_scores)
        
        # 5. Recopilar todos los issues y sugerencias
        all_issues = []
        all_suggestions = []
        critical_count = 0
        warning_count = 0
        
        for cs in category_scores:
            all_issues.extend(cs.issues)
            all_suggestions.extend(cs.suggestions)
            if cs.score < 0.5:
                critical_count += len([i for i in cs.issues if "crítico" in i.lower()])
            warning_count += len([i for i in cs.issues if "advertencia" in i.lower()])
        
        review_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        # 6. Crear review
        review = BuddyReview(
            code=code,
            verdict=verdict,
            overall_score=overall_score,
            category_scores=category_scores,
            total_issues=len(all_issues),
            critical_issues=critical_count,
            warnings=warning_count,
            suggestions=all_suggestions,
            learning_applied=learning_applied,
            review_time_ms=review_time_ms
        )
        
        # 7. Actualizar estadísticas
        self._update_stats(review)
        
        # 8. Guardar en historial para aprendizaje
        self.learning_history.append({
            "code_hash": hash(code) % (10**8),
            "category": category.value,
            "verdict": verdict.value,
            "score": overall_score,
            "issues": all_issues,
            "timestamp": datetime.now().isoformat()
        })
        
        # Mantener historial limitado
        if len(self.learning_history) > 1000:
            self.learning_history = self.learning_history[-500:]
        
        return review
    
    def _analyze_security(self, code: str, category: CodeCategory) -> CategoryScore:
        """Analiza seguridad del código"""
        issues = []
        suggestions = []
        score = 1.0
        
        # Verificar patrones de seguridad
        for pattern_name, patterns in self.security_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, code, re.IGNORECASE | re.MULTILINE)
                if matches:
                    severity = "crítico" if pattern_name in ["eval_exec", "sql_injection", "command_injection"] else "advertencia"
                    issues.append(f"[{severity.upper()}] {pattern_name}: {len(matches)} ocurrencia(s)")
                    score -= 0.15 if severity == "crítico" else 0.05
        
        # Verificaciones específicas por categoría
        if category == CodeCategory.WEB_SCRAPER:
            if "time.sleep" not in code and "asyncio.sleep" not in code:
                issues.append("[ADVERTENCIA] Scraper sin delays - riesgo de rate limiting")
                suggestions.append("Agregar delays entre requests para evitar bloqueo")
                score -= 0.05
        
        elif category == CodeCategory.API_CLIENT:
            if "timeout" not in code.lower():
                issues.append("[ADVERTENCIA] Cliente API sin timeout configurado")
                suggestions.append("Agregar timeout a las peticiones HTTP")
                score -= 0.05
        
        elif category == CodeCategory.FLASK_API:
            if "cors" not in code.lower():
                issues.append("[ADVERTENCIA] API Flask sin CORS configurado")
                suggestions.append("Configurar Flask-CORS para permitir cross-origin")
                score -= 0.03
        
        # Aplicar aprendizaje de seguridad
        for example in self.learning_examples:
            if example.issue_type == "security" and re.search(example.code_pattern, code):
                suggestions.append(f"💡 Aprendizaje: {example.description}")
                suggestions.append(f"   Ejemplo de fix: {example.fix_example}")
        
        score = max(0.0, min(1.0, score))
        
        return CategoryScore(
            category="seguridad",
            score=score,
            weight=self.category_weights["seguridad"],
            issues=issues,
            suggestions=suggestions
        )
    
    def _analyze_compatibility(self, code: str, category: CodeCategory) -> CategoryScore:
        """Analiza compatibilidad con Termux/ARM64"""
        issues = []
        suggestions = []
        score = 1.0
        
        # Verificar patrones de incompatibilidad
        for pattern_name, patterns in self.compatibility_patterns.items():
            for pattern in patterns:
                if re.search(pattern, code, re.IGNORECASE):
                    issues.append(f"[CRÍTICO] {pattern_name}: No compatible con Termux")
                    score -= 0.2
        
        # Verificar imports permitidos (lista blanca)
        allowed_imports = [
            'requests', 'beautifulsoup4', 'bs4', 'lxml',
            'sqlite3', 'json', 're', 'os', 'sys', 'time',
            'datetime', 'pathlib', 'hashlib', 'base64',
            'urllib', 'http', 'email', 'html', 'xml',
            'asyncio', ' threading', 'multiprocessing',
            'subprocess', 'shutil', 'tempfile', 'gzip',
            'zlib', 'csv', 'configparser', 'argparse',
            'logging', 'getpass', 'platform', 'socket',
            'ssl', 'random', 'secrets', 'string', 'textwrap',
            'unicodedata', 'collections', 'itertools', 'functools',
            'operator', 'copy', 'pprint', 'reprlib', 'enum',
            'dataclasses', 'typing', 'contextlib', 'io',
            'rich', 'click', 'prompt_toolkit',
            'python_telegram_bot', 'telegram',
        ]
        
        # Verificar imports sospechosos
        import_pattern = r'(?:^|\n)\s*import\s+(\w+)|(?:^|\n)\s*from\s+(\w+)'
        for match in re.finditer(import_pattern, code):
            module = match.group(1) or match.group(2)
            if module and module not in allowed_imports:
                # Verificar si está en la lista negra
                blacklisted = ['docker', 'kubernetes', 'proot', 'tkinter', 'PyQt', 'PyAutoGUI', 'selenium']
                if module in blacklisted:
                    issues.append(f"[CRÍTICO] Import prohibido: {module}")
                    suggestions.append(f"Reemplazar {module} con alternativa compatible con Termux")
                    score -= 0.15
        
        # Verificar rutas compatibles
        if "C:\\" in code or "C:/" in code:
            issues.append("[ADVERTENCIA] Rutas Windows hardcodeadas")
            suggestions.append("Usar rutas relativas o variables de entorno")
            score -= 0.05
        
        if "~/Documents" in code or "~/Desktop" in code:
            issues.append("[ADVERTENCIA] Rutas de escritorio no disponibles en Termux")
            suggestions.append("Usar $HOME o /sdcard/ para almacenamiento")
            score -= 0.05
        
        score = max(0.0, min(1.0, score))
        
        return CategoryScore(
            category="compatibilidad",
            score=score,
            weight=self.category_weights["compatibilidad"],
            issues=issues,
            suggestions=suggestions
        )
    
    def _analyze_quality(self, code: str, category: CodeCategory) -> CategoryScore:
        """Analiza calidad del código"""
        issues = []
        suggestions = []
        score = 1.0
        
        # Verificar patrones de calidad
        for pattern_name, patterns in self.quality_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, code, re.MULTILINE)
                if matches:
                    if pattern_name == "bare_except":
                        issues.append(f"[ADVERTENCIA] bare except: {len(matches)} ocurrencia(s)")
                        suggestions.append("Usar 'except Exception:' o excepciones específicas")
                        score -= 0.05 * len(matches)
                    elif pattern_name == "print_statements":
                        # Solo advertir si hay muchos prints
                        if len(matches) > 5:
                            issues.append(f"[ADVERTENCIA] {len(matches)} print statements - considerar logging")
                            suggestions.append("Usar módulo logging en lugar de print")
                            score -= 0.03
        
        # Verificar estructura básica
        lines = code.split('\n')
        
        # Funciones muy largas (>50 líneas)
        func_lines = 0
        for line in lines:
            if line.strip().startswith('def '):
                if func_lines > 50:
                    issues.append(f"[ADVERTENCIA] Función muy larga ({func_lines} líneas)")
                    suggestions.append("Dividir funciones largas en funciones más pequeñas")
                    score -= 0.03
                func_lines = 0
            else:
                func_lines += 1
        
        # Verificar docstrings
        if category in [CodeCategory.FLASK_API, CodeCategory.TELEGRAM_BOT]:
            if '"""' not in code and "'''" not in code:
                issues.append("[ADVERTENCIA] Código sin docstrings")
                suggestions.append("Agregar docstrings a funciones y clases")
                score -= 0.05
        
        score = max(0.0, min(1.0, score))
        
        return CategoryScore(
            category="calidad",
            score=score,
            weight=self.category_weights["calidad"],
            issues=issues,
            suggestions=suggestions
        )
    
    def _analyze_performance(self, code: str, category: CodeCategory) -> CategoryScore:
        """Analiza performance del código"""
        issues = []
        suggestions = []
        score = 1.0
        
        # Verificar patrones de performance
        for pattern_name, patterns in self.performance_patterns.items():
            for pattern in patterns:
                if re.search(pattern, code, re.IGNORECASE):
                    issues.append(f"[ADVERTENCIA] {pattern_name}: posible ineficiencia")
                    score -= 0.03
        
        # Verificaciones específicas
        if category == CodeCategory.WEB_SCRAPER:
            if "session" not in code.lower() and "Session" not in code:
                issues.append("[ADVERTENCIA] Scraper sin session reutilizada")
                suggestions.append("Usar requests.Session() para reutilizar conexiones")
                score -= 0.05
        
        if category == CodeCategory.DATA_PROCESSING:
            if "pandas" in code.lower() and "chunksize" not in code.lower():
                issues.append("[ADVERTENCIA] Procesamiento de datos sin chunks")
                suggestions.append("Usar chunksize para procesar datos grandes en memoria limitada")
                score -= 0.05
        
        # Verificar memory leaks potenciales
        if "while True:" in code and "break" not in code:
            issues.append("[ADVERTENCIA] Bucle infinito sin break aparente")
            suggestions.append("Asegurar condición de salida en bucles infinitos")
            score -= 0.05
        
        score = max(0.0, min(1.0, score))
        
        return CategoryScore(
            category="performance",
            score=score,
            weight=self.category_weights["performance"],
            issues=issues,
            suggestions=suggestions
        )
    
    def _determine_verdict(self, overall_score: float, category_scores: List[CategoryScore]) -> ReviewVerdict:
        """Determina veredicto basado en puntuaciones"""
        # Verificar si hay issues críticos en seguridad
        security_score = next((cs.score for cs in category_scores if cs.category == "seguridad"), 1.0)
        if security_score < 0.5:
            return ReviewVerdict.BLOCKED
        
        # Verificar compatibilidad crítica
        compatibility_score = next((cs.score for cs in category_scores if cs.category == "compatibilidad"), 1.0)
        if compatibility_score < 0.5:
            return ReviewVerdict.BLOCKED
        
        # Determinar por puntuación overall
        if overall_score >= self.approval_threshold:
            return ReviewVerdict.APPROVED
        elif overall_score >= self.needs_fix_threshold:
            return ReviewVerdict.NEEDS_FIX
        elif overall_score >= self.needs_review_threshold:
            return ReviewVerdict.NEEDS_REVIEW
        else:
            return ReviewVerdict.BLOCKED
    
    def _update_stats(self, review: BuddyReview):
        """Actualiza estadísticas"""
        self.stats["total_reviews"] += 1
        
        if review.verdict == ReviewVerdict.APPROVED:
            self.stats["approved_count"] += 1
        elif review.verdict == ReviewVerdict.NEEDS_FIX:
            self.stats["needs_fix_count"] += 1
        elif review.verdict == ReviewVerdict.NEEDS_REVIEW:
            self.stats["needs_review_count"] += 1
        else:
            self.stats["blocked_count"] += 1
        
        # Actualizar promedio móvil
        n = self.stats["total_reviews"]
        old_avg = self.stats["avg_score"]
        self.stats["avg_score"] = ((old_avg * (n - 1)) + review.overall_score) / n
    
    def add_learning_example(
        self,
        code_pattern: str,
        issue_type: str,
        description: str,
        fix_example: str,
        confidence: float = 0.8
    ):
        """
        Agrega un ejemplo de aprendizaje.
        
        Args:
            code_pattern: Patrón regex del código problemático
            issue_type: Tipo de issue (security, compatibility, quality, performance)
            description: Descripción del problema
            fix_example: Ejemplo de código corregido
            confidence: Confianza en el ejemplo (0-1)
        """
        example = LearningExample(
            code_pattern=code_pattern,
            issue_type=issue_type,
            description=description,
            fix_example=fix_example,
            confidence=confidence
        )
        self.learning_examples.append(example)
        
        # Mantener lista limitada
        if len(self.learning_examples) > 100:
            # Eliminar ejemplos menos usados
            self.learning_examples.sort(key=lambda x: x.times_applied, reverse=True)
            self.learning_examples = self.learning_examples[:50]
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del Buddy Reviewer"""
        return {
            **self.stats,
            "learning_examples_count": len(self.learning_examples),
            "learning_history_count": len(self.learning_history),
            "category_weights": self.category_weights,
            "thresholds": {
                "approval": self.approval_threshold,
                "needs_fix": self.needs_fix_threshold,
                "needs_review": self.needs_review_threshold
            }
        }
    
    def set_custom_reviewer(self, callback: Callable[[str, CodeCategory, Optional[Dict]], List[CategoryScore]]):
        """Establece un reviewer personalizado"""
        self.custom_reviewer_callback = callback


# Instancia global
_reviewer: Optional[EnhancedBuddyReviewer] = None


def get_enhanced_buddy_reviewer(config: Optional[Dict] = None) -> EnhancedBuddyReviewer:
    """Obtiene la instancia global del Enhanced Buddy Reviewer"""
    global _reviewer
    if _reviewer is None:
        _reviewer = EnhancedBuddyReviewer(config)
    return _reviewer


def review_code(
    code: str,
    category: CodeCategory = CodeCategory.GENERAL,
    context: Optional[Dict] = None
) -> BuddyReview:
    """Función helper para revisar código"""
    return get_enhanced_buddy_reviewer().review(code, category, context)


if __name__ == "__main__":
    # Ejemplo de uso
    print("=== Claw-Litle 1.0 - Enhanced Buddy Reviewer ===\n")
    
    reviewer = get_enhanced_buddy_reviewer()
    
    # Agregar ejemplos de aprendizaje
    reviewer.add_learning_example(
        code_pattern=r'os\.system\s*\(',
        issue_type="security",
        description="Usar os.system() es peligroso con input de usuario",
        fix_example="subprocess.run(['comando', 'arg1'], shell=False, check=True)",
        confidence=0.95
    )
    
    # Código de ejemplo
    test_code = '''
import os
import requests

def scrape_website(url):
    # Hacer request
    response = requests.get(url)
    return response.text

def process_data(data):
    result = []
    for i in range(len(data)):
        result.append(data[i] * 2)
    return result

def main():
    url = "http://example.com"
    content = scrape_website(url)
    print(content)

if __name__ == "__main__":
    main()
'''
    
    review = reviewer.review(test_code, CodeCategory.WEB_SCRAPER)
    
    print(f"Veredicto: {review.verdict.value}")
    print(f"Puntuación Overall: {review.overall_score:.1%}")
    print(f"Total Issues: {review.total_issues}")
    print(f"Críticos: {review.critical_issues}")
    print(f"Advertencias: {review.warnings}")
    print(f"Aprendizaje aplicado: {review.learning_applied}")
    print(f"Tiempo de revisión: {review.review_time_ms:.2f}ms")
    
    print("\n=== Puntuaciones por Categoría ===")
    for cs in review.category_scores:
        print(f"{cs.category.capitalize()}: {cs.score:.1%} (peso: {cs.weight:.0%})")
        if cs.issues:
            print(f"  Issues: {len(cs.issues)}")
        if cs.suggestions:
            print(f"  Sugerencias: {len(cs.suggestions)}")
    
    print("\n=== Estadísticas ===")
    stats = reviewer.get_stats()
    print(f"Total reviews: {stats['total_reviews']}")
    print(f"Aprobados: {stats['approved_count']}")
    print(f"Promedio score: {stats['avg_score']:.1%}")
    print(f"Ejemplos de aprendizaje: {stats['learning_examples_count']}")