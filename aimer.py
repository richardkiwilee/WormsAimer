import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QSlider, QSpinBox,
                             QPushButton, QSplitter, QDesktopWidget)
from PyQt5.QtCore import Qt, QPoint, QPointF
from PyQt5.QtGui import QPainter, QPen, QColor
import math

LEFT_SPACE = 400

class TransparentCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        self.setMinimumSize(100, 100)
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 40);
                border-radius: 10px;
            }
        """)
        
        # Initialize variables
        self.center_point = None
        self.current_point = None
        self.last_angle = None  # Store last angle for helper lines
        self.last_power = None  # Store last power for helper circle
        self.max_radius = None  # Will be set from main window
        self.gravity = 10      # Will be set from main window (pixels/sec^2)
        self.max_velocity = 100 # Will be set from main window (pixels/sec)
        self.trajectory_points = []
        self.time_points = []  # Points at each second
        self.setMouseTracking(True)  # Enable mouse tracking for better interaction
        
    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            # Clear previous trajectory and set new center point
            self.center_point = event.pos()
            self.current_point = None
            self.last_angle = None
            self.last_power = None
            self.trajectory_points = []
            self.time_points = []
            self.update()
        elif event.button() == Qt.LeftButton and self.center_point:
            # Start trajectory calculation
            self.current_point = event.pos()
            self.calculate_trajectory()
            
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self.center_point:
            self.current_point = event.pos()
            self.calculate_trajectory()
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Store the last angle and power before clearing current point
            if self.center_point and self.current_point:
                dx = self.current_point.x() - self.center_point.x()
                dy = self.current_point.y() - self.center_point.y()
                self.last_angle = math.atan2(-dy, dx)
                
                distance = math.sqrt(dx * dx + dy * dy)
                self.last_power = min(100, (distance / self.max_radius * 100) if self.max_radius else 100)
            
            self.current_point = None
            self.update()
            
    def calculate_power(self):
        if not self.center_point or not self.current_point:
            return 0
        
        # Calculate distance between center and current point
        distance = math.sqrt(
            (self.current_point.x() - self.center_point.x()) ** 2 +
            (self.current_point.y() - self.center_point.y()) ** 2
        )
        
        # If max_radius is not set, use the distance directly
        if self.max_radius is None:
            return 100
            
        # If distance is greater than max_radius, return 100% power
        if distance > self.max_radius:
            return 100
            
        # Calculate power percentage (0-100)
        power = (distance / self.max_radius) * 100
        return power
        
    def calculate_angle(self):
        if not self.center_point or not self.current_point:
            return 0
            
        # Calculate angle in radians
        dx = self.current_point.x() - self.center_point.x()
        dy = self.center_point.y() - self.current_point.y()  # Inverted Y axis
        angle = math.atan2(dy, dx)
        return angle
        
    def calculate_trajectory(self):
        if not self.center_point or not self.current_point:
            return
            
        # Calculate angle and initial velocity
        dx = self.current_point.x() - self.center_point.x()
        dy = self.current_point.y() - self.center_point.y()
        angle = math.atan2(-dy, dx)  # Negative because y is inverted in screen coordinates
        
        # Calculate power (0-100%)
        power = self.calculate_power()
        
        # Calculate initial velocity components
        v0 = self.max_velocity * (power / 100)
        v0x = v0 * math.cos(angle)
        v0y = v0 * math.sin(angle)
        
        # Calculate points
        points = []
        time_points = []
        t = 0
        dt = 0.1  # Time step
        x0 = self.center_point.x()
        y0 = self.center_point.y()
        
        # Keep calculating points until trajectory goes out of bounds
        while True:
            x = x0 + v0x * t
            y = y0 - (v0y * t - 0.5 * self.gravity * t * t)  # Subtract because Y is inverted
            
            # Check if point is out of bounds
            if x < 0 or x > self.width() or y < 0 or y > self.height():
                break
                
            point = QPointF(x, y)
            points.append(point)
            
            # Store points at each second for the first 6 seconds
            if abs(t % 1.0) < 0.05 and len(time_points) < 6:  # Use 0.05 to handle floating point imprecision
                time_points.append(point)
            
            t += dt
        
        self.trajectory_points = points
        self.time_points = time_points
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw frosted glass effect background
        painter.fillRect(self.rect(), QColor(255, 255, 255, 40))
        
        # Draw center point and radius circle if center is set
        if self.center_point:
            # Draw max radius circle first (so it's behind the center point)
            painter.setPen(QPen(QColor(0, 0, 139, 180), 2))  # Dark blue, slightly thicker
            if self.max_radius:
                painter.drawEllipse(self.center_point, self.max_radius, self.max_radius)
            
            # Draw center point on top
            painter.setPen(QPen(QColor(255, 0, 0, 255), 8))  # Larger red dot
            painter.drawPoint(self.center_point)
        
        # Draw helper lines if we have a center point and either current point or last angle
        if self.center_point and (self.current_point or self.last_angle is not None):
            if self.current_point:
                # Calculate current angle and power
                dx = self.current_point.x() - self.center_point.x()
                dy = self.current_point.y() - self.center_point.y()
                angle = math.atan2(-dy, dx)
                distance = math.sqrt(dx * dx + dy * dy)
                power = min(100, (distance / self.max_radius * 100) if self.max_radius else 100)
            else:
                # Use last stored angle and power
                angle = self.last_angle
                power = self.last_power
            
            # Draw radius line (red)
            painter.setPen(QPen(QColor(255, 0, 0, 200), 2))
            end_x = self.center_point.x() + math.cos(angle) * (self.max_radius or 200)
            end_y = self.center_point.y() - math.sin(angle) * (self.max_radius or 200)
            painter.drawLine(self.center_point, QPointF(end_x, end_y))
            
            # Draw power circle (red, smaller than max radius)
            radius = (self.max_radius or 200) * (power / 100)
            painter.setPen(QPen(QColor(255, 0, 0, 200), 2))
            painter.drawEllipse(self.center_point, radius, radius)
            
            # Draw power line (yellow)
            if self.current_point:
                painter.setPen(QPen(QColor(255, 255, 0, 200), 2))
                painter.drawLine(self.center_point, self.current_point)
        
        # Draw trajectory
        if self.trajectory_points:
            # Draw trajectory line
            painter.setPen(QPen(QColor(255, 0, 0, 200), 2))
            for i in range(len(self.trajectory_points) - 1):
                painter.drawLine(self.trajectory_points[i], self.trajectory_points[i + 1])
            
            # Draw time points with larger dots and labels
            painter.setPen(QPen(QColor(0, 0, 255, 200), 8))
            font = painter.font()
            font.setPointSize(10)
            painter.setFont(font)
            
            for i, point in enumerate(self.time_points):
                # Draw larger point
                painter.drawPoint(point)
                
                # Draw time label
                painter.drawText(
                    int(point.x()) + 10,
                    int(point.y()) - 10,
                    f"{i+1}s"
                )
    
    def set_parameters(self, max_radius, gravity, max_velocity):
        self.max_radius = max_radius
        self.gravity = gravity
        self.max_velocity = max_velocity
        if self.center_point and self.current_point:
            self.calculate_trajectory()

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
            Qt.FramelessWindowHint |
            Qt.WindowMaximizeButtonHint  # Allow maximize
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Enable resizing
        self.setMinimumSize(800, 600)  # Set minimum window size
        
        # Create main widget and layout
        main_widget = QWidget()
        main_widget.setStyleSheet("""
            QWidget#mainWidget {
                background-color: rgba(255, 255, 255, 180);
                border: 2px solid rgba(0, 0, 0, 100);
                border-radius: 10px;
            }
            QSplitter::handle {
                background-color: rgba(100, 100, 100, 150);
                margin: 1px;
            }
            QSplitter::handle:hover {
                background-color: rgba(100, 100, 100, 200);
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
            QPushButton#maximizeBtn:hover {
                background-color: rgba(0, 255, 0, 180);
            }
        """)
        title_bar.setFixedHeight(30)
        
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 0, 0)
        
        # Add title label
        title_label = QLabel('Aimer Tool')
        title_label.setStyleSheet('color: white; font-weight: bold;')
        title_layout.addWidget(title_label)
        
        # Add maximize button
        maximize_button = QPushButton('□')
        maximize_button.setObjectName('maximizeBtn')
        maximize_button.setFixedSize(30, 30)
        maximize_button.clicked.connect(self.toggle_maximize)
        title_layout.addWidget(maximize_button)
        
        # Add close button
        close_button = QPushButton('×')
        close_button.setFixedSize(30, 30)
        close_button.clicked.connect(self.close)
        title_layout.addWidget(close_button)
        
        main_layout.addWidget(title_bar)
        
        # Create splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(4)
        main_layout.addWidget(splitter)
        
        # Left side - Transparent Canvas
        self.canvas = TransparentCanvas()
        splitter.addWidget(self.canvas)
        
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
            QSpinBox, QSlider {
                background-color: rgba(255, 255, 255, 220);
                border: 1px solid gray;
                border-radius: 4px;
                padding: 2px;
            }
        """)
        controls_widget.setMinimumWidth(200)
        controls_widget.setMaximumWidth(400)
        controls_layout = QVBoxLayout(controls_widget)
        splitter.addWidget(controls_widget)
        
        # Gravity control
        gravity_label = QLabel('Gravity (pixels/sec²):')
        self.gravity_spin = QSpinBox()
        self.gravity_spin.setRange(1, 1000)
        self.gravity_spin.setValue(4)
        
        # Initial velocity control
        velocity_label = QLabel('100% Power Velocity (pixels/sec):')
        self.velocity_spin = QSpinBox()
        self.velocity_spin.setRange(1, 1000)
        self.velocity_spin.setValue(98)
        
        # Drawing radius control
        radius_label = QLabel('Drawing Radius (px):')
        self.radius_spin = QSpinBox()
        self.radius_spin.setRange(1, 9999)
        self.radius_spin.setValue(280)
        
        # Wind control
        wind_label = QLabel('Wind Direction and Power:')
        self.wind_slider = QSlider(Qt.Horizontal)
        self.wind_slider.setRange(-10, 10)
        self.wind_slider.setValue(0)
        
        # Wind value label
        self.wind_value_label = QLabel('Wind: 0')
        self.wind_value_label.setAlignment(Qt.AlignCenter)
        self.wind_slider.valueChanged.connect(self.update_wind_label)
        
        # Add all controls to layout
        controls_layout.addWidget(gravity_label)
        controls_layout.addWidget(self.gravity_spin)
        controls_layout.addWidget(velocity_label)
        controls_layout.addWidget(self.velocity_spin)
        controls_layout.addWidget(radius_label)
        controls_layout.addWidget(self.radius_spin)
        controls_layout.addWidget(wind_label)
        controls_layout.addWidget(self.wind_slider)
        controls_layout.addWidget(self.wind_value_label)
        controls_layout.addStretch()
        
        # Set initial sizes for splitter
        splitter.setStretchFactor(0, 1)  # Canvas gets all extra space
        splitter.setStretchFactor(1, 0)  # Controls keep their size
        
        # Store layouts as instance variables
        self.main_layout = main_layout
        
        # Window settings
        self.setWindowTitle('Aimer Tool')
        
        # Maximize window with left space
        screen = QDesktopWidget().availableGeometry()
        self.setGeometry(LEFT_SPACE, screen.y(), screen.width() - LEFT_SPACE, screen.height())
        
        # Connect signals
        self.gravity_spin.valueChanged.connect(self.update_parameters)
        self.velocity_spin.valueChanged.connect(self.update_parameters)
        self.radius_spin.valueChanged.connect(self.update_parameters)
        self.wind_slider.valueChanged.connect(self.update_parameters)
        
        # Initialize canvas parameters
        self.update_parameters()
        
    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
    
    def update_wind_label(self):
        value = self.wind_slider.value()
        direction = "←" if value < 0 else "→" if value > 0 else "-"
        self.wind_value_label.setText(f'Wind: {abs(value)} {direction}')
        
    def update_parameters(self):
        # Update canvas parameters
        self.canvas.set_parameters(
            max_radius=self.radius_spin.value(),
            gravity=self.gravity_spin.value(),
            max_velocity=self.velocity_spin.value()
        )

def main():
    app = QApplication(sys.argv)
    tool = AimerTool()
    tool.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()