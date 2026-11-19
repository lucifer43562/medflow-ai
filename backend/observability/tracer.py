"""
Observability & Provenance Tracing Subsystem:
Tracks execution spans, parent-child agent calls, estimated token consumption,
and dollar costs across multi-agent workflows.
"""

import time
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class AgentSpan(BaseModel):
    span_id: str = Field(default_factory=lambda: f"SPAN-{uuid.uuid4().hex[:6].upper()}")
    trace_id: str
    parent_span_id: Optional[str] = None
    agent_name: str
    framework: str = "MedFlow"
    action: str
    start_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    duration_ms: float = 0.0
    status: str = "RUNNING"
    prompt_architecture: str = "Standard"
    estimated_tokens: int = 0
    estimated_cost_usd: float = 0.0
    provenance_metadata: Dict[str, Any] = Field(default_factory=dict)


class ObservabilityTracer:
    """
    OpenTelemetry-compatible Tracing and Audit Provenance Manager.
    Records every agent deliberation step, tool invocation, and resource commitment.
    """
    
    # Blended Cost per 1K Tokens: ~$0.0003 for lightweight flash models
    COST_PER_1K_TOKENS = 0.0003

    def __init__(self):
        self._spans: Dict[str, AgentSpan] = {}
        self._active_traces: Dict[str, List[str]] = {}

    def start_span(
        self,
        trace_id: str,
        agent_name: str,
        action: str,
        framework: str = "MedFlow",
        parent_span_id: Optional[str] = None,
        prompt_architecture: str = "Standard",
        metadata: Optional[Dict[str, Any]] = None,
        prompt_arch: Optional[str] = None,
        est_tokens: int = 0,
        estimated_tokens: int = 0,
        **kwargs
    ) -> AgentSpan:
        p_arch = prompt_arch or prompt_architecture
        tokens = est_tokens or estimated_tokens
        span = AgentSpan(
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            agent_name=agent_name,
            framework=framework,
            action=action,
            prompt_architecture=p_arch,
            estimated_tokens=tokens,
            estimated_cost_usd=round((tokens / 1000.0) * self.COST_PER_1K_TOKENS, 6),
            provenance_metadata=metadata or {}
        )
        self._spans[span.span_id] = span
        if trace_id not in self._active_traces:
            self._active_traces[trace_id] = []
        self._active_traces[trace_id].append(span.span_id)
        return span

    def finish_span(
        self,
        span_id: str,
        status: str = "SUCCESS",
        estimated_tokens: Optional[int] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Optional[AgentSpan]:
        if span_id not in self._spans:
            return None
            
        span = self._spans[span_id]
        span.end_time = datetime.now(timezone.utc)
        span.duration_ms = max(1.0, (span.end_time - span.start_time).total_seconds() * 1000.0)
        span.status = status
        if estimated_tokens is not None:
            span.estimated_tokens = estimated_tokens
            span.estimated_cost_usd = round((estimated_tokens / 1000.0) * self.COST_PER_1K_TOKENS, 6)
        if extra_metadata:
            span.provenance_metadata.update(extra_metadata)
        return span

    def get_spans_by_trace(self, trace_id: str) -> List[AgentSpan]:
        span_ids = self._active_traces.get(trace_id, [])
        return [self._spans[sid] for sid in span_ids if sid in self._spans]

    def get_trace_summary(self, trace_id: str) -> Dict[str, Any]:
        span_ids = self._active_traces.get(trace_id, [])
        spans = [self._spans[sid] for sid in span_ids if sid in self._spans]
        
        total_time = sum(s.duration_ms for s in spans)
        total_tokens = sum(s.estimated_tokens for s in spans)
        total_cost = sum(s.estimated_cost_usd for s in spans)
        
        return {
            "trace_id": trace_id,
            "total_spans": len(spans),
            "total_duration_ms": round(total_time, 2),
            "total_estimated_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 6),
            "spans": [s.model_dump() for s in spans]
        }


# Global Observability Tracer
global_tracer = ObservabilityTracer()
