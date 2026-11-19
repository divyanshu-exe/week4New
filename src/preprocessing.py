"""
Preprocessing Module for NLP Language Trends Analysis.
Implements domain-aware text cleaning, POS-tagged lemmatization,
academic boilerplate filtering, and n-gram extraction.
"""

import re
import string
import unicodedata
import nltk
from nltk.corpus import stopwords, wordnet
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
import pandas as pd

# Academic boilerplate stopwords that dilute scientific domain topics
ACADEMIC_STOPWORDS = {
    "paper", "propose", "method", "model", "approach", "result", "present",
    "study", "show", "demonstrate", "based", "using", "task", "dataset",
    "performance", "experiment", "evaluation", "compare", "benchmark",
    "achieve", "improve", "state", "art", "also", "well", "one", "two",
    "work", "new", "novel", "existing", "different", "provide", "apply",
    "system", "framework", "analysis", "find", "use", "used", "via",
    "conduct", "various", "address", "investigate", "explore", "outperform",
    "furthermore", "however", "moreover", "therefore", "thus", "overall",
    "significantly", "effective", "effectively", "table", "figure", "section"
}

def get_wordnet_pos(nltk_tag):
    """Maps NLTK POS tag to WordNet POS tag."""
    if nltk_tag.startswith('J'):
        return wordnet.ADJ
    elif nltk_tag.startswith('V'):
        return wordnet.VERB
    elif nltk_tag.startswith('N'):
        return wordnet.NOUN
    elif nltk_tag.startswith('R'):
        return wordnet.ADV
    else:
        return wordnet.NOUN

class NLPPreprocessor:
    def __init__(self, remove_academic_stopwords: bool = True, min_word_len: int = 3):
        self.min_word_len = min_word_len
        self.lemmatizer = WordNetLemmatizer()
        
        # Build comprehensive stopword list
        base_stops = set(stopwords.words("english"))
        self.stopwords = base_stops.union(ACADEMIC_STOPWORDS if remove_academic_stopwords else set())
        
        # Regex patterns for scientific texts
        self.re_latex = re.compile(r"\$[^$]+\$|\\[a-zA-Z]+(\{[^}]*\})?")
        self.re_urls = re.compile(r"https?://\S+|www\.\S+")
        self.re_nums = re.compile(r"\b\d+([.,]\d+)*\b")
        self.re_punct = re.compile(r"[^\w\s-]")
        self.re_whitespace = re.compile(r"\s+")

    def clean_text(self, text: str) -> str:
        """Strips LaTeX, URLs, special punctuation, and normalizes casing."""
        if not isinstance(text, str):
            return ""
        # Normalize unicode
        text = unicodedata.normalize("NFKD", text)
        # Strip URLs
        text = self.re_urls.sub(" ", text)
        # Strip LaTeX formulas & tags
        text = self.re_latex.sub(" ", text)
        # Strip pure numeric literals
        text = self.re_nums.sub(" ", text)
        # Strip non-alphanumeric punctuation except hyphens inside words
        text = self.re_punct.sub(" ", text)
        # Replace multiple spaces/newlines
        text = self.re_whitespace.sub(" ", text).strip().lower()
        return text

    def tokenize_and_lemmatize(self, text: str, return_pos: bool = False) -> list[str]:
        """Cleans, tokenizes, POS-tags, and lemmatizes text into filtered lemmas."""
        cleaned = self.clean_text(text)
        if not cleaned:
            return []

        tokens = word_tokenize(cleaned)
        if not tokens:
            return []

        pos_tags = nltk.pos_tag(tokens)
        lemmas = []

        for word, tag in pos_tags:
            # Strip trailing/leading hyphens
            word = word.strip("-_")
            if len(word) < self.min_word_len:
                continue
            if word in self.stopwords:
                continue
            if not word.replace("-", "").isalpha():
                continue

            wn_pos = get_wordnet_pos(tag)
            lemma = self.lemmatizer.lemmatize(word, pos=wn_pos)
            
            if lemma in self.stopwords or len(lemma) < self.min_word_len:
                continue

            lemmas.append(lemma)

        return lemmas

    def extract_bigrams(self, tokens: list[str]) -> list[str]:
        """Extracts adjacent bigrams from a list of clean tokens."""
        bigrams = []
        for i in range(len(tokens) - 1):
            w1, w2 = tokens[i], tokens[i + 1]
            if w1 not in self.stopwords and w2 not in self.stopwords:
                bigrams.append(f"{w1}_{w2}")
        return bigrams

    def preprocess_series(self, text_series: pd.Series) -> pd.DataFrame:
        """Processes a pandas Series of abstracts into clean tokens and n-grams."""
        cleaned_texts = text_series.apply(self.clean_text)
        token_lists = cleaned_texts.apply(self.tokenize_and_lemmatize)
        bigram_lists = token_lists.apply(self.extract_bigrams)
        token_strings = token_lists.apply(lambda toks: " ".join(toks))
        
        result_df = pd.DataFrame({
            "cleaned_text": cleaned_texts,
            "tokens": token_lists,
            "bigrams": bigram_lists,
            "token_str": token_strings,
            "token_count": token_lists.apply(len)
        })
        return result_df

if __name__ == "__main__":
    sample = "In this paper, we propose a novel transformer-based framework for sentiment analysis ($F_1 = 92.4\\%$). http://arxiv.org"
    prep = NLPPreprocessor()
    print("Sample:", sample)
    print("Cleaned:", prep.clean_text(sample))
    print("Lemmas:", prep.tokenize_and_lemmatize(sample))
    print("Bigrams:", prep.extract_bigrams(prep.tokenize_and_lemmatize(sample)))
