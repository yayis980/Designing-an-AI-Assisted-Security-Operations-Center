"""All styling for the app, written as a Qt style sheet (it works like CSS)."""

ACCENT = "#0B6E99"

STYLESHEET = """
QWidget {
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    font-size: 14px;
    color: #17202E;
}
QMainWindow { background: #F1F3F5; }
QScrollArea { border: none; background: #F1F3F5; }
#content { background: #F1F3F5; }

/* Sidebar */
#sidebar { background: #0F1B2D; }
#brand { color: #FFFFFF; font-size: 18px; font-weight: 600; }
#brandSub { color: #A9B6C8; font-size: 12px; }
#sidebarNote { color: #A9B6C8; font-size: 12px; }
#navLink {
    text-align: left; padding: 10px 12px; border: none; border-radius: 6px;
    color: #C9D3E0; background: transparent;
}
#navLink:hover, #navLink:focus { background: #1C2C45; color: #FFFFFF; }
#navLink[active="true"] { background: #1C2C45; color: #FFFFFF; font-weight: 600; }

/* Header */
#title { font-size: 28px; font-weight: 600; }
#subtitle { color: #4A5568; }

/* Buttons and inputs */
QPushButton#primary {
    background: #0B6E99; color: #FFFFFF; border: none; border-radius: 6px;
    padding: 0 18px; min-height: 40px; font-weight: 600;
}
QPushButton#primary:hover { background: #095A7E; }
QPushButton#primary:disabled { background: #8FB7C9; }
QLineEdit {
    min-height: 38px; padding: 0 12px; border: 1px solid #C5CCD6;
    border-radius: 6px; background: #FFFFFF; min-width: 240px;
}
QLineEdit:focus { border: 2px solid #0B6E99; }

QLabel#notice {
    background: #E8F4EC; color: #1F6B3A; border-radius: 8px;
    padding: 10px 14px; font-weight: 600;
}
QLabel#notice[error="true"] { background: #FCE4E4; color: #8F1D1D; }

/* Generic card */
QFrame#card { background: #FFFFFF; border: 1px solid #DDE2E9; border-radius: 10px; }
QLabel#eyebrow { color: #4A5568; font-size: 12px; font-weight: 600; }
QLabel#muted { color: #4A5568; }
QLabel#small { color: #4A5568; font-size: 12px; }

/* Server cards */
QFrame#serverCard { background: #FFFFFF; border: 2px solid #DDE2E9; border-radius: 10px; }
QFrame#serverCard:hover { border-color: #9DB7C6; }
QFrame#serverCard:focus { border-color: #0B6E99; }
QFrame#serverCard[selected="true"] { border-color: #0B6E99; }

/* Summary tiles */
QFrame#tile { background: #FFFFFF; border: 1px solid #DDE2E9; border-radius: 10px; }
QLabel#tileLabel { color: #4A5568; font-size: 12px; }

/* Pipeline */
QFrame#stage { background: #FFFFFF; border: 1px solid #DDE2E9; border-radius: 8px; }
QLabel#stageNum {
    background: #0F1B2D; color: #FFFFFF; border-radius: 11px;
    min-width: 22px; max-width: 22px; min-height: 22px; max-height: 22px;
    font-size: 12px; font-weight: 600;
}
QLabel#stageName { font-weight: 600; }
QLabel#stageDone { color: #1F6B3A; font-size: 12px; font-weight: 600; }

/* Findings */
QPushButton#pill {
    min-height: 34px; padding: 0 14px; border-radius: 17px;
    border: 1px solid #C5CCD6; background: #FFFFFF; font-weight: 600;
}
QPushButton#pill:hover { border-color: #0B6E99; }
QPushButton#pill:checked { background: #0B6E99; border-color: #0B6E99; color: #FFFFFF; }

QFrame#findingRow { background: #FFFFFF; border: 1px solid #DDE2E9; border-radius: 8px; }
QFrame#findingRow:hover { border-color: #9DB7C6; }
QFrame#findingRow:focus { border-color: #0B6E99; }
QFrame#findingRow[selected="true"] { border: 2px solid #0B6E99; background: #F3F9FC; }
QLabel#rowTitle { font-weight: 600; }

QLabel#empty {
    padding: 18px; color: #4A5568; border: 1px dashed #C5CCD6; border-radius: 8px;
}

/* Detail panel */
QLabel#detailTitle { font-size: 20px; font-weight: 600; }
QFrame#metaRule { background: #E6EAF0; max-height: 1px; min-height: 1px; border: none; }
QFrame#evidenceBlock { background: #F6F8FA; border: none; border-radius: 8px; }
QFrame#evidenceBlock[action="true"] { background: #FFFFFF; border: 1px solid #0B6E99; }
QLabel#evidenceLabel { color: #4A5568; font-size: 12px; font-weight: 600; }
QLabel#jsonBox {
    background: #0F1B2D; color: #DCE5F0; border-radius: 8px; padding: 14px;
    font-family: Consolas, "Cascadia Mono", "Courier New", monospace; font-size: 12px;
}
"""
