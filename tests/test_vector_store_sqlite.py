#!/usr/bin/env python3
"""
Tests para el VectorStoreSQLite (Almacenamiento Vectorial en SQLite).
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock


class TestVectorStoreSQLite:
    """Tests para VectorStoreSQLite."""
    
    def setup_method(self):
        """Configurar tests."""
        self.test_db_path = tempfile.mktemp(suffix=".db")
    
    def teardown_method(self):
        """Limpiar después de tests."""
        if os.path.exists(self.test_db_path):
            os.unlink(self.test_db_path)
    
    def test_store_initialization(self):
        """Test que el store se inicializa correctamente."""
        from src.persistence.vector_store_sqlite import VectorStoreSQLite
        
        store = VectorStoreSQLite(self.test_db_path)
        assert store is not None
        assert os.path.exists(self.test_db_path)
    
    def test_add_vector(self):
        """Test agregar vector al store."""
        from src.persistence.vector_store_sqlite import VectorStoreSQLite
        
        store = VectorStoreSQLite(self.test_db_path)
        
        # Vector de prueba
        vector = [0.1, 0.2, 0.3, 0.4, 0.5]
        metadata = {"text": "test document", "category": "test"}
        
        vector_id = store.add_vector(vector, metadata)
        assert vector_id is not None
        assert isinstance(vector_id, (int, str))
    
    def test_search_vectors(self):
        """Test búsqueda de vectores similares."""
        from src.persistence.vector_store_sqlite import VectorStoreSQLite
        
        store = VectorStoreSQLite(self.test_db_path)
        
        # Agregar vectores
        store.add_vector([0.1, 0.2, 0.3], {"text": "doc1"})
        store.add_vector([0.15, 0.25, 0.35], {"text": "doc2"})
        store.add_vector([0.9, 0.8, 0.7], {"text": "doc3"})
        
        # Buscar vectores similares
        query_vector = [0.1, 0.2, 0.3]
        results = store.search(query_vector, k=2)
        
        assert results is not None
        assert len(results) <= 2
    
    def test_get_vector_by_id(self):
        """Test obtener vector por ID."""
        from src.persistence.vector_store_sqlite import VectorStoreSQLite
        
        store = VectorStoreSQLite(self.test_db_path)
        
        # Agregar vector
        vector_id = store.add_vector([0.1, 0.2, 0.3], {"text": "test"})
        
        # Recuperar vector
        vector, metadata = store.get_vector(vector_id)
        assert vector is not None
        assert metadata is not None
    
    def test_delete_vector(self):
        """Test eliminar vector."""
        from src.persistence.vector_store_sqlite import VectorStoreSQLite
        
        store = VectorStoreSQLite(self.test_db_path)
        
        # Agregar vector
        vector_id = store.add_vector([0.1, 0.2, 0.3], {"text": "test"})
        
        # Eliminar vector
        store.delete_vector(vector_id)
        
        # Verificar que ya no existe
        vector, metadata = store.get_vector(vector_id)
        assert vector is None or metadata is None
    
    def test_update_vector(self):
        """Test actualizar vector."""
        from src.persistence.vector_store_sqlite import VectorStoreSQLite
        
        store = VectorStoreSQLite(self.test_db_path)
        
        # Agregar vector
        vector_id = store.add_vector([0.1, 0.2, 0.3], {"text": "original"})
        
        # Actualizar vector
        store.update_vector(vector_id, [0.4, 0.5, 0.6], {"text": "updated"})
        
        # Verificar actualización
        vector, metadata = store.get_vector(vector_id)
        assert vector == [0.4, 0.5, 0.6]
        assert metadata.get("text") == "updated"
    
    def test_get_stats(self):
        """Test obtención de estadísticas."""
        from src.persistence.vector_store_sqlite import VectorStoreSQLite
        
        store = VectorStoreSQLite(self.test_db_path)
        
        # Agregar algunos vectores
        store.add_vector([0.1, 0.2, 0.3], {"text": "doc1"})
        store.add_vector([0.4, 0.5, 0.6], {"text": "doc2"})
        
        stats = store.get_stats()
        assert isinstance(stats, dict)
        assert "total_vectors" in stats or "vector_count" in stats
        assert stats.get("total_vectors") == 2 or stats.get("vector_count") == 2
    
    def test_clear_store(self):
        """Test limpieza completa del store."""
        from src.persistence.vector_store_sqlite import VectorStoreSQLite
        
        store = VectorStoreSQLite(self.test_db_path)
        
        # Agregar vectores
        store.add_vector([0.1, 0.2, 0.3], {"text": "doc1"})
        store.add_vector([0.4, 0.5, 0.6], {"text": "doc2"})
        
        # Limpiar
        store.clear()
        
        # Verificar que está vacío
        stats = store.get_stats()
        assert stats.get("total_vectors") == 0 or stats.get("vector_count") == 0
    
    def test_batch_add_vectors(self):
        """Test agregar vectores en lote."""
        from src.persistence.vector_store_sqlite import VectorStoreSQLite
        
        store = VectorStoreSQLite(self.test_db_path)
        
        # Vectores en lote
        vectors = [
            ([0.1, 0.2, 0.3], {"text": "doc1"}),
            ([0.4, 0.5, 0.6], {"text": "doc2"}),
            ([0.7, 0.8, 0.9], {"text": "doc3"})
        ]
        
        ids = store.add_vectors_batch(vectors)
        assert ids is not None
        assert len(ids) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])