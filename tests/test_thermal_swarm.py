#!/usr/bin/env python3
"""
Tests para Thermal Guard y Swarm Manager.
Cubre: control térmico, límites de agentes concurrentes, graceful degradation.
"""

import pytest
import time
import asyncio
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List


class MockAgent:
    """Agente mock para testing."""
    def __init__(self, name: str, execution_time: float = 0.1):
        self.name = name
        self.execution_time = execution_time
        self.executed = False
    
    async def execute(self, query: str) -> dict:
        """Ejecuta el agente (simulado)."""
        await asyncio.sleep(self.execution_time)
        self.executed = True
        return {
            "agent": self.name,
            "query": query,
            "results": [f"Resultado de {self.name}"],
            "success": True
        }


class ThermalGuard:
    """Implementación simplificada de Thermal Guard para testing."""
    def __init__(self, threshold: float = 70.0, critical_threshold: float = 85.0):
        self.threshold = threshold
        self.critical_threshold = critical_threshold
        self.current_temp = 45.0  # Temperatura inicial simulada
    
    def get_temperature(self) -> float:
        """Obtiene temperatura actual (simulada)."""
        return self.current_temp
    
    def set_temperature(self, temp: float):
        """Establece temperatura para testing."""
        self.current_temp = temp
    
    def should_throttle(self) -> bool:
        """Determina si debe aplicar throttling."""
        return self.current_temp > self.threshold
    
    def should_pause(self) -> bool:
        """Determina si debe pausar completamente."""
        return self.current_temp > self.critical_threshold
    
    def get_max_agents(self) -> int:
        """Obtiene máximo de agentes permitidos según temperatura."""
        if self.should_pause():
            return 0
        elif self.should_throttle():
            return 1
        else:
            return 2


class SwarmManager:
    """Implementación simplificada de Swarm Manager para testing."""
    def __init__(self, thermal_guard: ThermalGuard):
        self.thermal_guard = thermal_guard
        self.agents: Dict[str, MockAgent] = {}
        self.execution_log: List[dict] = []
    
    def add_agent(self, name: str, agent: MockAgent):
        """Agrega un agente al swarm."""
        self.agents[name] = agent
    
    async def execute_swarm(self, query: str, max_agents: int = None) -> List[dict]:
        """Ejecuta swarm con control térmico."""
        if max_agents is None:
            max_agents = self.thermal_guard.get_max_agents()
        
        if max_agents == 0:
            return []  # Pausado por temperatura crítica
        
        # Seleccionar agentes a ejecutar (máximo max_agents)
        agents_to_run = list(self.agents.values())[:max_agents]
        
        # Ejecutar en paralelo (pero limitado por thermal guard)
        tasks = [agent.execute(query) for agent in agents_to_run]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log de ejecución
        self.execution_log.append({
            "timestamp": time.time(),
            "query": query,
            "agents_used": len(agents_to_run),
            "temperature": self.thermal_guard.get_temperature(),
            "results_count": len(results)
        })
        
        return results


class TestThermalGuard:
    """Tests para Thermal Guard."""
    
    def setup_method(self):
        self.thermal_guard = ThermalGuard(threshold=70.0, critical_threshold=85.0)
    
    def test_initial_temperature(self):
        """Test que temperatura inicial es correcta."""
        assert self.thermal_guard.get_temperature() == 45.0
    
    def test_set_temperature(self):
        """Test que puede establecer temperatura."""
        self.thermal_guard.set_temperature(60.0)
        assert self.thermal_guard.get_temperature() == 60.0
    
    def test_no_throttle_at_normal_temp(self):
        """Test que no hay throttle a temperatura normal."""
        self.thermal_guard.set_temperature(50.0)
        assert not self.thermal_guard.should_throttle()
        assert not self.thermal_guard.should_pause()
    
    def test_throttle_at_high_temp(self):
        """Test que hay throttle a temperatura alta."""
        self.thermal_guard.set_temperature(75.0)
        assert self.thermal_guard.should_throttle()
        assert not self.thermal_guard.should_pause()
    
    def test_pause_at_critical_temp(self):
        """Test que pausa a temperatura crítica."""
        self.thermal_guard.set_temperature(90.0)
        assert self.thermal_guard.should_throttle()
        assert self.thermal_guard.should_pause()
    
    def test_max_agents_at_normal_temp(self):
        """Test que permite 2 agentes a temperatura normal."""
        self.thermal_guard.set_temperature(50.0)
        assert self.thermal_guard.get_max_agents() == 2
    
    def test_max_agents_at_high_temp(self):
        """Test que limita a 1 agente a temperatura alta."""
        self.thermal_guard.set_temperature(75.0)
        assert self.thermal_guard.get_max_agents() == 1
    
    def test_max_agents_at_critical_temp(self):
        """Test que limita a 0 agentes a temperatura crítica."""
        self.thermal_guard.set_temperature(90.0)
        assert self.thermal_guard.get_max_agents() == 0
    
    def test_threshold_boundary(self):
        """Test límite exacto del threshold."""
        self.thermal_guard.set_temperature(70.0)
        assert not self.thermal_guard.should_throttle()  # Iguala threshold, no supera
        
        self.thermal_guard.set_temperature(70.1)
        assert self.thermal_guard.should_throttle()  # Supera threshold


