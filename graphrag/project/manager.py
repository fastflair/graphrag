"""High-level orchestration for project chat archival and replay."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .models import (
    AgentProcessRecord,
    AgentReplayPlan,
    ChatSessionRecord,
    Persona,
    ReasoningStep,
    ReportSynthesisRecord,
    iter_reasoning_steps,
)
from .reasoning_store import ReasoningStore
from .storage import ensure_directory, read_json, write_json, write_text


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
        index_path = project_path / "index.json"
        if not index_path.exists():
            write_json(
                index_path,
                {
                    "chats": {},
                    "agents": {},
                    "reports": {},
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

        chat_index_payload: Dict[str, Any] = {
            "persona": canonical_record.persona.to_dict(),
            "skills_used": list(canonical_record.skills_used),
            "created_at": canonical_record.created_at.isoformat() + "Z",
            "input_path": str((Path("chats") / chat_identifier / "input.txt").as_posix()),
            "output_path": str((Path("chats") / chat_identifier / "output.txt").as_posix()),
        }
        if canonical_record.reasoning:
            chat_index_payload["reasoning_path"] = str(
                (Path("chats") / chat_identifier / "reasoning.json").as_posix()
            )
        if canonical_record.graph_snapshot:
            chat_index_payload["graph_path"] = str(
                (Path("chats") / chat_identifier / "graph.json").as_posix()
            )

        self._update_index(project_path, "chats", chat_identifier, chat_index_payload)

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

        report_index_payload: Dict[str, Any] = {
            "persona": report.persona.to_dict(),
            "question": report.question,
            "referenced_agents": list(report.referenced_agent_ids),
            "created_at": report.created_at.isoformat() + "Z",
            "output_path": str((Path("reports") / report.report_id / "output.txt").as_posix()),
        }
        if report.reasoning:
            report_index_payload["reasoning_path"] = str(
                (Path("reports") / report.report_id / "reasoning.json").as_posix()
            )

        self._update_index(project_path, "reports", report.report_id, report_index_payload)

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
            data = read_json(path)
            records.append(self._deserialize_agent_record(data))
        return records

    def load_agent(self, project_name: str, agent_id: str) -> AgentProcessRecord:
        project_path = self.create_project(project_name)
        agent_path = project_path / "agents" / f"{agent_id}.json"
        data = read_json(agent_path)
        return self._deserialize_agent_record(data)

    def build_replay_plan(self, project_name: str, agent_id: str) -> AgentReplayPlan:
        agent_record = self.load_agent(project_name, agent_id)
        return AgentReplayPlan.from_agent(agent_record)

    def _persist_agent_record(self, project_path: Path, record: AgentProcessRecord) -> None:
        agents_dir = ensure_directory(project_path / "agents")
        write_json(agents_dir / f"{record.agent_id}.json", record.to_dict())
        self._update_index(
            project_path,
            "agents",
            record.agent_id,
            {
                "source_chat_id": record.source_chat_id,
                "persona": record.persona.to_dict(),
                "skills": list(record.skills),
                "created_at": record.created_at.isoformat() + "Z",
            },
        )

    def _build_chat_identifier(self, record: ChatSessionRecord) -> str:
        timestamp = record.created_at.isoformat().replace(":", "").replace("-", "")
        random_suffix = uuid4().hex[:6]
        persona_slug = record.persona.name.lower().replace(" ", "-")
        return f"{timestamp}-{persona_slug}-{random_suffix}"

    def _update_index(
        self,
        project_path: Path,
        section: str,
        identifier: str,
        payload: Dict[str, Any],
    ) -> None:
        index_path = project_path / "index.json"
        if index_path.exists():
            index_data = read_json(index_path)
        else:
            index_data = {"chats": {}, "agents": {}, "reports": {}}
        section_payload = index_data.setdefault(section, {})
        section_payload[identifier] = payload
        write_json(index_path, index_data)

    def _deserialize_agent_record(self, data: Dict[str, Any]) -> AgentProcessRecord:
        persona_payload = data["persona"]
        persona = Persona(
            name=persona_payload["name"],
            description=persona_payload.get("description"),
            metadata=persona_payload.get("metadata", {}),
        )
        workflow = [
            ReasoningStep(
                name=step["name"],
                input_text=step["input_text"],
                output_text=step["output_text"],
                tool=step.get("tool"),
                metadata=step.get("metadata", {}),
            )
            for step in data.get("workflow", [])
        ]
        created_at_value = data.get("created_at")
        created_at = None
        if isinstance(created_at_value, str):
            created_at = self._parse_timestamp(created_at_value)

        record_kwargs = {
            "agent_id": data["agent_id"],
            "source_chat_id": data["source_chat_id"],
            "persona": persona,
            "skills": list(data.get("skills", [])),
            "workflow": workflow,
            "input_prompt": data["input_prompt"],
            "expected_output": data["expected_output"],
            "graph_snapshot": data.get("graph_snapshot", {}),
        }
        if created_at is not None:
            record_kwargs["created_at"] = created_at
        return AgentProcessRecord(**record_kwargs)

    def _parse_timestamp(self, value: str) -> datetime:
        if value.endswith("Z"):
            value = value[:-1]
        return datetime.fromisoformat(value)
