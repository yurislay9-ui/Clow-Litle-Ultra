#!/usr/bin/env python3
"""
Tests para el SwarmManager (Gestor de Enjambre de Agentes).
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import time


class TestSwarmManager:
    """Tests para SwarmManager."""
    
    def setup_method(self):
        """Configurar tests."""
        self.config = {
            "max_agents": 2,
            "thermal_throttling": True,
            "temp_threshold": 70
        }
    
    def test_manager_initialization(self):
        """Test que el manager se inicializa correctamente."""
        from src.agents.swarm_manager import SwarmManager
        
        manager = SwarmManager(self.config)
        assert manager is not None
        assert manager.max_agents == 2
    
    def test_thermal_guard_check(self):
        """Test verificación del thermal guard."""
        from src.agents.swarm_manager import SwarmManager
        
        manager = SwarmManager(self.config)
        
        # Simular temperatura normal
        with patch.object(manager, '_get_system_temp', return_value=45):
            allowed = manager._check_thermal_guard()
            assert allowed is True
        
        # Simular temperatura alta
        with patch.object(manager, '_get_system_temp', return_value=75):
            allowed = manager._check_thermal_guard()
            assert allowed is False
    
    def test_dispatch_single_agent(self):
        """Test despacho de un solo agente."""
        from src.agents.swarm_manager import SwarmManager
        
        manager = SwarmManager(self.config)
        
        # Mock de agente
        mock_agent = Mock()
        mock_agent.run.return_value = {"result": "success"}
        
        result = manager.dispatch(mock_agent, "test_query")
        assert result is not None
    
    def test_max_agents_limit(self):
        """Test que respeta el límite de agentes."""
        from src.agents.swarm_manager import SwarmManager
        
        manager = SwarmManager({"max_agents": 2, "thermal_throttling": False})
        
        # Intentar despachar más agentes de los permitidos
        mock_agent = Mock()
        mock_agent.run.return_value = {"result": "success"}
        
        # Primeros 2 agentes deberían funcionar
        manager.dispatch(mock_agent, "query1")
        manager.dispatch(mock_agent, "query2")
        
        # Tercer agente debería ser rechazado o encolado
        # (depende de la implementación)
    
    def test_get_active_agents_count(self):
        """Test conteo de agentes activos."""
        from src.agents.swarm_manager import SwarmManager
        
        manager = SwarmManager(self.config)
        
        count = manager.get_active_agents_count()
        assert isinstance(count, int)
        assert count >= 0
    
    def test_shutdown_all_agents(self):
        """Test apagado de todos los agentes."""
        from src.agents.swarm_manager import SwarmManager
        
        manager = SwarmManager(self.config)
        
        # Debería poder llamar a shutdown sin error
        manager.shutdown_all()
        
        # Después de shutdown, no debería haber agentes activos
        assert manager.get_active_agents_count() == 0
    
    def test_get_stats(self):
        """Test obtención de estadísticas."""
        from src.agents.swarm_manager import SwarmManager
        
        manager = SwarmManager(self.config)
        stats = manager.get_stats()
        
        assert isinstance(stats, dict)
        assert "max_agents" in stats or "active_agents" in stats
    
    def test_agent_timeout(self):
        """Test timeout de agente."""
        from src.agents.swarm_manager import SwarmManager
        
        manager = SwarmManager(self.config)
        
        # Mock de agente lento
        slow_agent = Mock()
        slow_agent.run.side_effect = lambda q: time.sleep(0.1) or {"result": "done"}
        
        # Debería manejar timeout apropiadamente
        result = manager.dispatch(slow_agent, "slow_query", timeout=0.05)
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])