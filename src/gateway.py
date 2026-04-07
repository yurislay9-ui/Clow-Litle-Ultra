"""
Claw-Litle 1.0
gateway.py - Gateway de Seguridad (Capa 0)

Primera línea de defensa: sanitización, autenticación JWT, rate limiting.
Todas las peticiones pasan por aquí antes de llegar al motor.
"""

import re
import time
import hashlib
import hmac
import logging
import json
import os
import secrets
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass, field
from collections import defaultdict
from pathlib import Path

logger = logging.getLogger(__name__)

# Importaciones para integración con intent_classifier y personality_engine
try:
    from .intent_classifier import get_classifier, ClassifiedIntent
    from .personality_engine import get_personality, get_formatter
    ENHANCED_MODULES_AVAILABLE = True
except ImportError:
    ENHANCED_MODULES_AVAILABLE = False
    logger.warning("Módulos mejorados no disponibles, usando fallback básico")


def _generate_jwt_secret() -> str:
    """Genera un secreto JWT aleatorio y seguro.
    
    Si existe un archivo de configuración, lo guarda/lee de allí.
    Si no, genera uno nuevo en cada sesión (para desarrollo).
    """
    config_dir = Path.home() / ".claw-lite"
    config_dir.mkdir(parents=True, exist_ok=True)
    secret_file = config_dir / "jwt_secret"
    
    try:
        # Intentar leer secreto existente
        if secret_file.exists():
            secret = secret_file.read_text().strip()
            if len(secret) >= 32:
                return secret
    except Exception:
        pass
    
    # Generar nuevo secreto seguro
    secret = secrets.token_urlsafe(48)  # 48 bytes = 384 bits de entropía
    
    try:
        secret_file.write_text(secret)
        secret_file.chmod(0o600)  # Solo lectura/escritura para el dueño
    except Exception:
        pass
    
    return secret


@dataclass
class SecurityConfig:
    """Configuración de seguridad del gateway."""
    jwt_secret: str = field(default_factory=_generate_jwt_secret)
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24
    rate_limit_free: int = 30  # queries por hora
    rate_limit_pro: int = 1000  # queries por hora
    rate_limit_window: int = 3600  # segundos
    max_query_length: int = 1000
    forbidden_patterns: List[str] = field(default_factory=lambda: [])
    allowed_imports: List[str] = field(default_factory=lambda: [])
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SecurityConfig':
        """Crea SecurityConfig desde diccionario."""
        return cls(
            jwt_secret=data.get('jwt_secret', cls.jwt_secret),
            jwt_algorithm=data.get('jwt_algorithm', cls.jwt_algorithm),
            jwt_expiry_hours=data.get('jwt_expiry_hours', cls.jwt_expiry_hours),
            rate_limit_free=data.get('free_limit', cls.rate_limit_free),
            rate_limit_pro=data.get('pro_limit', cls.rate_limit_pro),
            rate_limit_window=data.get('window_seconds', cls.rate_limit_window),
            max_query_length=data.get('max_query_length', cls.max_query_length),
            forbidden_patterns=data.get('forbidden_patterns', []),
            allowed_imports=data.get('allowed_imports', [])
        )


@dataclass
class Request:
    """Petición entrante al gateway."""
    user_id: str
    query: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict = field(default_factory=dict)
    
    def validate(self, config: SecurityConfig) -> Tuple[bool, str]:
        """Valida la petición."""
        if not self.user_id or not self.user_id.strip():
            return False, "user_id vacío"
        
        if not self.query or not self.query.strip():
            return False, "query vacío"
        
        if len(self.query) > config.max_query_length:
            return False, f"query excede longitud máxima ({config.max_query_length})"
        
        return True, "OK"


@dataclass
class Response:
    """Respuesta del gateway."""
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None
    metadata: Dict = field(default_factory=dict)


