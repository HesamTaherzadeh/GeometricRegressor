from PySide6.QtCore import Qt, QRectF, QPoint
from PySide6.QtGui import QPainter, QPixmap, QPen, QColor, QPainterPath
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene

class MagnifierGraphicsView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.image_item = None
        self.pixmap = None
        self.magnifier_active = False
        self.magnifier_pos = QPoint(0, 0)
        self.magnifier_size = 150  # Diameter of the magnifier
        self.magnification_factor = 2.0

    def set_image(self, pixmap):
        """Set the image to display and magnify."""
        self.pixmap = pixmap
        if self.image_item:
            self.scene().removeItem(self.image_item)
        self.image_item = self.scene().addPixmap(self.pixmap)

    def mousePressEvent(self, event):
        """Activate the magnifier on right-click."""
        if event.button() == Qt.RightButton and self.pixmap:
            self.magnifier_active = True
            self.magnifier_pos = event.pos()
            self.viewport().update()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Update the magnifier position on mouse move."""
        if self.magnifier_active:
            self.magnifier_pos = event.pos()
            self.viewport().update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Deactivate the magnifier on releasing the right mouse button."""
        if event.button() == Qt.RightButton:
            self.magnifier_active = False
            self.viewport().update()
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        """Draw the image and apply the magnifier effect."""
        super().paintEvent(event)
        if self.magnifier_active and self.pixmap:
            painter = QPainter(self.viewport())
            painter.setRenderHint(QPainter.Antialiasing)

            # Map the mouse position to scene coordinates
            scene_pos = self.mapToScene(self.magnifier_pos)
            center_x = int(scene_pos.x())
            center_y = int(scene_pos.y())

            # Calculate the zoomed region
            zoomed_rect = QRectF(
                center_x - self.magnifier_size / (2 * self.magnification_factor),
                center_y - self.magnifier_size / (2 * self.magnification_factor),
                self.magnifier_size / self.magnification_factor,
                self.magnifier_size / self.magnification_factor,
            )

            # Ensure zoomed_rect is within pixmap bounds
            if zoomed_rect.left() < 0 or zoomed_rect.top() < 0 or \
               zoomed_rect.right() > self.pixmap.width() or \
               zoomed_rect.bottom() > self.pixmap.height():
                return

            # Extract and scale the zoomed region
            zoomed_pixmap = self.pixmap.copy(zoomed_rect.toRect())
            zoomed_pixmap = zoomed_pixmap.scaled(
                self.magnifier_size, self.magnifier_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )

            # Draw the circular magnifier
            path = QPainterPath()
            path.addEllipse(
                self.magnifier_pos.x() - self.magnifier_size // 2,
                self.magnifier_pos.y() - self.magnifier_size // 2,
                self.magnifier_size,
                self.magnifier_size,
            )
            painter.setClipPath(path)

            # Draw the magnified content
            painter.drawPixmap(
                self.magnifier_pos.x() - self.magnifier_size // 2,
                self.magnifier_pos.y() - self.magnifier_size // 2,
                zoomed_pixmap,
            )

            # Draw the magnifier border
            painter.setClipping(False)
            pen = QPen(QColor(0, 0, 0, 255), 3)
            painter.setPen(pen)
            painter.drawEllipse(
                self.magnifier_pos.x() - self.magnifier_size // 2,
                self.magnifier_pos.y() - self.magnifier_size // 2,
                self.magnifier_size,
                self.magnifier_size,
            )

            painter.end()
