"""
Data loading utilities for training and inference
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer
import yaml

logger = logging.getLogger(__name__)


class IntentDataset(Dataset):
    """PyTorch dataset for intent classification"""
    
    def __init__(
        self, 
        data_dir: str,
        split: str = 'train',
        tokenizer_name: Optional[str] = None,
        max_length: int = 512,
        include_features: bool = True
    ):
        """
        Initialize dataset
        
        Args:
            data_dir: Directory containing processed data
            split: Data split ('train', 'val', 'test')
            tokenizer_name: Name of tokenizer to use
            max_length: Maximum sequence length
            include_features: Whether to include additional features
        """
        self.data_dir = Path(data_dir)
        self.split = split
        self.max_length = max_length
        self.include_features = include_features
        
        # Load metadata
        with open(self.data_dir / 'metadata.json', 'r') as f:
            self.metadata = json.load(f)
        
        # Initialize tokenizer
        if tokenizer_name:
            self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
        else:
            self.tokenizer = AutoTokenizer.from_pretrained(self.metadata['tokenizer'])
        
        # Load data
        self._load_data()
    
    def _load_data(self):
        """Load preprocessed data from disk"""
        # Load tokenized data
        token_dir = self.data_dir / f"{self.split}_tokens"
        self.input_ids = np.load(token_dir / 'input_ids.npy')
        self.attention_mask = np.load(token_dir / 'attention_mask.npy')
        
        if (token_dir / 'labels.npy').exists():
            self.labels = np.load(token_dir / 'labels.npy')
        else:
            self.labels = None
        
        # Load additional features if requested
        if self.include_features:
            self.features = {}
            feature_files = ['complexity', 'word_count', 'code_indicators']
            for feature in feature_files:
                feature_path = token_dir / f'{feature}.npy'
                if feature_path.exists():
                    self.features[feature] = np.load(feature_path)
        
        # Load DataFrame for text access
        df_path = self.data_dir / f"{self.split}_df.parquet"
        if df_path.exists():
            self.df = pd.read_parquet(df_path)
        else:
            self.df = None
        
        logger.info(f"Loaded {len(self)} samples for {self.split} split")
    
    def __len__(self) -> int:
        """Return dataset length"""
        return len(self.input_ids)
    
    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        """Get a single sample"""
        item = {
            'input_ids': torch.tensor(self.input_ids[idx], dtype=torch.long),
            'attention_mask': torch.tensor(self.attention_mask[idx], dtype=torch.long),
        }
        
        if self.labels is not None:
            item['labels'] = torch.tensor(self.labels[idx], dtype=torch.long)
        
        # Add features if available
        if self.include_features and self.features:
            for feature_name, feature_values in self.features.items():
                item[feature_name] = torch.tensor(feature_values[idx], dtype=torch.float)
        
        # Add text if DataFrame is available
        if self.df is not None:
            item['text'] = self.df.iloc[idx]['cleaned_text']
            if 'intent' in self.df.columns:
                item['intent'] = self.df.iloc[idx]['intent']
        
        return item
    
    def get_label_names(self) -> List[str]:
        """Get list of label names"""
        return self.metadata['intent_labels']
    
    def get_label_to_id(self) -> Dict[str, int]:
        """Get label to ID mapping"""
        return self.metadata['label_to_id']


class DataModule:
    """Manages data loading for training and inference"""
    
    def __init__(self, config_path: str = "configs/ml_pipeline_config.yaml"):
        """Initialize data module with configuration"""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.data_dir = Path(self.config['data']['processed_data_path'])
        self.batch_size = self.config['training']['batch_size']
        self.num_workers = 4  # Adjust based on system
    
    def setup(self, stage: Optional[str] = None):
        """Setup datasets for different stages"""
        if stage == 'fit' or stage is None:
            self.train_dataset = IntentDataset(
                self.data_dir,
                split='train',
                max_length=self.config['preprocessing']['max_length']
            )
            self.val_dataset = IntentDataset(
                self.data_dir,
                split='val',
                max_length=self.config['preprocessing']['max_length']
            )
        
        if stage == 'test' or stage is None:
            self.test_dataset = IntentDataset(
                self.data_dir,
                split='test',
                max_length=self.config['preprocessing']['max_length']
            )
    
    def train_dataloader(self) -> DataLoader:
        """Get training dataloader"""
        return DataLoader(
            self.train_dataset,
            batch_size=self.batch_size,
            shuffle=True,
            num_workers=self.num_workers,
            pin_memory=torch.cuda.is_available()
        )
    
    def val_dataloader(self) -> DataLoader:
        """Get validation dataloader"""
        return DataLoader(
            self.val_dataset,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=self.num_workers,
            pin_memory=torch.cuda.is_available()
        )
    
    def test_dataloader(self) -> DataLoader:
        """Get test dataloader"""
        return DataLoader(
            self.test_dataset,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=self.num_workers,
            pin_memory=torch.cuda.is_available()
        )
    
    def predict_dataloader(self, texts: List[str]) -> DataLoader:
        """Create dataloader for prediction"""
        # Tokenize texts
        tokenizer = self.train_dataset.tokenizer
        encodings = tokenizer(
            texts,
            truncation=True,
            padding=True,
            max_length=self.config['preprocessing']['max_length'],
            return_tensors='pt'
        )
        
        # Create simple dataset
        class PredictDataset(Dataset):
            def __init__(self, encodings, texts):
                self.encodings = encodings
                self.texts = texts
            
            def __len__(self):
                return len(self.texts)
            
            def __getitem__(self, idx):
                item = {key: val[idx] for key, val in self.encodings.items()}
                item['text'] = self.texts[idx]
                return item
        
        dataset = PredictDataset(encodings, texts)
        
        return DataLoader(
            dataset,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=0  # For prediction, use main thread
        )


class StreamingDataLoader:
    """Streaming data loader for large datasets"""
    
    def __init__(
        self,
        data_path: str,
        tokenizer_name: str,
        batch_size: int = 32,
        max_length: int = 512,
        shuffle: bool = True
    ):
        """
        Initialize streaming data loader
        
        Args:
            data_path: Path to JSONL data file
            tokenizer_name: Name of tokenizer
            batch_size: Batch size
            max_length: Maximum sequence length
            shuffle: Whether to shuffle data
        """
        self.data_path = Path(data_path)
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
        self.batch_size = batch_size
        self.max_length = max_length
        self.shuffle = shuffle
        
        # Count total lines for progress tracking
        self.total_samples = sum(1 for _ in open(self.data_path, 'r'))
    
    def __iter__(self):
        """Iterate over batches"""
        # Load all data if shuffling
        if self.shuffle:
            with open(self.data_path, 'r') as f:
                lines = f.readlines()
            np.random.shuffle(lines)
            data_iter = iter(lines)
        else:
            data_iter = open(self.data_path, 'r')
        
        batch_texts = []
        batch_labels = []
        
        for line in data_iter:
            sample = json.loads(line)
            batch_texts.append(sample['text'])
            
            if 'intent' in sample:
                batch_labels.append(sample['intent'])
            
            if len(batch_texts) == self.batch_size:
                # Tokenize batch
                encodings = self.tokenizer(
                    batch_texts,
                    truncation=True,
                    padding=True,
                    max_length=self.max_length,
                    return_tensors='pt'
                )
                
                batch = {
                    'input_ids': encodings['input_ids'],
                    'attention_mask': encodings['attention_mask'],
                }
                
                if batch_labels:
                    batch['labels'] = batch_labels
                
                yield batch
                
                # Reset batch
                batch_texts = []
                batch_labels = []
        
        # Handle remaining samples
        if batch_texts:
            encodings = self.tokenizer(
                batch_texts,
                truncation=True,
                padding=True,
                max_length=self.max_length,
                return_tensors='pt'
            )
            
            batch = {
                'input_ids': encodings['input_ids'],
                'attention_mask': encodings['attention_mask'],
            }
            
            if batch_labels:
                batch['labels'] = batch_labels
            
            yield batch
        
        # Close file if not shuffling
        if not self.shuffle:
            data_iter.close()


def create_dataloaders(
    data_dir: str,
    batch_size: int = 32,
    num_workers: int = 4
) -> Tuple[DataLoader, DataLoader, DataLoader]:
    """
    Create train, validation, and test dataloaders
    
    Args:
        data_dir: Directory with processed data
        batch_size: Batch size
        num_workers: Number of workers for data loading
    
    Returns:
        Tuple of (train_loader, val_loader, test_loader)
    """
    train_dataset = IntentDataset(data_dir, split='train')
    val_dataset = IntentDataset(data_dir, split='val')
    test_dataset = IntentDataset(data_dir, split='test')
    
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available()
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available()
    )
    
    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available()
    )
    
    return train_loader, val_loader, test_loader