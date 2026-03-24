"""Tests for axon.vault.wikilinks — wikilink parsing, resolution, and insertion."""

from __future__ import annotations

import pytest

from axon.vault.wikilinks import WikiLink, add_wikilink, extract_wikilinks, resolve_wikilink


class TestExtractWikilinks:
    def test_simple_target(self):
        links = extract_wikilinks("See [[decisions/pricing]] for details.")
        assert len(links) == 1
        assert links[0].target == "decisions/pricing"
        assert links[0].display is None
        assert links[0].line_number == 1

    def test_target_with_display_text(self):
        links = extract_wikilinks("Check [[decisions/pricing|the pricing doc]].")
        assert len(links) == 1
        assert links[0].target == "decisions/pricing"
        assert links[0].display == "the pricing doc"

    def test_multiple_links_on_one_line(self):
        links = extract_wikilinks("See [[alpha]] and [[beta]] here.")
        assert len(links) == 2
        assert links[0].target == "alpha"
        assert links[1].target == "beta"

    def test_multiple_links_on_separate_lines(self):
        content = "Line with [[first]].\nAnother line with [[second]]."
        links = extract_wikilinks(content)
        assert len(links) == 2
        assert links[0].line_number == 1
        assert links[1].line_number == 2

    def test_no_links(self):
        links = extract_wikilinks("Plain text with no links at all.")
        assert links == []

    def test_whitespace_in_target_stripped(self):
        links = extract_wikilinks("See [[ spaced target ]] here.")
        assert len(links) == 1
        assert links[0].target == "spaced target"

    def test_display_text_stripped(self):
        links = extract_wikilinks("See [[target | display text ]].")
        assert len(links) == 1
        assert links[0].display == "display text"

    def test_context_captured(self):
        links = extract_wikilinks("prefix text [[target]] suffix text", context_chars=10)
        assert len(links) == 1
        assert "target" in links[0].context

    def test_nested_brackets_not_matched(self):
        # [[outer [[inner]]]] should not match "outer [[inner"
        links = extract_wikilinks("[[valid]]")
        assert len(links) == 1
        assert links[0].target == "valid"

    def test_empty_content(self):
        links = extract_wikilinks("")
        assert links == []


class TestResolveWikilink:
    def test_exact_path_from_vault_root(self, tmp_path):
        (tmp_path / "decisions").mkdir()
        (tmp_path / "decisions" / "pricing.md").write_text("content")
        result = resolve_wikilink("decisions/pricing", tmp_path)
        assert result == tmp_path / "decisions" / "pricing.md"

    def test_exact_path_with_md_suffix(self, tmp_path):
        (tmp_path / "notes.md").write_text("content")
        result = resolve_wikilink("notes.md", tmp_path)
        assert result == tmp_path / "notes.md"

    def test_relative_to_current_file(self, tmp_path):
        (tmp_path / "branch").mkdir()
        (tmp_path / "branch" / "sibling.md").write_text("content")
        current = tmp_path / "branch" / "current.md"
        result = resolve_wikilink("sibling", tmp_path, current_file=current)
        assert result == tmp_path / "branch" / "sibling.md"

    def test_filename_match_anywhere(self, tmp_path):
        (tmp_path / "deep" / "nested").mkdir(parents=True)
        (tmp_path / "deep" / "nested" / "target.md").write_text("content")
        result = resolve_wikilink("target", tmp_path)
        assert result == tmp_path / "deep" / "nested" / "target.md"

    def test_not_found_returns_none(self, tmp_path):
        result = resolve_wikilink("nonexistent", tmp_path)
        assert result is None

    def test_exact_path_preferred_over_filename_match(self, tmp_path):
        # Create both an exact-path match and a filename match
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "readme.md").write_text("exact")
        (tmp_path / "other").mkdir()
        (tmp_path / "other" / "readme.md").write_text("filename")
        result = resolve_wikilink("docs/readme", tmp_path)
        assert result == tmp_path / "docs" / "readme.md"


class TestAddWikilink:
    def test_append_to_end(self):
        content = "Some content."
        result = add_wikilink(content, "new-link")
        assert "[[new-link]]" in result
        assert result.endswith("- [[new-link]]\n")

    def test_deduplication(self):
        content = "Some content.\n- [[existing-link]]\n"
        result = add_wikilink(content, "existing-link")
        assert result == content  # Unchanged

    def test_add_to_section(self):
        content = "# Intro\nText.\n## Related\n- [[old-link]]\n## Other\nMore text."
        result = add_wikilink(content, "new-link", section="Related")
        assert "- [[new-link]]" in result
        # New link should appear after existing list items under Related
        lines = result.split("\n")
        related_idx = next(i for i, l in enumerate(lines) if "## Related" in l)
        new_link_idx = next(i for i, l in enumerate(lines) if "[[new-link]]" in l)
        old_link_idx = next(i for i, l in enumerate(lines) if "[[old-link]]" in l)
        assert new_link_idx > old_link_idx
        assert new_link_idx > related_idx

    def test_add_to_section_no_existing_items(self):
        content = "# Intro\nText.\n## Links\n## Other\nMore text."
        result = add_wikilink(content, "first-link", section="Links")
        assert "- [[first-link]]" in result
        lines = result.split("\n")
        links_idx = next(i for i, l in enumerate(lines) if "## Links" in l)
        new_link_idx = next(i for i, l in enumerate(lines) if "[[first-link]]" in l)
        assert new_link_idx == links_idx + 1

    def test_section_not_found_appends_to_end(self):
        content = "# Intro\nText."
        result = add_wikilink(content, "fallback-link", section="Nonexistent")
        assert "- [[fallback-link]]" in result
        assert result.endswith("- [[fallback-link]]\n")

    def test_section_match_case_insensitive(self):
        content = "## related links\n- [[old]]\n"
        result = add_wikilink(content, "new", section="Related Links")
        assert "- [[new]]" in result