class TestSwarmManager:
    """Tests para Swarm Manager."""
    
    def setup_method(self):
        self.thermal_guard = ThermalGuard()
        self.swarm = SwarmManager(self.thermal_guard)
    
    def test_add_agent(self):
        """Test que puede agregar agentes."""
        agent = MockAgent("test_agent")
        self.swarm.add_agent("test", agent)
        
        assert "test" in self.swarm.agents
        assert self.swarm.agents["test"] == agent
    
    @pytest.mark.asyncio
    async def test_execute_swarm_with_agents(self):
        """Test ejecución de swarm con agentes."""
        # Agregar agentes
        agent1 = MockAgent("agent1", execution_time=0.1)
        agent2 = MockAgent("agent2", execution_time=0.1)
        self.swarm.add_agent("a1", agent1)
        self.swarm.add_agent("a2", agent2)
        
        # Ejecutar swarm
        results = await self.swarm.execute_swarm("test query")
        
        assert len(results) == 2
        assert agent1.executed
        assert agent2.executed
    
    @pytest.mark.asyncio
    async def test_execute_swarm_respects_thermal_limit(self):
        """Test que swarm respeta límite térmico."""
        # Temperatura alta -> máximo 1 agente
        self.thermal_guard.set_temperature(75.0)
        
        # Agregar 3 agentes
        for i in range(3):
            self.swarm.add_agent(f"agent{i}", MockAgent(f"agent{i}"))
        
        # Ejecutar swarm
        results = await self.swarm.execute_swarm("test query")
        
        # Solo debería ejecutar 1 agente (límite térmico)
        assert len(results) == 1
    
    @pytest.mark.asyncio
    async def test_execute_swarm_at_critical_temp(self):
        """Test que swarm no ejecuta a temperatura crítica."""
        # Temperatura crítica -> 0 agentes
        self.thermal_guard.set_temperature(90.0)
        
        # Agregar agentes
        agent = MockAgent("agent1")
        self.swarm.add_agent("a1", agent)
        
        # Ejecutar swarm
        results = await self.swarm.execute_swarm("test query")
        
        # No debería ejecutar nada
        assert len(results) == 0
        assert not agent.executed
    
    @pytest.mark.asyncio
    async def test_execution_log(self):
        """Test que se registra la ejecución."""
        agent = MockAgent("test_agent")
        self.swarm.add_agent("test", agent)
        
        await self.swarm.execute_swarm("test query")
        
        assert len(self.swarm.execution_log) == 1
        log_entry = self.swarm.execution_log[0]
        
        assert log_entry["query"] == "test query"
        assert log_entry["agents_used"] == 1
        assert "timestamp" in log_entry
        assert "temperature" in log_entry
    
    @pytest.mark.asyncio
    async def test_multiple_swarm_executions(self):
        """Test múltiples ejecuciones de swarm."""
        agent = MockAgent("test_agent")
        self.swarm.add_agent("test", agent)
        
        # Ejecutar 3 veces
        for i in range(3):
            await self.swarm.execute_swarm(f"query {i}")
        
        assert len(self.swarm.execution_log) == 3


