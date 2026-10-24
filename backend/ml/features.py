"""Sentence-embedding features for the clause classifier.

A small pretrained model (BAAI/bge-base-en-v1.5) turns each sentence into 768 numbers that capture
its meaning, so "how long we keep your data" and "retention period" end up close together even
though they share no words. We combine these with the TF-IDF word/character features in train.py.

The embedding model is downloaded once (~440 MB) and cached by Hugging Face. It is NOT saved inside
our .joblib file; it is reloaded by name when needed.
"""
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.base import BaseEstimator, TransformerMixin

EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"

_models = {}
_cache = {}  # sentence -> vector, so cross-validation doesn't re-encode the same sentences


def _encoder(name):
    if name not in _models:
        from sentence_transformers import SentenceTransformer  # slow import, only when needed
        _models[name] = SentenceTransformer(name)
    return _models[name]


class SentenceEmbeddings(BaseEstimator, TransformerMixin):
    def __init__(self, model_name=EMBEDDING_MODEL, weight=2.0):
        self.model_name = model_name
        self.weight = weight  # embeddings count double compared with the TF-IDF features (tuned by CV)

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        sentences = list(X)
        todo = [s for s in dict.fromkeys(sentences) if (self.model_name, s) not in _cache]
        if todo:
            vectors = _encoder(self.model_name).encode(todo, normalize_embeddings=True, show_progress_bar=False)
            for s, v in zip(todo, vectors):
                _cache[(self.model_name, s)] = v
        return csr_matrix(np.array([_cache[(self.model_name, s)] for s in sentences]) * self.weight)
