"""
OpenTelemetry-based tracing for RAG pipeline
Phase 3 Enhancement: Detailed observability
"""

from __future__ import annotations

import os
import time
from contextlib import contextmanager
from typing import Dict, Optional, Any
from datetime import datetime
import json
from pathlib import Path


class RAGTracer:
    """Lightweight tracing for RAG pipeline operations"""
    
    def __init__(self, project_name: str, logs_dir: Optional[Path] = None):
        self.project_name = project_name
        self.logs_dir = logs_dir or Path("/home/scalp/rag_system/logs/traces")
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        self.enabled = os.getenv('RAG_TRACING_ENABLED', '1') == '1'
        self.current_trace: Optional[Dict] = None
        self.spans: list[Dict] = []
    
    def start_trace(self, operation: str, query: str, metadata: Optional[Dict] = None) -> str:
        """Start a new trace for a RAG operation"""
        if not self.enabled:
            return ""
        
        trace_id = f"{operation}_{int(time.time() * 1000)}"
        
        self.current_trace = {
            'trace_id': trace_id,
            'operation': operation,
            'query': query[:200],  # Truncate for privacy
            'metadata': metadata or {},
            'start_time': time.time(),
            'start_ts': datetime.utcnow().isoformat() + 'Z',
            'spans': []
        }
        
        return trace_id
    
    @contextmanager
    def span(self, name: str, attributes: Optional[Dict] = None):
        """Context manager for creating spans"""
        if not self.enabled or not self.current_trace:
            yield
            return
        
        span_data = {
            'name': name,
            'start_time': time.time(),
            'attributes': attributes or {}
        }
        
        try:
            yield span_data
        except Exception as e:
            span_data['error'] = str(e)
            span_data['status'] = 'error'
            raise
        finally:
            span_data['end_time'] = time.time()
            span_data['duration_ms'] = round((span_data['end_time'] - span_data['start_time']) * 1000, 2)
            span_data['status'] = span_data.get('status', 'ok')
            
            if self.current_trace:
                self.current_trace['spans'].append(span_data)
    
    def end_trace(self, result: Optional[Dict] = None) -> None:
        """End current trace and save to disk"""
        if not self.enabled or not self.current_trace:
            return
        
        self.current_trace['end_time'] = time.time()
        self.current_trace['duration_ms'] = round(
            (self.current_trace['end_time'] - self.current_trace['start_time']) * 1000, 
            2
        )
        
        if result:
            self.current_trace['result'] = {
                'retrieved_docs': result.get('retrieved', 0),
                'reranked_docs': result.get('reranked', 0),
                'context_chars': result.get('context_chars', 0),
                'confidence': result.get('confidence', 0),
                'from_cache': result.get('from_cache', False)
            }
        
        # Save trace to JSONL
        trace_file = self.logs_dir / f"traces_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"
        try:
            with open(trace_file, 'a', encoding='utf-8') as f:
                json.dump(self.current_trace, f)
                f.write('\n')
        except Exception as e:
            print(f"⚠️  Failed to save trace: {e}")
        
        # Reset
        self.current_trace = None
    
    def get_metrics_summary(self, last_n_traces: int = 100) -> Dict:
        """Get aggregated metrics from recent traces"""
        if not self.enabled:
            return {}
        
        # Read last N traces
        traces = []
        for trace_file in sorted(self.logs_dir.glob("traces_*.jsonl"), reverse=True)[:3]:
            try:
                with open(trace_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            traces.append(json.loads(line))
                        if len(traces) >= last_n_traces:
                            break
            except Exception:
                continue
            if len(traces) >= last_n_traces:
                break
        
        if not traces:
            return {}
        
        # Aggregate metrics
        durations = [t['duration_ms'] for t in traces if 'duration_ms' in t]
        
        # Span analysis
        span_stats: Dict[str, list] = {}
        for trace in traces:
            for span in trace.get('spans', []):
                name = span['name']
                if name not in span_stats:
                    span_stats[name] = []
                span_stats[name].append(span['duration_ms'])
        
        return {
            'total_traces': len(traces),
            'avg_duration_ms': round(sum(durations) / len(durations), 2) if durations else 0,
            'p50_duration_ms': round(sorted(durations)[len(durations) // 2], 2) if durations else 0,
            'p95_duration_ms': round(sorted(durations)[int(len(durations) * 0.95)], 2) if durations else 0,
            'p99_duration_ms': round(sorted(durations)[int(len(durations) * 0.99)], 2) if durations else 0,
            'span_breakdown': {
                name: {
                    'avg_ms': round(sum(times) / len(times), 2),
                    'p95_ms': round(sorted(times)[int(len(times) * 0.95)], 2) if len(times) > 20 else max(times)
                }
                for name, times in span_stats.items()
            }
        }


# Global tracer instance
_global_tracer: Optional[RAGTracer] = None


def get_tracer(project_name: str = "scalp") -> RAGTracer:
    """Get or create global tracer instance"""
    global _global_tracer
    if _global_tracer is None:
        _global_tracer = RAGTracer(project_name)
    return _global_tracer
