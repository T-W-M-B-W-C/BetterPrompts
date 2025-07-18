"""
Model evaluation metrics and visualization utilities
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
    classification_report,
    roc_auc_score,
    roc_curve,
    precision_recall_curve,
    average_precision_score,
    cohen_kappa_score,
    matthews_corrcoef,
    top_k_accuracy_score
)
from sklearn.preprocessing import label_binarize
import torch

logger = logging.getLogger(__name__)


def calculate_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_proba: Optional[np.ndarray] = None,
    label_names: Optional[List[str]] = None,
    average: str = 'weighted'
) -> Dict[str, Union[float, str, np.ndarray]]:
    """
    Calculate comprehensive metrics for classification
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
        y_proba: Prediction probabilities (optional)
        label_names: Names of labels
        average: Averaging method for multi-class metrics
    
    Returns:
        Dictionary of metrics
    """
    metrics = {}
    
    # Basic metrics
    metrics['accuracy'] = accuracy_score(y_true, y_pred)
    
    # Precision, recall, F1
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, average=None, zero_division=0
    )
    
    # Store per-class metrics
    if label_names:
        for i, label in enumerate(label_names):
            metrics[f'precision_{label}'] = precision[i]
            metrics[f'recall_{label}'] = recall[i]
            metrics[f'f1_{label}'] = f1[i]
            metrics[f'support_{label}'] = support[i]
    
    # Averaged metrics
    for avg in ['weighted', 'macro', 'micro']:
        p, r, f, _ = precision_recall_fscore_support(
            y_true, y_pred, average=avg, zero_division=0
        )
        metrics[f'precision_{avg}'] = p
        metrics[f'recall_{avg}'] = r
        metrics[f'f1_{avg}'] = f
    
    # Additional metrics
    metrics['cohen_kappa'] = cohen_kappa_score(y_true, y_pred)
    metrics['matthews_corrcoef'] = matthews_corrcoef(y_true, y_pred)
    
    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    metrics['confusion_matrix'] = cm.tolist()
    
    # Classification report
    if label_names:
        report = classification_report(
            y_true, y_pred, 
            target_names=label_names,
            zero_division=0
        )
        metrics['classification_report'] = report
    
    # Probability-based metrics
    if y_proba is not None:
        # Top-k accuracy
        for k in [3, 5]:
            if y_proba.shape[1] >= k:
                metrics[f'top_{k}_accuracy'] = top_k_accuracy_score(
                    y_true, y_proba, k=k
                )
        
        # AUC metrics
        try:
            if len(np.unique(y_true)) == 2:
                # Binary classification
                metrics['roc_auc'] = roc_auc_score(y_true, y_proba[:, 1])
                metrics['average_precision'] = average_precision_score(
                    y_true, y_proba[:, 1]
                )
            else:
                # Multi-class
                # One-vs-rest AUC
                y_true_bin = label_binarize(
                    y_true, 
                    classes=list(range(y_proba.shape[1]))
                )
                
                # Macro AUC
                metrics['roc_auc_macro'] = roc_auc_score(
                    y_true_bin, y_proba, average='macro', multi_class='ovr'
                )
                
                # Weighted AUC
                metrics['roc_auc_weighted'] = roc_auc_score(
                    y_true_bin, y_proba, average='weighted', multi_class='ovr'
                )
        except Exception as e:
            logger.warning(f"Could not calculate AUC metrics: {e}")
        
        # Confidence metrics
        max_probs = np.max(y_proba, axis=1)
        metrics['mean_confidence'] = np.mean(max_probs)
        metrics['confidence_std'] = np.std(max_probs)
        
        # Calibration error
        metrics['expected_calibration_error'] = calculate_ece(
            y_true, y_pred, max_probs
        )
    
    return metrics


def calculate_ece(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_conf: np.ndarray,
    n_bins: int = 10
) -> float:
    """
    Calculate Expected Calibration Error (ECE)
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
        y_conf: Confidence scores
        n_bins: Number of bins for calibration
    
    Returns:
        ECE score
    """
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    bin_lowers = bin_boundaries[:-1]
    bin_uppers = bin_boundaries[1:]
    
    ece = 0
    for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
        in_bin = (y_conf > bin_lower) & (y_conf <= bin_upper)
        prop_in_bin = in_bin.mean()
        
        if prop_in_bin > 0:
            accuracy_in_bin = (y_true[in_bin] == y_pred[in_bin]).mean()
            avg_confidence_in_bin = y_conf[in_bin].mean()
            ece += np.abs(avg_confidence_in_bin - accuracy_in_bin) * prop_in_bin
    
    return ece


def plot_confusion_matrix(
    cm: np.ndarray,
    label_names: List[str],
    save_path: Optional[str] = None,
    figsize: Tuple[int, int] = (10, 8),
    cmap: str = 'Blues'
) -> plt.Figure:
    """
    Plot confusion matrix
    
    Args:
        cm: Confusion matrix
        label_names: Names of labels
        save_path: Path to save figure
        figsize: Figure size
        cmap: Colormap
    
    Returns:
        Matplotlib figure
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    # Normalize confusion matrix
    cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
    
    # Create heatmap
    sns.heatmap(
        cm_normalized,
        annot=True,
        fmt='.2f',
        cmap=cmap,
        square=True,
        xticklabels=label_names,
        yticklabels=label_names,
        cbar_kws={'label': 'Normalized Count'},
        ax=ax
    )
    
    ax.set_xlabel('Predicted Label', fontsize=12)
    ax.set_ylabel('True Label', fontsize=12)
    ax.set_title('Confusion Matrix (Normalized)', fontsize=14)
    
    # Rotate labels for better readability
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig


