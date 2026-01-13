#!/usr/bin/env python3
"""Test embeddings API"""

import sys
sys.path.append('/data/scripts')

from sentiment_financial import get_embedding, ANCHOR_POSITIVE_FINANCIAL, ANCHOR_NEGATIVE_FINANCIAL

print("=== Testing Embedding API ===\n")

# Test text
text = "Amazon Web Services announces new AI chips, beating earnings expectations"

print(f"Text: {text}\n")

# Get embeddings
print("Getting embeddings...")
text_emb = get_embedding(text)
pos_emb = get_embedding(ANCHOR_POSITIVE_FINANCIAL)
neg_emb = get_embedding(ANCHOR_NEGATIVE_FINANCIAL)

print(f"Text embedding: {text_emb.shape if text_emb is not None else 'None'}")
print(f"Positive anchor: {pos_emb.shape if pos_emb is not None else 'None'}")
print(f"Negative anchor: {neg_emb.shape if neg_emb is not None else 'None'}")

if text_emb is not None:
    print(f"\nText embedding sample (first 5 values): {text_emb[:5]}")
    print(f"Text embedding norm: {(text_emb ** 2).sum() ** 0.5:.3f}")
