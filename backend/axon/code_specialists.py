"""Code specialist definitions — expert coder profiles for worker agents.

Each specialist carries detection rules (to auto-identify from a codebase)
and points to a comprehensive instructions template that gets written into
the worker's vault as instructions.md.
"""

from __future__ import annotations

import logging
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)

# Instruction templates live alongside this module
INSTRUCTIONS_DIR = Path(__file__).parent / "specialist_instructions"


class CodeSpecialist(str, Enum):
    GENERAL = "general"
    PYTHON_BACKEND = "python_backend"
    FASTIFY_BACKEND = "fastify_backend"
    NEXTJS = "nextjs"
    VITE_REACT = "vite_react"
    DOTNET_BACKEND = "dotnet_backend"
    DOTNET_FRONTEND = "dotnet_frontend"


# ── Metadata ────────────────────────────────────────────────────────

SPECIALIST_LABELS: dict[CodeSpecialist, str] = {
    CodeSpecialist.GENERAL: "General",
    CodeSpecialist.PYTHON_BACKEND: "Python Backend",
    CodeSpecialist.FASTIFY_BACKEND: "Fastify Backend",
    CodeSpecialist.NEXTJS: "Next.js",
    CodeSpecialist.VITE_REACT: "Vite + React",
    CodeSpecialist.DOTNET_BACKEND: ".NET Backend",
    CodeSpecialist.DOTNET_FRONTEND: ".NET Frontend",
}

SPECIALIST_DESCRIPTIONS: dict[CodeSpecialist, str] = {
    CodeSpecialist.GENERAL: "General-purpose coder — works across any stack",
    CodeSpecialist.PYTHON_BACKEND: "FastAPI, Django, Flask — async Python, SQLAlchemy, Alembic, pytest",
    CodeSpecialist.FASTIFY_BACKEND: "Fastify, Express — Node.js APIs, Prisma/Drizzle, TypeScript",
    CodeSpecialist.NEXTJS: "Next.js App Router — RSC, server actions, middleware, ISR/SSG",
    CodeSpecialist.VITE_REACT: "Vite + React SPA — Zustand, TanStack, Tailwind, client-side routing",
    CodeSpecialist.DOTNET_BACKEND: "ASP.NET Core — minimal APIs, EF Core, DI, middleware pipeline",
    CodeSpecialist.DOTNET_FRONTEND: "Blazor & Razor — component lifecycle, SignalR, .NET frontend",
}

SPECIALIST_COLORS: dict[CodeSpecialist, str] = {
    CodeSpecialist.GENERAL: "#10B981",
    CodeSpecialist.PYTHON_BACKEND: "#3776AB",
    CodeSpecialist.FASTIFY_BACKEND: "#000000",
    CodeSpecialist.NEXTJS: "#171717",
    CodeSpecialist.VITE_REACT: "#646CFF",
    CodeSpecialist.DOTNET_BACKEND: "#512BD4",
    CodeSpecialist.DOTNET_FRONTEND: "#512BD4",
}

# ── Detection rules ─────────────────────────────────────────────────
# Each rule is a list of (file_or_glob, weight) pairs. The specialist
# with the highest total weight wins. Globs are checked with Path.glob
# against the codebase root.

_DETECTION_RULES: dict[CodeSpecialist, list[tuple[str, float]]] = {
    CodeSpecialist.NEXTJS: [
        ("next.config.js", 10),
        ("next.config.mjs", 10),
        ("next.config.ts", 10),
        ("app/layout.tsx", 5),
        ("app/layout.jsx", 5),
        ("app/page.tsx", 3),
        ("src/app/layout.tsx", 5),
        ("src/app/page.tsx", 3),
        ("pages/_app.tsx", 4),
        ("pages/_app.jsx", 4),
    ],
    CodeSpecialist.VITE_REACT: [
        ("vite.config.ts", 10),
        ("vite.config.js", 10),
        ("vite.config.mjs", 10),
        ("src/main.tsx", 3),
        ("src/main.jsx", 3),
        ("src/App.tsx", 2),
        ("index.html", 1),  # weak — many things have this
    ],
    CodeSpecialist.FASTIFY_BACKEND: [
        ("fastify", 0),  # package.json dependency — checked separately
        ("src/server.ts", 2),
        ("src/app.ts", 1),
        ("src/routes", 1),
        ("drizzle.config.ts", 3),
        ("prisma/schema.prisma", 3),
    ],
    CodeSpecialist.PYTHON_BACKEND: [
        ("pyproject.toml", 5),
        ("requirements.txt", 3),
        ("setup.py", 3),
        ("manage.py", 8),  # Django
        ("alembic.ini", 5),
        ("alembic/", 4),
        ("app/main.py", 3),  # FastAPI convention
        ("src/main.py", 2),
    ],
    CodeSpecialist.DOTNET_BACKEND: [
        ("*.csproj", 5),
        ("*.sln", 3),
        ("Program.cs", 4),
        ("appsettings.json", 3),
        ("Controllers/", 3),
        ("Startup.cs", 4),
    ],
    CodeSpecialist.DOTNET_FRONTEND: [
        ("_Imports.razor", 10),
        ("App.razor", 8),
        ("Pages/*.razor", 5),
        ("Components/*.razor", 5),
        ("wwwroot/", 2),
    ],
}


