"""
Advanced Context Management Pipeline - Claw-Litle 1.0

Sistema de gestión inteligente de contexto que resuelve el problema de
"Context Entropy" - cuanto más larga corre una sesión, más se degrada la calidad.

Implementa 4 etapas: Monitoring → Analysis → Compaction → Verification
"""

import time
import json
import hashlib
import re
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path


class ContextPriority(Enum):
    """Prioridad de bloques de contexto"""
    CRITICAL = "critical"      # 🔴 Preservar intacto (0% pérdida)
    IMPORTANT = "important"    # 🟠 Comprimir alta fidelidad (~2:1)
    RELEVANT = "relevant"      # 🟡 Resumir manteniendo detalles
    NOISE = "noise"            # ⚪ Descartar


class CompactionStrategy(Enum):
    """Estrategias de compresión"""
    COPY = "copy"              # Copiar tal cual
    COMPRESS = "compress"      # Comprimir manteniendo esencia
    SUMMARIZE = "summarize"    # Resumir en puntos clave
    DISCARD = "discard"        # Eliminar completamente


@dataclass
class ContextBlock:
    """Representa un bloque de contexto"""
    block_id: str
    content: str
    priority: ContextPriority
    strategy: CompactionStrategy
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    size_bytes: int = 0
    compressed_content: Optional[str] = None
    compression_ratio: float = 1.0
    
    def __post_init__(self):
        self.size_bytes = len(self.content.encode('utf-8'))
    
    def compress(self) -> str:
        """Aplica la estrategia de compresión"""
        if self.strategy == CompactionStrategy.COPY:
            return self.content
        elif self.strategy == CompactionStrategy.COMPRESS:
            # Compresión simple: eliminar whitespace excesivo, abreviar
            compressed = re.sub(r'\s+', ' ', self.content)
            self.compression_ratio = len(compressed) / len(self.content) if self.content else 1.0
            self.compressed_content = compressed
            return compressed
        elif self.strategy == CompactionStrategy.SUMMARIZE:
            # Resumen: extraer primeras y últimas frases
            sentences = self.content.split('. ')
            if len(sentences) > 3:
                summary = '. '.join(sentences[:2] + ['...'] + sentences[-1:])
            else:
                summary = self.content
            self.compression_ratio = len(summary) / len(self.content) if self.content else 1.0
            self.compressed_content = summary
            return summary
        else:  # DISCARD
            return ""


@dataclass
class ContextHealth:
    """Métricas de salud del contexto"""
    total_size_bytes: int
    total_blocks: int
    utilization_percentage: float  # % del límite (ej: 256MB)
    repetition_score: float  # 0-1, donde 1 = mucho contenido duplicado
    contradiction_count: int
    avg_block_age_hours: float
    critical_blocks: int
    important_blocks: int
    relevant_blocks: int
    noise_blocks: int
    needs_compaction: bool
    health_score: float  # 0-1, donde 1 = excelente


@dataclass
class CompactionResult:
    """Resultado del proceso de compaction"""
    original_size_bytes: int
    compressed_size_bytes: int
    reduction_percentage: float
    blocks_processed: int
    blocks_preserved: int
    blocks_compressed: int
    blocks_summarized: int
    blocks_discarded: int
    critical_facts_preserved: bool
    instructions_preserved: bool
    coherence_maintained: bool
    time_taken_ms: float
    verification_passed: bool


