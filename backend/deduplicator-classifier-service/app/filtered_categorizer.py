"""
Production-ready news categorizer that classifies articles as POLITICS, ENTERTAINMENT, or BUSINESS.
"""

import logging
import pickle
import os
from typing import Tuple, List, Optional

# Configure logging
logger = logging.getLogger(__name__)

# Constants
MODEL_FILE = "./models/filtered_news_model.pkl"
ALLOWED_CATEGORIES = ["POLITICS", "ENTERTAINMENT", "BUSINESS"]
DEFAULT_CATEGORY = "UNCATEGORIZED"

class FilteredCategorizer:
    """Categorizer for news articles using a pre-trained model."""
    
    def __init__(self):
        self.pipeline = None
        self.categories = ALLOWED_CATEGORIES
        self.model_loaded = False
        self.load_model()
    
    def load_model(self) -> bool:
        """Loads the pre-trained model if it exists."""
        try:
            if os.path.exists(MODEL_FILE):
                with open(MODEL_FILE, 'rb') as f:
                    model_data = pickle.load(f)
                    self.pipeline = model_data.get('pipeline')
                    self.categories = model_data.get('categories', ALLOWED_CATEGORIES)
                
                self.model_loaded = self.pipeline is not None
                if self.model_loaded:
                    logger.info("Filtered categorizer model loaded successfully")
                else:
                    logger.warning("Model loaded but pipeline is missing")
                return self.model_loaded
            
            logger.warning(f"Model file {MODEL_FILE} not found")
            return False
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
    
    def predict_category(self, text: str) -> Tuple[str, List[Tuple[str, float]]]:
        """Predicts article category with confidence scores."""
        if not self.model_loaded:
            return DEFAULT_CATEGORY, []
        
        try:
            # Make prediction
            prediction = self.pipeline.predict([text])[0]
            
            # Get probabilities for each category
            probabilities = self.pipeline.predict_proba([text])[0]
            top_categories = [(self.categories[i], probabilities[i]) 
                             for i in range(len(self.categories))]
            top_categories.sort(key=lambda x: x[1], reverse=True)
            
            return prediction, top_categories
            
        except Exception as e:
            logger.error(f"Error predicting category: {e}")
            return DEFAULT_CATEGORY, []

# Singleton instance
filtered_categorizer = FilteredCategorizer()

def categorize_article(text: str) -> str:
    """Gets predicted category for article text."""
    if not filtered_categorizer.model_loaded:
        return DEFAULT_CATEGORY
    
    try:
        prediction, _ = filtered_categorizer.predict_category(text)
        return prediction
    except Exception:
        return DEFAULT_CATEGORY

def get_category_probabilities(text: str) -> List[Tuple[str, float]]:
    """Gets probability scores for each possible category."""
    if not filtered_categorizer.model_loaded:
        return [(cat, 0.0) for cat in ALLOWED_CATEGORIES]
    
    try:
        _, probabilities = filtered_categorizer.predict_category(text)
        return probabilities
    except Exception:
        return [(cat, 0.0) for cat in ALLOWED_CATEGORIES] 