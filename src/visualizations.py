"""
Visualization Module for NLP Language Trends Analysis.
Generates publication-quality charts (300 DPI) for report and repository.
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from wordcloud import WordCloud

# Publication styling settings
plt.rcParams.update({
    "font.sans-serif": "Arial",
    "font.family": "sans-serif",
    "figure.titlesize": 14,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.dpi": 300,
    "savefig.dpi": 300
})

sns.set_theme(style="whitegrid", palette="muted")

class TrendVisualizer:
    def __init__(self, output_dir: str = "visualizations"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def plot_corpus_volume(self, corpus_stats: dict, filename: str = "fig1_corpus_volume.png"):
        """Fig 1: Two-panel chart showing paper count and vocabulary growth across epochs."""
        epochs = list(corpus_stats["epoch_vocab_size"].keys())
        vocab_sizes = list(corpus_stats["epoch_vocab_size"].values())
        token_counts = list(corpus_stats["epoch_total_tokens"].values())
        short_epochs = [e.split()[0] + " " + e.split()[1] for e in epochs]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

        # Panel 1: Total Tokens
        bars1 = ax1.bar(short_epochs, token_counts, color="#1E3A8A", alpha=0.85, edgecolor="#0F172A", width=0.55)
        ax1.set_title("Total Token Volume per Epoch", fontweight="bold", pad=12)
        ax1.set_ylabel("Total Lemmatized Tokens")
        ax1.set_ylim(0, max(token_counts) * 1.15)
        for bar in bars1:
            h = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., h + 500, f"{int(h):,}", ha="center", va="bottom", fontsize=9, fontweight="bold")

        # Panel 2: Vocabulary Size
        bars2 = ax2.bar(short_epochs, vocab_sizes, color="#0D9488", alpha=0.85, edgecolor="#0F172A", width=0.55)
        ax2.set_title("Unique Vocabulary Size (Types) per Epoch", fontweight="bold", pad=12)
        ax2.set_ylabel("Unique Types (Lemmas)")
        ax2.set_ylim(0, max(vocab_sizes) * 1.15)
        for bar in bars2:
            h = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., h + 100, f"{int(h):,}", ha="center", va="bottom", fontsize=9, fontweight="bold")

        plt.tight_layout()
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, bbox_inches="tight")
        plt.close()
        return filepath

    def plot_emergent_vs_decaying(self, df_trends: pd.DataFrame, top_k: int = 12, filename: str = "fig2_emergent_vs_decaying_lexicon.png"):
        """Fig 2: Diverging bar chart showing emergent vs decaying terminology."""
        emergent = df_trends[df_trends["emergence_index"] > 0].head(top_k)
        decaying = df_trends[df_trends["emergence_index"] < 0].tail(top_k).iloc[::-1]

        combined = pd.concat([emergent, decaying]).sort_values(by="emergence_index", ascending=True)

        fig, ax = plt.subplots(figsize=(12, 8))
        colors = ["#BE123C" if val < 0 else "#047857" for val in combined["emergence_index"]]

        y_positions = np.arange(len(combined))
        bars = ax.barh(y_positions, combined["emergence_index"], color=colors, alpha=0.88, edgecolor="#111827", height=0.65)
        ax.set_yticks(y_positions)
        ax.set_yticklabels(combined["term"], fontsize=10, fontweight="semibold")
        ax.axvline(0, color="#111827", linewidth=1.2, linestyle="--")

        ax.set_title("Lexical Paradigm Shift: Emergent vs. Decaying NLP Terminology\n($Log_2$ Normalized Emergence Index: Epoch 4 vs. Epoch 1)", fontweight="bold", pad=15)
        ax.set_xlabel("Emergence Index ($Log_2$ Growth Ratio)", fontweight="bold")

        # Annotations
        for bar, val in zip(bars, combined["emergence_index"]):
            offset = 0.15 if val >= 0 else -0.15
            ha = "left" if val >= 0 else "right"
            ax.text(val + offset, bar.get_y() + bar.get_height()/2., f"{val:+.2f}", ha=ha, va="center", fontsize=9, fontweight="bold")

        # Custom legend handles
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor="#047857", edgecolor="#111827", label="Emergent Lexicon (Epoch 4 Surge)"),
            Patch(facecolor="#BE123C", edgecolor="#111827", label="Decaying Lexicon (Epoch 1 Obsolescence)")
        ]
        ax.legend(handles=legend_elements, loc="lower right", frameon=True)

        plt.tight_layout()
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, bbox_inches="tight")
        plt.close()
        return filepath

    def plot_keyword_trajectories(self, df_trajectories: pd.DataFrame, filename: str = "fig3_target_keywords_trajectories.png"):
        """Fig 3: Longitudinal multi-line trends of core paradigm keywords."""
        fig, ax = plt.subplots(figsize=(12, 6))

        palette = {
            "prompt": "#E11D48",
            "llm": "#7C3AED",
            "transformer": "#2563EB",
            "lstm": "#DC2626",
            "reasoning": "#059669",
            "hallucination": "#D97706",
            "agent": "#0891B2",
            "parsing": "#64748B"
        }

        # Filter keywords present
        keywords = [k for k in df_trajectories["keyword"].unique() if k in palette]

        for kw in keywords:
            sub = df_trajectories[df_trajectories["keyword"] == kw]
            short_epochs = [e.split()[0] + " " + e.split()[1] for e in sub["epoch"]]
            ax.plot(
                short_epochs,
                sub["norm_freq_per_10k"],
                marker="o",
                linewidth=2.5,
                markersize=7,
                label=kw.upper(),
                color=palette.get(kw, "#334155")
            )

        ax.set_title("Longitudinal Frequency Trajectories of Paradigm Keywords (2018-2025)", fontweight="bold", pad=15)
        ax.set_ylabel("Normalized Frequency (per 10,000 Tokens)", fontweight="bold")
        ax.set_xlabel("Epoch", fontweight="bold")
        ax.legend(title="Keyword Marker", bbox_to_anchor=(1.02, 1), loc="upper left", frameon=True)

        plt.tight_layout()
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, bbox_inches="tight")
        plt.close()
        return filepath

    def plot_top_bigrams(self, epoch_bigrams: dict, top_k: int = 8, filename: str = "fig4_top_bigrams_per_epoch.png"):
        """Fig 4: 2x2 grid of horizontal bar charts showing top collocations per epoch."""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        axes = axes.flatten()
        epochs = list(epoch_bigrams.keys())
        colors = ["#1E3A8A", "#0D9488", "#7C3AED", "#BE123C"]

        for idx, (epoch, ax) in enumerate(zip(epochs, axes)):
            bg_counter = epoch_bigrams[epoch]
            top_bgs = bg_counter.most_common(top_k)
            labels = [b[0].replace("_", " ") for b in top_bgs][::-1]
            vals = [b[1] for b in top_bgs][::-1]

            bars = ax.barh(labels, vals, color=colors[idx], alpha=0.85, edgecolor="#0F172A", height=0.6)
            ax.set_title(f"{epoch} - Signature Collocations", fontweight="bold", fontsize=11)
            ax.set_xlabel("Frequency Count")
            for bar in bars:
                w = bar.get_width()
                ax.text(w + max(vals)*0.01, bar.get_y() + bar.get_height()/2., f"{int(w)}", va="center", fontsize=8, fontweight="bold")

        plt.suptitle("Evolution of High-Frequency Collocations Across Scientific Epochs", fontweight="bold", fontsize=14, y=1.02)
        plt.tight_layout()
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, bbox_inches="tight")
        plt.close()
        return filepath

    def plot_topic_coherence_sweep(self, sweep_df: pd.DataFrame, filename: str = "fig5_topic_coherence_sweep.png"):
        """Fig 5: Dual-axis plot of Topic Coherence vs k for LDA and NMF."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

        # Panel 1: Coherence
        ax1.plot(sweep_df["k"], sweep_df["nmf_coherence"], marker="s", linewidth=2.5, color="#0D9488", label="NMF (UMass Coherence)")
        ax1.plot(sweep_df["k"], sweep_df["lda_coherence"], marker="o", linewidth=2.5, color="#2563EB", label="LDA (UMass Coherence)")
        ax1.set_title("Topic Coherence ($C_{UMass}$) across Topic Numbers ($k$)", fontweight="bold")
        ax1.set_xlabel("Number of Topics ($k$)")
        ax1.set_ylabel("UMass Coherence (Higher is Better)")
        ax1.legend(frameon=True)

        # Panel 2: LDA Perplexity vs NMF Reconstruction Error
        ax2.plot(sweep_df["k"], sweep_df["nmf_reconstruction_err"], marker="^", linewidth=2, color="#E11D48", label="NMF Reconstruction Error")
        ax2.set_title("Model Fit Metrics across $k$", fontweight="bold")
        ax2.set_xlabel("Number of Topics ($k$)")
        ax2.set_ylabel("NMF Reconstruction Error", color="#E11D48")
        ax2.tick_params(axis="y", labelcolor="#E11D48")

        ax2_twin = ax2.twinx()
        ax2_twin.plot(sweep_df["k"], sweep_df["lda_perplexity"], marker="d", linewidth=2, color="#7C3AED", linestyle="--", label="LDA Perplexity")
        ax2_twin.set_ylabel("LDA Perplexity", color="#7C3AED")
        ax2_twin.tick_params(axis="y", labelcolor="#7C3AED")

        plt.tight_layout()
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, bbox_inches="tight")
        plt.close()
        return filepath

    def plot_topic_streamgraph(self, epoch_topic_df: pd.DataFrame, topic_labels: dict, filename: str = "fig6_topic_evolution_streamgraph.png"):
        """Fig 6: Stacked area / streamgraph showing topic proportion shifts over epochs."""
        fig, ax = plt.subplots(figsize=(13, 7))

        short_epochs = [e.split()[0] + " " + e.split()[1] for e in epoch_topic_df["epoch"]]
        topic_cols = [c for c in epoch_topic_df.columns if c.startswith("Topic_") or c in topic_labels.values()]

        # Prepare 100% normalized stacked data
        data_matrix = epoch_topic_df[topic_cols].values
        norm_matrix = (data_matrix / data_matrix.sum(axis=1, keepdims=True)) * 100.0

        colors = ["#1E3A8A", "#0284C7", "#0D9488", "#16A34A", "#D97706", "#EA580C", "#DC2626", "#7C3AED"]

        labels = [topic_labels.get(c, c) for c in topic_cols]
        ax.stackplot(short_epochs, norm_matrix.T, labels=labels, colors=colors[:len(topic_cols)], alpha=0.88, edgecolor="white", linewidth=0.5)

        ax.set_title("Dynamic Topic Evolution in NLP Research Discourse (2018-2025)", fontweight="bold", pad=15)
        ax.set_ylabel("Relative Topic Prevalence (%)", fontweight="bold")
        ax.set_xlabel("Research Epoch", fontweight="bold")
        ax.set_ylim(0, 100)
        ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5), frameon=True, title="Latent Research Topics")

        plt.tight_layout()
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, bbox_inches="tight")
        plt.close()
        return filepath

    def plot_topic_heatmap(self, epoch_topic_df: pd.DataFrame, topic_labels: dict, filename: str = "fig7_topic_epoch_intensity_heatmap.png"):
        """Fig 7: Annotated heatmap of topic intensity across epochs."""
        fig, ax = plt.subplots(figsize=(11, 7))

        short_epochs = [e.split()[0] + " " + e.split()[1] for e in epoch_topic_df["epoch"]]
        topic_cols = [c for c in epoch_topic_df.columns if c.startswith("Topic_") or c in topic_labels.values()]

        mat = epoch_topic_df[topic_cols].values
        # Relative percentage per epoch
        mat_pct = (mat / mat.sum(axis=1, keepdims=True)) * 100.0
        ylabels = [topic_labels.get(c, c) for c in topic_cols]

        sns.heatmap(
            mat_pct.T,
            annot=True,
            fmt=".1f",
            cmap="YlGnBu",
            xticklabels=short_epochs,
            yticklabels=ylabels,
            cbar_kws={"label": "Prevalence (%)"},
            linewidths=0.5,
            ax=ax
        )

        ax.set_title("Topic Intensity Matrix Across Longitudinal Epochs (% Composition)", fontweight="bold", pad=15)
        ax.set_xlabel("Epoch", fontweight="bold")
        ax.set_ylabel("Research Topic", fontweight="bold")

        plt.tight_layout()
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, bbox_inches="tight")
        plt.close()
        return filepath

    def plot_semantic_clustering(self, proj_df: pd.DataFrame, cluster_names: dict, filename: str = "fig8_semantic_clustering_lsa.png"):
        """Fig 8: 2D LSA projection scatter plot colored by cluster and styled by epoch."""
        fig, ax = plt.subplots(figsize=(13, 8))

        # Assign cluster names
        proj_df["cluster_label"] = proj_df["cluster"].map(lambda c: cluster_names.get(f"Cluster_{c}", f"Cluster {c}"))
        palette = ["#2563EB", "#0D9488", "#D97706", "#DC2626", "#7C3AED", "#475569"]

        sns.scatterplot(
            data=proj_df,
            x="svd_1",
            y="svd_2",
            hue="cluster_label",
            style="epoch",
            palette=palette[:proj_df["cluster"].nunique()],
            alpha=0.65,
            s=45,
            ax=ax
        )

        ax.set_title("Latent Semantic Geometry: Document Clustering & Diachronic Distribution\n(TruncatedSVD 2D Projection of TF-IDF Space)", fontweight="bold", pad=15)
        ax.set_xlabel("LSA Dimension 1 (General Linguistic Architecture)")
        ax.set_ylabel("LSA Dimension 2 (Task Specificity & Generative Paradigm)")
        ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", frameon=True)

        plt.tight_layout()
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, bbox_inches="tight")
        plt.close()
        return filepath

    def plot_cluster_epoch_migration(self, crosstab_df: pd.DataFrame, cluster_names: dict, filename: str = "fig9_cluster_epoch_shift_stacked.png"):
        """Fig 9: 100% stacked bar chart of cluster proportions by epoch."""
        fig, ax = plt.subplots(figsize=(12, 6))

        short_epochs = [e.split()[0] + " " + e.split()[1] for e in crosstab_df.index]
        colors = ["#1E3A8A", "#0D9488", "#F59E0B", "#DC2626", "#7C3AED"]

        col_labels = [cluster_names.get(f"Cluster_{c}", f"Cluster {c}") for c in crosstab_df.columns]

        bottom = np.zeros(len(crosstab_df))
        for idx, col in enumerate(crosstab_df.columns):
            vals = crosstab_df[col].values
            ax.bar(short_epochs, vals, bottom=bottom, label=col_labels[idx], color=colors[idx % len(colors)], width=0.55, edgecolor="#0F172A")
            # Annotate percentage if significant
            for i, (v, b) in enumerate(zip(vals, bottom)):
                if v > 10.0:
                    ax.text(i, b + v/2., f"{v:.1f}%", ha="center", va="center", color="white", fontweight="bold", fontsize=9)
            bottom += vals

        ax.set_title("Cluster Share Evolution Across Epochs (% of Papers per Epoch)", fontweight="bold", pad=15)
        ax.set_ylabel("Epoch Share (%)", fontweight="bold")
        ax.set_xlabel("Epoch", fontweight="bold")
        ax.set_ylim(0, 100)
        ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", frameon=True, title="Research Clusters")

        plt.tight_layout()
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, bbox_inches="tight")
        plt.close()
        return filepath

    def plot_linguistic_complexity_dashboard(self, df_metrics: pd.DataFrame, filename: str = "fig10_linguistic_complexity_dashboard.png"):
        """Fig 10: 4-panel dashboard of readability, lexical diversity, sentence length, and stance."""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        short_epochs = [e.split()[0] + " " + e.split()[1] for e in sorted(df_metrics["epoch"].unique())]

        epoch_means = df_metrics.groupby("epoch").mean(numeric_only=True).loc[sorted(df_metrics["epoch"].unique())]

        # Panel 1: Readability (Flesch-Kincaid Grade Level vs Reading Ease)
        ax1 = axes[0, 0]
        ax1.plot(short_epochs, epoch_means["fk_grade_level"], marker="o", color="#BE123C", linewidth=2.5, label="Flesch-Kincaid Grade Level")
        ax1.set_title("Readability & Syntactic Difficulty", fontweight="bold")
        ax1.set_ylabel("Grade Level (FKGL)", color="#BE123C")
        ax1.tick_params(axis="y", labelcolor="#BE123C")

        ax1_twin = ax1.twinx()
        ax1_twin.plot(short_epochs, epoch_means["flesch_reading_ease"], marker="s", color="#1E3A8A", linewidth=2.5, linestyle="--", label="Flesch Reading Ease")
        ax1_twin.set_ylabel("Reading Ease (FRE)", color="#1E3A8A")
        ax1_twin.tick_params(axis="y", labelcolor="#1E3A8A")

        # Panel 2: Lexical Diversity (TTR & Maas Index)
        ax2 = axes[0, 1]
        ax2.plot(short_epochs, epoch_means["ttr"], marker="^", color="#0D9488", linewidth=2.5, label="Type-Token Ratio (TTR)")
        ax2.set_title("Lexical Diversity (Type-Token Ratio)", fontweight="bold")
        ax2.set_ylabel("TTR (Mean)", color="#0D9488")
        ax2.tick_params(axis="y", labelcolor="#0D9488")

        # Panel 3: Structural Lengths (Avg Sentence Length & Word Length)
        ax3 = axes[1, 0]
        ax3.bar(short_epochs, epoch_means["avg_sentence_len"], color="#475569", alpha=0.85, width=0.5, edgecolor="#0F172A")
        ax3.set_title("Average Sentence Length (Words per Sentence)", fontweight="bold")
        ax3.set_ylabel("Words / Sentence")
        for i, v in enumerate(epoch_means["avg_sentence_len"]):
            ax3.text(i, v + 0.3, f"{v:.1f}", ha="center", va="bottom", fontweight="bold", fontsize=9)

        # Panel 4: Pragmatic Stance (Booster-to-Hedge Ratio)
        ax4 = axes[1, 1]
        ax4.plot(short_epochs, epoch_means["booster_hedge_ratio"], marker="D", color="#EA580C", linewidth=2.8, markersize=8)
        ax4.set_title("Epistemic Stance Shift: Booster / Hedge Ratio\n(Rhetorical Certainty vs. Scientific Hedging)", fontweight="bold")
        ax4.set_ylabel("Ratio ($Boosters / Hedges$)")
        for i, v in enumerate(epoch_means["booster_hedge_ratio"]):
            ax4.text(i, v + 0.02, f"{v:.3f}", ha="center", va="bottom", fontweight="bold", fontsize=9)

        plt.tight_layout()
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, bbox_inches="tight")
        plt.close()
        return filepath

    def plot_epoch_wordclouds(self, epoch_unigrams: dict, filename: str = "fig11_epoch_wordclouds.png"):
        """Fig 11: 2x2 grid of Word Clouds representing lexical density per epoch."""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        axes = axes.flatten()
        cmaps = ["Blues", "Greens", "Purples", "Oranges"]

        for idx, (epoch, ax) in enumerate(zip(epoch_unigrams.keys(), axes)):
            word_counts = epoch_unigrams[epoch]
            wc = WordCloud(
                width=800,
                height=500,
                background_color="white",
                colormap=cmaps[idx],
                max_words=80,
                random_state=42
            ).generate_from_frequencies(word_counts)

            ax.imshow(wc, interpolation="bilinear")
            ax.set_title(f"Lexical Landscape: {epoch}", fontweight="bold", fontsize=14, pad=10)
            ax.axis("off")

        plt.tight_layout()
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, bbox_inches="tight")
        plt.close()
        return filepath

if __name__ == "__main__":
    pass
