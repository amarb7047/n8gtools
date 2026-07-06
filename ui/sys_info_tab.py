from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QColor, QPen, QFont
import platform
import psutil
import os

class CircularProgress(QWidget):
    def __init__(self, title, color_hex="#66FCF1"):
        super().__init__()
        self.title = title
        self.value = 0
        self.color = QColor(color_hex)
        self.setMinimumSize(150, 160)

    def set_value(self, val):
        self.value = max(0, min(100, val))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w = self.width()
        h = self.height()
        size = min(w, h) - 40
        x = (w - size) / 2
        y = (h - size - 20) / 2
        
        # Track Background Circle
        pen_bg = QPen(QColor("#161925"), 10)
        painter.setPen(pen_bg)
        painter.drawEllipse(QRectF(x, y, size, size))
        
        # Active Progress Arc (starts from 12 o'clock, spans clockwise)
        pen_fg = QPen(self.color, 10)
        pen_fg.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_fg)
        
        span_angle = -int(self.value * 3.6 * 16)
        painter.drawArc(QRectF(x, y, size, size), 90 * 16, span_angle)
        
        # Inner Value Text
        painter.setPen(QColor("#FFFFFF"))
        painter.setFont(QFont("Segoe UI", 18, QFont.Bold))
        text = f"{int(self.value)}%"
        painter.drawText(QRectF(x, y, size, size), Qt.AlignCenter, text)
        
        # Below Label Title
        painter.setPen(QColor("#8E9AAF"))
        painter.setFont(QFont("Segoe UI", 11, QFont.Bold))
        painter.drawText(QRectF(0, h - 30, w, 25), Qt.AlignCenter, self.title)


class SysInfoTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Title Card
        title_label = QLabel("System Performance Monitor")
        title_label.setObjectName("tabTitle")
        layout.addWidget(title_label)

        # Main Monitor Card
        monitor_card = QFrame()
        monitor_card.setObjectName("engineCard")
        monitor_card.setStyleSheet("""
            QFrame#engineCard {
                background-color: #1F2833;
                border: 1px solid #2D3748;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        monitor_layout = QHBoxLayout(monitor_card)
        monitor_layout.setSpacing(20)

        # Gauges
        self.cpu_gauge = CircularProgress("CPU Usage", "#66FCF1")
        self.ram_gauge = CircularProgress("RAM Usage", "#2ECC71")
        self.disk_gauge = CircularProgress("C: Disk Usage", "#E67E22")

        monitor_layout.addWidget(self.cpu_gauge)
        monitor_layout.addWidget(self.ram_gauge)
        monitor_layout.addWidget(self.disk_gauge)

        layout.addWidget(monitor_card)

        # System Information Details Card
        info_card = QFrame()
        info_card.setObjectName("infoCard")
        info_card.setStyleSheet("""
            QFrame#infoCard {
                background-color: #161925;
                border: 1px solid #2D3748;
                border-radius: 12px;
                padding: 25px;
            }
            QLabel {
                font-family: 'Segoe UI';
                font-size: 13px;
            }
            QLabel#labelTitle {
                color: #8E9AAF;
                font-weight: bold;
            }
            QLabel#labelVal {
                color: #FFFFFF;
                font-weight: 600;
            }
        """)
        
        info_layout = QGridLayout(info_card)
        info_layout.setSpacing(15)

        # Retrieve static system specs
        os_name = f"{platform.system()} {platform.release()} (Build {platform.version()})"
        cpu_name = platform.processor() or "AMD/Intel Processor"
        total_ram_gb = round(psutil.virtual_memory().total / (1024**3), 1)

        # 1. OS Info Row
        l_os_title = QLabel("Operating System:")
        l_os_title.setObjectName("labelTitle")
        self.l_os_val = QLabel(os_name)
        self.l_os_val.setObjectName("labelVal")
        info_layout.addWidget(l_os_title, 0, 0)
        info_layout.addWidget(self.l_os_val, 0, 1)

        # 2. CPU Specs Row
        l_cpu_title = QLabel("Processor Model:")
        l_cpu_title.setObjectName("labelTitle")
        self.l_cpu_val = QLabel(cpu_name)
        self.l_cpu_val.setObjectName("labelVal")
        self.l_cpu_val.setWordWrap(True)
        info_layout.addWidget(l_cpu_title, 1, 0)
        info_layout.addWidget(self.l_cpu_val, 1, 1)

        # 3. RAM Specs Row
        l_ram_title = QLabel("Total Installed Memory:")
        l_ram_title.setObjectName("labelTitle")
        self.l_ram_val = QLabel(f"{total_ram_gb} GB RAM")
        self.l_ram_val.setObjectName("labelVal")
        info_layout.addWidget(l_ram_title, 2, 0)
        info_layout.addWidget(self.l_ram_val, 2, 1)

        # 4. Storage Row
        l_disk_title = QLabel("System Storage Capacity:")
        l_disk_title.setObjectName("labelTitle")
        self.l_disk_val = QLabel("Calculating...")
        self.l_disk_val.setObjectName("labelVal")
        info_layout.addWidget(l_disk_title, 3, 0)
        info_layout.addWidget(self.l_disk_val, 3, 1)

        layout.addWidget(info_card)
        layout.addStretch()

        self.setLayout(layout)

    def update_stats(self, cpu, ram, disk_free, disk_used, disk_total):
        # Update circular progress views
        self.cpu_gauge.set_value(cpu)
        self.ram_gauge.set_value(ram)
        self.disk_gauge.set_value(disk_used)

        # Update text labels
        self.l_disk_val.setText(f"{disk_total:.1f} GB Total / {disk_free:.1f} GB Free")