def plot_roc_curves(
    y_true: np.ndarray,
    y_proba: np.ndarray,
    label_names: List[str],
    save_path: Optional[str] = None,
    figsize: Tuple[int, int] = (10, 8)
) -> plt.Figure:
    """
    Plot ROC curves for multi-class classification
    
    Args:
        y_true: True labels
        y_proba: Prediction probabilities
        label_names: Names of labels
        save_path: Path to save figure
        figsize: Figure size
    
    Returns:
        Matplotlib figure
    """
    # Binarize labels
    y_true_bin = label_binarize(y_true, classes=list(range(len(label_names))))
    n_classes = y_true_bin.shape[1]
    
    fig, ax = plt.subplots(figsize=figsize)
    
    # Calculate ROC curve for each class
    for i in range(n_classes):
        fpr, tpr, _ = roc_curve(y_true_bin[:, i], y_proba[:, i])
        roc_auc = roc_auc_score(y_true_bin[:, i], y_proba[:, i])
        
        ax.plot(
            fpr, tpr,
            label=f'{label_names[i]} (AUC = {roc_auc:.3f})',
            linewidth=2
        )
    
    # Plot diagonal
    ax.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Random')
    
    ax.set_xlabel('False Positive Rate', fontsize=12)
    ax.set_ylabel('True Positive Rate', fontsize=12)
    ax.set_title('ROC Curves by Class', fontsize=14)
    ax.legend(loc='lower right')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig


def plot_precision_recall_curves(
    y_true: np.ndarray,
    y_proba: np.ndarray,
    label_names: List[str],
    save_path: Optional[str] = None,
    figsize: Tuple[int, int] = (10, 8)
) -> plt.Figure:
    """
    Plot precision-recall curves for multi-class classification
    
    Args:
        y_true: True labels
        y_proba: Prediction probabilities
        label_names: Names of labels
        save_path: Path to save figure
        figsize: Figure size
    
    Returns:
        Matplotlib figure
    """
    # Binarize labels
    y_true_bin = label_binarize(y_true, classes=list(range(len(label_names))))
    n_classes = y_true_bin.shape[1]
    
    fig, ax = plt.subplots(figsize=figsize)
    
    # Calculate precision-recall curve for each class
    for i in range(n_classes):
        precision, recall, _ = precision_recall_curve(
            y_true_bin[:, i], y_proba[:, i]
        )
        avg_precision = average_precision_score(
            y_true_bin[:, i], y_proba[:, i]
        )
        
        ax.plot(
            recall, precision,
            label=f'{label_names[i]} (AP = {avg_precision:.3f})',
            linewidth=2
        )
    
    ax.set_xlabel('Recall', fontsize=12)
    ax.set_ylabel('Precision', fontsize=12)
    ax.set_title('Precision-Recall Curves by Class', fontsize=14)
    ax.legend(loc='lower left')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig


