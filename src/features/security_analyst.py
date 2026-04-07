"""
Security Analyst - Claw-Litle 1.0

Integrated security analysis system that scans generated code
for vulnerabilities, bad practices, and security risks.
"""

import re
import ast
import json
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path


class SecuritySeverity(Enum):
    """Vulnerability severity levels"""
    CRITICAL = "critical"    # Immediate code execution, SQL injection
    HIGH = "high"           # Sensitive data exposure, weak auth
    MEDIUM = "medium"       # Bad practices, hardcoded configs
    LOW = "low"             # Style issues, minor warnings
    INFO = "info"           # Improvement suggestions


class VulnerabilityType(Enum):
    """Detectable vulnerability types"""
    CODE_INJECTION = "code_injection"           # eval(), exec()
    SQL_INJECTION = "sql_injection"             # String formatting in queries
    HARDCODED_SECRETS = "hardcoded_secrets"     # Passwords, API keys in code
    INSECURE_RANDOM = "insecure_random"         # random instead of secrets
    PATH_TRAVERSAL = "path_traversal"           # ../ in paths
    UNSAFE_DESERIALIZATION = "unsafe_deserialization"  # pickle with user input
    XSS_VULNERABILITY = "xss_vulnerability"     # Unescaped HTML
    COMMAND_INJECTION = "command_injection"     # os.system() with user input
    INSECURE_PROTOCOL = "insecure_protocol"     # HTTP instead of HTTPS
    MISSING_AUTH = "missing_auth"               # Endpoints without authentication
    WEAK_CRYPTO = "weak_crypto"                 # MD5, SHA1 for security
    DEBUG_MODE = "debug_mode"                   # Debug=True in production
    VERBOSE_ERRORS = "verbose_errors"           # Exposed stack traces
    UNVALIDATED_INPUT = "unvalidated_input"     # Unsanitized input
    INSECURE_TEMP_FILES = "insecure_temp_files" # Temp files with 777 permissions


@dataclass
class SecurityFinding:
    """Represents a security finding"""
    vulnerability_type: VulnerabilityType
    severity: SecuritySeverity
    line_number: int
    file_name: str
    description: str
    code_snippet: str
    cwe_id: Optional[str] = None  # Common Weakness Enumeration
    owasp_category: Optional[str] = None  # OWASP Top 10
    recommendation: str = ""
    confidence: float = 0.8  # 0-1, confianza en el hallazgo
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "vulnerability_type": self.vulnerability_type.value,
            "severity": self.severity.value,
            "line_number": self.line_number,
            "file_name": self.file_name,
            "description": self.description,
            "code_snippet": self.code_snippet[:200] + ("..." if len(self.code_snippet) > 200 else ""),
            "cwe_id": self.cwe_id,
            "owasp_category": self.owasp_category,
            "recommendation": self.recommendation,
            "confidence": self.confidence
        }


@dataclass
class SecurityReport:
    """Complete security analysis report"""
    code_analyzed: str
    total_findings: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    info_count: int
    findings: List[SecurityFinding]
    security_score: float  # 0-100, donde 100 = seguro
    risk_level: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    analysis_time_ms: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "total_findings": self.total_findings,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "info_count": self.info_count,
            "security_score": self.security_score,
            "risk_level": self.risk_level,
            "findings": [f.to_dict() for f in self.findings],
            "analysis_time_ms": self.analysis_time_ms,
            "timestamp": self.timestamp.isoformat()
        }


