"""
Claw-Litle 1.0
environment_detector.py - Detector de Entorno

Detecta automáticamente el entorno de ejecución (Termux, Raspberry Pi, Laptop, etc.)
y selecciona el perfil de configuración óptimo.
"""

import os
import sys
import platform
import json
import logging
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class EnvironmentDetector:
    """
    Detector de entorno multi-plataforma.
    
    Detecta automáticamente:
    - Termux en Android (ARM64)
    - Raspberry Pi (ARM64)
    - Laptop/PC (x86_64)
    - Otros entornos Linux
    
    Selecciona el perfil de configuración óptimo basado en:
    - Arquitectura CPU
    - RAM disponible
    - Sistema operativo
    - Capacidades del entorno
    """
    
    def __init__(self, config_dir: str = "src/config/environment_profiles"):
        """
        Inicializa el detector de entorno.
        
        Args:
            config_dir: Directorio con los perfiles de entorno
        """
        self.config_dir = Path(config_dir)
        self._detected_profile = None
        self._capabilities = None
        
        logger.info("EnvironmentDetector inicializado")
    
    def detect(self) -> str:
        """
        Detecta el entorno de ejecución actual.
        
        Returns:
            Nombre del perfil detectado
        """
        # Verificar si ya detectamos
        if self._detected_profile:
            return self._detected_profile
        
        # Detectar entorno
        profile = self._detect_environment()
        self._detected_profile = profile
        
        logger.info(f"Entorno detectado: {profile}")
        return profile
    
    def _detect_environment(self) -> str:
        """
        Lógica principal de detección.
        
        Returns:
            Nombre del perfil detectado
        """
        # 1. Detectar Termux (Android)
        if self._is_termux():
            # Verificar si es dispositivo ligero (<2GB RAM)
            ram_gb = self._get_ram_gb()
            if ram_gb < 2:
                return "termux_light"
            return "termux_arm64"
        
        # 2. Detectar Raspberry Pi
        if self._is_raspberry_pi():
            return "raspberry_pi"
        
        # 3. Detectar arquitectura
        arch = platform.machine().lower()
        
        if 'x86_64' in arch or 'amd64' in arch or 'AMD64' in arch:
            return "laptop_pc"
        
        if 'aarch64' in arch or 'arm64' in arch or 'ARM64' in arch:
            # ARM64 genérico (no Termux, no Raspberry Pi)
            return "laptop_pc"  # Usar perfil genérico
        
        # Fallback: perfil ligero
        return "termux_light"
    
    def _is_termux(self) -> bool:
        """
        Detecta si estamos en Termux (Android).
        
        Returns:
            True si es Termux
        """
        # Variables de entorno de Termux
        if os.environ.get('TERMUX_VERSION'):
            return True
        
        if os.environ.get('PREFIX', '').endswith('termux'):
            return True
        
        # Ruta típica de Termux
        if '/com.termux/' in str(Path.home()) or '/data/data/com.termux/' in str(Path.home()):
            return True
        
        # Verificar por archivo de propiedades de Android
        try:
            if os.path.exists('/system/build.prop'):
                # Estamos en Android
                if os.path.exists(os.environ.get('PREFIX', '/data/data/com.termux/files/usr')):
                    return True
        except Exception:
            pass
        
        return False
    
    def _is_raspberry_pi(self) -> bool:
        """
        Detecta si estamos en Raspberry Pi.
        
        Returns:
            True si is Raspberry Pi
        """
        # Verificar por modelo de CPU
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                
                if 'Raspberry Pi' in cpuinfo:
                    return True
                
                if 'BCM2711' in cpuinfo or 'BCM2712' in cpuinfo:  # Pi 4/5
                    return True
        except Exception:
            pass
        
        # Verificar por hostname
        hostname = platform.node().lower()
        if 'raspberry' in hostname or 'raspi' in hostname:
            return True
        
        # Verificar por archivo de modelo
        try:
            if os.path.exists('/sys/firmware/devicetree/base/model'):
                with open('/sys/firmware/devicetree/base/model', 'r') as f:
                    model = f.read()
                    if 'Raspberry Pi' in model:
                        return True
        except Exception:
            pass
        
        return False
    
    def _get_ram_gb(self) -> float:
        """
        Obtiene la RAM total del sistema en GB.
        
        Returns:
            RAM en GB
        """
        try:
            import psutil
            ram_bytes = psutil.virtual_memory().total
            return ram_bytes / (1024 ** 3)
        except ImportError:
            # Fallback: leer /proc/meminfo
            try:
                with open('/proc/meminfo', 'r') as f:
                    for line in f:
                        if line.startswith('MemTotal:'):
                            # MemTotal está en kB
                            kb = int(line.split()[1])
                            return kb / (1024 * 1024)
            except Exception:
                pass
        
        return 1.0  # Default seguro
    
    def get_profile(self) -> Dict:
        """
        Obtiene el perfil de configuración completo.
        
        Returns:
            Diccionario con la configuración del perfil
        """
        profile_name = self.detect()
        profile_path = self.config_dir / f"{profile_name}.json"
        
        if not profile_path.exists():
            logger.warning(f"Perfil no encontrado: {profile_path}. Usando termux_arm64")
            profile_path = self.config_dir / "termux_arm64.json"
        
        try:
            with open(profile_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error cargando perfil {profile_path}: {e}")
            return self._get_default_profile()
    
    def _get_default_profile(self) -> Dict:
        """
        Retorna un perfil por defecto seguro.
        
        Returns:
            Diccionario con configuración conservadora
        """
        return {
            "profile_name": "termux_arm64",
            "profile_version": "1.0",
            "description": "Perfil por defecto - Configuración conservadora",
            "environment": {
                "type": "termux_android",
                "arch": "arm64-v8a",
                "ram_typical_mb": 4096,
                "ram_min_mb": 2048,
                "python_version_min": "3.11",
                "has_root": False,
                "has_docker": False,
                "has_gui_display": False,
                "cpu_cores_typical": 8
            },
            "capabilities_detected": {
                "can_compile_c": False,
                "can_run_docker": False,
                "can_use_gui": False,
                "has_internet": True,
                "has_telegram": True,
                "max_concurrent_agents": 2,
                "safe_timeout_seconds": 10,
                "max_memory_mb": 350,
                "supports_async": True,
                "supports_sqlite": True,
                "supports_onnx": True
            },
            "performance_tuning": {
                "swarm_max_agents": 2,
                "model_lazy_load": True,
                "cache_aggressive": True,
                "battery_saver_mode": False,
                "thermal_throttling": True,
                "memory_optimization": "high"
            },
            "limits": {
                "max_file_size_mb": 50,
                "max_query_length": 1000,
                "max_response_length": 10000,
                "max_concurrent_tasks": 3,
                "max_retries": 3,
                "timeout_short_seconds": 5,
                "timeout_medium_seconds": 15,
                "timeout_long_seconds": 30
            }
        }
    
    def get_capabilities(self) -> Dict:
        """
        Obtiene las capacidades detectadas del entorno.
        
        Returns:
            Diccionario con capacidades del sistema
        """
        if self._capabilities:
            return self._capabilities
        
        profile = self.get_profile()
        self._capabilities = profile.get('capabilities_detected', {})
        
        return self._capabilities
    
    def is_mobile(self) -> bool:
        """
        Verifica if el entorno es móvil (Termux).
        
        Returns:
            True si is entorno móvil
        """
        profile = self.detect()
        return 'termux' in profile
    
    def has_gui(self) -> bool:
        """
        Verifica si el entorno tiene soporte GUI.
        
        Returns:
            True si hay soporte GUI
        """
        profile = self.get_profile()
        return profile.get('environment', {}).get('has_gui_display', False)
    
    def get_max_agents(self) -> int:
        """
        Obtiene el máximo de agentes concurrentes permitido.
        
        Returns:
            Número máximo de agentes
        """
        profile = self.get_profile()
        return profile.get('capabilities_detected', {}).get('max_concurrent_agents', 2)
    
    def get_max_memory_mb(self) -> int:
        """
        Obtiene la memoria máxima usable en MB.
        
        Returns:
            Memoria máxima en MB
        """
        profile = self.get_profile()
        return profile.get('capabilities_detected', {}).get('max_memory_mb', 350)
    
    def should_use_onnx(self) -> bool:
        """
        Verifica si se debe usar ONNX (modelo semántico).
        
        Returns:
            True si se puede usar ONNX
        """
        profile = self.get_profile()
        return profile.get('capabilities_detected', {}).get('supports_onnx', True)