"""Local demo workbench for normalized Feishu-style sales chat events."""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from threading import RLock
from urllib.parse import parse_qs, urlparse

from .customer_state import generate_customer_state
from .llm import build_coach
from .models import Transcript, Turn
from .pipeline import coach_transcript
from datetime import datetime, timedelta, timezone


# China Standard Time is UTC+8 year-round; a fixed offset avoids relying on
# an operating-system time-zone database in local Windows virtualenvs.
_BEIJING_TIMEZONE = timezone(timedelta(hours=8), name="CST")


def _beijing_timestamp(timestamp: str) -> str:
    """Render all inbound event timestamps in China Standard Time for the workbench."""
    return datetime.fromisoformat(timestamp).astimezone(_BEIJING_TIMEZONE).isoformat(timespec="seconds")


def normalize_events(events: Iterable[Mapping[str, str]], role_map: Mapping[str, str]) -> list[dict[str, str]]:
    """Deduplicate and order text events before creating sales-analysis input."""
    role_labels = {"customer": "客户", "sales": "销售"}
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
            "senderName": role_labels[role],
            "role": role,
            "sentAt": _beijing_timestamp(event["timestamp"]),
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


def build_evidence_map(report: Mapping, messages: Iterable[Mapping[str, str]]) -> dict[str, list[str]]:
    """Link LLM quote evidence to normalized message IDs for UI navigation.

    Exact text is preferred. A contained quote is accepted as a fallback because an
    LLM may omit an unimportant particle while still citing the same message.
    """
    normalized_messages = list(messages)
    evidence_map: dict[str, list[str]] = {}

    def visit(value: object) -> None:
        if isinstance(value, Mapping):
            evidence = value.get("evidence")
            if isinstance(evidence, list):
                for quote in evidence:
                    if not isinstance(quote, Mapping):
                        continue
                    speaker, text = quote.get("speaker"), quote.get("text")
                    if not isinstance(speaker, str) or not isinstance(text, str):
                        continue
                    key = f"{speaker}\n{text}"
                    ids = [
                        message["messageId"]
                        for message in normalized_messages
                        if message.get("text") == text
                        or text in message.get("text", "")
                        or message.get("text", "") in text
                    ]
                    if ids:
                        evidence_map[key] = ids
            for nested in value.values():
                visit(nested)
        elif isinstance(value, list):
            for nested in value:
                visit(nested)

    visit(report)
    return evidence_map


_ROOT = Path(__file__).resolve().parents[2]
_FIXTURE = _ROOT / "fixtures" / "feishu-events" / "demo_customer_a.json"
_ROLE_MAP = {"customer-demo": "customer", "sales-demo": "sales", "bot-demo": "bot"}
_CALL_TYPE_LABELS = {
    "discovery": "需求探索（Discovery）",
    "demo": "产品演示（Demo）",
    "technical-evaluation": "技术评估",
    "negotiation": "商务谈判",
    "renewal": "续约沟通",
}


def display_call_type(call_type: str) -> str:
    """Keep canonical stage IDs in the engine while showing sales-friendly labels."""
    return _CALL_TYPE_LABELS.get(call_type, call_type)


class DemoWorkbench:
    def __init__(self) -> None:
        fixture = json.loads(_FIXTURE.read_text(encoding="utf-8"))
        self.name = fixture["customerName"]
        self.messages = normalize_events(fixture["events"], _ROLE_MAP)
        self.transcript, self.segments = build_standard_transcript(self.messages)
        self.analysis = None
        self.evidence_map: dict[str, list[str]] = {}

    def snapshot(self) -> dict:
        return {"customerName": self.name, "sourceLabel": "飞书测试数据", "messages": self.messages,
                "segments": self.segments, "analysis": self.analysis, "evidenceMap": self.evidence_map,
                "callTypeLabel": display_call_type(self.analysis["classification"]["call_type"])
                if self.analysis else None}

    def analyze(self) -> dict:
        turns = [Turn(speaker="客户" if m["role"] == "customer" else "销售",
                      side="prospect" if m["role"] == "customer" else "rep", text=m["text"])
                 for m in self.messages]
        self.analysis = coach_transcript(Transcript(title=self.name, turns=turns)).model_dump()
        self.evidence_map = build_evidence_map(self.analysis, self.messages)
        return self.snapshot()


