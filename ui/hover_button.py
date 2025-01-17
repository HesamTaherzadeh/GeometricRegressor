from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, Qt

class HoverButton(QPushButton):
    def __init__(self, icon_path, parent=None):
        super().__init__(parent)

        # Convert the icon to a completely white pixmap
        white_icon_pixmap = self.create_white_icon(icon_path)
        self.setIcon(QIcon(white_icon_pixmap))

        # Set the initial icon size
        self.setIconSize(QSize(80, 80))  # Initial size
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
        """)

        # Create the animation for icon size
        self.animation = QPropertyAnimation(self, b"iconSize")
        self.animation.setEasingCurve(QEasingCurve.OutQuad)

    def create_white_icon(self, icon_path):
        """Convert the given icon to a completely white version."""
        original_pixmap = QPixmap(icon_path)
        if original_pixmap.isNull():
            raise ValueError(f"Could not load icon from path: {icon_path}")

        # Create a white pixmap of the same size
        white_pixmap = QPixmap(original_pixmap.size())
        white_pixmap.fill(Qt.transparent)

        # Use QPainter to overlay the white color onto the pixmap
        painter = QPainter(white_pixmap)
        painter.drawPixmap(0, 0, original_pixmap)  # Draw the original pixmap
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(original_pixmap.rect(), QColor("white"))  # Fill with white color
        painter.end()

        return white_pixmap

    def enterEvent(self, event):
        """Animate enlarging the icon when the mouse hovers over the button."""
        self.animation.stop()
        self.animation.setStartValue(self.iconSize())
        self.animation.setEndValue(QSize(120, 120))  # Enlarged size
        self.animation.setDuration(200)  # Duration in milliseconds
        self.animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Animate shrinking the icon back to its original size."""
        self.animation.stop()
        self.animation.setStartValue(self.iconSize())
        self.animation.setEndValue(QSize(80, 80))  # Original size
        self.animation.setDuration(200)
        self.animation.start()
        super().leaveEvent(event)
