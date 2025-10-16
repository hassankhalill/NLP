"""
Full NLP ABSA Pipeline - Complete End-to-End Execution
This script runs all phases of the analysis from start to finish.
"""

import sys
import warnings
warnings.filterwarnings('ignore')

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
import numpy as np
import json
import ast
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import matplotlib

# Use non-GUI backend for matplotlib
matplotlib.use('Agg')

# Set display options
pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', 100)

print("="*80)
print(" NLP ABSA PIPELINE - FULL EXECUTION")
print("="*80)

#==============================================================================
# PHASE 1: DATA PREPROCESSING AND TRANSFORMATION
#==============================================================================

print("\n" + "="*80)
print("PHASE 1: DATA PREPROCESSING AND TRANSFORMATION")
print("="*80)

# Load dataset
print("\n[1.1] Loading dataset...")
df = pd.read_csv('DataSet.csv')
print(f"✅ Loaded {len(df)} reviews with {len(df.columns)} columns")

# Load mappings
print("\n[1.2] Loading mappings...")
with open('Mappings.json', 'r', encoding='utf-8') as f:
    mappings = json.load(f)
tags_mapping = mappings['tags_mapping']
print(f"✅ Loaded {len(tags_mapping)} hash key mappings")

# Parse JSON columns
print("\n[1.3] Parsing JSON columns...")

def safe_parse_json(json_string):
    if pd.isna(json_string):
        return None
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        try:
            return ast.literal_eval(json_string)
        except (ValueError, SyntaxError):
            return None

df['ratings_parsed'] = df['ratings'].apply(safe_parse_json)
df['normalized_rating'] = df['ratings_parsed'].apply(lambda x: x.get('normalized') if x else None)
df['raw_rating'] = df['ratings_parsed'].apply(lambda x: x.get('raw') if x else None)

df['tags_parsed'] = df['tags'].apply(safe_parse_json)

def extract_hash_values(tags_list):
    if not tags_list or not isinstance(tags_list, list):
        return []
    return [tag.get('value') for tag in tags_list if isinstance(tag, dict) and 'value' in tag]

df['hash_values'] = df['tags_parsed'].apply(extract_hash_values)
print("✅ JSON columns parsed successfully")

# Map to offerings and destinations
print("\n[1.4] Mapping hash keys to offerings and destinations...")

def map_hash_to_attributes(hash_list, mappings_dict):
    if not hash_list:
        return [], []

    offerings = []
    destinations = []

    for hash_val in hash_list:
        if hash_val in mappings_dict:
            mapping = mappings_dict[hash_val]
            if len(mapping) >= 2:
                offerings.append(mapping[0])
                destinations.append(mapping[1])

    offerings = list(dict.fromkeys(offerings))
    destinations = list(dict.fromkeys(destinations))

    return offerings, destinations

df[['offerings_list', 'destinations_list']] = df['hash_values'].apply(
    lambda x: pd.Series(map_hash_to_attributes(x, tags_mapping))
)

df['offerings'] = df['offerings_list'].apply(lambda x: ', '.join(x) if x else '')
df['destinations'] = df['destinations_list'].apply(lambda x: ', '.join(x) if x else '')
print("✅ Mapping completed")

# Create clean dataframe
df_clean = df[[
    'id', 'content', 'date', 'language', 'title',
    'normalized_rating', 'raw_rating',
    'offerings', 'destinations',
    'offerings_list', 'destinations_list'
]].copy()

print(f"✅ Phase 1 Complete! Clean dataset shape: {df_clean.shape}")

# Save Phase 1 output
df_clean.to_csv('preprocessed_data.csv', index=False)
print("💾 Saved: preprocessed_data.csv")

#==============================================================================
# PHASE 2: TEXT CLEANING AND NLP PREPROCESSING
#==============================================================================

print("\n" + "="*80)
print("PHASE 2: TEXT CLEANING AND NLP PREPROCESSING")
print("="*80)

from text_preprocessing import preprocess_dataframe, TextCleaner

print("\n[2.1] Cleaning text (multilingual: Arabic + English)...")
df_clean = preprocess_dataframe(
    df_clean,
    text_column='content',
    remove_stopwords=True,
    remove_numbers=False,
    normalize=True,
    lemmatize=False,
    stem=False
)
print("✅ Text cleaning completed")

# Detect language
cleaner = TextCleaner()
df_clean['detected_lang'] = df_clean['content'].apply(lambda x: cleaner.detect_language(x))
print(f"✅ Language detection completed")
print(f"   Arabic: {(df_clean['detected_lang'] == 'ara').sum()} reviews")
print(f"   English: {(df_clean['detected_lang'] == 'eng').sum()} reviews")