class LiveWorkbench:
    """Feishu workbench backed by optional local SQLite persistence."""

    def __init__(
        self,
        role_map: Mapping[str, str],
        store=None,
        chat_id: str | None = None,
        coach_runner=coach_transcript,
        state_llm=None,
    ) -> None:
        self.name = "飞书测试群"
        self.role_map = dict(role_map)
        self.store = store
        self.chat_id = chat_id
        self.coach_runner = coach_runner
        self.state_llm = state_llm
        self.raw_events: list[dict[str, str]] = []
        self.messages: list[dict[str, str]] = []
        self.transcript = ""
        self.segments: list[dict[str, str]] = []
        self.analysis = None
        self.evidence_map: dict[str, list[str]] = {}
        self.customer_state = None
        self.state_change = None
        self.state_history: list = []
        self.rejected_state_changes: list[str] = []
        self.no_new_messages = False
        self._lock = RLock()
        if self.store and self.chat_id:
            with self._lock:
                self._restore_locked()

    def _restore_locked(self) -> None:
        if not self.store or not self.chat_id:
            return
        self.raw_events = self.store.load_events(self.chat_id)
        self.messages = normalize_events(self.raw_events, self.role_map)
        self.transcript, self.segments = build_standard_transcript(self.messages)
        saved_report = self.store.load_report(self.chat_id)
        self.analysis, self.evidence_map = saved_report if saved_report else (None, {})
        self.customer_state = self.store.load_latest_state(self.chat_id)
        self.state_change = (
            self.store.load_state_change(self.chat_id, self.customer_state.version)
            if self.customer_state else None
        )
        self.state_history = self.store.list_state_versions(self.chat_id)

    def ingest(self, event: Mapping[str, str]) -> None:
        """Store an event and rebuild the deterministic chat view."""
        with self._lock:
            incoming_chat_id = event.get("chat_id", "")
            if self.chat_id and incoming_chat_id != self.chat_id:
                return
            if not self.chat_id:
                self.chat_id = incoming_chat_id
            sender_id = event.get("sender_id", "")
            if sender_id not in self.role_map:
                print(
                    "Feishu message ignored: add sender "
                    f"{sender_id} to FEISHU_ROLE_MAP before analysis "
                    f"(chat ID: {event.get('chat_id', '')})."
                )
            if self.store:
                is_new = self.store.save_event(event)
                if is_new:
                    self.store.delete_report(self.chat_id)
                self._restore_locked()
                self.no_new_messages = False
                return
            self.raw_events.append(dict(event))
            self.messages = normalize_events(self.raw_events, self.role_map)
            self.transcript, self.segments = build_standard_transcript(self.messages)
            self.analysis = None
            self.evidence_map = {}
            self.no_new_messages = False

    def snapshot(self) -> dict:
        with self._lock:
            state_evidence = build_evidence_map(
                {
                    "customer_state": self.customer_state.model_dump() if self.customer_state else {},
                    "state_change": self.state_change.model_dump() if self.state_change else {},
                },
                self.messages,
            )
            evidence_map = dict(self.evidence_map)
            evidence_map.update(state_evidence)
            return {
                "customerName": self.name,
                "sourceLabel": "飞书测试群同步",
                "messages": list(self.messages),
                "segments": list(self.segments),
                "analysis": self.analysis,
                "evidenceMap": evidence_map,
                "callTypeLabel": display_call_type(self.analysis["classification"]["call_type"])
                if self.analysis else None,
                "customerState": self.customer_state.model_dump() if self.customer_state else None,
                "stateChange": self.state_change.model_dump() if self.state_change else None,
                "stateHistory": [
                    {
                        "version": state.version,
                        "updatedAt": state.updated_at,
                        "change": self.store.load_state_change(self.chat_id, state.version).model_dump()
                        if self.store and self.store.load_state_change(self.chat_id, state.version) else None,
                    }
                    for state in self.state_history
                ],
                "rejectedStateChanges": list(self.rejected_state_changes),
                "noNewMessages": self.no_new_messages,
            }

    def analyze(self) -> dict:
        with self._lock:
            messages = list(self.messages)
            previous_state = self.customer_state
            analyzed_ids = set(previous_state.analyzed_message_ids) if previous_state else set()
            new_messages = [message for message in messages if message["messageId"] not in analyzed_ids]
        if not messages:
            raise ValueError("尚未同步可分析的客户或销售群聊消息")
        if previous_state and not new_messages:
            with self._lock:
                self.no_new_messages = True
            return self.snapshot()
        turns = [Turn(speaker="客户" if m["role"] == "customer" else "销售",
                      side="prospect" if m["role"] == "customer" else "rep", text=m["text"])
                 for m in messages]
        analysis = self.coach_runner(Transcript(title=self.name, turns=turns)).model_dump()
        state_result = None
        if self.store and self.chat_id:
            state_result = generate_customer_state(
                previous_state,
                new_messages,
                self.state_llm or build_coach(),
            )
        with self._lock:
            self.analysis = analysis
            self.evidence_map = build_evidence_map(analysis, self.messages)
            if self.store and self.chat_id:
                self.store.save_report(self.chat_id, self.analysis, self.evidence_map)
                self.customer_state = self.store.save_state_version(
                    self.chat_id,
                    state_result.state,
                    state_result.change,
                    [message["messageId"] for message in messages],
                )
                self.state_change = state_result.change
                self.state_history = self.store.list_state_versions(self.chat_id)
                self.rejected_state_changes = state_result.rejected_changes
            self.no_new_messages = False
        return self.snapshot()


