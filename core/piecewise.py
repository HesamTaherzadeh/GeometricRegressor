import numpy as np

from PySide6.QtWidgets import (
    QDialog, QGraphicsScene, QGraphicsPixmapItem,
    QVBoxLayout, QLabel, QScrollArea, QMessageBox
)
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPixmap, QPen, QImage, QPainter

from core.polynomial import Polynomial

class GraphicsSceneMouseLabel(QLabel):
    """
    A QLabel that holds a QGraphicsScene rendered as a QPixmap,
    capturing mouse clicks in scene coordinates.
    """
    def __init__(self, scene, parent=None):
        super().__init__(parent)
        self.scene = scene
        self.left_click_callback = None

        # Convert scene to QPixmap. We'll do a quick approach: get boundingRect, 
        # then create a QPixmap of that size, render the scene, set as our pixmap.
        rect = self.scene.itemsBoundingRect()
        w = int(rect.width())
        h = int(rect.height())

        pixmap = QPixmap(w, h)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        self.scene.render(painter, target=rect, source=rect)
        painter.end()

        self.setPixmap(pixmap)
        self.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.setMouseTracking(True)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Convert local coords -> scene coords
            x = event.position().x()
            y = event.position().y()
            scene_pos = QPointF(x, y)
            if self.left_click_callback:
                self.left_click_callback(scene_pos)
        super().mousePressEvent(event)



