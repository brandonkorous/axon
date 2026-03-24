"""Tests for axon.vault.frontmatter — YAML frontmatter parsing and writing."""

from __future__ import annotations

import pytest

from axon.vault.frontmatter import (
    parse_frontmatter,
    read_file_with_frontmatter,
    write_file_with_frontmatter,
    write_frontmatter,
)


class TestParseFrontmatter:
    def test_valid_frontmatter(self):
        content = "---\ntitle: Hello\ntags: [a, b]\n---\nBody text here."
        meta, body = parse_frontmatter(content)
        assert meta["title"] == "Hello"
        assert meta["tags"] == ["a", "b"]
        assert "Body text here." in body

    def test_no_frontmatter(self):
        content = "Just a plain markdown file.\nNo frontmatter at all."
        meta, body = parse_frontmatter(content)
        assert meta == {}
        assert "Just a plain markdown file." in body

    def test_empty_frontmatter(self):
        content = "---\n---\nBody after empty frontmatter."
        meta, body = parse_frontmatter(content)
        assert meta == {}
        assert "Body after empty frontmatter." in body

    def test_special_chars_in_values(self):
        content = "---\ntitle: \"Colon: here & ampersand\"\nnote: 'Single quotes'\n---\nBody."
        meta, body = parse_frontmatter(content)
        assert "Colon: here & ampersand" in meta["title"]
        assert meta["note"] == "Single quotes"

    def test_numeric_and_boolean_values(self):
        content = "---\nconfidence: 0.85\nactive: true\ncount: 42\n---\nBody."
        meta, body = parse_frontmatter(content)
        assert meta["confidence"] == 0.85
        assert meta["active"] is True
        assert meta["count"] == 42

    def test_multiline_body_preserved(self):
        content = "---\ntitle: Test\n---\nLine 1\n\nLine 3\n- bullet"
        meta, body = parse_frontmatter(content)
        assert "Line 1" in body
        assert "Line 3" in body
        assert "- bullet" in body


class TestWriteFrontmatter:
    def test_basic_write(self):
        result = write_frontmatter({"title": "Hello"}, "Body text.")
        assert "---" in result
        assert "title: Hello" in result
        assert "Body text." in result

    def test_round_trip(self):
        original_meta = {"title": "Round Trip", "confidence": 0.75, "tags": ["a", "b"]}
        original_body = "This is the body.\n\nWith paragraphs."
        combined = write_frontmatter(original_meta, original_body)
        parsed_meta, parsed_body = parse_frontmatter(combined)
        assert parsed_meta["title"] == original_meta["title"]
        assert parsed_meta["confidence"] == original_meta["confidence"]
        assert parsed_meta["tags"] == original_meta["tags"]
        assert "This is the body." in parsed_body
        assert "With paragraphs." in parsed_body

    def test_empty_metadata_round_trip(self):
        combined = write_frontmatter({}, "Just body.")
        meta, body = parse_frontmatter(combined)
        assert meta == {}
        assert "Just body." in body

    def test_special_chars_round_trip(self):
        meta = {"title": "Test: colons & special < > chars"}
        combined = write_frontmatter(meta, "Body.")
        parsed_meta, _ = parse_frontmatter(combined)
        assert parsed_meta["title"] == meta["title"]


class TestFileIO:
    def test_read_write_file(self, tmp_path):
        filepath = tmp_path / "test.md"
        meta = {"title": "File Test", "confidence": 0.9}
        body = "File body content."
        write_file_with_frontmatter(str(filepath), meta, body)

        read_meta, read_body = read_file_with_frontmatter(str(filepath))
        assert read_meta["title"] == "File Test"
        assert read_meta["confidence"] == 0.9
        assert "File body content." in read_body

    def test_read_nonexistent_file_raises(self):
        with pytest.raises(FileNotFoundError):
            read_file_with_frontmatter("/nonexistent/path.md")
