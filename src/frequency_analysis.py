"""
Frequency Analysis & Lexical Trend Detection Module.
Computes unigram/bigram frequencies, TF-IDF epoch signatures,
and quantifies Lexical Emergence vs Decay indices.
"""

import os
import math
import numpy as np
import pandas as pd
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer

class FrequencyAnalyzer:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.epochs = sorted(df["epoch"].unique())

    def compute_ngram_frequencies(self, top_n: int = 50) -> dict:
        """Computes top unigrams and bigrams per epoch and overall."""
        results = {
            "overall_unigrams": Counter(),
            "overall_bigrams": Counter(),
            "epoch_unigrams": {},
            "epoch_bigrams": {},
            "epoch_vocab_size": {},
            "epoch_total_tokens": {}
        }

        for epoch in self.epochs:
            sub_df = self.df[self.df["epoch"] == epoch]
            epoch_tokens = [tok for toks in sub_df["tokens"] for tok in toks]
            epoch_bigrams = [bg for bgs in sub_df["bigrams"] for bg in bgs]

            u_counts = Counter(epoch_tokens)
            b_counts = Counter(epoch_bigrams)

            results["epoch_unigrams"][epoch] = u_counts
            results["epoch_bigrams"][epoch] = b_counts
            results["epoch_vocab_size"][epoch] = len(u_counts)
            results["epoch_total_tokens"][epoch] = len(epoch_tokens)

            results["overall_unigrams"].update(u_counts)
            results["overall_bigrams"].update(b_counts)

        return results

    def compute_epoch_tfidf(self, top_k: int = 20) -> pd.DataFrame:
        """Extracts top TF-IDF signature terms for each epoch."""
        # Aggregate all text per epoch into a pseudo-document
        epoch_docs = []
        for epoch in self.epochs:
            sub_df = self.df[self.df["epoch"] == epoch]
            epoch_docs.append(" ".join(sub_df["token_str"]))

        vectorizer = TfidfVectorizer(max_features=5000, sublinear_tf=True)
        tfidf_mat = vectorizer.fit_transform(epoch_docs).toarray()
        feature_names = np.array(vectorizer.get_feature_names_out())

        records = []
        for idx, epoch in enumerate(self.epochs):
            row = tfidf_mat[idx]
            top_indices = np.argsort(row)[::-1][:top_k]
            top_words = feature_names[top_indices]
            top_scores = row[top_indices]

            for rank, (word, score) in enumerate(zip(top_words, top_scores), 1):
                records.append({
                    "epoch": epoch,
                    "rank": rank,
                    "term": word,
                    "tfidf_score": round(float(score), 4)
                })

        return pd.DataFrame(records)

    def compute_emergence_decay_index(self, min_freq: int = 10) -> pd.DataFrame:
        """Calculates growth ratios, log emergence index, and categorizes lexical dynamics."""
        epoch_1 = self.epochs[0]
        epoch_4 = self.epochs[-1]

        sub_1 = self.df[self.df["epoch"] == epoch_1]
        sub_4 = self.df[self.df["epoch"] == epoch_4]

        tokens_1 = Counter([tok for toks in sub_1["tokens"] for tok in toks])
        tokens_4 = Counter([tok for toks in sub_4["tokens"] for tok in toks])

        total_1 = sum(tokens_1.values())
        total_4 = sum(tokens_4.values())

        all_vocab = set(tokens_1.keys()).union(set(tokens_4.keys()))
        records = []

        for term in all_vocab:
            c1 = tokens_1.get(term, 0)
            c4 = tokens_4.get(term, 0)

            # Filter terms that are too rare in both
            if (c1 + c4) < min_freq:
                continue

            # Normalized frequency per 10,000 tokens
            norm_f1 = (c1 / total_1) * 10000.0
            norm_f4 = (c4 / total_4) * 10000.0

            # Log2 Emergence Index with Laplace smoothing
            emergence_index = math.log2((norm_f4 + 0.5) / (norm_f1 + 0.5))
            growth_ratio = (norm_f4 + 0.1) / (norm_f1 + 0.1)

            category = "Stable"
            if emergence_index >= 1.5:
                category = "Emergent (High Growth)"
            elif emergence_index <= -1.5:
                category = "Decaying (Obsolescent)"
            elif emergence_index >= 0.5:
                category = "Moderate Rise"
            elif emergence_index <= -0.5:
                category = "Moderate Decline"

            records.append({
                "term": term,
                "raw_count_e1": c1,
                "raw_count_e4": c4,
                "norm_freq_e1": round(norm_f1, 2),
                "norm_freq_e4": round(norm_f4, 2),
                "emergence_index": round(emergence_index, 3),
                "growth_ratio": round(growth_ratio, 2),
                "category": category
            })

        df_trends = pd.DataFrame(records)
        df_trends = df_trends.sort_values(by="emergence_index", ascending=False).reset_index(drop=True)
        return df_trends

    def track_target_keywords_over_time(self, target_words: list[str]) -> pd.DataFrame:
        """Tracks the normalized frequency of specific benchmark keywords across all epochs."""
        records = []
        for epoch in self.epochs:
            sub = self.df[self.df["epoch"] == epoch]
            all_toks = [t for toks in sub["tokens"] for t in toks]
            tot = len(all_toks)
            cnts = Counter(all_toks)

            for w in target_words:
                c = cnts.get(w, 0)
                norm_c = (c / tot) * 10000.0 if tot > 0 else 0
                records.append({
                    "epoch": epoch,
                    "keyword": w,
                    "raw_count": c,
                    "norm_freq_per_10k": round(norm_c, 2)
                })

        return pd.DataFrame(records)

if __name__ == "__main__":
    pass
