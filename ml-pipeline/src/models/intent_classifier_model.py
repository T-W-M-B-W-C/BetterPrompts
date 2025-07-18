"""
DeBERTa-v3 based intent classification model
"""

import logging
from typing import Dict, List, Optional, Tuple
import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import (
    AutoModel,
    AutoTokenizer,
    AutoConfig,
    PreTrainedModel,
    PretrainedConfig
)
from transformers.modeling_outputs import SequenceClassifierOutput

logger = logging.getLogger(__name__)


class IntentClassifierConfig(PretrainedConfig):
    """Configuration for intent classifier"""
    
    model_type = "intent_classifier"
    
    def __init__(
        self,
        pretrained_model_name: str = "microsoft/deberta-v3-base",
        num_labels: int = 10,
        hidden_dropout_prob: float = 0.1,
        attention_dropout_prob: float = 0.1,
        use_complexity_features: bool = True,
        complexity_hidden_size: int = 64,
        pooling_strategy: str = "cls",  # cls, mean, max, attention
        freeze_base_model: bool = False,
        freeze_layers: int = 0,
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


class AttentionPooling(nn.Module):
    """Attention-based pooling layer"""
    
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


class IntentClassifier(PreTrainedModel):
    """DeBERTa-v3 based intent classification model"""
    
    config_class = IntentClassifierConfig
    base_model_prefix = "deberta"
    
    def __init__(self, config: IntentClassifierConfig):
        super().__init__(config)
        
        # Load base model
        self.base_model_config = AutoConfig.from_pretrained(config.pretrained_model_name)
        self.base_model = AutoModel.from_pretrained(
            config.pretrained_model_name,
            config=self.base_model_config
        )
        
        # Freeze base model layers if requested
        if config.freeze_base_model:
            for param in self.base_model.parameters():
                param.requires_grad = False
        elif config.freeze_layers > 0:
            # Freeze specific number of layers
            modules_to_freeze = list(self.base_model.encoder.layer[:config.freeze_layers])
            for module in modules_to_freeze:
                for param in module.parameters():
                    param.requires_grad = False
        
        # Get hidden size from base model
        self.hidden_size = self.base_model_config.hidden_size
        
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
        
        # Classification head
        self.classifier = nn.Sequential(
            nn.Linear(classifier_input_size, self.hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(config.hidden_dropout_prob),
            nn.Linear(self.hidden_size // 2, config.num_labels)
        )
        
        # Complexity regression head (optional)
        self.complexity_predictor = nn.Sequential(
            nn.Linear(self.hidden_size, self.hidden_size // 4),
            nn.ReLU(),
            nn.Dropout(config.hidden_dropout_prob),
            nn.Linear(self.hidden_size // 4, 1),
            nn.Sigmoid()  # Output between 0 and 1
        )
        
        # Initialize weights
        self._init_weights()
    
    def _init_weights(self):
        """Initialize weights for new layers"""
        # Initialize classifier
        for module in self.classifier.modules():
            if isinstance(module, nn.Linear):
                module.weight.data.normal_(mean=0.0, std=0.02)
                if module.bias is not None:
                    module.bias.data.zero_()
        
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
        token_type_ids: Optional[torch.Tensor] = None,
        labels: Optional[torch.Tensor] = None,
        complexity: Optional[torch.Tensor] = None,
        word_count: Optional[torch.Tensor] = None,
        code_indicators: Optional[torch.Tensor] = None,
        return_dict: bool = True,
        output_attentions: bool = False,
        output_hidden_states: bool = False,
    ) -> SequenceClassifierOutput:
        """Forward pass"""
        # Get base model outputs
        outputs = self.base_model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
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
            base_outputs = self.base_model(
                input_ids=input_ids,
                attention_mask=attention_mask
            )
            pooled_output = self.pool_hidden_states(
                base_outputs.last_hidden_state,
                attention_mask
            )
            complexity_preds = self.complexity_predictor(pooled_output).squeeze()
            
            return {
                'intent_logits': outputs.logits,
                'intent_probs': intent_probs,
                'intent_preds': intent_preds,
                'complexity_preds': complexity_preds
            }


def create_model(config_path: str = None, num_labels: int = 10) -> IntentClassifier:
    """Create intent classifier model"""
    if config_path:
        import yaml
        with open(config_path, 'r') as f:
            config_dict = yaml.safe_load(f)
        
        model_config = config_dict['model']['intent_classifier']
        config = IntentClassifierConfig(
            pretrained_model_name=model_config['pretrained_model'],
            num_labels=model_config['num_labels'],
            hidden_dropout_prob=model_config['hidden_dropout_prob'],
            attention_dropout_prob=model_config['attention_dropout_prob']
        )
    else:
        config = IntentClassifierConfig(num_labels=num_labels)
    
    model = IntentClassifier(config)
    logger.info(f"Created IntentClassifier model with {num_labels} labels")
    
    return model