class SplitLineWindow(QDialog):
    """
    A dialog window that:
      1) Displays an image in a QGraphicsScene.
      2) Lets the user pick two points on the image by left-clicking.
      3) Draws a line between those two points.
      4) Splits GCP/ICP points by which side of the line they fall on.
      5) Performs polynomial regression separately for each side (part).
      6) Computes RMSE for each part using the ICPs in that part.
    """

    def __init__(self, qpixmap, gcp_points, icp_points, scene, degree=1, parent=None):
        """
        :param qpixmap:    QPixmap of the image to display.
        :param gcp_points: List of GCP dicts, e.g. [{"x": .., "y": .., "X": .., "Y": .., "Z": ..}, ...].
        :param icp_points: List of ICP dicts, e.g. [{"x": .., "y": .., "X": .., "Y": ..}, ...].
        :param degree:     Polynomial degree to use for regression.
        :param parent:     Optional parent QWidget.
        """
        super().__init__(parent)
        self.setWindowTitle("Split Line Regression")
        self.setModal(True)  # Make this dialog modal

        self.gcp_points = gcp_points
        self.icp_points = icp_points
        self.degree = degree

        # For storing the two clicked points (defining the line)
        self.line_points = []  # Will hold [(x1, y1), (x2, y2)]

        # Create the scene and add the pixmap
        self.scene = scene
        # self.pixmap_item = QGraphicsPixmapItem(qpixmap)
        # self.scene.addItem(self.pixmap_item)

        # # We need the image dimensions
        # self.img_width = qpixmap.width()
        # self.img_height = qpixmap.height()

        # # Set up a scrollable view
        # self.scroll_area = QScrollArea(self)
        # self.scroll_area.setWidgetResizable(True)

        # Create a label that wraps our scene in a single widget
        # We'll capture mouse events by subclassing the label or by using an EventFilter.
        self.image_label = GraphicsSceneMouseLabel(self.scene, self)
        self.image_label.left_click_callback = self.handle_left_click

        # Put the label inside the scroll area
        # self.scroll_area.setWidget(self.image_label)

        # Layout
        layout = QVBoxLayout(self)
        # layout.addWidget(self.scroll_area)
        self.setLayout(layout)

    def handle_left_click(self, scene_pos):
        """
        Called whenever the user left-clicks on the image.
        scene_pos is a QPointF in scene coordinates.
        """
        x, y = scene_pos.x(), scene_pos.y()
        print(f"Clicked at: {x}, {y}")

        # Store the line points
        if len(self.line_points) < 2:
            self.line_points.append((x, y))

            # If we have 2 points, draw the line and do the regression
            if len(self.line_points) == 2:
                self.draw_split_line()
                self.perform_split_regressions()
        else:
            QMessageBox.information(self, "Info", "You already picked two points!")

    def draw_split_line(self):
        """
        Draw a line on the scene between the two user-selected points.
        """
        (x1, y1), (x2, y2) = self.line_points
        pen = QPen(Qt.red, 2)  # Red line, thickness 2
        self.scene.addLine(x1, y1, x2, y2, pen)

    def perform_split_regressions(self):
        """
        Split GCPs/ICPs based on which side of the line they lie.
        Then do polynomial regression for each side, compute RMSE,
        and display in a message box.
        """
        # Unpack the line endpoints
        (x1, y1), (x2, y2) = self.line_points

        # Separate GCPs into side A or side B of the line
        gcp_side_a = []
        gcp_side_b = []

        for gcp in self.gcp_points:
            sign = self._side_of_line(gcp["x"], gcp["y"], x1, y1, x2, y2)
            if sign >= 0:
                gcp_side_a.append(gcp)
            else:
                gcp_side_b.append(gcp)

        # Separate ICPs into side A or side B
        icp_side_a = []
        icp_side_b = []
        for icp in self.icp_points:
            sign = self._side_of_line(icp["x"], icp["y"], x1, y1, x2, y2)
            if sign >= 0:
                icp_side_a.append(icp)
            else:
                icp_side_b.append(icp)

        # Perform regression on side A
        rmse_forward_a, rmse_backward_a = None, None
        if gcp_side_a and icp_side_a:
            poly_a = Polynomial(gcp_side_a, self.degree)
            # Regress polynomials
            fxA, fyA, bxA, byA = poly_a.regress_polynomial()

            # Evaluate forward polynomial on side A's ICP
            px_fwd, py_fwd = poly_a.evaluate((fxA, fyA), icp_side_a, forward=True)
            # Evaluate backward polynomial on side A's ICP
            px_bwd, py_bwd = poly_a.evaluate((bxA, byA), icp_side_a, forward=False)

            # Compute RMSE
            actual_x = np.array([p["x"] for p in icp_side_a])
            actual_y = np.array([p["y"] for p in icp_side_a])
            rmseX_fwd, rmseY_fwd = poly_a.rmse(px_fwd, py_fwd, actual_x, actual_y)

            actual_X = np.array([p["X"] for p in icp_side_a])
            actual_Y = np.array([p["Y"] for p in icp_side_a])
            rmseX_bwd, rmseY_bwd = poly_a.rmse(px_bwd, py_bwd, actual_X, actual_Y)

            rmse_forward_a = (rmseX_fwd, rmseY_fwd)
            rmse_backward_a = (rmseX_bwd, rmseY_bwd)

        # Perform regression on side B
        rmse_forward_b, rmse_backward_b = None, None
        if gcp_side_b and icp_side_b:
            poly_b = Polynomial(gcp_side_b, self.degree)
            fxB, fyB, bxB, byB = poly_b.regress_polynomial()

            # Evaluate forward polynomial on side B's ICP
            px_fwd, py_fwd = poly_b.evaluate((fxB, fyB), icp_side_b, forward=True)
            # Evaluate backward polynomial on side B's ICP
            px_bwd, py_bwd = poly_b.evaluate((bxB, byB), icp_side_b, forward=False)

            # Compute RMSE
            actual_x = np.array([p["x"] for p in icp_side_b])
            actual_y = np.array([p["y"] for p in icp_side_b])
            rmseX_fwd, rmseY_fwd = poly_b.rmse(px_fwd, py_fwd, actual_x, actual_y)

            actual_X = np.array([p["X"] for p in icp_side_b])
            actual_Y = np.array([p["Y"] for p in icp_side_b])
            rmseX_bwd, rmseY_bwd = poly_b.rmse(px_bwd, py_bwd, actual_X, actual_Y)

            rmse_forward_b = (rmseX_fwd, rmseY_fwd)
            rmse_backward_b = (rmseX_bwd, rmseY_bwd)

        # Display results
        text_lines = []
        text_lines.append("<b>Split Line Regression Results</b><br>")

        if rmse_forward_a is not None:
            fx, fy = rmse_forward_a
            bx, by = rmse_backward_a
            text_lines.append(f"<b>Side A:</b> (GCPs: {len(gcp_side_a)}, ICPs: {len(icp_side_a)})<br>")
            text_lines.append(f"Forward RMSE: X={fx:.4f}, Y={fy:.4f}<br>")
            text_lines.append(f"Backward RMSE: X={bx:.4f}, Y={by:.4f}<br><br>")
        else:
            text_lines.append(f"<b>Side A:</b> Not enough GCP/ICP to perform regression.<br><br>")

        if rmse_forward_b is not None:
            fx, fy = rmse_forward_b
            bx, by = rmse_backward_b
            text_lines.append(f"<b>Side B:</b> (GCPs: {len(gcp_side_b)}, ICPs: {len(icp_side_b)})<br>")
            text_lines.append(f"Forward RMSE: X={fx:.4f}, Y={fy:.4f}<br>")
            text_lines.append(f"Backward RMSE: X={bx:.4f}, Y={by:.4f}<br><br>")
        else:
            text_lines.append(f"<b>Side B:</b> Not enough GCP/ICP to perform regression.<br><br>")

        QMessageBox.information(self, "Split Regression RMSE", "".join(text_lines))

    def _side_of_line(self, px, py, x1, y1, x2, y2):
        """
        Returns the signed area (cross product) to indicate which side
        of the line (x1,y1)->(x2,y2) the point (px,py) is on.
        Positive => 'left side', negative => 'right side'.
        """
        return (px - x1) * (y2 - y1) - (py - y1) * (x2 - x1)