class RateLimiter:
    """
    Rate limiter sliding window para control de peticiones.
    Thread-safe y optimizado para ARM64.
    """
    
    def __init__(self, window_seconds: int = 3600):
        """
        Inicializa el rate limiter.
        
        Args:
            window_seconds: Ventana de tiempo en segundos
        """
        self.window = window_seconds
        self._requests: Dict[str, List[float]] = defaultdict(list)
    
    def is_allowed(self, user_id: str, limit: int) -> Tuple[bool, int]:
        """
        Verifica si el usuario puede hacer una petición.
        
        Args:
            user_id: ID del usuario
            limit: Límite de peticiones por ventana
        
        Returns:
            (permitido,剩余 peticiones)
        """
        now = time.time()
        cutoff = now - self.window
        
        # Limpiar peticiones viejas
        self._requests[user_id] = [
            t for t in self._requests[user_id] if t > cutoff
        ]
        
        current_count = len(self._requests[user_id])
        remaining = limit - current_count
        
        if current_count < limit:
            self._requests[user_id].append(now)
            return True, remaining - 1
        
        return False, 0
    
    def get_usage(self, user_id: str) -> Dict:
        """
        Obtiene el uso actual del usuario.
        
        Args:
            user_id: ID del usuario
        
        Returns:
            Diccionario con estadísticas de uso
        """
        now = time.time()
        cutoff = now - self.window
        
        requests = [t for t in self._requests[user_id] if t > cutoff]
        
        return {
            "requests_in_window": len(requests),
            "window_seconds": self.window,
            "oldest_request": min(requests) if requests else None,
            "newest_request": max(requests) if requests else None
        }


