#!/usr/bin/env python3
"""
License Manager - Sistema de Licencias para Claw-Litle.
Gestiona versiones Free, Pro y Enterprise con verificación offline/online.
"""

import os
import sys
import json
import hashlib
import base64
import hmac
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List
from enum import Enum


class LicenseTier(Enum):
    """Niveles de licencia."""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class LicenseStatus(Enum):
    """Estado de la licencia."""
    VALID = "valid"
    EXPIRED = "expired"
    INVALID = "invalid"
    TRIAL = "trial"
    NOT_ACTIVATED = "not_activated"


# Características por nivel
FEATURES_BY_TIER = {
    LicenseTier.FREE: {
        "max_agents": 2,
        "max_memory_mb": 350,
        "semantic_engine": True,
        "vision_agency": True,
        "code_generation": True,
        "background_tasks": False,
        "priority_support": False,
        "cloud_sync": False,
        "advanced_analytics": False,
        "custom_integrations": False,
        "api_access": False,
        "max_daily_queries": 100,
        "thermal_throttling": True,
        "battery_saver": True,
    },
    LicenseTier.PRO: {
        "max_agents": 6,
        "max_memory_mb": 1000,
        "semantic_engine": True,
        "vision_agency": True,
        "code_generation": True,
        "background_tasks": True,
        "priority_support": True,
        "cloud_sync": True,
        "advanced_analytics": True,
        "custom_integrations": False,
        "api_access": True,
        "max_daily_queries": 10000,
        "thermal_throttling": True,
        "battery_saver": True,
    },
    LicenseTier.ENTERPRISE: {
        "max_agents": -1,  # Ilimitado
        "max_memory_mb": -1,  # Ilimitado
        "semantic_engine": True,
        "vision_agency": True,
        "code_generation": True,
        "background_tasks": True,
        "priority_support": True,
        "cloud_sync": True,
        "advanced_analytics": True,
        "custom_integrations": True,
        "api_access": True,
        "max_daily_queries": -1,  # Ilimitado
        "thermal_throttling": True,
        "battery_saver": True,
    },
}


