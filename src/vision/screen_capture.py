"""
Claw-Litle 1.0
screen_capture.py - Captura de Pantalla para Vision Agency

Compatible con Termux mediante ADB/UIAutomator.
"""

import logging
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ScreenshotResult:
    """Resultado de captura de pantalla."""
    success: bool
    image_path: Optional[str] = None
    width: int = 0
    height: int = 0
    timestamp: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = None


class ScreenCapture:
    """
    Captura de pantalla compatible con Termux.
    
    Métodos soportados:
    - ADB (Android Debug Bridge) - requiere USB debugging
    - UIAutomator - requiere permisos de accesibilidad
    - Fallback: simulación para testing
    """
    
    def __init__(self, method: str = "auto"):
        self.method = method
        self._last_screenshot: Optional[ScreenshotResult] = None
        
        logger.info(f"ScreenCapture inicializado - Método: {method}")
    
    def capture(self, output_path: Optional[str] = None) -> ScreenshotResult:
        """
        Captura la pantalla actual.
        
        Args:
            output_path: Ruta para guardar la imagen (opcional)
            
        Returns:
            ScreenshotResult con los datos de la captura
        """
        start_time = time.time()
        
        if self.method == "auto":
            return self._auto_capture(output_path)
        elif self.method == "adb":
            return self._adb_capture(output_path)
        elif self.method == "uiautomator":
            return self._uiautomator_capture(output_path)
        else:
            return self._mock_capture(output_path)
    
    def _auto_capture(self, output_path: Optional[str]) -> ScreenshotResult:
        """Intenta métodos de captura en orden de preferencia."""
        # Intentar ADB primero
        result = self._adb_capture(output_path)
        if result.success:
            return result
        
        # Intentar UIAutomator
        result = self._uiautomator_capture(output_path)
        if result.success:
            return result
        
        # Fallback a mock
        return self._mock_capture(output_path)
    
    def _adb_capture(self, output_path: Optional[str]) -> ScreenshotResult:
        """Captura usando ADB (Android Debug Bridge)."""
        try:
            import subprocess
            
            # Generar ruta temporal si no se especifica
            if not output_path:
                output_path = f"/sdcard/Download/claw_screenshot_{int(time.time())}.png"
            
            # Comando ADB para captura
            cmd = ["adb", "shell", "screenshot", output_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self._last_screenshot = ScreenshotResult(
                    success=True,
                    image_path=output_path,
                    width=1080,  # Resolución típica
                    height=2400,
                    timestamp=time.time(),
                    metadata={"method": "adb"}
                )
                logger.info(f"Captura ADB exitosa: {output_path}")
                return self._last_screenshot
            
            return ScreenshotResult(
                success=False,
                error=f"ADB failed: {result.stderr}",
                timestamp=time.time()
            )
            
        except FileNotFoundError:
            return ScreenshotResult(
                success=False,
                error="ADB no encontrado",
                timestamp=time.time()
            )
        except Exception as e:
            return ScreenshotResult(
                success=False,
                error=str(e),
                timestamp=time.time()
            )
    
    def _uiautomator_capture(self, output_path: Optional[str]) -> ScreenshotResult:
        """Captura usando UIAutomator."""
        try:
            import subprocess
            
            if not output_path:
                output_path = f"/sdcard/Download/claw_screenshot_{int(time.time())}.png"
            
            # UIAutomator para captura
            cmd = ["uiautomator", "screendump", output_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self._last_screenshot = ScreenshotResult(
                    success=True,
                    image_path=output_path,
                    width=1080,
                    height=2400,
                    timestamp=time.time(),
                    metadata={"method": "uiautomator"}
                )
                logger.info(f"Captura UIAutomator exitosa: {output_path}")
                return self._last_screenshot
            
            return ScreenshotResult(
                success=False,
                error=f"UIAutomator failed: {result.stderr}",
                timestamp=time.time()
            )
            
        except FileNotFoundError:
            return ScreenshotResult(
                success=False,
                error="UIAutomator no encontrado",
                timestamp=time.time()
            )
        except Exception as e:
            return ScreenshotResult(
                success=False,
                error=str(e),
                timestamp=time.time()
            )
    
    def _mock_capture(self, output_path: Optional[str]) -> ScreenshotResult:
        """Captura simulada para testing."""
        if not output_path:
            output_path = f"/tmp/claw_mock_screenshot_{int(time.time())}.png"
        
        # Simular captura
        self._last_screenshot = ScreenshotResult(
            success=True,
            image_path=output_path,
            width=1080,
            height=2400,
            timestamp=time.time(),
            metadata={"method": "mock", "simulated": True}
        )
        
        logger.info(f"Captura simulada: {output_path}")
        return self._last_screenshot
    
    def get_last_screenshot(self) -> Optional[ScreenshotResult]:
        """Obtiene la última captura realizada."""
        return self._last_screenshot
    
    def get_screen_resolution(self) -> Dict[str, int]:
        """Obtiene resolución de pantalla."""
        try:
            import subprocess
            result = subprocess.run(
                ["adb", "shell", "wm", "size"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                # Parsear "Physical size: 1080x2400"
                parts = result.stdout.strip().split(":")
                if len(parts) > 1:
                    dims = parts[1].strip().split("x")
                    return {"width": int(dims[0]), "height": int(dims[1])}
        except Exception:
            pass
        
        return {"width": 1080, "height": 2400}  # Default


if __name__ == "__main__":
    # Test rápido
    capture = ScreenCapture(method="mock")
    result = capture.capture()
    print(f"Captura: {result.success}")
    print(f"Ruta: {result.image_path}")
    print(f"Resolución: {result.width}x{result.height}")
    print(f"Resolución pantalla: {capture.get_screen_resolution()}")