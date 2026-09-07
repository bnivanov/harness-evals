/**
 * Explicitly loaded OMP extension (`--extension` / `--hook`).
 * Intercepts tool_call and fail-closes on foreign URI schemes,
 * access to quarantined benchmark directories/solutions,
 * access to the project repository outside the workspace/scratch,
 * agent configuration homes, unquarantined temporary directories,
 * and network/package fetch.
 */
import { appendFileSync, existsSync, mkdirSync, realpathSync } from "node:fs";
import { basename, dirname, isAbsolute, resolve, sep } from "node:path";

export type ToolCallEvent = {
  toolName?: string;
  tool?: string;
  input?: Record<string, unknown>;
};

export type GuardDecision = { block: true; reason: string };

export type ExtensionAPI = {
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

// Anchored network command pattern matching CLI execution including subshells, backticks, and pipes
const NETWORK_COMMAND =
  /(?:^|[;&|(`$\s{])(?:curl|wget|ssh|scp|rsync|ncat|netcat|socat|telnet)\b|(?:^|[;&|(`$\s{])nc\s+-[a-zA-Z0-9]|(?:^|[;&|(`$\s{])nc\s+[0-9a-zA-Z.-]+\s+\d+/i;
const GIT_NETWORK =
  /\bgit(?:\s+\S+)*\s+(?:clone|fetch|pull)\b|\bgit(?:\s+\S+)*\s+remote\s+add\b/i;
const PACKAGE_FETCH =
  /\b(?:pip3?|python3?\s+-m\s+pip)\s+(?:install|download)\b|\bnpm\s+(?:install|i|ci|add)\b|\bgem\s+install\b/i;
const NETWORK_IMPORT =
  /\b(?:import|from)\s+(?:urllib|requests|httpx|socket|http|https|net)\b|\brequire\s*\(\s*['"](?:http|https|net|urllib|socket)['"]|\brequire\s+['"](?:net\/http|socket|open-uri|net\/https)['"]|\bfrom\s+['"](?:http|https|net|socket)(?:\/|['"])|\bfetch\s*\(/i;

const BASH_PATH_TOKEN =
  /(?:^|[\s"'=])(~(?:\/[^\s"']*)?|\$(?:\{HOME\}|HOME)(?:\/[^\s"']*)?|\$(?:\{TMPDIR\}|TMPDIR)(?:\/[^\s"']*)?|(?:\.\.\/)+[^\s"']*|\/[^\s"']+|\.\/[^\s"']+|[^\s"']+\/[^\s"']+)/g;

const SAFE_OS_READ_PREFIXES = [
  "/usr/",
  "/bin/",
  "/sbin/",
  "/lib/",
  "/System/",
  "/Library/",
  "/opt/homebrew/",
  "/etc/",
  "/private/etc/",
  "/dev/",
  "/private/dev/",
];

function workspaceFromEnv(): string {
  return (process.env.BENCHMARK_WORKSPACE ?? "").trim();
}

function scratchDirFromEnv(): string {
  // Fail-closed: only return an explicitly provisioned private scratch directory.
  return (process.env.BENCHMARK_SCRATCH_DIR ?? "").trim();
}

function projectRootFromEnv(): string {
  return (process.env.PROJECT_ROOT ?? "").trim();
}

function isLocalUri(value: string): boolean {
  return /^local:\/\//i.test(value.trim());
}

const URI_SCHEME = /^([a-z][a-z0-9+.-]*):\/\//i;

/**
 * Harness-internal schemes (`skill://`, `artifact://`, `history://`, ...) resolve
 * inside the harness and never touch the workspace, so file system checks
 * cannot see them. Only `file://` (canonicalized) and `local://` are allowed.
 */
export function foreignUriScheme(value: string): string | undefined {
  const match = URI_SCHEME.exec(value.trim());
  if (!match) return undefined;
  const scheme = match[1].toLowerCase();
  return (scheme === "file" || scheme === "local") ? undefined : scheme;
}

export function isOrdinaryNonPath(value: string): boolean {
  const v = value.trim();
  if (!v || isLocalUri(v)) return true;
  if (v.includes("://")) return false;
  if (isAbsolute(v) || v.startsWith("~") || v.startsWith("$HOME") || v.startsWith("${HOME}") || v.startsWith("$TMPDIR") || v.startsWith("${TMPDIR}")) return false;
  if (v === ".." || v.startsWith("../") || v.startsWith("..\\") || v.startsWith(`..${sep}`)) {
    return false;
  }
  return !v.includes("/") && !v.includes("\\");
}

export function canonicalize(raw: string, workspace: string): string {
  let value = raw.trim();
  if (value.toLowerCase().startsWith("file://")) {
    try {
      value = decodeURIComponent(new URL(value).pathname);
    } catch {
      value = value.slice("file://".length);
    }
  }
  const home = process.env.HOME || "";
  if (home) {
    if (value === "~" || value.startsWith("~/")) {
      value = resolve(home, value.slice(2));
    } else if (value === "$HOME" || value.startsWith("$HOME/")) {
      value = resolve(home, value.slice(6));
    } else if (value === "${HOME}" || value.startsWith("${HOME}/")) {
      value = resolve(home, value.slice(8));
    }
  }
  const scratch = process.env.BENCHMARK_SCRATCH_DIR || process.env.TMPDIR || "";
  if (scratch) {
    if (value === "$TMPDIR" || value.startsWith("$TMPDIR/")) {
      value = resolve(scratch, value.slice(8));
    } else if (value === "${TMPDIR}" || value.startsWith("${TMPDIR}/")) {
      value = resolve(scratch, value.slice(10));
    }
  }
  const abs = resolve(workspace || ".", value);
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

export function isSubpath(target: string, parentDir: string): boolean {
  if (!parentDir || !target) return false;
  let parent = resolve(parentDir);
  try {
    if (existsSync(parentDir)) parent = realpathSync(parentDir);
  } catch {}
  let child = resolve(target);
  try {
    if (existsSync(target)) child = realpathSync(target);
  } catch {}
  if (child === parent) return true;
  const prefix = parent.endsWith(sep) ? parent : parent + sep;
  return child.startsWith(prefix);
}

export function isAllowedReadTarget(canonical: string, workspace: string, scratchDir: string): boolean {
  if (workspace && isSubpath(canonical, workspace)) return true;
  if (scratchDir && isSubpath(canonical, scratchDir)) return true;
  for (const prefix of SAFE_OS_READ_PREFIXES) {
    if (canonical.startsWith(prefix)) return true;
  }
  return false;
}

/**
 * Returns a rejection reason if the candidate path violates benchmark quarantine:
 * - Foreign URI schemes (skill://, artifact://, history://, etc.)
 * - Quarantined benchmark directories (oracle solutions, held-out tests, other tasks)
 * - Project repository files outside the active workspace and private scratch directory
 * - Agent configuration and history homes (~/.omp, ~/.codex, ~/.gemini, etc.)
 * - Location rule: any file under temporary hierarchies (/tmp, /private/tmp, /var/folders, /private/var/folders)
 *   that is NOT strictly inside the active workspace or private scratchDir.
 */
export function forbiddenTargetReason(
  raw: string,
  workspace: string,
  scratchDir: string,
  projectRoot: string,
): string | undefined {
  const value = raw.trim();
  if (!value || isLocalUri(value)) return undefined;

  const scheme = foreignUriScheme(value);
  if (scheme) return `blocked ${scheme}:// resource outside benchmark workspace`;

  if (isOrdinaryNonPath(value)) return undefined;

  const canonical = canonicalize(value, workspace);

  // 1. Quarantined benchmark directories (oracle solutions, tasks)
  if (/\/benchmarks\/aider-python\/(?:oracle|tasks)\b/i.test(canonical) || /\/benchmarks\/aider-python\/(?:oracle|tasks)\b/i.test(value)) {
    // If the canonical path is strictly inside the assigned workspace, it's allowed
    if (workspace && isSubpath(canonical, workspace)) {
      return undefined;
    }
    return "access to quarantined benchmark directory";
  }

  // 2. Project repository tree outside workspace and scratch
  if (projectRoot && isSubpath(canonical, projectRoot)) {
    if (workspace && isSubpath(canonical, workspace)) return undefined;
    if (scratchDir && isSubpath(canonical, scratchDir)) return undefined;
    return "access to project repository outside benchmark workspace";
  }

  // 3. Agent configuration / session directories
  const home = process.env.HOME || "";
  if (home) {
    const agentHomes = [
      resolve(home, ".omp"),
      resolve(home, ".codex"),
      resolve(home, ".gemini"),
      resolve(home, ".grok"),
      resolve(home, ".cursor"),
      resolve(home, ".t3"),
    ];
    for (const aHome of agentHomes) {
      if (isSubpath(canonical, aHome)) {
        return "access to agent configuration directory";
      }
    }
  }

  // 4. Location-based quarantine rule:
  // Deny any path under temporary hierarchies (/tmp, /var/folders) unless strictly inside workspace or scratchDir
  const tempRoots = [
    "/tmp",
    "/private/tmp",
    "/var/folders",
    "/private/var/folders",
  ];
  for (const root of tempRoots) {
    if (isSubpath(canonical, root)) {
      const inWs = workspace && isSubpath(canonical, workspace);
      const inScratch = scratchDir && isSubpath(canonical, scratchDir);
      if (!inWs && !inScratch) {
        return "path outside benchmark workspace";
      }
    }
  }

  return undefined;
}

export function collectPathFields(tool: string, input: Record<string, unknown> | undefined): string[] {
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

  // B1: Support OMP hashline edit tool input ([PATH#TAG] headers and MV DEST)
  if (tool === "edit") {
    const rawInput = input.input ?? input.patch ?? input.script;
    if (typeof rawInput === "string") {
      const headerRegex = /^\s*\[([^\n#\]]+)(?:#[0-9a-fA-F]+)?\]/mg;
      let m: RegExpExecArray | null;
      while ((m = headerRegex.exec(rawInput))) {
        const path = m[1].trim();
        if (path) out.push(path);
      }
      const mvRegex = /^\s*MV\s+([^\n]+)/mg;
      while ((m = mvRegex.exec(rawInput))) {
        const path = m[1].trim().replace(/^["']|["']$/g, "");
        if (path) out.push(path);
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

export function inspectPathTool(
  tool: string,
  input: Record<string, unknown> | undefined,
): GuardDecision | void {
  const workspace = workspaceFromEnv();
  const scratchDir = scratchDirFromEnv();
  const projectRoot = projectRootFromEnv();

  const candidates = collectPathFields(tool, input);
  for (const candidate of candidates) {
    const err = forbiddenTargetReason(candidate, workspace, scratchDir, projectRoot);
    if (err) return block(tool, err, input);

    const canonical = canonicalize(candidate, workspace);

    // Write / edit tools: strictly positive confinement to workspace or scratchDir
    if (tool === "write" || tool === "edit") {
      const inWorkspace = workspace && isSubpath(canonical, workspace);
      const inScratch = scratchDir && isSubpath(canonical, scratchDir);
      if (!inWorkspace && !inScratch) {
        return block(tool, "path outside benchmark workspace", input);
      }
    }

    // Read / glob / grep tools: positive confinement to workspace, scratchDir, or safe system OS prefixes
    if (tool === "read" || tool === "glob" || tool === "grep") {
      if (!isAllowedReadTarget(canonical, workspace, scratchDir)) {
        return block(tool, "path outside benchmark workspace", input);
      }
    }
  }
}

export function inspectBash(input: Record<string, unknown> | undefined): GuardDecision | void {
  const raw = input?.command ?? input?.cmd ?? input?.script;
  const command = typeof raw === "string" ? raw : Array.isArray(raw) ? raw.map(String).join(" ") : "";
  if (!command.trim()) return;
  if (NETWORK_COMMAND.test(command)) return block("bash", "blocked network command", input);
  if (GIT_NETWORK.test(command)) return block("bash", "blocked git network command", input);
  if (PACKAGE_FETCH.test(command)) return block("bash", "blocked package install", input);
  if (NETWORK_IMPORT.test(command)) return block("bash", "blocked network import", input);

  const workspace = workspaceFromEnv();
  const scratchDir = scratchDirFromEnv();
  const projectRoot = projectRootFromEnv();

  BASH_PATH_TOKEN.lastIndex = 0;
  let m: RegExpExecArray | null;
  while ((m = BASH_PATH_TOKEN.exec(command))) {
    const token = m[1];
    if (!token || token.startsWith("-")) continue;
    const err = forbiddenTargetReason(token, workspace, scratchDir, projectRoot);
    if (err) return block("bash", err, input);

    // B2: Positive confinement on bash path tokens pointing to files
    if (
      token.startsWith("/") ||
      token.startsWith("~") ||
      token.startsWith("$HOME") ||
      token.startsWith("${HOME}") ||
      token.startsWith("$TMPDIR") ||
      token.startsWith("${TMPDIR}") ||
      token.startsWith("../")
    ) {
      const canonical = canonicalize(token, workspace);
      if (!isAllowedReadTarget(canonical, workspace, scratchDir)) {
        return block("bash", "path outside benchmark workspace", input);
      }
    }
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
