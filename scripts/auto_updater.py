#!/usr/bin/env python3
"""
Auto-Updater - Script de Actualización Automática para Claw-Litle.
Verifica nuevas versiones, descarga e instala actualizaciones de forma segura.
"""

import os
import sys
import json
import hashlib
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import zipfile
import tempfile


class AutoUpdater:
    """Gestor de actualizaciones automáticas con verificación de integridad."""
    
    # URL del repositorio (GitHub)
    REPO_URL = "https://github.com/yurislay9-ui/Clow-Litle-Ultra"
    RELEASES_API = "https://api.github.com/repos/yurislay9-ui/Clow-Litle-Ultra/releases"
    
    def __init__(self, install_dir: str = None):
        self.install_dir = Path(install_dir) if install_dir else Path.cwd()
        self.version_file = self.install_dir / "VERSION"
        self.config_dir = self.install_dir / "src" / "config"
        
        # Archivo de configuración de actualizaciones
        self.update_config_file = self.install_dir / ".update_config.json"
        self.update_config = self._load_update_config()
    
    def _load_update_config(self) -> Dict:
        """Carga la configuración de actualizaciones."""
        default_config = {
            "auto_update": False,
            "check_interval_hours": 24,
            "backup_before_update": True,
            "rollback_on_failure": True,
            "last_check": None,
            "current_version": self._get_current_version(),
            "update_channel": "stable"  # stable, beta, dev
        }
        
        if self.update_config_file.exists():
            try:
                with open(self.update_config_file, 'r') as f:
                    saved_config = json.load(f)
                    default_config.update(saved_config)
            except:
                pass
        
        return default_config
    
    def _save_update_config(self):
        """Guarda la configuración de actualizaciones."""
        with open(self.update_config_file, 'w') as f:
            json.dump(self.update_config, f, indent=2)
    
    def _get_current_version(self) -> str:
        """Obtiene la versión actual instalada."""
        if self.version_file.exists():
            return self.version_file.read_text().strip()
        return "0.0.0"
    
    def _set_current_version(self, version: str):
        """Establece la versión actual."""
        self.version_file.write_text(version)
        self.update_config["current_version"] = version
        self._save_update_config()
    
    def check_for_updates(self) -> Dict:
        """Verifica si hay actualizaciones disponibles."""
        print(f"🔍 Verificando actualizaciones...")
        
        # En producción, esto haría una petición a GitHub API
        # Por ahora, simulamos la verificación
        
        current_version = self._get_current_version()
        print(f"   Versión actual: {current_version}")
        
        # Simular respuesta (en producción usar requests.get(self.RELEASES_API))
        latest_version = self._get_latest_version_simulated()
        
        if latest_version > current_version:
            print(f"   ✅ Nueva versión disponible: {latest_version}")
            return {
                "update_available": True,
                "current_version": current_version,
                "latest_version": latest_version,
                "release_notes": self._get_release_notes_simulated(latest_version)
            }
        else:
            print(f"   ℹ️  Ya estás en la última versión")
            return {
                "update_available": False,
                "current_version": current_version,
                "latest_version": current_version
            }
    
    def _get_latest_version_simulated(self) -> str:
        """Simula obtención de última versión (reemplazar con API real)."""
        # En producción: hacer GET a self.RELEASES_API y parsear JSON
        return "1.0.1"  # Versión simulada
    
    def _get_release_notes_simulated(self, version: str) -> str:
        """Simula notas de lanzamiento (reemplazar con API real)."""
        return f"""
🦁 Claw-Litle {version}

Novedades:
- Mejoras de rendimiento en Termux
- Corrección de bugs en thermal throttling
- Nuevos templates de código
- Optimización de memoria
"""
    
    def download_update(self, version: str) -> Tuple[bool, str]:
        """Descarga la actualización (simulado)."""
        print(f"📥 Descargando actualización {version}...")
        
        # En producción:
        # 1. Descargar ZIP del release desde GitHub
        # 2. Verificar checksum SHA256
        # 3. Guardar en archivo temporal
        
        # Simulación
        temp_dir = Path(tempfile.mkdtemp(prefix="claw_update_"))
        update_file = temp_dir / f"claw-lite-{version}.zip"
        
        # Crear archivo dummy para simulación
        update_file.write_text(f"Update package v{version}")
        
        print(f"   ✅ Descarga completada: {update_file}")
        return True, str(update_file)
    
    def verify_update(self, update_file: str, expected_checksum: str) -> bool:
        """Verifica la integridad de la actualización."""
        print(f"🔒 Verificando integridad...")
        
        # Calcular checksum del archivo descargado
        sha256_hash = hashlib.sha256()
        with open(update_file, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        actual_checksum = sha256_hash.hexdigest()
        
        if actual_checksum == expected_checksum:
            print(f"   ✅ Integridad verificada")
            return True
        else:
            print(f"   ❌ Checksum no coincide")
            print(f"      Esperado: {expected_checksum}")
            print(f"      Obtenido: {actual_checksum}")
            return False
    
    def install_update(self, update_file: str, backup: bool = True) -> Dict:
        """Instala la actualización."""
        print(f"🔧 Instalando actualización...")
        
        install_info = {
            "success": False,
            "backup_created": False,
            "backup_file": None,
            "rolled_back": False,
            "errors": []
        }
        
        temp_dir = Path(tempfile.mkdtemp(prefix="claw_install_"))
        
        try:
            # 1. Crear backup si se solicita
            if backup and self.update_config.get("backup_before_update", True):
                print(f"   📦 Creando backup...")
                from .backup_manager import BackupManager
                backup_manager = BackupManager()
                backup_info = backup_manager.create_backup(f"pre_update_{self._get_current_version()}")
                install_info["backup_created"] = True
                install_info["backup_file"] = backup_info.get("name")
                print(f"   ✅ Backup creado: {install_info['backup_file']}")
            
            # 2. Extraer nueva versión
            print(f"   📂 Extrayendo actualización...")
            with zipfile.ZipFile(update_file, 'r') as zipf:
                zipf.extractall(temp_dir)
            
            # 3. Copiar archivos (manteniendo configuraciones del usuario)
            print(f"   📋 Copiando archivos...")
            self._copy_files_safely(temp_dir)
            
            # 4. Actualizar versión
            new_version = self._extract_version_from_update(update_file)
            self._set_current_version(new_version)
            
            install_info["success"] = True
            print(f"   ✅ Actualización instalada: {new_version}")
            
        except Exception as e:
            install_info["errors"].append(str(e))
            print(f"   ❌ Error instalando: {e}")
            
            # Rollback si está habilitado
            if self.update_config.get("rollback_on_failure", True) and install_info["backup_created"]:
                print(f"   🔄 Intentando rollback...")
                try:
                    from .backup_manager import BackupManager
                    backup_manager = BackupManager()
                    backup_manager.restore_backup(install_info["backup_file"])
                    install_info["rolled_back"] = True
                    print(f"   ✅ Rollback completado")
                except Exception as rollback_error:
                    print(f"   ❌ Error en rollback: {rollback_error}")
                    install_info["errors"].append(f"Rollback failed: {rollback_error}")
        
        finally:
            # Limpiar temporal
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
        
        return install_info
    
    def _copy_files_safely(self, source_dir: Path):
        """Copia archivos manteniendo configuraciones del usuario."""
        # Archivos/directorios a NO sobrescribir
        preserve = [
            "src/config/defaults.toml",  # El usuario puede tener customizaciones
            "data/",  # Datos del usuario
            ".env",  # Variables de entorno
        ]
        
        for item in source_dir.iterdir():
            dest = self.install_dir / item.name
            
            # Verificar si debe preservarse
            should_preserve = any(
                str(dest).endswith(p) or str(dest).startswith(str(self.install_dir / p))
                for p in preserve
            )
            
            if should_preserve and dest.exists():
                print(f"   ⏭️  Preservando: {item.name}")
                continue
            
            if item.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)
    
    def _extract_version_from_update(self, update_file: str) -> str:
        """Extrae la versión del paquete de actualización."""
        # En producción, extraer del archivo VERSION dentro del ZIP
        return "1.0.1"  # Simulado
    
    def auto_update(self) -> Dict:
        """Ejecuta actualización automática completa."""
        print(f"🦁 Claw-Litle Auto-Updater")
        print(f"=" * 50)
        
        # 1. Verificar actualizaciones
        update_info = self.check_for_updates()
        if not update_info["update_available"]:
            return {"updated": False, "reason": "No hay actualizaciones"}
        
        # 2. Descargar
        success, update_file = self.download_update(update_info["latest_version"])
        if not success:
            return {"updated": False, "reason": "Error descargando"}
        
        # 3. Verificar (en producción con checksum real)
        # verified = self.verify_update(update_file, expected_checksum)
        # if not verified:
        #     return {"updated": False, "reason": "Verificación fallida"}
        
        # 4. Instalar
        install_result = self.install_update(update_file)
        
        return {
            "updated": install_result["success"],
            "old_version": update_info["current_version"],
            "new_version": update_info["latest_version"],
            "backup_created": install_result["backup_created"],
            "rolled_back": install_result["rolled_back"],
            "errors": install_result["errors"]
        }
    
    def configure(self, **kwargs):
        """Configura opciones de actualización."""
        for key, value in kwargs.items():
            if key in self.update_config:
                self.update_config[key] = value
        
        self._save_update_config()
        print(f"✅ Configuración actualizada")
    
    def get_status(self) -> Dict:
        """Obtiene estado del actualizador."""
        return {
            "current_version": self._get_current_version(),
            "auto_update_enabled": self.update_config.get("auto_update", False),
            "check_interval_hours": self.update_config.get("check_interval_hours", 24),
            "backup_before_update": self.update_config.get("backup_before_update", True),
            "rollback_on_failure": self.update_config.get("rollback_on_failure", True),
            "last_check": self.update_config.get("last_check"),
            "update_channel": self.update_config.get("update_channel", "stable")
        }


def main():
    """Función principal para CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Claw-Litle Auto-Updater")
    parser.add_argument("action", choices=["check", "update", "configure", "status"],
                       help="Acción a realizar")
    parser.add_argument("--auto-update", action="store_true", help="Habilitar actualización automática")
    parser.add_argument("--no-backup", action="store_true", help="No crear backup antes de actualizar")
    
    args = parser.parse_args()
    
    updater = AutoUpdater()
    
    if args.action == "check":
        result = updater.check_for_updates()
        if result["update_available"]:
            print(f"\n{result['release_notes']}")
    elif args.action == "update":
        result = updater.auto_update()
        if result["updated"]:
            print(f"\n✅ Actualizado de {result['old_version']} a {result['new_version']}")
        else:
            print(f"\n❌ Error: {result.get('reason', 'Desconocido')}")
    elif args.action == "configure":
        updater.configure(
            auto_update=args.auto_update,
            backup_before_update=not args.no_backup
        )
    elif args.action == "status":
        status = updater.get_status()
        print(f"\n📊 Estado del Actualizador:")
        for key, value in status.items():
            print(f"   {key}: {value}")


if __name__ == "__main__":
    main()