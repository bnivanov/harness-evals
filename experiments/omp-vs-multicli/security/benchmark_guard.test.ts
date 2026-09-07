import { afterEach, beforeEach, expect, test } from "bun:test";
import { mkdtempSync, readFileSync, rmSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import benchmarkGuard from "./benchmark_guard";

type ToolCallEvent = {
  toolName?: string;
  tool?: string;
  input?: Record<string, unknown>;
};

type GuardDecision = { block: true; reason: string } | void;

type Handler = (event: ToolCallEvent, ctx?: unknown) => GuardDecision | Promise<GuardDecision>;

const temps: string[] = [];

function tempDir(prefix: string): string {
  const dir = mkdtempSync(join(tmpdir(), prefix));
  temps.push(dir);
  return dir;
}

function installGuard(): Handler {
  const handlers = new Map<string, Handler>();
  benchmarkGuard({
    on: (event, handler) => {
      handlers.set(event, handler as Handler);
    },
  });
  const handler = handlers.get("tool_call");
  if (!handler) throw new Error("tool_call interceptor was not registered");
  return handler;
}

function blockedLines(logPath: string): Array<Record<string, unknown>> {
  const raw = readFileSync(logPath, "utf8").trim();
  if (!raw) return [];
  return raw.split("\n").map((line) => JSON.parse(line) as Record<string, unknown>);
}

let workspace = "";
let logPath = "";
let oracleDir = "";
let handler: Handler;

beforeEach(() => {
  workspace = tempDir("bench-ws-");
  oracleDir = tempDir("bench-oracle-");
  logPath = join(tempDir("bench-log-"), "guard.ndjson");
  writeFileSync(join(workspace, "public_test.py"), "import unittest\n");
  writeFileSync(join(oracleDir, "secret.py"), "ANSWER = 42\n");
  process.env.BENCHMARK_WORKSPACE = workspace;
  process.env.BENCHMARK_GUARD_LOG = logPath;
  handler = installGuard();
});

afterEach(() => {
  delete process.env.BENCHMARK_WORKSPACE;
  delete process.env.BENCHMARK_GUARD_LOG;
  for (const dir of temps.splice(0)) {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("allows public unittest and local:// reads", async () => {
  expect(
    await handler({
      toolName: "bash",
      input: { command: "python3 -m unittest public_test.py" },
    }),
  ).toBeUndefined();
  expect(
    await handler({
      toolName: "read",
      input: { path: "public_test.py" },
    }),
  ).toBeUndefined();
  expect(
    await handler({
      toolName: "read",
      input: { path: join(workspace, "public_test.py") },
    }),
  ).toBeUndefined();
  expect(
    await handler({
      toolName: "read",
      input: { path: "local://notes" },
    }),
  ).toBeUndefined();
  expect(
    await handler({
      toolName: "grep",
      input: { pattern: "unittest", path: "hello world" },
    }),
  ).toBeUndefined();
  expect(() => readFileSync(logPath)).toThrow();
});

test("blocks oracle path reads and logs NDJSON", async () => {
  const result = await handler({
    toolName: "read",
    input: { path: join(oracleDir, "secret.py") },
  });
  expect(result).toEqual({
    block: true,
    reason: "path outside benchmark workspace",
  });
  const parentEscape = await handler({
    toolName: "read",
    input: { path: join("..", "bench-oracle-escape", "secret.py") },
  });
  expect(parentEscape?.block).toBe(true);
  const lines = blockedLines(logPath);
  expect(lines.length).toBeGreaterThanOrEqual(1);
  expect(lines[0]?.tool).toBe("read");
  expect(lines[0]?.reason).toBe("path outside benchmark workspace");
});

test("blocks symlink escape out of the workspace", async () => {
  symlinkSync(oracleDir, join(workspace, "escape"));
  const result = await handler({
    toolName: "read",
    input: { path: join("escape", "secret.py") },
  });
  expect(result).toEqual({
    block: true,
    reason: "path outside benchmark workspace",
  });
  const lines = blockedLines(logPath);
  expect(lines).toHaveLength(1);
  expect(lines[0]?.tool).toBe("read");
});

test("blocks harness-internal URI schemes but allows file:// inside the workspace", async () => {
  const cases = [
    { path: "skill://writing", reason: "blocked skill:// resource outside benchmark workspace" },
    { path: "artifact://3:raw", reason: "blocked artifact:// resource outside benchmark workspace" },
    { path: "history://abc", reason: "blocked history:// resource outside benchmark workspace" },
  ];
  for (const c of cases) {
    const result = await handler({ toolName: "read", input: { path: c.path } });
    expect(result).toEqual({ block: true, reason: c.reason });
  }
  expect(
    await handler({
      toolName: "read",
      input: { path: `file://${join(workspace, "public_test.py")}` },
    }),
  ).toBeUndefined();
  expect(blockedLines(logPath).map((row) => row.reason)).toEqual(cases.map((c) => c.reason));
});

test("blocks curl, git clone, pip, and Python socket", async () => {
  const cases = [
    { command: "curl https://example.com", reason: "blocked network command" },
    { command: "git clone https://github.com/exercism/python.git", reason: "blocked git network command" },
    { command: "pip install requests", reason: "blocked package install" },
    { command: 'python3 -c "import socket; socket.socket()"', reason: "blocked network import" },
  ];
  for (const c of cases) {
    const result = await handler({ toolName: "bash", input: { command: c.command } });
    expect(result).toEqual({ block: true, reason: c.reason });
  }
  const lines = blockedLines(logPath);
  expect(lines.map((row) => row.reason)).toEqual(cases.map((c) => c.reason));
  expect(lines.every((row) => row.tool === "bash")).toBe(true);
});

test("allows python integer division and comments while blocking genuine escapes", async () => {
  const allowedCommands = [
    "python3 -c 'a = 5 // 2'",
    'python3 -c "print(\'foldl:\', (5 // 2) // 5)"',
    'python3 -c "assert foldl(...) == n * (n - 1) // 2"',
    "python3 -c 'x = 10 // 3 # test //: comment'",
    "python3 -c 'y = (10 // 2)'",
    "python3 -c 'z = foo(10 // 2, 3)'",
  ];
  for (const cmd of allowedCommands) {
    const res = await handler({ toolName: "bash", input: { command: cmd } });
    expect(res).toBeUndefined();
  }

  const blockedCommands = [
    { command: "cat //tmp/leak", reason: "path outside benchmark workspace" },
    { command: "ls /tmp", reason: "path outside benchmark workspace" },
    { command: "head /var/folders/other/foo", reason: "path outside benchmark workspace" },
  ];
  for (const c of blockedCommands) {
    const res = await handler({ toolName: "bash", input: { command: c.command } });
    expect(res).toEqual({ block: true, reason: c.reason });
  }
});
