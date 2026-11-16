"""
Agent-to-Agent (A2A) Communication Protocol:
Implements standardized A2A message envelopes, FIPA-compliant performatives,
and an interoperability bus for cross-framework communication (CrewAI <-> ADK).
"""

import uuid
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class A2APerformative(str, Enum):
    REQUEST = "REQUEST"      # Initiator asks receiver to perform action (e.g. Triage requests Allocation)
    PROPOSE = "PROPOSE"      # Agent proposes candidate allocation or diagnosis
    INFORM = "INFORM"        # Agent conveys state or telemetry
    AGREE = "AGREE"          # Agent concurs with proposal
    REFUSE = "REFUSE"        # Agent or Guardrail rejects proposal (e.g. Escalation circuit breaker)
    QUERY = "QUERY"          # Agent queries blackboard or knowledge base


class A2AMessage(BaseModel):
    """
    Standardized Interoperable A2A Message Envelope.
    Permits heterogeneous agents (CrewAI and Google ADK) to communicate seamlessly.
    """
    message_id: str = Field(default_factory=lambda: f"A2A-{uuid.uuid4().hex[:8].upper()}")
    conversation_id: str
    sender_id: str
    sender_framework: str = Field(default="CrewAI", description="'CrewAI' or 'ADK'")
    receiver_id: str
    receiver_framework: str = Field(default="ADK", description="'CrewAI' or 'ADK'")
    performative: A2APerformative
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: Dict[str, Any]
    in_reply_to: Optional[str] = None


class A2ADispatcher:
    """
    Interoperable Message Bus routing messages across agents.
    Maintains a complete audit history for provenance and observability.
    """
    
    def __init__(self):
        self._handlers: Dict[str, Any] = {}
        self.message_history: List[A2AMessage] = []

    def register_agent(self, agent_id: str, handler_func):
        """Registers a message listener for an agent."""
        self._handlers[agent_id] = handler_func

    def send(self, message: A2AMessage) -> Optional[A2AMessage]:
        """Dispatches an A2A message to target agent."""
        self.message_history.append(message)
        
        if message.receiver_id in self._handlers:
            handler = self._handlers[message.receiver_id]
            try:
                response = handler(message)
                if isinstance(response, A2AMessage):
                    self.message_history.append(response)
                return response
            except Exception as e:
                # Fallback error message
                err_reply = A2AMessage(
                    conversation_id=message.conversation_id,
                    sender_id="A2A-ROUTER",
                    sender_framework="SYSTEM",
                    receiver_id=message.sender_id,
                    receiver_framework=message.sender_framework,
                    performative=A2APerformative.REFUSE,
                    payload={"error": str(e)},
                    in_reply_to=message.message_id
                )
                self.message_history.append(err_reply)
                return err_reply
        return None

    def get_conversation(self, conversation_id: str) -> List[A2AMessage]:
        return [m for m in self.message_history if m.conversation_id == conversation_id]


# Global A2A Dispatcher Instance
global_a2a_dispatcher = A2ADispatcher()