class SecurityAnalyst:
    """
    Analista de seguridad integrado para Claw-Litle.
    
    Escanea código generado en busca de vulnerabilidades usando:
    1. Análisis estático (AST parsing)
    2. Pattern matching (regex para patrones conocidos)
    3. Heurísticas (detección de malas prácticas)
    4. Base de conocimientos (CWE, OWASP Top 10)
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Configuración
        self.min_confidence_threshold = self.config.get("min_confidence_threshold", 0.6)
        self.max_depth_analysis = self.config.get("max_depth_analysis", 3)
        
        # Estadísticas
        self.stats = {
            "total_scans": 0,
            "total_vulnerabilities": 0,
            "vulnerabilities_by_type": {},
            "avg_security_score": 0.0
        }
        
        # Patrones de vulnerabilidades (regex)
        self._initialize_patterns()
        
        # Callbacks para análisis personalizado
        self.custom_analyzer_callback: Optional[Callable] = None
    
    def _initialize_patterns(self):
        """Inicializa patrones regex para detección de vulnerabilidades"""
        self.patterns = {
            VulnerabilityType.CODE_INJECTION: [
                r'\beval\s*\(',
                r'\bexec\s*\(',
                r'\bcompile\s*\(',
                r'\b__import__\s*\(',
            ],
            VulnerabilityType.SQL_INJECTION: [
                r'execute\s*\(\s*["\'].*%s',
                r'execute\s*\(\s*f["\']',
                r'execute\s*\(\s*["\'].*\+',
                r'cursor\.execute\s*\(\s*["\'].*\.format',
            ],
            VulnerabilityType.HARDCODED_SECRETS: [
                r'password\s*=\s*["\'][^"\']+["\']',
                r'api_key\s*=\s*["\'][^"\']+["\']',
                r'secret\s*=\s*["\'][^"\']+["\']',
                r'token\s*=\s*["\'][^"\']+["\']',
                r'AWS_SECRET_ACCESS_KEY\s*=',
            ],
            VulnerabilityType.INSECURE_RANDOM: [
                r'\brandom\.(choice|randint|random|shuffle)\b',
            ],
            VulnerabilityType.PATH_TRAVERSAL: [
                r'\.\./',
                r'\.\.\\',
                r'os\.path\.join\s*\([^)]*\.\.',
            ],
            VulnerabilityType.UNSAFE_DESERIALIZATION: [
                r'\bpickle\.load',
                r'\bpickle\.loads',
                r'\byaml\.load\s*\(',  # sin Loader=SafeLoader
            ],
            VulnerabilityType.XSS_VULNERABILITY: [
                r'innerHTML\s*=',
                r'document\.write\s*\(',
                r'\.html\s*\(\s*[^)]*request',
            ],
            VulnerabilityType.COMMAND_INJECTION: [
                r'\bos\.system\s*\(',
                r'\bsubprocess\.call\s*\(',
                r'\bsubprocess\.run\s*\(',
                r'\bos\.popen\s*\(',
            ],
            VulnerabilityType.INSECURE_PROTOCOL: [
                r'http://(?!localhost|127\.0\.0\.1)',
                r'requests\.(get|post)\s*\(\s*["\']http://',
            ],
            VulnerabilityType.WEAK_CRYPTO: [
                r'\bhashlib\.md5\b',
                r'\bhashlib\.sha1\b',
                r'\bMD5\.new\(\)',
                r'\bSHA\.new\(\)',
            ],
            VulnerabilityType.DEBUG_MODE: [
                r'debug\s*=\s*True',
                r'DEBUG\s*=\s*True',
                r'\bflask\.run\s*\(\s*debug\s*=\s*True',
            ],
            VulnerabilityType.VERBOSE_ERRORS: [
                r'app\.debug\s*=\s*True',
                r'EXCEPTION_PROPAGATION\s*=\s*True',
            ],
        }
        
        # Mapeo CWE y OWASP
        self.cwe_mapping = {
            VulnerabilityType.CODE_INJECTION: ("CWE-94", "A03:2021-Injection"),
            VulnerabilityType.SQL_INJECTION: ("CWE-89", "A03:2021-Injection"),
            VulnerabilityType.HARDCODED_SECRETS: ("CWE-798", "A07:2021-Identification and Authentication Failures"),
            VulnerabilityType.INSECURE_RANDOM: ("CWE-330", "A02:2021-Cryptographic Failures"),
            VulnerabilityType.PATH_TRAVERSAL: ("CWE-22", "A01:2021-Broken Access Control"),
            VulnerabilityType.UNSAFE_DESERIALIZATION: ("CWE-502", "A08:2021-Software and Data Integrity Failures"),
            VulnerabilityType.XSS_VULNERABILITY: ("CWE-79", "A03:2021-Injection"),
            VulnerabilityType.COMMAND_INJECTION: ("CWE-78", "A03:2021-Injection"),
            VulnerabilityType.INSECURE_PROTOCOL: ("CWE-319", "A02:2021-Cryptographic Failures"),
            VulnerabilityType.WEAK_CRYPTO: ("CWE-328", "A02:2021-Cryptographic Failures"),
            VulnerabilityType.DEBUG_MODE: ("CWE-489", "A05:2021-Security Misconfiguration"),
            VulnerabilityType.VERBOSE_ERRORS: ("CWE-209", "A05:2021-Security Misconfiguration"),
        }
        
        # Recomendaciones por tipo
        self.recommendations = {
            VulnerabilityType.CODE_INJECTION: "Evitar eval()/exec(). Usar ast.literal_eval() para datos seguros o refactorizar la lógica.",
            VulnerabilityType.SQL_INJECTION: "Usar consultas parametrizadas con placeholders (?) en lugar de string formatting.",
            VulnerabilityType.HARDCODED_SECRETS: "Usar variables de entorno o un gestor de secretos (ej: python-dotenv, AWS Secrets Manager).",
            VulnerabilityType.INSECURE_RANDOM: "Usar secrets module para generación de tokens, contraseñas o valores criptográficos.",
            VulnerabilityType.PATH_TRAVERSAL: "Validar y sanitizar rutas. Usar os.path.abspath() y verificar que esté dentro del directorio esperado.",
            VulnerabilityType.UNSAFE_DESERIALIZATION: "Usar formatos seguros como JSON. Si es necesario pickle, validar fuente y usar restricciones.",
            VulnerabilityType.XSS_VULNERABILITY: "Escapar contenido HTML. Usar librerías como bleach o Jinja2 con autoescape activado.",
            VulnerabilityType.COMMAND_INJECTION: "Evitar os.system(). Usar subprocess con listas y shell=False. Validar input estrictamente.",
            VulnerabilityType.INSECURE_PROTOCOL: "Usar HTTPS para todas las comunicaciones externas. Configurar HSTS headers.",
            VulnerabilityType.WEAK_CRYPTO: "Usar algoritmos seguros como SHA-256, SHA-3, o bcrypt para hashing de contraseñas.",
            VulnerabilityType.DEBUG_MODE: "Desactivar debug en producción. Usar variables de entorno para controlar el modo.",
            VulnerabilityType.VERBOSE_ERRORS: "Mostrar mensajes genéricos al usuario. Loggear detalles técnicos en el servidor.",
        }
    
    def analyze(self, code: str, file_name: str = "generated_code.py") -> SecurityReport:
        """
        Analiza código en busca de vulnerabilidades.
        
        Args:
            code: Código fuente a analizar
            file_name: Nombre del archivo (para reporting)
        
        Returns:
            SecurityReport con todos los hallazgos
        """
        start_time = datetime.now()
        findings: List[SecurityFinding] = []
        
        # 1. Análisis por patrones regex
        findings.extend(self._pattern_analysis(code, file_name))
        
        # 2. Análisis AST (Abstract Syntax Tree)
        findings.extend(self._ast_analysis(code, file_name))
        
        # 3. Análisis heurístico
        findings.extend(self._heuristic_analysis(code, file_name))
        
        # 4. Análisis personalizado (si hay callback)
        if self.custom_analyzer_callback:
            try:
                custom_findings = self.custom_analyzer_callback(code, file_name)
                if isinstance(custom_findings, list):
                    findings.extend(custom_findings)
            except Exception as e:
                pass
        
        # Filtrar por confianza mínima
        findings = [f for f in findings if f.confidence >= self.min_confidence_threshold]
        
        # Eliminar duplicados (mismo tipo, línea y archivo)
        findings = self._deduplicate_findings(findings)
        
        # Calcular métricas
        total_findings = len(findings)
        critical_count = sum(1 for f in findings if f.severity == SecuritySeverity.CRITICAL)
        high_count = sum(1 for f in findings if f.severity == SecuritySeverity.HIGH)
        medium_count = sum(1 for f in findings if f.severity == SecuritySeverity.MEDIUM)
        low_count = sum(1 for f in findings if f.severity == SecuritySeverity.LOW)
        info_count = sum(1 for f in findings if f.severity == SecuritySeverity.INFO)
        
        # Calcular security score (0-100)
        security_score = self._calculate_security_score(findings)
        
        # Determinar nivel de riesgo
        risk_level = self._determine_risk_level(security_score, critical_count)
        
        analysis_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        # Actualizar estadísticas
        self.stats["total_scans"] += 1
        self.stats["total_vulnerabilities"] += total_findings
        for finding in findings:
            vtype = finding.vulnerability_type.value
            self.stats["vulnerabilities_by_type"][vtype] = (
                self.stats["vulnerabilities_by_type"].get(vtype, 0) + 1
            )
        
        # Actualizar promedio móvil
        n = self.stats["total_scans"]
        old_avg = self.stats["avg_security_score"]
        self.stats["avg_security_score"] = ((old_avg * (n - 1)) + security_score) / n
        
        return SecurityReport(
            code_analyzed=code,
            total_findings=total_findings,
            critical_count=critical_count,
            high_count=high_count,
            medium_count=medium_count,
            low_count=low_count,
            info_count=info_count,
            findings=findings,
            security_score=round(security_score, 1),
            risk_level=risk_level,
            analysis_time_ms=round(analysis_time_ms, 2)
        )
    
    def _pattern_analysis(self, code: str, file_name: str) -> List[SecurityFinding]:
        """Análisis basado en patrones regex"""
        findings = []
        lines = code.split('\n')
        
        for vuln_type, patterns in self.patterns.items():
            for pattern in patterns:
                for line_num, line in enumerate(lines, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        cwe_id, owasp = self.cwe_mapping.get(vuln_type, (None, None))
                        
                        # Determinar severidad basada en contexto
                        severity = self._determine_severity_from_context(vuln_type, line)
                        
                        finding = SecurityFinding(
                            vulnerability_type=vuln_type,
                            severity=severity,
                            line_number=line_num,
                            file_name=file_name,
                            description=f"Posible {vuln_type.value.replace('_', ' ')} detectado",
                            code_snippet=line.strip(),
                            cwe_id=cwe_id,
                            owasp_category=owasp,
                            recommendation=self.recommendations.get(vuln_type, "Revisar manualmente"),
                            confidence=0.75  # Confianza base para pattern matching
                        )
                        findings.append(finding)
        
        return findings
    
    def _ast_analysis(self, code: str, file_name: str) -> List[SecurityFinding]:
        """Análisis usando Abstract Syntax Tree"""
        findings = []
        
        try:
            tree = ast.parse(code)
        except SyntaxError:
            # Si no se puede parsear, retornar hallazgo de sintaxis inválida
            findings.append(SecurityFinding(
                vulnerability_type=VulnerabilityType.UNVALIDATED_INPUT,
                severity=SecuritySeverity.MEDIUM,
                line_number=0,
                file_name=file_name,
                description="Código con sintaxis inválida - no se pudo analizar AST",
                code_snippet=code[:100],
                recommendation="Corregir errores de sintaxis antes de ejecutar",
                confidence=1.0
            ))
            return findings
        
        # Analizar nodos AST
        for node in ast.walk(tree):
            # Detectar llamadas a funciones peligrosas
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    
                    # eval(), exec()
                    if func_name in ('eval', 'exec', 'compile'):
                        findings.append(SecurityFinding(
                            vulnerability_type=VulnerabilityType.CODE_INJECTION,
                            severity=SecuritySeverity.CRITICAL,
                            line_number=node.lineno,
                            file_name=file_name,
                            description=f"Llamada peligrosa a {func_name}()",
                            code_snippet=ast.get_source_segment(code, node) or f"{func_name}(...)",
                            cwe_id="CWE-94",
                            owasp_category="A03:2021-Injection",
                            recommendation=f"Evitar {func_name}(). Usar alternativas seguras.",
                            confidence=0.95
                        ))
                    
                    # os.system(), os.popen()
                    elif func_name in ('system', 'popen') and self._is_os_module(node):
                        findings.append(SecurityFinding(
                            vulnerability_type=VulnerabilityType.COMMAND_INJECTION,
                            severity=SecuritySeverity.HIGH,
                            line_number=node.lineno,
                            file_name=file_name,
                            description=f"Llamada peligrosa a os.{func_name}()",
                            code_snippet=ast.get_source_segment(code, node) or f"os.{func_name}(...)",
                            cwe_id="CWE-78",
                            owasp_category="A03:2021-Injection",
                            recommendation="Usar subprocess con shell=False y listas de argumentos",
                            confidence=0.9
                        ))
            
            # Detectar asignaciones sospechosas
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_name = target.id
                        # Variables que suenan a secretos
                        if any(keyword in var_name.lower() for keyword in ['password', 'secret', 'api_key', 'token']):
                            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                                findings.append(SecurityFinding(
                                    vulnerability_type=VulnerabilityType.HARDCODED_SECRETS,
                                    severity=SecuritySeverity.HIGH,
                                    line_number=node.lineno,
                                    file_name=file_name,
                                    description=f"Posible secreto hardcodeado en variable '{var_name}'",
                                    code_snippet=ast.get_source_segment(code, node) or f"{var_name} = ...",
                                    cwe_id="CWE-798",
                                    owasp_category="A07:2021-Identification and Authentication Failures",
                                    recommendation="Usar variables de entorno o gestor de secretos",
                                    confidence=0.85
                                ))
        
        return findings
    
    def _heuristic_analysis(self, code: str, file_name: str) -> List[SecurityFinding]:
        """Análisis heurístico basado en patrones de comportamiento"""
        findings = []
        
        # Verificar si hay imports peligrosos
        dangerous_imports = {
            'pickle': VulnerabilityType.UNSAFE_DESERIALIZATION,
            'marshal': VulnerabilityType.UNSAFE_DESERIALIZATION,
            'shelve': VulnerabilityType.UNSAFE_DESERIALIZATION,
        }
        
        for module, vuln_type in dangerous_imports.items():
            if re.search(rf'^\s*import\s+{module}', code, re.MULTILINE):
                findings.append(SecurityFinding(
                    vulnerability_type=vuln_type,
                    severity=SecuritySeverity.MEDIUM,
                    line_number=0,
                    file_name=file_name,
                    description=f"Importación de módulo peligroso: {module}",
                    code_snippet=f"import {module}",
                    cwe_id=self.cwe_mapping[vuln_type][0],
                    owasp_category=self.cwe_mapping[vuln_type][1],
                    recommendation="Considerar alternativas más seguras como JSON",
                    confidence=0.7
                ))
        
        # Verificar si hay try/except muy amplios que oculten errores
        if re.search(r'try:\s*\n\s*.*\nexcept:\s*\n\s*pass', code):
            findings.append(SecurityFinding(
                vulnerability_type=VulnerabilityType.VERBOSE_ERRORS,
                severity=SecuritySeverity.LOW,
                line_number=0,
                file_name=file_name,
                description="Bloque try/except que silencia todos los errores",
                code_snippet="except: pass",
                cwe_id="CWE-754",
                owasp_category="A05:2021-Security Misconfiguration",
                recommendation="Capturar excepciones específicas y loggear apropiadamente",
                confidence=0.65
            ))
        
        # Verificar si hay funciones sin validación de input
        function_pattern = r'def\s+(\w+)\s*\(([^)]*)\):'
        for match in re.finditer(function_pattern, code):
            func_name = match.group(1)
            params = match.group(2)
            
            # Si la función recibe parámetros pero no tiene validación aparente
            if params and 'self' not in params:
                # Buscar la función y verificar si hay validación
                func_start = match.start()
                func_body = code[func_start:func_start + 500]  # Primeros 500 chars del cuerpo
                
                has_validation = any(keyword in func_body for keyword in [
                    'if ', 'assert', 'raise', 'validate', 'sanitize', 'clean'
                ])
                
                if not has_validation:
                    findings.append(SecurityFinding(
                        vulnerability_type=VulnerabilityType.UNVALIDATED_INPUT,
                        severity=SecuritySeverity.MEDIUM,
                        line_number=code[:func_start].count('\n') + 1,
                        file_name=file_name,
                        description=f"Función '{func_name}' sin validación aparente de parámetros",
                        code_snippet=f"def {func_name}({params}):",
                        recommendation="Agregar validación de parámetros al inicio de la función",
                        confidence=0.5  # Baja confianza, es heurístico
                    ))
        
        return findings
    
    def _determine_severity_from_context(self, vuln_type: VulnerabilityType, line: str) -> SecuritySeverity:
        """Determina severidad basada en contexto de la línea"""
        # Por defecto, severidad media para la mayoría
        default_severity = {
            VulnerabilityType.CODE_INJECTION: SecuritySeverity.CRITICAL,
            VulnerabilityType.SQL_INJECTION: SecuritySeverity.CRITICAL,
            VulnerabilityType.HARDCODED_SECRETS: SecuritySeverity.HIGH,
            VulnerabilityType.INSECURE_RANDOM: SecuritySeverity.MEDIUM,
            VulnerabilityType.PATH_TRAVERSAL: SecuritySeverity.HIGH,
            VulnerabilityType.UNSAFE_DESERIALIZATION: SecuritySeverity.HIGH,
            VulnerabilityType.XSS_VULNERABILITY: SecuritySeverity.HIGH,
            VulnerabilityType.COMMAND_INJECTION: SecuritySeverity.CRITICAL,
            VulnerabilityType.INSECURE_PROTOCOL: SecuritySeverity.MEDIUM,
            VulnerabilityType.WEAK_CRYPTO: SecuritySeverity.MEDIUM,
            VulnerabilityType.DEBUG_MODE: SecuritySeverity.LOW,
            VulnerabilityType.VERBOSE_ERRORS: SecuritySeverity.LOW,
        }
        
        # Ajustar severidad si hay input de usuario involucrado
        user_input_indicators = ['request', 'input()', 'sys.argv', 'os.environ', 'form', 'query']
        if any(indicator in line.lower() for indicator in user_input_indicators):
            # Aumentar severidad si hay input de usuario
            severity_map = {
                SecuritySeverity.INFO: SecuritySeverity.LOW,
                SecuritySeverity.LOW: SecuritySeverity.MEDIUM,
                SecuritySeverity.MEDIUM: SecuritySeverity.HIGH,
                SecuritySeverity.HIGH: SecuritySeverity.CRITICAL,
            }
            base_severity = default_severity.get(vuln_type, SecuritySeverity.MEDIUM)
            return severity_map.get(base_severity, base_severity)
        
        return default_severity.get(vuln_type, SecuritySeverity.MEDIUM)
    
    def _calculate_security_score(self, findings: List[SecurityFinding]) -> float:
        """Calcula security score (0-100) basado en hallazgos"""
        if not findings:
            return 100.0
        
        # Pesos por severidad
        severity_weights = {
            SecuritySeverity.CRITICAL: 25,
            SecuritySeverity.HIGH: 15,
            SecuritySeverity.MEDIUM: 8,
            SecuritySeverity.LOW: 3,
            SecuritySeverity.INFO: 1,
        }
        
        total_penalty = sum(
            severity_weights.get(f.severity, 5) * f.confidence
            for f in findings
        )
        
        # Score = 100 - penalización (mínimo 0)
        score = max(0, 100 - total_penalty)
        return score
    
    def _determine_risk_level(self, security_score: float, critical_count: int) -> str:
        """Determina nivel de riesgo basado en score y críticos"""
        if critical_count > 0:
            return "CRITICAL"
        elif security_score >= 90:
            return "LOW"
        elif security_score >= 70:
            return "MEDIUM"
        elif security_score >= 50:
            return "HIGH"
        else:
            return "CRITICAL"
    
    def _deduplicate_findings(self, findings: List[SecurityFinding]) -> List[SecurityFinding]:
        """Elimina hallazgos duplicados (mismo tipo, línea y archivo)"""
        seen = set()
        unique = []
        
        for finding in findings:
            key = (finding.vulnerability_type, finding.line_number, finding.file_name)
            if key not in seen:
                seen.add(key)
                unique.append(finding)
        
        return unique
    
    def _is_os_module(self, node: ast.Call) -> bool:
        """Verifica si una llamada es del módulo os"""
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                return node.func.value.id == 'os'
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del analista"""
        return {
            **self.stats,
            "last_scan": self.stats.get("last_scan"),
            "most_common_vulnerabilities": sorted(
                self.stats["vulnerabilities_by_type"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }
    
    def set_custom_analyzer(self, callback: Callable[[str, str], List[SecurityFinding]]):
        """Establece un analizador personalizado"""
        self.custom_analyzer_callback = callback


# Instancia global
_analyst: Optional[SecurityAnalyst] = None


def get_security_analyst(config: Optional[Dict] = None) -> SecurityAnalyst:
    """Obtiene la instancia global del Security Analyst"""
    global _analyst
    if _analyst is None:
        _analyst = SecurityAnalyst(config)
    return _analyst


def analyze_code_security(code: str, file_name: str = "generated_code.py") -> SecurityReport:
    """Función helper para analizar seguridad de código"""
    return get_security_analyst().analyze(code, file_name)


if __name__ == "__main__":
    # Ejemplo de uso
    print("=== Claw-Litle 1.0 - Security Analyst ===\n")
    
    analyst = get_security_analyst()
    
    # Código de ejemplo con vulnerabilidades
    test_code = '''
import os
import pickle

def process_user_input(user_input):
    # Vulnerabilidad: eval() con input de usuario
    result = eval(user_input)
    
    # Vulnerabilidad: hardcodeado
    password = "secret123"
    
    # Vulnerabilidad: comando del sistema
    os.system(f"echo {user_input}")
    
    # Vulnerabilidad: pickle inseguro
    data = pickle.loads(user_input)
    
    return result

def unsafe_query(db, user_id):
    # Vulnerabilidad: SQL injection
    query = f"SELECT * FROM users WHERE id = {user_id}"
    db.execute(query)
'''
    
    report = analyst.analyze(test_code, "vulnerable_example.py")
    
    print(f"Security Score: {report.security_score}/100")
    print(f"Risk Level: {report.risk_level}")
    print(f"Total Findings: {report.total_findings}")
    print(f"  Critical: {report.critical_count}")
    print(f"  High: {report.high_count}")
    print(f"  Medium: {report.medium_count}")
    print(f"  Low: {report.low_count}")
    print(f"  Info: {report.info_count}")
    print(f"\nAnalysis Time: {report.analysis_time_ms:.2f}ms")
    
    print("\n=== Hallazgos Detallados ===")
    for finding in report.findings:
        print(f"\n[{finding.severity.value.upper()}] {finding.vulnerability_type.value}")
        print(f"  Línea {finding.line_number}: {finding.description}")
        print(f"  Código: {finding.code_snippet}")
        print(f"  CWE: {finding.cwe_id}")
        print(f"  OWASP: {finding.owasp_category}")
        print(f"  Recomendación: {finding.recommendation}")
        print(f"  Confianza: {finding.confidence:.0%}")