"""
Claw-Litle 1.0
__main__.py - Punto de entrada principal

Inicializa todos los componentes y lanza la interfaz de terminal.
"""

import sys
import logging
import tomllib
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.logging import RichHandler
from rich.prompt import Prompt
from rich.text import Text

from .environment_detector import EnvironmentDetector
from .gateway import Gateway, SecurityConfig, Request
from .engine import HybridEngine
from .router import Router, RouterConfig

# Consola Rich para terminal bonita
console = Console()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, rich_tracebacks=True)]
)

logger = logging.getLogger("claw_lite")


class CLAWLiteApp:
    """
    Aplicación principal de Claw-Litle.
    
    Orquesta todos los componentes del sistema.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Inicializa la aplicación.
        
        Args:
            config_path: Ruta al archivo de configuración (opcional)
        """
        self.config_path = config_path or "src/config/defaults.toml"
        
        # 1. Detectar entorno
        console.print("[bold blue]🔍 Detectando entorno...[/bold blue]")
        self.env_detector = EnvironmentDetector()
        self.env_profile = self.env_detector.get_profile()
        console.print(f"[green]✓ Entorno: {self.env_profile['profile_name']}[/green]")
        
        # 2. Cargar configuración
        console.print("[bold blue]⚙️ Cargando configuración...[/bold blue]")
        self.config = self._load_config()
        console.print("[green]✓ Configuración cargada[/green]")
        
        # 3. Inicializar Gateway
        console.print("[bold blue]🔒 Inicializando Gateway...[/bold blue]")
        security_config = SecurityConfig.from_dict({
            "rate_limit_free": self.config.get("rate_limiting", {}).get("free_limit", 30),
            "rate_limit_pro": self.config.get("rate_limiting", {}).get("pro_limit", 1000),
            "rate_limit_window": self.config.get("rate_limiting", {}).get("window_seconds", 3600),
            "max_query_length": self.env_profile.get("limits", {}).get("max_query_length", 1000),
            "forbidden_patterns": self.config.get("security", {}).get("forbidden_patterns", []),
            "allowed_imports": self.config.get("security", {}).get("allowed_imports", [])
        })
        self.gateway = Gateway(security_config)
        console.print("[green]✓ Gateway inicializado[/green]")
        
        # 4. Inicializar HybridEngine
        console.print("[bold blue]🧠 Inicializando Motor Híbrido...[/bold blue]")
        engine_config = self.config.get("motor_4_niveles", {})
        engine_config["short_circuit_threshold"] = self.config.get("engine", {}).get("short_circuit_threshold", 0.95)
        self.engine = HybridEngine(engine_config)
        console.print("[green]✓ Motor Híbrido inicializado[/green]")
        
        # 5. Inicializar Router
        console.print("[bold blue]🔀 Inicializando Router...[/bold blue]")
        router_config = RouterConfig(
            max_retries=3,
            timeout_seconds=self.env_profile.get("limits", {}).get("timeout_long_seconds", 30),
            enable_caching=True,
            cache_ttl_seconds=self.config.get("engine", {}).get("cache_ttl", 86400),
            fallback_to_search=True
        )
        self.router = Router(self.engine, self.gateway, router_config)
        console.print("[green]✓ Router inicializado[/green]")
        
        # Estado de la sesión
        self.user_id = "anonymous"
        self.running = False
        
        console.print("\n[bold green]✅ Claw-Litle 1.0 1.0 listo![/bold green]\n")
    
    def _load_config(self) -> dict:
        """
        Carga la configuración desde archivo TOML.
        
        Returns:
            Diccionario con la configuración
        """
        config_path = Path(self.config_path)
        
        if not config_path.exists():
            logger.warning(f"Archivo de configuración no encontrado: {config_path}")
            return {}
        
        try:
            with open(config_path, "rb") as f:
                return tomllib.load(f)
        except Exception as e:
            logger.error(f"Error cargando configuración: {e}")
            return {}
    
    def show_banner(self):
        """Muestra el banner de bienvenida."""
        banner = Text.from_markup("""
[bold cyan]
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║   ███████╗███████╗ ██████╗ ██╗  ██╗███████╗             ║
║   ██╔════╝╚══██╔══╝██╔═══██╗██║  ██║██╔════╝             ║
║   ███████╗   ██║   ██║   ██║███████║█████╗               ║
║   ╚════██║   ██║   ██║   ██║╚════██║╚════╝               ║
║   ███████║   ██║   ╚██████╔╝     ██║                     ║
║   ╚══════╝   ╚═╝    ╚═════╝      ╚═╝                     ║
║                                                          ║
║         U L T R A   P R O   3 . 0   " F É N I X "        ║
║                                                          ║
║   Sistema Operativo Agéntico Personal                    ║
║   100% LOCAL/OFFLINE - Optimizado para Termux ARM64      ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
[/bold cyan]""")
        console.print(Panel(banner, border_style="cyan"))
        
        # Información del entorno
        env_info = f"""
[bold]Entorno:[/bold] {self.env_profile['profile_name']}
[bold]Arquitectura:[/bold] {self.env_profile['environment']['arch']}
[bold]RAM Máx:[/bold] {self.env_profile['capabilities_detected']['max_memory_mb']}MB
[bold]Agentes Máx:[/bold] {self.env_profile['capabilities_detected']['max_concurrent_agents']}
[bold]ONNX:[/bold] {'✓' if self.env_profile['capabilities_detected']['supports_onnx'] else '✗'}
"""
        console.print(Panel(env_info, title="Información del Sistema", border_style="green"))
    
    def process_query(self, query: str) -> str:
        """
        Procesa una query del usuario.
        
        Args:
            query: Query del usuario
        
        Returns:
            Respuesta formateada
        """
        # Comandos especiales
        if query.lower().strip() in ["exit", "quit", "salir"]:
            self.running = False
            return "Saliendo de Claw-Litle. ¡Hasta pronto!"
        
        if query.lower().strip() == "status":
            return self._get_status()
        
        # Procesar a través del router
        try:
            result = self.router.route(query, self.user_id)
            
            if result.success:
                if result.action == "respond":
                    return str(result.data)
                elif result.action == "dispatch":
                    return f"🔄 Procesando: {result.intent}..."
                else:
                    return f"✅ {result.data or 'Completado'}"
            else:
                return f"❌ Error: {result.error}"
                
        except Exception as e:
            logger.error(f"Error procesando query: {e}")
            return f"❌ Error interno: {str(e)}"
    
    def _get_status(self) -> str:
        """Obtiene el estado del sistema."""
        stats = self.router.get_stats()
        engine_stats = self.engine.get_stats()
        
        status = f"""
[bold]Estado del Sistema:[/bold]

[green]✓ Gateway:[/green] {len(self.gateway.rate_limiter._requests)} usuarios activos
[green]✓ Engine:[/green] Niveles activos: {sum(1 for v in engine_stats['levels_enabled'].values() if v)}/4
[green]✓ Router:[/green] {stats['cache_size']} entradas en caché
[green]✓ Handlers:[/green] {stats['handlers_count']} registrados

[bold]Configuración:[/bold]
  Timeout: {stats['config']['timeout_seconds']}s
  Caché: {'activa' if stats['config']['enable_caching'] else 'desactivada'}
  Fallback: {'búsqueda' if stats['config']['fallback_to_search'] else 'mensaje'}
"""
        return status
    
    def run(self):
        """Ejecuta el loop principal de la aplicación."""
        self.running = True
        self.show_banner()
        
        console.print("\n[bold yellow]Escribe 'help' para ver comandos disponibles.[/bold yellow]\n")
        
        while self.running:
            try:
                # Prompt para input
                query = Prompt.ask("[bold cyan]:input[/bold cyan]")
                
                if not query.strip():
                    continue
                
                # Procesar query
                response = self.process_query(query)
                
                # Mostrar respuesta
                console.print(f"\n[bold magenta]:robot:[/bold magenta] {response}\n")
                
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrumpido. Escribe 'exit' para salir.[/yellow]")
            except EOFError:
                self.running = False
        
        console.print("\n[bold green]¡Gracias por usar Claw-Litle! 👋[/bold green]")


def main():
    """Función de entrada principal."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Claw-Litle 1.0 1.0 - Sistema Operativo Agéntico Personal"
    )
    parser.add_argument(
        "--config", 
        type=str, 
        default="src/config/defaults.toml",
        help="Ruta al archivo de configuración"
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Mostrar versión"
    )
    
    args = parser.parse_args()
    
    if args.version:
        console.print("[bold cyan]Claw-Litle 1.0 1.0[/bold cyan]")
        console.print("Versión: 1.0.0")
        console.print("Optimizado para Termux ARM64")
        return
    
    try:
        app = CLAWLiteApp(config_path=args.config)
        app.run()
    except Exception as e:
        console.print(f"[bold red]Error fatal:[/bold red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()