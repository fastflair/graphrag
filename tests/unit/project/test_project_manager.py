from __future__ import annotations

import json
from pathlib import Path

from graphrag.project import (
    Persona,
    ProjectFolderManager,
    ReasoningStep,
    ChatSessionRecord,
    ReportSynthesisRecord,
)


def build_reasoning(prefix: str) -> list[ReasoningStep]:
    return [
        ReasoningStep(
            name=f"{prefix}-step-{index}",
            input_text=f"{prefix} input {index}",
            output_text=f"{prefix} output {index}",
            tool="mock_tool",
        )
        for index in range(2)
    ]


def test_create_project_structure(tmp_path: Path) -> None:
    manager = ProjectFolderManager(tmp_path)
    project_path = manager.create_project("demo")

    assert (project_path / "project.json").exists()
    assert (project_path / "chats").is_dir()
    assert (project_path / "agents").is_dir()
    assert (project_path / "reports").is_dir()
    assert (project_path / "reasoning.db").exists()


def test_ingest_chat_persists_required_artifacts(tmp_path: Path) -> None:
    manager = ProjectFolderManager(tmp_path)
    persona = Persona(name="Analyst", description="Understands sales data")
    record = ChatSessionRecord(
        persona=persona,
        skills_used=["sql_query", "summarisation"],
        input_prompt="Show quarterly sales.",
        output_text="Sales increased.",
        reasoning=build_reasoning("chat"),
        graph_snapshot={"nodes": 10},
    )

    agent_record = manager.ingest_chat("demo", record)

    chats_dir = tmp_path / "demo" / "chats"
    chat_folder = chats_dir / agent_record.source_chat_id

    assert chat_folder.exists()
    assert (chat_folder / "input.txt").read_text(encoding="utf-8") == "Show quarterly sales."
    assert (chat_folder / "output.txt").read_text(encoding="utf-8") == "Sales increased."
    reasoning_payload = json.loads((chat_folder / "reasoning.json").read_text(encoding="utf-8"))
    assert len(reasoning_payload) == 2
    assert reasoning_payload[0]["name"].startswith("chat-step")

    agent_path = tmp_path / "demo" / "agents" / f"{agent_record.agent_id}.json"
    assert agent_path.exists()
    agent_payload = json.loads(agent_path.read_text(encoding="utf-8"))
    assert agent_payload["expected_output"] == "Sales increased."

    reasoning_db = tmp_path / "demo" / "reasoning.db"
    assert reasoning_db.exists()


def test_promote_report_creates_agent_and_saves_reasoning(tmp_path: Path) -> None:
    manager = ProjectFolderManager(tmp_path)
    persona = Persona(name="Reporter")
    report = ReportSynthesisRecord(
        report_id="report-1",
        persona=persona,
        question="What happened?",
        output_text="A summary.",
        referenced_agent_ids=["agent-123"],
        reasoning=build_reasoning("report"),
    )

    agent_record = manager.promote_report_to_agent("demo", report, new_agent_id="agent-final")

    report_dir = tmp_path / "demo" / "reports" / "report-1"
    assert report_dir.is_dir()
    assert (report_dir / "output.txt").read_text(encoding="utf-8") == "A summary."

    agent_path = tmp_path / "demo" / "agents" / "agent-final.json"
    assert agent_path.exists()
    payload = json.loads(agent_path.read_text(encoding="utf-8"))
    assert payload["skills"] == ["agent-123"]
    assert payload["input_prompt"] == "What happened?"
