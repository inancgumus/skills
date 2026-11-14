#!/usr/bin/env python3
"""Mine agent session logs (Claude Code, Codex, opencode) for how a tool or topic was used.

  mine.py agents                    which agents have logs on this machine, with session counts
  mine.py sessions TOPIC            which sessions touched the topic, per agent
  mine.py calls    TOPIC [--top N]  most repeated commands that match the topic
  mine.py fails    TOPIC            commands that failed, grouped by error
  mine.py talk     TOPIC            user messages, agent notes, saved memory notes, and prompt history
  mine.py show     SESSION_ID       one session as a compact conversation (id from `sessions`)

TOPIC is a case-insensitive regex, e.g. 'vmctl|ghostvm'. Add --agent claude|codex|opencode
(repeatable) to limit the source, and --root DIR to read a different log folder.
"""
import argparse, glob, json, os, re, sqlite3, sys
from collections import Counter, defaultdict

HOME = os.path.expanduser("~")
FAIL = re.compile(
    r"(Traceback|\bError:|command not found|No such file|Operation not permitted|Permission denied|timed out|"
    r"Empty response|Invalid response|Connection refused|"
    r"\"ok\": ?false|\"error\":\{)", re.I)
OK_JSON = re.compile(r'"ok": ?true')
SELF = re.compile(r"mine\.py|extract-skill")  # skip calls made while mining logs
TROUBLE = re.compile(r"(fail|stuck|hang|wrong|didn.t|can.t|blocked|empty|timed out|dropped|denied|"
                     r"instead|turns out|because|never|always|don.t|stop|again)", re.I)


def text_of(x):
    if x is None: return ""
    if isinstance(x, str): return x
    if isinstance(x, list): return "\n".join(text_of(i) for i in x)
    if isinstance(x, dict):
        for k in ("text", "output", "content", "stdout"):
            if k in x: return text_of(x[k])
        return json.dumps(x)[:2000]
    return str(x)


# Each reader yields events: dict(agent, session, kind, text, tool, id, err)
# kind: user | assistant | call | result
def read_claude(root):
    for f in glob.glob(os.path.join(root or HOME + "/.claude/projects", "**/*.jsonl"), recursive=True):
        sid = os.path.basename(f)[:8]
        for line in open(f, errors="ignore"):
            try: d = json.loads(line)
            except Exception: continue
            m = d.get("message") if isinstance(d.get("message"), dict) else None
            if not m: continue
            c = m.get("content")
            if isinstance(c, str): c = [{"type": "text", "text": c}]
            for b in c if isinstance(c, list) else []:
                t = b.get("type")
                if t == "text":
                    if b["text"].lstrip().startswith(("<", "# Environment")): continue
                    yield dict(agent="claude", session=sid, kind="user" if d.get("type") == "user" else "assistant", text=b["text"])
                elif t == "tool_use":
                    i = b.get("input", {})
                    yield dict(agent="claude", session=sid, kind="call", tool=b.get("name"), id=b.get("id"),
                               text=i.get("command") or json.dumps(i)[:600])
                elif t == "tool_result":
                    yield dict(agent="claude", session=sid, kind="result", id=b.get("tool_use_id"),
                               text=text_of(b.get("content")), err=bool(b.get("is_error")))


def read_claude_notes(root):
    """User prompts and agent messages from history.jsonl, plus saved memory notes. Often hold rules no transcript states."""
    base = (root and os.path.dirname(root.rstrip("/"))) or HOME + "/.claude"
    h = os.path.join(base, "history.jsonl")
    if os.path.exists(h):
        for line in open(h, errors="ignore"):
            try: t = json.loads(line).get("display") or ""
            except Exception: continue
            if t: yield dict(agent="claude", session="history", kind="user", text=t)
    for f in glob.glob(os.path.join(root or base + "/projects", "**/memory/*.md"), recursive=True):
        if os.path.basename(f) != "MEMORY.md":
            yield dict(agent="claude", session="notes", kind="note", text=open(f, errors="ignore").read())


