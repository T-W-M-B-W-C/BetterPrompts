"""
Prompt engineering techniques implementation
"""

from .base import BaseTechnique, TechniqueRegistry
from .chain_of_thought import ChainOfThoughtTechnique
from .tree_of_thoughts import TreeOfThoughtsTechnique
from .few_shot import FewShotTechnique
from .zero_shot import ZeroShotTechnique
from .role_play import RolePlayTechnique
from .step_by_step import StepByStepTechnique
from .structured_output import StructuredOutputTechnique
from .emotional_appeal import EmotionalAppealTechnique
from .constraints import ConstraintsTechnique
from .analogical import AnalogicalTechnique

__all__ = [
    "BaseTechnique",
    "TechniqueRegistry",
    "ChainOfThoughtTechnique",
    "TreeOfThoughtsTechnique",
    "FewShotTechnique",
    "ZeroShotTechnique",
    "RolePlayTechnique",
    "StepByStepTechnique",
    "StructuredOutputTechnique",
    "EmotionalAppealTechnique",
    "ConstraintsTechnique",
    "AnalogicalTechnique",
]