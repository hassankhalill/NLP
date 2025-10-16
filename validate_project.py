"""
Complete Project Validation Script
Tests all components to ensure everything works correctly.
"""

import os
import sys
import pandas as pd
import json

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("="*80)
print(" PROJECT VALIDATION - COMPREHENSIVE CHECK")
print("="*80)

validation_results = []

def check(name, condition, details=""):
    """Record validation result"""
    status = "✅ PASS" if condition else "❌ FAIL"
    validation_results.append((name, condition, details))
    print(f"{status} | {name}")
    if details and not condition:
        print(f"      Details: {details}")
    return condition

# 1. Check Required Files
print("\n[1/10] Checking Required Files...")
check("DataSet.csv exists", os.path.exists('DataSet.csv'))
check("Mappings.json exists", os.path.exists('Mappings.json'))
check("text_preprocessing.py exists", os.path.exists('text_preprocessing.py'))
check("sentiment_analysis.py exists", os.path.exists('sentiment_analysis.py'))
check("absa_model.py exists", os.path.exists('absa_model.py'))
check("api_app.py exists", os.path.exists('api_app.py'))

# 2. Check Output Files
print("\n[2/10] Checking Output Files...")
check("preprocessed_data.csv exists", os.path.exists('preprocessed_data.csv'))
check("processed_data_with_sentiment.csv exists", os.path.exists('processed_data_with_sentiment.csv'))
check("data_with_absa.csv exists", os.path.exists('data_with_absa.csv'))
check("visualizations folder exists", os.path.exists('visualizations'))

# 3. Check Visualizations
print("\n[3/10] Checking Visualizations...")
viz_files = [
    '01_sentiment_distribution.png',
    '02_sentiment_by_rating.png',
    '03_top_destinations.png',
    '04_top_offerings.png',
    '05_rating_distribution.png',
    '06_aspect_frequency.png',
    '07_aspect_sentiment_distribution.png',
    '08_aspects_per_review.png'
]
for viz in viz_files:
    path = os.path.join('visualizations', viz)
    check(f"{viz}", os.path.exists(path))

# 4. Validate Data Files
print("\n[4/10] Validating Data Files...")
try:
    df_original = pd.read_csv('DataSet.csv')
    check("Original dataset loadable", True, f"{len(df_original)} rows")
    check("Original has 10K rows", len(df_original) == 10000)
except Exception as e:
    check("Original dataset loadable", False, str(e))

try:
    df_preprocessed = pd.read_csv('preprocessed_data.csv')
    check("Preprocessed data loadable", True, f"{len(df_preprocessed)} rows")
    required_cols = ['offerings', 'destinations', 'normalized_rating', 'raw_rating']
    has_cols = all(col in df_preprocessed.columns for col in required_cols)
    check("Has required columns", has_cols, str(required_cols))
except Exception as e:
    check("Preprocessed data loadable", False, str(e))

try:
    df_sentiment = pd.read_csv('processed_data_with_sentiment.csv')
    check("Sentiment data loadable", True, f"{len(df_sentiment)} rows")
    has_sent = 'sentiment_label' in df_sentiment.columns
    check("Has sentiment_label column", has_sent)
except Exception as e:
    check("Sentiment data loadable", False, str(e))

try:
    df_absa = pd.read_csv('data_with_absa.csv')
    check("ABSA data loadable", True, f"{len(df_absa)} rows")
    absa_cols = ['num_aspects', 'detected_aspects', 'aspect_sentiments']
    has_absa_cols = all(col in df_absa.columns for col in absa_cols)
    check("Has ABSA columns", has_absa_cols, str(absa_cols))
except Exception as e:
    check("ABSA data loadable", False, str(e))

# 5. Test Module Imports
print("\n[5/10] Testing Module Imports...")
try:
    from text_preprocessing import TextCleaner, preprocess_dataframe
    check("text_preprocessing imports", True)
except Exception as e:
    check("text_preprocessing imports", False, str(e))

try:
    from sentiment_analysis import RatingBasedSentimentAnalyzer
    check("sentiment_analysis imports", True)
except Exception as e:
    check("sentiment_analysis imports", False, str(e))

try:
    from absa_model import ABSAModel
    check("absa_model imports", True)
except Exception as e:
    check("absa_model imports", False, str(e))

try:
    from api_app import app
    check("api_app imports", True)
except Exception as e:
    check("api_app imports", False, str(e))

# 6. Test Text Preprocessing
print("\n[6/10] Testing Text Preprocessing...")
try:
    from text_preprocessing import TextCleaner
    cleaner = TextCleaner()

    # Test Arabic
    arabic_text = "هذا مكان جميل"
    cleaned_ar = cleaner.clean_text(arabic_text)
    check("Arabic text cleaning works", len(cleaned_ar) > 0)

    # Test English
    english_text = "This is a great place!"
    cleaned_en = cleaner.clean_text(english_text)
    check("English text cleaning works", len(cleaned_en) > 0)

    # Test language detection
    lang_ar = cleaner.detect_language(arabic_text)
    check("Arabic language detection", lang_ar == 'ara')

    lang_en = cleaner.detect_language(english_text)
    check("English language detection", lang_en == 'eng')

except Exception as e:
    check("Text preprocessing functional", False, str(e))