def plot_confidence_distribution(
    y_conf: np.ndarray,
    y_correct: np.ndarray,
    save_path: Optional[str] = None,
    figsize: Tuple[int, int] = (10, 6),
    n_bins: int = 20
) -> plt.Figure:
    """
    Plot confidence distribution for correct and incorrect predictions
    
    Args:
        y_conf: Confidence scores
        y_correct: Boolean array of correct predictions
        save_path: Path to save figure
        figsize: Figure size
        n_bins: Number of bins
    
    Returns:
        Matplotlib figure
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
    
    # Distribution plot
    ax1.hist(
        y_conf[y_correct], bins=n_bins, alpha=0.7, 
        label='Correct', density=True, color='green'
    )
    ax1.hist(
        y_conf[~y_correct], bins=n_bins, alpha=0.7,
        label='Incorrect', density=True, color='red'
    )
    ax1.set_xlabel('Confidence Score', fontsize=12)
    ax1.set_ylabel('Density', fontsize=12)
    ax1.set_title('Confidence Distribution', fontsize=14)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Calibration plot
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    bin_centers = (bin_boundaries[:-1] + bin_boundaries[1:]) / 2
    
    accuracies = []
    avg_confidences = []
    
    for bin_lower, bin_upper in zip(bin_boundaries[:-1], bin_boundaries[1:]):
        in_bin = (y_conf > bin_lower) & (y_conf <= bin_upper)
        if in_bin.sum() > 0:
            accuracies.append(y_correct[in_bin].mean())
            avg_confidences.append(y_conf[in_bin].mean())
    
    ax2.plot(avg_confidences, accuracies, 'o-', label='Model', markersize=8)
    ax2.plot([0, 1], [0, 1], 'k--', label='Perfect calibration')
    ax2.set_xlabel('Mean Confidence', fontsize=12)
    ax2.set_ylabel('Accuracy', fontsize=12)
    ax2.set_title('Calibration Plot', fontsize=14)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim([0, 1])
    ax2.set_ylim([0, 1])
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig


def create_evaluation_report(
    model,
    test_loader,
    device: torch.device,
    label_names: List[str],
    output_dir: str
) -> Dict:
    """
    Create comprehensive evaluation report
    
    Args:
        model: Trained model
        test_loader: Test data loader
        device: Torch device
        label_names: Names of labels
        output_dir: Directory to save outputs
    
    Returns:
        Dictionary of evaluation results
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Collect predictions
    model.eval()
    all_preds = []
    all_labels = []
    all_probs = []
    all_texts = []
    
    with torch.no_grad():
        for batch in test_loader:
            # Move to device
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            
            # Get predictions
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            probs = torch.softmax(outputs.logits, dim=-1)
            preds = torch.argmax(probs, dim=-1)
            
            all_probs.extend(probs.cpu().numpy())
            all_preds.extend(preds.cpu().numpy())
            
            if 'labels' in batch:
                all_labels.extend(batch['labels'].numpy())
            
            if 'text' in batch:
                all_texts.extend(batch['text'])
    
    # Convert to numpy arrays
    y_true = np.array(all_labels)
    y_pred = np.array(all_preds)
    y_proba = np.array(all_probs)
    
    # Calculate metrics
    metrics = calculate_metrics(y_true, y_pred, y_proba, label_names)
    
    # Save metrics
    with open(output_path / 'metrics.json', 'w') as f:
        # Convert numpy arrays to lists for JSON serialization
        metrics_json = {
            k: v.tolist() if isinstance(v, np.ndarray) else v
            for k, v in metrics.items()
        }
        json.dump(metrics_json, f, indent=2)
    
    # Save classification report
    with open(output_path / 'classification_report.txt', 'w') as f:
        f.write(metrics['classification_report'])
    
    # Create visualizations
    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    plot_confusion_matrix(
        cm, label_names,
        save_path=str(output_path / 'confusion_matrix.png')
    )
    
    # ROC curves
    plot_roc_curves(
        y_true, y_proba, label_names,
        save_path=str(output_path / 'roc_curves.png')
    )
    
    # Precision-recall curves
    plot_precision_recall_curves(
        y_true, y_proba, label_names,
        save_path=str(output_path / 'pr_curves.png')
    )
    
    # Confidence distribution
    y_conf = np.max(y_proba, axis=1)
    y_correct = y_true == y_pred
    plot_confidence_distribution(
        y_conf, y_correct,
        save_path=str(output_path / 'confidence_dist.png')
    )
    
    # Error analysis
    error_df = pd.DataFrame({
        'text': all_texts,
        'true_label': [label_names[i] for i in y_true],
        'pred_label': [label_names[i] for i in y_pred],
        'confidence': y_conf,
        'correct': y_correct
    })
    
    # Save error examples
    errors = error_df[~error_df['correct']].sort_values('confidence', ascending=False)
    errors.head(50).to_csv(output_path / 'error_examples.csv', index=False)
    
    # Low confidence correct predictions
    low_conf_correct = error_df[error_df['correct']].sort_values('confidence')
    low_conf_correct.head(50).to_csv(
        output_path / 'low_confidence_correct.csv', index=False
    )
    
    logger.info(f"Evaluation report saved to {output_path}")
    
    return metrics