#!/usr/bin/env python3
"""
Battery Saver Mode - Modo de Ahorro de Energía.
Optimiza el consumo de recursos para extender la batería en dispositivos móviles.
"""

import time
import asyncio
from typing import Dict, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class PowerMode(Enum):
    """Modos de energía del sistema."""
    PERFORMANCE = "performance"  # Máximo rendimiento, mayor consumo
    BALANCED = "balanced"        # Equilibrio rendimiento/consumo
    POWER_SAVE = "power_save"    # Máximo ahorro, mínimo consumo
    ULTRA_SAVE = "ultra_save"    # Solo funciones esenciales


@dataclass
class PowerProfile:
    """Perfil de configuración de energía."""
    mode: PowerMode
    max_cpu_percent: int
    max_memory_mb: int
    agent_timeout: float
    enable_caching: bool
    cache_ttl: int  # segundos
    batch_operations: bool
    background_tasks: bool
    network_requests: bool
    semantic_engine: bool


class BatterySaver:
    """Gestor de ahorro de energía con control adaptativo."""
    
    # Perfiles predefinidos
    PROFILES: Dict[PowerMode, PowerProfile] = {
        PowerMode.PERFORMANCE: PowerProfile(
            mode=PowerMode.PERFORMANCE,
            max_cpu_percent=100,
            max_memory_mb=1000,
            agent_timeout=30.0,
            enable_caching=True,
            cache_ttl=300,  # 5 minutos
            batch_operations=True,
            background_tasks=True,
            network_requests=True,
            semantic_engine=True
        ),
        PowerMode.BALANCED: PowerProfile(
            mode=PowerMode.BALANCED,
            max_cpu_percent=70,
            max_memory_mb=500,
            agent_timeout=20.0,
            enable_caching=True,
            cache_ttl=600,  # 10 minutos
            batch_operations=True,
            background_tasks=True,
            network_requests=True,
            semantic_engine=True
        ),
        PowerMode.POWER_SAVE: PowerProfile(
            mode=PowerMode.POWER_SAVE,
            max_cpu_percent=40,
            max_memory_mb=350,
            agent_timeout=15.0,
            enable_caching=True,
            cache_ttl=1800,  # 30 minutos
            batch_operations=True,
            background_tasks=False,
            network_requests=True,
            semantic_engine=False  # Desactivar ONNX para ahorrar
        ),
        PowerMode.ULTRA_SAVE: PowerProfile(
            mode=PowerMode.ULTRA_SAVE,
            max_cpu_percent=20,
            max_memory_mb=200,
            agent_timeout=10.0,
            enable_caching=True,
            cache_ttl=3600,  # 1 hora
            batch_operations=False,
            background_tasks=False,
            network_requests=False,  # Solo operaciones locales
            semantic_engine=False
        )
    }
    
    def __init__(self):
        self.current_mode = PowerMode.BALANCED
        self.battery_level = 100  # Porcentaje
        self.is_charging = False
        self.profile = self.PROFILES[self.current_mode]
        self._last_adjustment = time.time()
        self._adjustment_interval = 60  # Segundos entre ajustes
    
    def set_mode(self, mode: PowerMode):
        """Establece el modo de energía."""
        self.current_mode = mode
        self.profile = self.PROFILES[mode]
        print(f"🔋 Modo de energía: {mode.value}")
    
    def update_battery_status(self, level: int, charging: bool = False):
        """Actualiza el estado de la batería."""
        self.battery_level = level
        self.is_charging = charging
        
        # Ajuste automático basado en batería
        if charging:
            self.set_mode(PowerMode.PERFORMANCE)
        elif level < 10:
            self.set_mode(PowerMode.ULTRA_SAVE)
        elif level < 25:
            self.set_mode(PowerMode.POWER_SAVE)
        elif level < 50:
            self.set_mode(PowerMode.BALANCED)
        else:
            self.set_mode(PowerMode.PERFORMANCE)
    
    def should_execute(self, operation: str) -> bool:
        """Determina si una operación debe ejecutarse según el modo."""
        if operation == "background_task" and not self.profile.background_tasks:
            return False
        if operation == "network_request" and not self.profile.network_requests:
            return False
        if operation == "semantic_search" and not self.profile.semantic_engine:
            return False
        return True
    
    def get_timeout(self) -> float:
        """Obtiene el timeout para operaciones."""
        return self.profile.agent_timeout
    
    def get_memory_limit(self) -> int:
        """Obtiene el límite de memoria en MB."""
        return self.profile.max_memory_mb
    
    def get_cache_config(self) -> tuple:
        """Obtiene configuración de caché (enabled, ttl)."""
        return self.profile.enable_caching, self.profile.cache_ttl
    
    async def execute_with_power_control(self, operation: Callable, *args, **kwargs):
        """Ejecuta una operación con control de energía."""
        if not self.should_execute(operation.__name__):
            raise PermissionError(f"Operación {operation.__name__} no permitida en modo {self.current_mode.value}")
        
        # Limitar CPU si es necesario
        if self.profile.max_cpu_percent < 100:
            # Simular throttling (en producción usar cpulimit o similar)
            await asyncio.sleep(0.01 * (1 - self.profile.max_cpu_percent/100))
        
        # Ejecutar con timeout
        try:
            if asyncio.iscoroutinefunction(operation):
                return await asyncio.wait_for(
                    operation(*args, **kwargs),
                    timeout=self.profile.agent_timeout
                )
            else:
                return operation(*args, **kwargs)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Operación excedió timeout de {self.profile.agent_timeout}s")
    
    def get_status(self) -> Dict:
        """Obtiene estado actual del battery saver."""
        return {
            "mode": self.current_mode.value,
            "battery_level": self.battery_level,
            "is_charging": self.is_charging,
            "max_cpu_percent": self.profile.max_cpu_percent,
            "max_memory_mb": self.profile.max_memory_mb,
            "caching_enabled": self.profile.enable_caching,
            "cache_ttl": self.profile.cache_ttl,
            "background_tasks": self.profile.background_tasks,
            "network_requests": self.profile.network_requests,
            "semantic_engine": self.profile.semantic_engine
        }


