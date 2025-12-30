from typing import List, Dict, Any
import os
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="FinBERT Sentiment API (GPU)", version="1.0.0")

_tokenizer = None
_model = None
_device = None


def _load_model():
    global _tokenizer, _model, _device
    if _model is not None and _tokenizer is not None:
        return

    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch

    model_name = os.getenv("FINBERT_MODEL", "ProsusAI/finbert")
    _tokenizer = AutoTokenizer.from_pretrained(model_name)
    _model = AutoModelForSequenceClassification.from_pretrained(model_name)
    _model.eval()
    _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    _model.to(_device)


class AnalyzeRequest(BaseModel):
    text: str


class AnalyzeBatchRequest(BaseModel):
    texts: List[str]
    batch_size: int | None = 32


@app.on_event("startup")
def on_startup():
    _load_model()


@app.get("/health")
def health() -> Dict[str, Any]:
    import torch
    return {
        "status": "ok",
        "device": str(_device) if _device else "unknown",
        "cuda": bool(torch.cuda.is_available()),
    }


@app.post("/analyze")
def analyze(req: AnalyzeRequest) -> Dict[str, float]:
    if not req.text or not req.text.strip():
        return {"positive": 0.0, "negative": 0.0, "neutral": 1.0, "compound": 0.0}

    import torch
    from torch import no_grad

    enc = _tokenizer(
        req.text,
        return_tensors="pt",
        truncation=True,
        max_length=512,
        padding=True,
    ).to(_device)

    with no_grad():
        out = _model(**enc)
        probs = torch.nn.functional.softmax(out.logits, dim=-1).cpu().numpy()[0]

    positive = float(probs[0])
    negative = float(probs[1])
    neutral = float(probs[2])
    compound = positive - negative
    return {
        "positive": positive,
        "negative": negative,
        "neutral": neutral,
        "compound": compound,
    }


@app.post("/analyze_batch")
def analyze_batch(req: AnalyzeBatchRequest) -> Dict[str, List[Dict[str, float]]]:
    texts = [t for t in req.texts if t and t.strip()]
    if not texts:
        return {"results": []}

    batch_size = req.batch_size or 32
    import torch
    from torch import no_grad

    results: List[Dict[str, float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        enc = _tokenizer(
            batch,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True,
        ).to(_device)

        with no_grad():
            out = _model(**enc)
            probs = torch.nn.functional.softmax(out.logits, dim=-1).cpu().numpy()

        for p in probs:
            positive = float(p[0])
            negative = float(p[1])
            neutral = float(p[2])
            compound = positive - negative
            results.append(
                {
                    "positive": positive,
                    "negative": negative,
                    "neutral": neutral,
                    "compound": compound,
                }
            )

    return {"results": results}
