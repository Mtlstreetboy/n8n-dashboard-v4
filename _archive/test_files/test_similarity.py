#!/usr/bin/env python3
"""Test cosine similarity"""

import sys
sys.path.append('/data/scripts')

from sentiment_financial import get_embedding, cosine_similarity, ANCHOR_POSITIVE_FINANCIAL, ANCHOR_NEGATIVE_FINANCIAL

print("=== Testing Cosine Similarity ===\n")

# Get anchors
print("Loading anchors...")
pos_emb = get_embedding(ANCHOR_POSITIVE_FINANCIAL)
neg_emb = get_embedding(ANCHOR_NEGATIVE_FINANCIAL)

# Test positive news
positive_text = "Amazon Web Services announces record revenue growth and major partnership with Microsoft"
print(f"\n1. POSITIVE: {positive_text}")
pos_vec = get_embedding(positive_text)
sim_pos = cosine_similarity(pos_vec, pos_emb)
sim_neg = cosine_similarity(pos_vec, neg_emb)
index = sim_pos - sim_neg
print(f"   Similarity to positive: {sim_pos:.3f}")
print(f"   Similarity to negative: {sim_neg:.3f}")
print(f"   Sentiment index: {index:.3f}")

# Test negative news
negative_text = "Amazon faces major layoffs and earnings miss, stock drops significantly"
print(f"\n2. NEGATIVE: {negative_text}")
neg_vec = get_embedding(negative_text)
sim_pos = cosine_similarity(neg_vec, pos_emb)
sim_neg = cosine_similarity(neg_vec, neg_emb)
index = sim_pos - sim_neg
print(f"   Similarity to positive: {sim_pos:.3f}")
print(f"   Similarity to negative: {sim_neg:.3f}")
print(f"   Sentiment index: {index:.3f}")

# Test neutral news
neutral_text = "Amazon announces new office location in Seattle"
print(f"\n3. NEUTRAL: {neutral_text}")
neu_vec = get_embedding(neutral_text)
sim_pos = cosine_similarity(neu_vec, pos_emb)
sim_neg = cosine_similarity(neu_vec, neg_emb)
index = sim_pos - sim_neg
print(f"   Similarity to positive: {sim_pos:.3f}")
print(f"   Similarity to negative: {sim_neg:.3f}")
print(f"   Sentiment index: {index:.3f}")
