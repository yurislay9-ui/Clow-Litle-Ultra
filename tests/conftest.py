"""
Claw-Litle 1.0
conftest.py - Fixtures compartidos para pytest

Proporciona fixtures reutilizables para todos los tests.
"""

import pytest
import json
from pathlib import Path


@pytest.fixture
def sample_intents_registry():
    """Registro de intenciones de prueba."""
    return {
        "version": "1.0.0",
        "intents": [
            {
                "name": "greet",
                "description": "Maneja saludos simples",
                "triggers": {
                    "keywords": ["hola", "buenos", "buenas", "hey"],
                    "patterns": ["^hola$", "^buen[ao]s?$", "^hey$"]
                },
                "handler": {
                    "type": "inline",
                    "details": {"response": "¡Hola!"}
                }
            },
            {
                "name": "farewell",
                "description": "Maneja despedidas",
                "triggers": {
                    "keywords": ["chao", "adios", "hasta"],
                    "patterns": ["^chau?$$", "^adi[oó]s?$"]
                },
                "handler": {
                    "type": "inline",
                    "details": {"response": "¡Adiós!"}
                }
            },
            {
                "name": "help",
                "description": "Muestra ayuda",
                "triggers": {
                    "keywords": ["ayuda", "help"],
                    "patterns": ["^ayuda$", "^help$"]
                },
                "handler": {
                    "type": "inline",
                    "details": {"response": "Ayuda..."}
                }
            }
        ],
        "fallback": {
            "type": "agent",
            "details": {"agent": "router", "action": "intelligent_routing"}
        }
    }


@pytest.fixture
def sample_security_config():
    """Configuración de seguridad de prueba."""
    from src.gateway import SecurityConfig
    return SecurityConfig(
        jwt_secret="test-secret-key-12345",
        jwt_algorithm="HS256",
        jwt_expiry_hours=1,
        rate_limit_free=10,
        rate_limit_pro=100,
        rate_limit_window=60,
        max_query_length=500,
        forbidden_patterns=[
            r"<script>",
            r"javascript:",
            r"DROP TABLE",
            r"rm -rf /"
        ],
        allowed_imports=["requests", "json", "re"]
    )


@pytest.fixture
def sample_router_config():
    """Configuración de router de prueba."""
    from src.router import RouterConfig
    return RouterConfig(
        max_retries=2,
        timeout_seconds=10,
        enable_caching=True,
        cache_ttl_seconds=60,
        fallback_to_search=True
    )


@pytest.fixture
def sample_engine_config():
    """Configuración de engine de prueba."""
    return {
        "level_1_enabled": True,
        "level_2_enabled": True,
        "level_3_enabled": False,  # Desactivado para tests sin ONNX
        "level_4_enabled": True,
        "short_circuit_threshold": 0.95,
        "fuzzy_threshold": 0.85,
        "semantic_threshold": 0.89,
        "model_path": "models/keep/model.onnx"
    }


@pytest.fixture
def sample_user_context():
    """Contexto de usuario de prueba."""
    return {
        "user_id": "test_user_123",
        "tier": "free",
        "recent_intents": [],
        "mode": "development"
    }


@pytest.fixture
def temp_config_dir(tmp_path):
    """Directorio temporal para perfiles de entorno."""
    profiles = {
        "termux_arm64.json": {
            "profile_name": "termux_arm64",
            "environment": {"arch": "arm64-v8a", "has_gui_display": False},
            "capabilities_detected": {
                "max_concurrent_agents": 2,
                "max_memory_mb": 350,
                "supports_onnx": True
            },
            "limits": {"max_query_length": 1000, "timeout_long_seconds": 30}
        },
        "laptop_pc.json": {
            "profile_name": "laptop_pc",
            "environment": {"arch": "x86_64", "has_gui_display": True},
            "capabilities_detected": {
                "max_concurrent_agents": 6,
                "max_memory_mb": 1000,
                "supports_onnx": True
            },
            "limits": {"max_query_length": 2000, "timeout_long_seconds": 60}
        }
    }
    
    for filename, content in profiles.items():
        with open(tmp_path / filename, 'w') as f:
            json.dump(content, f)
    
    return tmp_path


@pytest.fixture
def sample_request():
    """Petición de prueba."""
    from src.gateway import Request
    return Request(
        user_id="test_user",
        query="hola mundo",
        metadata={"source": "test"}
    )


@pytest.fixture
def malicious_requests():
    """Peticiones maliciosas de prueba."""
    from src.gateway import Request
    return [
        Request(user_id="attacker", query="<script>alert('xss')</script>"),
        Request(user_id="attacker", query="'; DROP TABLE users; --"),
        Request(user_id="attacker", query="javascript:alert(1)"),
        Request(user_id="attacker", query="rm -rf /"),
        Request(user_id="attacker", query="A" * 10000),  # Muy largo
        Request(user_id="", query="hola"),  # User vacío
        Request(user_id="test", query=""),  # Query vacío
    ]


@pytest.fixture
def benchmark_queries():
    """Queries para benchmarks de rendimiento."""
    return [
        "hola",                           # Simple
        "holaa",                          # Fuzzy
        "buscar información sobre Python",  # Compleja
        "crear una app para gestionar tareas",  # Code gen
        "A" * 100,                        # Larga
    ]