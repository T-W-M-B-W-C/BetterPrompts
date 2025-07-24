"""
DistilBERT-based intent classification model
A lighter, faster alternative to DeBERTa-v3 for resource-constrained environments
"""

import logging
from typing import Dict, List, Optional, Tuple
import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import (
    DistilBertModel,
    DistilBertConfig,
    DistilBertTokenizer,
    PreTrainedModel,
    PretrainedConfig
)
from transformers.modeling_outputs import SequenceClassifierOutput

logger = logging.getLogger(__name__)


class DistilBertIntentClassifierConfig(PretrainedConfig):
    """Configuration for DistilBERT intent classifier"""
    
    model_type = "distilbert_intent_classifier"
    
    def __init__(
        self,
        pretrained_model_name: str = "distilbert-base-uncased",
        num_labels: int = 10,
        hidden_dropout_prob: float = 0.1,
        attention_dropout_prob: float = 0.1,
        use_complexity_features: bool = True,
        complexity_hidden_size: int = 64,
        pooling_strategy: str = "cls",  # cls, mean, max, attention
        freeze_base_model: bool = False,
        freeze_layers: int = 0,
        classifier_hidden_size: int = 768,
        use_layer_norm: bool = True,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.pretrained_model_name = pretrained_model_name
        self.num_labels = num_labels
        self.hidden_dropout_prob = hidden_dropout_prob
        self.attention_dropout_prob = attention_dropout_prob
        self.use_complexity_features = use_complexity_features
        self.complexity_hidden_size = complexity_hidden_size
        self.pooling_strategy = pooling_strategy
        self.freeze_base_model = freeze_base_model
        self.freeze_layers = freeze_layers
        self.classifier_hidden_size = classifier_hidden_size
        self.use_layer_norm = use_layer_norm


class AttentionPooling(nn.Module):
    """Attention-based pooling layer for DistilBERT"""
    
    def __init__(self, hidden_size: int):
        super().__init__()
        self.attention = nn.Linear(hidden_size, 1)
    
    def forward(self, hidden_states: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        # Calculate attention scores
        attention_scores = self.attention(hidden_states).squeeze(-1)
        
        # Apply attention mask
        attention_scores = attention_scores.masked_fill(
            attention_mask == 0,
            float('-inf')
        )
        
        # Calculate attention weights
        attention_weights = F.softmax(attention_scores, dim=1).unsqueeze(-1)
        
        # Apply attention weights
        pooled_output = torch.sum(hidden_states * attention_weights, dim=1)
        
        return pooled_output


class DistilBertIntentClassifier(PreTrainedModel):
    """DistilBERT-based intent classification model
    
    This model is optimized for:
    - Faster inference (2x faster than BERT)
    - Smaller memory footprint (40% smaller)
    - Maintains 97% of BERT's performance
    """
    
    config_class = DistilBertIntentClassifierConfig
    base_model_prefix = "distilbert"
    
    def __init__(self, config: DistilBertIntentClassifierConfig):
        super().__init__(config)
        
        # Load base DistilBERT model
        self.distilbert = DistilBertModel.from_pretrained(
            config.pretrained_model_name
        )
        
        # Freeze base model layers if requested
        if config.freeze_base_model:
            for param in self.distilbert.parameters():
                param.requires_grad = False
        elif config.freeze_layers > 0:
            # Freeze specific number of transformer layers
            modules_to_freeze = list(self.distilbert.transformer.layer[:config.freeze_layers])
            for module in modules_to_freeze:
                for param in module.parameters():
                    param.requires_grad = False
        
        # Get hidden size from base model
        self.hidden_size = self.distilbert.config.hidden_size
        
        # Pooling strategy
        self.pooling_strategy = config.pooling_strategy
        if self.pooling_strategy == "attention":
            self.attention_pooling = AttentionPooling(self.hidden_size)
        
        # Dropout
        self.dropout = nn.Dropout(config.hidden_dropout_prob)
        
        # Complexity feature processing
        self.use_complexity_features = config.use_complexity_features
        if self.use_complexity_features:
            self.complexity_fc = nn.Sequential(
                nn.Linear(3, config.complexity_hidden_size),  # 3 features: complexity, word_count, code_indicators
                nn.ReLU(),
                nn.Dropout(config.hidden_dropout_prob),
                nn.Linear(config.complexity_hidden_size, config.complexity_hidden_size),
                nn.ReLU()
            )
            classifier_input_size = self.hidden_size + config.complexity_hidden_size
        else:
            classifier_input_size = self.hidden_size
        
        # Classification head with optional layer normalization
        layers = []
        
        # First layer
        layers.append(nn.Linear(classifier_input_size, config.classifier_hidden_size))
        if config.use_layer_norm:
            layers.append(nn.LayerNorm(config.classifier_hidden_size))
        layers.append(nn.ReLU())
        layers.append(nn.Dropout(config.hidden_dropout_prob))
        
        # Second layer (smaller for efficiency)
        layers.append(nn.Linear(config.classifier_hidden_size, config.classifier_hidden_size // 2))
        if config.use_layer_norm:
            layers.append(nn.LayerNorm(config.classifier_hidden_size // 2))
        layers.append(nn.ReLU())
        layers.append(nn.Dropout(config.hidden_dropout_prob))
        
        # Output layer
        layers.append(nn.Linear(config.classifier_hidden_size // 2, config.num_labels))
        
        self.classifier = nn.Sequential(*layers)
        
        # Complexity regression head (auxiliary task)
        self.complexity_predictor = nn.Sequential(
            nn.Linear(self.hidden_size, self.hidden_size // 4),
            nn.ReLU(),
            nn.Dropout(config.hidden_dropout_prob),
            nn.Linear(self.hidden_size // 4, 1),
            nn.Sigmoid()  # Output between 0 and 1
        )
        
        # Initialize weights
        self._init_weights()
        
        logger.info(f"Initialized DistilBertIntentClassifier with {self._count_parameters()} parameters")
    
    def _count_parameters(self) -> int:
        """Count trainable parameters"""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
    
    def _init_weights(self):
        """Initialize weights for new layers"""
        # Initialize classifier
        for module in self.classifier.modules():
            if isinstance(module, nn.Linear):
                module.weight.data.normal_(mean=0.0, std=0.02)
                if module.bias is not None:
                    module.bias.data.zero_()
            elif isinstance(module, nn.LayerNorm):
                module.bias.data.zero_()
                module.weight.data.fill_(1.0)
        
        # Initialize complexity layers
        if self.use_complexity_features:
            for module in self.complexity_fc.modules():
                if isinstance(module, nn.Linear):
                    module.weight.data.normal_(mean=0.0, std=0.02)
                    if module.bias is not None:
                        module.bias.data.zero_()
        
        # Initialize complexity predictor
        for module in self.complexity_predictor.modules():
            if isinstance(module, nn.Linear):
                module.weight.data.normal_(mean=0.0, std=0.02)
                if module.bias is not None:
                    module.bias.data.zero_()
    
    def pool_hidden_states(
        self,
        hidden_states: torch.Tensor,
        attention_mask: torch.Tensor
    ) -> torch.Tensor:
        """Pool hidden states based on strategy"""
        if self.pooling_strategy == "cls":
            # Use [CLS] token representation
            pooled_output = hidden_states[:, 0]
        elif self.pooling_strategy == "mean":
            # Mean pooling
            input_mask_expanded = attention_mask.unsqueeze(-1).expand(hidden_states.size()).float()
            sum_embeddings = torch.sum(hidden_states * input_mask_expanded, 1)
            sum_mask = input_mask_expanded.sum(1)
            sum_mask = torch.clamp(sum_mask, min=1e-9)
            pooled_output = sum_embeddings / sum_mask
        elif self.pooling_strategy == "max":
            # Max pooling
            input_mask_expanded = attention_mask.unsqueeze(-1).expand(hidden_states.size())
            hidden_states[input_mask_expanded == 0] = -1e9
            pooled_output = torch.max(hidden_states, 1)[0]
        elif self.pooling_strategy == "attention":
            # Attention pooling
            pooled_output = self.attention_pooling(hidden_states, attention_mask)
        else:
            raise ValueError(f"Unknown pooling strategy: {self.pooling_strategy}")
        
        return pooled_output
    
    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        labels: Optional[torch.Tensor] = None,
        complexity: Optional[torch.Tensor] = None,
        word_count: Optional[torch.Tensor] = None,
        code_indicators: Optional[torch.Tensor] = None,
        return_dict: bool = True,
        output_attentions: bool = False,
        output_hidden_states: bool = False,
    ) -> SequenceClassifierOutput:
        """Forward pass"""
        # Get DistilBERT outputs
        outputs = self.distilbert(
            input_ids=input_ids,
            attention_mask=attention_mask,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
        )
        
        # Get hidden states
        hidden_states = outputs.last_hidden_state
        
        # Pool hidden states
        pooled_output = self.pool_hidden_states(hidden_states, attention_mask)
        pooled_output = self.dropout(pooled_output)
        
        # Process complexity features if available
        if self.use_complexity_features and complexity is not None:
            # Stack features
            complexity_features = torch.stack([
                complexity,
                word_count.float() / 100.0,  # Normalize word count
                code_indicators.float()
            ], dim=1)
            
            # Process features
            complexity_embedding = self.complexity_fc(complexity_features)
            
            # Concatenate with pooled output
            classifier_input = torch.cat([pooled_output, complexity_embedding], dim=1)
        else:
            classifier_input = pooled_output
        
        # Classification
        logits = self.classifier(classifier_input)
        
        # Complexity prediction (auxiliary task)
        complexity_pred = self.complexity_predictor(pooled_output)
        
        # Calculate loss
        loss = None
        if labels is not None:
            loss_fct = nn.CrossEntropyLoss()
            classification_loss = loss_fct(logits, labels)
            
            # Add complexity loss if ground truth is available
            if complexity is not None:
                complexity_loss = F.mse_loss(complexity_pred.squeeze(), complexity)
                loss = classification_loss + 0.1 * complexity_loss  # Weight complexity loss
            else:
                loss = classification_loss
        
        return SequenceClassifierOutput(
            loss=loss,
            logits=logits,
            hidden_states=outputs.hidden_states,
            attentions=outputs.attentions,
        )
    
    def predict(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        **kwargs
    ) -> Dict[str, torch.Tensor]:
        """Predict intent and complexity"""
        with torch.no_grad():
            outputs = self.forward(
                input_ids=input_ids,
                attention_mask=attention_mask,
                **kwargs
            )
            
            # Get predictions
            intent_probs = F.softmax(outputs.logits, dim=-1)
            intent_preds = torch.argmax(intent_probs, dim=-1)
            
            # Get complexity predictions
            distilbert_outputs = self.distilbert(
                input_ids=input_ids,
                attention_mask=attention_mask
            )
            pooled_output = self.pool_hidden_states(
                distilbert_outputs.last_hidden_state,
                attention_mask
            )
            complexity_preds = self.complexity_predictor(pooled_output).squeeze()
            
            return {
                'intent_logits': outputs.logits,
                'intent_probs': intent_probs,
                'intent_preds': intent_preds,
                'complexity_preds': complexity_preds
            }
    
    @classmethod
    def from_deberta_checkpoint(
        cls,
        deberta_checkpoint_path: str,
        config: Optional[DistilBertIntentClassifierConfig] = None
    ) -> "DistilBertIntentClassifier":
        """Load from a DeBERTa checkpoint with weight mapping
        
        This allows leveraging pre-trained DeBERTa weights when available
        """
        if config is None:
            config = DistilBertIntentClassifierConfig()
        
        # Create new model
        model = cls(config)
        
        # Load DeBERTa checkpoint
        deberta_state = torch.load(deberta_checkpoint_path, map_location='cpu')
        
        # Map compatible weights
        # Note: This is a simplified mapping - in practice, you'd need more sophisticated
        # weight mapping between DeBERTa and DistilBERT architectures
        logger.info("Mapping weights from DeBERTa checkpoint...")
        
        # Load classifier and complexity predictor weights if compatible
        distilbert_state = model.state_dict()
        for key in ['classifier', 'complexity_predictor', 'complexity_fc']:
            if key in deberta_state and key in distilbert_state:
                if deberta_state[key].shape == distilbert_state[key].shape:
                    distilbert_state[key] = deberta_state[key]
                    logger.info(f"Loaded {key} weights from DeBERTa checkpoint")
        
        model.load_state_dict(distilbert_state, strict=False)
        
        return model


def create_distilbert_model(
    config_path: str = None,
    num_labels: int = 10,
    **kwargs
) -> DistilBertIntentClassifier:
    """Create DistilBERT intent classifier model
    
    Args:
        config_path: Path to YAML configuration file
        num_labels: Number of intent labels
        **kwargs: Additional configuration parameters
    
    Returns:
        DistilBertIntentClassifier model
    """
    if config_path:
        import yaml
        with open(config_path, 'r') as f:
            config_dict = yaml.safe_load(f)
        
        # Look for DistilBERT-specific config, fall back to general config
        model_config = config_dict.get('model', {}).get('distilbert_classifier', {})
        if not model_config:
            # Use DeBERTa config as template but with DistilBERT model
            model_config = config_dict.get('model', {}).get('intent_classifier', {})
            model_config['pretrained_model'] = 'distilbert-base-uncased'
        
        config = DistilBertIntentClassifierConfig(
            pretrained_model_name=model_config.get('pretrained_model', 'distilbert-base-uncased'),
            num_labels=model_config.get('num_labels', num_labels),
            hidden_dropout_prob=model_config.get('hidden_dropout_prob', 0.1),
            attention_dropout_prob=model_config.get('attention_dropout_prob', 0.1),
            **kwargs
        )
    else:
        config = DistilBertIntentClassifierConfig(
            num_labels=num_labels,
            **kwargs
        )
    
    model = DistilBertIntentClassifier(config)
    logger.info(f"Created DistilBertIntentClassifier model with {num_labels} labels")
    
    return model