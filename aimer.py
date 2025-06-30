import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QSlider, QSpinBox, QDoubleSpinBox,
                             QPushButton, QSplitter, QDesktopWidget)
from PyQt5.QtCore import Qt, QPoint, QPointF
from PyQt5.QtGui import QPainter, QPen, QColor
import math

LEFT_SPACE = 0

class TransparentCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        self.setMinimumSize(400, 400)  # Set reasonable minimum size
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
        self.ticks_per_second = 30  # Will be set from main window
        self.wind_power = 0    # Will be set from main window (-10 to 10)
        self.wind_accel = 5    # Will be set from main window (pixels/sec^2)
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
        dt = 0.02  # 更小的时间步长以获得更平滑的轨迹
        x0 = self.center_point.x()
        y0 = self.center_point.y()
        
        # 计算轨迹点
        t = 0
        while True:
            # 计算风力效果
            wind_ax = self.wind_power * self.wind_accel
            
            # 计算位置
            x = x0 + v0x * t + 0.5 * wind_ax * t * t
            y = y0 - (v0y * t - 0.5 * self.gravity * t * t)  # Y轴反转
            
            # 计算垂直速度
            vy = v0y - self.gravity * t
            going_down = vy < 0
            
            # 获取画布大小
            canvas_height = self.height() if self.height() > 0 else 1000
            canvas_width = self.width() if self.width() > 0 else 1000
            
            # 检查水平边界
            if x < 0 or x > canvas_width:
                break
                
            # 添加轨迹点
            point = QPointF(x, y)
            points.append(point)
            
            t += dt
            
            # 检查是否超出底部边界
            if going_down and y > canvas_height:
                break
        
        # 直接计算6个时间点的位置
        for i in range(1, 7):
            t = i * self.ticks_per_second  # 实际物理时间
            x = x0 + v0x * t + 0.5 * wind_ax * t * t
            y = y0 - (v0y * t - 0.5 * self.gravity * t * t)
            time_points.append(QPointF(x, y))
            
            # Check if we should stop - only when going down and below bottom
            if going_down and y > canvas_height:
                break
                
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
            painter.setPen(QPen(QColor(255, 0, 0), 4))
            for i, point in enumerate(self.time_points[:6]):  # 只绘制前6个时间点
                # Draw larger point
                painter.drawPoint(point)
                
                # Draw time label with actual game time
                painter.drawText(
                    int(point.x()) + 10,
                    int(point.y()) - 10,
                    f"{i+1}s"
                )
    
    def set_parameters(self, max_radius, gravity, max_velocity, ticks_per_second, wind_power, wind_accel):
        self.max_radius = max_radius
        self.gravity = gravity
        self.max_velocity = max_velocity
        self.ticks_per_second = ticks_per_second
        self.wind_power = wind_power
        self.wind_accel = wind_accel
        if self.center_point and self.current_point:
            self.calculate_trajectory()

class AimerTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.oldPos = None
        self.resize_edge = None
        self.resize_start_pos = None
        self.resize_start_geometry = None
        self.resize_edge_width = 8
        self.initUI()
        
    def initUI(self):
        # Set window flags for resizable frameless window
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Enable resizing
        self.setMouseTracking(True)
        
        # Create main widget and layout
        main_widget = QWidget()
        main_widget.setStyleSheet("""
            QWidget#mainWidget {
                background-color: rgba(255, 255, 255, 180);
                border: 2px solid rgba(0, 0, 0, 100);
                border-radius: 10px;
            }
            QMainWindow {
                border: 1px solid rgba(100, 100, 100, 150);
            }
            QMainWindow:hover {
                border: 2px solid rgba(60, 60, 60, 180);
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
        title_layout.setContentsMargins(10, 0, 10, 0)
        
        # Add title label
        title_label = QLabel('Aimer Tool')
        title_label.setStyleSheet('color: white; font-weight: bold;')
        title_layout.addWidget(title_label)
        
        main_layout.addWidget(title_bar)
        
        # Create splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(4)
        main_layout.addWidget(splitter)
        
        # Left side - Controls
        controls_widget = QWidget()
        self.controls_widget = controls_widget  # Store reference for later use
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
        # Set fixed width for controls
        controls_widget.setFixedWidth(250)
        controls_layout = QVBoxLayout(controls_widget)
        splitter.addWidget(controls_widget)
        
        # Right side - Transparent Canvas
        self.canvas = TransparentCanvas()
        splitter.addWidget(self.canvas)
        
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
        
        # Wind acceleration control
        wind_accel_label = QLabel('Wind Acceleration (pixels/sec²):')
        self.wind_accel_spin = QDoubleSpinBox()
        self.wind_accel_spin.setRange(0, 100)
        self.wind_accel_spin.setValue(5)
        self.wind_accel_spin.setDecimals(1)
        self.wind_accel_spin.setSingleStep(0.5)
        
        # Wind value label
        self.wind_value_label = QLabel('Wind: 0')
        self.wind_value_label.setAlignment(Qt.AlignCenter)
        self.wind_slider.valueChanged.connect(self.update_wind_label)
        
        # Time scale control
        tick_label = QLabel('引线1秒=逻辑秒数:')
        self.tick_spin = QDoubleSpinBox()
        self.tick_spin.setRange(0.1, 100)
        self.tick_spin.setValue(7.0)
        self.tick_spin.setDecimals(2)
        self.tick_spin.setSingleStep(0.01)
        
        # Add all controls to layout
        controls_layout.addWidget(gravity_label)
        controls_layout.addWidget(self.gravity_spin)
        controls_layout.addWidget(velocity_label)
        controls_layout.addWidget(self.velocity_spin)
        controls_layout.addWidget(radius_label)
        controls_layout.addWidget(self.radius_spin)
        controls_layout.addWidget(tick_label)
        controls_layout.addWidget(self.tick_spin)
        controls_layout.addWidget(wind_label)
        controls_layout.addWidget(self.wind_slider)
        controls_layout.addWidget(wind_accel_label)
        controls_layout.addWidget(self.wind_accel_spin)
        controls_layout.addWidget(self.wind_value_label)
        controls_layout.addStretch()
        
        # Add toggle canvas button
        toggle_canvas_button = QPushButton('收起 Canvas')
        toggle_canvas_button.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
            QPushButton:pressed {
                background-color: #2a5f9e;
            }
        """)
        toggle_canvas_button.clicked.connect(self.toggle_canvas)
        controls_layout.addWidget(toggle_canvas_button)
        self.toggle_canvas_button = toggle_canvas_button
        
        # Add exit button
        exit_button = QPushButton('退出')
        exit_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
                margin-top: 4px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        exit_button.clicked.connect(self.close)
        controls_layout.addWidget(exit_button)
        
        # Set initial sizes for splitter
        splitter.setStretchFactor(0, 0)  # Controls keep their size
        splitter.setStretchFactor(1, 1)  # Canvas gets all extra space
        
        # Set window size based on desired canvas size
        canvas_width = 3240
        canvas_height = 1800
        window_width = controls_widget.width() + canvas_width
        window_height = canvas_height
        
        # Set minimum sizes
        self.setMinimumWidth(controls_widget.width())  # Controls width plus minimum canvas width
        self.setMinimumHeight(window_height)
        
        # Store layouts as instance variables
        self.main_layout = main_layout
        
        # Window settings
        self.setWindowTitle('Aimer Tool')
        
        # Center window on screen
        screen = QDesktopWidget().availableGeometry()
        x = (screen.width() - window_width) // 2
        y = (screen.height() - window_height) // 2
        self.setGeometry(x, y, window_width, window_height)
        
        # Connect signals
        self.gravity_spin.valueChanged.connect(self.update_parameters)
        self.velocity_spin.valueChanged.connect(self.update_parameters)
        self.radius_spin.valueChanged.connect(self.update_parameters)
        self.wind_slider.valueChanged.connect(self.update_parameters)
        self.tick_spin.valueChanged.connect(self.update_parameters)
        self.wind_accel_spin.valueChanged.connect(self.update_parameters)
        
        # Initialize canvas parameters
        self.update_parameters()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # 检查是否点击在控制区域
            if self.controls_widget.geometry().contains(event.pos()):
                self.oldPos = event.globalPos()
            else:
                # 如果不在控制区域，检查是否是调整大小
                edge = self.check_resize_edge(event.pos())
                if edge:
                    self.resize_start_pos = event.globalPos()
                    self.resize_edge = edge
                    self.resize_start_geometry = self.geometry()
                    
    def mouseMoveEvent(self, event):
        if self.resize_start_pos is not None and self.canvas.isVisible():
            # 处理窗口调整大小
            delta = event.globalPos() - self.resize_start_pos
            new_geometry = self.resize_start_geometry
            min_width = self.minimumWidth()
            min_height = self.minimumHeight()
            
            if self.resize_edge & Qt.RightEdge:
                new_width = max(min_width, self.resize_start_geometry.width() + delta.x())
                new_geometry.setWidth(new_width)
            if self.resize_edge & Qt.BottomEdge:
                new_height = max(min_height, self.resize_start_geometry.height() + delta.y())
                new_geometry.setHeight(new_height)
            
            self.setGeometry(new_geometry)
        
        elif self.oldPos:
            # 处理窗口拖动
            delta = event.globalPos() - self.oldPos
            self.move(self.pos() + delta)
            self.oldPos = event.globalPos()
        
        else:
            # 更新鼠标光标形状
            if not self.canvas.isVisible():
                self.setCursor(Qt.ArrowCursor)
            else:
                edge = self.check_resize_edge(event.pos())
                if edge == Qt.RightEdge:
                    self.setCursor(Qt.SizeHorCursor)
                elif edge == Qt.BottomEdge:
                    self.setCursor(Qt.SizeVerCursor)
                elif edge == (Qt.RightEdge | Qt.BottomEdge):
                    self.setCursor(Qt.SizeFDiagCursor)
                else:
                    self.setCursor(Qt.ArrowCursor)
            
    def mouseReleaseEvent(self, event):
        self.oldPos = None
        self.resize_start_pos = None
        self.resize_edge = None
        self.resize_start_geometry = None
        
    def check_resize_edge(self, pos):
        # 如果canvas已经隐藏，不允许调整大小
        if not self.canvas.isVisible():
            return 0
            
        edge = 0
        # 只允许从右边和底部调整大小
        if pos.x() >= self.width() - self.resize_edge_width:
            edge |= Qt.RightEdge
        if pos.y() >= self.height() - self.resize_edge_width:
            edge |= Qt.BottomEdge
            
        return edge
        
    def toggle_canvas(self):
        current_geometry = self.geometry()
        if self.canvas.isVisible():
            # 保存当前窗口状态
            self.last_window_geometry = self.geometry()
            # 隐藏canvas
            self.canvas.hide()
            self.toggle_canvas_button.setText('展开 Canvas')
            
            # 获取控件栏的实际大小
            controls_size = self.controls_widget.sizeHint()
            # 调整窗口宽度为控件栏宽度，保持高度不变
            new_width = controls_size.width()  # 边框的额外空间
            
            # 保持当前位置不变，只改变宽度
            print(current_geometry.x(), current_geometry.y(), new_width, current_geometry.height())
            # 设置固定大小，禁止调整
            self.setFixedSize(new_width, current_geometry.height())
        else:
            # 显示canvas
            self.canvas.show()
            self.toggle_canvas_button.setText('收起 Canvas')
            # 恢复之前的窗口状态，但保持当前位置
            if hasattr(self, 'last_window_geometry'):
                print(current_geometry.x(), current_geometry.y(), self.last_window_geometry.width(), self.last_window_geometry.height())
                # 允许调整窗口大小
                self.setMinimumSize(0, 0)
                self.setMaximumSize(16777215, 16777215)  # QWIDGETSIZE_MAX
                self.resize(self.last_window_geometry.width(),
                          self.last_window_geometry.height())
            else:
                # 如果没有保存的状态，使用默认大小但保持当前位置
                default_width = self.controls_widget.width() + 2560
                default_height = 1440
                print(current_geometry.x(), current_geometry.y(), default_width, default_height)
                # 允许调整窗口大小
                self.setMinimumSize(0, 0)
                self.setMaximumSize(16777215, 16777215)  # QWIDGETSIZE_MAX
                self.resize(default_width, default_height)
        
    def update_wind_label(self):
        value = self.wind_slider.value()
        direction = "←" if value < 0 else "→" if value > 0 else "-"
        self.wind_value_label.setText(f'Wind: {abs(value)} {direction}')
        
    def update_parameters(self):
        # Update canvas parameters
        self.canvas.set_parameters(
            max_radius=self.radius_spin.value(),
            gravity=self.gravity_spin.value(),
            max_velocity=self.velocity_spin.value(),
            ticks_per_second=self.tick_spin.value(),
            wind_power=self.wind_slider.value(),
            wind_accel=self.wind_accel_spin.value()
        )

def main():
    app = QApplication(sys.argv)
    tool = AimerTool()
    tool.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()