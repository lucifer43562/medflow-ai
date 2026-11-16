"""
Task Monitoring & Logging via Callbacks:
Provides an extensible callback subsystem to intercept and log agent execution flows,
tool executions, state mutations, and runtime errors.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger("medflow.callbacks")


class BaseAgentCallback:
    """Abstract callback interface for autonomous agents."""
    
    def on_agent_start(self, agent_name: str, input_data: Dict[str, Any]):
        pass

    def on_tool_start(self, agent_name: str, tool_name: str, tool_args: Dict[str, Any]):
        pass

    def on_tool_end(self, agent_name: str, tool_name: str, tool_output: Dict[str, Any]):
        pass

    def on_agent_finish(self, agent_name: str, output_data: Dict[str, Any], execution_time_ms: float):
        pass

    def on_error(self, agent_name: str, error: Exception, context: Dict[str, Any]):
        pass

    def on_state_change(self, entity_id: str, old_state: str, new_state: str, reason: str):
        pass


class TelemetryMonitoringCallback(BaseAgentCallback):
    """
    In-Memory Monitoring & Execution Tracker Callback.
    Maintains a forensic timeline of all agent activities for debugging and dashboard streaming.
    """
    
    def __init__(self):
        self.execution_spans: List[Dict[str, Any]] = []
        self._active_timers: Dict[str, float] = {}

    def on_agent_start(self, agent_name: str, input_data: Dict[str, Any]):
        self._active_timers[agent_name] = time.time()
        span = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "AGENT_START",
            "agent": agent_name,
            "input_summary": str(input_data)[:120]
        }
        self.execution_spans.append(span)
        logger.info(f"[CALLBACK] {agent_name} started execution.")

    def on_tool_start(self, agent_name: str, tool_name: str, tool_args: Dict[str, Any]):
        span = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "TOOL_INVOKED",
            "agent": agent_name,
            "tool": tool_name,
            "args": tool_args
        }
        self.execution_spans.append(span)
        logger.info(f"[CALLBACK] {agent_name} invoked tool: {tool_name}")

    def on_tool_end(self, agent_name: str, tool_name: str, tool_output: Dict[str, Any]):
        span = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "TOOL_COMPLETED",
            "agent": agent_name,
            "tool": tool_name,
            "output_preview": str(tool_output)[:120]
        }
        self.execution_spans.append(span)

    def on_agent_finish(self, agent_name: str, output_data: Dict[str, Any], execution_time_ms: float):
        span = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "AGENT_FINISH",
            "agent": agent_name,
            "execution_time_ms": execution_time_ms,
            "status": "SUCCESS"
        }
        self.execution_spans.append(span)
        logger.info(f"[CALLBACK] {agent_name} finished in {execution_time_ms:.1f}ms.")

    def on_error(self, agent_name: str, error: Exception, context: Dict[str, Any]):
        span = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "AGENT_ERROR",
            "agent": agent_name,
            "error_type": type(error).__name__,
            "error_msg": str(error),
            "context": context
        }
        self.execution_spans.append(span)
        logger.error(f"[CALLBACK] Error in {agent_name}: {error}")

    def on_state_change(self, entity_id: str, old_state: str, new_state: str, reason: str):
        span = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "STATE_MUTATION",
            "entity": entity_id,
            "transition": f"{old_state} -> {new_state}",
            "reason": reason
        }
        self.execution_spans.append(span)

    def get_timeline(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self.execution_spans[-limit:]


# Global monitoring callback instance
global_monitor = TelemetryMonitoringCallback()
