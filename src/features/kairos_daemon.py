"""
KAIROS Daemon Mode - Claw-Litle 1.0

Proceso daemon (servicio background) que continúa trabajando cuando el usuario
NO está interactuando. Implementa el concepto "autoDream" para consolidar
memoria, pre-calentar caché, y optimizar el sistema.
"""

import time
import threading
import json
import os
import signal
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path


class DaemonStatus(Enum):
    """Estados del daemon KAIROS"""
    STOPPED = "stopped"
    STARTING = "starting"
    IDLE = "idle"
    WORKING = "working"
    PAUSED = "paused"
    ERROR = "error"


class DaemonTaskType(Enum):
    """Tipos de tareas que puede ejecutar KAIROS"""
    MEMORY_CONSOLIDATION = "memory_consolidation"
    CACHE_WARMUP = "cache_warmup"
    TEMP_CLEANUP = "temp_cleanup"
    EMBEDDINGS_UPDATE = "embeddings_update"
    INDEX_OPTIMIZATION = "index_optimization"
    LOG_COMPRESSION = "log_compression"
    STATS_AGGREGATION = "stats_aggregation"


@dataclass
class DaemonTask:
    """Representa una tarea del daemon"""
    task_type: DaemonTaskType
    priority: int  # 1 = alta, 5 = baja
    interval_seconds: int  # Frecuencia de ejecución
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    duration_ms: float = 0.0
    success_count: int = 0
    failure_count: int = 0
    enabled: bool = True
    
    def should_run(self) -> bool:
        """Verifica si la tarea debe ejecutarse"""
        if not self.enabled:
            return False
        if self.next_run is None:
            return True
        return datetime.now() >= self.next_run
    
    def mark_completed(self, success: bool, duration_ms: float):
        """Marca la tarea como completada"""
        self.last_run = datetime.now()
        self.next_run = self.last_run + timedelta(seconds=self.interval_seconds)
        self.duration_ms = duration_ms
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1


