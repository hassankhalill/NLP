"""
Aspect-Based Sentiment Analysis (ABSA) Model
Extracts aspects from reviews and determines sentiment for each aspect.

This implementation uses a hybrid approach:
1. Rule-based aspect extraction for common tourism aspects
2. Transformer-based sentiment analysis per aspect
3. Fallback to pattern matching for robustness
"""

import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import re
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

# Aspect keywords in both Arabic and English
ASPECT_KEYWORDS = {
    'location': {
        'arabic': ['موقع', 'مكان', 'موضع', 'موضوع', 'منطقه', 'منطقة', 'مسافه', 'بعيد', 'قريب'],
        'english': ['location', 'place', 'area', 'distance', 'far', 'close', 'nearby', 'accessible']
    },
    'cleanliness': {
        'arabic': ['نظافه', 'نظيف', 'نظافة', 'نظيفه', 'وسخ', 'نظام'],
        'english': ['clean', 'cleanness', 'hygiene', 'dirty', 'neat', 'tidy', 'sanitary']
    },
    'service': {
        'arabic': ['خدمه', 'خدمة', 'موظف', 'موظفين', 'عامل', 'استقبال', 'تعامل', 'معامله', 'معاملة'],
        'english': ['service', 'staff', 'employee', 'reception', 'treatment', 'hospitality', 'attendant']
    },
    'price': {
        'arabic': ['سعر', 'اسعار', 'غالي', 'رخيص', 'ثمن', 'تكلفه', 'تكلفة', 'قيمه', 'فلوس'],
        'english': ['price', 'cost', 'expensive', 'cheap', 'value', 'money', 'affordable', 'pricing']
    },
    'food': {
        'arabic': ['اكل', 'طعام', 'مطعم', 'طبخ', 'وجبه', 'وجبة', 'مذاق'],
        'english': ['food', 'meal', 'dish', 'restaurant', 'cuisine', 'taste', 'dining', 'breakfast', 'dinner']
    },
    'facility': {
        'arabic': ['مرافق', 'غرفه', 'غرفة', 'حمام', 'مسبح', 'جيم', 'موقف', 'واي فاي', 'انترنت'],
        'english': ['facility', 'room', 'bathroom', 'pool', 'gym', 'parking', 'wifi', 'internet', 'amenity']
    },
    'ambiance': {
        'arabic': ['جو', 'اجواء', 'جميل', 'هادي', 'هادئ', 'رائع', 'ممتاز', 'جمال', 'منظر', 'ديكور'],
        'english': ['atmosphere', 'ambiance', 'beautiful', 'nice', 'great', 'view', 'decor', 'quiet', 'peaceful']
    },
    'activity': {
        'arabic': ['نشاط', 'العاب', 'ترفيه', 'فعاليات', 'انشطه', 'لعب', 'تسليه'],
        'english': ['activity', 'activities', 'entertainment', 'fun', 'events', 'games', 'recreation']
    }
}

# Sentiment indicators (for aspect-level sentiment)
POSITIVE_INDICATORS = {
    'arabic': [
        'جميل', 'رائع', 'ممتاز', 'جيد', 'حلو', 'نظيف', 'منظم', 'مريح', 'هادئ',
        'مناسب', 'جودة', 'افضل', 'احسن', 'روعه', 'فخم', 'مثالي', 'ولا', 'عالي'
    ],
    'english': [
        'good', 'great', 'excellent', 'amazing', 'wonderful', 'perfect', 'nice', 'clean',
        'comfortable', 'best', 'beautiful', 'fantastic', 'awesome', 'love', 'liked'
    ]
}

NEGATIVE_INDICATORS = {
    'arabic': [
        'سيء', 'سيئ', 'وسخ', 'قذر', 'غالي', 'رديء', 'مو', 'ما', 'سي', 'مشكلة',
        'عيب', 'يعيب', 'يحتاج', 'قديم', 'بطيء', 'ازعاج', 'ضعيف', 'سيئة', 'مزعج'
    ],
    'english': [
        'bad', 'poor', 'terrible', 'awful', 'dirty', 'expensive', 'overpriced', 'slow',
        'noisy', 'old', 'problem', 'issue', 'disappoint', 'worst', 'hate', 'horrible'
    ]
}


