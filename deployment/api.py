
"""
FastAPI Application for ABSA Model Deployment
Production-ready API server for Aspect-Based Sentiment Analysis
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import uvicorn
import torch
import pickle
import json
from datetime import datetime
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import logging
import sys
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ABSA API - Tourism Reviews",
    description="Aspect-Based Sentiment Analysis API for tourism reviews (Arabic & English)",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class ReviewInput(BaseModel):
    content: str = Field(..., description="Review text content")
    language: str = Field(..., description="Language code: 'ara' or 'eng'")
    review_id: Optional[str] = Field(None, description="Optional review identifier")

class AspectSentiment(BaseModel):
    aspect: str
    sentiment: str
    confidence: float

class ABSAResponse(BaseModel):
    review_id: str
    language: str
    aspects: List[str]
    aspect_sentiments: Dict[str, str]
    aspect_confidences: Dict[str, float]
    overall_sentiment: str
    overall_confidence: float
    overall_probabilities: Dict[str, float]
    average_confidence: float
    processing_time_ms: float

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    device: str
    timestamp: str

class BatchReviewInput(BaseModel):
    reviews: List[ReviewInput]

# Global pipeline instance
pipeline = None

# Text cleaning functions (simplified versions)
def clean_arabic_text(text):
    """Basic Arabic text cleaning"""
    import re
    text = re.sub(r'[^\w\s؀-ۿ]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def clean_english_text(text):
    """Basic English text cleaning"""
    import re
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip().lower()

class ABSAPipeline:
    """Production ABSA Pipeline"""

    def __init__(self, model_dir='./models/production'):
        logger.info("Initializing ABSA Pipeline...")
        self.model_dir = model_dir

        # Load configuration
        with open(f'{model_dir}/aspects_config.pkl', 'rb') as f:
            config = pickle.load(f)
            self.aspects_dict = config['aspects']
            self.reverse_sentiment_mapping = config['reverse_sentiment_mapping']

        # Load metadata
        with open(f'{model_dir}/metadata.json', 'r') as f:
            self.metadata = json.load(f)

        # Load models
        logger.info("Loading fine-tuned models...")
        self.arabic_tokenizer = AutoTokenizer.from_pretrained(f'{model_dir}/arabic_absa')
        self.arabic_model = AutoModelForSequenceClassification.from_pretrained(f'{model_dir}/arabic_absa')
        self.arabic_model.eval()

        self.english_tokenizer = AutoTokenizer.from_pretrained(f'{model_dir}/english_absa')
        self.english_model = AutoModelForSequenceClassification.from_pretrained(f'{model_dir}/english_absa')
        self.english_model.eval()

        # Set device
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.arabic_model.to(self.device)
        self.english_model.to(self.device)

        logger.info(f"Models loaded successfully on {self.device}")

    def extract_aspects(self, text):
        """Extract aspects from text"""
        found_aspects = []
        text_lower = text.lower()

        for aspect, keywords in self.aspects_dict.items():
            for keyword in keywords:
                if keyword in text_lower:
                    found_aspects.append(aspect)
                    break
        return list(set(found_aspects))

    def predict_sentiment(self, text, language, max_length=128):
        """Predict sentiment using fine-tuned models"""
        try:
            # Select model
            if language == 'ara':
                tokenizer = self.arabic_tokenizer
                model = self.arabic_model
                text = clean_arabic_text(text)
            else:
                tokenizer = self.english_tokenizer
                model = self.english_model
                text = clean_english_text(text)

            # Tokenize
            inputs = tokenizer(text, padding='max_length', truncation=True, 
                             max_length=max_length, return_tensors='pt').to(self.device)

            # Predict
            with torch.no_grad():
                outputs = model(**inputs)
                probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
                prediction = torch.argmax(probs, dim=-1).item()
                confidence = probs[0][prediction].item()

            return {
                'label': self.reverse_sentiment_mapping[prediction],
                'score': confidence,
                'probabilities': {
                    'negative': probs[0][0].item(),
                    'neutral': probs[0][1].item(),
                    'positive': probs[0][2].item()
                }
            }
        except Exception as e:
            logger.error(f"Sentiment prediction error: {e}")
            return {'label': 'neutral', 'score': 0.5, 
                   'probabilities': {'negative': 0.33, 'neutral': 0.34, 'positive': 0.33}}

    def process_review(self, review_text, language, review_id='unknown'):
        """Process single review"""
        import time
        start_time = time.time()

        # Clean text
        if language == 'ara':
            cleaned = clean_arabic_text(review_text)
        else:
            cleaned = clean_english_text(review_text)

        # Extract aspects
        aspects = self.extract_aspects(cleaned)

        # Get overall sentiment
        overall_sentiment = self.predict_sentiment(cleaned, language)

        # Analyze aspect-level sentiment
        aspect_sentiments = {}
        aspect_confidences = {}

        for aspect in aspects:
            keywords = self.aspects_dict[aspect]
            aspect_context = []

            for sentence in cleaned.split('.'):
                if any(keyword in sentence.lower() for keyword in keywords):
                    aspect_context.append(sentence)

            if aspect_context:
                context_text = ' '.join(aspect_context)
                aspect_sent = self.predict_sentiment(context_text, language)
                aspect_sentiments[aspect] = aspect_sent['label']
                aspect_confidences[aspect] = aspect_sent['score']
            else:
                aspect_sentiments[aspect] = overall_sentiment['label']
                aspect_confidences[aspect] = overall_sentiment['score']

        # Calculate metrics
        avg_confidence = (sum(aspect_confidences.values()) / len(aspect_confidences) 
                         if aspect_confidences else overall_sentiment['score'])

        processing_time = (time.time() - start_time) * 1000  # Convert to ms

        return {
            'review_id': review_id,
            'language': language,
            'aspects': aspects,
            'aspect_sentiments': aspect_sentiments,
            'aspect_confidences': aspect_confidences,
            'overall_sentiment': overall_sentiment['label'],
            'overall_confidence': overall_sentiment['score'],
            'overall_probabilities': overall_sentiment['probabilities'],
            'average_confidence': avg_confidence,
            'processing_time_ms': processing_time
        }

@app.on_event("startup")
async def startup_event():
    """Initialize pipeline on startup"""
    global pipeline
    try:
        pipeline = ABSAPipeline('./models/production')
        logger.info("ABSA Pipeline initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize pipeline: {e}")
        raise

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check"""
    return {
        "status": "running",
        "model_loaded": pipeline is not None,
        "device": str(pipeline.device) if pipeline else "unknown",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy" if pipeline is not None else "unhealthy",
        "model_loaded": pipeline is not None,
        "device": str(pipeline.device) if pipeline else "unknown",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/analyze", response_model=ABSAResponse)
async def analyze_review(review: ReviewInput):
    """
    Analyze a single review for aspect-based sentiment
    """
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    if review.language not in ['ara', 'eng']:
        raise HTTPException(status_code=400, detail="Language must be 'ara' or 'eng'")

    try:
        result = pipeline.process_review(
            review.content,
            review.language,
            review.review_id or 'unknown'
        )
        return result
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/analyze-batch")
async def analyze_batch(batch: BatchReviewInput):
    """
    Analyze multiple reviews in batch
    """
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    results = []
    for review in batch.reviews:
        try:
            result = pipeline.process_review(
                review.content,
                review.language,
                review.review_id or 'unknown'
            )
            results.append(result)
        except Exception as e:
            logger.error(f"Batch analysis error for review {review.review_id}: {e}")
            results.append({"error": str(e), "review_id": review.review_id})

    return {"results": results, "total": len(results)}

@app.get("/aspects")
async def get_aspects():
    """Get list of all supported aspects"""
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    return {
        "aspects": list(pipeline.aspects_dict.keys()),
        "total": len(pipeline.aspects_dict)
    }

@app.get("/model-info")
async def get_model_info():
    """Get model metadata and performance info"""
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    return pipeline.metadata

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
