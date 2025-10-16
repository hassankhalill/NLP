"""
Run ABSA Analysis on Processed Dataset
Applies Aspect-Based Sentiment Analysis to all reviews.
"""

import sys
import pandas as pd
import numpy as np
from absa_model import analyze_dataframe_absa, get_aspect_summary
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib
matplotlib.use('Agg')

print("="*80)
print("PHASE 5: ASPECT-BASED SENTIMENT ANALYSIS (ABSA)")
print("="*80)

# Load processed data
print("\n[5.1] Loading processed data...")
df = pd.read_csv('processed_data_with_sentiment.csv')
print(f"✅ Loaded {len(df)} reviews")

# Apply ABSA
print("\n[5.2] Applying ABSA model to all reviews...")
df = analyze_dataframe_absa(df, text_column='content', rating_column='raw_rating')
print("✅ ABSA analysis complete!")

# Get aspect statistics
print("\n[5.3] Generating aspect statistics...")
aspect_stats = get_aspect_summary(df)

print("\n📊 Aspect-Level Statistics:")
print("="*80)
for aspect, stats in sorted(aspect_stats.items(), key=lambda x: x[1]['total'], reverse=True):
    total = stats['total']
    pos = stats['positive']
    neu = stats['neutral']
    neg = stats['negative']

    pos_pct = (pos / total * 100) if total > 0 else 0
    neu_pct = (neu / total * 100) if total > 0 else 0
    neg_pct = (neg / total * 100) if total > 0 else 0

    print(f"\n{aspect.upper()}:")
    print(f"   Total Mentions: {total}")
    print(f"   Positive: {pos} ({pos_pct:.1f}%)")
    print(f"   Neutral: {neu} ({neu_pct:.1f}%)")
    print(f"   Negative: {neg} ({neg_pct:.1f}%)")

# Save results
print("\n[5.4] Saving ABSA results...")
df.to_csv('data_with_absa.csv', index=False)
print("✅ Saved: data_with_absa.csv")

# Create visualizations
print("\n[5.5] Creating ABSA visualizations...")

# 1. Aspect Mention Frequency
fig, ax = plt.subplots(figsize=(12, 6))
aspects = list(aspect_stats.keys())
counts = [aspect_stats[a]['total'] for a in aspects]
sorted_indices = np.argsort(counts)[::-1]
aspects_sorted = [aspects[i] for i in sorted_indices]
counts_sorted = [counts[i] for i in sorted_indices]

ax.barh(aspects_sorted, counts_sorted, color='skyblue')
ax.set_xlabel('Number of Mentions', fontsize=12)
ax.set_title('Aspect Mention Frequency in Reviews', fontsize=16, fontweight='bold')
ax.invert_yaxis()
plt.tight_layout()
plt.savefig('visualizations/06_aspect_frequency.png', dpi=300, bbox_inches='tight')
plt.close()
print("✅ Generated: aspect_frequency.png")

# 2. Aspect Sentiment Distribution
fig, ax = plt.subplots(figsize=(14, 8))
aspect_names = []
pos_vals = []
neu_vals = []
neg_vals = []

for aspect in aspects_sorted:
    stats = aspect_stats[aspect]
    total = stats['total']
    if total > 0:
        aspect_names.append(aspect)
        pos_vals.append(stats['positive'] / total * 100)
        neu_vals.append(stats['neutral'] / total * 100)
        neg_vals.append(stats['negative'] / total * 100)

x = np.arange(len(aspect_names))
width = 0.25

ax.bar(x - width, pos_vals, width, label='Positive', color='lightgreen')
ax.bar(x, neu_vals, width, label='Neutral', color='lightblue')
ax.bar(x + width, neg_vals, width, label='Negative', color='lightcoral')

ax.set_ylabel('Percentage (%)', fontsize=12)
ax.set_title('Sentiment Distribution by Aspect', fontsize=16, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(aspect_names, rotation=45, ha='right')
ax.legend()
plt.tight_layout()
plt.savefig('visualizations/07_aspect_sentiment_distribution.png', dpi=300, bbox_inches='tight')
plt.close()
print("✅ Generated: aspect_sentiment_distribution.png")

# 3. Number of aspects per review distribution
fig, ax = plt.subplots(figsize=(10, 6))
aspect_counts = df['num_aspects'].value_counts().sort_index()
ax.bar(aspect_counts.index, aspect_counts.values, color='coral', edgecolor='black')
ax.set_xlabel('Number of Aspects Detected', fontsize=12)
ax.set_ylabel('Number of Reviews', fontsize=12)
ax.set_title('Distribution of Aspect Count per Review', fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig('visualizations/08_aspects_per_review.png', dpi=300, bbox_inches='tight')
plt.close()
print("✅ Generated: aspects_per_review.png")

# Summary statistics
print("\n" + "="*80)
print("ABSA SUMMARY STATISTICS")
print("="*80)

print(f"\n📊 Overall Statistics:")
print(f"   Total Reviews Analyzed: {len(df):,}")
print(f"   Reviews with Aspects Detected: {(df['num_aspects'] > 0).sum():,}")
print(f"   Average Aspects per Review: {df['num_aspects'].mean():.2f}")
print(f"   Max Aspects in Single Review: {df['num_aspects'].max()}")

print(f"\n🏆 Most Discussed Aspects:")
for i, (aspect, stats) in enumerate(sorted(aspect_stats.items(),
                                           key=lambda x: x[1]['total'],
                                           reverse=True)[:5], 1):
    print(f"   {i}. {aspect.capitalize()}: {stats['total']:,} mentions")

print(f"\n😊 Most Positive Aspects:")
positive_ratios = {a: (s['positive'] / s['total'] if s['total'] > 50 else 0)
                   for a, s in aspect_stats.items()}
for i, (aspect, ratio) in enumerate(sorted(positive_ratios.items(),
                                           key=lambda x: x[1],
                                           reverse=True)[:5], 1):
    if ratio > 0:
        print(f"   {i}. {aspect.capitalize()}: {ratio*100:.1f}% positive")

print(f"\n😟 Most Negative Aspects:")
negative_ratios = {a: (s['negative'] / s['total'] if s['total'] > 50 else 0)
                   for a, s in aspect_stats.items()}
for i, (aspect, ratio) in enumerate(sorted(negative_ratios.items(),
                                           key=lambda x: x[1],
                                           reverse=True)[:5], 1):
    if ratio > 0:
        print(f"   {i}. {aspect.capitalize()}: {ratio*100:.1f}% negative")

print("\n" + "="*80)
print("✅ PHASE 5 COMPLETE!")
print("="*80)

print("\n📁 Output Files:")
print("   - data_with_absa.csv: Complete dataset with ABSA results")
print("   - visualizations/06_aspect_frequency.png")
print("   - visualizations/07_aspect_sentiment_distribution.png")
print("   - visualizations/08_aspects_per_review.png")

print("\n🎯 Next Steps:")
print("   - Phase 6: Deploy API")
print("   - Phase 7: Monitoring & Retraining")
print("   - Phase 8: Final Report")
