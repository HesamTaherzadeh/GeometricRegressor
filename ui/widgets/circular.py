from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QPainter, QColor


class CircleNumberWidget(QWidget):
    def __init__(self, initial_value=1, parent=None):
        super().__init__(parent)

        # Initial value for the number
        self.value = initial_value

        # Set fixed size for the circular widget
        self.setFixedSize(80, 80)

        # Label to display the number
        self.number_label = QLabel(str(self.value), self)
        self.number_label.setAlignment(Qt.AlignCenter)
        self.number_label.setFont(QFont("Arial", 24, QFont.Bold))  # Set modern font
        self.number_label.setStyleSheet("""
            QLabel {
                color: white;
            }
        """)

        # Layout to center the label
        layout = QVBoxLayout(self)
        layout.addWidget(self.number_label)
        layout.setContentsMargins(0, 0, 0, 0)

    def set_value(self, value):
        """Update the displayed number."""
        self.value = value
        self.number_label.setText(str(self.value))
        self.update()

    def paintEvent(self, event):
        """Draw the circular background."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw circle
        rect = self.rect()
        painter.setBrush(QColor("#3d544d"))  # Background color
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(rect)