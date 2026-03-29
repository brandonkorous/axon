import type { CodeSpecialist } from "../stores/workerStore";

export interface SpecialistInfo {
  id: CodeSpecialist;
  label: string;
  description: string;
  icon: string;
  color: string;
}

export const CODE_SPECIALISTS: SpecialistInfo[] = [
  {
    id: "general",
    label: "General",
    description: "Polyglot coder — works across any stack",
    icon: "M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z",
    color: "#10B981",
  },
  {
    id: "python_backend",
    label: "Python Backend",
    description: "FastAPI, Django, Flask — async Python, SQLAlchemy, pytest",
    icon: "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z",
    color: "#3776AB",
  },
  {
    id: "fastify_backend",
    label: "Fastify Backend",
    description: "Fastify, Express — Node.js APIs, Prisma/Drizzle, TypeScript",
    icon: "M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4",
    color: "#000000",
  },
  {
    id: "nextjs",
    label: "Next.js",
    description: "App Router — RSC, server actions, middleware, ISR/SSG",
    icon: "M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z",
    color: "#171717",
  },
  {
    id: "vite_react",
    label: "Vite + React",
    description: "Vite SPA — Zustand, TanStack, Tailwind, client-side routing",
    icon: "M13 10V3L4 14h7v7l9-11h-7z",
    color: "#646CFF",
  },
  {
    id: "dotnet_backend",
    label: ".NET Backend",
    description: "ASP.NET Core — minimal APIs, EF Core, DI, middleware",
    icon: "M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01",
    color: "#512BD4",
  },
  {
    id: "dotnet_frontend",
    label: ".NET Frontend",
    description: "Blazor & Razor — component lifecycle, SignalR",
    icon: "M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zm0 8a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zm12 0a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z",
    color: "#512BD4",
  },
];

export const SPECIALIST_MAP = Object.fromEntries(
  CODE_SPECIALISTS.map((s) => [s.id, s]),
) as Record<CodeSpecialist, SpecialistInfo>;