class MultiChatWorkbench:
    """Dispatch configured chat IDs to isolated single-chat workbenches."""

    def __init__(self, role_map, chat_ids, store, coach_runner=coach_transcript, state_llm=None) -> None:
        self.role_map = dict(role_map)
        self.chat_ids = list(dict.fromkeys(chat_ids))
        if not self.chat_ids:
            raise ValueError("至少需要配置一个飞书群")
        self.store = store
        self.coach_runner = coach_runner
        self.state_llm = state_llm
        self._workbenches: dict[str, LiveWorkbench] = {}
        self._lock = RLock()

    def _workbench(self, chat_id: str | None) -> LiveWorkbench:
        chat_id = chat_id or self.chat_ids[0]
        if chat_id not in self.chat_ids:
            raise KeyError(f"群 {chat_id} 未配置在 FEISHU_GROUP_ALLOWLIST 中")
        with self._lock:
            if chat_id not in self._workbenches:
                self._workbenches[chat_id] = LiveWorkbench(
                    self.role_map, store=self.store, chat_id=chat_id,
                    coach_runner=self.coach_runner, state_llm=self.state_llm,
                )
            return self._workbenches[chat_id]

    def ingest(self, event: Mapping[str, str]) -> None:
        chat_id = event.get("chat_id")
        if chat_id not in self.chat_ids:
            return
        self._workbench(chat_id).ingest(event)

    def snapshot(self, chat_id: str | None = None) -> dict:
        return self._workbench(chat_id).snapshot()

    def analyze(self, chat_id: str | None = None) -> dict:
        return self._workbench(chat_id).analyze()

    def chat_summaries(self) -> list[dict]:
        return self.store.load_chat_summaries(self.chat_ids)


