"""
Evaluation module for BetterPrompts ML pipeline
"""

from .metrics import (
    calculate_metrics,
    calculate_ece,
    plot_confusion_matrix,
    plot_roc_curves,
    plot_precision_recall_curves,
    plot_confidence_distribution,
    create_evaluation_report
)

__all__ = [
    'calculate_metrics',
    'calculate_ece',
    'plot_confusion_matrix',
    'plot_roc_curves',
    'plot_precision_recall_curves',
    'plot_confidence_distribution',
    'create_evaluation_report'
]