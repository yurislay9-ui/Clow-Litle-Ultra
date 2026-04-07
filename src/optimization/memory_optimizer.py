#!/usr/bin/env python3
"""
Memory Optimizer - Optimizador de Memoria para dispositivos móviles.
Implementa lazy loading, garbage collection estratégico y límites de RAM.
"""

import gc
import time
import psutil
import asyncio
from typing import Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import OrderedDict
import weakref


@dataclass
class MemoryStats:
    """Estadísticas de uso de memoria."""
    current_mb: float
    peak_mb: float
    available_mb: float
    percent_used: float
    process_mb: float


class LRUCache:
    """Cache LRU con límite de memoria."""
    
    def __init__(self, max_size_mb: int = 50):
        self.cache: OrderedDict = OrderedDict()
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.current_size = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Obtiene un elemento del cache."""
        if key in self.cache:
            # Mover al final (más reciente)
            self.cache.move_to_end(key)
            return self.cache[key][0]
        return None
    
    def put(self, key: str, value: Any, size_bytes: int):
        """Agrega un elemento al cache."""
        # Si ya existe, removerlo primero
        if key in self.cache:
            old_value, old_size = self.cache.pop(key)
            self.current_size -= old_size
        
        # Si excede el límite, eliminar elementos antiguos
        while self.current_size + size_bytes > self.max_size_bytes and self.cache:
            _, (_, old_size) = self.cache.popitem(last=False)
            self.current_size -= old_size
        
        self.cache[key] = (value, size_bytes)
        self.current_size += size_bytes
    
    def clear(self):
        """Limpia el cache completamente."""
        self.cache.clear()
        self.current_size = 0
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas del cache."""
        return {
            "items": len(self.cache),
            "current_size_mb": self.current_size / (1024 * 1024),
            "max_size_mb": self.max_size_bytes / (1024 * 1024),
            "usage_percent": (self.current_size / self.max_size_bytes * 100) if self.max_size_bytes > 0 else 0
        }