class ContextManager:
    """
    Gestor avanzado de contexto para Claw-Litle.
    
    Implementa un pipeline de 4 etapas para mantener la calidad del contexto
    en sesiones largas:
    1. MONITORING: Monitoreo de salud del contexto
    2. ANALYSIS & CLASSIFICATION: Clasificación de bloques por prioridad
    3. COMPACTION: Compresión inteligente
    4. VERIFICATION: Verificación post-procesamiento
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Configuración
        self.max_context_size_mb = self.config.get("max_context_size_mb", 256)
        self.compaction_threshold = self.config.get("compaction_threshold", 0.85)  # 85% utilización
        self.repetition_threshold = self.config.get("repetition_threshold", 0.3)  # 30% duplicación
        self.max_block_age_hours = self.config.get("max_block_age_hours", 24)
        
        # Almacenamiento de bloques
        self.blocks: Dict[str, ContextBlock] = {}
        
        # Estadísticas
        self.stats = {
            "total_compactions": 0,
            "total_bytes_saved": 0,
            "avg_reduction_percentage": 0.0,
            "last_compaction": None
        }
        
        # Callbacks
        self.summarization_callback: Optional[Callable] = None
        self.contradiction_detector_callback: Optional[Callable] = None
        
        # Límite de tamaño en bytes
        self.max_context_size_bytes = self.max_context_size_mb * 1024 * 1024
    
    def add_block(
        self,
        content: str,
        priority: ContextPriority = ContextPriority.RELEVANT,
        block_id: Optional[str] = None
    ) -> str:
        """
        Agrega un bloque de contexto.
        
        Args:
            content: Contenido del bloque
            priority: Prioridad del bloque
            block_id: ID único (si None, se genera)
        
        Returns:
            block_id del bloque agregado
        """
        if block_id is None:
            block_id = hashlib.md5(f"{content[:50]}-{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        
        block = ContextBlock(
            block_id=block_id,
            content=content,
            priority=priority,
            strategy=self._priority_to_strategy(priority),
            created_at=datetime.now(),
            last_accessed=datetime.now()
        )
        
        self.blocks[block_id] = block
        return block_id
    
    def _priority_to_strategy(self, priority: ContextPriority) -> CompactionStrategy:
        """Convierte prioridad a estrategia de compresión"""
        mapping = {
            ContextPriority.CRITICAL: CompactionStrategy.COPY,
            ContextPriority.IMPORTANT: CompactionStrategy.COMPRESS,
            ContextPriority.RELEVANT: CompactionStrategy.SUMMARIZE,
            ContextPriority.NOISE: CompactionStrategy.DISCARD
        }
        return mapping.get(priority, CompactionStrategy.SUMMARIZE)
    
    def get_health(self) -> ContextHealth:
        """
        ETAPA 1: MONITORING - Obtiene métricas de salud del contexto.
        
        Returns:
            ContextHealth con métricas completas
        """
        total_size = sum(block.size_bytes for block in self.blocks.values())
        total_blocks = len(self.blocks)
        utilization = total_size / self.max_context_size_bytes if self.max_context_size_bytes > 0 else 0.0
        
        # Calcular score de repetición
        repetition_score = self._calculate_repetition_score()
        
        # Contar contradicciones
        contradiction_count = 0
        if self.contradiction_detector_callback:
            try:
                contradiction_count = self.contradiction_detector_callback(list(self.blocks.values()))
            except Exception:
                pass
        
        # Calcular edad promedio
        if self.blocks:
            ages = [(datetime.now() - block.created_at).total_seconds() / 3600 
                   for block in self.blocks.values()]
            avg_age_hours = sum(ages) / len(ages)
        else:
            avg_age_hours = 0.0
        
        # Contar bloques por prioridad
        priority_counts = {p: 0 for p in ContextPriority}
        for block in self.blocks.values():
            priority_counts[block.priority] += 1
        
        # Determinar si necesita compaction
        needs_compaction = (
            utilization > self.compaction_threshold or
            repetition_score > self.repetition_threshold or
            total_size > self.max_context_size_bytes
        )
        
        # Calcular health score (0-1)
        health_score = self._calculate_health_score(
            utilization, repetition_score, contradiction_count, avg_age_hours
        )
        
        return ContextHealth(
            total_size_bytes=total_size,
            total_blocks=total_blocks,
            utilization_percentage=round(utilization * 100, 2),
            repetition_score=round(repetition_score, 3),
            contradiction_count=contradiction_count,
            avg_block_age_hours=round(avg_age_hours, 1),
            critical_blocks=priority_counts[ContextPriority.CRITICAL],
            important_blocks=priority_counts[ContextPriority.IMPORTANT],
            relevant_blocks=priority_counts[ContextPriority.RELEVANT],
            noise_blocks=priority_counts[ContextPriority.NOISE],
            needs_compaction=needs_compaction,
            health_score=round(health_score, 3)
        )
    
    def _calculate_repetition_score(self) -> float:
        """Calcula el score de repetición (0 = único, 1 = muy repetitivo)"""
        if len(self.blocks) < 2:
            return 0.0
        
        # Comparar hashes de contenido
        content_hashes = [hashlib.md5(block.content.encode()).hexdigest() 
                         for block in self.blocks.values()]
        
        unique_hashes = len(set(content_hashes))
        total_hashes = len(content_hashes)
        
        # Score de repetición = 1 - (únicos / total)
        repetition_score = 1.0 - (unique_hashes / total_hashes) if total_hashes > 0 else 0.0
        return repetition_score
    
    def _calculate_health_score(
        self,
        utilization: float,
        repetition_score: float,
        contradiction_count: int,
        avg_age_hours: float
    ) -> float:
        """Calcula el health score general (0-1)"""
        # Peso de cada factor
        utilization_weight = 0.3
        repetition_weight = 0.25
        contradiction_weight = 0.25
        age_weight = 0.2
        
        # Scores individuales (1 = excelente, 0 = pobre)
        utilization_score = max(0, 1.0 - utilization)
        repetition_score = max(0, 1.0 - repetition_score)
        contradiction_score = max(0, 1.0 - (contradiction_count * 0.1))
        age_score = max(0, 1.0 - (avg_age_hours / self.max_block_age_hours))
        
        # Score ponderado
        health_score = (
            utilization_score * utilization_weight +
            repetition_score * repetition_weight +
            contradiction_score * contradiction_weight +
            age_score * age_weight
        )
        
        return health_score
    
    def analyze_and_classify(self) -> Dict[str, List[str]]:
        """
        ETAPA 2: ANALYSIS & CLASSIFICATION - Clasifica bloques por prioridad.
        
        Returns:
            Diccionario con listas de block_ids por prioridad
        """
        classified = {p.value: [] for p in ContextPriority}
        
        for block_id, block in self.blocks.items():
            # Si ya tiene prioridad crítica, mantener
            if block.priority == ContextPriority.CRITICAL:
                classified[ContextPriority.CRITICAL.value].append(block_id)
                continue
            
            # Analizar contenido para determinar prioridad
            priority = self._analyze_block_priority(block)
            classified[priority.value].append(block_id)
            
            # Actualizar prioridad del bloque
            block.priority = priority
            block.strategy = self._priority_to_strategy(priority)
        
        return classified
    
    def _analyze_block_priority(self, block: ContextBlock) -> ContextPriority:
        """Analiza un bloque para determinar su prioridad"""
        content_lower = block.content.lower()
        
        # Indicadores de contenido crítico
        critical_indicators = [
            "instrucciones del usuario", "preferencias del usuario",
            "configuración", "parámetros importantes", "datos críticos",
            "no olvidar", "importante:", "crítico:", "esencial:"
        ]
        
        # Indicadores de contenido importante
        important_indicators = [
            "resultado:", "conclusión:", "resumen ejecutivo",
            "hallazgo clave", "dato importante", "relevante:"
        ]
        
        # Indicadores de ruido
        noise_indicators = [
            "error:", "timeout", "intento fallido", "reintentando",
            "debug:", "trace:", "stack trace", "excepción no controlada"
        ]
        
        # Verificar indicadores
        critical_count = sum(1 for indicator in critical_indicators if indicator in content_lower)
        important_count = sum(1 for indicator in important_indicators if indicator in content_lower)
        noise_count = sum(1 for indicator in noise_indicators if indicator in content_lower)
        
        # Determinar prioridad
        if critical_count > 0:
            return ContextPriority.CRITICAL
        elif important_count > 0:
            return ContextPriority.IMPORTANT
        elif noise_count > len(noise_indicators) * 0.5:
            return ContextPriority.NOISE
        else:
            # Por defecto, basado en antigüedad y acceso
            age_hours = (datetime.now() - block.created_at).total_seconds() / 3600
            if age_hours > self.max_block_age_hours and block.access_count < 3:
                return ContextPriority.NOISE
            elif block.access_count > 10:
                return ContextPriority.IMPORTANT
            else:
                return ContextPriority.RELEVANT
    
    def compact(self) -> CompactionResult:
        """
        ETAPA 3: COMPACTION - Aplica compresión inteligente.
        
        Returns:
            CompactionResult con métricas del proceso
        """
        start_time = time.time()
        
        original_size = sum(block.size_bytes for block in self.blocks.values())
        
        # Contadores
        blocks_preserved = 0
        blocks_compressed = 0
        blocks_summarized = 0
        blocks_discarded = 0
        
        # Aplicar estrategias de compresión
        for block in self.blocks.values():
            if block.strategy == CompactionStrategy.COPY:
                blocks_preserved += 1
            elif block.strategy == CompactionStrategy.COMPRESS:
                block.compress()
                blocks_compressed += 1
            elif block.strategy == CompactionStrategy.SUMMARIZE:
                block.compress()
                blocks_summarized += 1
            else:  # DISCARD
                blocks_discarded += 1
        
        compressed_size = sum(
            len((block.compressed_content or block.content).encode('utf-8'))
            for block in self.blocks.values()
        )
        
        reduction_percentage = ((original_size - compressed_size) / original_size * 100) if original_size > 0 else 0
        
        time_taken_ms = (time.time() - start_time) * 1000
        
        # Verificación post-compaction
        verification = self.verify(original_size, compressed_size)
        
        result = CompactionResult(
            original_size_bytes=original_size,
            compressed_size_bytes=compressed_size,
            reduction_percentage=round(reduction_percentage, 2),
            blocks_processed=len(self.blocks),
            blocks_preserved=blocks_preserved,
            blocks_compressed=blocks_compressed,
            blocks_summarized=blocks_summarized,
            blocks_discarded=blocks_discarded,
            critical_facts_preserved=verification["critical_preserved"],
            instructions_preserved=verification["instructions_preserved"],
            coherence_maintained=verification["coherence_maintained"],
            time_taken_ms=round(time_taken_ms, 2),
            verification_passed=verification["passed"]
        )
        
        # Actualizar estadísticas
        self.stats["total_compactions"] += 1
        self.stats["total_bytes_saved"] += (original_size - compressed_size)
        self.stats["last_compaction"] = datetime.now().isoformat()
        
        return result
    
    def verify(self, original_size: int, compressed_size: int) -> Dict[str, Any]:
        """
        ETAPA 4: VERIFICATION - Verifica calidad post-procesamiento.
        
        Args:
            original_size: Tamaño original
            compressed_size: Tamaño después de compaction
        
        Returns:
            Diccionario con resultados de verificación
        """
        # Verificar que bloques críticos estén intactos
        critical_blocks = [b for b in self.blocks.values() 
                          if b.priority == ContextPriority.CRITICAL]
        critical_preserved = all(
            b.strategy == CompactionStrategy.COPY and b.compression_ratio == 1.0
            for b in critical_blocks
        )
        
        # Verificar que instrucciones del usuario estén preservadas
        instructions_preserved = True
        for block in critical_blocks:
            if "instrucciones" in block.content.lower() or "preferencias" in block.content.lower():
                if block.strategy != CompactionStrategy.COPY:
                    instructions_preserved = False
                    break
        
        # Verificar coherencia narrativa (básico)
        coherence_maintained = True
        # Aquí se podría implementar un análisis más sofisticado
        
        # Verificar que la reducción sea razonable
        if original_size > 0:
            reduction = (original_size - compressed_size) / original_size
            # Si la reducción es >90%, probablemente se perdió demasiado
            if reduction > 0.9:
                coherence_maintained = False
        
        passed = critical_preserved and instructions_preserved and coherence_maintained
        
        return {
            "critical_preserved": critical_preserved,
            "instructions_preserved": instructions_preserved,
            "coherence_maintained": coherence_maintained,
            "passed": passed
        }
    
    def run_full_pipeline(self) -> Dict[str, Any]:
        """
        Ejecuta el pipeline completo de gestión de contexto.
        
        Returns:
            Diccionario con resultados de todas las etapas
        """
        # Etapa 1: Monitoring
        health = self.get_health()
        
        if not health.needs_compaction:
            return {
                "action": "none",
                "reason": "Context health is good",
                "health": health.__dict__
            }
        
        # Etapa 2: Analysis & Classification
        classification = self.analyze_and_classify()
        
        # Etapa 3: Compaction
        compaction_result = self.compact()
        
        return {
            "action": "compacted",
            "health_before": health.__dict__,
            "classification": classification,
            "compaction_result": compaction_result.__dict__
        }
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Obtiene un resumen del contexto actual"""
        health = self.get_health()
        
        return {
            "total_blocks": health.total_blocks,
            "total_size_mb": round(health.total_size_bytes / (1024 * 1024), 2),
            "utilization_percentage": health.utilization_percentage,
            "health_score": health.health_score,
            "needs_compaction": health.needs_compaction,
            "priority_distribution": {
                "critical": health.critical_blocks,
                "important": health.important_blocks,
                "relevant": health.relevant_blocks,
                "noise": health.noise_blocks
            },
            "stats": self.stats
        }
    
    def clear(self):
        """Limpia todo el contexto"""
        self.blocks.clear()
    
    def remove_old_blocks(self, max_age_hours: Optional[int] = None):
        """Elimina bloques antiguos"""
        max_age = max_age_hours or self.max_block_age_hours
        cutoff = datetime.now() - timedelta(hours=max_age)
        
        to_remove = [
            block_id for block_id, block in self.blocks.items()
            if block.created_at < cutoff and block.priority != ContextPriority.CRITICAL
        ]
        
        for block_id in to_remove:
            del self.blocks[block_id]
        
        return len(to_remove)


