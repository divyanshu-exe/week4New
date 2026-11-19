"""
End-to-End Orchestrator Pipeline for Advanced Language Trends Analysis.
Executes data preprocessing, frequency analysis, topic modeling,
clustering, linguistic complexity evaluation, and visualization generation.
"""

import os
import sys
import json
import logging
import pandas as pd
import numpy as np

from src.preprocessing import NLPPreprocessor
from src.frequency_analysis import FrequencyAnalyzer
from src.topic_modeling import TopicModelingPipeline
from src.clustering_analysis import ClusteringPipeline
from src.linguistic_complexity import LinguisticComplexityAnalyzer
from src.visualizations import TrendVisualizer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def execute_pipeline(
    corpus_csv: str = "data/processed/arxiv_nlp_corpus.csv",
    output_dir: str = "data/processed",
    viz_dir: str = "visualizations"
):
    logger.info("=" * 70)
    logger.info("STARTING NLP ADVANCED LANGUAGE TRENDS PIPELINE")
    logger.info("=" * 70)

    # 1. Load Corpus
    if not os.path.exists(corpus_csv):
        raise FileNotFoundError(f"Corpus file {corpus_csv} does not exist. Run src/data_acquisition.py first.")

    df = pd.read_csv(corpus_csv)
    logger.info(f"Loaded {len(df)} papers from {corpus_csv}.")

    # 2. Preprocessing
    processed_csv = os.path.join(output_dir, "arxiv_nlp_processed.csv")
    if os.path.exists(processed_csv):
        logger.info(f"Loading cached preprocessed dataset from {processed_csv}...")
        df = pd.read_csv(processed_csv)
        # Rehydrate tokens and bigrams lists
        df["tokens"] = df["tokens_str"].fillna("").apply(lambda s: s.split())
        df["bigrams"] = df["bigrams_str"].fillna("").apply(lambda s: s.split())
    else:
        logger.info("Step 1: Executing NLP Preprocessing (Tokenization, POS Lemmatization, Academic Stopwords Filtering)...")
        preprocessor = NLPPreprocessor()
        prep_df = preprocessor.preprocess_series(df["abstract"])
        df = pd.concat([df, prep_df], axis=1)
        
        df_to_save = df.copy()
        df_to_save["tokens_str"] = df["tokens"].apply(lambda l: " ".join(l))
        df_to_save["bigrams_str"] = df["bigrams"].apply(lambda l: " ".join(l))
        df_to_save.drop(columns=["tokens", "bigrams"]).to_csv(processed_csv, index=False)
        logger.info(f"Saved processed dataset to {processed_csv}.")

    # 3. Frequency & Trend Analysis
    logger.info("Step 2: Performing Lexical Frequency & Emergence/Decay Analysis...")
    freq_analyzer = FrequencyAnalyzer(df)
    corpus_stats = freq_analyzer.compute_ngram_frequencies(top_n=50)

    # TF-IDF Signatures
    tfidf_signatures = freq_analyzer.compute_epoch_tfidf(top_k=15)
    tfidf_signatures.to_csv(os.path.join(output_dir, "epoch_tfidf_signatures.csv"), index=False)

    # Emergence & Decay Index
    emergence_df = freq_analyzer.compute_emergence_decay_index(min_freq=8)
    emergence_df.to_csv(os.path.join(output_dir, "lexical_emergence_decay_index.csv"), index=False)

    # Target Keywords Trajectory
    target_kws = ["prompt", "llm", "transformer", "lstm", "reasoning", "hallucination", "agent", "parsing"]
    trajectories_df = freq_analyzer.track_target_keywords_over_time(target_kws)
    trajectories_df.to_csv(os.path.join(output_dir, "keyword_trajectories.csv"), index=False)
    logger.info("Frequency and lexical dynamics analysis complete.")

    # 4. Topic Modeling
    logger.info("Step 3: Performing Latent Dirichlet Allocation (LDA) & NMF Topic Modeling...")
    topic_pipeline = TopicModelingPipeline(df, n_topics=8, random_state=42)

    # Hyperparameter coherence sweep
    sweep_df = topic_pipeline.evaluate_topic_coherence_sweep(k_values=[4, 6, 8, 10])
    sweep_df.to_csv(os.path.join(output_dir, "topic_coherence_sweep.csv"), index=False)
    logger.info(f"Topic Coherence Sweep Results:\n{sweep_df.to_string(index=False)}")

    # Fit NMF (Primary) and LDA
    nmf_doc_dist = topic_pipeline.fit_nmf(max_features=2500)
    lda_doc_dist = topic_pipeline.fit_lda(max_features=2500)

    # Extract top words per topic
    nmf_topic_terms = topic_pipeline.extract_top_topic_terms(model_type="nmf", n_words=15)
    nmf_topic_terms.to_csv(os.path.join(output_dir, "nmf_topic_terms.csv"), index=False)

    lda_topic_terms = topic_pipeline.extract_top_topic_terms(model_type="lda", n_words=15)
    lda_topic_terms.to_csv(os.path.join(output_dir, "lda_topic_terms.csv"), index=False)

    # Dynamically derive semantic topic labels from top terms
    # Inspect top 3 terms of each topic
    topic_labels = {}
    for t_id in range(1, 9):
        top_terms = nmf_topic_terms[nmf_topic_terms["topic_id"] == f"Topic_{t_id}"].head(4)["term"].tolist()
        label_str = f"T{t_id}: {' / '.join(top_terms[:3]).title()}"
        topic_labels[f"Topic_{t_id}"] = label_str
    logger.info(f"Discovered Semantic Topic Labels:\n{json.dumps(topic_labels, indent=2)}")

    # Epoch topic distributions
    epoch_topic_dist = topic_pipeline.compute_epoch_topic_distribution(nmf_doc_dist, topic_labels=None)
    epoch_topic_dist.to_csv(os.path.join(output_dir, "epoch_topic_distribution.csv"), index=False)

    # 5. Semantic Clustering & LSA
    logger.info("Step 4: Performing High-Dimensional Clustering (LSA + K-Means)...")
    cluster_pipeline = ClusteringPipeline(df, n_clusters=5, random_state=42)
    clustering_metrics = cluster_pipeline.fit_lsa_kmeans(max_features=3000, n_components=50)
    logger.info(f"Clustering Quality Metrics: {clustering_metrics}")

    cluster_terms = cluster_pipeline.extract_cluster_keywords(top_n=10)
    cluster_terms.to_csv(os.path.join(output_dir, "cluster_keywords.csv"), index=False)

    cluster_names = {}
    for c_id in range(5):
        top_c = cluster_terms[cluster_terms["cluster_id"] == f"Cluster_{c_id}"].head(3)["term"].tolist()
        cluster_names[f"Cluster_{c_id}"] = f"C{c_id+1}: {'-'.join(top_c).title()}"
    logger.info(f"Cluster Semantic Names: {cluster_names}")

    crosstab_df, chi2_stats = cluster_pipeline.analyze_cluster_epoch_distribution()
    crosstab_df.to_csv(os.path.join(output_dir, "cluster_epoch_crosstab.csv"))
    logger.info(f"Cluster Diachronic Shift Chi-Square Test: {chi2_stats}")

    proj_df = cluster_pipeline.get_2d_projection()

    # 6. Linguistic Complexity, Readability, & Epistemic Stance
    logger.info("Step 5: Computing Syntactic Complexity, Readability Indices, and Epistemic Stance...")
    ling_analyzer = LinguisticComplexityAnalyzer(df)
    complexity_df = ling_analyzer.compute_corpus_complexity()
    epoch_summary = ling_analyzer.compute_epoch_summary(complexity_df)
    epoch_summary.to_csv(os.path.join(output_dir, "linguistic_complexity_summary.csv"))
    logger.info(f"Linguistic Complexity Epoch Aggregates:\n{epoch_summary}")

    # 7. Visualization Generation
    logger.info("Step 6: Generating Publication-Grade Visualizations (300 DPI)...")
    viz = TrendVisualizer(output_dir=viz_dir)
    f1 = viz.plot_corpus_volume(corpus_stats)
    f2 = viz.plot_emergent_vs_decaying(emergence_df, top_k=12)
    f3 = viz.plot_keyword_trajectories(trajectories_df)
    f4 = viz.plot_top_bigrams(corpus_stats["epoch_bigrams"], top_k=8)
    f5 = viz.plot_topic_coherence_sweep(sweep_df)
    f6 = viz.plot_topic_streamgraph(epoch_topic_dist, topic_labels)
    f7 = viz.plot_topic_heatmap(epoch_topic_dist, topic_labels)
    f8 = viz.plot_semantic_clustering(proj_df, cluster_names)
    f9 = viz.plot_cluster_epoch_migration(crosstab_df, cluster_names)
    f10 = viz.plot_linguistic_complexity_dashboard(complexity_df)
    f11 = viz.plot_epoch_wordclouds(corpus_stats["epoch_unigrams"])

    logger.info(f"Successfully generated all 11 high-resolution figures in {viz_dir}/.")

    # Save summary metadata JSON for report generation
    summary_metadata = {
        "corpus_size": len(df),
        "epochs": list(corpus_stats["epoch_vocab_size"].keys()),
        "vocab_sizes": corpus_stats["epoch_vocab_size"],
        "token_counts": corpus_stats["epoch_total_tokens"],
        "clustering_metrics": clustering_metrics,
        "chi2_test": chi2_stats,
        "topic_labels": topic_labels,
        "cluster_names": cluster_names,
        "top_emergent_terms": emergence_df[emergence_df["emergence_index"] > 1.5].head(10)[["term", "norm_freq_e1", "norm_freq_e4", "emergence_index"]].to_dict(orient="records"),
        "top_decaying_terms": emergence_df[emergence_df["emergence_index"] < -1.5].tail(10)[["term", "norm_freq_e1", "norm_freq_e4", "emergence_index"]].to_dict(orient="records")
    }
    with open(os.path.join(output_dir, "summary_metadata.json"), "w", encoding="utf-8") as f:
        json.dump(summary_metadata, f, indent=2)

    logger.info("=" * 70)
    logger.info("PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")
    logger.info("=" * 70)
    return summary_metadata

if __name__ == "__main__":
    execute_pipeline()
