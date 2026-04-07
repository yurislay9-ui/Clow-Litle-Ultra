"""
Claw-Litle 1.0
test_swarm_manager.py - Tests para Swarm Manager y Thermal Guard

Tests exhaustivos para el gestor de enjambre multi-agente.
"""

import pytest
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.agents.swarm_manager import (
    SwarmManager,
    SwarmConfig,
    ThermalGuard,
    AgentStatus,
    AgentResult,
    search_sync
)


class TestAgentStatus:
    """Tests para el enum AgentStatus."""
    
    def test_agent_status_values(self):
        """Test que todos los estados existen."""
        assert AgentStatus.IDLE.value == "idle"
        assert AgentStatus.RUNNING.value == "running"
        assert AgentStatus.COMPLETED.value == "completed"
        assert AgentStatus.FAILED.value == "failed"
        assert AgentStatus.TIMEOUT.value == "timeout"


class TestAgentResult:
    """Tests para la dataclass AgentResult."""
    
    def test_agent_result_default_values(self):
        """Test valores por defecto."""
        result = AgentResult(agent_name="test")
        assert result.agent_name == "test"
        assert result.results == []
        assert result.status == AgentStatus.IDLE
        assert result.error is None
        assert result.execution_time_ms == 0.0
        assert result.result_count == 0
    
    def test_agent_result_with_values(self):
        """Test con valores personalizados."""
        result = AgentResult(
            agent_name="google",
            results=[{"title": "Test"}],
            status=AgentStatus.COMPLETED,
            error=None,
            execution_time_ms=100.5,
            result_count=1
        )
        assert result.agent_name == "google"
        assert len(result.results) == 1
        assert result.status == AgentStatus.COMPLETED
        assert result.execution_time_ms == 100.5


class TestSwarmConfig:
    """Tests para la dataclass SwarmConfig."""
    
    def test_swarm_config_default_values(self):
        """Test valores por defecto."""
        config = SwarmConfig()
        assert config.max_parallel_agents == 2
        assert config.timeout_per_agent_seconds == 15
        assert config.min_results_required == 3
        assert config.deduplication_enabled is True
        assert config.thermal_throttling is True
        assert config.temp_threshold_warning == 70.0
        assert config.temp_threshold_critical == 85.0
        assert config.cooldown_seconds == 30
    
    def test_swarm_config_custom_values(self):
        """Test con valores personalizados."""
        config = SwarmConfig(
            max_parallel_agents=1,
            timeout_per_agent_seconds=10,
            thermal_throttling=False
        )
        assert config.max_parallel_agents == 1
        assert config.timeout_per_agent_seconds == 10
        assert config.thermal_throttling is False


class TestThermalGuard:
    """Tests para ThermalGuard."""
    
    def test_thermal_guard_initialization(self):
        """Test inicialización de ThermalGuard."""
        guard = ThermalGuard()
        assert guard.config is not None
        assert guard._is_paused is False
        assert len(guard._temp_history) == 0
    
    def test_thermal_guard_get_system_temp_default(self):
        """Test temperatura por defecto (simulada)."""
        guard = ThermalGuard()
        temp = guard.get_system_temp()
        assert temp == 45.0  # Temperatura base simulada
    
    def test_thermal_guard_record_temp(self):
        """Test registro de temperatura."""
        guard = ThermalGuard()
        guard.record_temp(50.0)
        guard.record_temp(55.0)
        assert len(guard._temp_history) == 2
        assert guard._temp_history[-1] == 55.0
    
    def test_thermal_guard_temp_history_limit(self):
        """Test límite del historial de temperatura."""
        guard = ThermalGuard()
        for i in range(25):
            guard.record_temp(40.0 + i)
        assert len(guard._temp_history) <= 20
    
    def test_thermal_guard_should_not_pause_normal(self):
        """Test no pausa en temperatura normal."""
        guard = ThermalGuard()
        assert guard.should_pause() is False
    
    def test_thermal_guard_get_max_agents_normal(self):
        """Test máx agentes en temperatura normal."""
        guard = ThermalGuard()
        assert guard.get_max_agents() == 2
    
    def test_thermal_guard_get_thermal_status_normal(self):
        """Test estado térmico normal."""
        guard = ThermalGuard()
        status = guard.get_thermal_status()
        assert status["status"] == "normal"
        assert status["max_agents"] == 2
        assert status["is_paused"] is False
        assert status["throttling"] is False
    
    def test_thermal_guard_high_temp_simulation(self):
        """Test comportamiento con temperatura alta simulada."""
        guard = ThermalGuard()
        # Simular temperatura alta añadiendo al historial
        for _ in range(5):
            guard.record_temp(75.0)
        
        # La temperatura simulada debería ser alta
        status = guard.get_thermal_status()
        # Depende de la implementación, pero con temp base 45 y historial 75
        # el promedio debería ser intermedio
        assert status["temperature_celsius"] >= 45.0


class TestSwarmManagerInitialization:
    """Tests para inicialización de SwarmManager."""
    
    def test_swarm_manager_init_default(self):
        """Test inicialización por defecto."""
        manager = SwarmManager()
        assert manager.config is not None
        assert manager.thermal_guard is not None
        assert manager._total_searches == 0
        assert manager._total_results == 0
    
    def test_swarm_manager_init_custom_config(self):
        """Test inicialización con config personalizada."""
        config = SwarmConfig(max_parallel_agents=1)
        manager = SwarmManager(config)
        assert manager.config.max_parallel_agents == 1


