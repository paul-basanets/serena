"""Tests for the ``SearchForPatternTool`` overflow shortening chain.

The snippet stage and, in particular, its position in the shortening chain were
previously untested. Test contributed by @AmirF194 in review of PR #1667.
"""

import logging
from unittest.mock import MagicMock

from serena.config.serena_config import SerenaConfig
from serena.project import Project
from serena.tools.file_tools import SearchForPatternTool


def test_search_for_pattern_snippet_stage(tmp_path):
    lines: list[str] = []
    for i in range(60):
        lines += [
            "filler above",
            "filler above",
            f"MATCHME item number {i:04d} " + "payload " * 6,
            "filler below",
            "filler below",
        ]
    (tmp_path / "data.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    project = Project.load(str(tmp_path), serena_config=SerenaConfig(gui_log_window=False, web_dashboard=False))
    agent = MagicMock()
    agent.get_active_project_or_raise.return_value = project
    tool = SearchForPatternTool(agent)

    def run(cap: int) -> str:
        return tool.apply(
            substring_pattern="MATCHME",
            context_lines_before=2,
            context_lines_after=2,
            restrict_search_to_code_files=False,
            max_answer_chars=cap,
        )

    # wide but overflowing cap: the snippet stage (line + matched text) is returned
    snippet = run(7000)
    assert "The answer is too long" in snippet
    assert '"text":' in snippet and "MATCHME item number 0000" in snippet
    assert "Match lines per file" not in snippet  # not the bare-line-numbers stage

    # tighter cap: the chain degrades past the snippet stage to bare line numbers
    bare = run(1000)
    assert "Match lines per file" in bare and '"text":' not in bare


def test_search_skips_binaries_quietly_and_still_reads_foreign_encodings(tmp_path, caplog):
    """
    Scanning non-code files sweeps up binary assets: they must be skipped without error-level noise
    (2023 such log entries in one real project), while files in another encoding stay searchable.
    """
    (tmp_path / "notes.txt").write_text("MATCHME utf-8\n", encoding="utf-8")
    (tmp_path / "legacy.txt").write_bytes("MATCHME José\n".encode("cp1252"))
    (tmp_path / "icon.png").write_bytes(b"\x89PNG\r\n\x1a\n" + bytes(range(256)) * 4)

    project = Project.load(str(tmp_path), serena_config=SerenaConfig(gui_log_window=False, web_dashboard=False))
    agent = MagicMock()
    agent.get_active_project_or_raise.return_value = project
    tool = SearchForPatternTool(agent)

    with caplog.at_level(logging.DEBUG):
        result = tool.apply(substring_pattern="MATCHME", restrict_search_to_code_files=False, max_answer_chars=100_000)

    assert "notes.txt" in result
    assert "legacy.txt" in result, "the encoding-detection fallback must keep non-UTF-8 files searchable"
    assert "icon.png" not in result
    assert [r.getMessage() for r in caplog.records if r.levelno >= logging.ERROR] == []