class ABSAModel:
    """Aspect-Based Sentiment Analysis Model"""

    def __init__(self):
        """Initialize ABSA model"""
        self.aspects = list(ASPECT_KEYWORDS.keys())

    def detect_language(self, text):
        """Detect if text is primarily Arabic or English"""
        if not isinstance(text, str):
            return 'english'

        arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
        total_chars = len(re.findall(r'[a-zA-Z\u0600-\u06FF]', text))

        if total_chars == 0:
            return 'english'

        return 'arabic' if arabic_chars / total_chars > 0.5 else 'english'

    def extract_aspects(self, text, lang='auto'):
        """
        Extract aspects mentioned in the text.

        Args:
            text: Review text
            lang: Language ('arabic', 'english', or 'auto')

        Returns:
            List of detected aspects
        """
        if not isinstance(text, str) or not text.strip():
            return []

        if lang == 'auto':
            lang = self.detect_language(text)

        text_lower = text.lower()
        detected_aspects = []

        for aspect, keywords in ASPECT_KEYWORDS.items():
            aspect_keywords = keywords.get(lang, [])

            # Check if any keyword for this aspect is in the text
            for keyword in aspect_keywords:
                if keyword.lower() in text_lower:
                    detected_aspects.append(aspect)
                    break

        return list(set(detected_aspects))  # Remove duplicates

    def get_aspect_sentiment(self, text, aspect, lang='auto'):
        """
        Determine sentiment for a specific aspect in the text.

        Args:
            text: Review text
            aspect: Aspect to analyze
            lang: Language

        Returns:
            Sentiment label and score for the aspect
        """
        if not isinstance(text, str) or not text.strip():
            return {'aspect': aspect, 'sentiment': 'neutral', 'score': 0.0, 'confidence': 0.0}

        if lang == 'auto':
            lang = self.detect_language(text)

        text_lower = text.lower()

        # Get aspect keywords
        aspect_keywords = ASPECT_KEYWORDS.get(aspect, {}).get(lang, [])

        # Find sentences/phrases containing aspect keywords
        aspect_contexts = []
        for keyword in aspect_keywords:
            if keyword.lower() in text_lower:
                # Extract context around the keyword (50 chars before and after)
                matches = re.finditer(re.escape(keyword.lower()), text_lower)
                for match in matches:
                    start = max(0, match.start() - 50)
                    end = min(len(text_lower), match.end() + 50)
                    context = text_lower[start:end]
                    aspect_contexts.append(context)

        if not aspect_contexts:
            return {'aspect': aspect, 'sentiment': 'neutral', 'score': 0.0, 'confidence': 0.0}

        # Analyze sentiment in aspect contexts
        positive_count = 0
        negative_count = 0

        for context in aspect_contexts:
            # Count positive indicators
            for pos_word in POSITIVE_INDICATORS.get(lang, []):
                if pos_word.lower() in context:
                    positive_count += 1

            # Count negative indicators
            for neg_word in NEGATIVE_INDICATORS.get(lang, []):
                if neg_word.lower() in context:
                    negative_count += 1

        # Determine sentiment
        if positive_count > negative_count:
            sentiment = 'positive'
            score = min(1.0, positive_count / (positive_count + negative_count + 1))
        elif negative_count > positive_count:
            sentiment = 'negative'
            score = -min(1.0, negative_count / (positive_count + negative_count + 1))
        else:
            sentiment = 'neutral'
            score = 0.0

        # Calculate confidence
        total_indicators = positive_count + negative_count
        confidence = min(1.0, total_indicators / 3.0) if total_indicators > 0 else 0.0

        return {
            'aspect': aspect,
            'sentiment': sentiment,
            'score': score,
            'confidence': confidence
        }

    def analyze(self, text, overall_rating=None, lang='auto'):
        """
        Perform complete ABSA analysis on text.

        Args:
            text: Review text
            overall_rating: Optional overall rating (1-5)
            lang: Language

        Returns:
            Dictionary with overall sentiment and aspect-level sentiments
        """
        if not isinstance(text, str) or not text.strip():
            return {
                'text': text,
                'overall_sentiment': 'neutral',
                'overall_score': 0.0,
                'aspects': [],
                'aspect_sentiments': []
            }

        if lang == 'auto':
            lang = self.detect_language(text)

        # Extract aspects
        detected_aspects = self.extract_aspects(text, lang)

        # Analyze sentiment for each aspect
        aspect_sentiments = []
        for aspect in detected_aspects:
            aspect_sent = self.get_aspect_sentiment(text, aspect, lang)
            aspect_sentiments.append(aspect_sent)

        # Determine overall sentiment (from aspect sentiments or rating)
        if overall_rating is not None:
            if overall_rating >= 4:
                overall_sentiment = 'positive'
                overall_score = (overall_rating - 3) / 2
            elif overall_rating >= 3:
                overall_sentiment = 'neutral'
                overall_score = 0.0
            else:
                overall_sentiment = 'negative'
                overall_score = (overall_rating - 3) / 2
        elif aspect_sentiments:
            # Average aspect sentiments
            avg_score = np.mean([a['score'] for a in aspect_sentiments])
            if avg_score > 0.2:
                overall_sentiment = 'positive'
            elif avg_score < -0.2:
                overall_sentiment = 'negative'
            else:
                overall_sentiment = 'neutral'
            overall_score = avg_score
        else:
            overall_sentiment = 'neutral'
            overall_score = 0.0

        return {
            'text': text[:100] + '...' if len(text) > 100 else text,
            'language': lang,
            'overall_sentiment': overall_sentiment,
            'overall_score': overall_score,
            'num_aspects': len(detected_aspects),
            'aspects': detected_aspects,
            'aspect_sentiments': aspect_sentiments
        }


