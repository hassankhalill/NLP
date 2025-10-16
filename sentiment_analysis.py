"""
Sentiment Analysis Module for Arabic and English Reviews
Uses multiple approaches including transformers and rule-based methods.
"""

import re
import pandas as pd
import numpy as np
from typing import Dict, Tuple, List
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import warnings
warnings.filterwarnings('ignore')


class MultilingualSentimentAnalyzer:
    """Sentiment analyzer supporting both Arabic and English."""

    def __init__(self, use_transformers=True):
        """
        Initialize the sentiment analyzer.

        Args:
            use_transformers: Whether to use transformer models (requires torch)
        """
        self.use_transformers = use_transformers
        self.model = None
        self.tokenizer = None

        if use_transformers:
            try:
                self._load_transformer_model()
            except Exception as e:
                print(f"Failed to load transformer model: {e}")
                print("Falling back to rating-based sentiment analysis.")
                self.use_transformers = False

    def _load_transformer_model(self):
        """Load multilingual sentiment analysis model."""
        try:
            # Try XLM-RoBERTa multilingual sentiment model
            model_name = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
            print(f"Loading model: {model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=self.model,
                tokenizer=self.tokenizer,
                max_length=512,
                truncation=True
            )
            print("Model loaded successfully!")
        except Exception as e:
            print(f"Error loading transformer model: {e}")
            raise

    def _sentiment_from_rating(self, rating):
        """
        Derive sentiment from rating.

        Args:
            rating: Numerical rating (1-5)

        Returns:
            Sentiment label
        """
        if pd.isna(rating):
            return 'neutral'

        rating = float(rating)

        if rating >= 4:
            return 'positive'
        elif rating >= 3:
            return 'neutral'
        else:
            return 'negative'

    def _sentiment_score_from_rating(self, rating):
        """
        Convert rating to sentiment score.

        Args:
            rating: Numerical rating (1-5)

        Returns:
            Sentiment score (-1 to 1)
        """
        if pd.isna(rating):
            return 0.0

        # Normalize rating from 1-5 to -1 to 1
        rating = float(rating)
        return (rating - 3) / 2

    def analyze_with_transformers(self, text, lang='auto'):
        """
        Analyze sentiment using transformer model.

        Args:
            text: Input text
            lang: Language ('ara', 'eng', or 'auto')

        Returns:
            Dict with sentiment label and score
        """
        if not isinstance(text, str) or not text.strip():
            return {'label': 'neutral', 'score': 0.0}

        try:
            # Truncate text if too long
            if len(text) > 512:
                text = text[:512]

            result = self.sentiment_pipeline(text)[0]

            # Map model output to our labels
            label = result['label'].lower()

            # Handle different label formats
            if 'positive' in label or 'pos' in label:
                sentiment_label = 'positive'
                score = result['score']
            elif 'negative' in label or 'neg' in label:
                sentiment_label = 'negative'
                score = -result['score']
            else:
                sentiment_label = 'neutral'
                score = 0.0

            return {
                'label': sentiment_label,
                'score': score,
                'confidence': result['score']
            }

        except Exception as e:
            print(f"Error in transformer analysis: {e}")
            return {'label': 'neutral', 'score': 0.0, 'confidence': 0.0}

    def analyze_sentiment(self, text, rating=None, lang='auto'):
        """
        Analyze sentiment of text.

        Args:
            text: Input text
            rating: Optional rating (1-5) for fallback/validation
            lang: Language ('ara', 'eng', or 'auto')

        Returns:
            Dict with sentiment information
        """
        # If transformers available, use them
        if self.use_transformers and self.model is not None:
            result = self.analyze_with_transformers(text, lang)

            # If we have a rating, we can validate/adjust
            if rating is not None:
                rating_sentiment = self._sentiment_from_rating(rating)
                rating_score = self._sentiment_score_from_rating(rating)

                # Blend transformer and rating-based sentiment
                # Give more weight to rating as it's explicit user feedback
                result['rating_sentiment'] = rating_sentiment
                result['blended_score'] = 0.4 * result['score'] + 0.6 * rating_score

                # Use rating sentiment if confidence is low
                if result.get('confidence', 0) < 0.6:
                    result['label'] = rating_sentiment

            return result

        # Fallback to rating-based sentiment
        elif rating is not None:
            return {
                'label': self._sentiment_from_rating(rating),
                'score': self._sentiment_score_from_rating(rating),
                'method': 'rating-based'
            }

        # If no model and no rating, return neutral
        else:
            return {
                'label': 'neutral',
                'score': 0.0,
                'method': 'default'
            }

    def detect_language(self, text):
        """Detect if text is primarily Arabic or English."""
        if not isinstance(text, str):
            return 'eng'

        arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
        total_chars = len(re.findall(r'[a-zA-Z\u0600-\u06FF]', text))

        if total_chars == 0:
            return 'eng'

        return 'ara' if arabic_chars / total_chars > 0.5 else 'eng'


