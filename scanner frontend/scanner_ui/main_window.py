"""The main window: sidebar on the left, scrolling dashboard on the right.

How it works, in short:
  * self.servers / self.server_id / self.filter_key / self.finding_id hold the state.
  * render_servers(), render_summary(), render_bottom() rebuild one part of the page
    from that state. Clicking something changes state, then calls the render methods.
  * Anything slow (network) runs in a Worker thread so the window never freezes.
"""

import json

from PySide6.QtCore import QPoint, QThread, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from . import api
from .severity import (
    SEVERITIES,
    SEVERITY_STYLES,
    count_by_severity,
    level_for_score,
)
from .widgets import (
    ClickableFrame,
    SeverityBarWidget,
    make_badge,
    make_label,
)


class Worker(QThread):
    """Runs one function off the UI thread and reports back with a signal."""

    succeeded = Signal(object)
    failed = Signal(str)

    def __init__(self, fn, *args):
        super().__init__()
        self._fn = fn
        self._args = args

    def run(self):
        try:
            self.succeeded.emit(self._fn(*self._args))
        except Exception as exc:  # shown to the user, not swallowed
            self.failed.emit(str(exc))


def clear_layout(layout):
    """Remove and delete everything inside a layout."""
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.setParent(None)
            widget.deleteLater()
        elif item.layout() is not None:
            clear_layout(item.layout())
            item.layout().deleteLater()