class AdaptivePowerManager:
    """Gestor de energía adaptativo que ajusta automáticamente según uso."""
    
    def __init__(self, battery_saver: BatterySaver):
        self.battery_saver = battery_saver
        self.usage_history = []
        self.adjustment_count = 0
    
    def record_usage(self, operation: str, duration: float, memory_used: int):
        """Registra el uso de una operación."""
        self.usage_history.append({
            "operation": operation,
            "duration": duration,
            "memory_used": memory_used,
            "timestamp": time.time()
        })
        
        # Mantener solo últimas 100 operaciones
        if len(self.usage_history) > 100:
            self.usage_history = self.usage_history[-100:]
        
        # Ajustar automáticamente cada 10 operaciones
        if len(self.usage_history) % 10 == 0:
            self._auto_adjust()
    
    def _auto_adjust(self):
        """Ajusta automáticamente el modo según patrones de uso."""
        if not self.usage_history:
            return
        
        # Calcular promedios
        avg_duration = sum(u["duration"] for u in self.usage_history) / len(self.usage_history)
        avg_memory = sum(u["memory_used"] for u in self.usage_history) / len(self.usage_history)
        
        # Ajustar según patrones
        if avg_duration > 5.0 or avg_memory > 500:
            # Uso intensivo -> reducir modo
            if self.battery_saver.current_mode != PowerMode.ULTRA_SAVE:
                self.battery_saver.set_mode(PowerMode.POWER_SAVE)
        elif avg_duration < 1.0 and avg_memory < 200:
            # Uso ligero -> aumentar modo
            if self.battery_saver.current_mode == PowerMode.ULTRA_SAVE:
                self.battery_saver.set_mode(PowerMode.POWER_SAVE)
    
    def get_recommendations(self) -> list:
        """Obtiene recomendaciones de optimización."""
        recommendations = []
        
        if not self.usage_history:
            return recommendations
        
        avg_memory = sum(u["memory_used"] for u in self.usage_history) / len(self.usage_history)
        
        if avg_memory > 300:
            recommendations.append("Considera reducir el número de agentes concurrentes")
        
        if self.battery_saver.battery_level < 30 and not self.battery_saver.is_charging:
            recommendations.append("Batería baja: activa el modo ahorro de energía")
        
        return recommendations