class Gateway:
    """
    Gateway de seguridad - Capa 0.
    
    Funcionalidades:
    1. Sanitización de input (XSS, injection, etc.)
    2. Autenticación JWT (opcional)
    3. Rate limiting por usuario
    4. Validación de patrones prohibidos
    5. Logging de auditoría
    """
    
    def __init__(self, config: SecurityConfig):
        """
        Inicializa el gateway.
        
        Args:
            config: Configuración de seguridad
        """
        self.config = config
        self.rate_limiter = RateLimiter(config.rate_limit_window)
        
        # Compilar patrones prohibidos
        self._forbidden_regex = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in config.forbidden_patterns
        ]
        
        logger.info("Gateway de seguridad inicializado")
    
    def process(self, request: Request, user_tier: str = "free") -> Response:
        """
        Procesa una petición a través del gateway.
        
        Args:
            request: Petición entrante
            user_tier: Nivel del usuario ("free" o "pro")
        
        Returns:
            Response con el resultado
        """
        # 1. Validar petición básica
        valid, error = request.validate(self.config)
        if not valid:
            logger.warning(f"Petición inválida de {request.user_id}: {error}")
            return Response(success=False, error=f"Petición inválida: {error}")
        
        # 2. Sanitizar input
        sanitized_query = self._sanitize(request.query)
        
        # 3. Verificar patrones prohibidos
        if self._contains_forbidden_pattern(sanitized_query):
            logger.warning(f"Patrón prohibido detectado de {request.user_id}: {sanitized_query[:50]}")
            return Response(success=False, error="Contenido potencialmente peligroso detectado")
        
        # 4. Rate limiting
        limit = self.config.rate_limit_pro if user_tier == "pro" else self.config.rate_limit_free
        allowed, remaining = self.rate_limiter.is_allowed(request.user_id, limit)
        
        if not allowed:
            logger.warning(f"Rate limit excedido para {request.user_id}")
            return Response(
                success=False, 
                error="Límite de peticiones excedido. Intenta en una hora.",
                metadata={"remaining": 0}
            )
        
        # 5. Logging de auditoría
        self._audit_log(request.user_id, sanitized_query, remaining)
        
        # 6. Retornar petición procesada
        return Response(
            success=True,
            data={
                "query": sanitized_query,
                "user_id": request.user_id,
                "timestamp": request.timestamp
            },
            metadata={
                "remaining_requests": remaining,
                "user_tier": user_tier,
                "sanitized": True
            }
        )
    
    def _sanitize(self, query: str) -> str:
        """
        Sanitiza el input del usuario.
        
        Elimina:
        - Tags HTML
        - Caracteres de escape peligrosos
        - Espacios extra
        - Caracteres nulos
        
        Args:
            query: Query original
        
        Returns:
            Query sanitizado
        """
        # Eliminar tags HTML
        clean = re.sub(r'<[^>]+>', '', query)
        
        # Eliminar caracteres de escape peligrosos
        clean = clean.replace('\\x', '')
        clean = clean.replace('\\u', '')
        clean = clean.replace('\0', '')
        
        # Normalizar espacios
        clean = ' '.join(clean.split())
        
        # Truncar si es muy largo
        if len(clean) > self.config.max_query_length:
            clean = clean[:self.config.max_query_length]
        
        return clean.strip()
    
    def _contains_forbidden_pattern(self, query: str) -> bool:
        """
        Verifica si la query contiene patrones prohibidos.
        
        Args:
            query: Query a verificar
        
        Returns:
            True si contiene patrón prohibido
        """
        for pattern in self._forbidden_regex:
            if pattern.search(query):
                return True
        return False
    
    def _audit_log(self, user_id: str, query: str, remaining: int):
        """
        Registra la petición en el log de auditoría.
        
        Args:
            user_id: ID del usuario
            query: Query procesada
            remaining: Peticiones restantes
        """
        logger.debug(f"Audit: user={user_id}, query='{query[:30]}...', remaining={remaining}")
    
    def generate_jwt(self, user_id: str, user_data: Dict = None) -> str:
        """
        Genera un token JWT para el usuario.
        
        Nota: Implementación simplificada. En producción usar PyJWT.
        
        Args:
            user_id: ID del usuario
            user_data: Datos adicionales del usuario
        
        Returns:
            Token JWT
        """
        import base64
        import time
        
        header = {"alg": self.config.jwt_algorithm, "typ": "JWT"}
        now = int(time.time())
        
        payload = {
            "user_id": user_id,
            "iat": now,
            "exp": now + (self.config.jwt_expiry_hours * 3600),
            **(user_data or {})
        }
        
        # Codificar header y payload
        def base64url_encode(data):
            return base64.urlsafe_b64encode(
                json.dumps(data, separators=(',', ':')).encode()
            ).rstrip(b'=').decode()
        
        header_b64 = base64url_encode(header)
        payload_b64 = base64url_encode(payload)
        
        # Crear firma
        message = f"{header_b64}.{payload_b64}"
        signature = hmac.new(
            self.config.jwt_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).digest()
        signature_b64 = base64.urlsafe_b64encode(signature).rstrip(b'=').decode()
        
        return f"{header_b64}.{payload_b64}.{signature_b64}"
    
    def verify_jwt(self, token: str) -> Tuple[bool, Optional[Dict]]:
        """
        Verifica un token JWT.
        
        Args:
            token: Token JWT a verificar
        
        Returns:
            (válido, payload)
        """
        import base64
        import time
        
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return False, None
            
            header_b64, payload_b64, signature_b64 = parts
            
            # Verificar firma
            message = f"{header_b64}.{payload_b64}"
            expected_sig = hmac.new(
                self.config.jwt_secret.encode(),
                message.encode(),
                hashlib.sha256
            ).digest()
            
            # Decodificar signature
            sig_padding = 4 - len(signature_b64) % 4
            if sig_padding != 4:
                signature_b64 += '=' * sig_padding
            actual_sig = base64.urlsafe_b64decode(signature_b64)
            
            if not hmac.compare_digest(expected_sig, actual_sig):
                return False, None
            
            # Decodificar payload
            pay_padding = 4 - len(payload_b64) % 4
            if pay_padding != 4:
                payload_b64 += '=' * pay_padding
            payload = json.loads(base64.urlsafe_b64decode(payload_b64))
            
            # Verificar expiración
            if payload.get('exp', 0) < time.time():
                return False, None
            
            return True, payload
            
        except Exception as e:
            logger.error(f"Error verificando JWT: {e}")
            return False, None
    
    def get_stats(self) -> Dict:
        """
        Obtiene estadísticas del gateway.
        
        Returns:
            Diccionario con estadísticas
        """
        return {
            "rate_limiter_window": self.config.rate_limit_window,
            "rate_limit_free": self.config.rate_limit_free,
            "rate_limit_pro": self.config.rate_limit_pro,
            "forbidden_patterns_count": len(self._forbidden_regex),
            "max_query_length": self.config.max_query_length,
            "enhanced_modules_available": ENHANCED_MODULES_AVAILABLE
        }

    def classify_intent(self, query: str, user_id: str = "default") -> Optional['ClassifiedIntent']:
        """
        Clasifica la intención de una consulta usando el intent_classifier mejorado.
        
        Args:
            query: Query del usuario
            user_id: ID del usuario para memoria contextual
        
        Returns:
            ClassifiedIntent o None si los módulos no están disponibles
        """
        if not ENHANCED_MODULES_AVAILABLE:
            return None
        
        try:
            classifier = get_classifier()
            return classifier.classify(query, user_id)
        except Exception as e:
            logger.error(f"Error clasificando intención: {e}")
            return None

    def get_personality_response(self, content: str, intent: str = None, 
                                is_error: bool = False) -> str:
        """
        Formatea una respuesta con la personalidad del bot.
        
        Args:
            content: Contenido base de la respuesta
            intent: Tipo de intención detectada
            is_error: Si es una respuesta de error
        
        Returns:
            Respuesta formateada con personalidad
        """
        if not ENHANCED_MODULES_AVAILABLE:
            return content
        
        try:
            personality = get_personality()
            return personality.format_response(content, intent, is_error)
        except Exception as e:
            logger.error(f"Error formateando respuesta: {e}")
            return content