def make_card(title):
    """A white rounded panel with a small uppercase title. Returns (frame, layout)."""
    frame = QFrame()
    frame.setObjectName("card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(20, 18, 20, 18)
    layout.setSpacing(14)
    if title:
        layout.addWidget(make_label(title.upper(), "eyebrow"))
    return frame, layout


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MCP Scanner")
        self.resize(1360, 880)
        self.setMinimumSize(1000, 640)

        # State
        self.servers = []
        self.server_id = None
        self.filter_key = "all"
        self.finding_id = None
        self._workers = []

        self._build_shell()
        self._load_servers()

    def closeEvent(self, event):
        # Let any background request finish so Qt can shut down cleanly.
        for worker in list(self._workers):
            worker.wait(3000)
        super().closeEvent(event)

    # ------------------------------------------------------------------ shell

    def _build_shell(self):
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._build_sidebar())

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.content = QWidget()
        self.content.setObjectName("content")
        self.scroll.setWidget(self.content)
        outer.addWidget(self.scroll, 1)

        column = QVBoxLayout(self.content)
        column.setContentsMargins(32, 28, 32, 40)
        column.setSpacing(22)
        column.addLayout(self._build_header())

        self.status = make_label("Loading scan results...", "notice", wrap=True)
        column.addWidget(self.status)

        self.dashboard = QWidget()
        dash = QVBoxLayout(self.dashboard)
        dash.setContentsMargins(0, 0, 0, 0)
        dash.setSpacing(22)
        self.servers_box = self._section(dash, QVBoxLayout)
        self.summary_box = self._section(dash, QVBoxLayout)
        self.bottom_box = self._section(dash, QHBoxLayout)
        self.dashboard.hide()
        column.addWidget(self.dashboard)
        column.addStretch(1)

    @staticmethod
    def _section(parent_layout, layout_type):
        box = QWidget()
        layout = layout_type(box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14 if layout_type is QVBoxLayout else 18)
        parent_layout.addWidget(box)
        box.inner = layout
        return box

    def _build_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(230)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(18, 28, 18, 28)
        layout.setSpacing(4)

        layout.addWidget(make_label("MCP Scanner", "brand"))
        layout.addWidget(make_label("AI-assisted SOC", "brandSub"))
        layout.addSpacing(24)

        self.nav_buttons = []
        for text, target in (
            ("Overview", lambda: self._scroll_to(None)),
            ("Servers", lambda: self._scroll_to(self.servers_box)),
            ("Findings", lambda: self._scroll_to(getattr(self, "findings_card", None))),
            ("Evidence", lambda: self._scroll_to(getattr(self, "detail_card", None))),
        ):
            button = QPushButton(text)
            button.setObjectName("navLink")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setProperty("active", text == "Overview")
            button.clicked.connect(lambda _=False, b=button, t=target: self._on_nav(b, t))
            layout.addWidget(button)
            self.nav_buttons.append(button)

        layout.addStretch(1)
        layout.addWidget(
            make_label(
                "Prototype running on sample data. Switch to the real API in scanner_ui/api.py.",
                "sidebarNote",
                wrap=True,
            )
        )
        return sidebar

    def _build_header(self):
        header = QHBoxLayout()
        header.setSpacing(16)

        left = QVBoxLayout()
        left.setSpacing(4)
        left.addWidget(make_label("Scan overview", "title"))
        left.addWidget(
            make_label(
                "Servers scanned before deployment, with the evidence behind each finding.",
                "subtitle",
                wrap=True,
            )
        )
        header.addLayout(left, 1)

        right = QVBoxLayout()
        right.setSpacing(8)
        form = QHBoxLayout()
        form.setSpacing(8)
        self.scan_input = QLineEdit()
        self.scan_input.setPlaceholderText("Server path or URL")
        self.scan_input.setAccessibleName("MCP server path or URL")
        self.scan_input.returnPressed.connect(self._on_new_scan)
        self.scan_input.textChanged.connect(self._update_scan_button)
        self.scan_button = QPushButton("New scan")
        self.scan_button.setObjectName("primary")
        self.scan_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.scan_button.clicked.connect(self._on_new_scan)
        self.scan_button.setEnabled(False)
        form.addWidget(self.scan_input)
        form.addWidget(self.scan_button)
        right.addLayout(form)
        self.scan_notice = make_label("", "notice", wrap=True)
        self.scan_notice.hide()
        right.addWidget(self.scan_notice)
        header.addLayout(right)
        return header

    # --------------------------------------------------------------- loading

    def _run(self, fn, *args, on_ok, on_fail):
        worker = Worker(fn, *args)
        worker.succeeded.connect(on_ok)
        worker.failed.connect(on_fail)
        worker.finished.connect(lambda w=worker: self._workers.remove(w) if w in self._workers else None)
        self._workers.append(worker)
        worker.start()

    def _load_servers(self):
        self._run(api.fetch_servers, on_ok=self._servers_loaded, on_fail=self._servers_failed)

    def _servers_loaded(self, servers):
        self.servers = servers
        if not servers:
            self.status.setText("No servers have been scanned yet.")
            return
        self.server_id = servers[0]["id"]
        self.finding_id = servers[0]["findings"][0]["id"] if servers[0]["findings"] else None
        self.status.hide()
        self.dashboard.show()
        self.render_all()

    def _servers_failed(self, message):
        self.status.setText(f"Could not load results: {message}")
        self.status.setProperty("error", True)
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)

    # ------------------------------------------------------- state and events

    def current_server(self):
        for server in self.servers:
            if server["id"] == self.server_id:
                return server
        return self.servers[0] if self.servers else None

    def visible_findings(self):
        server = self.current_server()
        if not server:
            return []
        return [f for f in server["findings"] if self.filter_key == "all" or f["severity"] == self.filter_key]

    def current_finding(self):
        visible = self.visible_findings()
        for finding in visible:
            if finding["id"] == self.finding_id:
                return finding
        return visible[0] if visible else None  # selected one is hidden by the filter

    def select_server(self, server_id):
        self.server_id = server_id
        self.filter_key = "all"
        server = self.current_server()
        self.finding_id = server["findings"][0]["id"] if server and server["findings"] else None
        self.render_all()

    def select_filter(self, key):
        self.filter_key = key
        self.render_bottom()

    def select_finding(self, finding_id):
        self.finding_id = finding_id
        self.render_bottom()

    def _on_nav(self, button, target):
        for other in self.nav_buttons:
            other.setProperty("active", other is button)
            other.style().unpolish(other)
            other.style().polish(other)
        target()

    def _scroll_to(self, widget):
        bar = self.scroll.verticalScrollBar()
        if widget is None:
            bar.setValue(0)
            return
        y = widget.mapTo(self.content, QPoint(0, 0)).y()
        bar.setValue(max(0, y - 12))

    def _update_scan_button(self):
        self.scan_button.setEnabled(bool(self.scan_input.text().strip()))

    def _on_new_scan(self):
        target = self.scan_input.text().strip()
        if not target:
            return
        self.scan_button.setEnabled(False)
        self.scan_button.setText("Starting...")
        self.scan_notice.hide()
        self._run(api.start_scan, target, on_ok=self._scan_started, on_fail=self._scan_failed)

    def _finish_scan_ui(self, text, error):
        self.scan_button.setText("New scan")
        self._update_scan_button()
        self.scan_notice.setText(text)
        self.scan_notice.setProperty("error", error)
        self.scan_notice.style().unpolish(self.scan_notice)
        self.scan_notice.style().polish(self.scan_notice)
        self.scan_notice.show()

    def _scan_started(self, result):
        self.scan_input.clear()
        self._finish_scan_ui(result.get("message", "Scan started."), False)

    def _scan_failed(self, message):
        self._finish_scan_ui(message, True)

    # -------------------------------------------------------------- rendering

    def render_all(self):
        self.render_servers()
        self.render_summary()
        self.render_bottom()

    def render_servers(self):
        layout = self.servers_box.inner
        clear_layout(layout)
        layout.addWidget(make_label("SCANNED SERVERS", "eyebrow"))
        row = QHBoxLayout()
        row.setSpacing(14)
        for server in self.servers:
            row.addWidget(self._server_card(server), 1)
        layout.addLayout(row)

    def _server_card(self, server):
        level = level_for_score(server["risk_score"])
        card = ClickableFrame("serverCard")
        card.setProperty("selected", server["id"] == self.server_id)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        top = QHBoxLayout()
        top.addWidget(make_label(server["name"], mono=True, bold=True))
        top.addStretch(1)
        top.addWidget(make_badge(f"{level} {server['risk_score']}", level))
        layout.addLayout(top)
        layout.addWidget(make_label(server["description"], "muted", wrap=True))
        layout.addWidget(
            make_label(
                f"{server['tools_count']} tools · {len(server['findings'])} findings · scanned in {server['scan_time']}",
                "small",
                wrap=True,
            )
        )
        card.finish()
        card.clicked.connect(lambda sid=server["id"]: self.select_server(sid))
        return card

    def render_summary(self):
        layout = self.summary_box.inner
        clear_layout(layout)
        server = self.current_server()
        if not server:
            return

        tiles = QHBoxLayout()
        tiles.setSpacing(14)
        level = level_for_score(server["risk_score"])
        tiles.addWidget(self._tile("Risk score", str(server["risk_score"]), level), 1)
        tiles.addWidget(self._tile("Findings", str(len(server["findings"]))), 1)
        tiles.addWidget(self._tile("Tools analyzed", str(server["tools_count"])), 1)
        tiles.addWidget(self._tile("Scan time", server["scan_time"]), 1)
        layout.addLayout(tiles)

        # Severity breakdown
        counts = count_by_severity(server["findings"])
        card, card_layout = make_card("Severity breakdown")
        bar = SeverityBarWidget()
        bar.set_counts(counts)
        card_layout.addWidget(bar)
        legend = QHBoxLayout()
        legend.setSpacing(24)
        for sev in SEVERITIES:
            item = QHBoxLayout()
            item.setSpacing(8)
            swatch = QLabel()
            swatch.setFixedSize(10, 10)
            swatch.setStyleSheet(f"background: {SEVERITY_STYLES[sev]['bar']}; border-radius: 2px;")
            item.addWidget(swatch)
            item.addWidget(QLabel(sev))
            item.addWidget(make_label(str(counts[sev]), mono=True, bold=True))
            legend.addLayout(item)
        legend.addStretch(1)
        card_layout.addLayout(legend)
        layout.addWidget(card)

        # Pipeline
        card, card_layout = make_card("Scan pipeline")
        row = QHBoxLayout()
        row.setSpacing(12)
        stages = [
            ("Enumerate", f"{server['tools_count']} tools, {server['permissions_count']} permissions"),
            ("Static analysis", f"{server['static_hits']} rule hits"),
            ("Sandbox run", f"{server['sandbox_runs']} runs, {server['canary_hits']} canary hits"),
            ("Risk scoring", f"Score {server['risk_score']} of 100"),
            ("AI analysis", f"{server['ai_notes']} semantic notes"),
            ("Wazuh", f"{len(server['findings'])} events forwarded"),
        ]
        for number, (name, detail) in enumerate(stages, start=1):
            row.addWidget(self._stage(number, name, detail), 1)
        card_layout.addLayout(row)
        layout.addWidget(card)

    def _tile(self, label, value, level=None):
        tile = QFrame()
        tile.setObjectName("tile")
        layout = QVBoxLayout(tile)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(6)
        layout.addWidget(make_label(label, "tileLabel"))
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(make_label(value, mono=True, size=30, bold=True))
        if level:
            row.addWidget(
                make_label(level, bold=True, color=SEVERITY_STYLES[level]["fg"]),
                0,
                Qt.AlignmentFlag.AlignBottom,
            )
        row.addStretch(1)
        layout.addLayout(row)
        return tile

    def _stage(self, number, name, detail):
        stage = QFrame()
        stage.setObjectName("stage")
        layout = QVBoxLayout(stage)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)
        head = QHBoxLayout()
        head.setSpacing(8)
        num = make_label(str(number), "stageNum")
        num.setAlignment(Qt.AlignmentFlag.AlignCenter)
        head.addWidget(num)
        head.addWidget(make_label(name, "stageName", wrap=True), 1)
        layout.addLayout(head)
        layout.addWidget(make_label(detail, "small", wrap=True))
        layout.addWidget(make_label("Complete", "stageDone"))
        return stage

    def render_bottom(self):
        layout = self.bottom_box.inner
        clear_layout(layout)
        server = self.current_server()
        if not server:
            return
        self.findings_card = self._findings_card(server)
        self.detail_card = self._detail_card(server, self.current_finding())
        layout.addWidget(self.findings_card, 4, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.detail_card, 6, Qt.AlignmentFlag.AlignTop)

    def _findings_card(self, server):
        card, layout = make_card("Findings")
        counts = count_by_severity(server["findings"])

        pills = QHBoxLayout()
        pills.setSpacing(8)
        for key in ["all"] + SEVERITIES:
            total = len(server["findings"]) if key == "all" else counts[key]
            pill = QPushButton(f"{'All' if key == 'all' else key} {total}")
            pill.setObjectName("pill")
            pill.setCheckable(True)
            pill.setChecked(self.filter_key == key)
            pill.setCursor(Qt.CursorShape.PointingHandCursor)
            pill.clicked.connect(lambda _=False, k=key: self.select_filter(k))
            pills.addWidget(pill)
        pills.addStretch(1)
        layout.addLayout(pills)

        visible = self.visible_findings()
        if not visible:
            layout.addWidget(make_label("No findings at this severity for this server.", "empty", wrap=True))

        selected = self.current_finding()
        for finding in visible:
            layout.addWidget(self._finding_row(finding, selected is not None and finding["id"] == selected["id"]))
        return card

    def _finding_row(self, finding, selected):
        row = ClickableFrame("findingRow")
        row.setProperty("selected", selected)
        layout = QVBoxLayout(row)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)
        top = QHBoxLayout()
        top.setSpacing(10)
        top.addWidget(make_badge(finding["severity"], finding["severity"]))
        top.addWidget(make_label(finding["id"], "small", mono=True))
        top.addStretch(1)
        layout.addLayout(top)
        layout.addWidget(make_label(finding["title"], "rowTitle", wrap=True))
        layout.addWidget(make_label(f"Tool: {finding['tool']}", "small", wrap=True))
        row.finish()
        row.clicked.connect(lambda fid=finding["id"]: self.select_finding(fid))
        return row

    def _detail_card(self, server, finding):
        card, layout = make_card("Evidence")
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(18)

        if finding is None:
            layout.addWidget(make_label("Select a finding to see its evidence.", "empty", wrap=True))
            return card

        head = QVBoxLayout()
        head.setSpacing(8)
        top = QHBoxLayout()
        top.setSpacing(10)
        top.addWidget(make_badge(finding["severity"], finding["severity"]))
        top.addWidget(make_label(finding["id"], "small", mono=True))
        top.addStretch(1)
        head.addLayout(top)
        head.addWidget(make_label(finding["title"], "detailTitle", wrap=True))
        head.addWidget(make_label(finding["summary"], wrap=True))
        layout.addLayout(head)

        layout.addWidget(self._rule())
        meta = QHBoxLayout()
        meta.setSpacing(28)
        for label, value, mono in (
            ("Tool", finding["tool"], True),
            ("Category", finding["category"], False),
            ("Confidence", finding["confidence"], False),
            ("Wazuh rule", finding["rule_id"], True),
        ):
            cell = QVBoxLayout()
            cell.setSpacing(2)
            cell.addWidget(make_label(label, "small"))
            cell.addWidget(make_label(value, mono=mono, wrap=True))
            cell.addStretch(1)
            meta.addLayout(cell, 1)
        layout.addLayout(meta)
        layout.addWidget(self._rule())

        blocks = QVBoxLayout()
        blocks.setSpacing(12)
        blocks.addWidget(self._evidence_block("Static analysis", finding["evidence"]["static"]))
        blocks.addWidget(self._evidence_block("Sandbox run", finding["evidence"]["runtime"]))
        blocks.addWidget(self._evidence_block("AI semantic analysis", finding["evidence"]["ai"]))
        blocks.addWidget(self._evidence_block("Recommended action", finding["recommendation"], action=True))
        layout.addLayout(blocks)

        layout.addWidget(make_label("EVENT SENT TO WAZUH", "evidenceLabel"))
        event = {
            "source": "mcp-scanner",
            "server": server["name"],
            "tool": finding["tool"],
            "severity": finding["severity"].lower(),
            "rule_id": finding["rule_id"],
            "category": finding["category"],
            "evidence": finding["evidence"],
            "recommendation": finding["recommendation"],
        }
        json_label = make_label(json.dumps(event, indent=2), "jsonBox", wrap=True)
        json_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(json_label)
        return card

    @staticmethod
    def _rule():
        rule = QFrame()
        rule.setObjectName("metaRule")
        rule.setFrameShape(QFrame.Shape.NoFrame)
        rule.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return rule

    @staticmethod
    def _evidence_block(title, text, action=False):
        block = QFrame()
        block.setObjectName("evidenceBlock")
        block.setProperty("action", action)
        layout = QVBoxLayout(block)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)
        layout.addWidget(make_label(title.upper(), "evidenceLabel"))
        layout.addWidget(make_label(text, wrap=True))
        return block
