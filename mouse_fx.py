import sys
import os
import math
import random
import ctypes
from ctypes import wintypes
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QPointF, QSettings
from PySide6.QtGui import QColor, QPainter, QPen, QRadialGradient, QAction, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication, QWidget, QSystemTrayIcon, QMenu, QMainWindow,
    QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox,
    QSlider, QCheckBox, QColorDialog, QMessageBox
)

SETTINGS = QSettings("Xtremerpie", "MouseFX")
VK_F8 = 0x77
VK_LBUTTON = 0x01


def cursor_pos():
    point = wintypes.POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
    return QPointF(point.x, point.y)


def key_down(key):
    return bool(ctypes.windll.user32.GetAsyncKeyState(key) & 0x8000)


def startup_path():
    return (
        Path(os.environ["APPDATA"])
        / "Microsoft/Windows/Start Menu/Programs/Startup/MouseFX-start.bat"
    )


class Particle:
    def __init__(self, x, y, color, mode):
        angle = random.random() * math.tau
        speed = random.uniform(0.35, 1.8)

        self.x = x
        self.y = y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = self.max_life = random.randint(28, 48)
        self.radius = random.uniform(3.0, 7.0)
        self.color = QColor(color)
        self.mode = mode
        self.phase = random.random() * math.tau

    def update(self):
        self.life -= 1
        self.x += self.vx
        self.y += self.vy

        if self.mode == "Smoke":
            self.vy -= 0.025
            self.vx *= 0.99
        else:
            self.vx *= 0.975
            self.vy *= 0.975

        self.phase += 0.12

    def opacity(self):
        return max(0.0, self.life / self.max_life)


class Overlay(QWidget):
    def __init__(self):
        super().__init__()

        self.mode = SETTINGS.value("mode", "Neon")
        self.color = SETTINGS.value("color", "#31d9ff")
        self.density = int(SETTINGS.value("density", 4))
        self.enabled = SETTINGS.value("enabled", "true") == "true"

        self.particles = []
        self.last_pos = cursor_pos()
        self.last_click = False
        self.last_f8 = False

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        # Cover the virtual desktop, including secondary monitors.
        self.setGeometry(QApplication.primaryScreen().virtualGeometry())
        self.show()
        self.raise_()
        self.set_click_through()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(25)

    def set_click_through(self):
        try:
            user32 = ctypes.windll.user32
            hwnd = int(self.winId())
            style = user32.GetWindowLongW(hwnd, -20)
            style |= 0x00080000 | 0x00000020 | 0x00000080 | 0x08000000
            user32.SetWindowLongW(hwnd, -20, style)
        except Exception as error:
            print("Could not set click-through mode:", error)

    def configure(self, **values):
        for key, value in values.items():
            setattr(self, key, value)
            SETTINGS.setValue(
                key,
                ("true" if value else "false")
                if key == "enabled"
                else value,
            )

        if not self.enabled:
            self.particles.clear()

        self.update()

    def toggle(self):
        self.configure(enabled=not self.enabled)

    def tick(self):
        current = cursor_pos()
        distance = math.hypot(
            current.x() - self.last_pos.x(),
            current.y() - self.last_pos.y(),
        )

        if self.enabled and distance > 1:
            count = max(2, self.density)

            if distance > 18:
                count += 2

            for _ in range(count):
                self.particles.append(
                    Particle(current.x(), current.y(), self.color, self.mode)
                )

        click = key_down(VK_LBUTTON)
        if self.enabled and click and not self.last_click:
            for _ in range(22):
                self.particles.append(
                    Particle(current.x(), current.y(), self.color, self.mode)
                )

        self.last_click = click

        f8 = key_down(VK_F8)
        if f8 and not self.last_f8:
            self.toggle()
        self.last_f8 = f8
        self.last_pos = current

        for particle in self.particles:
            particle.update()

        self.particles = [
            particle for particle in self.particles if particle.life > 0
        ][-500:]

        self.update()

    def paintEvent(self, event):
        if not self.enabled:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        for particle in self.particles:
            x = particle.x - self.x()
            y = particle.y - self.y()

            if not (-30 < x < self.width() + 30 and
                    -30 < y < self.height() + 30):
                continue

            opacity = particle.opacity()
            radius = particle.radius * (0.65 + opacity * 0.35)

            if particle.mode == "Smoke":
                color = QColor(150, 190, 220)
                color.setAlphaF(opacity * 0.22)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(color)
                painter.drawEllipse(
                    QPointF(x, y), radius * 1.8, radius * 1.8
                )
                continue

            # Radial gradient creates a soft glow, not square particles.
            color = QColor(particle.color)
            color.setAlphaF(opacity * 0.85)

            gradient = QRadialGradient(QPointF(x, y), radius * 2.5)
            gradient.setColorAt(0.0, color)

            middle = QColor(particle.color)
            middle.setAlphaF(opacity * 0.30)
            gradient.setColorAt(0.45, middle)
            gradient.setColorAt(1.0, QColor(0, 0, 0, 0))

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(gradient)
            painter.drawEllipse(
                QPointF(x, y), radius * 2.5, radius * 2.5
            )

            if particle.mode == "Magic":
                core = QColor(235, 250, 255)
                core.setAlphaF(opacity)
                painter.setBrush(core)
                painter.drawEllipse(QPointF(x, y), 1.5, 1.5)

        painter.end()


