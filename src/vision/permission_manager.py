"""
Claw-Litle 1.0
permission_manager.py - Gestor de Permisos para Vision Agency

Niveles de permisos:
- Nivel 0: Sin permisos (solo lectura básica)
- Nivel 1: Permisos básicos (captura de pantalla, UI parsing)
- Nivel 2: Permisos completos (acción, ejecución, acceso a datos)
"""

import logging
from enum import Enum
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class PermissionLevel(Enum):
    """Niveles de permisos para Vision Agency."""
    LEVEL_0 = "level_0"  # Sin permisos
    LEVEL_1 = "level_1"  # Básicos
    LEVEL_2 = "level_2"  # Completos


class PermissionType(Enum):
    """Tipos de permisos específicos."""
    SCREEN_CAPTURE = "screen_capture"
    UI_PARSING = "ui_parsing"
    ACTION_EXECUTION = "action_execution"
    DATA_EXTRACTION = "data_extraction"
    PII_DETECTION = "pii_detection"
    FILE_ACCESS = "file_access"
    CLIPBOARD_ACCESS = "clipboard_access"


@dataclass
class PermissionRequest:
    """Solicitud de permiso."""
    permission_type: PermissionType
    required_level: PermissionLevel
    description: str
    resource: Optional[str] = None


@dataclass
class PermissionGrant:
    """Concesión de permiso."""
    permission_type: PermissionType
    granted: bool
    level: PermissionLevel
    restrictions: List[str] = field(default_factory=list)
    reason: Optional[str] = None


