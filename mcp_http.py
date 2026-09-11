#!/usr/bin/env python3
"""Minimal MCP-over-HTTP client (streamable HTTP, JSON-RPC). Stdlib only.
Used for You.com (free profile, no key) and One Remote MCP (key in header).

    from mcp_http import McpHttp
    m = McpHttp("https://api.you.com/mcp?profile=free")
    print(m.tools())            # names
    print(m.call("you-search", {"query": "...", "count": 3}))   # text content joined
"""
import json, urllib.request

class McpHttp:
    def __init__(self, url, headers=None, timeout=60):
        self.url, self.timeout = url, timeout
        self.headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
                        "User-Agent": "curl/8.7.1"}  # Cloudflare 403s the default Python-urllib UA
        self.headers.update(headers or {})
        self._id = 0
        self.session_id = None
        self._init()

    def _post(self, method, params=None):
        self._id += 1
        body = json.dumps({"jsonrpc": "2.0", "id": self._id, "method": method, "params": params or {}}).encode()
        h = dict(self.headers)
        if self.session_id:
            h["Mcp-Session-Id"] = self.session_id
        req = urllib.request.Request(self.url, data=body, headers=h, method="POST")
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            sid = r.headers.get("Mcp-Session-Id")
            if sid:
                self.session_id = sid
            raw = r.read().decode("utf-8", "replace")
            ctype = r.headers.get("Content-Type", "")
        msgs = []
        if "text/event-stream" in ctype:
            for line in raw.splitlines():
                if line.startswith("data:"):
                    try:
                        msgs.append(json.loads(line[5:].strip()))
                    except json.JSONDecodeError:
                        pass
        elif raw.strip():
            msgs.append(json.loads(raw))
        for m in msgs:
            if m.get("id") == self._id:
                if "error" in m:
                    raise RuntimeError(f"MCP error: {m['error']}")
                return m.get("result")
        raise RuntimeError(f"no response for {method}: {raw[:300]}")

    def _init(self):
        self._post("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                                  "clientInfo": {"name": "a2-harness", "version": "0"}})
        try:
            self._post("notifications/initialized")
        except Exception:
            pass

    def tools(self):
        return [t["name"] for t in self._post("tools/list").get("tools", [])]

    def call(self, name, arguments):
        res = self._post("tools/call", {"name": name, "arguments": arguments})
        if res.get("isError"):
            raise RuntimeError(f"tool {name} error: {json.dumps(res)[:400]}")
        texts = [c.get("text", "") for c in res.get("content", []) if c.get("type") == "text"]
        return "\n".join(texts), res

if __name__ == "__main__":
    import sys
    m = McpHttp(sys.argv[1] if len(sys.argv) > 1 else "https://api.you.com/mcp?profile=free")
    print(m.tools())