class ControlPanel(QMainWindow):
    def __init__(self, overlay):
        super().__init__()
        self.overlay = overlay

        self.setWindowTitle("MouseFX Control Center")
        self.setMinimumWidth(380)

        root = QWidget()
        root.setStyleSheet("""
            QWidget {
                background: #101720;
                color: #eaf6ff;
                font-size: 13px;
            }
            QLabel#title {
                font-size: 25px;
                font-weight: bold;
                color: #53ddff;
            }
            QComboBox, QPushButton {
                background: #1b2a38;
                border: 1px solid #355064;
                padding: 8px;
                border-radius: 8px;
            }
            QSlider::groove:horizontal {
                height: 5px;
                background: #304454;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #53ddff;
                width: 15px;
                margin: -5px 0;
                border-radius: 7px;
            }
        """)

        layout = QVBoxLayout(root)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("MouseFX")
        title.setObjectName("title")
        layout.addWidget(title)
        layout.addWidget(QLabel("Smooth desktop cursor effects"))

        enabled = QCheckBox("Enable cursor effects")
        enabled.setChecked(overlay.enabled)
        enabled.toggled.connect(
            lambda value: overlay.configure(enabled=value)
        )
        layout.addWidget(enabled)

        layout.addWidget(QLabel("Effect style"))
        mode = QComboBox()
        mode.addItems(["Neon", "Fireflies", "Smoke", "Magic"])
        mode.setCurrentText(overlay.mode)
        mode.currentTextChanged.connect(
            lambda value: overlay.configure(mode=value)
        )
        layout.addWidget(mode)

        row = QHBoxLayout()
        row.addWidget(QLabel("Particle density"))
        density_value = QLabel(str(overlay.density))
        row.addStretch()
        row.addWidget(density_value)
        layout.addLayout(row)

        density = QSlider(Qt.Orientation.Horizontal)
        density.setRange(1, 8)
        density.setValue(overlay.density)

        def set_density(value):
            density_value.setText(str(value))
            overlay.configure(density=value)

        density.valueChanged.connect(set_density)
        layout.addWidget(density)

        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("Trail colour"))
        color_button = QPushButton("Choose colour")
        color_row.addWidget(color_button)
        layout.addLayout(color_row)

        def choose_color():
            color = QColorDialog.getColor(QColor(overlay.color), self)
            if color.isValid():
                overlay.configure(color=color.name())

        color_button.clicked.connect(choose_color)

        auto_start = QCheckBox("Start with Windows")
        auto_start.setChecked(startup_path().exists())
        auto_start.toggled.connect(self.set_autostart)
        layout.addWidget(auto_start)

        layout.addWidget(QLabel("F8: toggle effects  •  Click: glow burst"))

        buttons = QHBoxLayout()
        hide_button = QPushButton("Hide to tray")
        hide_button.clicked.connect(self.hide)
        buttons.addWidget(hide_button)

        quit_button = QPushButton("Quit MouseFX")
        quit_button.clicked.connect(QApplication.instance().quit)
        buttons.addWidget(quit_button)

        layout.addLayout(buttons)
        self.setCentralWidget(root)

    def set_autostart(self, enabled):
        try:
            path = startup_path()

            if enabled:
                path.parent.mkdir(parents=True, exist_ok=True)

                if getattr(sys, "frozen", False):
                    command = f'"{sys.executable}"'
                else:
                    command = f'"{sys.executable}" "{Path(__file__).resolve()}"'

                path.write_text(
                    '@echo off\r\nstart "" ' + command + '\r\n',
                    encoding="utf-8",
                )
            elif path.exists():
                path.unlink()

        except Exception as error:
            QMessageBox.warning(self, "Startup error", str(error))


def main():
    if sys.platform != "win32":
        print("MouseFX supports Windows only.")
        return

    app = QApplication(sys.argv)
    app.setApplicationName("MouseFX")
    app.setQuitOnLastWindowClosed(False)

    overlay = Overlay()
    panel = ControlPanel(overlay)

    # Give the tray icon a visible cyan design.
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#31d9ff"))
    painter.drawEllipse(3, 3, 26, 26)
    painter.setBrush(QColor("#101720"))
    painter.drawEllipse(11, 11, 10, 10)
    painter.end()

    tray = QSystemTrayIcon(QIcon(pixmap), app)
    tray.setToolTip("MouseFX - F8 toggles effects")

    menu = QMenu()
    show_action = QAction("Open Control Center", app)
    show_action.triggered.connect(
        lambda: (panel.show(), panel.raise_(), panel.activateWindow())
    )

    toggle_action = QAction("Toggle Effects (F8)", app)
    toggle_action.triggered.connect(overlay.toggle)

    quit_action = QAction("Quit MouseFX", app)
    quit_action.triggered.connect(app.quit)

    menu.addAction(show_action)
    menu.addAction(toggle_action)
    menu.addSeparator()
    menu.addAction(quit_action)
    tray.setContextMenu(menu)

    tray.activated.connect(
        lambda reason: (
            panel.show(), panel.raise_(), panel.activateWindow()
        )
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick
        else None
    )

    tray.show()

    # Open the settings panel every time the app starts.
    panel.show()
    panel.raise_()
    panel.activateWindow()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()