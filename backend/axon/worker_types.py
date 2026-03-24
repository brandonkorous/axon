"""Worker type definitions — the kinds of workers Axon can run."""

from __future__ import annotations

from enum import Enum


class WorkerType(str, Enum):
    CODE = "code"
    DOCUMENTS = "documents"
    EMAIL = "email"
    IMAGES = "images"
    BROWSER = "browser"
    SHELL = "shell"


WORKER_TYPE_LABELS: dict[WorkerType, str] = {
    WorkerType.CODE: "Code",
    WorkerType.DOCUMENTS: "Documents",
    WorkerType.EMAIL: "Email",
    WorkerType.IMAGES: "Images",
    WorkerType.BROWSER: "Browser",
    WorkerType.SHELL: "Shell",
}

WORKER_TYPE_DESCRIPTIONS: dict[WorkerType, str] = {
    WorkerType.CODE: "Execute code changes via Claude Code CLI",
    WorkerType.DOCUMENTS: "PDF/DOCX parsing, analysis, and generation",
    WorkerType.EMAIL: "Gmail, O365, Resend read/send",
    WorkerType.IMAGES: "Image analysis and manipulation",
    WorkerType.BROWSER: "Playwright web automation",
    WorkerType.SHELL: "Direct shell command execution",
}
