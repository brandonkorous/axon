"""Tests for axon.worker_types — enum completeness."""

from __future__ import annotations

from axon.worker_types import (
    WORKER_TYPE_DESCRIPTIONS,
    WORKER_TYPE_LABELS,
    WorkerType,
)


class TestWorkerTypeCompleteness:
    def test_all_types_have_labels(self):
        for wt in WorkerType:
            assert wt in WORKER_TYPE_LABELS, f"{wt} missing from WORKER_TYPE_LABELS"

    def test_all_types_have_descriptions(self):
        for wt in WorkerType:
            assert wt in WORKER_TYPE_DESCRIPTIONS, f"{wt} missing from WORKER_TYPE_DESCRIPTIONS"

    def test_no_extra_labels(self):
        for key in WORKER_TYPE_LABELS:
            assert key in WorkerType.__members__.values(), f"extra label key: {key}"

    def test_no_extra_descriptions(self):
        for key in WORKER_TYPE_DESCRIPTIONS:
            assert key in WorkerType.__members__.values(), f"extra description key: {key}"

    def test_labels_are_nonempty_strings(self):
        for wt, label in WORKER_TYPE_LABELS.items():
            assert isinstance(label, str) and len(label) > 0, f"{wt} has empty label"

    def test_descriptions_are_nonempty_strings(self):
        for wt, desc in WORKER_TYPE_DESCRIPTIONS.items():
            assert isinstance(desc, str) and len(desc) > 0, f"{wt} has empty description"

    def test_enum_values_are_lowercase_strings(self):
        for wt in WorkerType:
            assert wt.value == wt.value.lower(), f"{wt} value is not lowercase"
