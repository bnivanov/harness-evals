/**
 * Explicitly loaded OMP extension (`--extension` / `--hook`).
 * Intercepts tool_call and fail-closes on workspace escapes and network/package fetch.
 */
import { appendFileSync, existsSync, mkdirSync, realpathSync } from "node:fs";
import { basename, dirname, isAbsolute, resolve, sep } from "node:path";

type ToolCallEvent = {
  toolName?: string;
  tool?: string;
  input?: Record<string, unknown>;
};

type GuardDecision = { block: true; reason: string };

type ExtensionAPI = {
  on: (
    event: "tool_call" | string,
    handler: (
      event: ToolCallEvent,
      ctx?: unknown,
    ) => GuardDecision | void | Promise<GuardDecision | void>,
  ) => void;
};

const PATH_TOOLS: Record<string, true> = {
  read: true,
  write: true,
  edit: true,
  glob: true,
  grep: true,
};

const PATH_KEYS = ["path", "file", "filename", "target", "dest", "destination"] as const;

const NETWORK_COMMAND =
  /\b(?:curl|wget|nc|ncat|netcat|ssh|scp|rsync)\b/i;
const GIT_NETWORK =
  /\bgit(?:\s+\S+)*\s+(?:clone|fetch|pull)\b|\bgit(?:\s+\S+)*\s+remote\s+add\b/i;
const PACKAGE_FETCH =
  /\b(?:pip3?|python3?\s+-m\s+pip)\s+(?:install|download)\b|\bnpm\s+(?:install|i|ci|add)\b|\bgem\s+install\b/i;
