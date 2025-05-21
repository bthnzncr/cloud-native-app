import json
import logging
import pickle
import os
import time
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
MODEL_FILE = "./models/news_category_model.pkl"
VECTORIZER_FILE = "./models/news_tfidf_vectorizer.pkl"
DATASET_PATH = "./News_Category_Dataset.json"
MODEL_DIR = "./models"

class NewsCategorizer:
    def __init__(self):
        self.pipeline = None
        self.categories = None
        # Create models directory if it doesn't exist
        if not os.path.exists(MODEL_DIR):
            os.makedirs(MODEL_DIR)
        
        # Try to load pre-trained model
        self.load_model()
    
    def load_model(self):
        """Loads the pre-trained model if it exists."""
        try:
            if os.path.exists(MODEL_FILE) and os.path.exists(VECTORIZER_FILE):
                with open(MODEL_FILE, 'rb') as f:
                    self.pipeline = pickle.load(f)
                with open(VECTORIZER_FILE, 'rb') as f:
                    model_info = pickle.load(f)
                    self.categories = model_info.get('categories')
                logger.info("Pre-trained model loaded successfully")
                return True
            return False
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
    
    def save_model(self):
        """Saves the trained model."""
        try:
            # Save the classifier pipeline
            with open(MODEL_FILE, 'wb') as f:
                pickle.dump(self.pipeline, f)
            
            # Save the categories
            with open(VECTORIZER_FILE, 'wb') as f:
                model_info = {'categories': self.categories}
                pickle.dump(model_info, f)
            
            logger.info("Model saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            return False
    
    def train(self, max_samples=125000):
        """Trains the categorizer model using the news dataset."""
        start_time = time.time()
        logger.info(f"Training news categorizer model with max_samples={max_samples}...")
        
        try:
            # Load the dataset
            training_data = []
            training_labels = []
            categories_set = set()
            category_counts = {}
            
            # First, count total records for progress reporting
            total_records = 0
            with open(DATASET_PATH, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        total_records += 1
            
            logger.info(f"Dataset contains {total_records} total records")
            
            # Process the dataset line by line to avoid loading it all into memory
            count = 0
            last_report = 0
            report_interval = max(1, min(10000, total_records // 10))  # Report progress at most 10 times
            
            with open(DATASET_PATH, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        if not line.strip():
                            continue
                            
                        article = json.loads(line.strip())
                        # Use headline and short_description for training
                        text = f"{article.get('headline', '')} {article.get('short_description', '')}"
                        category = article.get('category')
                        
                        if text and category:
                            training_data.append(text)
                            training_labels.append(category)
                            categories_set.add(category)
                            
                            # Update category count
                            if category in category_counts:
                                category_counts[category] += 1
                            else:
                                category_counts[category] = 1
                                
                            count += 1
                            
                            # Report progress
                            if count - last_report >= report_interval:
                                logger.info(f"Loaded {count}/{min(total_records, max_samples)} samples ({count/min(total_records, max_samples)*100:.1f}%)")
                                last_report = count
                            
                            if count >= max_samples:
                                break
                    except json.JSONDecodeError:
                        continue
            
            if not training_data:
                logger.error("No training data could be loaded")
                return False
            
            logger.info(f"Loaded {len(training_data)} training samples with {len(categories_set)} categories")
            
            # Report top categories
            sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
            logger.info("Top 5 categories by frequency:")
            for category, count in sorted_categories[:5]:
                logger.info(f"  {category}: {count} samples ({count/len(training_data)*100:.1f}%)")
            
            # Convert categories to a list for indexing
            self.categories = list(categories_set)
            
            # Split into training and validation sets
            logger.info("Splitting data into 80% training and 20% validation sets...")
            X_train, X_val, y_train, y_val = train_test_split(
                training_data, training_labels, test_size=0.2, random_state=42
            )
            
            logger.info(f"Training set: {len(X_train)} samples, Validation set: {len(X_val)} samples")
            
            # Create and train the pipeline
            logger.info("Training TF-IDF vectorizer and MultinomialNB classifier...")
            self.pipeline = Pipeline([
                ('tfidf', TfidfVectorizer(max_features=15000, stop_words='english')),
                ('classifier', MultinomialNB())
            ])
            
            fit_start = time.time()
            self.pipeline.fit(X_train, y_train)
            fit_time = time.time() - fit_start
            logger.info(f"Model fitting completed in {fit_time:.2f} seconds")
            
            # Evaluate on validation set
            val_start = time.time()
            accuracy = self.pipeline.score(X_val, y_val)
            val_time = time.time() - val_start
            logger.info(f"Validation completed in {val_time:.2f} seconds")
            logger.info(f"Model trained with validation accuracy: {accuracy:.4f}")
            
            # Save the model
            save_start = time.time()
            self.save_model()
            save_time = time.time() - save_start
            logger.info(f"Model saving completed in {save_time:.2f} seconds")
            
            total_time = time.time() - start_time
            logger.info(f"Total training process completed in {total_time:.2f} seconds")
            
            return True
            
        except Exception as e:
            logger.error(f"Error training model: {e}", exc_info=True)
            return False
    
    def predict_category(self, text):
        """Predicts the category of a news article."""
        if not self.pipeline or not self.categories:
            logger.error("Model not loaded. Please train or load a model first.")
            return None
        
        try:
            # Make prediction
            prediction = self.pipeline.predict([text])[0]
            
            # Get top categories with probabilities
            probs = self.pipeline.predict_proba([text])[0]
            top_categories = [(self.categories[i], probs[i]) for i in np.argsort(-probs)[:3]]
            
            return prediction, top_categories
        except Exception as e:
            logger.error(f"Error predicting category: {e}")
            return None, []
            
    def test_model_split(self, max_samples=1000):
        """Tests the model with 80-20 split directly without saving."""
        logger.info("Testing model with 80-20 split...")
        
        try:
            # Load a sample of the dataset
            training_data = []
            training_labels = []
            categories_set = set()
            
            # Process the dataset line by line
            count = 0
            with open(DATASET_PATH, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        article = json.loads(line.strip())
                        text = f"{article.get('headline', '')} {article.get('short_description', '')}"
                        category = article.get('category')
                        
                        if text and category:
                            training_data.append(text)
                            training_labels.append(category)
                            categories_set.add(category)
                            count += 1
                            
                            if count >= max_samples:
                                break
                    except json.JSONDecodeError:
                        continue
            
            if not training_data:
                logger.error("No test data could be loaded")
                return False
            
            logger.info(f"Loaded {len(training_data)} test samples with {len(categories_set)} categories")
            
            # Split into training (80%) and validation (20%) sets
            X_train, X_val, y_train, y_val = train_test_split(
                training_data, training_labels, test_size=0.2, random_state=42
            )
            
            logger.info(f"Split data into {len(X_train)} training samples and {len(X_val)} validation samples")
            logger.info(f"Training set size: {len(X_train)} ({len(X_train) / len(training_data) * 100:.1f}%)")
            logger.info(f"Validation set size: {len(X_val)} ({len(X_val) / len(training_data) * 100:.1f}%)")
            
            # Create and train a temporary pipeline
            pipeline = Pipeline([
                ('tfidf', TfidfVectorizer(max_features=10000, stop_words='english')),
                ('classifier', MultinomialNB())
            ])
            
            pipeline.fit(X_train, y_train)
            
            # Evaluate on validation set
            train_accuracy = pipeline.score(X_train, y_train)
            val_accuracy = pipeline.score(X_val, y_val)
            
            logger.info(f"Training accuracy: {train_accuracy:.4f}")
            logger.info(f"Validation accuracy: {val_accuracy:.4f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error testing model: {e}", exc_info=True)
            return False

# Singleton instance
categorizer = NewsCategorizer()

def ensure_model_trained():
    """Ensures the model is trained if it hasn't been already."""
    if not categorizer.pipeline:
        logger.info("Model not found. Training new model...")
        categorizer.train()
    return categorizer.pipeline is not None

def get_category(text):
    """Gets the predicted category for a news article."""
    if ensure_model_trained():
        return categorizer.predict_category(text)
    return None, []

def test_model():
    """Tests the model with 80-20 split."""
    categorizer.test_model_split(max_samples=5000)

if __name__ == "__main__":
    test_model() 