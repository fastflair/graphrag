"""High-level orchestration for project chat archival and replay."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from .models import (
    AgentProcessRecord,
    ChatSessionRecord,
    Persona,
    ReasoningStep,
    ReportSynthesisRecord,
    iter_reasoning_steps,
)
from .reasoning_store import ReasoningStore
from .storage import ensure_directory, write_json, write_text


class ProjectFolderManager:
    """Creates deterministic project structures that make tacit knowledge explicit."""

    def __init__(self, root_directory: Path) -> None:
        self.root_directory = Path(root_directory)

    def create_project(self, project_name: str) -> Path:
        project_path = self.root_directory / project_name
        ensure_directory(project_path)
        ensure_directory(project_path / "chats")
        ensure_directory(project_path / "agents")
        ensure_directory(project_path / "reports")

        reasoning_store = ReasoningStore(project_path / "reasoning.db")
        reasoning_store.initialise()

        manifest_path = project_path / "project.json"
        if not manifest_path.exists():
            write_json(
                manifest_path,
                {
                    "project_name": project_name,
                    "created_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
                },
            )
        return project_path

    def ingest_chat(self, project_name: str, record: ChatSessionRecord) -> AgentProcessRecord:
        project_path = self.create_project(project_name)
        chat_identifier = record.chat_id or self._build_chat_identifier(record)
        chat_dir = ensure_directory(project_path / "chats" / chat_identifier)

        canonical_record = replace(record, chat_id=chat_identifier)

        write_json(chat_dir / "metadata.json", canonical_record.to_dict())
        write_text(chat_dir / "input.txt", canonical_record.input_prompt)
        write_text(chat_dir / "output.txt", canonical_record.output_text)
        if canonical_record.graph_snapshot:
            write_json(chat_dir / "graph.json", canonical_record.graph_snapshot)
        if canonical_record.reasoning:
            write_json(chat_dir / "reasoning.json", iter_reasoning_steps(canonical_record.reasoning))

        reasoning_store = ReasoningStore(project_path / "reasoning.db")
        reasoning_store.initialise()
        reasoning_store.append("chat", chat_identifier, canonical_record.reasoning)

        agent_record = AgentProcessRecord(
            agent_id=f"agent-{chat_identifier}",
            source_chat_id=chat_identifier,
            persona=canonical_record.persona,
            skills=list(canonical_record.skills_used),
            workflow=list(canonical_record.reasoning),
            input_prompt=canonical_record.input_prompt,
            expected_output=canonical_record.output_text,
            graph_snapshot=canonical_record.graph_snapshot,
        )

        self._persist_agent_record(project_path, agent_record)
        return agent_record

    def promote_report_to_agent(
        self,
        project_name: str,
        report: ReportSynthesisRecord,
        *,
        new_agent_id: Optional[str] = None,
    ) -> AgentProcessRecord:
        project_path = self.create_project(project_name)
        reports_dir = ensure_directory(project_path / "reports")
        report_dir = ensure_directory(reports_dir / report.report_id)

        write_json(report_dir / "report.json", report.to_dict())
        write_text(report_dir / "question.txt", report.question)
        write_text(report_dir / "output.txt", report.output_text)
        if report.reasoning:
            write_json(report_dir / "reasoning.json", iter_reasoning_steps(report.reasoning))

        reasoning_store = ReasoningStore(project_path / "reasoning.db")
        reasoning_store.initialise()
        reasoning_store.append("report", report.report_id, report.reasoning)

        agent_identifier = new_agent_id or f"agent-report-{report.report_id}"
        agent_record = AgentProcessRecord(
            agent_id=agent_identifier,
            source_chat_id=report.report_id,
            persona=report.persona,
            skills=report.referenced_agent_ids,
            workflow=list(report.reasoning),
            input_prompt=report.question,
            expected_output=report.output_text,
        )

        self._persist_agent_record(project_path, agent_record)
        return agent_record

    def list_agents(self, project_name: str) -> List[AgentProcessRecord]:
        project_path = self.create_project(project_name)
        agents_dir = project_path / "agents"
        records: List[AgentProcessRecord] = []
        for path in sorted(agents_dir.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            records.append(
                AgentProcessRecord(
                    agent_id=data["agent_id"],
                    source_chat_id=data["source_chat_id"],
                    persona=Persona(
                        name=data["persona"]["name"],
                        description=data["persona"].get("description"),
                        metadata=data["persona"].get("metadata", {}),
                    ),
                    skills=list(data.get("skills", [])),
                    workflow=[
                        ReasoningStep(
                            name=step["name"],
                            input_text=step["input_text"],
                            output_text=step["output_text"],
                            tool=step.get("tool"),
                            metadata=step.get("metadata", {}),
                        )
                        for step in data.get("workflow", [])
                    ],
                    input_prompt=data["input_prompt"],
                    expected_output=data["expected_output"],
                    graph_snapshot=data.get("graph_snapshot", {}),
                )
            )
        return records

    def _persist_agent_record(self, project_path: Path, record: AgentProcessRecord) -> None:
        agents_dir = ensure_directory(project_path / "agents")
        write_json(agents_dir / f"{record.agent_id}.json", record.to_dict())

    def _build_chat_identifier(self, record: ChatSessionRecord) -> str:
        timestamp = record.created_at.isoformat().replace(":", "").replace("-", "")
        random_suffix = uuid4().hex[:6]
        persona_slug = record.persona.name.lower().replace(" ", "-")
        return f"{timestamp}-{persona_slug}-{random_suffix}"