class RatingBasedSentimentAnalyzer:
    """Simple sentiment analyzer based on ratings."""

    def __init__(self):
        """Initialize rating-based analyzer."""
        pass

    def analyze_sentiment(self, text, rating):
        """
        Analyze sentiment from rating.

        Args:
            text: Review text (not used, kept for interface consistency)
            rating: Numerical rating (1-5)

        Returns:
            Dict with sentiment information
        """
        if pd.isna(rating):
            return {
                'label': 'neutral',
                'score': 0.0,
                'confidence': 0.0
            }

        rating = float(rating)

        if rating >= 4:
            label = 'positive'
            score = (rating - 3) / 2
        elif rating >= 3:
            label = 'neutral'
            score = 0.0
        else:
            label = 'negative'
            score = (rating - 3) / 2

        return {
            'label': label,
            'score': score,
            'confidence': 1.0,  # High confidence as it's explicit rating
            'method': 'rating-based'
        }


def analyze_dataframe_sentiment(df, text_column='content', rating_column='raw_rating',
                               use_transformers=True):
    """
    Analyze sentiment for all reviews in a dataframe.

    Args:
        df: Input dataframe
        text_column: Column containing review text
        rating_column: Column containing ratings
        use_transformers: Whether to use transformer models

    Returns:
        DataFrame with sentiment columns added
    """
    print("Initializing sentiment analyzer...")

    try:
        analyzer = MultilingualSentimentAnalyzer(use_transformers=use_transformers)
    except:
        print("Using rating-based sentiment analysis")
        analyzer = RatingBasedSentimentAnalyzer()

    print("Analyzing sentiments...")

    results = []
    for idx, row in df.iterrows():
        text = row.get(text_column, '')
        rating = row.get(rating_column, None)

        result = analyzer.analyze_sentiment(text, rating)
        results.append(result)

        if (idx + 1) % 1000 == 0:
            print(f"Processed {idx + 1}/{len(df)} reviews")

    # Add results to dataframe
    df['sentiment_label'] = [r['label'] for r in results]
    df['sentiment_score'] = [r['score'] for r in results]

    if 'confidence' in results[0]:
        df['sentiment_confidence'] = [r.get('confidence', 0.0) for r in results]

    print("Sentiment analysis complete!")

    return df


def get_sentiment_distribution(df, sentiment_column='sentiment_label'):
    """
    Get distribution of sentiments.

    Args:
        df: Input dataframe
        sentiment_column: Column containing sentiment labels

    Returns:
        Dictionary with sentiment counts and percentages
    """
    distribution = df[sentiment_column].value_counts()
    percentages = df[sentiment_column].value_counts(normalize=True) * 100

    result = {}
    for sentiment in distribution.index:
        result[sentiment] = {
            'count': distribution[sentiment],
            'percentage': percentages[sentiment]
        }

    return result


if __name__ == "__main__":
    # Fix encoding for Windows
    import sys
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # Test the analyzer
    print("Testing Sentiment Analyzer...")

    # Test with rating-based analyzer
    analyzer = RatingBasedSentimentAnalyzer()

    test_cases = [
        ("مكان رائع وجميل", 5),
        ("سيء جداً", 1),
        ("عادي", 3),
        ("Great place!", 5),
        ("Terrible experience", 1),
    ]

    print("\nRating-based Analysis:")
    for text, rating in test_cases:
        result = analyzer.analyze_sentiment(text, rating)
        print(f"Text: {text[:30]}... | Rating: {rating} | Sentiment: {result['label']} | Score: {result['score']:.2f}")
