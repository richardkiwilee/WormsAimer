import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QComboBox, QSlider, QSpinBox)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPainter, QPen, QColor

class TransparentCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        self.trajectory_points = []
        self.setMinimumSize(100, 100)  # Set minimum size to ensure visibility
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background with semi-transparent color to make canvas visible
        painter.fillRect(self.rect(), QColor(0, 0, 0, 30))
        
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
        
    def initUI(self):
        # Set window flags to prevent resizing
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.MSWindowsFixedSizeDialogHint)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Left side - Transparent Canvas
        self.canvas = TransparentCanvas()
        layout.addWidget(self.canvas)
        
        # Right side - Controls
        controls_widget = QWidget()
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
        
        # Add controls to main layout
        layout.addWidget(controls_widget)
        
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