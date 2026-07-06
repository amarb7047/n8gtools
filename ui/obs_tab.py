from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QScrollArea, QGroupBox, QComboBox, QSlider, QGridLayout, QFrame)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPainter, QColor, QLinearGradient, QPen, QBrush, QFont, QPolygon

class GamePreviewWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(320, 180)
        self.setMaximumSize(450, 240)
        self.hdr_factor = 0.5  # 0.0 (Normal) to 1.0 (HDR)
        
    def set_hdr_factor(self, factor):
        self.hdr_factor = factor
        self.update()

    def interpolate_color(self, c1, c2, factor):
        r = int(c1.red() + (c2.red() - c1.red()) * factor)
        g = int(c1.green() + (c2.green() - c1.green()) * factor)
        b = int(c1.blue() + (c2.blue() - c1.blue()) * factor)
        return QColor(r, g, b)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Geometry
        w = self.width()
        h = self.height()
        
        # Color palettes
        # Sky: Dull grey/blue to sunset orange/purple
        sky_top_normal = QColor(100, 115, 130)
        sky_bottom_normal = QColor(135, 125, 120)
        sky_top_hdr = QColor(30, 20, 90)
        sky_bottom_hdr = QColor(255, 69, 0)
        
        sky_top = self.interpolate_color(sky_top_normal, sky_top_hdr, self.hdr_factor)
        sky_bottom = self.interpolate_color(sky_bottom_normal, sky_bottom_hdr, self.hdr_factor)
        
        # Draw Sky Gradient
        sky_grad = QLinearGradient(0, 0, 0, h)
        sky_grad.setColorAt(0.0, sky_top)
        sky_grad.setColorAt(1.0, sky_bottom)
        painter.fillRect(0, 0, w, h, sky_grad)
        
        # Draw Sun
        sun_color_normal = QColor(220, 220, 200, 180)
        sun_color_hdr = QColor(255, 223, 0, 240)
        sun_color = self.interpolate_color(sun_color_normal, sun_color_hdr, self.hdr_factor)
        
        painter.setPen(Qt.NoPen)
        # Glow ring
        glow_color = QColor(sun_color.red(), sun_color.green(), sun_color.blue(), int(40 * self.hdr_factor))
        painter.setBrush(QBrush(glow_color))
        painter.drawEllipse(int(w * 0.75) - 30, int(h * 0.3) - 30, 60, 60)
        # Inner Sun
        painter.setBrush(QBrush(sun_color))
        painter.drawEllipse(int(w * 0.75) - 15, int(h * 0.3) - 15, 30, 30)

        # Draw Mountains
        # Mountains normal: dull grey/green
        mountains_normal_1 = QColor(80, 85, 90)
        mountains_normal_2 = QColor(60, 65, 70)
        # Mountains HDR: vibrant forest emerald to rich purple
        mountains_hdr_1 = QColor(15, 120, 80)
        mountains_hdr_2 = QColor(75, 0, 130)
        
        m1_color = self.interpolate_color(mountains_normal_1, mountains_hdr_1, self.hdr_factor)
        m2_color = self.interpolate_color(mountains_normal_2, mountains_hdr_2, self.hdr_factor)
        
        # Far mountain
        painter.setBrush(QBrush(m2_color))
        painter.drawPolygon(self.make_mountain_poly(w, h, start_pct=0.0, peak_pct=0.35, end_pct=0.8, height_pct=0.55))
        
        # Near mountain
        painter.setBrush(QBrush(m1_color))
        painter.drawPolygon(self.make_mountain_poly(w, h, start_pct=0.3, peak_pct=0.65, end_pct=1.0, height_pct=0.45))

        # Ground
        ground_normal = QColor(70, 75, 70)
        ground_hdr = QColor(10, 80, 30)
        ground_color = self.interpolate_color(ground_normal, ground_hdr, self.hdr_factor)
        painter.fillRect(0, int(h * 0.8), w, int(h * 0.2), ground_color)

        # Draw Game HUD (Health/Shield Bar and MiniMap)
        # Minimap (top left)
        painter.setPen(QPen(QColor(255, 255, 255, 100), 1))
        painter.setBrush(QBrush(QColor(0, 0, 0, 80)))
        painter.drawRect(10, 10, 35, 35)
        # Map dots
        dot_color_normal = QColor(120, 120, 120)
        dot_color_hdr = QColor(255, 0, 100)
        dot_color = self.interpolate_color(dot_color_normal, dot_color_hdr, self.hdr_factor)
        painter.setBrush(QBrush(dot_color))
        painter.drawEllipse(25, 25, 6, 6)

        # Health / Shield bars (bottom left)
        # Shield Bar (top)
        shield_normal = QColor(120, 120, 180)
        shield_hdr = QColor(0, 180, 255)
        shield_color = self.interpolate_color(shield_normal, shield_hdr, self.hdr_factor)
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 150)))
        painter.drawRect(10, h - 35, 80, 6)
        painter.setBrush(QBrush(shield_color))
        painter.drawRect(10, h - 35, int(80 * 0.8), 6) # 80% shield
        
        # Health Bar (bottom)
        health_normal = QColor(120, 180, 120)
        health_hdr = QColor(0, 255, 100)
        health_color = self.interpolate_color(health_normal, health_hdr, self.hdr_factor)
        
        painter.setBrush(QBrush(QColor(0, 0, 0, 150)))
        painter.drawRect(10, h - 25, 80, 6)
        painter.setBrush(QBrush(health_color))
        painter.drawRect(10, h - 25, int(80 * 0.95), 6) # 95% health
        
        # Ammo HUD (bottom right)
        ammo_color_normal = QColor(180, 180, 180)
        ammo_color_hdr = QColor(255, 215, 0)
        ammo_color = self.interpolate_color(ammo_color_normal, ammo_color_hdr, self.hdr_factor)
        painter.setPen(QPen(ammo_color))
        painter.setFont(QFont("Arial", 8, QFont.Bold))
        painter.drawText(w - 60, h - 15, "30 / 90")

        # Draw Title/Watermark on preview
        painter.setPen(QPen(QColor(255, 255, 255, 120)))
        painter.setFont(QFont("Arial", 7, QFont.Bold))
        painter.drawText(w - 75, 20, "HDR PREVIEW")

    def make_mountain_poly(self, w, h, start_pct, peak_pct, end_pct, height_pct):
        poly = QPolygon()
        poly.append(QPoint(int(w * start_pct), int(h * 0.8)))
        poly.append(QPoint(int(w * peak_pct), int(h * (0.8 - height_pct))))
        poly.append(QPoint(int(w * end_pct), int(h * 0.8)))
        return poly

class ObsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(15)

        # Title Card
        title_label = QLabel("OBS Studio HDR & 4K Stream Guide")
        title_label.setObjectName("tabTitle")
        main_layout.addWidget(title_label)

        # Horizontal Split Layout
        split_layout = QHBoxLayout()
        split_layout.setSpacing(20)

        # --- Left Panel: Presets, Sliders, and OBS values ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(15)

        # Presets Group Box
        preset_group = QGroupBox("1. Choose HDR Preset")
        preset_group.setObjectName("settingsGroup")
        preset_form = QVBoxLayout(preset_group)
        preset_form.setSpacing(10)

        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "Vibrant Pro (Recommended for PUBG/Free Fire)",
            "Ultra HDR Mode (Deep contrast & neon colors)",
            "Cinematic 4K (Balanced & natural colors)",
            "Custom Tuning"
        ])
        self.preset_combo.setMinimumHeight(35)
        self.preset_combo.currentIndexChanged.connect(self.preset_changed)
        preset_form.addWidget(self.preset_combo)
        left_layout.addWidget(preset_group)

        # Sliders Group Box
        slider_group = QGroupBox("2. Fine-tune Colors")
        slider_group.setObjectName("settingsGroup")
        slider_grid = QGridLayout(slider_group)
        slider_grid.setSpacing(10)

        # Saturation Slider
        slider_grid.addWidget(QLabel("HDR Color Boost (Saturation):"), 0, 0)
        self.sat_slider = QSlider(Qt.Horizontal)
        self.sat_slider.setRange(0, 100)
        self.sat_slider.setValue(60)
        self.sat_slider.valueChanged.connect(self.slider_values_changed)
        slider_grid.addWidget(self.sat_slider, 0, 1)

        # Contrast Slider
        slider_grid.addWidget(QLabel("HDR Contrast Enhancer:"), 1, 0)
        self.con_slider = QSlider(Qt.Horizontal)
        self.con_slider.setRange(0, 100)
        self.con_slider.setValue(55)
        self.con_slider.valueChanged.connect(self.slider_values_changed)
        slider_grid.addWidget(self.con_slider, 1, 1)

        # Sharpness Slider
        slider_grid.addWidget(QLabel("4K Sharpness Enhancer:"), 2, 0)
        self.sharp_slider = QSlider(Qt.Horizontal)
        self.sharp_slider.setRange(0, 100)
        self.sharp_slider.setValue(40)
        self.sharp_slider.valueChanged.connect(self.slider_values_changed)
        slider_grid.addWidget(self.sharp_slider, 2, 1)

        left_layout.addWidget(slider_group)

        # OBS Settings Values Group Box
        values_group = QGroupBox("3. Copy values into OBS Filters")
        values_group.setObjectName("settingsGroup")
        values_layout = QGridLayout(values_group)
        values_layout.setSpacing(12)

        # Column headers
        values_layout.addWidget(QLabel("<b>OBS Filter Name</b>"), 0, 0)
        values_layout.addWidget(QLabel("<b>Parameter</b>"), 0, 1)
        values_layout.addWidget(QLabel("<b>Setting Value</b>"), 0, 2)

        # Divider
        div1 = QFrame()
        div1.setFrameShape(QFrame.HLine)
        div1.setStyleSheet("background-color: #2D3748;")
        values_layout.addWidget(div1, 1, 0, 1, 3)

        # Color Correction values
        values_layout.addWidget(QLabel("Color Correction"), 2, 0)
        values_layout.addWidget(QLabel("Gamma:"), 2, 1)
        self.val_gamma = QLabel("-0.08")
        self.val_gamma.setStyleSheet("color: #66FCF1; font-weight: bold;")
        values_layout.addWidget(self.val_gamma, 2, 2)

        values_layout.addWidget(QLabel(""), 3, 0)
        values_layout.addWidget(QLabel("Contrast:"), 3, 1)
        self.val_contrast = QLabel("0.12")
        self.val_contrast.setStyleSheet("color: #66FCF1; font-weight: bold;")
        values_layout.addWidget(self.val_contrast, 3, 2)

        values_layout.addWidget(QLabel(""), 4, 0)
        values_layout.addWidget(QLabel("Saturation:"), 4, 1)
        self.val_saturation = QLabel("0.24")
        self.val_saturation.setStyleSheet("color: #66FCF1; font-weight: bold;")
        values_layout.addWidget(self.val_saturation, 4, 2)

        # Divider 2
        div2 = QFrame()
        div2.setFrameShape(QFrame.HLine)
        div2.setStyleSheet("background-color: #2D3748;")
        values_layout.addWidget(div2, 5, 0, 1, 3)

        # Sharpen value
        values_layout.addWidget(QLabel("Sharpen"), 6, 0)
        values_layout.addWidget(QLabel("Sharpness:"), 6, 1)
        self.val_sharpness = QLabel("0.08")
        self.val_sharpness.setStyleSheet("color: #66FCF1; font-weight: bold;")
        values_layout.addWidget(self.val_sharpness, 6, 2)

        left_layout.addWidget(values_group)
        left_layout.addStretch()

        split_layout.addWidget(left_panel, 1)

        # --- Right Panel: Preview and Step-by-step instructions ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(15)

        # Live Preview Group Box
        preview_group = QGroupBox("Real-time HDR & 4K Simulator Preview")
        preview_group.setObjectName("settingsGroup")
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setContentsMargins(15, 15, 15, 15)
        
        self.preview_widget = GamePreviewWidget()
        preview_layout.addWidget(self.preview_widget)
        right_layout.addWidget(preview_group)

        # OBS Step-by-step instructions scroll area
        instructions_group = QGroupBox("Step-by-step OBS Setup Guide")
        instructions_group.setObjectName("settingsGroup")
        inst_layout = QVBoxLayout(instructions_group)
        inst_layout.setContentsMargins(15, 15, 15, 15)

        guide_scroll = QScrollArea()
        guide_scroll.setWidgetResizable(True)
        guide_scroll.setObjectName("guideScroll")
        guide_scroll.setStyleSheet("background-color: transparent; border: none;")
        guide_scroll.viewport().setStyleSheet("background-color: transparent;")
        
        guide_content = QWidget()
        guide_content.setStyleSheet("background-color: transparent;")
        guide_content_layout = QVBoxLayout(guide_content)
        guide_content_layout.setContentsMargins(0, 0, 0, 0)
        guide_content_layout.setSpacing(10)

        guide_text = (
            "<h3>How to apply these filters in OBS Studio:</h3>"
            "<ol>"
            "  <li>In the OBS <b>Sources</b> panel, right-click your <code>Window Capture</code> source (Android/iOS mirror) and select <b>Filters</b>.</li>"
            "  <li>Click the <b>'+'</b> button in the bottom-left of the filters window:</li>"
            "  <ul>"
            "    <li>Select <b>Color Correction</b>. Copy the <b>Gamma</b>, <b>Contrast</b>, and <b>Saturation</b> values shown on the left into their respective sliders.</li>"
            "    <li>Select <b>Sharpen</b>. Copy the <b>Sharpness</b> value shown on the left.</li>"
            "  </ul>"
            "  <li>Click Close. Your stream will now look beautifully vibrant, sharp, and HDR-like!</li>"
            "</ol>"
            "<hr/>"
            "<h3>General Stream Setup Guide:</h3>"
            "<ol>"
            "  <li><b>Window Capture Method:</b> If your captured window shows a black screen, change <b>Capture Method</b> in OBS from 'Automatic' to <b>'Windows 10 (1903 and up)'</b>. This fixes it instantly!</li>"
            "  <li><b>Audio Setup:</b> OBS will automatically capture the game sound via your desktop audio. Make sure <b>Desktop Audio</b> is enabled in OBS Audio settings and use headphones to avoid echo.</li>"
            "  <li><b>Smooth Stream:</b> For zero lag, run OBS as Administrator and ensure both OBS and HeroRec are utilizing the same dedicated GPU.</li>"
            "</ol>"
        )

        guide_label = QLabel(guide_text)
        guide_label.setTextFormat(Qt.RichText)
        guide_label.setWordWrap(True)
        guide_label.setObjectName("guideText")
        guide_label.setStyleSheet("color: #E2E8F0; background-color: transparent;")
        guide_content_layout.addWidget(guide_label)
        guide_content_layout.addStretch()
        
        guide_scroll.setWidget(guide_content)
        inst_layout.addWidget(guide_scroll)
        right_layout.addWidget(instructions_group)

        split_layout.addWidget(right_panel, 1)

        main_layout.addLayout(split_layout)
        self.setLayout(main_layout)
        
        # Trigger initial values
        self.slider_values_changed()

    def preset_changed(self, index):
        # Prevent recursion by blocking signals temporarily
        self.sat_slider.blockSignals(True)
        self.con_slider.blockSignals(True)
        self.sharp_slider.blockSignals(True)

        if index == 0:  # Vibrant Pro
            self.sat_slider.setValue(60)
            self.con_slider.setValue(55)
            self.sharp_slider.setValue(40)
        elif index == 1:  # Ultra HDR
            self.sat_slider.setValue(85)
            self.con_slider.setValue(70)
            self.sharp_slider.setValue(60)
        elif index == 2:  # Cinematic 4K
            self.sat_slider.setValue(40)
            self.con_slider.setValue(45)
            self.sharp_slider.setValue(50)

        self.sat_slider.blockSignals(False)
        self.con_slider.blockSignals(False)
        self.sharp_slider.blockSignals(False)
        
        self.slider_values_changed()

    def slider_values_changed(self):
        # Calculate values to display
        sat_val = self.sat_slider.value()
        con_val = self.con_slider.value()
        sharp_val = self.sharp_slider.value()

        # If user moves sliders manually, change preset selection to "Custom Tuning"
        if self.sender() in [self.sat_slider, self.con_slider, self.sharp_slider]:
            self.preset_combo.blockSignals(True)
            self.preset_combo.setCurrentIndex(3) # Custom Tuning
            self.preset_combo.blockSignals(False)

        # Scale slider values to OBS ranges
        # Gamma: 0.00 to -0.15 (mapped from contrast slider, higher contrast -> lower gamma)
        gamma = -0.02 - (con_val / 100.0) * 0.12
        # Contrast: 0.00 to 0.25
        contrast = (con_val / 100.0) * 0.25
        # Saturation: 0.00 to 0.50
        saturation = (sat_val / 100.0) * 0.45
        # Sharpness: 0.00 to 0.25
        sharpness = (sharp_val / 100.0) * 0.22

        # Update labels
        self.val_gamma.setText(f"{gamma:.2f}")
        self.val_contrast.setText(f"{contrast:.2f}")
        self.val_saturation.setText(f"{saturation:.2f}")
        self.val_sharpness.setText(f"{sharpness:.2f}")

        # Update preview widget factor (blend based on average of sat and con)
        factor = (sat_val * 0.6 + con_val * 0.4) / 100.0
        self.preview_widget.set_hdr_factor(factor)
