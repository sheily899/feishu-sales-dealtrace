"""Local demo workbench for normalized Feishu-style sales chat events."""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import urlparse

from .models import Transcript, Turn
from .pipeline import coach_transcript
from datetime import datetime


def normalize_events(events: Iterable[Mapping[str, str]], role_map: Mapping[str, str]) -> list[dict[str, str]]:
    """Deduplicate and order text events before creating sales-analysis input."""
    unique: dict[str, dict[str, str]] = {}
    for event in events:
        message_id = event["message_id"]
        if message_id in unique:
            continue
        role = role_map.get(event["sender_id"], "unknown")
        if role not in {"customer", "sales"} or not event.get("text", "").strip():
            continue
        unique[message_id] = {
            "messageId": message_id,
            "chatId": event["chat_id"],
            "senderName": event.get("sender_name", role),
            "role": role,
            "sentAt": event["timestamp"],
            "text": event["text"].strip(),
        }
    return sorted(unique.values(), key=lambda message: (message["sentAt"], message["messageId"]))


def build_standard_transcript(messages: Iterable[Mapping[str, str]]) -> tuple[str, list[dict[str, str]]]:
    """Convert normalized messages to the engine's role-labelled text contract."""
    labels = {"customer": "客户", "sales": "销售"}
    lines: list[str] = []
    segments: list[dict[str, str]] = []
    for message in messages:
        label = labels.get(message["role"])
        if not label:
            continue
        lines.append(f"{label}：{message['text']}")
        segments.append({"segmentId": f"seg_{message['messageId']}", "messageId": message["messageId"]})
    return "\n\n".join(lines), segments


_ROOT = Path(__file__).resolve().parents[2]
_FIXTURE = _ROOT / "fixtures" / "feishu-events" / "demo_customer_a.json"
_ROLE_MAP = {"customer-demo": "customer", "sales-demo": "sales", "bot-demo": "bot"}


class DemoWorkbench:
    def __init__(self) -> None:
        fixture = json.loads(_FIXTURE.read_text(encoding="utf-8"))
        self.name = fixture["customerName"]
        self.messages = normalize_events(fixture["events"], _ROLE_MAP)
        self.transcript, self.segments = build_standard_transcript(self.messages)
        self.analysis = None

    def snapshot(self) -> dict:
        return {"customerName": self.name, "sourceLabel": "飞书测试数据", "messages": self.messages,
                "segments": self.segments, "analysis": self.analysis}

    def analyze(self) -> dict:
        turns = [Turn(speaker="客户" if m["role"] == "customer" else "销售",
                      side="prospect" if m["role"] == "customer" else "rep", text=m["text"])
                 for m in self.messages]
        self.analysis = coach_transcript(Transcript(title=self.name, turns=turns)).model_dump()
        return self.snapshot()


