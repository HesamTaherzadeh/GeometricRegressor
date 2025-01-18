from PySide6.QtWidgets import QGraphicsView, QWidget, QGraphicsLineItem
from PySide6.QtCore import Qt, QPoint, QRect, QTimer, QPointF
from PySide6.QtGui import QPainter, QPixmap, QBrush, QColor, QPainterPath, QPen

class CircularMagnifier(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(150, 150)  # Size of the circular magnifier
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.pixmap = None
        self.scene_point = QPointF()
        self.zoom_factor = 2

    def set_pixmap_and_position(self, pixmap, scene_point):
        """
        Updates the magnifier with a new pixmap and scene point.
        """
        self.pixmap = pixmap
        self.scene_point = scene_point
        self.update()

    def paintEvent(self, event):
        if not self.pixmap:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw circular background
        size = self.size()
        radius = size.width() // 2
        painter.setBrush(QBrush(Qt.white))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, size.width(), size.height())

        # Create a circular clipping path
        clip_path = QPainterPath()
        clip_path.addEllipse(0, 0, size.width(), size.height())
        painter.setClipPath(clip_path)

        # Draw zoomed-in image
        source_rect = QRect(
            int(self.scene_point.x() - radius / self.zoom_factor),
            int(self.scene_point.y() - radius / self.zoom_factor),
            int(radius / self.zoom_factor * 4),
            int(radius / self.zoom_factor * 4),
        )
        target_rect = QRect(0, 0, size.width(), size.height())
        painter.drawPixmap(target_rect, self.pixmap, source_rect)

        # Ensure the painter is properly ended
        painter.end()


class MagnifierGraphicsView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setScene(scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)
        self.main = parent
        self.pixmap = None
        self.magnifier = CircularMagnifier(self)
        self.magnifier.hide()
        self.parent = parent
        self.is_magnifier_active = False

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)

    def set_pixmap(self, pixmap):
        """
        Set the pixmap for the view, typically an image displayed in the scene.
        """
        self.pixmap = pixmap
            
    def mousePressEvent(self, event):
        super().mousePressEvent(event)

        if event.button() == Qt.RightButton and self.pixmap:
            self.is_magnifier_active = True
            self.update_magnifier(event.pos())
                            
        if self.parent.split_line_mode and event.button() == Qt.LeftButton:
            scene_pos = self.parent.image_viewer.mapToScene(event.pos())
            self.parent.line_points.append((scene_pos.x(), scene_pos.y()))

            if len(self.parent.line_points) == 1:
                self.parent.image_scene.addEllipse(scene_pos.x() - 3, scene_pos.y() - 3, 6, 6, QPen(Qt.red), Qt.red)
            elif len(self.parent.line_points) == 2:
                x1, y1 = map(int, self.parent.line_points[0])
                x2, y2 = map(int, self.parent.line_points[1])
                pen = QPen(Qt.blue)
                pen.setWidth(100)
                self.parent.image_scene.addLine(x1, y1, x2, y2, pen)
                self.parent.image_scene.update()  

                self.parent.perform_split_line_regression(x1, y1, x2, y2)
                self.parent.split_line_mode = False
                self.parent.line_points.clear()
        else:
            super().mousePressEvent(event)
    
    def keyPressEvent(self, event):
        """
        Handles key press events to remove lines when 'C' is pressed.
        """
        if event.key() == Qt.Key_C:
            # Clear all line items from the scene
            for item in self.parent.image_scene.items():
                if isinstance(item, QGraphicsLineItem):  # Check if the item is a line
                    self.parent.image_scene.removeItem(item)
            self.parent.image_scene.update()  # Refresh the scene
        else:
            super().keyPressEvent(event)



    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        if self.is_magnifier_active and self.pixmap:
            self.update_magnifier(event.pos())

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if event.button() == Qt.RightButton:
            self.is_magnifier_active = False
            self.magnifier.hide()

    def update_magnifier(self, cursor_pos):
        """
        Updates the magnifier's position and content based on the cursor position.
        """
        scene_pos = self.mapToScene(cursor_pos)

        # Position the magnifier slightly to the right and below the cursor
        offset = QPoint(20, 20)
        magnifier_pos = cursor_pos + offset - QPoint(self.magnifier.width() // 2, self.magnifier.height() // 2)

        # Update the magnifier's content and position
        self.magnifier.set_pixmap_and_position(self.pixmap, scene_pos)
        self.magnifier.move(magnifier_pos)
        self.magnifier.show()
