"""
Test script to verify Phase 1 (Data Preprocessing) works correctly
"""

import pandas as pd
import json
import ast
import sys

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 70)
print("TESTING PHASE 1: DATA PREPROCESSING")
print("=" * 70)

# Test 1: Load Dataset
print("\n[1/6] Loading dataset...")
try:
    df = pd.read_csv('DataSet.csv')
    print(f"✅ Success! Loaded {len(df)} rows and {len(df.columns)} columns")
    print(f"   Columns: {df.columns.tolist()}")
except Exception as e:
    print(f"❌ Error loading dataset: {e}")
    exit(1)

# Test 2: Load Mappings
print("\n[2/6] Loading mappings...")
try:
    with open('Mappings.json', 'r', encoding='utf-8') as f:
        mappings = json.load(f)
    tags_mapping = mappings['tags_mapping']
    print(f"✅ Success! Loaded {len(tags_mapping)} mappings")
except Exception as e:
    print(f"❌ Error loading mappings: {e}")
    exit(1)

# Test 3: Parse JSON columns
print("\n[3/6] Parsing JSON columns...")
try:
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

    print(f"✅ Success! Parsed ratings and tags")
    print(f"   Sample normalized rating: {df['normalized_rating'].iloc[0]}")
    print(f"   Sample raw rating: {df['raw_rating'].iloc[0]}")
except Exception as e:
    print(f"❌ Error parsing JSON: {e}")
    exit(1)

# Test 4: Extract hash values
print("\n[4/6] Extracting hash values...")
try:
    def extract_hash_values(tags_list):
        if not tags_list or not isinstance(tags_list, list):
            return []
        return [tag.get('value') for tag in tags_list if isinstance(tag, dict) and 'value' in tag]

    df['hash_values'] = df['tags_parsed'].apply(extract_hash_values)
    print(f"✅ Success! Extracted hash values")
    print(f"   Sample hash values: {df['hash_values'].iloc[0]}")
except Exception as e:
    print(f"❌ Error extracting hash values: {e}")
    exit(1)

# Test 5: Map to offerings and destinations
print("\n[5/6] Mapping to offerings and destinations...")
try:
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

    print(f"✅ Success! Mapped to offerings and destinations")
    print(f"   Sample offering: {df['offerings'].iloc[1]}")
    print(f"   Sample destination: {df['destinations'].iloc[1]}")
except Exception as e:
    print(f"❌ Error mapping: {e}")
    exit(1)

# Test 6: Create clean dataframe
print("\n[6/6] Creating clean dataframe...")
try:
    df_clean = df[[
        'id', 'content', 'date', 'language', 'title',
        'normalized_rating', 'raw_rating',
        'offerings', 'destinations',
        'offerings_list', 'destinations_list'
    ]].copy()

    print(f"✅ Success! Created clean dataframe")
    print(f"   Shape: {df_clean.shape}")
    print(f"   Missing values:\n{df_clean.isnull().sum()}")
except Exception as e:
    print(f"❌ Error creating clean dataframe: {e}")
    exit(1)

# Save preprocessed data
print("\n[SAVING] Saving preprocessed data...")
try:
    df_clean.to_csv('preprocessed_data.csv', index=False)
    print(f"✅ Saved to 'preprocessed_data.csv'")
except Exception as e:
    print(f"❌ Error saving: {e}")

# Final summary
print("\n" + "=" * 70)
print("PHASE 1 TEST COMPLETE - ALL TESTS PASSED! ✅")
print("=" * 70)
print(f"\nDataset Summary:")
print(f"  Total Reviews: {len(df_clean)}")
print(f"  Languages: {df['language'].value_counts().to_dict()}")
print(f"  Rating Distribution:\n{df_clean['raw_rating'].value_counts().sort_index()}")
print(f"\nTop 5 Destinations:")
from collections import Counter
all_dest = []
for d in df_clean['destinations_list']:
    all_dest.extend(d)
for dest, count in Counter(all_dest).most_common(5):
    print(f"  - {dest}: {count}")

print("\n✅ Phase 1 is working correctly! Ready to proceed to Phase 2.")