class MemoryOptimizer:
    """Optimizador de memoria con lazy loading y gestión automática."""
    
    # Umbrales de memoria (MB)
    CRITICAL_THRESHOLD = 50  # Memoria libre crítica
    WARNING_THRESHOLD = 100  # Memoria libre de advertencia
    TARGET_THRESHOLD = 200   # Memoria libre objetivo
    
    def __init__(self, max_memory_mb: int = 350):
        self.max_memory_mb = max_memory_mb
        self.lru_cache = LRUCache(max_size_mb=50)
        self._loaded_modules: Dict[str, weakref.ref] = {}
        self._memory_history = []
        self._peak_memory = 0
        self._last_gc = time.time()
        self._gc_interval = 300  # 5 minutos
    
    def get_memory_stats(self) -> MemoryStats:
        """Obtiene estadísticas de memoria actuales."""
        process = psutil.Process()
        mem_info = psutil.virtual_memory()
        
        current = process.memory_info().rss / (1024 * 1024)
        self._peak_memory = max(self._peak_memory, current)
        
        return MemoryStats(
            current_mb=current,
            peak_mb=self._peak_memory,
            available_mb=mem_info.available / (1024 * 1024),
            percent_used=mem_info.percent,
            process_mb=current
        )
    
    def should_load(self, module_name: str) -> bool:
        """Determina si se debe cargar un módulo pesado."""
        stats = self.get_memory_stats()
        
        # Si hay poca memoria disponible, no cargar
        if stats.available_mb < self.CRITICAL_THRESHOLD:
            return False
        
        # Si el módulo ya está cargado, no recargar
        if module_name in self._loaded_modules:
            ref = self._loaded_modules[module_name]
            if ref() is not None:
                return False
        
        return True
    
    def register_module(self, module_name: str, module_obj: Any):
        """Registra un módulo cargado."""
        self._loaded_modules[module_name] = weakref.ref(module_obj)
    
    def unload_module(self, module_name: str):
        """Descarga un módulo de la memoria."""
        if module_name in self._loaded_modules:
            del self._loaded_modules[module_name]
            gc.collect()
    
    def cache_result(self, key: str, result: Any, estimate_size_kb: int = 10):
        """Almacena un resultado en el cache LRU."""
        size_bytes = estimate_size_kb * 1024
        self.lru_cache.put(key, result, size_bytes)
    
    def get_cached(self, key: str) -> Optional[Any]:
        """Obtiene un resultado del cache."""
        return self.lru_cache.get(key)
    
    def force_garbage_collection(self):
        """Fuerza garbage collection inmediato."""
        collected = gc.collect()
        self._last_gc = time.time()
        return collected
    
    def auto_gc(self):
        """Ejecuta GC automático si ha pasado suficiente tiempo."""
        if time.time() - self._last_gc > self._gc_interval:
            return self.force_garbage_collection()
        return 0
    
    def check_memory_pressure(self) -> str:
        """Verifica la presión de memoria y retorna el estado."""
        stats = self.get_memory_stats()
        
        if stats.available_mb < self.CRITICAL_THRESHOLD:
            return "CRITICAL"
        elif stats.available_mb < self.WARNING_THRESHOLD:
            return "WARNING"
        elif stats.available_mb < self.TARGET_THRESHOLD:
            return "MODERATE"
        else:
            return "HEALTHY"
    
    def optimize_for_mobile(self):
        """Aplica optimizaciones específicas para móvil."""
        # 1. Forzar GC si hay presión
        pressure = self.check_memory_pressure()
        if pressure in ["CRITICAL", "WARNING"]:
            self.force_garbage_collection()
        
        # 2. Limpiar cache LRU parcialmente
        if pressure == "CRITICAL":
            self.lru_cache.clear()
        elif pressure == "WARNING":
            # Eliminar 50% del cache
            while len(self.lru_cache.cache) > 0 and self.lru_cache.current_size > self.lru_cache.max_size_bytes * 0.5:
                self.lru_cache.cache.popitem(last=False)
        
        # 3. Descargar módulos no críticos
        if pressure == "CRITICAL":
            non_critical = ["semantic_searcher", "deep_scraper", "synthesizer"]
            for module in non_critical:
                self.unload_module(module)
    
    def record_memory_usage(self, operation: str):
        """Registra el uso de memoria para análisis."""
        stats = self.get_memory_stats()
        self._memory_history.append({
            "timestamp": time.time(),
            "operation": operation,
            "memory_mb": stats.current_mb,
            "available_mb": stats.available_mb,
            "pressure": self.check_memory_pressure()
        })
        
        # Mantener solo últimas 1000 entradas
        if len(self._memory_history) > 1000:
            self._memory_history = self._memory_history[-1000:]
    
    def get_memory_report(self) -> Dict:
        """Genera un reporte de uso de memoria."""
        stats = self.get_memory_stats()
        
        return {
            "current_memory_mb": stats.current_mb,
            "peak_memory_mb": stats.peak_mb,
            "available_memory_mb": stats.available_mb,
            "memory_pressure": self.check_memory_pressure(),
            "cache_stats": self.lru_cache.get_stats(),
            "loaded_modules": len(self._loaded_modules),
            "last_gc": self._last_gc,
            "history_entries": len(self._memory_history)
        }


class LazyLoader:
    """Cargador perezoso de módulos pesados."""
    
    def __init__(self, optimizer: MemoryOptimizer):
        self.optimizer = optimizer
        self._module_cache: Dict[str, Any] = {}
    
    def load_if_needed(self, module_name: str, import_func: Callable) -> Optional[Any]:
        """Carga un módulo solo si es necesario y hay memoria."""
        # Verificar si ya está en cache
        if module_name in self._module_cache:
            return self._module_cache[module_name]
        
        # Verificar si hay memoria suficiente
        if not self.optimizer.should_load(module_name):
            return None
        
        # Intentar cargar
        try:
            module = import_func()
            self._module_cache[module_name] = module
            self.optimizer.register_module(module_name, module)
            return module
        except Exception as e:
            print(f"Error cargando {module_name}: {e}")
            return None
    
    def unload(self, module_name: str):
        """Descarga un módulo del cache."""
        if module_name in self._module_cache:
            del self._module_cache[module_name]
            self.optimizer.unload_module(module_name)
    
    def unload_all(self):
        """Descarga todos los módulos."""
        self._module_cache.clear()
        gc.collect()