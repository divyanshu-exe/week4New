"""
Unit Tests for Advanced Language Trends NLP Pipeline.
Verifies data preprocessing, frequency metrics, topic modeling,
clustering geometry, readability calculations, and deliverable artifacts.
"""

import os
import unittest
import pandas as pd
import numpy as np

from src.preprocessing import NLPPreprocessor
from src.frequency_analysis import FrequencyAnalyzer
from src.topic_modeling import TopicModelingPipeline, compute_umass_coherence
from src.clustering_analysis import ClusteringPipeline
from src.linguistic_complexity import LinguisticComplexityAnalyzer, count_syllables_in_word

class TestNLPPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.sample_texts = [
            "In this paper, we propose a novel transformer-based framework for sentiment analysis ($F_1 = 92.4\\%$).",
            "Recurrent neural networks and LSTMs have achieved state-of-the-art results in sequence modeling.",
            "Large language models (LLMs) with prompt engineering demonstrate emergent reasoning capabilities.",
            "Autonomous multi-agent architectures mitigate hallucinations in generative question answering."
        ]
        cls.prep = NLPPreprocessor(remove_academic_stopwords=True)
        cls.df_mock = pd.DataFrame({
            "abstract": cls.sample_texts,
            "epoch": [
                "Epoch 1 (2018-2019)",
                "Epoch 1 (2018-2019)",
                "Epoch 4 (2024-2025)",
                "Epoch 4 (2024-2025)"
            ],
            "year": [2018, 2019, 2024, 2025]
        })
        prep_results = cls.prep.preprocess_series(cls.df_mock["abstract"])
        cls.df_mock = pd.concat([cls.df_mock, prep_results], axis=1)

    def test_preprocessing_cleaning(self):
        cleaned = self.prep.clean_text("Testing LaTeX $x = \\alpha$ and URL https://arxiv.org/abs/1234")
        self.assertNotIn("$x", cleaned)
        self.assertNotIn("https", cleaned)
        self.assertIn("testing", cleaned)

    def test_preprocessing_lemmatization(self):
        tokens = self.prep.tokenize_and_lemmatize("The researchers evaluated prompting strategies on transformer models.")
        self.assertIn("prompt", tokens)  # Correctly lemmatized from 'prompting'
        self.assertIn("transformer", tokens)  # Plural reduced

    def test_syllable_counter(self):
        self.assertEqual(count_syllables_in_word("transformer"), 3)
        self.assertEqual(count_syllables_in_word("ai"), 1)
        self.assertEqual(count_syllables_in_word("reasoning"), 3)

    def test_frequency_analyzer(self):
        fa = FrequencyAnalyzer(self.df_mock)
        res = fa.compute_ngram_frequencies(top_n=10)
        self.assertIn("overall_unigrams", res)
        self.assertIn("epoch_vocab_size", res)

    def test_emergence_decay_index(self):
        fa = FrequencyAnalyzer(self.df_mock)
        df_trends = fa.compute_emergence_decay_index(min_freq=1)
        self.assertIsInstance(df_trends, pd.DataFrame)
        self.assertTrue(len(df_trends) > 0)
        self.assertIn("emergence_index", df_trends.columns)

    def test_umass_coherence(self):
        sample_corpus = [["transformer", "attention", "neural"], ["transformer", "attention", "model"]]
        topics = [["transformer", "attention"]]
        score = compute_umass_coherence(topics, sample_corpus)
        self.assertIsInstance(score, float)
        self.assertTrue(score <= 0.01)

    def test_linguistic_complexity(self):
        lca = LinguisticComplexityAnalyzer(self.df_mock)
        doc_metrics = lca.analyze_document(self.sample_texts[0], ["transformer", "sentiment", "analysis"])
        self.assertIn("flesch_reading_ease", doc_metrics)
        self.assertIn("fk_grade_level", doc_metrics)
        self.assertIn("sentiment_compound", doc_metrics)
        self.assertTrue(doc_metrics["fk_grade_level"] > 0)

    def test_deliverable_artifacts_exist(self):
        expected_figures = [
            "visualizations/fig1_corpus_volume.png",
            "visualizations/fig2_emergent_vs_decaying_lexicon.png",
            "visualizations/fig3_target_keywords_trajectories.png",
            "visualizations/fig4_top_bigrams_per_epoch.png",
            "visualizations/fig5_topic_coherence_sweep.png",
            "visualizations/fig6_topic_evolution_streamgraph.png",
            "visualizations/fig7_topic_epoch_intensity_heatmap.png",
            "visualizations/fig8_semantic_clustering_lsa.png",
            "visualizations/fig9_cluster_epoch_shift_stacked.png",
            "visualizations/fig10_linguistic_complexity_dashboard.png",
            "visualizations/fig11_epoch_wordclouds.png"
        ]
        for fig_path in expected_figures:
            self.assertTrue(os.path.exists(fig_path), f"Figure missing: {fig_path}")
            self.assertTrue(os.path.getsize(fig_path) > 10000, f"Figure too small: {fig_path}")

        # Final DOCX report
        report_path = "reports/Advanced_Language_Trends_NLP_Report.docx"
        self.assertTrue(os.path.exists(report_path), "Final report DOCX missing!")
        self.assertTrue(os.path.getsize(report_path) > 1000000, "Final report DOCX file size is unexpectedly small!")

if __name__ == "__main__":
    unittest.main()