# Instancia global
_manager: Optional[ContextManager] = None


def get_context_manager(config: Optional[Dict] = None) -> ContextManager:
    """Obtiene la instancia global del context manager"""
    global _manager
    if _manager is None:
        _manager = ContextManager(config)
    return _manager


if __name__ == "__main__":
    # Ejemplo de uso
    print("=== Claw-Litle 1.0 - Context Manager ===\n")
    
    manager = get_context_manager({
        "max_context_size_mb": 1,  # 1MB para testing
        "compaction_threshold": 0.5  # 50% para testing
    })
    
    # Agregar bloques de ejemplo
    manager.add_block(
        "Instrucciones del usuario: Siempre responder en español y ser conciso.",
        ContextPriority.CRITICAL
    )
    
    manager.add_block(
        "Resultado de la búsqueda: El precio del iPhone 15 es $999.",
        ContextPriority.IMPORTANT
    )
    
    manager.add_block(
        "Debug: Intentando conectar a la API...",
        ContextPriority.NOISE
    )
    
    manager.add_block(
        "Este es un bloque de contexto relevante con información general sobre el tema.",
        ContextPriority.RELEVANT
    )
    
    # Ver salud del contexto
    print("Salud del contexto:")
    health = manager.get_health()
    print(f"  Bloques: {health.total_blocks}")
    print(f"  Tamaño: {health.total_size_bytes} bytes")
    print(f"  Utilización: {health.utilization_percentage}%")
    print(f"  Health Score: {health.health_score}")
    print(f"  Necesita compaction: {health.needs_compaction}")
    
    # Ejecutar pipeline completo
    print("\nEjecutando pipeline completo:")
    result = manager.run_full_pipeline()
    print(json.dumps(result, indent=2, default=str))
    
    # Resumen final
    print("\nResumen del contexto:")
    summary = manager.get_context_summary()
    print(json.dumps(summary, indent=2, default=str))