def read_codex(root):
    base = root or HOME + "/.codex"
    for f in glob.glob(base + "/sessions/**/*.jsonl", recursive=True) + glob.glob(base + "/archived_sessions/*.jsonl"):
        sid = os.path.basename(f)[-14:-6]
        for line in open(f, errors="ignore"):
            try: d = json.loads(line)
            except Exception: continue
            p = d.get("payload") or {}
            t = p.get("type")
            if d.get("type") == "event_msg" and t == "user_message":
                yield dict(agent="codex", session=sid, kind="user", text=p.get("message", ""))
            elif d.get("type") == "response_item":
                if t == "message" and p.get("role") == "assistant":
                    yield dict(agent="codex", session=sid, kind="assistant", text=text_of(p.get("content")))
                elif t in ("function_call", "custom_tool_call", "local_shell_call"):
                    a = p.get("arguments") or p.get("input") or p.get("action") or ""
                    try: a = json.loads(a) if isinstance(a, str) else a
                    except Exception: pass
                    cmd = a.get("cmd") or a.get("command") if isinstance(a, dict) else a
                    yield dict(agent="codex", session=sid, kind="call", tool=p.get("name"), id=p.get("call_id"),
                               text=text_of(cmd))
                elif t in ("function_call_output", "custom_tool_call_output"):
                    yield dict(agent="codex", session=sid, kind="result", id=p.get("call_id"), text=text_of(p.get("output")))


def read_opencode(root):
    db = (root or HOME + "/.local/share/opencode") + "/opencode.db"
    if not os.path.exists(db): return
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    for sid, mid, data in con.execute("select session_id, message_id, data from part order by time_created"):
        try: d = json.loads(data)
        except Exception: continue
        sid = sid[-8:]
        if d.get("type") == "tool":
            st = d.get("state", {})
            i = st.get("input", {})
            yield dict(agent="opencode", session=sid, kind="call", tool=d.get("tool"), id=d.get("callID"),
                       text=i.get("command") or json.dumps(i)[:600])
            yield dict(agent="opencode", session=sid, kind="result", id=d.get("callID"),
                       text=text_of(st.get("output")), err=st.get("status") == "error")
        elif d.get("type") == "text":
            yield dict(agent="opencode", session=sid, kind="assistant", text=d.get("text", ""))


def read_pi(root):
    """Pi coding agent: ~/.pi/agent/sessions/<cwd>/<time>_<id>.jsonl (format from Pi's docs; untested on real logs here)."""
    base = root or HOME + "/.pi/agent/sessions"
    for f in glob.glob(os.path.join(base, "**/*.jsonl"), recursive=True):
        sid = os.path.basename(f)[-14:-6]
        for line in open(f, errors="ignore"):
            try: d = json.loads(line)
            except Exception: continue
            m = d.get("message") if isinstance(d.get("message"), dict) else None
            if not m: continue
            role, c = m.get("role"), m.get("content")
            if isinstance(c, str): c = [{"type": "text", "text": c}]
            if role == "toolResult":
                yield dict(agent="pi", session=sid, kind="result", id=m.get("toolCallId"), text=text_of(c), err=bool(m.get("isError")))
                continue
            for b in c if isinstance(c, list) else []:
                t = b.get("type")
                if t == "text":
                    yield dict(agent="pi", session=sid, kind="user" if role == "user" else "assistant", text=b.get("text", ""))
                elif t in ("toolCall", "toolUse", "tool_use"):
                    a = b.get("arguments") or b.get("input") or {}
                    yield dict(agent="pi", session=sid, kind="call", tool=b.get("name"), id=b.get("id"),
                               text=a.get("command") if isinstance(a, dict) and a.get("command") else json.dumps(a)[:600])


def read_claude_all(root):
    yield from read_claude(root)
    yield from read_claude_notes(root)


READERS = dict(claude=read_claude_all, codex=read_codex, opencode=read_opencode, pi=read_pi)
LOCATIONS = dict(
    claude=lambda: len(glob.glob(HOME + "/.claude/projects/**/*.jsonl", recursive=True)),
    codex=lambda: len(glob.glob(HOME + "/.codex/sessions/**/*.jsonl", recursive=True)) + len(glob.glob(HOME + "/.codex/archived_sessions/*.jsonl")),
    opencode=lambda: _count_sql(HOME + "/.local/share/opencode/opencode.db", "select count(*) from session"),
    pi=lambda: len(glob.glob(HOME + "/.pi/agent/sessions/**/*.jsonl", recursive=True)),
)


def _count_sql(db, q):
    try: return sqlite3.connect(f"file:{db}?mode=ro", uri=True).execute(q).fetchone()[0]
    except Exception: return 0


def events(args):
    skip = tuple(args.skip or ())
    for name, fn in READERS.items():
        if not args.agent or name in args.agent:
            for e in fn(args.root):
                if not (skip and e["session"].startswith(skip)):
                    yield e


def norm(cmd):
    """Collapse a command so near-identical calls group together."""
    c = re.sub(r"\s+", " ", cmd.strip())
    c = re.sub(r"/private/tmp/\S+|/tmp/\S+|\b[0-9a-f]{8,}\b|\d+", "N", c)
    return c[:140]