def run_workbench(host: str = "127.0.0.1", port: int = 8765) -> None:
    state = DemoWorkbench()

    class Handler(BaseHTTPRequestHandler):
        def _send(self, body: bytes, content_type: str, status: HTTPStatus = HTTPStatus.OK) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _json(self, body: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
            self._send(json.dumps(body, ensure_ascii=False).encode(), "application/json; charset=utf-8", status)

        def do_GET(self) -> None:
            if urlparse(self.path).path == "/api/workbench":
                self._json(state.snapshot())
            elif urlparse(self.path).path == "/":
                self._send(_PAGE.encode(), "text/html; charset=utf-8")
            else:
                self.send_error(HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:
            if urlparse(self.path).path != "/api/analyze":
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            try:
                self._json(state.analyze())
            except Exception as error:
                self._json({"error": str(error)}, HTTPStatus.BAD_GATEWAY)

        def log_message(self, format: str, *args) -> None:
            return

    print(f"Sales workbench: http://{host}:{port}")
    ThreadingHTTPServer((host, port), Handler).serve_forever()


_PAGE = """<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>AI 销售沟通分析</title>
<style>:root{--i:#17232c;--m:#6b7984;--l:#dce4e8;--a:#13756b}*{box-sizing:border-box}body{margin:0;background:#f4f7f6;color:var(--i);font:15px Arial,"Microsoft YaHei",sans-serif}main{max-width:1400px;margin:auto;padding:32px}header{display:flex;justify-content:space-between;align-items:center;margin-bottom:24px}.eyebrow{font-size:11px;font-weight:bold;letter-spacing:1px;color:var(--a)}h1{margin:4px 0;font-size:28px}h2{font-size:18px}button{background:var(--a);color:#fff;border:0;border-radius:6px;padding:11px 16px;font-weight:bold;cursor:pointer}.workspace{display:grid;grid-template-columns:35% 65%;background:#fffefa;border:1px solid var(--l);min-height:600px}aside{padding:20px;border-right:1px solid var(--l)}article{padding:24px}.message{padding:14px 0;border-bottom:1px solid #edf0f1}.who{font-weight:bold}.customer .who{color:#885918}.time{color:var(--m);font-size:12px;margin-left:8px}.highlight{background:#fff0b8;margin:0 -8px;padding:14px 8px}.item{border-left:3px solid #79aaa3;background:#f4f8f7;padding:10px 12px;margin:8px 0}.item button{all:unset;cursor:pointer;font-weight:bold}.muted{color:var(--m)}.error{color:#a12d2d}@media(max-width:800px){main{padding:16px}.workspace{grid-template-columns:1fr}aside{border-right:0;border-bottom:1px solid var(--l)}}</style>
<main><header><div><p class="eyebrow">SALES INTELLIGENCE</p><h1 id="name">加载中…</h1><p id="meta" class="muted"></p></div><button id="go">生成分析</button></header><section class="workspace"><aside><h2>群聊记录</h2><div id="messages"></div></aside><article><p class="eyebrow">AI ANALYSIS</p><h2>销售沟通分析</h2><p id="status" class="muted">待分析</p><div id="report" class="muted">点击“生成分析”，由 DeepSeek 基于群聊生成销售教练报告。</div></article></section></main>
<script>let state;const q=s=>document.querySelector(s),e=v=>String(v||"").replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));function items(title,list){if(!list||!list.length)return"";return'<h3>'+title+'</h3>'+list.map(i=>'<div class="item"><strong>'+e(i.title||i.statement)+'</strong><p>'+e(i.detail||i.status||"")+'</p></div>').join("")}function show(d){state=d;q("#name").textContent=d.customerName;q("#meta").textContent="来源："+d.sourceLabel+" · 已同步 "+d.messages.length+" 条有效消息";q("#messages").innerHTML=d.messages.map(m=>'<div class="message '+m.role+'"><span class="who">'+e(m.senderName)+'</span><span class="time">'+m.sentAt.slice(11,16)+'</span><p>'+e(m.text)+'</p></div>').join("");if(!d.analysis)return;let a=d.analysis,g=a.group_chat,out='<p>'+e(a.summary)+'</p><h3>沟通阶段：'+e(a.classification.call_type)+'</h3>';if(g){out+=items("客户需求",g.customer_needs)+items("客户顾虑",g.customer_concerns)+items("销售回应覆盖",g.response_coverage)+items("销售承诺",g.sales_commitments)+items("待办事项",g.todos)+items("下一步建议",g.next_steps)}else{out+=items("客户目标",a.outcomes)+items("销售表现",a.coaching.strengths)+items("改进建议",a.coaching.improvements)}q("#report").innerHTML=out}q("#go").onclick=async()=>{let b=q("#go");b.disabled=true;b.textContent="分析中…";q("#status").textContent="DeepSeek 分析中";try{let r=await fetch("/api/analyze",{method:"POST"}),d=await r.json();if(!r.ok)throw Error(d.error);show(d);q("#status").textContent="分析完成";b.textContent="重新分析"}catch(x){q("#report").className="error";q("#report").textContent="分析失败："+x.message;q("#status").textContent="分析失败"}finally{b.disabled=false}};fetch("/api/workbench").then(r=>r.json()).then(show)</script>"""