class TestSwarmManagerSearch:
    """Tests para búsqueda del SwarmManager."""
    
    @pytest.mark.asyncio
    async def test_swarm_search_basic(self):
        """Test búsqueda básica."""
        manager = SwarmManager()
        result = await manager.search("Python tutorial")
        
        assert result["success"] is True
        assert result["query"] == "Python tutorial"
        assert "results" in result
        assert "agents_used" in result
        assert "execution_time_ms" in result
        assert "thermal_status" in result
    
    @pytest.mark.asyncio
    async def test_swarm_search_with_specific_agents(self):
        """Test búsqueda con agentes específicos."""
        manager = SwarmManager()
        result = await manager.search("test", agents=["google", "bing"])
        
        assert result["success"] is True
        assert set(result["agents_used"]) <= {"google", "bing"}
    
    @pytest.mark.asyncio
    async def test_swarm_search_deduplication(self):
        """Test deduplicación de resultados."""
        manager = SwarmManager(SwarmConfig(deduplication_enabled=True))
        result = await manager.search("test query")
        
        # Verificar que hay resultados
        assert len(result["results"]) > 0
        
        # Verificar que no hay URLs duplicadas
        urls = [r["url"] for r in result["results"]]
        assert len(urls) == len(set(urls))
    
    @pytest.mark.asyncio
    async def test_swarm_search_results_sorted_by_relevance(self):
        """Test que resultados están ordenados por relevancia."""
        manager = SwarmManager()
        result = await manager.search("test")
        
        if len(result["results"]) > 1:
            scores = [r.get("relevance_score", 0) for r in result["results"]]
            assert scores == sorted(scores, reverse=True)
    
    @pytest.mark.asyncio
    async def test_swarm_search_empty_query(self):
        """Test búsqueda con query vacía."""
        manager = SwarmManager()
        result = await manager.search("")
        
        assert result["success"] is True  # La búsqueda puede ser vacía pero exitosa
    
    @pytest.mark.asyncio
    async def test_swarm_search_thermal_status_included(self):
        """Test que estado térmico está incluido."""
        manager = SwarmManager()
        result = await manager.search("test")
        
        thermal = result["thermal_status"]
        assert "temperature_celsius" in thermal
        assert "status" in thermal
        assert "max_agents" in thermal


class TestSwarmManagerStats:
    """Tests para estadísticas del SwarmManager."""
    
    def test_swarm_manager_get_stats_initial(self):
        """Test estadísticas iniciales."""
        manager = SwarmManager()
        stats = manager.get_stats()
        
        assert stats["total_searches"] == 0
        assert stats["total_results"] == 0
        assert "thermal_status" in stats
        assert "config" in stats
    
    @pytest.mark.asyncio
    async def test_swarm_manager_stats_after_search(self):
        """Test estadísticas después de búsqueda."""
        manager = SwarmManager()
        await manager.search("test")
        
        stats = manager.get_stats()
        assert stats["total_searches"] == 1
        assert stats["total_results"] > 0
    
    def test_swarm_manager_clear_status(self):
        """Test limpieza de estado."""
        manager = SwarmManager()
        manager._agent_status["google"] = AgentStatus.COMPLETED
        manager.clear_status()
        assert len(manager._agent_status) == 0


class TestSearchSync:
    """Tests para la función síncrona search_sync."""
    
    def test_search_sync_basic(self):
        """Test búsqueda síncrona básica."""
        result = search_sync("Python tutorial")
        
        assert result["success"] is True
        assert result["query"] == "Python tutorial"
        assert "results" in result


class TestSwarmManagerEdgeCases:
    """Tests para casos extremos."""
    
    @pytest.mark.asyncio
    async def test_swarm_search_very_long_query(self):
        """Test búsqueda con query muy larga."""
        manager = SwarmManager()
        long_query = "a" * 1000
        result = await manager.search(long_query)
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_swarm_search_special_characters(self):
        """Test búsqueda con caracteres especiales."""
        manager = SwarmManager()
        result = await manager.search("!@#$%^&*()")
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_swarm_search_unicode(self):
        """Test búsqueda con unicode."""
        manager = SwarmManager()
        result = await manager.search("🐍 Python 教程")
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_swarm_search_single_agent(self):
        """Test búsqueda con un solo agente."""
        manager = SwarmManager(SwarmConfig(max_parallel_agents=1))
        result = await manager.search("test")
        
        assert result["success"] is True
        assert len(result["agents_used"]) <= 1
    
    @pytest.mark.asyncio
    async def test_swarm_search_multiple_times(self):
        """Test múltiples búsquedas consecutivas."""
        manager = SwarmManager()
        
        for i in range(3):
            result = await manager.search(f"query {i}")
            assert result["success"] is True
        
        stats = manager.get_stats()
        assert stats["total_searches"] == 3


class TestThermalGuardEdgeCases:
    """Tests para casos extremos de ThermalGuard."""
    
    def test_thermal_guard_rapid_temperature_changes(self):
        """Test cambios rápidos de temperatura."""
        guard = ThermalGuard()
        
        # Simular cambios rápidos
        for temp in [40, 80, 45, 90, 50]:
            guard.record_temp(temp)
        
        # Debería manejar sin errores
        status = guard.get_thermal_status()
        assert "temperature_celsius" in status
    
    def test_thermal_guard_consistent_readings(self):
        """Test lecturas consistentes."""
        guard = ThermalGuard()
        
        temps = [guard.get_system_temp() for _ in range(5)]
        # Sin historial, todas deberían ser 45.0
        assert all(t == 45.0 for t in temps)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])