class TestThermalSwarmIntegration:
    """Tests de integración Thermal Guard + Swarm Manager."""
    
    def setup_method(self):
        self.thermal_guard = ThermalGuard()
        self.swarm = SwarmManager(self.thermal_guard)
        
        # Agregar varios agentes
        for i in range(5):
            self.swarm.add_agent(f"agent{i}", MockAgent(f"agent{i}", execution_time=0.05))
    
    @pytest.mark.asyncio
    async def test_dynamic_throttling(self):
        """Test throttling dinámico según temperatura."""
        # Temperatura normal -> 2 agentes
        self.thermal_guard.set_temperature(50.0)
        results = await self.swarm.execute_swarm("query1")
        assert len(results) == 2
        
        # Subir temperatura -> 1 agente
        self.thermal_guard.set_temperature(75.0)
        results = await self.swarm.execute_swarm("query2")
        assert len(results) == 1
        
        # Temperatura crítica -> 0 agentes
        self.thermal_guard.set_temperature(90.0)
        results = await self.swarm.execute_swarm("query3")
        assert len(results) == 0
        
        # Bajar temperatura -> vuelve a 2 agentes
        self.thermal_guard.set_temperature(45.0)
        results = await self.swarm.execute_swarm("query4")
        assert len(results) == 2
    
    @pytest.mark.asyncio
    async def test_graceful_degradation(self):
        """Test degradación gradual con temperatura."""
        temperatures = [45.0, 65.0, 75.0, 85.0, 95.0]
        expected_agents = [2, 2, 1, 0, 0]
        
        for temp, expected in zip(temperatures, expected_agents):
            self.thermal_guard.set_temperature(temp)
            results = await self.swarm.execute_swarm(f"query at {temp}°C")
            assert len(results) == expected, f"Fallo a {temp}°C: esperado {expected}, obtenido {len(results)}"
    
    @pytest.mark.asyncio
    async def test_recovery_after_cooling(self):
        """Test recuperación después de enfriamiento."""
        # Calentar a crítico
        self.thermal_guard.set_temperature(95.0)
        results = await self.swarm.execute_swarm("hot query")
        assert len(results) == 0
        
        # Enfriar gradualmente
        self.thermal_guard.set_temperature(75.0)
        results = await self.swarm.execute_swarm("warm query")
        assert len(results) == 1
        
        # Enfriar completamente
        self.thermal_guard.set_temperature(40.0)
        results = await self.swarm.execute_swarm("cool query")
        assert len(results) == 2
    
    @pytest.mark.asyncio
    async def test_concurrent_execution_with_thermal_control(self):
        """Test ejecución concurrente con control térmico."""
        # Temperatura que permite 2 agentes
        self.thermal_guard.set_temperature(60.0)
        
        # Ejecutar múltiples queries concurrentes
        queries = [f"query{i}" for i in range(5)]
        tasks = [self.swarm.execute_swarm(q) for q in queries]
        all_results = await asyncio.gather(*tasks)
        
        # Cada query debería obtener 2 resultados (límite térmico)
        for results in all_results:
            assert len(results) == 2


class TestEdgeCases:
    """Tests para casos borde."""
    
    def setup_method(self):
        self.thermal_guard = ThermalGuard()
        self.swarm = SwarmManager(self.thermal_guard)
    
    @pytest.mark.asyncio
    async def test_empty_swarm(self):
        """Test swarm sin agentes."""
        results = await self.swarm.execute_swarm("test query")
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_single_agent_swarm(self):
        """Test swarm con un solo agente."""
        agent = MockAgent("solo_agent")
        self.swarm.add_agent("solo", agent)
        
        results = await self.swarm.execute_swarm("test query")
        assert len(results) == 1
        assert agent.executed
    
    @pytest.mark.asyncio
    async def test_agent_failure_handling(self):
        """Test manejo de fallo de agente."""
        # Agente que falla
        failing_agent = MockAgent("failing_agent")
        failing_agent.execute = AsyncMock(side_effect=Exception("Agent failed"))
        
        self.swarm.add_agent("fail", failing_agent)
        
        # No debería colapsar todo el swarm
        results = await self.swarm.execute_swarm("test query")
        # El resultado debería incluir la excepción
        assert len(results) == 1
        assert isinstance(results[0], Exception)
    
    def test_negative_temperature(self):
        """Test temperatura negativa (caso extremo)."""
        self.thermal_guard.set_temperature(-10.0)
        assert not self.thermal_guard.should_throttle()
        assert self.thermal_guard.get_max_agents() == 2
    
    def test_very_high_temperature(self):
        """Test temperatura muy alta (caso extremo)."""
        self.thermal_guard.set_temperature(200.0)
        assert self.thermal_guard.should_throttle()
        assert self.thermal_guard.should_pause()
        assert self.thermal_guard.get_max_agents() == 0


# Helper para async mock
class AsyncMock(Mock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)