const NETWORK_IMPORT =
  /\b(?:import|from)\s+(?:urllib|requests|httpx|socket|http|https|net)\b|\brequire\s*\(\s*['"](?:http|https|net|urllib|socket)['"]|\brequire\s+['"](?:net\/http|socket|open-uri|net\/https)['"]|\bfrom\s+['"](?:http|https|net|socket)(?:\/|['"])|\bfetch\s*\(/i;

const BASH_PATH_TOKEN =
  /(?:^|[\s"'=])(~(?:\/[^\s"']*)?|(?:\.\.\/)+[^\s"']*|\/[^\s"']+|\.\/[^\s"']+|[^\s"']+\/[^\s"']+)/g;

function workspaceFromEnv(): string {
  return (process.env.BENCHMARK_WORKSPACE ?? "").trim();
}

function isLocalUri(value: string): boolean {
  return /^local:\/\//i.test(value.trim());
}

const URI_SCHEME = /^([a-z][a-z0-9+.-]*):\/\//i;

/**
 * Harness-internal schemes (`skill://`, `artifact://`, `history://`, ...) resolve
 * inside the harness and never touch the workspace, so the path checks below
 * cannot see them. Only `file://` (canonicalized) and `local://` are allowed.
 */
function foreignUriScheme(value: string): string | undefined {
  const match = URI_SCHEME.exec(value.trim());
  if (!match) return undefined;
  const scheme = match[1].toLowerCase();
  return scheme === "file" ? undefined : scheme;
}

function isOrdinaryNonPath(value: string): boolean {
  const v = value.trim();
  if (!v || isLocalUri(v)) return true;
  if (v.includes("://")) return false;
  if (isAbsolute(v) || v.startsWith("~")) return false;
  if (v === ".." || v.startsWith("../") || v.startsWith("..\\") || v.startsWith(`..${sep}`)) {
    return false;
  }
  return !v.includes("/") && !v.includes("\\");
}

function canonicalize(raw: string, workspace: string): string {
  let value = raw.trim();
  if (value.toLowerCase().startsWith("file://")) {
    try {
      value = decodeURIComponent(new URL(value).pathname);
    } catch {
      value = value.slice("file://".length);
    }
  }
  const abs = resolve(workspace, value);
  const missing: string[] = [];
  let cursor = abs;
  while (true) {
    if (existsSync(cursor)) {
      try {
        const real = realpathSync(cursor);
        return missing.length === 0 ? real : resolve(real, ...missing.reverse());
      } catch {
        break;
      }
    }
    const parent = dirname(cursor);
    if (parent === cursor) break;
    missing.push(basename(cursor));
    cursor = parent;
  }
  return abs;
}

function isInsideWorkspace(canonical: string, workspace: string): boolean {
  let root = resolve(workspace);
  try {
    if (existsSync(workspace)) root = realpathSync(workspace);
  } catch {
    // Keep the resolved workspace path if realpath fails.
  }
  if (canonical === root) return true;
  const prefix = root.endsWith(sep) ? root : root + sep;
  return canonical.startsWith(prefix);
}

function pathOutsideReason(raw: string, workspace: string): string | undefined {
  const value = raw.trim();
  if (!value || isLocalUri(value) || isOrdinaryNonPath(value)) return undefined;
  const scheme = foreignUriScheme(value);
  if (scheme) return `blocked ${scheme}:// resource outside benchmark workspace`;
  if (!workspace) return "path outside benchmark workspace";
  const canonical = canonicalize(value, workspace);
  if (!isInsideWorkspace(canonical, workspace)) return "path outside benchmark workspace";
  return undefined;
}

function collectPathFields(input: Record<string, unknown> | undefined): string[] {
  if (!input) return [];
  const out: string[] = [];
  for (const key of PATH_KEYS) {
    const raw = input[key];
    if (typeof raw === "string") {
      for (const part of raw.split(";")) {
        if (part.trim()) out.push(part.trim());
      }
    } else if (Array.isArray(raw)) {
      for (const item of raw) {
        if (typeof item === "string") {
          for (const part of item.split(";")) {
            if (part.trim()) out.push(part.trim());
          }
        }
      }
    }
  }
  return out;
}

function logBlock(tool: string, reason: string, input: Record<string, unknown> | undefined): void {
  const logPath = (process.env.BENCHMARK_GUARD_LOG ?? "").trim();
  if (!logPath) return;
  try {
    mkdirSync(dirname(logPath), { recursive: true });
    appendFileSync(
      logPath,
      `${JSON.stringify({ ts: new Date().toISOString(), tool, reason, input: input ?? {} })}\n`,
      "utf8",
    );
  } catch {
    // Fail closed via the return value even if the audit log cannot be written.
  }
}

function block(
  tool: string,
  reason: string,
  input: Record<string, unknown> | undefined,
): GuardDecision {
  logBlock(tool, reason, input);
  return { block: true, reason };
}

function inspectPathTool(
  tool: string,
  input: Record<string, unknown> | undefined,
): GuardDecision | void {
  const workspace = workspaceFromEnv();
  for (const candidate of collectPathFields(input)) {
    const err = pathOutsideReason(candidate, workspace);
    if (err) return block(tool, err, input);
  }
}

function inspectBash(input: Record<string, unknown> | undefined): GuardDecision | void {
  const raw = input?.command ?? input?.cmd ?? input?.script;
  const command = typeof raw === "string" ? raw : Array.isArray(raw) ? raw.map(String).join(" ") : "";
  if (!command.trim()) return;
  if (NETWORK_COMMAND.test(command)) return block("bash", "blocked network command", input);
  if (GIT_NETWORK.test(command)) return block("bash", "blocked git network command", input);
  if (PACKAGE_FETCH.test(command)) return block("bash", "blocked package install", input);
  if (NETWORK_IMPORT.test(command)) return block("bash", "blocked network import", input);

  const workspace = workspaceFromEnv();
  BASH_PATH_TOKEN.lastIndex = 0;
  let m: RegExpExecArray | null;
  while ((m = BASH_PATH_TOKEN.exec(command))) {
    const token = m[1];
    if (!token || token.startsWith("-")) continue;
    const err = pathOutsideReason(token, workspace);
    if (err) return block("bash", err, input);
  }
}

export default function benchmarkGuard(pi: ExtensionAPI): void {
  pi.on("tool_call", (event) => {
    const tool = String(event.toolName ?? event.tool ?? "").trim().toLowerCase();
    const input = event.input && typeof event.input === "object" ? event.input : {};
    if (PATH_TOOLS[tool]) return inspectPathTool(tool, input);
    if (tool === "bash") return inspectBash(input);
  });
}
