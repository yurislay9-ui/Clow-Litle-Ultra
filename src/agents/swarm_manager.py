"""
Claw-Litle 1.0
swarm_manager.py - Gestor de Enjambre Multi-Agente

Orquesta búsquedas paralelas con múltiples agentes (Google, Bing, Brave, Semantic)
con Thermal Guard para limitar ejecución según temperatura del sistema.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Estado de un agente."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class AgentResult:
    """Resultado de un agente individual."""
    agent_name: str
    results: List[Dict] = field(default_factory=list)
    status: AgentStatus = AgentStatus.IDLE
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    result_count: int = 0


@dataclass
class SwarmConfig:
    """Configuración del swarm manager."""
    max_parallel_agents: int = 2  # Máx 2 por Thermal Guard
    timeout_per_agent_seconds: int = 15
    min_results_required: int = 3
    deduplication_enabled: bool = True
    thermal_throttling: bool = True
    temp_threshold_warning: float = 70.0  # °C
    temp_threshold_critical: float = 85.0  # °C
    cooldown_seconds: int = 30


class ThermalGuard:
    """
    Guardian Térmico - Limita ejecución según temperatura.
    
    Niveles:
    - Normal (<70°C): 2 agentes paralelos
    - Warning (70-85°C): 1 agente paralelo
    - Critical (>85°C): Pausa 30s
    """
    
    def __init__(self, config: SwarmConfig = None):
        self.config = config or SwarmConfig()
        self._temp_history: List[float] = []
        self._last_critical_pause = 0.0
        self._is_paused = False
    
    def get_system_temp(self) -> float:
        """
        Obtiene temperatura del sistema.
        Intenta leer de /sys/class/thermal/, sino simula.
        """
        try:
            # Intentar leer temperatura real en Termux
            import os
            thermal_paths = [
                "/sys/class/thermal/thermal_zone0/temp",
                "/sys/class/hwmon/hwmon0/temp1_input",
            ]
            for path in thermal_paths:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        temp = int(f.read().strip()) / 1000.0
                        return temp
        except Exception:
            pass
        
        # Simular temperatura basada en carga reciente
        if self._temp_history:
            return sum(self._temp_history[-5:]) / min(len(self._temp_history), 5)
        return 45.0  # Temperatura base simulada
    
    def record_temp(self, temp: float):
        """Registra temperatura en historial."""
        self._temp_history.append(temp)
        if len(self._temp_history) > 20:
            self._temp_history = self._temp_history[-20:]
    
    def should_pause(self) -> bool:
        """Verifica si debe pausar por temperatura crítica."""
        if self._is_paused:
            if time.time() - self._last_critical_pause > self.config.cooldown_seconds:
                self._is_paused = False
                return False
            return True
        
        temp = self.get_system_temp()
        self.record_temp(temp)
        
        if temp > self.config.temp_threshold_critical:
            self._is_paused = True
            self._last_critical_pause = time.time()
            logger.warning(f"🌡️ Temperatura crítica: {temp:.1f}°C - Pausando {self.config.cooldown_seconds}s")
            return True
        
        return False
    
    def get_max_agents(self) -> int:
        """Obtiene máximo de agentes según temperatura."""
        temp = self.get_system_temp()
        self.record_temp(temp)
        
        if temp > self.config.temp_threshold_critical:
            return 0  # Pausar completamente
        elif temp > self.config.temp_threshold_warning:
            return 1  # Solo 1 agente
        else:
            return self.config.max_parallel_agents
    
    def get_thermal_status(self) -> Dict:
        """Obtiene estado térmico actual."""
        temp = self.get_system_temp()
        self.record_temp(temp)
        
        if temp > self.config.temp_threshold_critical:
            status = "critical"
        elif temp > self.config.temp_threshold_warning:
            status = "warning"
        else:
            status = "normal"
        
        return {
            "temperature_celsius": temp,
            "status": status,
            "max_agents": self.get_max_agents(),
            "is_paused": self._is_paused,
            "throttling": status != "normal"
        }


class SwarmManager:
    """
    Gestor de Enjambre Multi-Agente.
    
    Orquesta búsquedas paralelas con:
    - Google Searcher
    - Bing Searcher
    - Brave Searcher
    - Semantic Searcher
    
    Con consolidación de resultados y thermal throttling.
    """
    
    def __init__(self, config: SwarmConfig = None):
        self.config = config or SwarmConfig()
        self.thermal_guard = ThermalGuard(self.config)
        self._agent_status: Dict[str, AgentStatus] = {}
        self._total_searches = 0
        self._total_results = 0
        logger.info("SwarmManager inicializado")
    
    async def search(
        self,
        query: str,
        agents: List[str] = None,
        max_results_per_agent: int = 5
    ) -> Dict[str, Any]:
        """
        Ejecuta búsqueda multi-agente en paralelo.
        
        Args:
            query: Término de búsqueda
            agents: Lista de agentes a usar (default: todos disponibles)
            max_results_per_agent: Máx resultados por agente
        
        Returns:
            Dict con resultados consolidados
        """
        start_time = time.time()
        
        # Verificar thermal guard
        if self.thermal_guard.should_pause():
            return {
                "success": False,
                "error": "Thermal throttling activo - sistema en pausa",
                "thermal_status": self.thermal_guard.get_thermal_status(),
                "results": [],
                "execution_time_ms": 0
            }
        
        # Seleccionar agentes
        available_agents = agents or ["google", "bing", "brave", "semantic"]
        max_agents = self.thermal_guard.get_max_agents()
        
        if max_agents == 0:
            return {
                "success": False,
                "error": "Temperatura crítica - no se pueden ejecutar agentes",
                "thermal_status": self.thermal_guard.get_thermal_status(),
                "results": [],
                "execution_time_ms": 0
            }
        
        # Limitar agentes según thermal guard
        selected_agents = available_agents[:max_agents]
        
        if len(selected_agents) > max_agents:
            logger.info(f"Thermal throttling: limitando a {max_agents} agentes")
        
        # Crear tareas asíncronas
        tasks = []
        for agent_name in selected_agents:
            self._agent_status[agent_name] = AgentStatus.RUNNING
            tasks.append(self._run_agent(agent_name, query, max_results_per_agent))
        
        # Ejecutar en paralelo (limitado por thermal guard)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Consolidar resultados
        consolidated = self._consolidate_results(results, selected_agents)
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        self._total_searches += 1
        self._total_results += len(consolidated["results"])
        
        return {
            "success": True,
            "query": query,
            "agents_used": selected_agents,
            "results": consolidated["results"],
            "total_results": len(consolidated["results"]),
            "deduplicated": consolidated["deduplicated"],
            "execution_time_ms": elapsed_ms,
            "thermal_status": self.thermal_guard.get_thermal_status()
        }
    
    async def _run_agent(
        self,
        agent_name: str,
        query: str,
        max_results: int
    ) -> AgentResult:
        """Ejecuta un agente individual con timeout."""
        start_time = time.time()
        result = AgentResult(agent_name=agent_name)
        
        try:
            # Timeout por agente
            agent_func = self._get_agent_function(agent_name)
            
            if agent_func:
                result.results = await asyncio.wait_for(
                    agent_func(query, max_results),
                    timeout=self.config.timeout_per_agent_seconds
                )
                result.status = AgentStatus.COMPLETED
                result.result_count = len(result.results)
            else:
                result.status = AgentStatus.FAILED
                result.error = f"Agente '{agent_name}' no disponible"
                
        except asyncio.TimeoutError:
            result.status = AgentStatus.TIMEOUT
            result.error = f"Timeout después de {self.config.timeout_per_agent_seconds}s"
            logger.warning(f"Agente {agent_name}超时")
            
        except Exception as e:
            result.status = AgentStatus.FAILED
            result.error = str(e)
            logger.error(f"Error en agente {agent_name}: {e}")
        
        finally:
            result.execution_time_ms = (time.time() - start_time) * 1000
            self._agent_status[agent_name] = result.status
        
        return result
    
    def _get_agent_function(self, agent_name: str):
        """Obtiene función del agente por nombre."""
        agents = {
            "google": self._google_search,
            "bing": self._bing_search,
            "brave": self._brave_search,
            "semantic": self._semantic_search,
        }
        return agents.get(agent_name)
    
    async def _google_search(self, query: str, max_results: int) -> List[Dict]:
        """Búsqueda en Google (simulada - requiere API key)."""
        # En producción: usar google-search-results o similar
        logger.info(f"[Google] Buscando: {query[:50]}...")
        await asyncio.sleep(0.5)  # Simular latencia
        return self._generate_mock_results("Google", query, max_results)
    
    async def _bing_search(self, query: str, max_results: int) -> List[Dict]:
        """Búsqueda en Bing (simulada - requiere API key)."""
        logger.info(f"[Bing] Buscando: {query[:50]}...")
        await asyncio.sleep(0.3)
        return self._generate_mock_results("Bing", query, max_results)
    
    async def _brave_search(self, query: str, max_results: int) -> List[Dict]:
        """Búsqueda en Brave (simulada - requiere API key)."""
        logger.info(f"[Brave] Buscando: {query[:50]}...")
        await asyncio.sleep(0.4)
        return self._generate_mock_results("Brave", query, max_results)
    
    async def _semantic_search(self, query: str, max_results: int) -> List[Dict]:
        """Búsqueda semántica local (sqlite-vec)."""
        logger.info(f"[Semantic] Buscando: {query[:50]}...")
        await asyncio.sleep(0.2)
        return self._generate_mock_results("Semantic", query, max_results)
    
    def _generate_mock_results(self, source: str, query: str, count: int) -> List[Dict]:
        """Genera resultados mock para testing."""
        results = []
        for i in range(min(count, 5)):
            results.append({
                "title": f"Resultado {source} #{i+1} para '{query[:30]}'",
                "url": f"https://{source.lower()}.com/result/{i+1}",
                "snippet": f"Snippet de {source} para la búsqueda: {query[:50]}...",
                "source": source,
                "relevance_score": max(0.5, 1.0 - (i * 0.15)),
                "timestamp": time.time()
            })
        return results
    
    def _consolidate_results(
        self,
        agent_results: List[AgentResult],
        agents_used: List[str]
    ) -> Dict:
        """
        Consolida resultados de múltiples agentes.
        
        - Elimina duplicados por URL
        - Ordena por relevancia
        - Mantiene metadatos por fuente
        """
        all_results = []
        seen_urls = set()
        
        for result in agent_results:
            if result.status == AgentStatus.COMPLETED:
                for item in result.results:
                    url = item.get("url", "")
                    if self.config.deduplication_enabled:
                        if url not in seen_urls:
                            seen_urls.add(url)
                            all_results.append(item)
                    else:
                        all_results.append(item)
        
        # Ordenar por relevancia
        all_results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        # Estadísticas por fuente
        source_stats = {}
        for result in agent_results:
            source_stats[result.agent_name] = {
                "status": result.status.value,
                "results": result.result_count,
                "time_ms": result.execution_time_ms,
                "error": result.error
            }
        
        return {
            "results": all_results,
            "deduplicated": len(all_results),
            "source_stats": source_stats,
            "agents_used": agents_used
        }
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas del swarm."""
        return {
            "total_searches": self._total_searches,
            "total_results": self._total_results,
            "thermal_status": self.thermal_guard.get_thermal_status(),
            "agent_status": {k: v.value for k, v in self._agent_status.items()},
            "config": {
                "max_parallel_agents": self.config.max_parallel_agents,
                "timeout_seconds": self.config.timeout_per_agent_seconds,
                "thermal_throttling": self.config.thermal_throttling
            }
        }
    
    def clear_status(self):
        """Limpia estado de agentes."""
        self._agent_status.clear()


# Función síncrona wrapper para compatibilidad
def search_sync(query: str, config: SwarmConfig = None) -> Dict:
    """
    Wrapper síncrono para search().
    Útil para integración con código no asíncrono.
    """
    manager = SwarmManager(config)
    return asyncio.run(manager.search(query))


if __name__ == "__main__":
    # Test rápido
    async def main():
        manager = SwarmManager()
        result = await manager.search("Python asyncio tutorial")
        print(f"Resultados: {result['total_results']}")
        print(f"Agentes usados: {result['agents_used']}")
        print(f"Tiempo: {result['execution_time_ms']:.1f}ms")
        print(f"Thermal: {result['thermal_status']}")
    
    asyncio.run(main())