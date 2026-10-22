"""Small reusable pieces: labels, badges, clickable cards, and the severity bar."""

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath
from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy, QWidget

from .severity import SEVERITIES, SEVERITY_STYLES

MONO_FAMILIES = ["Consolas", "Cascadia Mono", "Courier New", "monospace"]


def make_label(text="", name=None, wrap=False, mono=False, size=None, bold=False, color=None):
    """Create a QLabel. `name` links it to a rule in theme.py."""
    label = QLabel(text)
    if name:
        label.setObjectName(name)
    label.setWordWrap(wrap)
    # Fonts are set through a style sheet: the app-wide style sheet in theme.py
    # would override anything set with QLabel.setFont().
    parts = []
    if mono:
        parts.append("font-family: " + ", ".join(f"'{f}'" for f in MONO_FAMILIES))
    if size:
        parts.append(f"font-size: {size}px")
    if bold:
        parts.append("font-weight: 600")
    if color:
        parts.append(f"color: {color}")
    if parts:
        label.setStyleSheet("; ".join(parts) + ";")
    return label


def make_badge(text, level):
    """Small colored pill showing a severity."""
    style = SEVERITY_STYLES[level]
    badge = QLabel(text)
    badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
    badge.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
    badge.setStyleSheet(
        f"background: {style['bg']}; color: {style['fg']}; border-radius: 10px;"
        "padding: 2px 10px; font-size: 12px; font-weight: 600;"
    )
    return badge


class ClickableFrame(QFrame):
    """A frame that acts like a button: click, or Tab to it and press Enter/Space."""

    clicked = Signal()

    def __init__(self, object_name):
        super().__init__()
        self.setObjectName(object_name)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def finish(self):
        """Call after adding child labels so clicks on them reach the frame."""
        for child in self.findChildren(QLabel):
            child.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def set_selected(self, selected):
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.position().toPoint()):
            self.clicked.emit()
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.clicked.emit()
        else:
            super().keyPressEvent(event)


class SeverityBarWidget(QWidget):
    """Stacked horizontal bar: one colored segment per severity."""

    def __init__(self):
        super().__init__()
        self.setFixedHeight(14)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._segments = []

    def set_counts(self, counts):
        total = sum(counts.values())
        self._segments = (
            [(counts[s] / total, SEVERITY_STYLES[s]["bar"]) for s in SEVERITIES if counts[s] > 0]
            if total
            else []
        )
        self.setAccessibleName(
            "Findings by severity: " + ", ".join(f"{counts[s]} {s}" for s in SEVERITIES)
        )
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect())
        clip = QPainterPath()
        clip.addRoundedRect(rect, 7, 7)
        painter.setClipPath(clip)
        painter.fillRect(rect, QColor("#E6EAF0"))
        gap = 2
        usable = rect.width() - gap * max(len(self._segments) - 1, 0)
        x = 0.0
        for fraction, color in self._segments:
            width = usable * fraction
            painter.fillRect(QRectF(x, 0, width, rect.height()), QColor(color))
            x += width + gap
        painter.end()
