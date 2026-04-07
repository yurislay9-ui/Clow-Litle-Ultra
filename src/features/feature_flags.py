"""
Feature Flags System - Claw-Litle 1.0

Sistema de Feature Flags para activar/desactivar nuevas características
sin necesidad de deploy, permitiendo testing gradual y rollback seguro.
"""

import json
import os
import threading
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path


class FeatureFlag:
    """Representa un feature flag individual"""
    
    def __init__(
        self,
        name: str,
        enabled: bool = False,
        description: str = "",
        rollout_percentage: float = 0.0,
        user_ids: Optional[List[str]] = None,
        expiration: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.enabled = enabled
        self.description = description
        self.rollout_percentage = rollout_percentage  # 0-100
        self.user_ids = user_ids or []
        self.expiration = expiration
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def is_enabled_for_user(self, user_id: Optional[str] = None) -> bool:
        """Verifica si el feature está habilitado para un usuario específico"""
        
        # Si está deshabilitado globalmente
        if not self.enabled:
            return False
        
        # Verificar expiración
        if self.expiration and datetime.now() > self.expiration:
            return False
        
        # Verificar lista específica de usuarios
        if self.user_ids:
            if user_id in self.user_ids:
                return True
            # Si hay user_ids específicos, solo esos usuarios tienen acceso
            if user_id is not None:
                return False
        
        # Verificar rollout percentage
        if self.rollout_percentage > 0:
            # Usar hash del user_id para consistencia
            if user_id:
                hash_value = hash(user_id + self.name) % 100
                return hash_value < self.rollout_percentage
            else:
                # Para usuarios anónimos, usar porcentaje aleatorio
                import random
                return random.random() * 100 < self.rollout_percentage
        
        # Si está habilitado y no hay restricciones
        return self.enabled
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa el feature flag a diccionario"""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "description": self.description,
            "rollout_percentage": self.rollout_percentage,
            "user_ids": self.user_ids,
            "expiration": self.expiration.isoformat() if self.expiration else None,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeatureFlag":
        """Crea un FeatureFlag desde un diccionario"""
        flag = cls(
            name=data["name"],
            enabled=data.get("enabled", False),
            description=data.get("description", ""),
            rollout_percentage=data.get("rollout_percentage", 0.0),
            user_ids=data.get("user_ids"),
            metadata=data.get("metadata")
        )
        
        if data.get("expiration"):
            flag.expiration = datetime.fromisoformat(data["expiration"])
        
        if data.get("created_at"):
            flag.created_at = datetime.fromisoformat(data["created_at"])
        
        if data.get("updated_at"):
            flag.updated_at = datetime.fromisoformat(data["updated_at"])
        
        return flag


class FeatureFlagsManager:
    """Gestor central de Feature Flags para Claw-Litle"""
    
    # Feature flags predefinidos para 1.0
    CURRENT_FEATURE_FLAGS = {
        "self_refining_reasoning": {
            "enabled": False,
            "description": "Motor de razonamiento auto-refinado (3 iteraciones)",
            "rollout_percentage": 0.0,
            "metadata": {
                "category": "reasoning",
                "phase": "v4",
                "impact": "high",
                "performance_overhead": "+200-800ms per query"
            }
        },
        "adaptive_thinking": {
            "enabled": False,
            "description": "Sistema de pensamiento adaptativo (4 niveles)",
            "rollout_percentage": 0.0,
            "metadata": {
                "category": "reasoning",
                "phase": "v4",
                "impact": "high",
                "levels": ["rápido", "estándar", "profundo", "máximo"]
            }
        },
        "kairos_daemon": {
            "enabled": False,
            "description": "Agente persistente en background (autoDream)",
            "rollout_percentage": 0.0,
            "metadata": {
                "category": "background",
                "phase": "v4",
                "impact": "high",
                "performance_overhead": "+2-5% CPU, +10-30MB RAM when idle"
            }
        },
        "security_analyst": {
            "enabled": False,
            "description": "Auditoría de seguridad integrada en code generation",
            "rollout_percentage": 0.0,
            "metadata": {
                "category": "security",
                "phase": "v4",
                "impact": "high",
                "safe_default": True
            }
        },
        "context_management_pipeline": {
            "enabled": False,
            "description": "Gestión inteligente de contexto (4 etapas)",
            "rollout_percentage": 0.0,
            "metadata": {
                "category": "memory",
                "phase": "v4",
                "impact": "medium",
                "performance_overhead": "+50-100ms per compaction"
            }
        },
        "enhanced_buddy_reviewer": {
            "enabled": False,
            "description": "Buddy Reviewer con aprendizaje continuo",
            "rollout_percentage": 0.0,
            "metadata": {
                "category": "code_quality",
                "phase": "v4",
                "impact": "medium"
            }
        },
        "query_complexity_analyzer": {
            "enabled": False,
            "description": "Analizador de complejidad de queries",
            "rollout_percentage": 0.0,
            "metadata": {
                "category": "routing",
                "phase": "v4",
                "impact": "medium"
            }
        },
        "telemetry_framework": {
            "enabled": False,
            "description": "Framework de telemetría para métricas base",
            "rollout_percentage": 0.0,
            "metadata": {
                "category": "monitoring",
                "phase": "foundation",
                "impact": "low"
            }
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._default_config_path()
        self.flags: Dict[str, FeatureFlag] = {}
        self._lock = threading.RLock()
        self._callbacks: Dict[str, List[Callable]] = {}
        
        # Cargar configuración
        self._load_config()
        
        # Inicializar flags predefinidos si no existen
        self._initialize_default_flags()
    
    def _default_config_path(self) -> str:
        """Obtiene la ruta por defecto para la configuración"""
        # Compatibilidad con Termux
        if "PREFIX" in os.environ:
            # Termux environment
            base_path = Path(os.environ["HOME"]) / ".claw_lite"
        else:
            base_path = Path.home() / ".claw_lite"
        
        base_path.mkdir(parents=True, exist_ok=True)
        return str(base_path / "feature_flags.json")
    
    def _initialize_default_flags(self):
        """Inicializa los flags predefinidos si no existen"""
        for name, config in self.CURRENT_FEATURE_FLAGS.items():
            if name not in self.flags:
                self.flags[name] = FeatureFlag(
                    name=name,
                    enabled=config["enabled"],
                    description=config["description"],
                    rollout_percentage=config["rollout_percentage"],
                    metadata=config["metadata"]
                )
    
    def _load_config(self):
        """Carga la configuración desde el archivo"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    for name, flag_data in data.get("flags", {}).items():
                        self.flags[name] = FeatureFlag.from_dict(flag_data)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Error loading feature flags config: {e}")
            self.flags = {}
    
    def _save_config(self):
        """Guarda la configuración en el archivo"""
        try:
            data = {
                "version": "1.0",
                "updated_at": datetime.now().isoformat(),
                "flags": {name: flag.to_dict() for name, flag in self.flags.items()}
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            print(f"Error saving feature flags config: {e}")
    
    def is_enabled(
        self, 
        feature_name: str, 
        user_id: Optional[str] = None,
        default: bool = False
    ) -> bool:
        """
        Verifica si un feature está habilitado
        
        Args:
            feature_name: Nombre del feature
            user_id: ID del usuario (opcional)
            default: Valor por defecto si el feature no existe
        
        Returns:
            True si el feature está habilitado, False en caso contrario
        """
        with self._lock:
            if feature_name not in self.flags:
                return default
            
            return self.flags[feature_name].is_enabled_for_user(user_id)
    
    def enable(
        self, 
        feature_name: str, 
        user_ids: Optional[List[str]] = None,
        rollout_percentage: float = 100.0
    ) -> bool:
        """
        Habilita un feature flag
        
        Args:
            feature_name: Nombre del feature
            user_ids: Lista de user_ids específicos (opcional)
            rollout_percentage: Porcentaje de rollout (0-100)
        
        Returns:
            True si se habilitó correctamente
        """
        with self._lock:
            if feature_name not in self.flags:
                # Crear nuevo flag
                self.flags[feature_name] = FeatureFlag(
                    name=feature_name,
                    enabled=True,
                    user_ids=user_ids,
                    rollout_percentage=rollout_percentage
                )
            else:
                flag = self.flags[feature_name]
                flag.enabled = True
                flag.user_ids = user_ids or []
                flag.rollout_percentage = rollout_percentage
                flag.updated_at = datetime.now()
            
            self._save_config()
            self._trigger_callbacks(feature_name, True)
            return True
    
    def disable(self, feature_name: str) -> bool:
        """
        Deshabilita un feature flag
        
        Args:
            feature_name: Nombre del feature
        
        Returns:
            True si se deshabilitó correctamente
        """
        with self._lock:
            if feature_name not in self.flags:
                return False
            
            flag = self.flags[feature_name]
            flag.enabled = False
            flag.updated_at = datetime.now()
            
            self._save_config()
            self._trigger_callbacks(feature_name, False)
            return True
    
    def get_flag(self, feature_name: str) -> Optional[FeatureFlag]:
        """Obtiene un feature flag por nombre"""
        return self.flags.get(feature_name)
    
    def get_all_flags(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene todos los feature flags"""
        return {name: flag.to_dict() for name, flag in self.flags.items()}
    
    def get_enabled_flags(self, user_id: Optional[str] = None) -> List[str]:
        """Obtiene lista de flags habilitados para un usuario"""
        enabled = []
        for name, flag in self.flags.items():
            if flag.is_enabled_for_user(user_id):
                enabled.append(name)
        return enabled
    
    def register_callback(self, feature_name: str, callback: Callable[[str, bool], None]):
        """
        Registra un callback para cuando un feature cambie
        
        Args:
            feature_name: Nombre del feature
            callback: Función a llamar con (feature_name, enabled)
        """
        if feature_name not in self._callbacks:
            self._callbacks[feature_name] = []
        self._callbacks[feature_name].append(callback)
    
    def _trigger_callbacks(self, feature_name: str, enabled: bool):
        """Ejecuta los callbacks registrados para un feature"""
        if feature_name in self._callbacks:
            for callback in self._callbacks[feature_name]:
                try:
                    callback(feature_name, enabled)
                except Exception as e:
                    print(f"Error in feature flag callback: {e}")
    
    def reset_to_defaults(self):
        """Resetea todos los flags a los valores por defecto"""
        with self._lock:
            self.flags = {}
            self._initialize_default_flags()
            self._save_config()
    
    def export_config(self, filepath: str):
        """Exporta la configuración actual a un archivo"""
        data = {
            "version": "1.0",
            "exported_at": datetime.now().isoformat(),
            "flags": {name: flag.to_dict() for name, flag in self.flags.items()}
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def import_config(self, filepath: str):
        """Importa configuración desde un archivo"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        with self._lock:
            for name, flag_data in data.get("flags", {}).items():
                self.flags[name] = FeatureFlag.from_dict(flag_data)
            self._save_config()


# Instancia global por defecto
_default_manager: Optional[FeatureFlagsManager] = None


def get_feature_flags_manager(config_path: Optional[str] = None) -> FeatureFlagsManager:
    """Obtiene la instancia global del gestor de feature flags"""
    global _default_manager
    
    if _default_manager is None:
        _default_manager = FeatureFlagsManager(config_path)
    
    return _default_manager


def is_feature_enabled(
    feature_name: str, 
    user_id: Optional[str] = None,
    default: bool = False
) -> bool:
    """Función helper para verificar si un feature está habilitado"""
    manager = get_feature_flags_manager()
    return manager.is_enabled(feature_name, user_id, default)


# Decorador para funciones condicionales
def feature_required(feature_name: str):
    """
    Decorador para hacer que una función requiera un feature flag habilitado
    
    Usage:
        @feature_required("self_refining_reasoning")
        def enhanced_synthesizer():
            # Código del feature
            pass
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            if not is_feature_enabled(feature_name):
                # Si el feature no está habilitado, ejecutar versión fallback
                # o lanzar excepción dependiendo del caso
                fallback = kwargs.pop('fallback', None)
                if fallback:
                    return fallback(*args, **kwargs)
                else:
                    raise RuntimeError(f"Feature '{feature_name}' is not enabled")
            return func(*args, **kwargs)
        return wrapper
    return decorator


if __name__ == "__main__":
    # Ejemplo de uso
    manager = get_feature_flags_manager()
    
    print("=== Claw-Litle 1.0 - Feature Flags ===\n")
    print("Feature flags disponibles:")
    for name, config in manager.get_all_flags().items():
        status = "✅" if config["enabled"] else "❌"
        print(f"  {status} {name}: {config['description']}")
    
    print("\nEjemplo: Habilitar self_refining_reasoning para testing")
    manager.enable("self_refining_reasoning", user_ids=["test_user"], rollout_percentage=50.0)
    
    print(f"\n¿self_refining_reasoning habilitado? {manager.is_enabled('self_refining_reasoning')}")
    print(f"¿self_refining_reasoning para 'test_user'? {manager.is_enabled('self_refining_reasoning', 'test_user')}")