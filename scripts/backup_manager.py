#!/usr/bin/env python3
"""
Backup Manager - Script de Backup Automático para Claw-Litle.
Crea copias de seguridad de configuraciones, bases de datos y datos del usuario.
"""

import os
import sys
import json
import shutil
import sqlite3
import hashlib
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class BackupManager:
    """Gestor de backups automáticos con compresión y verificación."""
    
    def __init__(self, backup_dir: str = None):
        if backup_dir is None:
            # Directorio por defecto: /sdcard/clawlite-backups/ o ~/.clawlite-backups/
            if os.path.exists("/sdcard"):
                backup_dir = "/sdcard/clawlite-backups"
            else:
                backup_dir = str(Path.home() / ".clawlite-backups")
        
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Elementos a respaldar
        self.items_to_backup = {
            "config": Path("src/config"),
            "database": Path("data/clawlite.db"),
            "vector_store": Path("data/vector_store.db"),
            "memory_store": Path("data/memory.json"),
            "templates": Path("src/config/templates"),
            "user_data": Path("data/user_data"),
        }
        
        # Máximo número de backups a mantener
        self.max_backups = 5
    
    def calculate_checksum(self, file_path: Path) -> str:
        """Calcula checksum SHA256 de un archivo."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def create_backup(self, backup_name: str = None) -> Dict:
        """Crea un backup completo del sistema."""
        if backup_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"claw_backup_{timestamp}"
        
        backup_path = self.backup_dir / backup_name
        backup_zip = backup_path.with_suffix(".zip")
        
        print(f"🔄 Creando backup: {backup_name}")
        
        backup_info = {
            "name": backup_name,
            "timestamp": datetime.now().isoformat(),
            "items": {},
            "total_size": 0,
            "checksum": ""
        }
        
        # Crear directorio temporal
        temp_dir = backup_path / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Copiar cada elemento
            for item_name, item_path in self.items_to_backup.items():
                if item_path.exists():
                    if item_path.is_file():
                        # Copiar archivo individual
                        dest = temp_dir / item_path.name
                        shutil.copy2(item_path, dest)
                        size = dest.stat().st_size
                        checksum = self.calculate_checksum(dest)
                    elif item_path.is_dir():
                        # Copiar directorio completo
                        dest = temp_dir / item_path.name
                        shutil.copytree(item_path, dest)
                        size = sum(f.stat().st_size for f in dest.rglob("*") if f.is_file())
                        checksum = "directory"
                    else:
                        continue
                    
                    backup_info["items"][item_name] = {
                        "path": str(item_path),
                        "size": size,
                        "checksum": checksum,
                        "backed_up": True
                    }
                    backup_info["total_size"] += size
                    print(f"   ✅ {item_name}: {size/1024:.1f}KB")
                else:
                    backup_info["items"][item_name] = {
                        "path": str(item_path),
                        "backed_up": False,
                        "reason": "No existe"
                    }
                    print(f"   ⚠️  {item_name}: No existe (saltado)")
            
            # Crear archivo ZIP
            with zipfile.ZipFile(backup_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in temp_dir.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(temp_dir)
                        zipf.write(file_path, arcname)
            
            # Calcular checksum del ZIP
            backup_info["checksum"] = self.calculate_checksum(backup_zip)
            
            # Guardar metadata del backup
            metadata_file = backup_zip.with_suffix(".json")
            with open(metadata_file, 'w') as f:
                json.dump(backup_info, f, indent=2)
            
            # Limpiar directorio temporal
            shutil.rmtree(temp_dir)
            
            # Eliminar backups antiguos si excede el máximo
            self._cleanup_old_backups()
            
            print(f"✅ Backup completado: {backup_zip}")
            print(f"   Tamaño: {backup_zip.stat().st_size/1024/1024:.2f}MB")
            
            return backup_info
            
        except Exception as e:
            print(f"❌ Error creando backup: {e}")
            # Limpiar en caso de error
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            raise
    
    def restore_backup(self, backup_file: str) -> Dict:
        """Restaura un backup específico."""
        backup_path = Path(backup_file)
        
        if not backup_path.exists():
            # Buscar en directorio de backups
            backup_path = self.backup_dir / backup_file
            if not backup_path.exists():
                raise FileNotFoundError(f"Backup no encontrado: {backup_file}")
        
        print(f"🔄 Restaurando backup: {backup_path.name}")
        
        restore_info = {
            "backup_file": str(backup_path),
            "restored_items": [],
            "failed_items": [],
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Extraer ZIP
            temp_dir = backup_path.parent / "temp_restore"
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(temp_dir)
            
            # Restaurar cada elemento
            for item_name, item_path in self.items_to_backup.items():
                extracted_file = temp_dir / item_path.name
                
                if extracted_file.exists():
                    try:
                        # Crear directorio padre si no existe
                        item_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        if extracted_file.is_dir():
                            # Restaurar directorio
                            if item_path.exists():
                                shutil.rmtree(item_path)
                            shutil.copytree(extracted_file, item_path)
                        else:
                            # Restaurar archivo
                            shutil.copy2(extracted_file, item_path)
                        
                        restore_info["restored_items"].append(item_name)
                        print(f"   ✅ {item_name} restaurado")
                    except Exception as e:
                        restore_info["failed_items"].append({
                            "item": item_name,
                            "error": str(e)
                        })
                        print(f"   ❌ {item_name}: {e}")
            
            # Limpiar temporal
            shutil.rmtree(temp_dir)
            
            print(f"✅ Restauración completada")
            print(f"   Exitosos: {len(restore_info['restored_items'])}")
            print(f"   Fallidos: {len(restore_info['failed_items'])}")
            
            return restore_info
            
        except Exception as e:
            print(f"❌ Error restaurando backup: {e}")
            raise
    
    def list_backups(self) -> List[Dict]:
        """Lista todos los backups disponibles."""
        backups = []
        
        for backup_file in sorted(self.backup_dir.glob("claw_backup_*.zip")):
            metadata_file = backup_file.with_suffix(".json")
            
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                backups.append(metadata)
            else:
                # Si no hay metadata, crear información básica
                backups.append({
                    "name": backup_file.stem,
                    "file": str(backup_file),
                    "size": backup_file.stat().st_size,
                    "timestamp": "Desconocido"
                })
        
        return backups
    
    def delete_backup(self, backup_name: str) -> bool:
        """Elimina un backup específico."""
        backup_file = self.backup_dir / f"{backup_name}.zip"
        metadata_file = backup_file.with_suffix(".json")
        
        if backup_file.exists():
            backup_file.unlink()
            if metadata_file.exists():
                metadata_file.unlink()
            print(f"✅ Backup eliminado: {backup_name}")
            return True
        
        print(f"❌ Backup no encontrado: {backup_name}")
        return False
    
    def _cleanup_old_backups(self):
        """Elimina backups antiguos manteniendo solo los últimos N."""
        backups = self.list_backups()
        
        if len(backups) > self.max_backups:
            # Ordenar por timestamp (más reciente primero)
            backups.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            # Eliminar los más antiguos
            for backup in backups[self.max_backups:]:
                self.delete_backup(backup["name"])
    
    def get_backup_stats(self) -> Dict:
        """Obtiene estadísticas de backups."""
        backups = self.list_backups()
        
        total_size = sum(b.get("size", 0) for b in backups)
        
        return {
            "total_backups": len(backups),
            "total_size_mb": total_size / (1024 * 1024),
            "max_backups": self.max_backups,
            "backup_dir": str(self.backup_dir),
            "newest_backup": backups[0]["timestamp"] if backups else None,
            "oldest_backup": backups[-1]["timestamp"] if backups else None
        }


def main():
    """Función principal para ejecutar desde línea de comandos."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Claw-Litle Backup Manager")
    parser.add_argument("action", choices=["create", "restore", "list", "delete", "stats"],
                       help="Acción a realizar")
    parser.add_argument("--name", "-n", help="Nombre del backup (para restore/delete)")
    parser.add_argument("--dir", "-d", help="Directorio de backups")
    
    args = parser.parse_args()
    
    manager = BackupManager(backup_dir=args.dir)
    
    if args.action == "create":
        manager.create_backup(args.name)
    elif args.action == "restore":
        if not args.name:
            print("❌ Se requiere --name para restaurar")
            sys.exit(1)
        manager.restore_backup(args.name)
    elif args.action == "list":
        backups = manager.list_backups()
        print(f"\n📦 Backups disponibles ({len(backups)}):")
        for backup in backups:
            print(f"   • {backup['name']} - {backup.get('timestamp', 'N/A')}")
    elif args.action == "delete":
        if not args.name:
            print("❌ Se requiere --name para eliminar")
            sys.exit(1)
        manager.delete_backup(args.name)
    elif args.action == "stats":
        stats = manager.get_backup_stats()
        print(f"\n📊 Estadísticas de Backups:")
        print(f"   Total: {stats['total_backups']}")
        print(f"   Tamaño: {stats['total_size_mb']:.2f}MB")
        print(f"   Máximo: {stats['max_backups']}")
        print(f"   Directorio: {stats['backup_dir']}")


if __name__ == "__main__":
    main()