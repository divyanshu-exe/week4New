"""
Clustering and Semantic Geometry Module.
Performs TF-IDF vectorization, Latent Semantic Analysis (TruncatedSVD),
K-Means document clustering, silhouette evaluation, and diachronic cluster migration.
"""

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score
from scipy.stats import chi2_contingency

class ClusteringPipeline:
    def __init__(self, df: pd.DataFrame, n_clusters: int = 5, random_state: int = 42):
        self.df = df
        self.n_clusters = n_clusters
        self.random_state = random_state

        self.vectorizer = None
        self.svd_model = None
        self.kmeans_model = None
        self.tfidf_matrix = None
        self.lsa_embeddings = None
        self.cluster_labels = None
        self.cluster_names = {}

    def fit_lsa_kmeans(self, max_features: int = 3000, n_components: int = 50):
        """Fits TF-IDF -> TruncatedSVD (LSA) -> KMeans clustering."""
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            min_df=4,
            max_df=0.80,
            sublinear_tf=True
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(self.df["token_str"])

        # Dimensionality reduction via LSA
        self.svd_model = TruncatedSVD(n_components=n_components, random_state=self.random_state)
        self.lsa_embeddings = self.svd_model.fit_transform(self.tfidf_matrix)

        # KMeans
        self.kmeans_model = KMeans(
            n_clusters=self.n_clusters,
            random_state=self.random_state,
            n_init=10,
            max_iter=300
        )
        self.cluster_labels = self.kmeans_model.fit_predict(self.lsa_embeddings)
        self.df["cluster"] = self.cluster_labels

        # Metrics
        sil_score = float(silhouette_score(self.lsa_embeddings, self.cluster_labels))
        db_score = float(davies_bouldin_score(self.lsa_embeddings, self.cluster_labels))

        return {
            "silhouette_score": round(sil_score, 4),
            "davies_bouldin_score": round(db_score, 4),
            "explained_variance_ratio": round(float(self.svd_model.explained_variance_ratio_.sum()), 4)
        }

    def extract_cluster_keywords(self, top_n: int = 10) -> pd.DataFrame:
        """Extracts top representative keywords for each cluster centroid."""
        # Project cluster centers back to TF-IDF feature space
        # centroid in LSA space: (n_clusters, n_components)
        # SVD components: (n_components, n_features)
        centroid_tfidf = np.dot(self.kmeans_model.cluster_centers_, self.svd_model.components_)
        feature_names = self.vectorizer.get_feature_names_out()

        records = []
        for cluster_id in range(self.n_clusters):
            row = centroid_tfidf[cluster_id]
            top_idx = np.argsort(row)[::-1][:top_n]
            top_words = feature_names[top_idx]
            top_weights = row[top_idx]

            for rank, (word, weight) in enumerate(zip(top_words, top_weights), 1):
                records.append({
                    "cluster_id": f"Cluster_{cluster_id}",
                    "rank": rank,
                    "term": word,
                    "weight": round(float(weight), 4)
                })

        return pd.DataFrame(records)

    def analyze_cluster_epoch_distribution(self) -> tuple[pd.DataFrame, dict]:
        """Cross-tabulates clusters across epochs and performs Chi-Square independence test."""
        crosstab = pd.crosstab(self.df["epoch"], self.df["cluster"], normalize="index") * 100.0
        crosstab = crosstab.round(2)

        # Raw counts for Chi-square
        count_tab = pd.crosstab(self.df["epoch"], self.df["cluster"])
        chi2, p_val, dof, _ = chi2_contingency(count_tab)

        stats = {
            "chi2_statistic": round(float(chi2), 2),
            "p_value": float(p_val),
            "degrees_of_freedom": int(dof),
            "is_significant": bool(p_val < 0.001)
        }

        return crosstab, stats

    def get_2d_projection(self) -> pd.DataFrame:
        """Extracts first 2 LSA components for scatter plot visualization."""
        proj_df = pd.DataFrame({
            "svd_1": self.lsa_embeddings[:, 0],
            "svd_2": self.lsa_embeddings[:, 1],
            "cluster": self.cluster_labels,
            "epoch": self.df["epoch"].values,
            "title": self.df["title"].values
        })
        return proj_df

if __name__ == "__main__":
    pass
