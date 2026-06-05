import json
from typing import Dict, Optional
from pathlib import Path
from collections import Counter
import logging
import os

logger = logging.getLogger(__name__)


class CorpusManager:
    """
    Gestisce il corpus di riferimento italiano per le frequenze di n-grammi.

    Priorità:
    1. JSON custom (già pronto)
    2. Wikipedia/OPUS .tok (build n-grammi)
    3. fallback statico
    """

    ITALIAN_UNIGRAM_FREQUENCIES = {
        "il": 0.087,
        "di": 0.063,
        "è": 0.058,
        "a": 0.041,
        "e": 0.036,
        "che": 0.033,
        "in": 0.032,
        "per": 0.027,
        "non": 0.025,
    }

    ITALIAN_BIGRAM_FREQUENCIES = {
        "il ristorante": 0.0035,
        "il cibo": 0.0028,
        "è buono": 0.0022,
        "molto bene": 0.0015,
    }

    ITALIAN_TRIGRAM_FREQUENCIES = {
        "il ristorante è": 0.0008,
        "il cibo è": 0.0007,
        "è molto buono": 0.0004,
    }

    # -------------------------
    # INIT
    # -------------------------

    def __init__(
        self,
        corpus_json_path: Optional[str] = None,
        tok_path: Optional[str] = None,
    ):
        self.bigram_freq = self.ITALIAN_BIGRAM_FREQUENCIES.copy()
        self.trigram_freq = self.ITALIAN_TRIGRAM_FREQUENCIES.copy()
        self.unigram_freq = self.ITALIAN_UNIGRAM_FREQUENCIES.copy()

        cache_dir = Path(
            os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")
        ) / "trustable"

        self.cache_path = cache_dir / "wiki-it.json"

        if corpus_json_path and Path(corpus_json_path).exists():
            self._load_json(corpus_json_path)
            return

        if self.cache_path and self.cache_path.exists():
            self._load_json(str(self.cache_path))
            return
            
        if tok_path and Path(tok_path).exists():
            self._build_from_tok(tok_path)


    # -------------------------
    # LOAD JSON
    # -------------------------

    def _load_json(self, path: str):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.unigram_freq.update(data.get("unigrams", {}))
            self.bigram_freq.update(data.get("bigrams", {}))
            self.trigram_freq.update(data.get("trigrams", {}))

            logger.info(f"Loaded corpus from JSON: {path}")

        except Exception as e:
            logger.warning(f"Failed loading JSON corpus: {e}")

    # -------------------------
    # BUILD FROM .TOK
    # -------------------------

    def _build_from_tok(self, tok_path: str):
        """
        Costruisce n-grammi da file .tok (già tokenizzato)
        """

        uni = Counter()
        bi = Counter()
        tri = Counter()

        logger.info(f"Building n-grams from .tok: {tok_path}")

        with open(tok_path, "r", encoding="utf-8") as f:
            for line in f:
                tokens = line.lower().strip().split()

                if len(tokens) == 0:
                    continue

                uni.update(tokens)

                bi.update(
                    " ".join(x)
                    for x in zip(tokens, tokens[1:])
                )

                tri.update(
                    " ".join(x)
                    for x in zip(tokens, tokens[1:], tokens[2:])
                )

        total_uni = sum(uni.values())

        self.unigram_freq = {
            k: v / total_uni for k, v in uni.items()
        }

        total_bi = sum(bi.values())
        self.bigram_freq = {
            k: v / total_bi for k, v in bi.items()
        }

        total_tri = sum(tri.values())
        self.trigram_freq = {
            k: v / total_tri for k, v in tri.items()
        }

        if self.cache_path:
            self._save_cache()

    # -------------------------
    # CACHE
    # -------------------------

    def _save_cache(self):
        try:
            data = {
                "unigrams": self.unigram_freq,
                "bigrams": self.bigram_freq,
                "trigrams": self.trigram_freq,
                "source": "auto-built from .tok (OPUS/Wikipedia)"
            }

            if self.cache_path:
                self.cache_path.parent.mkdir(parents=True, exist_ok=True)

                with open(self.cache_path, "w", encoding="utf-8") as f:
                    json.dump(data, f)

                logger.info(f"Saved cache to {self.cache_path}")

        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")


    def get_ngram_frequency(self, ngram: str, n: int) -> float:
        ngram = ngram.lower().strip()

        if n == 1:
            return self.unigram_freq.get(ngram, 0.0001)
        if n == 2:
            return self.bigram_freq.get(ngram, 0.00001)
        if n == 3:
            return self.trigram_freq.get(ngram, 0.000001)

        return 0.0
    
    def estimate_probability_from_unigrams(self, ngram: str) -> float:
        """
        Stima la probabilità di un n-gramma dalla probabilità dei singoli termini
        (semplice prodotto). Usato come fallback.
        
        Args:
            ngram: L'n-gramma
        
        Returns:
            Probabilità stimata
        """
        words = ngram.lower().split()
        prob = 1.0
        for word in words:
            prob *= self.unigram_freq.get(word, 0.00001)
        return prob
    
    @staticmethod
    def create_default_corpus() -> Dict:
        """
        Crea un corpus JSON di default che può essere salvato e riutilizzato.
        """
        return {
            "bigrams": CorpusManager.ITALIAN_BIGRAM_FREQUENCIES,
            "trigrams": CorpusManager.ITALIAN_TRIGRAM_FREQUENCIES,
            "unigrams": CorpusManager.ITALIAN_UNIGRAM_FREQUENCIES,
            "source": "OPUS-based Italian corpus (estimated)",
            "note": "Minimal reference corpus for anomaly detection"
        }