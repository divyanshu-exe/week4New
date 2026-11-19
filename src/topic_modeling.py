"""
Topic Modeling Module for Longitudinal NLP Trends.
Implements Latent Dirichlet Allocation (LDA) and Non-Negative Matrix Factorization (NMF),
topic coherence scoring, and diachronic topic trajectory quantification.
"""

import math
import numpy as np
import pandas as pd
from collections import Counter
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation, NMF

def compute_umass_coherence(top_words_per_topic: list[list[str]], tokenized_corpus: list[list[str]], epsilon: float = 1e-12) -> float:
    """Computes UMass Topic Coherence score based on document co-occurrence.
    UMass(V) = sum_{m=2}^M sum_{l=1}^{m-1} log( (D(v_m, v_l) + eps) / D(v_l) )
    Higher (less negative) values indicate more coherent topics.
    """
    # Precompute document frequencies
    doc_sets = [set(doc) for doc in tokenized_corpus]
    num_docs = len(doc_sets)

    def doc_freq(word):
        return sum(1 for d in doc_sets if word in d)

    def co_doc_freq(w1, w2):
        return sum(1 for d in doc_sets if w1 in d and w2 in d)

    topic_coherences = []
    for top_words in top_words_per_topic:
        coherence = 0.0
        M = len(top_words)
        pairs_count = 0
        for m in range(1, M):
            for l in range(0, m):
                w_m = top_words[m]
                w_l = top_words[l]
                d_l = doc_freq(w_l)
                d_ml = co_doc_freq(w_m, w_l)
                if d_l > 0:
                    coherence += math.log((d_ml + epsilon) / d_l)
                    pairs_count += 1
        if pairs_count > 0:
            topic_coherences.append(coherence / pairs_count)

    return float(np.mean(topic_coherences)) if topic_coherences else -100.0

class TopicModelingPipeline:
    def __init__(self, df: pd.DataFrame, n_topics: int = 8, random_state: int = 42):
        self.df = df
        self.n_topics = n_topics
        self.random_state = random_state
        self.epochs = sorted(df["epoch"].unique())

        self.count_vectorizer = None
        self.tfidf_vectorizer = None
        self.lda_model = None
        self.nmf_model = None
        self.topic_names = {}

    def fit_lda(self, max_features: int = 2500):
        """Fits Latent Dirichlet Allocation on token count matrix."""
        self.count_vectorizer = CountVectorizer(
            max_features=max_features,
            min_df=5,
            max_df=0.85,
            stop_words=None  # Already stopped in preprocessing
        )
        dtm = self.count_vectorizer.fit_transform(self.df["token_str"])

        self.lda_model = LatentDirichletAllocation(
            n_components=self.n_topics,
            random_state=self.random_state,
            learning_method="batch",
            max_iter=20,
            n_jobs=1
        )
        doc_topic_dist = self.lda_model.fit_transform(dtm)
        return doc_topic_dist

    def fit_nmf(self, max_features: int = 2500):
        """Fits Non-Negative Matrix Factorization on TF-IDF matrix."""
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=max_features,
            min_df=5,
            max_df=0.85,
            sublinear_tf=True
        )
        tfidf_dtm = self.tfidf_vectorizer.fit_transform(self.df["token_str"])

        self.nmf_model = NMF(
            n_components=self.n_topics,
            random_state=self.random_state,
            init="nndsvda",
            max_iter=300
        )
        doc_topic_dist = self.nmf_model.fit_transform(tfidf_dtm)
        # Normalize rows to sum to 1
        row_sums = doc_topic_dist.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0
        doc_topic_dist = doc_topic_dist / row_sums
        return doc_topic_dist

    def evaluate_topic_coherence_sweep(self, k_values: list[int] = [4, 6, 8, 10]) -> pd.DataFrame:
        """Sweeps topic counts k and calculates UMass coherence to identify optimal k."""
        token_corpus = self.df["tokens"].tolist()
        results = []

        for k in k_values:
            # LDA sweep
            cv = CountVectorizer(max_features=2000, min_df=5, max_df=0.85)
            dtm = cv.fit_transform(self.df["token_str"])
            lda = LatentDirichletAllocation(n_components=k, random_state=self.random_state, max_iter=10, n_jobs=1)
            lda.fit(dtm)
            feature_names = cv.get_feature_names_out()
            lda_top_words = []
            for comp in lda.components_:
                top_idx = comp.argsort()[:-11:-1]
                lda_top_words.append([feature_names[i] for i in top_idx])
            lda_coherence = compute_umass_coherence(lda_top_words, token_corpus)

            # NMF sweep
            tv = TfidfVectorizer(max_features=2000, min_df=5, max_df=0.85, sublinear_tf=True)
            tfidf_mat = tv.fit_transform(self.df["token_str"])
            nmf = NMF(n_components=k, random_state=self.random_state, init="nndsvda", max_iter=200)
            nmf.fit(tfidf_mat)
            tv_features = tv.get_feature_names_out()
            nmf_top_words = []
            for comp in nmf.components_:
                top_idx = comp.argsort()[:-11:-1]
                nmf_top_words.append([tv_features[i] for i in top_idx])
            nmf_coherence = compute_umass_coherence(nmf_top_words, token_corpus)

            results.append({
                "k": k,
                "lda_coherence": round(lda_coherence, 4),
                "lda_perplexity": round(lda.perplexity(dtm), 2),
                "nmf_coherence": round(nmf_coherence, 4),
                "nmf_reconstruction_err": round(nmf.reconstruction_err_, 2)
            })

        return pd.DataFrame(results)

    def extract_top_topic_terms(self, model_type: str = "nmf", n_words: int = 15) -> pd.DataFrame:
        """Extracts top keywords for each discovered topic."""
        if model_type == "nmf":
            model = self.nmf_model
            features = self.tfidf_vectorizer.get_feature_names_out()
        else:
            model = self.lda_model
            features = self.count_vectorizer.get_feature_names_out()

        records = []
        for topic_idx, comp in enumerate(model.components_):
            top_indices = comp.argsort()[:-n_words - 1:-1]
            top_words = [features[i] for i in top_indices]
            weights = comp[top_indices]
            # Normalize weights
            norm_weights = weights / weights.sum()

            for rank, (word, weight) in enumerate(zip(top_words, norm_weights), 1):
                records.append({
                    "topic_id": f"Topic_{topic_idx + 1}",
                    "rank": rank,
                    "term": word,
                    "weight": round(float(weight), 4)
                })

        return pd.DataFrame(records)

    def compute_epoch_topic_distribution(self, doc_topic_dist: np.ndarray, topic_labels: dict = None) -> pd.DataFrame:
        """Aggregates topic weights across epochs to track longitudinal evolution."""
        n_comps = doc_topic_dist.shape[1]
        col_names = [f"Topic_{i+1}" for i in range(n_comps)]
        topic_df = pd.DataFrame(doc_topic_dist, columns=col_names)
        topic_df["epoch"] = self.df["epoch"].values
        topic_df["year"] = self.df["year"].values

        epoch_agg = topic_df.groupby("epoch")[col_names].mean().reset_index()

        # If custom topic names are provided, rename columns
        if topic_labels:
            epoch_agg.rename(columns=topic_labels, inplace=True)

        return epoch_agg

if __name__ == "__main__":
    pass
