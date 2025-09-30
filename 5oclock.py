#!/usr/bin/env python3
"""
PyQt6 app that shows the COUNTRIES where it's currently 5 o'clock (5 PM local time).

• Display shows country NAMES ONLY as a simple list under the title:
    It's 5 O'Clock in:
• Automatically refreshes exactly at the top of every hour.
• A bottom "toast" appears on each refresh showing the last-updated time
  (local + UTC) and fades away like a notification.

Requirements (install if needed):
    pip install PyQt6 pytz

Run:
    python five_oclock_somewhere.py
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from typing import List, Set

import pytz
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QAction, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenuBar,
    QGraphicsOpacityEffect,
)

APP_TITLE = "It's 5 O'Clock Somewhere"
TARGET_HOUR = 17  # 5 PM


def countries_at_five_now() -> List[str]:
    """Return a sorted list of COUNTRY NAMES where it is currently 5 PM (any minute).

    We iterate through all pytz time zones, check local hour==17, then map those zones
    to the owning country/countries via pytz.country_timezones. Duplicates removed.
    """
    now_utc = datetime.now(timezone.utc)

    country_codes: Set[str] = set()
    for tzname in pytz.all_timezones:
        tz = pytz.timezone(tzname)
        local_now = now_utc.astimezone(tz)
        if local_now.hour != TARGET_HOUR:
            continue
        owners = [cc for cc, zones in pytz.country_timezones.items() if tzname in zones]
        if not owners:
            continue
        country_codes.update(owners)

    names = [pytz.country_names.get(cc, cc) for cc in country_codes]
    names = [n.upper() for n in names if n]
    names.sort()
    return names


class ToastLabel(QLabel):
    """A small, fading label shown near the bottom center like a toast notification."""

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setObjectName("toast")
        self.setStyleSheet(
            """
            QLabel#toast {
                background-color: rgba(20, 24, 28, 220);
                color: #e6ebef;
                border: 1px solid rgba(255,255,255,30);
                border-radius: 10px;
                padding: 8px 12px;
                font-weight: 600;
            }
            """
        )
        self.setVisible(False)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self._effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._effect)
        self._anim = QPropertyAnimation(self._effect, b"opacity", self)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._hold_timer = QTimer(self)
        self._hold_timer.setSingleShot(True)

    def reposition(self):
        if not self.parent():
            return
        p = self.parent().rect()
        x = p.x() + (p.width() - self.width()) // 2
        y = p.y() + p.height() - self.height() - 16
        self.move(x, y)

    def show_message(self, text: str, duration_ms: int = 3500, fade_ms: int = 600):
        self.setText(text)
        self.adjustSize()
        self.reposition()
        self.setVisible(True)
        self._anim.stop()
        self._effect.setOpacity(1.0)

        # After a short hold, fade out and hide
        def start_fade():
            self._anim.stop()
            self._anim.setDuration(max(100, fade_ms))
            self._anim.setStartValue(1.0)
            self._anim.setEndValue(0.0)
            def on_done():
                self.setVisible(False)
            try:
                self._anim.finished.disconnect()
            except Exception:
                pass
            self._anim.finished.connect(on_done)
            self._anim.start()

        self._hold_timer.stop()
        self._hold_timer.timeout.disconnect() if self._hold_timer.receivers(self._hold_timer.timeout) else None
        self._hold_timer.timeout.connect(start_fade)
        self._hold_timer.start(max(0, duration_ms - fade_ms))


class FiveOClockBoard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.setMinimumWidth(640)

        # Global styling for simple split‑flap vibe (no boxes, just lines)
        self.apply_style()

        # Menu bar
        self.menu_bar = QMenuBar(self)
        actions_menu = self.menu_bar.addMenu("&Actions")
        act_refresh = QAction("Refresh Now", self)
        act_refresh.triggered.connect(self.refresh)
        actions_menu.addAction(act_refresh)

        # Header
        self.header_label = QLabel("<div style='font-size:30px; font-weight:800; letter-spacing:1px;'>🌴&nbsp;&nbsp;It\'s 5 O\'Clock in:&nbsp;&nbsp;🌴</div>")
        self.header_label.setTextFormat(Qt.TextFormat.RichText)
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # Board list (countries only)
        self.board = QListWidget()
        self.board.setAlternatingRowColors(False)
        self.board.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        try:
            from PyQt6.QtWidgets import QFrame
            self.board.setFrameShape(QFrame.Shape.NoFrame)
        except Exception:
            pass
        self.board.setSpacing(0)

        # Use a bold, monospaced font to mimic a board
        board_font = QFont("Courier New")
        if not board_font.exactMatch():
            board_font = QFont("Monospace")
            board_font.setStyleHint(QFont.StyleHint.TypeWriter)
        board_font.setPointSize(14)
        board_font.setBold(True)
        board_font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 110)
        self.board.setFont(board_font)

        # Layout
        layout = QVBoxLayout(self)
        layout.setMenuBar(self.menu_bar)
        layout.addWidget(self.header_label)
        layout.addWidget(self.board, 1)

        # Toast overlay for "Last updated" notifications
        self.toast = ToastLabel(self)

        # Timers: refresh immediately, then exactly at each top-of-hour thereafter
        self._hourly_timer = QTimer(self)
        self._hourly_timer.setSingleShot(True)
        self._hourly_timer.timeout.connect(self._on_hour_boundary)

        self.refresh()
        self._schedule_next_hour_refresh()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.toast.isVisible():
            self.toast.reposition()

    def apply_style(self):
        # App-wide style with a single solid background color and simple list styling.
        # We target the root widget by objectName for reliable background rendering.
        self.setObjectName("root")
        self.setStyleSheet(
            """
            QWidget#root {
                background: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0,
                stop:0 #E9D59C,
                stop:0.5 #64B8B1,
                stop:1 #22BED9);
                color: #256940; 
            }
            QMenuBar { background: transparent; border: none; color: #256940; }
            QMenuBar::item { padding: 6px 10px; }
            QLabel { color: #256940; }

            QListWidget { border: none; background: transparent; color: #256940; }
            QListWidget::item { background: transparent; border: none; padding: 2px 0; margin: 0;}
            QListWidget::item:selected { background: transparent; }
            """
        )

    def _schedule_next_hour_refresh(self):
        # Compute seconds until the next top-of-hour and arm a single-shot timer.
        now = datetime.now()
        next_hour = (now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1))
        seconds = max(1, int((next_hour - now).total_seconds()))
        self._hourly_timer.start(seconds * 1000)

    def _on_hour_boundary(self):
        # At the hour boundary, refresh, then schedule the next one again (keeps us aligned across DST shifts)
        self.refresh()
        self._schedule_next_hour_refresh()

    def refresh(self):
        # Build list of countries
        names = countries_at_five_now()

        self.board.clear()
        if not names:
            self.board.addItem(QListWidgetItem("NO COUNTRIES AT 5 PM RIGHT NOW"))
        else:
            for name in names:
                item = QListWidgetItem(name)
                item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                self.board.addItem(item)

        # Show a toast with the current update time (UTC + local)
        local_now = datetime.now().astimezone()
        utc_now = datetime.now(timezone.utc)
        local_tz = local_now.tzname()
        msg = (
            f"Last updated: {local_now.strftime('%Y-%m-%d %H:%M:%S')} {local_tz} · "
            f"UTC {utc_now.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        self.toast.show_message(msg)


def main():
    app = QApplication(sys.argv)
    win = FiveOClockBoard()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