def create_workbench_server(host: str, port: int, feishu_config=None, store=None, start_listener: bool = True):
    """Build a local workbench server; tests can inject a temporary store."""
    if feishu_config:
        from .workbench_store import SQLiteWorkbenchStore

        state = MultiChatWorkbench(
            feishu_config.role_map,
            feishu_config.group_allowlist,
            store=store or SQLiteWorkbenchStore(_ROOT / "data" / "workbench.sqlite3"),
        )
    else:
        state = DemoWorkbench()
    if feishu_config and start_listener:
        from .feishu import FeishuGroupListener

        FeishuGroupListener(feishu_config, state.ingest).start()

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
            request = urlparse(self.path)
            path = request.path
            chat_id = parse_qs(request.query).get("chatId", [None])[0]
            if path == "/api/chats":
                chats = state.chat_summaries() if feishu_config else []
                self._json({"chats": chats})
            elif path == "/api/workbench":
                try:
                    self._json(state.snapshot(chat_id) if feishu_config else state.snapshot())
                except KeyError as error:
                    self._json({"error": str(error)}, HTTPStatus.NOT_FOUND)
            elif path == "/":
                self._send(_PAGE.encode(), "text/html; charset=utf-8")
            else:
                self.send_error(HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:
            request = urlparse(self.path)
            if request.path != "/api/analyze":
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            try:
                chat_id = parse_qs(request.query).get("chatId", [None])[0]
                self._json(state.analyze(chat_id) if feishu_config else state.analyze())
            except KeyError as error:
                self._json({"error": str(error)}, HTTPStatus.NOT_FOUND)
            except Exception as error:
                self._json({"error": str(error)}, HTTPStatus.BAD_GATEWAY)

        def log_message(self, format: str, *args) -> None:
            return

    return ThreadingHTTPServer((host, port), Handler)


def run_workbench(host: str = "127.0.0.1", port: int = 8765, feishu_config=None) -> None:
    server = create_workbench_server(host, port, feishu_config)
    print(f"Sales workbench: http://{host}:{port}")
    server.serve_forever()


_PAGE = """<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>AI 销售沟通分析</title>
<style>:root{--i:#17232c;--m:#6b7984;--l:#dce4e8;--a:#13756b}*{box-sizing:border-box}body{margin:0;background:#f4f7f6;color:var(--i);font:15px Arial,"Microsoft YaHei",sans-serif}main{max-width:1400px;margin:auto;padding:32px}header{display:flex;justify-content:space-between;align-items:center;margin-bottom:24px}.eyebrow{font-size:11px;font-weight:bold;letter-spacing:1px;color:var(--a)}h1{margin:4px 0;font-size:28px}h2{font-size:18px}button{background:var(--a);color:#fff;border:0;border-radius:6px;padding:11px 16px;font-weight:bold;cursor:pointer}.workspace{display:grid;grid-template-columns:35% 65%;background:#fffefa;border:1px solid var(--l);min-height:600px}aside{padding:20px;border-right:1px solid var(--l)}article{padding:24px}.message{padding:14px 0;border-bottom:1px solid #edf0f1}.who{font-weight:bold}.customer .who{color:#885918}.time{color:var(--m);font-size:12px;margin-left:8px}.highlight{background:#fff0b8;margin:0 -8px;padding:14px 8px;outline:2px solid #e2ae38}.item{border-left:3px solid #79aaa3;background:#f4f8f7;padding:10px 12px;margin:8px 0}.evidence-link{all:unset;color:#13756b;cursor:pointer;font-size:13px;text-decoration:underline}.muted{color:var(--m)}.error{color:#a12d2d}@media(max-width:800px){main{padding:16px}.workspace{grid-template-columns:1fr}aside{border-right:0;border-bottom:1px solid var(--l)}}</style>
<main><header><div><p class="eyebrow">SALES INTELLIGENCE</p><h1 id="name">加载中…</h1><p id="meta" class="muted"></p></div><button id="go">生成分析</button></header><section class="workspace"><aside><h2>群聊记录</h2><div id="messages"></div></aside><article><p class="eyebrow">AI ANALYSIS</p><h2>销售沟通分析</h2><p id="status" class="muted">待分析</p><div id="customer-state"></div><div id="report" class="muted">点击“生成分析”，由 DeepSeek 基于群聊生成客户沟通分析报告。</div></article></section></main>
<script>
let state;
const q=s=>document.querySelector(s),e=v=>String(v||"").replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));
const evidenceKey=x=>(x.speaker||"")+"\\n"+(x.text||"");
function evidenceSpeaker(speaker){let value=String(speaker||"");if(value.includes("客户")||value==="prospect")return"客户";if(value.includes("销售")||value==="rep")return"销售";return value.replace(/\\s*\\([^)]*\\)/g,"")}
function evidenceLinks(evidence){return(evidence||[]).map(x=>{let ids=(state.evidenceMap||{})[evidenceKey(x)]||[];let label='原文依据：'+e(evidenceSpeaker(x.speaker))+'：'+e(x.text);if(!ids.length)return'<p class="muted">'+label+'</p>';return'<button type="button" class="evidence-link" data-message-id="'+e(ids[0])+'">'+label+'</button>'}).join("")}
function items(title,list){if(!list||!list.length)return"";return'<h3>'+title+'</h3>'+list.map(i=>'<div class="item"><strong>'+e(i.title||i.statement)+'</strong><p>'+e(i.detail||i.status||"")+'</p>'+evidenceLinks(i.evidence)+'</div>').join("")}
const changeLabels={need:"客户需求",concern:"客户顾虑",commitment:"销售承诺",todo:"待办事项",stakeholder:"相关角色",risk:"商机风险",next_step:"下一步行动"};
function stateItems(title,list){if(!list||!list.length)return"";return'<h4>'+title+'</h4>'+list.map(i=>'<div class="item"><strong>'+e(i.title)+'</strong>'+(i.detail?'<p>'+e(i.detail)+'</p>':"")+(i.status?'<p>状态：'+e(i.status==="completed"?"已完成":"待处理")+'</p>':"")+evidenceLinks(i.evidence)+'</div>').join("")}
function changeItems(title,list){if(!list||!list.length)return"";return'<h4>'+title+'</h4>'+list.map(i=>'<div class="item"><strong>'+e(changeLabels[i.category]||i.category)+'：'+e(i.title)+'</strong>'+evidenceLinks(i.evidence)+'</div>').join("")}
function renderCustomerState(d){let box=q("#customer-state"),s=d.customerState,c=d.stateChange,h=d.stateHistory||[];if(!s){box.innerHTML="";return}let out='<section class="state-panel"><h3>当前客户状态 · 第 '+e(s.version)+' 版</h3><p class="muted">更新时间：'+e(s.updatedAt||"-")+'</p><p><strong>当前阶段：</strong>'+e(s.stage||"未识别")+'</p>'+stateItems("已识别需求",s.needs)+stateItems("未解决顾虑",s.unresolvedConcerns)+stateItems("销售承诺",s.commitments)+stateItems("待办事项",s.todos)+stateItems("相关角色",s.stakeholders)+stateItems("商机风险",s.risks)+stateItems("已约定下一步",s.scheduledNextSteps);if(c){out+='<h3>本次变化</h3>'+(c.currentFocus?'<p><strong>当前重点：</strong>'+e(c.currentFocus)+'</p>':"")+changeItems("新增",c.added)+changeItems("已解决",c.resolved)+(c.statusTransitions||[]).map(x=>'<div class="item"><strong>状态迁移：'+e(changeLabels[x.category]||x.category)+'｜'+e(x.title)+'</strong><p>'+e(x.fromStatus)+' → '+e(x.toStatus)+'</p>'+evidenceLinks(x.evidence)+'</div>').join("")}out+='<h3>版本时间线</h3><ol class="timeline">'+h.map(x=>'<li><strong>第 '+e(x.version)+' 版</strong> · '+e(x.updatedAt||"-")+(x.change&&x.change.currentFocus?'：'+e(x.change.currentFocus):"")+'</li>').join("")+'</ol></section>';box.innerHTML=out}
function focusMessage(messageId){let target=q('[data-message-id="'+messageId+'"]');document.querySelectorAll('.message.highlight').forEach(x=>x.classList.remove('highlight'));if(target){target.classList.add('highlight');target.scrollIntoView({behavior:'smooth',block:'center'})}}
function show(d){state=d;q("#name").textContent=d.customerName;q("#meta").textContent="来源："+d.sourceLabel+" · 已同步 "+d.messages.length+" 条有效消息";q("#messages").innerHTML=d.messages.map(m=>'<div class="message '+m.role+'" data-message-id="'+e(m.messageId)+'"><span class="who">'+e(m.senderName)+'</span><span class="time">'+m.sentAt.slice(11,16)+'</span><p>'+e(m.text)+'</p></div>').join("");renderCustomerState(d);if(d.noNewMessages)q("#status").textContent="暂无新消息，已保留当前客户状态";if(!d.analysis)return;let a=d.analysis,g=a.group_chat,out='<p>'+e(a.summary)+'</p><h3>沟通阶段：'+e(d.callTypeLabel||a.classification.call_type)+'</h3>';if(g){out+=items("客户需求",g.customer_needs)+items("客户顾虑",g.customer_concerns)+items("销售回应覆盖",g.response_coverage)+items("销售承诺",g.sales_commitments)+items("待办事项",g.todos)+items("下一步建议",g.next_steps)}else{out+=items("客户目标",a.outcomes)+items("销售表现",a.coaching.strengths)+items("改进建议",a.coaching.improvements)}q("#report").innerHTML=out}
function followEvidence(x){let button=x.target.closest("[data-message-id]");if(button)focusMessage(button.dataset.messageId)}q("#report").onclick=followEvidence;q("#customer-state").onclick=followEvidence;
q("#go").onclick=async()=>{let b=q("#go");b.disabled=true;b.textContent="分析中…";q("#status").textContent="DeepSeek 分析中";try{let r=await fetch("/api/analyze",{method:"POST"}),d=await r.json();if(!r.ok)throw Error(d.error);show(d);q("#status").textContent="分析完成";b.textContent="重新分析"}catch(x){q("#report").className="error";q("#report").textContent="分析失败："+x.message;q("#status").textContent="分析失败"}finally{b.disabled=false}};
async function load(){try{let r=await fetch("/api/workbench");if(!r.ok)throw Error("群聊同步失败");show(await r.json())}catch(x){q("#status").textContent="同步失败"}}
load();setInterval(load, 3000)
</script>"""
