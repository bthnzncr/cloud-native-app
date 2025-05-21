#!/usr/bin/env python3
"""
Production model training script for News Consumer Service.
This script handles both filtering the dataset and training the model.
"""

import json
import logging
import pickle
import os
import time
import argparse
import sys
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MODEL_DIR = "./models"
MODEL_FILE = "./models/filtered_news_model.pkl"
DATASET_FILE = "./News_Category_Dataset.json"
FILTERED_DATASET_FILE = "./Filtered_News_Dataset.json"
ALLOWED_CATEGORIES = ["POLITICS", "ENTERTAINMENT", "BUSINESS"]

def filter_dataset(input_file, output_file, categories):
    """
    Filter dataset to only include specified categories.
    """
    if not os.path.exists(input_file):
        logger.error(f"Input file {input_file} not found")
        return False
    
    start_time = time.time()
    logger.info(f"Filtering dataset to categories: {', '.join(categories)}")
    
    # Counters
    total_count = 0
    filtered_count = 0
    category_counts = {category: 0 for category in categories}
    
    try:
        with open(input_file, 'r', encoding='utf-8') as infile, \
             open(output_file, 'w', encoding='utf-8') as outfile:
            
            # Process line by line
            for line in infile:
                if not line.strip():
                    continue
                
                total_count += 1
                
                try:
                    article = json.loads(line.strip())
                    category = article.get('category')
                    
                    # Filter by categories
                    if category in categories:
                        outfile.write(line)
                        filtered_count += 1
                        category_counts[category] += 1
                        
                    # Print progress
                    if total_count % 20000 == 0:
                        logger.info(f"Processed {total_count} records, kept {filtered_count}")
                        
                except json.JSONDecodeError:
                    continue
        
        # Summary
        elapsed_time = time.time() - start_time
        logger.info(f"Filtering completed in {elapsed_time:.2f} seconds")
        logger.info(f"Total records processed: {total_count}")
        logger.info(f"Records kept: {filtered_count} ({filtered_count/total_count*100:.1f}%)")
        
        logger.info("Category distribution:")
        for category, count in category_counts.items():
            if filtered_count > 0:
                logger.info(f"  {category}: {count} records ({count/filtered_count*100:.1f}%)")
        
        return True
    
    except Exception as e:
        logger.error(f"Error filtering dataset: {e}")
        return False

def train_model(dataset_file, model_file):
    """
    Train model on filtered dataset with 80-20 split.
    """
    start_time = time.time()
    logger.info(f"Training model on filtered dataset")
    
    # Create models directory if needed
    os.makedirs(os.path.dirname(model_file), exist_ok=True)
    
    # Check dataset
    if not os.path.exists(dataset_file):
        logger.error(f"Dataset file {dataset_file} not found")
        return False
    
    try:
        # Load dataset
        articles = []
        category_counts = {category: 0 for category in ALLOWED_CATEGORIES}
        
        with open(dataset_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        article = json.loads(line.strip())
                        category = article.get('category')
                        if category in ALLOWED_CATEGORIES:
                            headline = article.get('headline', '')
                            desc = article.get('short_description', '')
                            text = f"{headline} {desc}"
                            articles.append((text, category))
                            category_counts[category] += 1
                    except json.JSONDecodeError:
                        continue
        
        if not articles:
            logger.error("No valid articles found in dataset")
            return False
        
        logger.info(f"Loaded {len(articles)} articles for training")
        
        # Prepare data
        texts, labels = zip(*articles)
        
        # 80-20 train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            texts, labels, test_size=0.2, random_state=42, stratify=labels
        )
        
        logger.info(f"Training set: {len(X_train)} samples, Test set: {len(X_test)} samples")
        
        # Create and train model
        pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(max_features=10000, stop_words='english')),
            ('classifier', MultinomialNB())
        ])
        
        logger.info("Training model...")
        train_start = time.time()
        pipeline.fit(X_train, y_train)
        train_time = time.time() - train_start
        logger.info(f"Training completed in {train_time:.2f} seconds")
        
        # Evaluate
        y_pred = pipeline.predict(X_test)
        accuracy = sum(y_pred == y_test) / len(y_test)
        logger.info(f"Model accuracy: {accuracy:.4f}")
        
        # Classification report
        report = classification_report(y_test, y_pred)
        logger.info(f"Classification report:\n{report}")
        
        # Save model
        logger.info(f"Saving model to {model_file}")
        with open(model_file, 'wb') as f:
            pickle.dump({
                'pipeline': pipeline,
                'categories': ALLOWED_CATEGORIES,
                'accuracy': accuracy
            }, f)
        
        elapsed_time = time.time() - start_time
        logger.info(f"Total processing time: {elapsed_time:.2f} seconds")
        
        return True
        
    except Exception as e:
        logger.error(f"Error training model: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Filter dataset and train news categorization model')
    parser.add_argument('--filter-only', action='store_true', help='Only filter the dataset, don\'t train')
    parser.add_argument('--train-only', action='store_true', help='Only train the model, assuming filtered dataset exists')
    parser.add_argument('--input', type=str, default=DATASET_FILE, help='Input dataset file')
    parser.add_argument('--output', type=str, default=FILTERED_DATASET_FILE, help='Output filtered dataset file')
    parser.add_argument('--categories', type=str, nargs='+', default=ALLOWED_CATEGORIES, 
                        help='Categories to include')
    
    args = parser.parse_args()
    
    # Default: do both filtering and training
    do_filter = not args.train_only
    do_train = not args.filter_only
    
    # Filter dataset if requested
    if do_filter:
        logger.info("Step 1: Filtering dataset")
        if not filter_dataset(args.input, args.output, args.categories):
            logger.error("Dataset filtering failed")
            return 1
    
    # Train model if requested
    if do_train:
        logger.info("Step 2: Training model")
        if not train_model(args.output, MODEL_FILE):
            logger.error("Model training failed")
            return 1
    
    logger.info("All tasks completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 