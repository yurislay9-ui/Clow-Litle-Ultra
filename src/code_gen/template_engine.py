"""
Claw-Litle 1.0
template_engine.py - Generador de Código basado en Plantillas

Genera código Python listo para usar a partir de plantillas predefinidas.
Plantillas optimizadas para Termux/ARM64.
"""

import os
import re
import logging
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Template:
    """Plantilla de código."""
    name: str
    description: str
    category: str
    content: str
    variables: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class GeneratedCode:
    """Código generado."""
    template_name: str
    code: str
    variables: Dict[str, str]
    file_path: Optional[str] = None


class TemplateEngine:
    """
    Motor de Plantillas.
    
    Carga plantillas desde archivos .template y reemplaza variables.
    Todas las plantillas son compatibles con Termux/ARM64.
    """
    
    def __init__(self, templates_dir: Optional[str] = None):
        if templates_dir:
            self.templates_dir = Path(templates_dir)
        else:
            # Ruta por defecto
            self.templates_dir = Path(__file__).parent.parent / "config" / "templates" / "python"
        
        self._templates: Dict[str, Template] = {}
        self._load_templates()
        logger.info(f"TemplateEngine inicializado con {len(self._templates)} plantillas")
    
    def _load_templates(self):
        """Carga todas las plantillas disponibles."""
        if not self.templates_dir.exists():
            logger.warning(f"Directorio de plantillas no existe: {self.templates_dir}")
            self._load_builtin_templates()
            return
        
        for file_path in self.templates_dir.glob("*.template"):
            try:
                template = self._parse_template_file(file_path)
                self._templates[template.name] = template
            except Exception as e:
                logger.error(f"Error cargando plantilla {file_path}: {e}")
        
        if not self._templates:
            logger.info("Cargando plantillas integradas")
            self._load_builtin_templates()
    
    def _parse_template_file(self, file_path: Path) -> Template:
        """Parsea un archivo de plantilla."""
        content = file_path.read_text()
        
        # Extraer metadatos del encabezado
        metadata = {}
        lines = content.splitlines()
        
        for i, line in enumerate(lines):
            if line.startswith("---"):
                break
            if "=" in line:
                key, value = line.split("=", 1)
                metadata[key.strip()] = value.strip()
        
        # Extraer variables
        variables = list(set(re.findall(r"\{\{(\w+)\}\}", content)))
        
        return Template(
            name=file_path.stem,
            description=metadata.get("description", ""),
            category=metadata.get("category", "general"),
            content=content,
            variables=variables,
            tags=metadata.get("tags", "").split(",") if "tags" in metadata else []
        )
    
    def _load_builtin_templates(self):
        """Carga plantillas integradas si no hay archivos disponibles."""
        builtin_templates = [
            Template(
                name="cli_app",
                description="Aplicación CLI básica",
                category="app",
                content="""
#!/usr/bin/env python3
\"\"\"
{{app_name}} - {{description}}
\"\"\"

import click
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.group()
def cli():
    \"\"\"{{app_name}} CLI\"\"\"
    pass

@cli.command()
@click.argument('name')
def hello(name):
    \"\"\"Saluda a alguien\"\"\"
    click.echo(f'Hola {name}!')

if __name__ == "__main__":
    cli()
""",
                variables=["app_name", "description"]
            ),
            Template(
                name="web_scraper",
                description="Web Scraper con requests y beautifulsoup",
                category="web",
                content="""
#!/usr/bin/env python3
\"\"\"
Web Scraper: {{target_site}}
\"\"\"

import requests
from bs4 import BeautifulSoup
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Android 14; Mobile; rv:125.0) Gecko/125.0 Firefox/125.0'
}

def scrape_page(url):
    \"\"\"Extrae datos de una página\"\"\"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # TODO: Extraer datos aquí
        
        return {
            'url': url,
            'title': soup.title.string if soup.title else '',
            'links': len(soup.find_all('a'))
        }
    except Exception as e:
        logger.error(f"Error scrapeando {url}: {e}")
        return None

if __name__ == "__main__":
    result = scrape_page("{{target_url}}")
    if result:
        print(f"Resultado: {result}")
""",
                variables=["target_site", "target_url"]
            ),
            Template(
                name="telegram_bot",
                description="Bot de Telegram",
                category="bot",
                content="""
#!/usr/bin/env python3
\"\"\"
Telegram Bot: {{bot_name}}
\"\"\"

import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="¡Hola! Soy {{bot_name}} 🤖"
    )

if __name__ == "__main__":
    application = ApplicationBuilder().token("{{bot_token}}").build()
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)
    application.run_polling()
""",
                variables=["bot_name", "bot_token"]
            )
        ]
        
        for template in builtin_templates:
            self._templates[template.name] = template
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """Lista todas las plantillas disponibles."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "category": t.category,
                "variables": t.variables,
                "tags": t.tags
            }
            for t in self._templates.values()
        ]
    
    def get_template(self, name: str) -> Optional[Template]:
        """Obtiene una plantilla por nombre."""
        return self._templates.get(name)
    
    def generate(self, template_name: str, variables: Dict[str, str]) -> Optional[GeneratedCode]:
        """
        Genera código a partir de una plantilla.
        
        Args:
            template_name: Nombre de la plantilla
            variables: Diccionario con valores para reemplazar variables
            
        Returns:
            GeneratedCode con el código generado o None
        """
        template = self._templates.get(template_name)
        if not template:
            logger.error(f"Plantilla '{template_name}' no encontrada")
            return None
        
        # Verificar que todas las variables están presentes
        missing_vars = [v for v in template.variables if v not in variables]
        if missing_vars:
            logger.error(f"Faltan variables para plantilla {template_name}: {missing_vars}")
            return None
        
        # Reemplazar variables
        code = template.content
        for var_name, var_value in variables.items():
            code = code.replace(f"{{{{{var_name}}}}}", var_value)
        
        return GeneratedCode(
            template_name=template_name,
            code=code.strip(),
            variables=variables
        )
    
    def generate_and_save(
        self,
        template_name: str,
        variables: Dict[str, str],
        output_path: str
    ) -> Optional[str]:
        """
        Genera código y lo guarda en un archivo.
        
        Args:
            template_name: Nombre de la plantilla
            variables: Diccionario de variables
            output_path: Ruta para guardar el archivo
            
        Returns:
            Ruta del archivo generado o None
        """
        generated = self.generate(template_name, variables)
        if not generated:
            return None
        
        try:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w') as f:
                f.write(generated.code)
            
            # Hacer ejecutable
            os.chmod(path, 0o755)
            
            generated.file_path = str(path)
            logger.info(f"Código generado en {path}")
            return str(path)
            
        except Exception as e:
            logger.error(f"Error guardando código en {output_path}: {e}")
            return None
    
    def search_templates(self, query: str) -> List[Template]:
        """Busca plantillas por nombre, descripción o tags."""
        query = query.lower()
        results = []
        
        for template in self._templates.values():
            if (query in template.name.lower() or
                query in template.description.lower() or
                any(query in tag.lower() for tag in template.tags)):
                results.append(template)
        
        return results


# Función helper para uso rápido
def generate_code(template_name: str, variables: Dict[str, str]) -> Optional[str]:
    """Genera código rápidamente."""
    engine = TemplateEngine()
    result = engine.generate(template_name, variables)
    return result.code if result else None


if __name__ == "__main__":
    # Test rápido
    engine = TemplateEngine()
    print(f"Plantillas disponibles: {len(engine.list_templates())}")
    
    for t in engine.list_templates():
        print(f"\n📄 {t['name']}: {t['description']}")
        print(f"  Variables: {t['variables']}")
    
    # Generar ejemplo
    code = generate_code("cli_app", {
        "app_name": "MiApp",
        "description": "Aplicación de prueba"
    })
    
    if code:
        print("\n✅ Código generado:")
        print(code[:500] + "..." if len(code) > 500 else code)