# 7. Test Sentiment Analysis
print("\n[7/10] Testing Sentiment Analysis...")
try:
    from sentiment_analysis import RatingBasedSentimentAnalyzer
    analyzer = RatingBasedSentimentAnalyzer()

    # Test positive
    result_pos = analyzer.analyze_sentiment("Great place", 5)
    check("Positive sentiment detection", result_pos['label'] == 'positive')

    # Test negative
    result_neg = analyzer.analyze_sentiment("Bad place", 1)
    check("Negative sentiment detection", result_neg['label'] == 'negative')

    # Test neutral
    result_neu = analyzer.analyze_sentiment("Okay place", 3)
    check("Neutral sentiment detection", result_neu['label'] == 'neutral')

except Exception as e:
    check("Sentiment analysis functional", False, str(e))

# 8. Test ABSA Model
print("\n[8/10] Testing ABSA Model...")
try:
    from absa_model import ABSAModel
    absa = ABSAModel()

    # Test aspect extraction
    text = "The location is great but the service is poor and the price is expensive"
    result = absa.analyze(text, overall_rating=3)

    check("ABSA analysis runs", True)
    check("ABSA detects aspects", len(result['aspects']) > 0)
    check("ABSA has aspect sentiments", len(result['aspect_sentiments']) > 0)

    # Check specific aspects
    has_location = 'location' in result['aspects']
    has_service = 'service' in result['aspects']
    has_price = 'price' in result['aspects']

    check("ABSA detects location aspect", has_location)
    check("ABSA detects service aspect", has_service)
    check("ABSA detects price aspect", has_price)

except Exception as e:
    check("ABSA model functional", False, str(e))

# 9. Test Data Integrity
print("\n[9/10] Testing Data Integrity...")
try:
    df_absa = pd.read_csv('data_with_absa.csv')

    # Check no data loss
    check("No rows lost in processing", len(df_absa) == 10000)

    # Check sentiment distribution
    sentiment_counts = df_absa['sentiment_label'].value_counts()
    has_all_sentiments = all(s in sentiment_counts.index for s in ['positive', 'neutral', 'negative'])
    check("All sentiment types present", has_all_sentiments)

    # Check aspect detection
    reviews_with_aspects = (df_absa['num_aspects'] > 0).sum()
    check("Aspects detected in reviews", reviews_with_aspects > 6000)

    # Check ratings validity
    valid_ratings = df_absa['raw_rating'].between(0, 10).all()
    check("All ratings in valid range", valid_ratings)

except Exception as e:
    check("Data integrity validation", False, str(e))

# 10. Test API Structure
print("\n[10/10] Testing API Structure...")
try:
    from fastapi.testclient import TestClient
    from api_app import app

    client = TestClient(app)

    # Test root endpoint
    response = client.get("/")
    check("API root endpoint responds", response.status_code == 200)

    # Test health endpoint
    response = client.get("/health")
    check("API health endpoint responds", response.status_code == 200)

    # Test aspects endpoint
    response = client.get("/api/v1/aspects")
    check("API aspects endpoint responds", response.status_code == 200)

except ImportError:
    print("⚠️  SKIP | FastAPI TestClient not available (install with: pip install httpx)")
except Exception as e:
    check("API structure valid", False, str(e))

# Summary
print("\n" + "="*80)
print(" VALIDATION SUMMARY")
print("="*80)

total_checks = len(validation_results)
passed_checks = sum(1 for _, passed, _ in validation_results if passed)
failed_checks = total_checks - passed_checks

print(f"\nTotal Checks: {total_checks}")
print(f"✅ Passed: {passed_checks}")
print(f"❌ Failed: {failed_checks}")
print(f"Success Rate: {passed_checks/total_checks*100:.1f}%")

if failed_checks > 0:
    print(f"\n⚠️  {failed_checks} check(s) failed. Review details above.")
else:
    print(f"\n🎉 All checks passed! Project is in excellent shape.")

# Missing Deliverables
print("\n" + "="*80)
print(" MISSING DELIVERABLES")
print("="*80)

missing = []
if not os.path.exists('NLP_ABSA_Analysis.ipynb'):
    missing.append("❌ Jupyter Notebook (NLP_ABSA_Analysis.ipynb)")
elif os.path.getsize('NLP_ABSA_Analysis.ipynb') < 50000:
    missing.append("⚠️  Jupyter Notebook (exists but incomplete)")

if not any(f.endswith('.pdf') for f in os.listdir('.')):
    missing.append("❌ PDF Report")

if not os.path.exists('monitoring.py'):
    missing.append("❌ Monitoring Module")

if not os.path.exists('retraining.py'):
    missing.append("❌ Retraining Module")

if missing:
    print("\nMissing deliverables:")
    for item in missing:
        print(f"  {item}")
    print(f"\n⚠️  {len(missing)} deliverable(s) missing or incomplete")
else:
    print("\n✅ All deliverables present!")

print("\n" + "="*80)
print(" RECOMMENDATION")
print("="*80)

if passed_checks >= total_checks * 0.9:
    print("\n✅ PROJECT STATUS: EXCELLENT")
    print("   All core functionality working correctly.")
    print("   Focus on completing documentation deliverables.")
elif passed_checks >= total_checks * 0.7:
    print("\n⚠️  PROJECT STATUS: GOOD")
    print("   Most functionality working.")
    print("   Address failed checks before proceeding.")
else:
    print("\n❌ PROJECT STATUS: NEEDS WORK")
    print("   Multiple components failing.")
    print("   Debug issues before proceeding.")

print("\n" + "="*80)