class LicenseManager:
    """Gestor de licencias con verificación offline/online."""
    
    # Clave pública para verificación (en producción, usar criptografía asimétrica real)
    SECRET_KEY = "claw_lite_license_key_2024"
    
    def __init__(self, license_file: str = None):
        if license_file is None:
            license_file = str(Path.home() / ".clawlite" / "license.json")
        
        self.license_file = Path(license_file)
        self.license_data = None
        self._load_license()
    
    def _load_license(self):
        """Carga la licencia desde archivo."""
        if self.license_file.exists():
            try:
                with open(self.license_file, 'r') as f:
                    encrypted_data = json.load(f)
                    if self._verify_signature(encrypted_data):
                        self.license_data = encrypted_data["data"]
            except Exception as e:
                print(f"⚠️  Error cargando licencia: {e}")
                self.license_data = None
    
    def _generate_signature(self, data: Dict) -> str:
        """Genera firma HMAC para la licencia."""
        data_str = json.dumps(data, sort_keys=True)
        signature = hmac.new(
            self.SECRET_KEY.encode(),
            data_str.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _verify_signature(self, encrypted_data: Dict) -> bool:
        """Verifica la firma de la licencia."""
        expected_sig = encrypted_data.get("signature", "")
        actual_sig = self._generate_signature(encrypted_data["data"])
        return hmac.compare_digest(expected_sig, actual_sig)
    
    def activate_license(self, license_key: str, user_email: str = None) -> Dict:
        """Activa una licencia con clave."""
        # Decodificar clave (formato: base64(json_data).signature)
        try:
            parts = license_key.split('.')
            if len(parts) != 2:
                return {
                    "success": False,
                    "error": "Formato de licencia inválido"
                }
            
            # Decodificar datos
            data_b64, signature = parts
            data_json = base64.b64decode(data_b64).decode()
            data = json.loads(data_json)
            
            # Verificar firma
            expected_sig = self._generate_signature(data)
            if not hmac.compare_digest(signature, expected_sig):
                return {
                    "success": False,
                    "error": "Licencia inválida o tampered"
                }
            
            # Verificar expiración
            if "expires_at" in data:
                expires = datetime.fromisoformat(data["expires_at"])
                if datetime.now() > expires:
                    return {
                        "success": False,
                        "error": "Licencia expirada"
                    }
            
            # Guardar licencia
            self.license_data = data
            self._save_license()
            
            return {
                "success": True,
                "tier": data.get("tier", "free"),
                "expires_at": data.get("expires_at", "never"),
                "features": self.get_features()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error activando licencia: {str(e)}"
            }
    
    def _save_license(self):
        """Guarda la licencia en archivo."""
        if self.license_data is None:
            return
        
        self.license_file.parent.mkdir(parents=True, exist_ok=True)
        
        encrypted_data = {
            "data": self.license_data,
            "signature": self._generate_signature(self.license_data),
            "saved_at": datetime.now().isoformat()
        }
        
        with open(self.license_file, 'w') as f:
            json.dump(encrypted_data, f, indent=2)
    
    def get_license_status(self) -> LicenseStatus:
        """Obtiene el estado de la licencia."""
        if self.license_data is None:
            return LicenseStatus.NOT_ACTIVATED
        
        # Verificar expiración
        if "expires_at" in self.license_data:
            expires = datetime.fromisoformat(self.license_data["expires_at"])
            if datetime.now() > expires:
                return LicenseStatus.EXPIRED
        
        # Verificar si es trial
        if self.license_data.get("is_trial", False):
            return LicenseStatus.TRIAL
        
        return LicenseStatus.VALID
    
    def get_tier(self) -> LicenseTier:
        """Obtiene el nivel de licencia actual."""
        if self.license_data is None:
            return LicenseTier.FREE
        
        tier_str = self.license_data.get("tier", "free").lower()
        try:
            return LicenseTier(tier_str)
        except ValueError:
            return LicenseTier.FREE
    
    def get_features(self) -> Dict:
        """Obtiene características disponibles según licencia."""
        tier = self.get_tier()
        return FEATURES_BY_TIER.get(tier, FEATURES_BY_TIER[LicenseTier.FREE])
    
    def check_feature(self, feature: str) -> bool:
        """Verifica si una característica está disponible."""
        features = self.get_features()
        return features.get(feature, False)
    
    def get_usage_stats(self) -> Dict:
        """Obtiene estadísticas de uso."""
        usage_file = Path.home() / ".clawlite" / "usage.json"
        
        if usage_file.exists():
            with open(usage_file, 'r') as f:
                return json.load(f)
        
        return {
            "daily_queries": 0,
            "total_queries": 0,
            "last_reset": datetime.now().date().isoformat()
        }
    
    def record_query(self):
        """Registra una query para límites de uso."""
        usage_file = Path.home() / ".clawlite" / "usage.json"
        stats = self.get_usage_stats()
        
        # Resetear si es nuevo día
        today = datetime.now().date().isoformat()
        if stats.get("last_reset") != today:
            stats["daily_queries"] = 0
            stats["last_reset"] = today
        
        stats["daily_queries"] += 1
        stats["total_queries"] += 1
        
        # Guardar
        usage_file.parent.mkdir(parents=True, exist_ok=True)
        with open(usage_file, 'w') as f:
            json.dump(stats, f, indent=2)
    
    def can_use(self, feature: str) -> bool:
        """Verifica si se puede usar una característica (incluyendo límites)."""
        # Verificar si la característica está disponible
        if not self.check_feature(feature):
            return False
        
        # Verificar límites de uso para queries
        if feature == "query":
            features = self.get_features()
            max_queries = features.get("max_daily_queries", 100)
            if max_queries > 0:  # -1 significa ilimitado
                stats = self.get_usage_stats()
                if stats["daily_queries"] >= max_queries:
                    return False
        
        return True
    
    def generate_license_key(self, tier: LicenseTier, days: int = 365, 
                            user_email: str = None, is_trial: bool = False) -> str:
        """Genera una clave de licencia (solo para testing/admin)."""
        expires = datetime.now() + timedelta(days=days)
        
        data = {
            "tier": tier.value,
            "expires_at": expires.isoformat(),
            "user_email": user_email,
            "is_trial": is_trial,
            "issued_at": datetime.now().isoformat()
        }
        
        # Codificar
        data_json = json.dumps(data, sort_keys=True)
        data_b64 = base64.b64encode(data_json.encode()).decode()
        signature = self._generate_signature(data)
        
        return f"{data_b64}.{signature}"
    
    def deactivate_license(self) -> bool:
        """Desactiva la licencia actual."""
        if self.license_file.exists():
            self.license_file.unlink()
            self.license_data = None
            return True
        return False
    
    def get_license_info(self) -> Dict:
        """Obtiene información completa de la licencia."""
        return {
            "status": self.get_license_status().value,
            "tier": self.get_tier().value,
            "features": self.get_features(),
            "usage": self.get_usage_stats(),
            "license_data": self.license_data
        }


# Instancia global
license_manager = LicenseManager()