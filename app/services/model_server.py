"""
Model Server
============
Wraps the trained intent model (models/intent_model.pkl) and any
future fine-tuned models behind a clean service interface.

All pipeline code should call predict_intent() from here rather than
loading the .pkl directly, so the model is loaded once at startup and
swapped out in one place when a fine-tuned model is ready.

Fallback:
  If the pickle model is unavailable or fails to load, the server
  automatically falls back to the keyword-based IntentDetector so the
  API keeps working during development.
"""

import os
import logging
from pathlib import Path

import joblib

from app.core.intent_detector import IntentDetector

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).parents[2]
INTENT_MODEL_PATH = ROOT / "models" / "intent_model.pkl"


# ---------------------------------------------------------------------------
# Model loader
# ---------------------------------------------------------------------------

class ModelServer:
    """
    Singleton-style service that loads the ML model once and exposes
    a predict() method for intent classification.
    """

    def __init__(self):
        self._model = None          # sklearn / pickle model
        self._vectorizer = None     # optional fitted vectorizer
        self._fallback = IntentDetector()
        self._using_fallback = True
        self._load()

    def _load(self):
        """Attempt to load the pickle model. Fall back silently if missing."""

        if not INTENT_MODEL_PATH.exists():
            logger.warning(
                "Intent model not found at %s — using keyword fallback.",
                INTENT_MODEL_PATH,
            )
            return

        try:
            payload = joblib.load(INTENT_MODEL_PATH)

            # Support two save formats:
            #   Format A: plain sklearn Pipeline  (model.predict([text]))
            #   Format B: dict {"model": ..., "vectorizer": ...}
            if isinstance(payload, dict):
                self._model = payload.get("model")
                self._vectorizer = payload.get("vectorizer")
            else:
                self._model = payload

            self._using_fallback = False
            logger.info("Intent model loaded from %s", INTENT_MODEL_PATH)

        except Exception as exc:
            logger.error(
                "Failed to load intent model: %s — using keyword fallback.", exc
            )

    def predict_intent(self, text: str) -> str:
        """
        Predict the intent label for the given text.

        Args:
            text: Normalized instruction string.

        Returns:
            Intent label string, e.g. "ADD_CUSTOMER".
        """

        if self._using_fallback or self._model is None:
            return self._fallback.detect_intent(text)

        try:
            # sklearn Pipeline already includes vectorizer — no separate step needed
            features = [text]
            if self._vectorizer is not None:
                features = self._vectorizer.transform([text])

            prediction = self._model.predict(features)
            return str(prediction[0])

        except Exception as exc:
            logger.error("Model prediction failed: %s — using fallback.", exc)
            return self._fallback.detect_intent(text)

    def is_using_fallback(self) -> bool:
        """Return True if the server is running on the keyword fallback."""
        return self._using_fallback

    def model_info(self) -> dict:
        """Return metadata about the loaded model."""
        return {
            "model_path": str(INTENT_MODEL_PATH),
            "model_loaded": not self._using_fallback,
            "model_type": type(self._model).__name__ if self._model else "KeywordFallback",
            "has_vectorizer": self._vectorizer is not None,
        }


# ---------------------------------------------------------------------------
# Module-level singleton — import and use directly
# ---------------------------------------------------------------------------

_server: ModelServer | None = None


def get_model_server() -> ModelServer:
    """Return the module-level ModelServer singleton, creating it if needed."""
    global _server
    if _server is None:
        _server = ModelServer()
    return _server


def predict_intent(text: str) -> str:
    """Convenience wrapper: predict intent via the singleton server."""
    return get_model_server().predict_intent(text)


# ---------------------------------------------------------------------------
# Direct testing
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    server = get_model_server()

    print("\n" + "=" * 50)
    print("Model Server Info")
    print("=" * 50)

    import json
    print(json.dumps(server.model_info(), indent=2))

    test_inputs = [
        "Add Rahul as customer",
        "Delete customer Amit",
        "Upload file report.xlsx",
        "Download the report",
        "Send email to manager",
        "Rahul naam ka customer jod do",
    ]

    print("\nIntent Predictions:")
    print("-" * 40)
    for text in test_inputs:
        intent = server.predict_intent(text)
        print(f"  {text!r:45s} → {intent}")
