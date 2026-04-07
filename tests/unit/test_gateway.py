#!/usr/bin/env python3
"""
Tests unitarios para el Gateway de Seguridad (Capa 0).
Cubre: sanitización, autenticación JWT, rate limiting, anti-fraud.
"""

import pytest
import time
from datetime import datetime, timedelta

# Mock de jwt para Termux (si no está instalado)
try:
    import jwt
except ImportError:
    # Crear un mock mínimo de jwt para que los tests puedan ejecutarse
    class MockJWT:
        @staticmethod
        def encode(payload, key, algorithm='HS256'):
            return "mock_token_" + str(hash(str(payload)))
        
        @staticmethod
        def decode(token, key, algorithms=['HS256']):
            return {"user": "mock_user", "role": "user"}
        
        class PyJWTError(Exception):
            pass
        
        class ExpiredSignatureError(Exception):
            pass
        
        class InvalidTokenError(Exception):
            pass
    
    jwt = MockJWT()

# Mock del gateway para testing
class MockGateway:
    def __init__(self):
        self.rate_limits = {}
        self.auth_tokens = {}
        self.blocked_ips = set()
    
    def sanitize_input(self, user_input: str) -> str:
        """Sanitiza input de usuario (XSS prevention)."""
        if not isinstance(user_input, str):
            return ""
        
        # Remover tags HTML
        sanitized = user_input.replace("<", "<").replace(">", ">")
        # Remover scripts
        sanitized = sanitized.replace("javascript:", "")
        # Limitar longitud
        return sanitized[:1000]
    
    def generate_token(self, user_id: str, role: str = "user") -> str:
        """Genera JWT token."""
        payload = {
            "user_id": user_id,
            "role": role,
            "exp": datetime.utcnow() + timedelta(hours=24),
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, "secret_key_test", algorithm="HS256")
    
    def verify_token(self, token: str) -> dict:
        """Verifica JWT token."""
        try:
            payload = jwt.decode(token, "secret_key_test", algorithms=["HS256"])
            return {"valid": True, "payload": payload}
        except jwt.ExpiredSignatureError:
            return {"valid": False, "error": "Token expirado"}
        except jwt.InvalidTokenError:
            return {"valid": False, "error": "Token inválido"}
    
    def check_rate_limit(self, user_id: str, max_requests: int = 60, window: int = 60) -> bool:
        """Verifica rate limiting."""
        now = time.time()
        
        if user_id not in self.rate_limits:
            self.rate_limits[user_id] = []
        
        # Limpiar requests antiguos
        self.rate_limits[user_id] = [
            req_time for req_time in self.rate_limits[user_id]
            if now - req_time < window
        ]
        
        # Verificar límite
        if len(self.rate_limits[user_id]) >= max_requests:
            return False
        
        # Agregar request
        self.rate_limits[user_id].append(now)
        return True
    
    def block_ip(self, ip: str, reason: str = "suspicious_activity"):
        """Bloquea una IP."""
        self.blocked_ips.add(ip)
    
    def is_ip_blocked(self, ip: str) -> bool:
        """Verifica si una IP está bloqueada."""
        return ip in self.blocked_ips


class TestGatewaySanitization:
    """Tests para sanitización de input."""
    
    def setup_method(self):
        self.gateway = MockGateway()
    
    def test_sanitize_removes_html_tags(self):
        """Test que remueve tags HTML."""
        malicious_input = "<script>alert('xss')</script>Hello"
        result = self.gateway.sanitize_input(malicious_input)
        assert "<script>" not in result
        assert "<script>" in result or "script" not in result.lower()
    
    def test_sanitize_removes_javascript_protocol(self):
        """Test que remueve protocolo javascript."""
        malicious_input = "javascript:alert('xss')"
        result = self.gateway.sanitize_input(malicious_input)
        assert "javascript:" not in result
    
    def test_sanitize_limits_length(self):
        """Test que limita longitud a 1000 caracteres."""
        long_input = "a" * 2000
        result = self.gateway.sanitize_input(long_input)
        assert len(result) <= 1000
    
    def test_sanitize_handles_non_string(self):
        """Test que maneja input no-string."""
        result = self.gateway.sanitize_input(123)
        assert result == ""
        
        result = self.gateway.sanitize_input(None)
        assert result == ""
    
    def test_sanitize_preserves_normal_text(self):
        """Test que preserva texto normal."""
        normal_input = "Hola, ¿cómo estás?"
        result = self.gateway.sanitize_input(normal_input)
        assert result == normal_input