class PermissionManager:
    """
    Gestor de Permisos para Vision Agency.
    
    Implementa 3 niveles de permisos según especificaciones de Claw-Lite:
    - Nivel 0: Sin permisos (solo operaciones locales seguras)
    - Nivel 1: Permisos básicos (captura, parsing UI)
    - Nivel 2: Permisos completos (acción, ejecución)
    """
    
    def __init__(self, default_level: PermissionLevel = PermissionLevel.LEVEL_0):
        self._current_level = default_level
        self._granted_permissions: Set[PermissionType] = set()
        self._denied_permissions: Set[PermissionType] = set()
        self._permission_history: List[Dict] = []
        
        # Mapeo de permisos a niveles requeridos
        self._permission_level_map: Dict[PermissionType, PermissionLevel] = {
            PermissionType.SCREEN_CAPTURE: PermissionLevel.LEVEL_1,
            PermissionType.UI_PARSING: PermissionLevel.LEVEL_1,
            PermissionType.PII_DETECTION: PermissionLevel.LEVEL_1,
            PermissionType.DATA_EXTRACTION: PermissionLevel.LEVEL_1,
            PermissionType.ACTION_EXECUTION: PermissionLevel.LEVEL_2,
            PermissionType.FILE_ACCESS: PermissionLevel.LEVEL_2,
            PermissionType.CLIPBOARD_ACCESS: PermissionLevel.LEVEL_2,
        }
        
        logger.info(f"PermissionManager inicializado - Nivel: {default_level.value}")
    
    def set_level(self, level: PermissionLevel) -> bool:
        """
        Establece el nivel de permisos actual.
        
        Args:
            level: Nuevo nivel de permisos
            
        Returns:
            True si se pudo establecer, False si hay restricciones
        """
        # Verificar si podemos bajar de nivel (siempre permitido)
        if level.value < self._current_level.value:
            self._current_level = level
            self._clear_permissions_for_level(level)
            logger.info(f"Nivel de permisos reducido a: {level.value}")
            return True
        
        # Verificar si podemos subir de nivel (requiere validación)
        if level.value > self._current_level.value:
            if self._validate_level_upgrade(level):
                self._current_level = level
                logger.info(f"Nivel de permisos elevado a: {level.value}")
                return True
            else:
                logger.warning(f"No se pudo elevar a nivel {level.value}")
                return False
        
        return True  # Mismo nivel
    
    def _validate_level_upgrade(self, level: PermissionLevel) -> bool:
        """Valida si se puede elevar el nivel de permisos."""
        # En Termux, verificar permisos de accesibilidad
        if level == PermissionLevel.LEVEL_2:
            # Simular verificación de permisos de accesibilidad
            logger.info("Solicitando permisos de accesibilidad para Nivel 2")
            # En producción: verificar configuración de accesibilidad de Android
            return True
        return True
    
    def _clear_permissions_for_level(self, level: PermissionLevel):
        """Limpia permisos que requieren nivel superior."""
        to_remove = set()
        for perm_type, required_level in self._permission_level_map.items():
            if required_level.value > level.value:
                if perm_type in self._granted_permissions:
                    to_remove.add(perm_type)
        
        self._granted_permissions -= to_remove
        logger.info(f"Permisos limpiados: {[p.value for p in to_remove]}")
    
    def request_permission(self, request: PermissionRequest) -> PermissionGrant:
        """
        Solicita un permiso específico.
        
        Args:
            request: Solicitud de permiso
            
        Returns:
            Concesión de permiso con el resultado
        """
        # Verificar si ya está concedido
        if request.permission_type in self._granted_permissions:
            return PermissionGrant(
                permission_type=request.permission_type,
                granted=True,
                level=self._current_level
            )
        
        # Verificar si está denegado permanentemente
        if request.permission_type in self._denied_permissions:
            return PermissionGrant(
                permission_type=request.permission_type,
                granted=False,
                level=self._current_level,
                reason="Permiso denegado permanentemente"
            )
        
        # Verificar nivel requerido
        required_level = self._permission_level_map.get(request.permission_type)
        if required_level and required_level.value > self._current_level.value:
            return PermissionGrant(
                permission_type=request.permission_type,
                granted=False,
                level=self._current_level,
                reason=f"Se requiere nivel {required_level.value}, actual: {self._current_level.value}"
            )
        
        # Conceder permiso (en producción: solicitar al usuario)
        self._granted_permissions.add(request.permission_type)
        self._permission_history.append({
            "action": "grant",
            "permission": request.permission_type.value,
            "level": self._current_level.value,
            "timestamp": self._get_timestamp()
        })
        
        logger.info(f"Permiso concedido: {request.permission_type.value}")
        return PermissionGrant(
            permission_type=request.permission_type,
            granted=True,
            level=self._current_level
        )
    
    def has_permission(self, permission_type: PermissionType) -> bool:
        """Verifica si tiene un permiso específico."""
        return permission_type in self._granted_permissions
    
    def get_current_level(self) -> PermissionLevel:
        """Obtiene el nivel de permisos actual."""
        return self._current_level
    
    def get_granted_permissions(self) -> Set[PermissionType]:
        """Obtiene conjunto de permisos concedidos."""
        return self._granted_permissions.copy()
    
    def revoke_permission(self, permission_type: PermissionType) -> bool:
        """Revoca un permiso específico."""
        if permission_type in self._granted_permissions:
            self._granted_permissions.remove(permission_type)
            self._permission_history.append({
                "action": "revoke",
                "permission": permission_type.value,
                "timestamp": self._get_timestamp()
            })
            logger.info(f"Permiso revocado: {permission_type.value}")
            return True
        return False
    
    def get_permission_status(self) -> Dict:
        """Obtiene estado completo de permisos."""
        status = {
            "current_level": self._current_level.value,
            "granted_permissions": [p.value for p in self._granted_permissions],
            "denied_permissions": [p.value for p in self._denied_permissions],
            "available_permissions": []
        }
        
        for perm_type, required_level in self._permission_level_map.items():
            status["available_permissions"].append({
                "type": perm_type.value,
                "required_level": required_level.value,
                "granted": perm_type in self._granted_permissions,
                "can_grant": required_level.value <= self._current_level.value
            })
        
        return status
    
    def _get_timestamp(self) -> str:
        """Obtiene timestamp actual."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def reset(self):
        """Resetea todos los permisos a nivel 0."""
        self._current_level = PermissionLevel.LEVEL_0
        self._granted_permissions.clear()
        self._denied_permissions.clear()
        logger.info("Permisos reseteados a nivel 0")


# Función helper para uso rápido
def check_permission(permission_type: PermissionType) -> bool:
    """Verifica un permiso con el gestor global."""
    # En producción: usar instancia global
    manager = PermissionManager()
    return manager.has_permission(permission_type)


if __name__ == "__main__":
    # Test rápido
    manager = PermissionManager()
    
    print(f"Nivel actual: {manager.get_current_level().value}")
    
    # Solicitar permiso de captura de pantalla
    request = PermissionRequest(
        permission_type=PermissionType.SCREEN_CAPTURE,
        required_level=PermissionLevel.LEVEL_1,
        description="Necesito capturar pantalla para análisis UI"
    )
    
    grant = manager.request_permission(request)
    print(f"Permiso SCREEN_CAPTURE: {grant.granted}")
    
    # Elevar a nivel 2
    manager.set_level(PermissionLevel.LEVEL_2)
    print(f"Nivel actual: {manager.get_current_level().value}")
    
    # Solicitar permiso de ejecución de acciones
    request2 = PermissionRequest(
        permission_type=PermissionType.ACTION_EXECUTION,
        required_level=PermissionLevel.LEVEL_2,
        description="Necesito ejecutar acciones en la UI"
    )
    
    grant2 = manager.request_permission(request2)
    print(f"Permiso ACTION_EXECUTION: {grant2.granted}")
    
    print(f"\nEstado de permisos: {manager.get_permission_status()}")