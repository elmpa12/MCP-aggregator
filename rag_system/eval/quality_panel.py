"""
Quality Panel for Advanced RAG v2

Runs a test suite of real questions with ideal answers (gabarito),
queries the current RAG system, and scores on:
- precision (0-10)
- context_usage (0-10)
- hallucination (0-10, higher is worse → inverted for score)
- completeness (0-10)

Outputs JSON logs under rag_eval_runs/run_<timestamp>.json
"""

from __future__ import annotations
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple


def _tokenize(text: str) -> List[str]:
    return [t for t in ''.join(c.lower() if c.isalnum() else ' ' for c in text).split() if t]


def _overlap_score(a: str, b: str) -> float:
    ta, tb = set(_tokenize(a)), set(_tokenize(b))
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    denom = max(1, len(tb))
    return inter / denom


def _completeness_score(ideal: str, output: str) -> float:
    ti, to = set(_tokenize(ideal)), set(_tokenize(output))
    if not ti:
        return 0.0
    covered = len(ti & to) / len(ti)
    return covered


def _context_usage_score(output: str) -> float:
    # Heuristic: presence of [Doc N] citations boosts context usage
    has_cites = '[Doc ' in output
    return 1.0 if has_cites else 0.3


def _hallucination_penalty(ideal: str, output: str) -> float:
    # Heuristic: if very low overlap with ideal and no citations → high penalty
    overlap = _overlap_score(ideal, output)
    cites = _context_usage_score(output)
    if overlap > 0.5:
        return 0.0
    if overlap < 0.2 and cites < 0.5:
        return 0.8
    return 0.3


def score_answer(ideal: str, system_answer: str) -> Dict[str, float]:
    prec = _overlap_score(ideal, system_answer)
    comp = _completeness_score(ideal, system_answer)
    ctx = _context_usage_score(system_answer)
    hall = _hallucination_penalty(ideal, system_answer)
    # Map to 0–10 scale; hallucination is inverse of penalty
    return {
        'precisao': round(prec * 10, 2),
        'uso_contexto': round(ctx * 10, 2),
        'alucinacao': round((1 - hall) * 10, 2),
        'completude': round(comp * 10, 2),
    }


def run_quality_suite(rag, suite_path: Path, out_dir: Path) -> Path:
    suite = json.loads(Path(suite_path).read_text(encoding='utf-8'))
    results = []
    start = time.time()

    for case in suite.get('tests', []):
        question = case.get('question', '')
        ideal = case.get('ideal_answer', '')
        try:
            answer, confidence = rag.query(question)
        except Exception as e:
            answer, confidence = f"❌ Erro ao responder: {e}", 0.0

        scores = score_answer(ideal, answer)
        results.append({
            'question': question,
            'ideal_answer': ideal,
            'system_answer': answer,
            'confidence': confidence,
            'scores': scores,
        })

    elapsed = time.time() - start
    summary = {
        'avg_precisao': round(sum(r['scores']['precisao'] for r in results) / max(1, len(results)), 2),
        'avg_uso_contexto': round(sum(r['scores']['uso_contexto'] for r in results) / max(1, len(results)), 2),
        'avg_alucinacao': round(sum(r['scores']['alucinacao'] for r in results) / max(1, len(results)), 2),
        'avg_completude': round(sum(r['scores']['completude'] for r in results) / max(1, len(results)), 2),
    }

    payload = {
        'timestamp': int(time.time()),
        'elapsed_sec': round(elapsed, 2),
        'model': rag.get_stats().get('claude_model'),
        'reranker': rag.get_stats().get('reranker_model'),
        'vector_store': rag.get_stats().get('vector_store'),
        'results': results,
        'summary': summary,
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"run_{int(time.time())}.json"
    out_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    return out_file

