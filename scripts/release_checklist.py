#!/usr/bin/env python3
"""
Release Checklist - Lista de verificación para releases de Claw-Litle.
Automatiza la verificación de todos los requisitos antes de un release.
"""

import os
import sys
import json
import subprocess
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple


class ReleaseChecker:
    """Verifica todos los requisitos para un release."""
    
    def __init__(self, version: str = None):
        self.root_dir = Path.cwd()
        self.version = version or self._get_version_from_pyproject()
        self.checks = []
        self.warnings = []
        self.errors = []
    
    def _get_version_from_pyproject(self) -> str:
        """Obtiene la versión actual del pyproject.toml."""
        pyproject = self.root_dir / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text()
            match = re.search(r'version\s*=\s*"([^"]+)"', content)
            if match:
                return match.group(1)
        return "0.0.0"
    
    def check_python_files(self):
        """Verifica que todos los archivos Python sean válidos."""
        print("🔍 Verificando archivos Python...")
        
        errors = []
        for py_file in self.root_dir.rglob("*.py"):
            # Excluir venv y __pycache__
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue
            
            try:
                with open(py_file, 'r') as f:
                    compile(f.read(), py_file, 'exec')
            except SyntaxError as e:
                errors.append(f"{py_file}: {e}")
        
        if errors:
            self.errors.extend(errors)
            print(f"   ❌ {len(errors)} errores de sintaxis")
        else:
            print("   ✅ Todos los archivos Python son válidos")
    
    def check_tests(self):
        """Verifica que los tests estén presentes."""
        print("🧪 Verificando tests...")
        
        test_files = list((self.root_dir / "tests").rglob("test_*.py"))
        
        if len(test_files) < 10:
            self.warnings.append("Pocos archivos de test (< 10)")
            print(f"   ⚠️  Solo {len(test_files)} archivos de test")
        else:
            print(f"   ✅ {len(test_files)} archivos de test encontrados")
    
    def check_documentation(self):
        """Verifica documentación esencial."""
        print("📚 Verificando documentación...")
        
        required_docs = [
            "README.md",
            "QUICKSTART.md",
            "LICENSE",
            "CHANGELOG.md",
            "CONTRIBUTING.md",
        ]
        
        missing = []
        for doc in required_docs:
            if not (self.root_dir / doc).exists():
                missing.append(doc)
        
        if missing:
            self.errors.append(f"Documentación faltante: {', '.join(missing)}")
            print(f"   ❌ Falta: {', '.join(missing)}")
        else:
            print("   ✅ Documentación esencial completa")
        
        # Verificar docs adicionales
        docs_dir = self.root_dir / "docs"
        if docs_dir.exists():
            doc_files = list(docs_dir.glob("*.md"))
            print(f"   📄 {len(doc_files)} documentos en docs/")
    
    def check_requirements(self):
        """Verifica archivos de requisitos."""
        print("📦 Verificando requisitos...")
        
        required_files = [
            "requirements.txt",
            "requirements-dev.txt",
            "requirements-termux.txt",
        ]
        
        missing = []
        for req_file in required_files:
            if not (self.root_dir / req_file).exists():
                missing.append(req_file)
        
        if missing:
            self.warnings.append(f"Archivos de requisitos faltantes: {', '.join(missing)}")
            print(f"   ⚠️  Faltan: {', '.join(missing)}")
        else:
            print("   ✅ Todos los archivos de requisitos presentes")
    
    def check_config_files(self):
        """Verifica archivos de configuración."""
        print("⚙️  Verificando configuración...")
        
        config_dir = self.root_dir / "src" / "config"
        
        if not config_dir.exists():
            self.errors.append("Directorio src/config no existe")
            print("   ❌ src/config no existe")
            return
        
        # Verificar perfiles de entorno
        profiles_dir = config_dir / "environment_profiles"
        if profiles_dir.exists():
            profiles = list(profiles_dir.glob("*.json"))
            print(f"   📄 {len(profiles)} perfiles de entorno")
        else:
            self.warnings.append("No hay perfiles de entorno")
        
        # Verificar templates
        templates_dir = config_dir / "templates"
        if templates_dir.exists():
            templates = list(templates_dir.rglob("*.template"))
            print(f"   📄 {len(templates)} templates")
        else:
            self.warnings.append("No hay templates")
    
    def check_git_status(self):
        """Verifica estado de git."""
        print("🔀 Verificando estado de git...")
        
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=self.root_dir
            )
            
            if result.stdout.strip():
                self.warnings.append("Hay cambios sin commitear")
                print(f"   ⚠️  Cambios pendientes:")
                for line in result.stdout.strip().split('\n'):
                    print(f"      {line}")
            else:
                print("   ✅ Working directory limpio")
        except FileNotFoundError:
            self.warnings.append("Git no está instalado o no es un repo")
            print("   ⚠️  Git no disponible")
    
    def check_version_consistency(self):
        """Verifica consistencia de versión."""
        print("🔢 Verificando versión...")
        
        # Verificar pyproject.toml
        pyproject = self.root_dir / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text()
            match = re.search(r'version\s*=\s*"([^"]+)"', content)
            if match:
                pyproject_version = match.group(1)
                print(f"   📄 pyproject.toml: {pyproject_version}")
        
        # Verificar CHANGELOG
        changelog = self.root_dir / "CHANGELOG.md"
        if changelog.exists():
            content = changelog.read_text()
            if f"## [{self.version}]" in content or f"## {self.version}" in content:
                print(f"   ✅ Versión {self.version} en CHANGELOG")
            else:
                self.warnings.append(f"Versión {self.version} no está en CHANGELOG")
                print(f"   ⚠️  Versión {self.version} no encontrada en CHANGELOG")
    
    def check_security(self):
        """Verifica aspectos de seguridad."""
        print("🔒 Verificando seguridad...")
        
        # Buscar hardcoded secrets (básico)
        suspicious_patterns = [
            r'password\s*=\s*"[^"]+',
            r'api_key\s*=\s*"[^"]+',
            r'secret\s*=\s*"[^"]+',
            r'token\s*=\s*"[^"]+',
        ]
        
        found = []
        for py_file in self.root_dir.rglob("*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue
            
            content = py_file.read_text()
            for pattern in suspicious_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    # Excluir ejemplos y tests
                    if "example" not in str(py_file) and "test" not in str(py_file):
                        found.append(f"{py_file}: {match}")
        
        if found:
            self.warnings.append(f"Posibles secrets hardcoded: {len(found)}")
            print(f"   ⚠️  {len(found)} posibles secrets encontrados")
        else:
            print("   ✅ No se encontraron secrets obvios")
    
    def run_all_checks(self) -> Dict:
        """Ejecuta todas las verificaciones."""
        print(f"\n{'='*60}")
        print(f"🦁 Claw-Litle - Release Checklist")
        print(f"📦 Versión: {self.version}")
        print(f"{'='*60}\n")
        
        self.check_python_files()
        self.check_tests()
        self.check_documentation()
        self.check_requirements()
        self.check_config_files()
        self.check_git_status()
        self.check_version_consistency()
        self.check_security()
        
        print(f"\n{'='*60}")
        print(f"📊 Resumen:")
        print(f"   ✅ Checks pasados: {len(self.checks)}")
        print(f"   ⚠️  Warnings: {len(self.warnings)}")
        print(f"   ❌ Errores: {len(self.errors)}")
        print(f"{'='*60}\n")
        
        if self.errors:
            print("❌ ERRORES CRÍTICOS:")
            for error in self.errors:
                print(f"   • {error}")
            print()
        
        if self.warnings:
            print("⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"   • {warning}")
            print()
        
        if not self.errors:
            print("✅ ¡LISTO PARA RELEASE!")
            print(f"   Versión {self.version} está lista para publicar.")
        else:
            print("❌ NO LISTO PARA RELEASE")
            print("   Corrige los errores antes de continuar.")
        
        return {
            "version": self.version,
            "ready": len(self.errors) == 0,
            "checks_passed": len(self.checks),
            "warnings": len(self.warnings),
            "errors": len(self.errors),
            "error_list": self.errors,
            "warning_list": self.warnings,
            "timestamp": datetime.now().isoformat()
        }


def main():
    """Función principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Release Checklist para Claw-Litle")
    parser.add_argument("--version", "-v", help="Versión a verificar")
    parser.add_argument("--json", action="store_true", help="Salida en formato JSON")
    
    args = parser.parse_args()
    
    checker = ReleaseChecker(version=args.version)
    result = checker.run_all_checks()
    
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0 if result["ready"] else 1)
    else:
        sys.exit(0 if result["ready"] else 1)


if __name__ == "__main__":
    main()