# Keyword extraction
print("\n[2.2] Extracting keywords using TF-IDF...")
from sklearn.feature_extraction.text import TfidfVectorizer

def extract_keywords_tfidf(texts, top_n=20, max_features=1000):
    texts = [t for t in texts if isinstance(t, str) and len(t.strip()) > 0]
    if len(texts) == 0:
        return []

    vectorizer = TfidfVectorizer(max_features=max_features, ngram_range=(1, 2))
    tfidf_matrix = vectorizer.fit_transform(texts)
    feature_names = vectorizer.get_feature_names_out()
    avg_tfidf = tfidf_matrix.mean(axis=0).A1
    top_indices = avg_tfidf.argsort()[-top_n:][::-1]
    return [(feature_names[i], avg_tfidf[i]) for i in top_indices]

# Extract for Arabic
arabic_texts = df_clean[df_clean['detected_lang'] == 'ara']['cleaned_text'].tolist()
arabic_keywords = extract_keywords_tfidf(arabic_texts, top_n=15)
print("✅ Top Arabic keywords extracted:")
for word, score in arabic_keywords[:5]:
    print(f"   - {word}: {score:.4f}")

# Extract for English
english_texts = df_clean[df_clean['detected_lang'] == 'eng']['cleaned_text'].tolist()
english_keywords = extract_keywords_tfidf(english_texts, top_n=15)
print("✅ Top English keywords extracted:")
for word, score in english_keywords[:5]:
    print(f"   - {word}: {score:.4f}")

print(f"✅ Phase 2 Complete!")

#==============================================================================
# PHASE 3: SENTIMENT ANALYSIS
#==============================================================================

print("\n" + "="*80)
print("PHASE 3: SENTIMENT ANALYSIS")
print("="*80)

from sentiment_analysis import RatingBasedSentimentAnalyzer

print("\n[3.1] Analyzing sentiment (rating-based approach)...")
analyzer = RatingBasedSentimentAnalyzer()

results = []
for idx, row in df_clean.iterrows():
    result = analyzer.analyze_sentiment(row['content'], row['raw_rating'])
    results.append(result)
    if (idx + 1) % 2000 == 0:
        print(f"   Processed {idx + 1}/{len(df_clean)} reviews...")

df_clean['sentiment_label'] = [r['label'] for r in results]
df_clean['sentiment_score'] = [r['score'] for r in results]

print("✅ Sentiment analysis completed")

# Sentiment distribution
sentiment_dist = df_clean['sentiment_label'].value_counts()
print(f"\nSentiment Distribution:")
for sentiment, count in sentiment_dist.items():
    percentage = (count / len(df_clean)) * 100
    print(f"   {sentiment.capitalize()}: {count} ({percentage:.2f}%)")

print(f"✅ Phase 3 Complete!")

# Save Phase 3 output
df_clean.to_csv('processed_data_with_sentiment.csv', index=False)
print("💾 Saved: processed_data_with_sentiment.csv")

#==============================================================================
# PHASE 4: EXPLORATORY DATA ANALYSIS
#==============================================================================

print("\n" + "="*80)
print("PHASE 4: EXPLORATORY DATA ANALYSIS")
print("="*80)

print("\n[4.1] Generating visualizations...")

# Create output directory for plots
import os
os.makedirs('visualizations', exist_ok=True)

# 1. Sentiment Distribution Pie Chart
fig, ax = plt.subplots(figsize=(10, 6))
colors = {'positive': 'lightgreen', 'neutral': 'lightblue', 'negative': 'lightcoral'}
pie_colors = [colors.get(label, 'gray') for label in sentiment_dist.index]
ax.pie(sentiment_dist.values, labels=sentiment_dist.index, autopct='%1.1f%%',
       colors=pie_colors, startangle=90)
ax.set_title('Sentiment Distribution', fontsize=16, fontweight='bold')
plt.savefig('visualizations/01_sentiment_distribution.png', dpi=300, bbox_inches='tight')
plt.close()
print("✅ Generated: sentiment_distribution.png")

# 2. Sentiment by Rating
sentiment_by_rating = df_clean.groupby('raw_rating')['sentiment_label'].value_counts(normalize=True).unstack(fill_value=0) * 100
fig, ax = plt.subplots(figsize=(12, 6))
sentiment_by_rating.plot(kind='bar', stacked=False, ax=ax,
                         color=['lightcoral', 'lightblue', 'lightgreen'])
