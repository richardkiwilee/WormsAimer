import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QComboBox, QSlider, QSpinBox,
                             QPushButton)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPainter, QPen, QColor

class TransparentCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        self.trajectory_points = []
        self.setMinimumSize(100, 100)
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 40);
                border-radius: 10px;
            }
        """)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw frosted glass effect background
        painter.fillRect(self.rect(), QColor(255, 255, 255, 40))
        
        # Set pen for trajectory
        pen = QPen(QColor(255, 0, 0, 200))
        pen.setWidth(2)
        painter.setPen(pen)
        
        # Draw trajectory points
        for point in self.trajectory_points:
            painter.drawPoint(point)
            
    def update_trajectory(self, points):
        self.trajectory_points = points
        self.update()

class AimerTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.oldPos = None
        
    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.oldPos:
            delta = event.globalPos() - self.oldPos
            self.move(self.pos() + delta)
            self.oldPos = event.globalPos()
        
    def initUI(self):
        # Set window flags
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Create main widget and layout
        main_widget = QWidget()
        main_widget.setStyleSheet("""
            QWidget#mainWidget {
                background-color: rgba(255, 255, 255, 180);
                border: 2px solid rgba(0, 0, 0, 100);
                border-radius: 10px;
            }
        """)
        main_widget.setObjectName("mainWidget")
        self.setCentralWidget(main_widget)
        
        # Create main vertical layout
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add title bar
        title_bar = QWidget()
        title_bar.setStyleSheet("""
            QWidget {
                background-color: rgba(60, 60, 60, 180);
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 0);
                border: none;
                color: white;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: rgba(255, 0, 0, 180);
            }
        """)
        title_bar.setFixedHeight(30)
        
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 0, 0)
        
        # Add title label
        title_label = QLabel('Aimer Tool')
        title_label.setStyleSheet('color: white; font-weight: bold;')
        title_layout.addWidget(title_label)
        
        # Add close button
        close_button = QPushButton('×')
        close_button.setFixedSize(30, 30)
        close_button.clicked.connect(self.close)
        title_layout.addWidget(close_button)
        
        main_layout.addWidget(title_bar)
        
        # Create content layout
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(10)
        
        # Left side - Transparent Canvas
        self.canvas = TransparentCanvas()
        
        # Right side - Controls
        controls_widget = QWidget()
        controls_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 180);
                border-radius: 10px;
            }
            QLabel {
                color: black;
                font-weight: bold;
            }
            QSpinBox, QComboBox, QSlider {
                background-color: rgba(255, 255, 255, 220);
                border: 1px solid gray;
                border-radius: 4px;
                padding: 2px;
            }
        """)
        controls_layout = QVBoxLayout(controls_widget)
        
        # Resolution selector
        res_label = QLabel('Canvas Resolution:')
        self.res_combo = QComboBox()
        self.res_combo.addItems(['1920x1440', '1600x900', '1366x768', '1280x720'])
        
        # Gravity control
        gravity_label = QLabel('Gravity (m/s²):')
        self.gravity_spin = QSpinBox()
        self.gravity_spin.setRange(1, 100)
        self.gravity_spin.setValue(9)
        
        # Initial velocity control
        velocity_label = QLabel('100% Power Velocity (m/s):')
        self.velocity_spin = QSpinBox()
        self.velocity_spin.setRange(1, 1000)
        self.velocity_spin.setValue(100)
        
        # Drawing radius control
        radius_label = QLabel('Drawing Radius (px):')
        self.radius_spin = QSpinBox()
        self.radius_spin.setRange(1, 50)
        self.radius_spin.setValue(5)
        
        # Wind control
        wind_label = QLabel('Wind Direction and Power:')
        self.wind_slider = QSlider(Qt.Horizontal)
        self.wind_slider.setRange(-100, 100)
        self.wind_slider.setValue(0)
        
        # Add all controls to layout
        controls_layout.addWidget(res_label)
        controls_layout.addWidget(self.res_combo)
        controls_layout.addWidget(gravity_label)
        controls_layout.addWidget(self.gravity_spin)
        controls_layout.addWidget(velocity_label)
        controls_layout.addWidget(self.velocity_spin)
        controls_layout.addWidget(radius_label)
        controls_layout.addWidget(self.radius_spin)
        controls_layout.addWidget(wind_label)
        controls_layout.addWidget(self.wind_slider)
        controls_layout.addStretch()
        
        # Add controls to content layout
        content_layout.addWidget(self.canvas)
        content_layout.addWidget(controls_widget)
        
        # Add content layout to main layout
        main_layout.addLayout(content_layout)
        
        # Store layouts as instance variables
        self.main_layout = main_layout
        self.content_layout = content_layout
        
        # Window settings
        self.setWindowTitle('Aimer Tool')
        
        # Set initial size based on default resolution
        self.update_canvas_size('1920x1440')
        
        # Connect signals
        self.res_combo.currentTextChanged.connect(self.update_canvas_size)
        self.wind_slider.valueChanged.connect(self.update_trajectory)
        self.gravity_spin.valueChanged.connect(self.update_trajectory)
        self.velocity_spin.valueChanged.connect(self.update_trajectory)
        
    def update_canvas_size(self, resolution):
        width, height = map(int, resolution.split('x'))
        self.canvas.setFixedSize(width, height)
        
        # Calculate the total window size based on canvas and controls
        controls_width = 200  # Fixed width for controls panel
        self.setFixedSize(width + controls_width + 20, height + 20)  # Add some padding
        
    def update_trajectory(self):
        # TODO: Implement trajectory calculation based on physics
        pass

def main():
    app = QApplication(sys.argv)
    tool = AimerTool()
    tool.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()