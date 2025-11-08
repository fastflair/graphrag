"""Data models that describe project chat archival artifacts."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional


def _serialize_metadata(metadata: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    if metadata is None:
        return {}
    if isinstance(metadata, dict):
        return metadata
    return dict(metadata)


@dataclass(slots=True)
class Persona:
    """Describes the perspective a user employed when interacting with the agent."""

    name: str
    description: str | None = None
    metadata: MutableMapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "name": self.name,
            "description": self.description,
            "metadata": _serialize_metadata(self.metadata),
        }
        return {key: value for key, value in data.items() if value not in (None, {})}


@dataclass(slots=True)
class ReasoningStep:
    """Captures an intermediate reasoning step produced by the agent."""

    name: str
    input_text: str
    output_text: str
    tool: str | None = None
    metadata: MutableMapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "name": self.name,
            "input_text": self.input_text,
            "output_text": self.output_text,
            "tool": self.tool,
            "metadata": _serialize_metadata(self.metadata),
        }
        return {key: value for key, value in data.items() if value not in (None, {})}


@dataclass(slots=True)
class ChatSessionRecord:
    """A full record of a chat session imported into a project folder."""

    persona: Persona
    skills_used: List[str]
    input_prompt: str
    output_text: str
    reasoning: List[ReasoningStep]
    graph_snapshot: MutableMapping[str, Any] = field(default_factory=dict)
    chat_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.utcnow().replace(microsecond=0))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chat_id": self.chat_id,
            "created_at": self.created_at.isoformat() + "Z",
            "persona": self.persona.to_dict(),
            "skills_used": list(self.skills_used),
            "input_prompt": self.input_prompt,
            "output_text": self.output_text,
            "reasoning": [step.to_dict() for step in self.reasoning],
            "graph_snapshot": _serialize_metadata(self.graph_snapshot),
        }


@dataclass(slots=True)
class AgentProcessRecord:
    """Describes the artefacts required to recreate a conversation's behaviour."""

    agent_id: str
    source_chat_id: str
    persona: Persona
    skills: List[str]
    workflow: List[ReasoningStep]
    input_prompt: str
    expected_output: str
    created_at: datetime = field(default_factory=lambda: datetime.utcnow().replace(microsecond=0))
    graph_snapshot: MutableMapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "source_chat_id": self.source_chat_id,
            "created_at": self.created_at.isoformat() + "Z",
            "persona": self.persona.to_dict(),
            "skills": list(self.skills),
            "workflow": [step.to_dict() for step in self.workflow],
            "input_prompt": self.input_prompt,
            "expected_output": self.expected_output,
            "graph_snapshot": _serialize_metadata(self.graph_snapshot),
        }


@dataclass(slots=True)
class ReportSynthesisRecord:
    """Represents a report built from project chats and approved by a user."""

    report_id: str
    persona: Persona
    question: str
    output_text: str
    referenced_agent_ids: List[str]
    reasoning: List[ReasoningStep]
    created_at: datetime = field(default_factory=lambda: datetime.utcnow().replace(microsecond=0))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "created_at": self.created_at.isoformat() + "Z",
            "persona": self.persona.to_dict(),
            "question": self.question,
            "output_text": self.output_text,
            "referenced_agent_ids": list(self.referenced_agent_ids),
            "reasoning": [step.to_dict() for step in self.reasoning],
        }


@dataclass(slots=True)
class WorkflowHint:
    """A structured hint derived from a reasoning step for replay guidance."""

    index: int
    name: str
    instruction: str
    expected: str
    tool: str | None = None
    metadata: MutableMapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "index": self.index,
            "name": self.name,
            "instruction": self.instruction,
            "expected": self.expected,
            "tool": self.tool,
            "metadata": _serialize_metadata(self.metadata),
        }
        return {key: value for key, value in data.items() if value not in (None, {})}


@dataclass(slots=True)
class AgentReplayPlan:
    """Provides explicit instructions for recreating an archived agent run."""

    agent_id: str
    persona: Persona
    input_prompt: str
    expected_output: str
    skills: List[str]
    hints: List[WorkflowHint]
    graph_snapshot: MutableMapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "persona": self.persona.to_dict(),
            "input_prompt": self.input_prompt,
            "expected_output": self.expected_output,
            "skills": list(self.skills),
            "hints": [hint.to_dict() for hint in self.hints],
            "graph_snapshot": _serialize_metadata(self.graph_snapshot),
        }

    @classmethod
    def from_agent(cls, agent: "AgentProcessRecord") -> "AgentReplayPlan":
        hints = [
            WorkflowHint(
                index=index,
                name=step.name,
                instruction=step.input_text,
                expected=step.output_text,
                tool=step.tool,
                metadata=dict(step.metadata),
            )
            for index, step in enumerate(agent.workflow, start=1)
        ]
        return cls(
            agent_id=agent.agent_id,
            persona=agent.persona,
            input_prompt=agent.input_prompt,
            expected_output=agent.expected_output,
            skills=list(agent.skills),
            hints=hints,
            graph_snapshot=agent.graph_snapshot,
        )


def as_serializable_dict(data: Any) -> Dict[str, Any]:
    """Convert dataclasses to dictionaries, leaving other mappings untouched."""

    if hasattr(data, "to_dict"):
        return data.to_dict()  # type: ignore[return-value]
    if isinstance(data, dict):
        return data
    return asdict(data)


def iter_reasoning_steps(reasoning: Iterable[ReasoningStep]) -> List[Dict[str, Any]]:
    """Convert reasoning steps into serialisable dictionaries."""

    return [step.to_dict() for step in reasoning]