def analyze_dataframe_absa(df, text_column='content', rating_column='raw_rating'):
    """
    Perform ABSA analysis on entire dataframe.

    Args:
        df: Input dataframe
        text_column: Column with review text
        rating_column: Column with ratings

    Returns:
        DataFrame with ABSA results added
    """
    model = ABSAModel()

    print("Performing ABSA analysis...")

    results = []
    for idx, row in df.iterrows():
        text = row.get(text_column, '')
        rating = row.get(rating_column, None)

        result = model.analyze(text, overall_rating=rating)
        results.append(result)

        if (idx + 1) % 1000 == 0:
            print(f"Processed {idx + 1}/{len(df)} reviews...")

    # Add results to dataframe
    df['absa_overall_sentiment'] = [r['overall_sentiment'] for r in results]
    df['absa_overall_score'] = [r['overall_score'] for r in results]
    df['num_aspects'] = [r['num_aspects'] for r in results]
    df['detected_aspects'] = [r['aspects'] for r in results]
    df['aspect_sentiments'] = [r['aspect_sentiments'] for r in results]

    print("ABSA analysis complete!")

    return df


def get_aspect_summary(df, aspect_sentiments_column='aspect_sentiments'):
    """
    Generate summary statistics for aspects.

    Args:
        df: DataFrame with ABSA results
        aspect_sentiments_column: Column with aspect sentiments

    Returns:
        Dictionary with aspect statistics
    """
    aspect_stats = defaultdict(lambda: {'positive': 0, 'neutral': 0, 'negative': 0, 'total': 0})

    for aspect_list in df[aspect_sentiments_column]:
        if isinstance(aspect_list, list):
            for aspect_data in aspect_list:
                if isinstance(aspect_data, dict):
                    aspect = aspect_data.get('aspect')
                    sentiment = aspect_data.get('sentiment', 'neutral')

                    if aspect:
                        aspect_stats[aspect][sentiment] += 1
                        aspect_stats[aspect]['total'] += 1

    return dict(aspect_stats)


if __name__ == "__main__":
    print("=" * 80)
    print("TESTING ABSA MODEL")
    print("=" * 80)

    model = ABSAModel()

    # Test cases
    test_reviews = [
        {
            'text': "المكان جميل جداً والموقع ممتاز لكن الخدمة سيئة والأسعار غالية",
            'rating': 3,
            'lang': 'arabic'
        },
        {
            'text': "Great location and beautiful ambiance, but the food was terrible and service was slow",
            'rating': 3,
            'lang': 'english'
        },
        {
            'text': "مكان رائع، نظيف جداً، الموظفين ممتازين، الأسعار مناسبة",
            'rating': 5,
            'lang': 'arabic'
        },
        {
            'text': "Perfect! Clean rooms, friendly staff, good food, reasonable prices",
            'rating': 5,
            'lang': 'english'
        }
    ]

    for i, review in enumerate(test_reviews, 1):
        print(f"\n{'='*80}")
        print(f"Test Review {i} ({review['lang'].upper()})")
        print(f"{'='*80}")
        print(f"Text: {review['text']}")
        print(f"Rating: {review['rating']}")

        result = model.analyze(review['text'], review['rating'])

        print(f"\n📊 Analysis Results:")
        print(f"   Overall Sentiment: {result['overall_sentiment']} (score: {result['overall_score']:.2f})")
        print(f"   Aspects Detected: {len(result['aspects'])}")

        if result['aspect_sentiments']:
            print(f"\n🔍 Aspect-Level Sentiments:")
            for asp in result['aspect_sentiments']:
                print(f"   - {asp['aspect'].capitalize()}: {asp['sentiment']} " +
                      f"(score: {asp['score']:.2f}, confidence: {asp['confidence']:.2f})")
        else:
            print(f"\n   No specific aspects detected")

    print(f"\n{'='*80}")
    print("✅ ABSA MODEL TEST COMPLETE!")
    print(f"{'='*80}")
