from __future__ import annotations

import json
from pathlib import Path

from graphrag.project import (
    AgentReplayPlan,
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

    agents_dir = tmp_path / "demo" / "agents"
    agent_path = agents_dir / f"{agent_record.agent_id}.json"
    assert agent_path.exists()
    agent_payload = json.loads(agent_path.read_text(encoding="utf-8"))
    assert agent_payload["expected_output"] == "Sales increased."

    plan_path = agents_dir / f"{agent_record.agent_id}.plan.json"
    assert plan_path.exists()
    plan_payload = json.loads(plan_path.read_text(encoding="utf-8"))
    assert plan_payload["input_prompt"] == "Show quarterly sales."
    assert plan_payload["hints"][0]["instruction"] == "chat input 0"

    plan_markdown_path = agents_dir / f"{agent_record.agent_id}.plan.md"
    assert plan_markdown_path.exists()
    plan_markdown = plan_markdown_path.read_text(encoding="utf-8")
    assert "## Workflow Hints" in plan_markdown
    assert "chat input 0" in plan_markdown

    reasoning_db = tmp_path / "demo" / "reasoning.db"
    assert reasoning_db.exists()

    index_payload = json.loads((tmp_path / "demo" / "index.json").read_text(encoding="utf-8"))
    assert agent_record.source_chat_id in index_payload["chats"]
    assert agent_record.agent_id in index_payload["agents"]
    chat_entry = index_payload["chats"][agent_record.source_chat_id]
    assert chat_entry["reasoning_path"].endswith("reasoning.json")
    assert chat_entry["graph_path"].endswith("graph.json")
    agent_entry = index_payload["agents"][agent_record.agent_id]
    assert agent_entry["plan_path"].endswith("plan.json")
    assert agent_entry["plan_markdown_path"].endswith("plan.md")


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

    agents_dir = tmp_path / "demo" / "agents"
    agent_path = agents_dir / "agent-final.json"
    assert agent_path.exists()
    payload = json.loads(agent_path.read_text(encoding="utf-8"))
    assert payload["skills"] == ["agent-123"]
    assert payload["input_prompt"] == "What happened?"

    plan_json_path = agents_dir / "agent-final.plan.json"
    assert plan_json_path.exists()
    plan_payload = json.loads(plan_json_path.read_text(encoding="utf-8"))
    assert plan_payload["expected_output"] == "A summary."

    plan_markdown_path = agents_dir / "agent-final.plan.md"
    assert plan_markdown_path.exists()
    assert "## Persona" in plan_markdown_path.read_text(encoding="utf-8")

    index_payload = json.loads((tmp_path / "demo" / "index.json").read_text(encoding="utf-8"))
    assert "report-1" in index_payload["reports"]
    assert "agent-final" in index_payload["agents"]
    report_entry = index_payload["reports"]["report-1"]
    assert report_entry["reasoning_path"].endswith("reasoning.json")
    agent_entry = index_payload["agents"]["agent-final"]
    assert agent_entry["plan_path"].endswith("plan.json")


def test_build_replay_plan_exposes_reasoning_hints(tmp_path: Path) -> None:
    manager = ProjectFolderManager(tmp_path)
    persona = Persona(name="Strategist")
    record = ChatSessionRecord(
        persona=persona,
        skills_used=["internet_search"],
        input_prompt="Draft a market overview.",
        output_text="Overview ready.",
        reasoning=build_reasoning("strategy"),
    )

    agent_record = manager.ingest_chat("market", record)

    plan = manager.build_replay_plan("market", agent_record.agent_id)
    assert isinstance(plan, AgentReplayPlan)
    assert plan.agent_id == agent_record.agent_id
    assert plan.input_prompt == "Draft a market overview."
    assert plan.expected_output == "Overview ready."
    assert len(plan.hints) == 2
    assert plan.hints[0].instruction == "strategy input 0"
    assert plan.hints[0].expected == "strategy output 0"

    persisted_plan = manager.load_agent_plan("market", agent_record.agent_id)
    assert persisted_plan.hints[1].instruction == "strategy input 1"

    plan_markdown_path = tmp_path / "market" / "agents" / f"{agent_record.agent_id}.plan.md"
    assert plan_markdown_path.read_text(encoding="utf-8").startswith("# Agent Replay Plan")