def paired(args, pat):
    """Yield (call, result) for calls whose command matches the topic."""
    calls = {}
    for e in events(args):
        if e["kind"] == "call" and pat.search(e["text"]) and not SELF.search(e["text"]):
            calls[(e["agent"], e["session"], e["id"])] = e
        elif e["kind"] == "result":
            c = calls.pop((e["agent"], e["session"], e["id"]), None)
            if c: yield c, e


def cmd_sessions(args, pat):
    n = defaultdict(Counter); first = {}
    for e in events(args):
        if pat.search(e["text"]):
            k = (e["agent"], e["session"]); n[k][e["kind"]] += 1
            if e["kind"] == "user" and k not in first: first[k] = e["text"][:90].replace("\n", " ")
    for k, c in sorted(n.items(), key=lambda kv: -sum(kv[1].values())):
        print(f"{sum(c.values()):5d}  {k[0]:8s} {k[1]}  calls={c['call']} user={c['user']}  {first.get(k, '')}")


def cmd_calls(args, pat):
    cnt = Counter(); sess = defaultdict(set); ex = {}
    for c, _ in paired(args, pat):
        k = norm(c["text"]); cnt[k] += 1; sess[k].add(c["session"]); ex.setdefault(k, c["text"])
    for k, v in cnt.most_common(args.top):
        print(f"{v:4d}x in {len(sess[k]):2d} sessions  {k}")


def cmd_fails(args, pat):
    groups = defaultdict(list)
    for c, r in paired(args, pat):
        if SELF.search(c["text"]): continue
        if (r.get("err") and len(r["text"].strip()) > 40) or (FAIL.search(r["text"][:3000]) and not OK_JSON.search(r["text"][:3000])):
            m = FAIL.search(r["text"][:3000])
            start = max(0, (m.start() if m else 0) - 40)
            sig = re.sub(r"\s+", " ", r["text"][start:start + 110])
            sig = re.sub(r"\d+|/private/tmp/\S+", "N", sig)
            groups[sig].append((c, r))
    for sig, items in sorted(groups.items(), key=lambda kv: -len(kv[1]))[:args.top]:
        sessions = {c["session"] for c, _ in items}
        c, r = items[0]
        print(f"{len(items):3d}x in {len(sessions)} sessions  ERROR: {sig}")
        print(f"      e.g. {norm(c['text'])[:160]}")
        print(f"      out: {re.sub(chr(10), ' ', r['text'])[:200]}\n")


def cmd_talk(args, pat):
    seen = set()
    for e in events(args):
        if e["kind"] not in ("user", "assistant", "note") or not pat.search(e["text"]): continue
        if SELF.search(e["text"]) or e["text"].startswith(("Base directory for this skill", "The following skills")): continue
        t = e["text"].strip().replace("\n", " ")
        if len(t) > (1500 if e["kind"] == "note" else 700) or (e["kind"] == "assistant" and not TROUBLE.search(t)): continue
        if t[:60] in seen: continue
        seen.add(t[:60])
        print(f"[{e['agent']}/{e['session']}] {e['kind'].upper()[0]}: {t[:320]}")


def cmd_show(args, _pat):
    """Print one session as a compact conversation. TOPIC is the session id (prefix)."""
    n = 0; last = None
    for e in events(args):
        if not e["session"].startswith(args.topic): continue
        key = (e["kind"], e["text"][:300])
        if key == last: continue  # logs repeat a message while it streams
        last = key
        k = e["kind"]
        t = re.sub(r"\s+", " ", e["text"])
        cap = {"user": 500, "assistant": 400, "call": 260, "result": 240, "note": 500}[k]
        print({"user": "USER", "assistant": "AGENT", "call": "  $", "result": "  ->", "note": "NOTE"}[k], t[:cap])
        n += 1
        if n >= args.top * 10: print("... (raise --top to see more)"); break


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["agents", "sessions", "calls", "fails", "talk", "show"])
    ap.add_argument("topic", nargs="?")
    ap.add_argument("--agent", choices=list(READERS), action="append")
    ap.add_argument("--root")
    ap.add_argument("--skip", action="append", help="ignore sessions whose id starts with this (repeatable), e.g. the current one")
    ap.add_argument("--top", type=int, default=40)
    a = ap.parse_args()
    if a.cmd == "agents":
        for name, count in LOCATIONS.items():
            print(f"{name:9s} {count():5d} sessions")
        return
    if not a.topic: ap.error("TOPIC is required")
    pat = re.compile(a.topic, re.I)
    {"sessions": cmd_sessions, "calls": cmd_calls, "fails": cmd_fails, "talk": cmd_talk, "show": cmd_show}[a.cmd](a, pat)


if __name__ == "__main__":
    sys.exit(main())