def detect_specialist(codebase_path: str) -> tuple[CodeSpecialist, dict[str, float]]:
    """Scan a codebase directory and return the best-matching specialist.

    Returns (specialist, scores) where scores maps each evaluated
    specialist to its total weight. If nothing matches, returns GENERAL.
    """
    root = Path(codebase_path)
    if not root.is_dir():
        return CodeSpecialist.GENERAL, {}

    scores: dict[str, float] = {}

    for specialist, rules in _DETECTION_RULES.items():
        total = 0.0
        for pattern, weight in rules:
            if weight == 0:
                continue  # placeholder for dependency checks
            target = root / pattern
            # Direct file/dir check
            if target.exists():
                total += weight
                continue
            # Glob check (for patterns with wildcards)
            if "*" in pattern:
                matches = list(root.glob(pattern))
                if matches:
                    total += weight
        scores[specialist.value] = total

    # Bonus: check package.json for framework-specific dependencies
    pkg_json = root / "package.json"
    if pkg_json.exists():
        try:
            import json
            pkg = json.loads(pkg_json.read_text(encoding="utf-8"))
            all_deps = {
                **pkg.get("dependencies", {}),
                **pkg.get("devDependencies", {}),
            }
            if "fastify" in all_deps:
                scores.setdefault(CodeSpecialist.FASTIFY_BACKEND.value, 0)
                scores[CodeSpecialist.FASTIFY_BACKEND.value] += 10
            if "express" in all_deps and "fastify" not in all_deps:
                scores.setdefault(CodeSpecialist.FASTIFY_BACKEND.value, 0)
                scores[CodeSpecialist.FASTIFY_BACKEND.value] += 6
            if "next" in all_deps:
                scores.setdefault(CodeSpecialist.NEXTJS.value, 0)
                scores[CodeSpecialist.NEXTJS.value] += 8
            if "vite" in all_deps:
                scores.setdefault(CodeSpecialist.VITE_REACT.value, 0)
                scores[CodeSpecialist.VITE_REACT.value] += 5
            if "react" in all_deps and "next" not in all_deps:
                scores.setdefault(CodeSpecialist.VITE_REACT.value, 0)
                scores[CodeSpecialist.VITE_REACT.value] += 2
        except Exception:
            pass

    # Bonus: check pyproject.toml for Python framework deps
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        try:
            content = pyproject.read_text(encoding="utf-8").lower()
            if "fastapi" in content:
                scores.setdefault(CodeSpecialist.PYTHON_BACKEND.value, 0)
                scores[CodeSpecialist.PYTHON_BACKEND.value] += 8
            if "django" in content:
                scores.setdefault(CodeSpecialist.PYTHON_BACKEND.value, 0)
                scores[CodeSpecialist.PYTHON_BACKEND.value] += 8
            if "flask" in content:
                scores.setdefault(CodeSpecialist.PYTHON_BACKEND.value, 0)
                scores[CodeSpecialist.PYTHON_BACKEND.value] += 6
            if "sqlalchemy" in content or "alembic" in content:
                scores.setdefault(CodeSpecialist.PYTHON_BACKEND.value, 0)
                scores[CodeSpecialist.PYTHON_BACKEND.value] += 3
        except Exception:
            pass

    # Bonus: check .csproj for Blazor/Razor indicators
    for csproj in root.glob("**/*.csproj"):
        try:
            content = csproj.read_text(encoding="utf-8").lower()
            if "microsoft.aspnetcore.components" in content or "blazor" in content:
                scores.setdefault(CodeSpecialist.DOTNET_FRONTEND.value, 0)
                scores[CodeSpecialist.DOTNET_FRONTEND.value] += 10
            elif "microsoft.aspnetcore" in content:
                scores.setdefault(CodeSpecialist.DOTNET_BACKEND.value, 0)
                scores[CodeSpecialist.DOTNET_BACKEND.value] += 5
        except Exception:
            pass
        break  # Only check first csproj

    # Pick winner
    if not scores or max(scores.values()) == 0:
        return CodeSpecialist.GENERAL, scores

    winner = max(scores, key=lambda k: scores[k])
    if scores[winner] < 3:  # minimum threshold
        return CodeSpecialist.GENERAL, scores

    return CodeSpecialist(winner), scores


def get_specialist_instructions(specialist: CodeSpecialist) -> str:
    """Load the instructions.md template for a specialist."""
    path = INSTRUCTIONS_DIR / f"{specialist.value}.md"
    if not path.exists():
        path = INSTRUCTIONS_DIR / "general.md"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")
