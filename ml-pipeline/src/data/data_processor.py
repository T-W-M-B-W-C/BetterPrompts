"""
Data preprocessing pipeline for intent classification
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import hashlib

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from transformers import AutoTokenizer
import nltk
from nltk.corpus import wordnet
import spacy
from tqdm import tqdm
import yaml

logger = logging.getLogger(__name__)


class DataProcessor:
    """Handles data preprocessing for intent classification"""
    
    def __init__(self, config_path: str = "configs/ml_pipeline_config.yaml"):
        """Initialize data processor with configuration"""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config['model']['intent_classifier']['pretrained_model']
        )
        
        # Initialize spaCy for advanced NLP tasks
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except:
            logger.warning("spaCy model not found. Run: python -m spacy download en_core_web_sm")
            self.nlp = None
        
        # Download NLTK data
        try:
            nltk.download('wordnet', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
        except:
            logger.warning("Failed to download NLTK data")
        
        # Intent categories
        self.intent_labels = [
            "question_answering",
            "creative_writing", 
            "code_generation",
            "data_analysis",
            "reasoning",
            "summarization",
            "translation",
            "conversation",
            "task_planning",
            "problem_solving"
        ]
        
        self.label_to_id = {label: i for i, label in enumerate(self.intent_labels)}
        self.id_to_label = {i: label for label, i in self.label_to_id.items()}
    
    def load_raw_data(self, data_path: Union[str, Path]) -> pd.DataFrame:
        """Load raw data from various formats"""
        data_path = Path(data_path)
        
        if data_path.suffix == '.json':
            with open(data_path, 'r') as f:
                data = json.load(f)
            df = pd.DataFrame(data)
        elif data_path.suffix == '.jsonl':
            data = []
            with open(data_path, 'r') as f:
                for line in f:
                    data.append(json.loads(line))
            df = pd.DataFrame(data)
        elif data_path.suffix == '.csv':
            df = pd.read_csv(data_path)
        else:
            raise ValueError(f"Unsupported file format: {data_path.suffix}")
        
        logger.info(f"Loaded {len(df)} samples from {data_path}")
        return df
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Preserve code blocks (don't lowercase or remove special chars for code)
        if any(keyword in text.lower() for keyword in ['function', 'def', 'class', 'import', 'const', 'var']):
            return text.strip()
        
        # For non-code text, optionally lowercase
        if self.config['preprocessing'].get('lowercase', False):
            text = text.lower()
        
        return text.strip()
    
    def extract_features(self, text: str) -> Dict[str, float]:
        """Extract additional features from text"""
        features = {
            'length': len(text),
            'word_count': len(text.split()),
            'avg_word_length': np.mean([len(word) for word in text.split()]) if text.split() else 0,
            'question_marks': text.count('?'),
            'exclamation_marks': text.count('!'),
            'code_indicators': int(any(indicator in text for indicator in ['```', 'def ', 'function', 'import', 'class '])),
        }
        
        # Add spaCy features if available
        if self.nlp:
            doc = self.nlp(text[:1000])  # Limit to first 1000 chars for speed
            features['entity_count'] = len(doc.ents)
            features['noun_ratio'] = len([token for token in doc if token.pos_ == 'NOUN']) / len(doc) if len(doc) > 0 else 0
            features['verb_ratio'] = len([token for token in doc if token.pos_ == 'VERB']) / len(doc) if len(doc) > 0 else 0
        
        return features
    
    def calculate_complexity(self, text: str, features: Dict[str, float]) -> float:
        """Calculate prompt complexity score"""
        complexity = 0.0
        
        # Length-based complexity
        if features['word_count'] > 100:
            complexity += 0.2
        elif features['word_count'] > 50:
            complexity += 0.1
        
        # Question complexity
        if features['question_marks'] > 1:
            complexity += 0.1
        
        # Code complexity
        if features['code_indicators']:
            complexity += 0.2
        
        # Entity complexity
        if 'entity_count' in features and features['entity_count'] > 3:
            complexity += 0.1
        
        # Multi-step indicators
        multi_step_keywords = ['first', 'then', 'next', 'finally', 'step', 'stages']
        if any(keyword in text.lower() for keyword in multi_step_keywords):
            complexity += 0.2
        
        # Reasoning indicators
        reasoning_keywords = ['why', 'how', 'explain', 'analyze', 'compare', 'evaluate']
        if any(keyword in text.lower() for keyword in reasoning_keywords):
            complexity += 0.1
        
        return min(complexity, 1.0)  # Cap at 1.0
    
    def augment_text(self, text: str, technique: str = "paraphrase") -> str:
        """Augment text using various techniques"""
        if technique == "synonym_replacement":
            # Simple synonym replacement
            words = text.split()
            augmented_words = []
            
            for word in words:
                if np.random.random() < 0.1:  # Replace 10% of words
                    synonyms = []
                    for syn in wordnet.synsets(word):
                        for lemma in syn.lemmas():
                            if lemma.name() != word:
                                synonyms.append(lemma.name())
                    
                    if synonyms:
                        augmented_words.append(np.random.choice(synonyms))
                    else:
                        augmented_words.append(word)
                else:
                    augmented_words.append(word)
            
            return ' '.join(augmented_words)
        
        elif technique == "paraphrase":
            # Simple paraphrasing by reordering clauses
            sentences = text.split('.')
            if len(sentences) > 1:
                np.random.shuffle(sentences)
                return '. '.join(sentences).strip()
            return text
        
        elif technique == "back_translation":
            # Placeholder for back translation
            # In production, use a translation API
            return text + " (translated)"
        
        return text
    
    def preprocess_dataset(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preprocess entire dataset"""
        logger.info("Starting preprocessing...")
        
        # Clean text
        df['cleaned_text'] = df['text'].apply(self.clean_text)
        
        # Remove duplicates if configured
        if self.config['preprocessing']['remove_duplicates']:
            original_len = len(df)
            df = df.drop_duplicates(subset=['cleaned_text'])
            logger.info(f"Removed {original_len - len(df)} duplicates")
        
        # Filter by length
        min_length = self.config['preprocessing']['min_length']
        max_length = self.config['preprocessing']['max_length']
        df = df[df['cleaned_text'].str.len().between(min_length, max_length * 3)]  # Character limit
        
        # Extract features
        logger.info("Extracting features...")
        features_list = []
        for text in tqdm(df['cleaned_text'], desc="Feature extraction"):
            features_list.append(self.extract_features(text))
        
        features_df = pd.DataFrame(features_list)
        df = pd.concat([df, features_df], axis=1)
        
        # Calculate complexity if not provided
        if 'complexity' not in df.columns:
            df['complexity'] = df.apply(
                lambda row: self.calculate_complexity(row['cleaned_text'], row.to_dict()),
                axis=1
            )
        
        # Convert labels to IDs
        if 'intent' in df.columns:
            df['label_id'] = df['intent'].map(self.label_to_id)
            df = df[df['label_id'].notna()]  # Remove samples with unknown labels
        
        # Add text hash for tracking
        df['text_hash'] = df['cleaned_text'].apply(
            lambda x: hashlib.md5(x.encode()).hexdigest()
        )
        
        logger.info(f"Preprocessing complete. Final dataset size: {len(df)}")
        return df
    
    def tokenize_dataset(self, df: pd.DataFrame) -> Dict[str, np.ndarray]:
        """Tokenize dataset for model input"""
        logger.info("Tokenizing dataset...")
        
        encodings = self.tokenizer(
            df['cleaned_text'].tolist(),
            truncation=True,
            padding=True,
            max_length=self.config['preprocessing']['max_length'],
            return_tensors='np'
        )
        
        tokenized_data = {
            'input_ids': encodings['input_ids'],
            'attention_mask': encodings['attention_mask'],
        }
        
        if 'label_id' in df.columns:
            tokenized_data['labels'] = df['label_id'].values
        
        # Add additional features
        feature_columns = ['complexity', 'word_count', 'code_indicators']
        for col in feature_columns:
            if col in df.columns:
                tokenized_data[col] = df[col].values
        
        logger.info(f"Tokenization complete. Shape: {tokenized_data['input_ids'].shape}")
        return tokenized_data
    
    def split_dataset(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Split dataset into train, validation, and test sets"""
        train_ratio = self.config['data']['train_test_split']
        val_ratio = self.config['data']['validation_split']
        
        # First split: train+val vs test
        train_val_df, test_df = train_test_split(
            df, 
            test_size=1-train_ratio,
            random_state=self.config['data']['random_seed'],
            stratify=df['label_id'] if 'label_id' in df.columns else None
        )
        
        # Second split: train vs val
        train_df, val_df = train_test_split(
            train_val_df,
            test_size=val_ratio/(train_ratio),
            random_state=self.config['data']['random_seed'],
            stratify=train_val_df['label_id'] if 'label_id' in train_val_df.columns else None
        )
        
        logger.info(f"Dataset split - Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")
        return train_df, val_df, test_df
    
    def augment_dataset(self, df: pd.DataFrame) -> pd.DataFrame:
        """Augment training dataset"""
        if not self.config['preprocessing']['augmentation']['enabled']:
            return df
        
        logger.info("Augmenting dataset...")
        augmented_samples = []
        augmentation_factor = self.config['preprocessing']['augmentation']['augmentation_factor']
        techniques = self.config['preprocessing']['augmentation']['techniques']
        
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Augmentation"):
            for i in range(augmentation_factor - 1):
                technique = np.random.choice(techniques)
                augmented_text = self.augment_text(row['cleaned_text'], technique)
                
                augmented_row = row.copy()
                augmented_row['cleaned_text'] = augmented_text
                augmented_row['augmented'] = True
                augmented_row['augmentation_technique'] = technique
                augmented_samples.append(augmented_row)
        
        augmented_df = pd.DataFrame(augmented_samples)
        combined_df = pd.concat([df, augmented_df], ignore_index=True)
        
        logger.info(f"Augmentation complete. Dataset size: {len(df)} → {len(combined_df)}")
        return combined_df
    
    def save_processed_data(self, data: Dict[str, Union[pd.DataFrame, np.ndarray]], output_dir: str):
        """Save processed data to disk"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save DataFrames as parquet
        for key, value in data.items():
            if isinstance(value, pd.DataFrame):
                file_path = output_path / f"{key}.parquet"
                value.to_parquet(file_path, index=False)
                logger.info(f"Saved {key} to {file_path}")
            elif isinstance(value, dict):
                # Save tokenized data as numpy arrays
                np_dir = output_path / key
                np_dir.mkdir(exist_ok=True)
                for arr_name, arr_value in value.items():
                    np.save(np_dir / f"{arr_name}.npy", arr_value)
                logger.info(f"Saved {key} arrays to {np_dir}")
    
    def process_pipeline(self, input_path: str, output_dir: str):
        """Run complete preprocessing pipeline"""
        logger.info(f"Starting data processing pipeline...")
        
        # Load raw data
        df = self.load_raw_data(input_path)
        
        # Preprocess
        df = self.preprocess_dataset(df)
        
        # Split dataset
        train_df, val_df, test_df = self.split_dataset(df)
        
        # Augment training data
        train_df = self.augment_dataset(train_df)
        
        # Tokenize all splits
        train_tokens = self.tokenize_dataset(train_df)
        val_tokens = self.tokenize_dataset(val_df)
        test_tokens = self.tokenize_dataset(test_df)
        
        # Save processed data
        self.save_processed_data({
            'train_df': train_df,
            'val_df': val_df,
            'test_df': test_df,
            'train_tokens': train_tokens,
            'val_tokens': val_tokens,
            'test_tokens': test_tokens
        }, output_dir)
        
        # Save metadata
        metadata = {
            'intent_labels': self.intent_labels,
            'label_to_id': self.label_to_id,
            'train_size': len(train_df),
            'val_size': len(val_df),
            'test_size': len(test_df),
            'features': list(train_df.columns),
            'tokenizer': self.config['model']['intent_classifier']['pretrained_model']
        }
        
        with open(Path(output_dir) / 'metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Processing complete! Data saved to {output_dir}")