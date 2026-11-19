"""
Linguistic Complexity, Readability, and Epistemic Stance Analysis Module.
Measures lexical diversity (TTR, Guiraud, Maas), readability (Flesch-Kincaid, Coleman-Liau),
and rhetorical stance markers (hedges, boosters, sentiment polarity).
"""

import math
import re
import numpy as np
import pandas as pd
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Pragmatic Stance Lexicons (Hyland's Academic Metadiscourse Framework)
HEDGES = {
    "suggest", "suggests", "suggested", "suggesting",
    "indicate", "indicates", "indicated", "indicating",
    "may", "might", "could", "would",
    "likely", "unlikely", "possible", "possibly", "potential", "potentially",
    "preliminary", "hypothesize", "hypothesized", "seem", "seems", "seemed",
    "appear", "appears", "appeared", "tend", "tends", "tended",
    "partially", "somewhat", "perhaps", "presumably", "conceivably"
}

BOOSTERS = {
    "clearly", "definitely", "demonstrates", "demonstrated", "proves", "proved",
    "crucial", "essential", "vital", "undoubtedly", "unprecedented",
    "superior", "dominant", "revolutionize", "revolutionizes", "breakthrough",
    "dramatic", "dramatically", "state-of-the-art", "sota", "remarkable",
    "exceptional", "flawless", "outperform", "outperforms", "outperformed"
}

def count_syllables_in_word(word: str) -> int:
    """Estimates syllable count using heuristic vowel cluster regex."""
    w = word.lower()
    w = re.sub(r"[^a-z]", "", w)
    if not w:
        return 0
    if len(w) <= 3:
        return 1
    # Count vowel groups
    vowels = "aeiouy"
    count = 0
    prev_is_vowel = False
    for char in w:
        is_vowel = char in vowels
        if is_vowel and not prev_is_vowel:
            count += 1
        prev_is_vowel = is_vowel
    # Adjust trailing 'e'
    if w.endswith("e") and not w.endswith("le") and count > 1:
        count -= 1
    return max(1, count)

class LinguisticComplexityAnalyzer:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.vader = SentimentIntensityAnalyzer()

    def analyze_document(self, text: str, tokens: list[str]) -> dict:
        """Calculates diversity, readability, stance, and sentiment for a single document."""
        if not text or not tokens:
            return {
                "ttr": 0.0, "guiraud_r": 0.0, "maas_index": 0.0,
                "flesch_reading_ease": 0.0, "fk_grade_level": 0.0,
                "coleman_liau": 0.0, "hedge_count": 0, "booster_count": 0,
                "booster_hedge_ratio": 0.0, "sentiment_compound": 0.0
            }

        # Sentences
        sentences = [s.strip() for s in re.split(r"[.!?]+", text) if len(s.strip()) > 5]
        num_sentences = max(1, len(sentences))

        # Words (alphanumeric)
        raw_words = [w.lower() for w in re.findall(r"\b[a-zA-Z-]+\b", text)]
        num_words = max(1, len(raw_words))
        num_chars = sum(len(w) for w in raw_words)

        # 1. Lexical Diversity on cleaned tokens
        N = max(1, len(tokens))
        V = len(set(tokens))
        ttr = V / N
        guiraud_r = V / math.sqrt(N)
        maas_index = (math.log(N) - math.log(V)) / (math.log(N) ** 2) if N > 1 and V > 1 else 0.0

        # 2. Syllables & Readability
        num_syllables = sum(count_syllables_in_word(w) for w in raw_words)
        asl = num_words / num_sentences
        asw = num_syllables / num_words

        # Flesch Reading Ease
        fre = 206.835 - (1.015 * asl) - (84.6 * asw)
        # Flesch-Kincaid Grade Level
        fkgl = (0.39 * asl) + (11.8 * asw) - 15.59
        # Coleman-Liau Index (L = avg letters per 100 words, S = avg sentences per 100 words)
        L = (num_chars / num_words) * 100.0
        S = (num_sentences / num_words) * 100.0
        cli = (0.0588 * L) - (0.296 * S) - 15.8

        # 3. Epistemic Stance Markers
        hedge_c = sum(1 for w in raw_words if w in HEDGES)
        booster_c = sum(1 for w in raw_words if w in BOOSTERS)
        norm_hedges = (hedge_c / num_words) * 1000.0
        norm_boosters = (booster_c / num_words) * 1000.0
        stance_ratio = (booster_c + 0.1) / (hedge_c + 0.1)

        # 4. Sentiment Polarity
        polarity = self.vader.polarity_scores(text)["compound"]

        return {
            "num_words": num_words,
            "num_sentences": num_sentences,
            "avg_sentence_len": round(asl, 2),
            "ttr": round(ttr, 4),
            "guiraud_r": round(guiraud_r, 3),
            "maas_index": round(maas_index, 4),
            "flesch_reading_ease": round(fre, 2),
            "fk_grade_level": round(fkgl, 2),
            "coleman_liau": round(cli, 2),
            "hedges_per_1k": round(norm_hedges, 2),
            "boosters_per_1k": round(norm_boosters, 2),
            "booster_hedge_ratio": round(stance_ratio, 3),
            "sentiment_compound": round(polarity, 4)
        }

    def compute_corpus_complexity(self) -> pd.DataFrame:
        """Computes metrics across all documents in corpus."""
        records = []
        for _, row in self.df.iterrows():
            metrics = self.analyze_document(row["abstract"], row["tokens"])
            records.append(metrics)

        metrics_df = pd.DataFrame(records)
        combined_df = pd.concat([self.df, metrics_df], axis=1)
        return combined_df

    def compute_epoch_summary(self, combined_df: pd.DataFrame) -> pd.DataFrame:
        """Aggregates complexity metrics by epoch."""
        metric_cols = [
            "avg_sentence_len", "ttr", "guiraud_r", "maas_index",
            "flesch_reading_ease", "fk_grade_level", "coleman_liau",
            "hedges_per_1k", "boosters_per_1k", "booster_hedge_ratio", "sentiment_compound"
        ]
        epoch_agg = combined_df.groupby("epoch")[metric_cols].agg(["mean", "std"]).round(3)
        return epoch_agg

if __name__ == "__main__":
    pass
