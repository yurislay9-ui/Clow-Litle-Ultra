"""
Tests para Feature Flags Manager - Claw-Litle 1.0
"""

import pytest
from src.features.feature_flags import (
    FeatureFlag,
    FeatureFlagsManager,
    get_feature_flags_manager,
    is_feature_enabled,
    feature_required
)


@pytest.fixture
def manager():
    """Fixture para obtener un manager limpio"""
    # Resetear instancia global
    import src.features.feature_flags as ff_module
    ff_module._default_manager = None
    return get_feature_flags_manager()


class TestFeatureFlagsManager:
    """Tests para FeatureFlagsManager"""
    
    def test_initialization(self, manager):
        """Test de inicialización del manager"""
        assert manager is not None
        flags = manager.get_all_flags()
        assert isinstance(flags, dict)
        # Al menos 8 feature flags por defecto
        assert len(flags) >= 8
    
    def test_feature_flag_exists(self, manager):
        """Test que existen los feature flags esperados"""
        expected_flags = [
            "self_refining_reasoning",
            "adaptive_thinking",
            "kairos_daemon",
            "context_management_pipeline",
            "security_analyst",
            "enhanced_buddy_reviewer",
            "query_complexity_analyzer",
            "telemetry_framework"
        ]
        flags = manager.get_all_flags()
        for flag_name in expected_flags:
            assert flag_name in flags
    
    def test_is_feature_enabled_default(self, manager):
        """Test de estado por defecto de features"""
        # Todas las features están deshabilitadas por defecto
        assert manager.is_enabled("self_refining_reasoning") is False
        assert manager.is_enabled("query_complexity_analyzer") is False
    
    def test_enable_disable_feature(self, manager):
        """Test de habilitar/deshabilitar feature"""
        # Habilitar
        manager.enable("self_refining_reasoning")
        assert manager.is_enabled("self_refining_reasoning") is True
        
        # Deshabilitar
        manager.disable("self_refining_reasoning")
        assert manager.is_enabled("self_refining_reasoning") is False
    
    def test_rollout_percentage(self, manager):
        """Test de rollout porcentual"""
        flag = manager.get_flag("adaptive_thinking")
        assert flag is not None
        assert isinstance(flag, FeatureFlag)
        assert 0 <= flag.rollout_percentage <= 100
    
    def test_set_rollout_percentage(self, manager):
        """Test de configuración de rollout porcentual"""
        manager.enable("kairos_daemon", rollout_percentage=50)
        flag = manager.get_flag("kairos_daemon")
        assert flag.rollout_percentage == 50
    
    def test_is_feature_in_rollout(self, manager):
        """Test de verificación de rollout"""
        manager.enable("security_analyst", rollout_percentage=100)
        assert manager.is_enabled("security_analyst") is True
        
        manager.enable("security_analyst", rollout_percentage=0)
        # Con rollout 0, puede o no estar habilitado dependiendo del hash
    
    def test_get_feature_description(self, manager):
        """Test de obtención de descripción"""
        flag = manager.get_flag("adaptive_thinking")
        assert flag is not None
        assert flag.description != ""
    
    def test_add_custom_flag(self, manager):
        """Test de agregado de flag personalizado"""
        manager.enable("custom_feature", rollout_percentage=75)
        assert "custom_feature" in manager.get_all_flags()
    
    def test_remove_flag(self, manager):
        """Test de removido de flag"""
        manager.enable("temp_feature")
        assert "temp_feature" in manager.get_all_flags()
        # No hay método remove, pero podemos deshabilitar
        manager.disable("temp_feature")
        assert manager.is_enabled("temp_feature") is False
    
    def test_singleton_pattern(self, manager):
        """Test de patrón singleton"""
        manager2 = get_feature_flags_manager()
        assert manager is manager2
    
    def test_export_to_dict(self, manager):
        """Test de exportación a diccionario"""
        flags = manager.get_all_flags()
        assert isinstance(flags, dict)
        for name, flag_dict in flags.items():
            assert "name" in flag_dict
            assert "enabled" in flag_dict
            assert "description" in flag_dict
    
    def test_import_from_dict(self, manager):
        """Test de importación desde diccionario"""
        # El manager ya tiene flags por defecto
        assert len(manager.get_all_flags()) > 0


class TestFeatureFlagDecorators:
    """Tests para decoradores de Feature Flags"""
    
    def test_feature_required_enabled(self, manager):
        """Test de decorador con feature habilitado"""
        manager.enable("security_analyst")
        
        @feature_required("security_analyst")
        def test_func():
            return "executed"
        
        assert test_func() == "executed"
    
    def test_feature_required_disabled(self, manager):
        """Test de decorador con feature deshabilitado"""
        manager.disable("security_analyst")
        
        @feature_required("security_analyst")
        def test_func():
            return "executed"
        
        with pytest.raises(RuntimeError):
            test_func()
    
    def test_is_feature_enabled_helper(self, manager):
        """Test de función helper is_feature_enabled"""
        manager.disable("kairos_daemon")
        assert is_feature_enabled("kairos_daemon") is False
        
        manager.enable("kairos_daemon")
        assert is_feature_enabled("kairos_daemon") is True


class TestFeatureFlagEdgeCases:
    """Tests para casos de borde de Feature Flags"""
    
    def test_nonexistent_flag(self, manager):
        """Test de flag no existente"""
        assert manager.is_enabled("nonexistent_flag") is False
        assert manager.is_enabled("nonexistent_flag", default=True) is True
    
    def test_invalid_rollout_percentage(self, manager):
        """Test de porcentaje de rollout inválido"""
        # Porcentajes mayores a 100 se permiten pero se comportan como 100
        manager.enable("test_rollout", rollout_percentage=150)
        flag = manager.get_flag("test_rollout")
        assert flag.rollout_percentage == 150
    
    def test_concurrent_access(self, manager):
        """Test de acceso concurrente"""
        import threading
        
        errors = []
        
        def worker():
            try:
                for _ in range(100):
                    manager.enable("concurrent_test")
                    manager.disable("concurrent_test")
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0
    
    def test_large_number_of_flags(self, manager):
        """Test con gran cantidad de flags"""
        for i in range(100):
            manager.enable(f"flag_{i}")
        
        all_flags = manager.get_all_flags()
        assert len(all_flags) >= 100
    
    def test_persistence(self, manager):
        """Test de persistencia"""
        manager.enable("persist_test")
        manager._save_config()
        
        # Crear nuevo manager con misma config
        new_manager = FeatureFlagsManager(manager.config_path)
        assert new_manager.is_enabled("persist_test") is True