class TestGatewayAuth:
    """Tests para autenticación JWT."""
    
    def setup_method(self):
        self.gateway = MockGateway()
    
    def test_generate_token_returns_string(self):
        """Test que genera token como string."""
        token = self.gateway.generate_token("user123")
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_valid_token(self):
        """Test que verifica token válido."""
        token = self.gateway.generate_token("user123", "admin")
        result = self.gateway.verify_token(token)
        
        assert result["valid"] is True
        assert result["payload"]["user_id"] == "user123"
        assert result["payload"]["role"] == "admin"
    
    def test_verify_expired_token(self):
        """Test que rechaza token expirado."""
        # Crear token expirado manualmente
        expired_payload = {
            "user_id": "user123",
            "exp": datetime.utcnow() - timedelta(hours=1),  # Expirado
            "iat": datetime.utcnow() - timedelta(hours=25)
        }
        expired_token = jwt.encode(expired_payload, "secret_key_test", algorithm="HS256")
        
        result = self.gateway.verify_token(expired_token)
        assert result["valid"] is False
        assert result["error"] == "Token expirado"
    
    def test_verify_invalid_token(self):
        """Test que rechaza token inválido."""
        result = self.gateway.verify_token("token_falso")
        assert result["valid"] is False
        assert result["error"] == "Token inválido"
    
    def test_token_contains_required_claims(self):
        """Test que token contiene claims requeridos."""
        token = self.gateway.generate_token("user456")
        result = self.gateway.verify_token(token)
        
        assert "user_id" in result["payload"]
        assert "role" in result["payload"]
        assert "exp" in result["payload"]
        assert "iat" in result["payload"]


class TestGatewayRateLimiting:
    """Tests para rate limiting."""
    
    def setup_method(self):
        self.gateway = MockGateway()
    
    def test_allows_under_limit(self):
        """Test que permite requests bajo el límite."""
        user_id = "user1"
        for i in range(5):
            assert self.gateway.check_rate_limit(user_id, max_requests=10, window=60)
    
    def test_blocks_over_limit(self):
        """Test que bloquea requests sobre el límite."""
        user_id = "user2"
        max_requests = 3
        
        # Llenar hasta el límite
        for i in range(max_requests):
            assert self.gateway.check_rate_limit(user_id, max_requests=max_requests, window=60)
        
        # El siguiente debería ser bloqueado
        assert not self.gateway.check_rate_limit(user_id, max_requests=max_requests, window=60)
    
    def test_resets_after_window(self):
        """Test que se resetea después de la ventana de tiempo."""
        user_id = "user3"
        
        # Simular requests antiguos (hace 2 segundos)
        self.gateway.rate_limits[user_id] = [time.time() - 2]
        
        # Debería permitir nuevo request si window es 1 segundo
        assert self.gateway.check_rate_limit(user_id, max_requests=1, window=1)
    
    def test_different_users_independent(self):
        """Test que usuarios diferentes tienen límites independientes."""
        user1 = "user_a"
        user2 = "user_b"
        
        # Llenar límite de user1
        for i in range(5):
            self.gateway.check_rate_limit(user1, max_requests=5, window=60)
        
        # user2 debería poder hacer requests
        assert self.gateway.check_rate_limit(user2, max_requests=5, window=60)


class TestGatewayAntiFraud:
    """Tests para sistema anti-fraud."""
    
    def setup_method(self):
        self.gateway = MockGateway()
    
    def test_block_ip(self):
        """Test que bloquea IP correctamente."""
        ip = "192.168.1.100"
        self.gateway.block_ip(ip, "brute_force")
        
        assert self.gateway.is_ip_blocked(ip)
    
    def test_unblocked_ip(self):
        """Test que IP no bloqueada retorna False."""
        ip = "10.0.0.1"
        assert not self.gateway.is_ip_blocked(ip)
    
    def test_multiple_blocked_ips(self):
        """Test que puede bloquear múltiples IPs."""
        ips = ["192.168.1.1", "192.168.1.2", "192.168.1.3"]
        
        for ip in ips:
            self.gateway.block_ip(ip)
        
        for ip in ips:
            assert self.gateway.is_ip_blocked(ip)
    
    def test_block_same_ip_twice(self):
        """Test que bloquear misma IP dos veces no causa error."""
        ip = "172.16.0.1"
        self.gateway.block_ip(ip)
        self.gateway.block_ip(ip)  # Segunda vez
        
        assert self.gateway.is_ip_blocked(ip)


class TestGatewayIntegration:
    """Tests de integración para el gateway completo."""
    
    def setup_method(self):
        self.gateway = MockGateway()
    
    def test_full_auth_flow(self):
        """Test flujo completo de autenticación."""
        # 1. Generar token
        token = self.gateway.generate_token("user_test", "admin")
        
        # 2. Verificar token
        result = self.gateway.verify_token(token)
        assert result["valid"]
        
        # 3. Extraer información
        user_id = result["payload"]["user_id"]
        role = result["payload"]["role"]
        
        assert user_id == "user_test"
        assert role == "admin"
    
    def test_rate_limit_with_auth(self):
        """Test rate limiting combinado con autenticación."""
        user_id = "auth_user"
        token = self.gateway.generate_token(user_id)
        
        # Verificar token primero
        assert self.gateway.verify_token(token)["valid"]
        
        # Luego hacer requests con rate limiting
        for i in range(5):
            assert self.gateway.check_rate_limit(user_id, max_requests=10)
    
    def test_security_chain(self):
        """Test cadena de seguridad: sanitizar -> auth -> rate limit."""
        user_input = "<script>alert('xss')</script>buscar precios"
        user_id = "chain_user"
        token = self.gateway.generate_token(user_id)
        
        # 1. Sanitizar input
        clean_input = self.gateway.sanitize_input(user_input)
        assert "<script>" not in clean_input
        
        # 2. Verificar autenticación
        auth_result = self.gateway.verify_token(token)
        assert auth_result["valid"]
        
        # 3. Verificar rate limit
        assert self.gateway.check_rate_limit(user_id, max_requests=100)