@dataclass
class DaemonMetrics:
    """Métricas del daemon KAIROS"""
    start_time: datetime
    total_tasks_executed: int = 0
    total_tasks_failed: int = 0
    total_work_time_ms: float = 0.0
    total_idle_time_ms: float = 0.0
    last_user_interaction: Optional[datetime] = None
    battery_level: float = 100.0
    device_temp_celsius: float = 25.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa a diccionario"""
        return {
            "start_time": self.start_time.isoformat(),
            "total_tasks_executed": self.total_tasks_executed,
            "total_tasks_failed": self.total_tasks_failed,
            "total_work_time_ms": round(self.total_work_time_ms, 2),
            "total_idle_time_ms": round(self.total_idle_time_ms, 2),
            "last_user_interaction": self.last_user_interaction.isoformat() if self.last_user_interaction else None,
            "battery_level": self.battery_level,
            "device_temp_celsius": self.device_temp_celsius,
            "uptime_hours": (datetime.now() - self.start_time).total_seconds() / 3600
        }


class KairosDaemon:
    """
    Daemon KAIROS para Claw-Litle - "autoDream" mode.
    
    Trabaja en background cuando el usuario no interactúa para:
    1. Consolidar memoria (merge observaciones duplicadas, resolver contradicciones)
    2. Pre-calentar caché (queries populares recientes)
    3. Limpiar temporales (borrar archivos tmp, comprimir logs)
    4. Actualizar embeddings (regenerar vectores semánticos)
    5. Optimizar índices (rebuild índices SQLite)
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Configuración
        self.idle_threshold_seconds = self.config.get("idle_threshold_seconds", 30)
        self.min_battery_percentage = self.config.get("min_battery_percentage", 30.0)
        self.max_temp_celsius = self.config.get("max_temp_celsius", 70.0)
        self.work_interval_seconds = self.config.get("work_interval_seconds", 60)
        self.data_dir = self.config.get("data_dir", self._default_data_dir())
        
        # Estado
        self.status = DaemonStatus.STOPPED
        self.metrics = DaemonMetrics(start_time=datetime.now())
        self.tasks: Dict[str, DaemonTask] = {}
        
        # Callbacks
        self.memory_consolidation_callback: Optional[Callable] = None
        self.cache_warmup_callback: Optional[Callable] = None
        self.temp_cleanup_callback: Optional[Callable] = None
        self.embeddings_update_callback: Optional[Callable] = None
        self.index_optimization_callback: Optional[Callable] = None
        self.battery_callback: Optional[Callable] = None
        self.temperature_callback: Optional[Callable] = None
        self.idle_detector_callback: Optional[Callable] = None
        
        # Thread del daemon
        self._daemon_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.RLock()
        
        # Inicializar tareas por defecto
        self._initialize_default_tasks()
    
    def _default_data_dir(self) -> str:
        """Obtiene el directorio de datos por defecto"""
        if "PREFIX" in os.environ:
            # Termux
            base_path = Path(os.environ["HOME"]) / ".claw_lite" / "kairos"
        else:
            base_path = Path.home() / ".claw_lite" / "kairos"
        
        base_path.mkdir(parents=True, exist_ok=True)
        return str(base_path)
    
    def _initialize_default_tasks(self):
        """Inicializa las tareas por defecto"""
        default_tasks = [
            DaemonTask(
                task_type=DaemonTaskType.MEMORY_CONSOLIDATION,
                priority=1,
                interval_seconds=300,  # Cada 5 minutos
                enabled=True
            ),
            DaemonTask(
                task_type=DaemonTaskType.CACHE_WARMUP,
                priority=2,
                interval_seconds=180,  # Cada 3 minutos
                enabled=True
            ),
            DaemonTask(
                task_type=DaemonTaskType.TEMP_CLEANUP,
                priority=3,
                interval_seconds=600,  # Cada 10 minutos
                enabled=True
            ),
            DaemonTask(
                task_type=DaemonTaskType.EMBEDDINGS_UPDATE,
                priority=2,
                interval_seconds=600,  # Cada 10 minutos
                enabled=True
            ),
            DaemonTask(
                task_type=DaemonTaskType.INDEX_OPTIMIZATION,
                priority=4,
                interval_seconds=900,  # Cada 15 minutos
                enabled=True
            ),
            DaemonTask(
                task_type=DaemonTaskType.LOG_COMPRESSION,
                priority=5,
                interval_seconds=1800,  # Cada 30 minutos
                enabled=True
            ),
            DaemonTask(
                task_type=DaemonTaskType.STATS_AGGREGATION,
                priority=4,
                interval_seconds=300,  # Cada 5 minutos
                enabled=True
            )
        ]
        
        for task in default_tasks:
            self.tasks[task.task_type.value] = task
    
    # Configuración de callbacks
    def set_memory_consolidation_callback(self, callback: Callable[[], bool]):
        """Callback para consolidación de memoria"""
        self.memory_consolidation_callback = callback
    
    def set_cache_warmup_callback(self, callback: Callable[[], bool]):
        """Callback para pre-calentar caché"""
        self.cache_warmup_callback = callback
    
    def set_temp_cleanup_callback(self, callback: Callable[[], bool]):
        """Callback para limpieza de temporales"""
        self.temp_cleanup_callback = callback
    
    def set_embeddings_update_callback(self, callback: Callable[[], bool]):
        """Callback para actualizar embeddings"""
        self.embeddings_update_callback = callback
    
    def set_index_optimization_callback(self, callback: Callable[[], bool]):
        """Callback para optimizar índices"""
        self.index_optimization_callback = callback
    
    def set_battery_callback(self, callback: Callable[[], float]):
        """Callback para nivel de batería"""
        self.battery_callback = callback
    
    def set_temperature_callback(self, callback: Callable[[], float]):
        """Callback para temperatura del dispositivo"""
        self.temperature_callback = callback
    
    def set_idle_detector_callback(self, callback: Callable[[], float]):
        """Callback para detectar tiempo de inactividad"""
        self.idle_detector_callback = callback
    
    def start(self):
        """Inicia el daemon KAIROS"""
        with self._lock:
            if self.status == DaemonStatus.STARTING or self.status == DaemonStatus.WORKING:
                return
            
            self.status = DaemonStatus.STARTING
            self.metrics.start_time = datetime.now()
            self._stop_event.clear()
            
            # Iniciar thread del daemon
            self._daemon_thread = threading.Thread(
                target=self._daemon_loop,
                name="KAIROS-Daemon",
                daemon=True
            )
            self._daemon_thread.start()
            
            self.status = DaemonStatus.IDLE
    
    def stop(self):
        """Detiene el daemon KAIROS"""
        with self._lock:
            self._stop_event.set()
            if self._daemon_thread and self._daemon_thread.is_alive():
                self._daemon_thread.join(timeout=5.0)
            self.status = DaemonStatus.STOPPED
    
    def pause(self):
        """Pausa el daemon temporalmente"""
        with self._lock:
            if self.status == DaemonStatus.WORKING or self.status == DaemonStatus.IDLE:
                self.status = DaemonStatus.PAUSED
    
    def resume(self):
        """Reanuda el daemon después de una pausa"""
        with self._lock:
            if self.status == DaemonStatus.PAUSED:
                self.status = DaemonStatus.IDLE
    
    def notify_user_interaction(self):
        """Notifica que hubo interacción del usuario"""
        self.metrics.last_user_interaction = datetime.now()
    
    def is_user_idle(self) -> bool:
        """Verifica si el usuario está inactivo"""
        if self.metrics.last_user_interaction is None:
            return True
        
        idle_time = (datetime.now() - self.metrics.last_user_interaction).total_seconds()
        return idle_time >= self.idle_threshold_seconds
    
    def _daemon_loop(self):
        """Bucle principal del daemon"""
        while not self._stop_event.is_set():
            try:
                # Verificar si está pausado
                if self.status == DaemonStatus.PAUSED:
                    time.sleep(1.0)
                    continue
                
                # Actualizar métricas del sistema
                self._update_system_metrics()
                
                # Verificar condiciones para trabajar
                if not self._should_work():
                    self.status = DaemonStatus.IDLE
                    time.sleep(1.0)
                    continue
                
                # Ejecutar tareas pendientes
                self.status = DaemonStatus.WORKING
                self._execute_pending_tasks()
                
                # Pequeña pausa entre ciclos
                time.sleep(self.work_interval_seconds / 10)  # Dividir para más granularidad
                
            except Exception as e:
                self.status = DaemonStatus.ERROR
                print(f"KAIROS Daemon error: {e}")
                time.sleep(5.0)
    
    def _update_system_metrics(self):
        """Actualiza las métricas del sistema"""
        if self.battery_callback:
            try:
                self.metrics.battery_level = self.battery_callback()
            except Exception:
                pass
        
        if self.temperature_callback:
            try:
                self.metrics.device_temp_celsius = self.temperature_callback()
            except Exception:
                pass
    
    def _should_work(self) -> bool:
        """Verifica si el daemon debe trabajar"""
        # Verificar si el usuario está inactivo
        if not self.is_user_idle():
            return False
        
        # Verificar batería
        if self.metrics.battery_level < self.min_battery_percentage:
            return False
        
        # Verificar temperatura
        if self.metrics.device_temp_celsius > self.max_temp_celsius:
            return False
        
        return True
    
    def _execute_pending_tasks(self):
        """Ejecuta las tareas pendientes"""
        for task_name, task in self.tasks.items():
            if self._stop_event.is_set():
                break
            
            if not task.should_run():
                continue
            
            # Ejecutar tarea
            start_time = time.time()
            success = self._execute_task(task)
            duration_ms = (time.time() - start_time) * 1000
            
            # Actualizar métricas
            task.mark_completed(success, duration_ms)
            self.metrics.total_tasks_executed += 1
            if not success:
                self.metrics.total_tasks_failed += 1
            self.metrics.total_work_time_ms += duration_ms
    
    def _execute_task(self, task: DaemonTask) -> bool:
        """Ejecuta una tarea específica"""
        try:
            if task.task_type == DaemonTaskType.MEMORY_CONSOLIDATION:
                return self._run_memory_consolidation()
            elif task.task_type == DaemonTaskType.CACHE_WARMUP:
                return self._run_cache_warmup()
            elif task.task_type == DaemonTaskType.TEMP_CLEANUP:
                return self._run_temp_cleanup()
            elif task.task_type == DaemonTaskType.EMBEDDINGS_UPDATE:
                return self._run_embeddings_update()
            elif task.task_type == DaemonTaskType.INDEX_OPTIMIZATION:
                return self._run_index_optimization()
            elif task.task_type == DaemonTaskType.LOG_COMPRESSION:
                return self._run_log_compression()
            elif task.task_type == DaemonTaskType.STATS_AGGREGATION:
                return self._run_stats_aggregation()
            return True
        except Exception as e:
            print(f"KAIROS task {task.task_type.value} failed: {e}")
            return False
    
    def _run_memory_consolidation(self) -> bool:
        """Consolida la memoria (merge, clean, crystallize insights)"""
        if self.memory_consolidation_callback:
            try:
                return self.memory_consolidation_callback()
            except Exception as e:
                print(f"Memory consolidation failed: {e}")
                return False
        return True
    
    def _run_cache_warmup(self) -> bool:
        """Pre-calienta el caché con queries populares"""
        if self.cache_warmup_callback:
            try:
                return self.cache_warmup_callback()
            except Exception as e:
                print(f"Cache warmup failed: {e}")
                return False
        return True
    
    def _run_temp_cleanup(self) -> bool:
        """Limpia archivos temporales"""
        if self.temp_cleanup_callback:
            try:
                return self.temp_cleanup_callback()
            except Exception as e:
                print(f"Temp cleanup failed: {e}")
                return False
        
        # Limpieza básica de archivos tmp
        try:
            tmp_dir = Path(self.data_dir) / "tmp"
            if tmp_dir.exists():
                for file in tmp_dir.glob("*"):
                    if file.is_file() and file.stat().st_mtime < time.time() - 3600:
                        file.unlink()
        except Exception:
            pass
        return True
    
    def _run_embeddings_update(self) -> bool:
        """Actualiza embeddings de datos nuevos"""
        if self.embeddings_update_callback:
            try:
                return self.embeddings_update_callback()
            except Exception as e:
                print(f"Embeddings update failed: {e}")
                return False
        return True
    
    def _run_index_optimization(self) -> bool:
        """Optimiza índices de base de datos"""
        if self.index_optimization_callback:
            try:
                return self.index_optimization_callback()
            except Exception as e:
                print(f"Index optimization failed: {e}")
                return False
        return True
    
    def _run_log_compression(self) -> bool:
        """Comprime logs antiguos"""
        try:
            log_dir = Path(self.data_dir) / "logs"
            if log_dir.exists():
                for log_file in log_dir.glob("*.log"):
                    if log_file.stat().st_mtime < time.time() - 86400:  # 1 día
                        # Comprimir con gzip
                        import gzip
                        compressed = log_file.with_suffix(".log.gz")
                        with open(log_file, 'rb') as f_in:
                            with gzip.open(compressed, 'wb') as f_out:
                                f_out.write(f_in.read())
                        log_file.unlink()
        except Exception as e:
            print(f"Log compression failed: {e}")
            return False
        return True
    
    def _run_stats_aggregation(self) -> bool:
        """Agrega estadísticas de uso"""
        try:
            stats_file = Path(self.data_dir) / "stats.json"
            if stats_file.exists():
                with open(stats_file, 'r') as f:
                    stats = json.load(f)
                # Actualizar agregaciones
                stats["last_aggregation"] = datetime.now().isoformat()
                with open(stats_file, 'w') as f:
                    json.dump(stats, f, indent=2)
        except Exception as e:
            print(f"Stats aggregation failed: {e}")
            return False
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado actual del daemon"""
        return {
            "status": self.status.value,
            "is_user_idle": self.is_user_idle(),
            "metrics": self.metrics.to_dict(),
            "tasks": {
                name: {
                    "type": task.task_type.value,
                    "enabled": task.enabled,
                    "last_run": task.last_run.isoformat() if task.last_run else None,
                    "next_run": task.next_run.isoformat() if task.next_run else None,
                    "success_rate": task.success_count / max(1, task.success_count + task.failure_count)
                }
                for name, task in self.tasks.items()
            }
        }
    
    def enable_task(self, task_type: DaemonTaskType, enabled: bool = True):
        """Habilita o deshabilita una tarea"""
        if task_type.value in self.tasks:
            self.tasks[task_type.value].enabled = enabled
    
    def configure_task(self, task_type: DaemonTaskType, interval_seconds: Optional[int] = None):
        """Configura una tarea"""
        if task_type.value in self.tasks:
            if interval_seconds is not None:
                self.tasks[task_type.value].interval_seconds = interval_seconds


# Instancia global
_daemon: Optional[KairosDaemon] = None


def get_kairos_daemon(config: Optional[Dict] = None) -> KairosDaemon:
    """Obtiene la instancia global del daemon KAIROS"""
    global _daemon
    if _daemon is None:
        _daemon = KairosDaemon(config)
    return _daemon


def start_kairos_daemon(config: Optional[Dict] = None) -> KairosDaemon:
    """Inicia el daemon KAIROS y retorna la instancia"""
    daemon = get_kairos_daemon(config)
    daemon.start()
    return daemon


def stop_kairos_daemon():
    """Detiene el daemon KAIROS global"""
    global _daemon
    if _daemon is not None:
        _daemon.stop()


if __name__ == "__main__":
    # Ejemplo de uso
    print("=== Claw-Litle 1.0 - KAIROS Daemon ===\n")
    
    # Configurar daemon
    daemon = get_kairos_daemon({
        "idle_threshold_seconds": 10,  # 10 segundos para testing
        "min_battery_percentage": 20.0,
        "max_temp_celsius": 80.0
    })
    
    # Configurar callbacks de ejemplo
    def mock_battery():
        return 85.0
    
    def mock_temperature():
        return 35.0
    
    daemon.set_battery_callback(mock_battery)
    daemon.set_temperature_callback(mock_temperature)
    
    # Simular interacción del usuario
    daemon.notify_user_interaction()
    
    print("Estado inicial:")
    print(json.dumps(daemon.get_status(), indent=2))
    
    # Iniciar daemon
    print("\nIniciando daemon...")
    daemon.start()
    
    # Esperar un poco y verificar estado
    time.sleep(5)
    
    print("\nEstado después de 5 segundos:")
    print(json.dumps(daemon.get_status(), indent=2))
    
    # Detener daemon
    daemon.stop()
    print("\nDaemon detenido.")