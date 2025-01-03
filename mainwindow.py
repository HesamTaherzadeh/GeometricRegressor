from PySide6.QtCore import Qt, QSize, QRect, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QPainter, QPixmap, QPen, QIcon
from PySide6.QtWidgets import (
    QApplication, QSlider, QInputDialog, QMessageBox, QDialog, QProgressDialog, QMainWindow, QPushButton, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox, QScrollArea, QSpacerItem, QSizePolicy
)
from PySide6.QtGui import QImage, QPixmap
from matplotlib.figure import Figure
from ui.widgets.circular import CircleNumberWidget
from ui.magnifier import  MagnifierGraphicsView
from core.polynomial import Polynomial
from core.resampling import Resampling
import numpy as np 
import matplotlib.pyplot as plt


class HoverButton(QPushButton):
    def __init__(self, icon_path, parent=None):
        super().__init__(parent)

        # Set the icon and its initial size
        self.setIcon(QIcon(icon_path))
        self.setIconSize(QSize(50, 50))  # Initial size
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
        """)

        # Create the animation for icon size
        self.animation = QPropertyAnimation(self, b"iconSize")
        self.animation.setEasingCurve(QEasingCurve.OutQuad)

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
        self.animation.setEndValue(QSize(50, 50))  # Original size
        self.animation.setDuration(200)
        self.animation.start()
        super().leaveEvent(event)

        
class ToolBoxMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set window flags to make it movable
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Enable dragging of the window
        self.draggable = False
        self.offset = None
        
        # Create the main widget and set its layout
        main_widget = QWidget(self)
        self.main_layout = QHBoxLayout(main_widget)
        self.setCentralWidget(main_widget)

        # Left layout: Image display area
        image_layout = QVBoxLayout()
        self.image_scene = QGraphicsScene()
        self.image_viewer = MagnifierGraphicsView(self.image_scene)
        self.image_viewer.setScene(self.image_scene)
        self.image_viewer.setStyleSheet("border: 2px solid gray; background-color: transparent;")
        image_layout.addWidget(self.image_viewer)

        self.table_scroll_area = QScrollArea()
        self.table_scroll_area.setFixedHeight(300)
        self.table_scroll_area.setWidgetResizable(True)

        self.table_widget = QTableWidget()
        self.table_widget.setRowCount(0)
        self.table_widget.setColumnCount(7)
        self.table_widget.setHorizontalHeaderLabels(["Idx", "x", "y", "X", "Y", "Z", "ICP"])
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_scroll_area.setWidget(self.table_widget)

        self.table_scroll_area.setVisible(False)
        image_layout.addWidget(self.table_scroll_area)

        self.main_layout.addLayout(image_layout)

        # Right layout: Buttons and controls
        self.right_layout = QVBoxLayout()
        self.open_button = HoverButton("ui/icon/image.png")
        
        self.open_button.clicked.connect(self.open_image)
        self.right_layout.addWidget(self.open_button)

        self.load_gcp_button = HoverButton("ui/icon/icp.png")
        self.load_gcp_button.clicked.connect(self.load_gcp_file)
        self.right_layout.addWidget(self.load_gcp_button)

        self.toggle_table_button = HoverButton("ui/icon/eye.webp")
        self.toggle_table_button.clicked.connect(self.toggle_table_visibility)
        self.toggle_table_button.setVisible(False)
        self.right_layout.addWidget(self.toggle_table_button)
        last_layout = QVBoxLayout()

        self.forward_button = HoverButton("ui/icon/forward.webp")  # "Forward" button
        self.forward_button.clicked.connect(self.perform_regression)
        self.right_layout.addWidget(self.forward_button)
        
        self.resampling_button = HoverButton("ui/icon/resampling.png", self)  # Use your resampling icon
        self.resampling_button.clicked.connect(self.perform_resampling)
        self.right_layout.addWidget(self.resampling_button)

        self.degree_slider = QSlider(Qt.Vertical, self)  # Vertical slider for degree selection
        self.degree_slider.setMinimum(1)
        self.degree_slider.setMaximum(35)
        self.degree_slider.setValue(1)  # Default degree is 1
        self.degree_slider.setInvertedAppearance(True)  # Start from bottom
        self.degree_slider.setStyleSheet("""
            QSlider::groove:vertical {
                background: #3d544d;
                width: 100px;  /* Thickness of the slider */
                border-radius: 8px;
            }
            QSlider::handle:vertical {
                background: #5a5;
                border: 2px solid #3a3;
                height: 30px;  /* Height of the handle */
                margin: -2px;  /* Adjust position to center */
                border-radius: 15px;
            }
        """)
        
        circle_widget = CircleNumberWidget(initial_value=self.degree_slider.value(), parent=self)

        self.degree_slider.valueChanged.connect(circle_widget.set_value)

        # Add the slider to the right layout
        self.main_layout.addWidget(self.degree_slider)
        
        last_layout = QVBoxLayout()
        
        self.close_button = QPushButton("\u25CF", self)
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                border-radius: 15px;
                width: 15px;
                height: 15px;

            }
            QPushButton:hover {
                background-color: transparent;
                color: red;
            }
        """)

        self.main_layout.addWidget(self.degree_slider)
        self.close_button.clicked.connect(self.close)
        last_layout.addWidget(self.close_button)
        
        self.right_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.right_layout.addWidget(circle_widget)
        self.main_layout.addLayout(self.right_layout)
        self.main_layout.addLayout(last_layout)

    def perform_resampling(self):
        """
        Perform resampling using the Polynomial model and display the resampled grid image.
        """
        if not self.image_viewer.pixmap:
            QMessageBox.warning(self, "Warning", "Please load an image before performing resampling.")
            return

        gcp_points = self.get_gcp_points()
        if not gcp_points:
            QMessageBox.warning(self, "Warning", "No GCP points available for resampling.")
            return

        step, ok = QInputDialog.getDouble(
            self, "Input", "Enter satellite GSD (resolution):", 1.0, 0.1, 10.0, 2
        )
        if not ok:
            return

        try:
            # Initialize the resampling process
            polynomial = Polynomial(gcp_points, self.degree_slider.value())
            resampling = Resampling(
                polynomial=polynomial,
                image_path=self.image_viewer.image_path,
                gcp_points=gcp_points,
                icp_points=self.get_icp_points()
            )
            resampling.load_image()

            # Perform resampling
            progress = QProgressDialog("Resampling in progress...", "Cancel", 0, 100, self)
            progress.setWindowModality(Qt.WindowModal)
            grd_image = resampling.resample(step=step)

            # Save or display results
            np.save("resampled_grid.npy", grd_image)
            QMessageBox.information(self, "Success", "Resampling completed. Output saved as 'resampled_grid.npy'.")

            # Display the resampled grid in a new window
            self.show_resampled_grid(grd_image)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")

    def show_resampled_grid(self, grd_image):
        """
        Display the resampled grid image in a new dialog window.

        Parameters:
        grd_image (np.ndarray): The resampled grid image array.
        """
        # Normalize the resampled grid for visualization
        normalized_image = (grd_image - np.min(grd_image)) / (np.max(grd_image) - np.min(grd_image)) * 255
        normalized_image = normalized_image.astype(np.uint8)

        # Convert to QPixmap
        height, width = normalized_image.shape
        qimage = QImage(normalized_image, width, height, QImage.Format_Grayscale8)
        pixmap = QPixmap.fromImage(qimage)

        # Create a dialog for the resampled grid
        dialog = QDialog(self)
        dialog.setWindowTitle("Resampled Grid Image")
        dialog.setMinimumSize(800, 600)

        # Create a QLabel to display the resampled grid
        label = QLabel(dialog)
        label.setPixmap(pixmap)
        label.setAlignment(Qt.AlignCenter)

        # Set up the dialog layout
        layout = QVBoxLayout()
        layout.addWidget(label)
        dialog.setLayout(layout)

        # Show the dialog
        dialog.exec()
    
    def sizeHint(self):
        return QSize(1800, 1600)

    def paintEvent(self, event):
        """
        Handles the paint event of the widget.
        Draws a rounded rectangle background for the widget.

        Args:
            event (QPaintEvent): The paint event object.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rounded_rect = QRect(0, 0, self.width(), self.height())
        rounded_corner_radius = 20.0

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(47, 48, 54, 200))

        painter.drawRoundedRect(rounded_rect, rounded_corner_radius, rounded_corner_radius)

    def open_image(self):
        """
        Opens a file dialog to select an image and displays it in the image viewer.
        """
        image_path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Images (*.png *.xpm *.jpg *.jpeg *.bmp)")
        if image_path:
            pixmap = QPixmap(image_path)
            self.image_scene.clear()
            pixmap_item = QGraphicsPixmapItem(pixmap)
            self.image_scene.addItem(pixmap_item)
            self.image_viewer.setScene(self.image_scene)
            self.image_viewer.set_image(pixmap)
            self.image_viewer.fitInView(self.image_scene.sceneRect(), Qt.KeepAspectRatio)



    def load_gcp_file(self):
        """
        Opens a file dialog to select a GCP file and loads its content into the table.
        Draws the points from the GCP file onto the image using scaled icons.
        """
        if not self.image_scene.items():  # No items in the scene, meaning no image loaded
            QMessageBox.warning(self, "Warning", "Please import a photo before loading GCP points.")
            return
        file_path, _ = QFileDialog.getOpenFileName(self, "Open GCP File", "", "Text Files (*.txt)")
        if file_path:
            with open(file_path, "r") as file:
                lines = file.readlines()
                self.table_widget.setRowCount(len(lines))
                for row, line in enumerate(lines):
                    values = line.strip().split()
                    for col, value in enumerate(values):
                        self.table_widget.setItem(row, col, QTableWidgetItem(value))
                    
                    # Add ICP checkbox in the last column
                    checkbox = QCheckBox()
                    checkbox.setStyleSheet("margin-left: 50%; margin-right: 50%;")
                    self.table_widget.setCellWidget(row, 6, checkbox)

                    # Draw scaled icons on the image
                    if len(values) >= 3:  # Ensure there are at least x, y coordinates
                        x, y = int(float(values[1])), int(float(values[2]))
                        idx = values[0]

                        # Load, scale, and place the icon
                        icon_path = "ui/icon/pin.webp"  # Replace with the path to your icon
                        icon_pixmap = QPixmap(icon_path)
                        scaled_pixmap = icon_pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)  # Resize to 20x20
                        icon_item = self.image_scene.addPixmap(scaled_pixmap)
                        icon_item.setOffset(x - scaled_pixmap.width() // 2, y - scaled_pixmap.height() // 2)

                        # Add a label near the icon
                        label = QLabel(idx)
                        label.setStyleSheet("color: red; font-size: 10px;")
                        label.setAttribute(Qt.WA_TranslucentBackground)
                        proxy_label = self.image_scene.addWidget(label)
                        proxy_label.setPos(x + 5, y - 5)

            self.table_scroll_area.setVisible(True)
            self.toggle_table_button.setVisible(True)

    def get_gcp_points(self):
        """
        Extract GCP points from the table (unchecked rows).
        Returns a list of dictionaries with 'x', 'y', 'X', 'Y', and 'Z' for each GCP.
        """
        gcp_points = []
        for row in range(self.table_widget.rowCount()):
            checkbox = self.table_widget.cellWidget(row, 6)
            if checkbox and not checkbox.isChecked():  # Unchecked rows
                point = {
                    "x": float(self.table_widget.item(row, 1).text()),
                    "y": float(self.table_widget.item(row, 2).text()),
                    "X": float(self.table_widget.item(row, 3).text()),
                    "Y": float(self.table_widget.item(row, 4).text()),
                    "Z": float(self.table_widget.item(row, 5).text()),
                }
                gcp_points.append(point)
        return gcp_points

    def get_icp_points(self):
        """
        Extract ICP points from the table (checked rows).
        Returns a list of dictionaries with 'x', 'y', 'X', 'Y'.
        """
        icp_points = []
        for row in range(self.table_widget.rowCount()):
            checkbox = self.table_widget.cellWidget(row, 6)
            if checkbox and checkbox.isChecked(): 
                point = {
                    "x": float(self.table_widget.item(row, 1).text()),
                    "y": float(self.table_widget.item(row, 2).text()),
                    "X": float(self.table_widget.item(row, 3).text()),
                    "Y": float(self.table_widget.item(row, 4).text()),
                }
                icp_points.append(point)
        return icp_points


    def perform_regression(self):
        """
        Evaluate the polynomial regression on ICP points, calculate RMSE,
        and display a quiver plot in a new window added to the left of the main window.
        """
        icp_points = self.get_icp_points()  # Extract ICP points
        if not icp_points:
            QMessageBox.warning(self, "Warning", "No ICP points available.")
            return

        degree = self.degree_slider.value()
        gcp_points = self.get_gcp_points()
        if not gcp_points:
            QMessageBox.warning(self, "Warning", "No GCP points for regression.")
            return

        polynomial = Polynomial(gcp_points, degree)
        coeffs_X, coeffs_Y = polynomial.regress_polynomial()

        # Evaluate polynomial on ICP points
        predicted_X, predicted_Y = polynomial.evaluate(coeffs_X, coeffs_Y, icp_points)

        # Calculate RMSE
        actual_X = np.array([point['X'] for point in icp_points])
        actual_Y = np.array([point['Y'] for point in icp_points])
        rmse_X, rmse_Y = polynomial.rmse(predicted_X, predicted_Y, actual_X, actual_Y)

        # Display RMSE in a QMessageBox
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Evaluation Results")
        msg_box.setText(
            f"<b>Evaluation Summary:</b><br><br>"
            f"<b>Number of GCPs:</b> {len(gcp_points)}<br>"
            f"<b>Number of ICPs:</b> {len(icp_points)}<br>"
            f"<b>RMSE (X):</b> {rmse_X:.4f}<br>"
            f"<b>RMSE (Y):</b> {rmse_Y:.4f}"
        )
        msg_box.exec()

        self.show_quiver_plot(icp_points, predicted_X, predicted_Y, actual_X, actual_Y)

    def show_quiver_plot(self, icp_points, predicted_X, predicted_Y, actual_X, actual_Y):
        """
        Show the quiver plot in a new window added to the left of the main window with the image as the background.

        Parameters:
        icp_points (list): List of ICP points with 'x' and 'y'.
        predicted_X, predicted_Y (np.array): Predicted values for X and Y.
        actual_X, actual_Y (np.array): Actual values for X and Y.
        """
        if not hasattr(self, 'image_viewer') or self.image_viewer.pixmap is None:
            QMessageBox.warning(self, "Warning", "No image loaded to display as background.")
            return

        # Convert the loaded QPixmap to a NumPy array for plotting
        image = self.image_viewer.pixmap.toImage()
        image_array = np.array(image.bits()).reshape(image.height(), image.width(), 4)[..., :3]

        # Generate the quiver plot using matplotlib
        fig, ax = plt.subplots(figsize=(10, 8))  # Increased figure size
        fig.patch.set_facecolor('black')  # Set the background color of the plot area

        # Display the image as the background
        ax.imshow(image_array, extent=[0, image.width(), 0, image.height()], origin='upper')

        # Extract ICP points and calculate quiver vectors
        x = [point['x'] for point in icp_points]
        y = [point['y'] for point in icp_points]
        u = predicted_X - actual_X
        v = predicted_Y - actual_Y

        # Overlay the quiver plot
        ax.quiver(x, y, u, v, angles='xy', scale_units='xy', scale=1, color='red')

        # Customize plot appearance
        ax.set_title("Quiver Plot with Image Background", color='white')
        ax.set_xlabel("X", color='white')
        ax.set_ylabel("Y", color='white')
        ax.tick_params(axis='both', colors='white')

        # Save the plot to a temporary buffer
        fig.canvas.draw()
        width, height = fig.canvas.get_width_height()
        plot_data = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8).reshape(height, width, 3)

        # Close the matplotlib figure
        plt.close(fig)

        # Convert the plot to a QPixmap
        plot_image = QImage(plot_data, width, height, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(plot_image)

        # Create a new dialog for the plot
        dialog = QDialog(self)
        dialog.setWindowTitle("Quiver Plot")
        dialog.setMinimumSize(800, 600)  # Increased dialog size

        # Create a QLabel to display the pixmap
        label = QLabel(dialog)
        label.setPixmap(pixmap)
        label.setAlignment(Qt.AlignCenter)

        # Set up the dialog layout
        layout = QVBoxLayout()
        layout.addWidget(label)
        dialog.setLayout(layout)

        # Show the dialog
        dialog.exec()
    
    def toggle_table_visibility(self):
        """
        Toggles the visibility of the table and its scroll area.
        """
        is_visible = self.table_scroll_area.isVisible()
        self.table_scroll_area.setVisible(not is_visible)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.draggable = True
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.draggable:
            self.move(event.globalPos() - self.offset)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.draggable = False
            self.offset = None

if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    window = ToolBoxMainWindow()
    window.show()
    sys.exit(app.exec())
