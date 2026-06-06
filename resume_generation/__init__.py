"""Resume-generation orchestration boundary.

This package is reserved for code that loads resume evidence, calls the
selection services, and prepares structured resume fill data.
"""

from resume_generation.config import (
    DEFAULT_GENERATION_CONFIG_PATH,
    DEFAULT_JOB_TARGET_PATH,
    load_generation_config,
    load_job_target,
)
from resume_generation.models import (
    BulletCountRangeConfig,
    BulletPointGenerationConfig,
    GenerationAppConfig,
    JobTarget,
    ProjectBulletPointResult,
    ProjectSelectionConfig,
    ProjectSelectionResult,
    ResumeGenerationConfig,
    ResumeSelectionContext,
    SkillSelectionConfig,
    SkillSelectionResult,
)
from resume_generation.selection import (
    ResumeGenerationError,
    build_skill_selection_payload,
    generate_selection_context,
)

__all__ = [
    "DEFAULT_GENERATION_CONFIG_PATH",
    "DEFAULT_JOB_TARGET_PATH",
    "BulletCountRangeConfig",
    "BulletPointGenerationConfig",
    "GenerationAppConfig",
    "JobTarget",
    "ProjectBulletPointResult",
    "ProjectSelectionConfig",
    "ProjectSelectionResult",
    "ResumeGenerationConfig",
    "ResumeGenerationError",
    "ResumeSelectionContext",
    "SkillSelectionConfig",
    "SkillSelectionResult",
    "build_skill_selection_payload",
    "generate_selection_context",
    "load_generation_config",
    "load_job_target",
]