ax.set_title('Sentiment Distribution by Rating', fontsize=16, fontweight='bold')
ax.set_xlabel('Rating', fontsize=12)
ax.set_ylabel('Percentage (%)', fontsize=12)
ax.legend(title='Sentiment')
plt.savefig('visualizations/02_sentiment_by_rating.png', dpi=300, bbox_inches='tight')
plt.close()
print("✅ Generated: sentiment_by_rating.png")

# 3. Top Destinations
all_destinations = []
for dest_list in df_clean['destinations_list']:
    all_destinations.extend(dest_list)
dest_counter = Counter(all_destinations)
top_dest = dest_counter.most_common(10)

fig, ax = plt.subplots(figsize=(12, 6))
destinations = [d[0] for d in top_dest]
counts = [d[1] for d in top_dest]
ax.barh(destinations, counts, color='skyblue')
ax.set_xlabel('Number of Reviews', fontsize=12)
ax.set_title('Top 10 Destinations by Review Count', fontsize=16, fontweight='bold')
ax.invert_yaxis()
plt.savefig('visualizations/03_top_destinations.png', dpi=300, bbox_inches='tight')
plt.close()
print("✅ Generated: top_destinations.png")

# 4. Top Offerings
all_offerings = []
for offering_list in df_clean['offerings_list']:
    all_offerings.extend(offering_list)
offering_counter = Counter(all_offerings)
top_offerings = offering_counter.most_common(10)

fig, ax = plt.subplots(figsize=(12, 6))
offerings = [o[0] for o in top_offerings]
counts = [o[1] for o in top_offerings]
ax.barh(offerings, counts, color='lightgreen')
ax.set_xlabel('Number of Reviews', fontsize=12)
ax.set_title('Top 10 Offerings by Review Count', fontsize=16, fontweight='bold')
ax.invert_yaxis()
plt.savefig('visualizations/04_top_offerings.png', dpi=300, bbox_inches='tight')
plt.close()
print("✅ Generated: top_offerings.png")

# 5. Rating Distribution
fig, ax = plt.subplots(figsize=(10, 6))
rating_dist = df_clean['raw_rating'].value_counts().sort_index()
valid_ratings = rating_dist[rating_dist.index <= 5]
ax.bar(valid_ratings.index, valid_ratings.values, color='coral', edgecolor='black')
ax.set_xlabel('Rating', fontsize=12)
ax.set_ylabel('Count', fontsize=12)
ax.set_title('Rating Distribution', fontsize=16, fontweight='bold')
plt.savefig('visualizations/05_rating_distribution.png', dpi=300, bbox_inches='tight')
plt.close()
print("✅ Generated: rating_distribution.png")

print(f"✅ Phase 4 Complete! Generated 5 visualizations")

#==============================================================================
# SUMMARY STATISTICS
#==============================================================================

print("\n" + "="*80)
print("FINAL SUMMARY STATISTICS")
print("="*80)

print(f"\n📊 Dataset Overview:")
print(f"   Total Reviews: {len(df_clean):,}")
print(f"   Date Range: {df_clean['date'].min()} to {df_clean['date'].max()}")
print(f"   Languages: Arabic ({(df_clean['detected_lang'] == 'ara').sum()}), English ({(df_clean['detected_lang'] == 'eng').sum()})")

print(f"\n⭐ Rating Statistics:")
print(f"   Average Rating: {df_clean['raw_rating'].mean():.2f}")
print(f"   Median Rating: {df_clean['raw_rating'].median():.1f}")
print(f"   Most Common: {df_clean['raw_rating'].mode()[0]:.0f} stars")

print(f"\n😊 Sentiment Breakdown:")
for sentiment, count in sentiment_dist.items():
    print(f"   {sentiment.capitalize()}: {count:,} ({count/len(df_clean)*100:.1f}%)")

print(f"\n🏛️ Top 5 Destinations:")
for dest, count in dest_counter.most_common(5):
    print(f"   {dest}: {count:,} reviews")

print(f"\n🏨 Top 5 Offerings:")
for offering, count in offering_counter.most_common(5):
    print(f"   {offering}: {count:,} reviews")

print("\n" + "="*80)
print("✅ PIPELINE EXECUTION COMPLETE!")
print("="*80)

print("\n📁 Output Files Generated:")
print("   1. preprocessed_data.csv - Phase 1 output")
print("   2. processed_data_with_sentiment.csv - Phase 3 output")
print("   3. visualizations/ - 5 visualization images")

print("\n🎯 Next Steps:")
print("   - Phase 5: Develop ABSA Model")
print("   - Phase 6: Deploy API")
print("   - Phase 7: Implement Monitoring")
print("   - Phase 8: Generate Final Report")

print("\n" + "="*80)
