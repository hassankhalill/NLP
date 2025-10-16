"""
FastAPI Application for NLP ABSA Model
Provides REST API endpoints for sentiment analysis and ABSA
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime

# Import our modules
from sentiment_analysis import RatingBasedSentimentAnalyzer
from absa_model import ABSAModel
from text_preprocessing import TextCleaner

# Initialize FastAPI app
app = FastAPI(
    title="Saudi Tourism Review Analysis API",
    description="API for sentiment analysis and aspect-based sentiment analysis of tourism reviews",
    version="1.0.0"
)

# Initialize models
sentiment_analyzer = RatingBasedSentimentAnalyzer()
absa_model = ABSAModel()
text_cleaner = TextCleaner()

# Request/Response Models
class ReviewInput(BaseModel):
    """Input model for single review analysis"""
    text: str = Field(..., description="Review text in Arabic or English", min_length=1)
    rating: Optional[float] = Field(None, description="Optional rating (1-5)", ge=0, le=10)

    class Config:
        json_schema_extra = {
            "example": {
                "text": "المكان جميل جداً والموقع ممتاز لكن الخدمة سيئة",
                "rating": 3
            }
        }


class BatchReviewInput(BaseModel):
    """Input model for batch review analysis"""
    reviews: List[ReviewInput] = Field(..., description="List of reviews to analyze")


class SentimentResponse(BaseModel):
    """Response model for sentiment analysis"""
    text: str
    language: str
    sentiment_label: str
    sentiment_score: float
    confidence: float


class AspectSentiment(BaseModel):
    """Model for aspect-level sentiment"""
    aspect: str
    sentiment: str
    score: float
    confidence: float


class ABSAResponse(BaseModel):
    """Response model for ABSA"""
    text: str
    language: str
    overall_sentiment: str
    overall_score: float
    num_aspects: int
    aspects: List[str]
    aspect_sentiments: List[AspectSentiment]


class CleanTextResponse(BaseModel):
    """Response model for text cleaning"""
    original_text: str
    cleaned_text: str
    language: str


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    timestamp: str
    version: str
    models_loaded: bool


# API Endpoints

@app.get("/", tags=["General"])
async def root():
    """Root endpoint - API information"""
    return {
        "message": "Saudi Tourism Review Analysis API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "sentiment": "/api/v1/sentiment",
            "absa": "/api/v1/absa",
            "batch_sentiment": "/api/v1/batch/sentiment",
            "batch_absa": "/api/v1/batch/absa",
            "clean_text": "/api/v1/clean-text"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "models_loaded": True
    }


@app.post("/api/v1/sentiment", response_model=SentimentResponse, tags=["Sentiment Analysis"])
async def analyze_sentiment(review: ReviewInput):
    """
    Analyze sentiment of a single review.

    Returns overall sentiment classification and score.
    """
    try:
        # Detect language
        language = text_cleaner.detect_language(review.text)

        # Analyze sentiment
        result = sentiment_analyzer.analyze_sentiment(review.text, review.rating)

        return {
            "text": review.text[:200] + "..." if len(review.text) > 200 else review.text,
            "language": language,
            "sentiment_label": result['label'],
            "sentiment_score": result['score'],
            "confidence": result.get('confidence', 1.0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing sentiment: {str(e)}")


@app.post("/api/v1/absa", response_model=ABSAResponse, tags=["ABSA"])
async def analyze_absa(review: ReviewInput):
    """
    Perform Aspect-Based Sentiment Analysis on a single review.

    Extracts aspects mentioned in the review and determines sentiment for each aspect.
    """
    try:
        # Perform ABSA
        result = absa_model.analyze(review.text, review.rating)

        return {
            "text": review.text[:200] + "..." if len(review.text) > 200 else review.text,
            "language": result['language'],
            "overall_sentiment": result['overall_sentiment'],
            "overall_score": result['overall_score'],
            "num_aspects": result['num_aspects'],
            "aspects": result['aspects'],
            "aspect_sentiments": result['aspect_sentiments']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error performing ABSA: {str(e)}")


@app.post("/api/v1/batch/sentiment", tags=["Batch Processing"])
async def batch_analyze_sentiment(batch: BatchReviewInput):
    """
    Analyze sentiment for multiple reviews in batch.

    Maximum 100 reviews per batch.
    """
    if len(batch.reviews) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 reviews per batch")

    try:
        results = []
        for review in batch.reviews:
            language = text_cleaner.detect_language(review.text)
            sentiment_result = sentiment_analyzer.analyze_sentiment(review.text, review.rating)

            results.append({
                "text": review.text[:100] + "..." if len(review.text) > 100 else review.text,
                "language": language,
                "sentiment_label": sentiment_result['label'],
                "sentiment_score": sentiment_result['score'],
                "confidence": sentiment_result.get('confidence', 1.0)
            })

        return {
            "total_reviews": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in batch processing: {str(e)}")


@app.post("/api/v1/batch/absa", tags=["Batch Processing"])
async def batch_analyze_absa(batch: BatchReviewInput):
    """
    Perform ABSA for multiple reviews in batch.

    Maximum 50 reviews per batch (ABSA is more computationally intensive).
    """
    if len(batch.reviews) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 reviews per batch for ABSA")

    try:
        results = []
        for review in batch.reviews:
            absa_result = absa_model.analyze(review.text, review.rating)

            results.append({
                "text": review.text[:100] + "..." if len(review.text) > 100 else review.text,
                "language": absa_result['language'],
                "overall_sentiment": absa_result['overall_sentiment'],
                "overall_score": absa_result['overall_score'],
                "num_aspects": absa_result['num_aspects'],
                "aspects": absa_result['aspects'],
                "aspect_sentiments": absa_result['aspect_sentiments']
            })

        return {
            "total_reviews": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in batch ABSA: {str(e)}")


@app.post("/api/v1/clean-text", response_model=CleanTextResponse, tags=["Text Processing"])
async def clean_text_endpoint(review: ReviewInput):
    """
    Clean and preprocess text (remove stopwords, normalize, etc.)
    """
    try:
        language = text_cleaner.detect_language(review.text)
        cleaned = text_cleaner.clean_text(review.text)

        return {
            "original_text": review.text,
            "cleaned_text": cleaned,
            "language": language
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cleaning text: {str(e)}")


@app.get("/api/v1/aspects", tags=["Reference Data"])
async def get_supported_aspects():
    """
    Get list of supported aspects for ABSA.
    """
    return {
        "aspects": absa_model.aspects,
        "total": len(absa_model.aspects),
        "description": {
            "location": "Location, accessibility, distance",
            "cleanliness": "Cleanliness and hygiene",
            "service": "Customer service and staff",
            "price": "Pricing and value for money",
            "food": "Food quality and taste",
            "facility": "Facilities and amenities",
            "ambiance": "Atmosphere, decor, and aesthetics",
            "activity": "Activities and entertainment"
        }
    }


@app.get("/api/v1/stats", tags=["Statistics"])
async def get_statistics():
    """
    Get overall statistics from the analysis.
    """
    try:
        # Load the ABSA results
        df = pd.read_csv('data_with_absa.csv')

        # Calculate statistics
        total_reviews = len(df)
        sentiment_dist = df['sentiment_label'].value_counts().to_dict()
        avg_rating = df['raw_rating'].mean()
        avg_aspects = df['num_aspects'].mean()

        return {
            "total_reviews_analyzed": total_reviews,
            "average_rating": round(avg_rating, 2),
            "average_aspects_per_review": round(avg_aspects, 2),
            "sentiment_distribution": sentiment_dist,
            "languages": {
                "arabic": int((df['language'] == 'ara').sum()),
                "english": int((df['language'] == 'eng').sum())
            }
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Statistics not available. Run analysis first.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving statistics: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    print("="*80)
    print(" SAUDI TOURISM REVIEW ANALYSIS API")
    print("="*80)
    print("\n🚀 Starting API server...")
    print("📍 API will be available at: http://localhost:8000")
    print("📖 API documentation: http://localhost:8000/docs")
    print("📊 Alternative docs: http://localhost:8000/redoc")
    print("\n" + "="*80)

    uvicorn.run(app, host="0.0.0.0", port=8000)
