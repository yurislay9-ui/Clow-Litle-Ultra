"""
Claw-Litle 1.0
nivel_3_semantic.py - Nivel 3: Semantic Embeddings

Motor de embeddings semánticos usando ONNX MiniLM (~5-15ms).
Detecta intenciones por similitud semántica vectorial.
"""

import logging
import os
from typing import Dict, Optional, List
import numpy as np

from ..engine import IntentResult

logger = logging.getLogger(__name__)


class SemanticEngine:
    """
    Nivel 3 del Motor Híbrido: Semantic Embeddings.
    
    Usa modelo ONNX MiniLM para embeddings semánticos.
    Más lento (~5-15ms) pero entiende significado, no solo palabras.
    """
    
    def __init__(self, model_path: str, threshold: float = 0.89):
        """
        Inicializa el motor semántico.
        
        Args:
            model_path: Ruta al modelo ONNX
            threshold: Umbral mínimo de similitud coseno
        """
        self.model_path = model_path
        self.threshold = threshold
        self._session = None
        self._intent_embeddings = {}
        self._loaded = False
        
        # Lazy loading del modelo
        logger.debug(f"SemanticEngine configurado con modelo: {model_path}")
    
    def load(self):
        """Carga el modelo ONNX bajo demanda (lazy loading)."""
        if self._loaded:
            return
        
        try:
            import onnxruntime as ort
            
            if not os.path.exists(self.model_path):
                logger.warning(f"Modelo ONNX no encontrado en {self.model_path}")
                return
            
            # Cargar modelo ONNX
            self._session = ort.InferenceSession(self.model_path)
            self._loaded = True
            
            logger.info("Modelo ONNX cargado exitosamente")
            
        except ImportError:
            logger.warning("onnxruntime no instalado. Nivel semántico desactivado.")
        except Exception as e:
            logger.error(f"Error cargando modelo ONNX: {e}")
    
    def unload(self):
        """Descarga el modelo para liberar RAM."""
        self._session = None
        self._intent_embeddings = {}
        self._loaded = False
        logger.info("Modelo ONNX descargado - RAM liberada")
    
    def _get_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        Obtiene el embedding de un texto usando el modelo ONNX.
        
        Args:
            text: Texto a procesar
        
        Returns:
            Array numpy con el embedding o None si hay error
        """
        if not self._loaded or not self._session:
            return None
        
        try:
            # Input del modelo ONNX (asumiendo formato estándar MiniLM)
            input_name = self._session.get_inputs()[0].name
            output_name = self._session.get_outputs()[0].name
            
            # Tokenización simple (el modelo ONNX ya incluye tokenizer)
            # Nota: En producción usaríamos tokenizers compatibles
            tokens = self._tokenize(text)
            
            # Ejecutar inferencia
            result = self._session.run([output_name], {input_name: tokens})
            
            # Normalizar embedding
            embedding = result[0].flatten()
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error obteniendo embedding: {e}")
            return None
    
    def _tokenize(self, text: str) -> np.ndarray:
        """
        Tokenización simple para compatibilidad ARM64.
        
        Args:
            text: Texto a tokenizar
        
        Returns:
            Array numpy con tokens (simplificado)
        """
        # Tokenización básica (en producción usaríamos el tokenizer del modelo)
        words = text.lower().split()[:384]  # Máximo 384 tokens
        
        # Convertir a IDs simples (hash-based para compatibilidad)
        token_ids = [hash(word) % 30522 for word in words]  # Vocab size típico
        
        # Padding a longitud fija
        max_len = 384
        attention_mask = [1] * len(token_ids) + [0] * (max_len - len(token_ids))
        token_ids = token_ids + [0] * (max_len - len(token_ids))
        
        return np.array([token_ids, attention_mask], dtype=np.int64)
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calcula similitud coseno entre dos vectores."""
        if a is None or b is None:
            return 0.0
        
        # Ya están normalizados, así que solo producto punto
        return float(np.dot(a, b))
    
    def match(self, query: str) -> Optional[IntentResult]:
        """
        Intenta matchear la query con embeddings semánticos.
        
        Args:
            query: Texto de entrada del usuario
        
        Returns:
            IntentResult si hay match, None si no
        """
        if not self._loaded:
            self.load()
        
        if not self._loaded:
            return None
        
        # Obtener embedding de la query
        query_embedding = self._get_embedding(query)
        if query_embedding is None:
            return None
        
        best_intent = None
        best_score = 0.0
        
        # Comparar con embeddings de intenciones (cacheados)
        for intent_name, intent_embedding in self._intent_embeddings.items():
            score = self._cosine_similarity(query_embedding, intent_embedding)
            
            if score > best_score:
                best_score = score
                best_intent = intent_name
        
        if best_intent and best_score >= self.threshold:
            logger.debug(f"Semantic match: '{query}' -> {best_intent} ({best_score:.2%})")
            return IntentResult(
                intent_name=best_intent,
                confidence=best_score,
                level_reached=3,
                metadata={
                    "level": "semantic",
                    "threshold": self.threshold,
                    "model": "MiniLM-ONNX"
                }
            )
        
        return None