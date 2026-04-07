"""
Claw-Litle 1.0 - Features Module

Advanced features module containing:
- Feature Flags System
- Query Complexity Analyzer
- Self-Refining Reasoning Engine
- Adaptive Thinking Controller

All features are designed to be:
- Opt-in (activated via feature flags)
- Backward compatible
- Termux-compatible (ARM64, <350MB RAM)
"""

from .feature_flags import (
    FeatureFlag,
    FeatureFlagsManager,
    get_feature_flags_manager,
    is_feature_enabled,
    feature_required
)

from .query_complexity_analyzer import (
    QueryComplexityAnalyzer,
    ComplexityScore,
    ThinkingLevel,
    get_complexity_analyzer,
    analyze_query_complexity
)

from .self_refining_engine import (
    SelfRefiningEngine,
    ConfidenceEvaluator,
    RefinementResult,
    RefinementIteration,
    RefinementStatus,
    get_self_refining_engine,
    refine_response
)

from .adaptive_thinking_controller import (
    AdaptiveThinkingController,
    ThinkingConfig,
    ThinkingDecision,
    get_adaptive_thinking_controller,
    get_thinking_recommendation
)

from .kairos_daemon import (
    KairosDaemon,
    DaemonStatus,
    DaemonTaskType,
    DaemonTask,
    DaemonMetrics,
    get_kairos_daemon,
    start_kairos_daemon,
    stop_kairos_daemon
)

from .context_manager import (
    ContextManager,
    ContextPriority,
    CompactionStrategy,
    ContextBlock,
    ContextHealth,
    CompactionResult,
    get_context_manager
)

from .security_analyst import (
    SecurityAnalyst,
    SecuritySeverity,
    VulnerabilityType,
    SecurityFinding,
    SecurityReport,
    get_security_analyst,
    analyze_code_security
)

from .enhanced_buddy_reviewer import (
    EnhancedBuddyReviewer,
    ReviewVerdict,
    CodeCategory,
    CategoryScore,
    BuddyReview,
    LearningExample,
    get_enhanced_buddy_reviewer,
    review_code
)

__version__ = "1.0.0"
__phase__ = "production_stable"

__all__ = [
    "FeatureFlag",
    "FeatureFlagsManager",
    "get_feature_flags_manager",
    "is_feature_enabled",
    "feature_required",
    "QueryComplexityAnalyzer",
    "ComplexityScore",
    "ThinkingLevel",
    "get_complexity_analyzer",
    "analyze_query_complexity",
    "SelfRefiningEngine",
    "ConfidenceEvaluator",
    "RefinementResult",
    "RefinementIteration",
    "RefinementStatus",
    "get_self_refining_engine",
    "refine_response",
    "AdaptiveThinkingController",
    "ThinkingConfig",
    "ThinkingDecision",
    "get_adaptive_thinking_controller",
    "get_thinking_recommendation",
    "KairosDaemon",
    "DaemonStatus",
    "DaemonTaskType",
    "DaemonTask",
    "DaemonMetrics",
    "get_kairos_daemon",
    "start_kairos_daemon",
    "stop_kairos_daemon",
    "ContextManager",
    "ContextPriority",
    "CompactionStrategy",
    "ContextBlock",
    "ContextHealth",
    "CompactionResult",
    "get_context_manager",
    "SecurityAnalyst",
    "SecuritySeverity",
    "VulnerabilityType",
    "SecurityFinding",
    "SecurityReport",
    "get_security_analyst",
    "analyze_code_security",
    "EnhancedBuddyReviewer",
    "ReviewVerdict",
    "CodeCategory",
    "CategoryScore",
    "BuddyReview",
    "LearningExample",
    "get_enhanced_buddy_reviewer",
    "review_code",
]


def get_features_status() -> dict:
    """Get current features status"""
    from .feature_flags import get_feature_flags_manager
    
    manager = get_feature_flags_manager()
    flags = manager.get_all_flags()
    
    return {
        "version": __version__,
        "phase": __phase__,
        "features": {
            name: {
                "enabled": flag["enabled"],
                "description": flag["description"],
                "rollout_percentage": flag["rollout_percentage"]
            }
            for name, flag in flags.items()
        }
    }