from PySide6.QtCore import Qt, QSize, QRect, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QPainter, QPixmap, QPen, QIcon
from PySide6.QtWidgets import (
    QApplication, QSlider, QInputDialog, QMessageBox, QDialog, QProgressDialog, QMainWindow, QPushButton, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox, QScrollArea, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import QThread
from PySide6.QtGui import QImage, QPixmap
from matplotlib.figure import Figure
from ui.widgets.circular import CircleNumberWidget
from ui.magnifier import MagnifierGraphicsView
from core.polynomial import Polynomial
from core.resampling import ResamplingWorker
import numpy as np 
import matplotlib.pyplot as plt
from core.project import Project
from core.ga_runner import GARunner
from core.piecewise import SplitLineWindow
from ui.hover_button import HoverButton

class ToolBoxMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.project = Project.get_instance() 

        # Set window flags to make it movable
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Enable dragging of the window
        self.draggable = False
        self.offset = None
        self.image = None
        self.split_line_mode = False  
        self.line_points = []      
            
        # Create the main widget and set its layout
        main_widget = QWidget(self)
        self.main_layout = QHBoxLayout(main_widget)
        self.setCentralWidget(main_widget)

        # Left layout: Image display area
        image_layout = QVBoxLayout()
        self.image_scene = QGraphicsScene()
        self.image_viewer = MagnifierGraphicsView(self.image_scene, self)
        self.image_viewer.setScene(self.image_scene)
        self.image_viewer.setStyleSheet("border: 0.5px solid gray; background-color: transparent;")
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
        
        self.right_layout = QVBoxLayout()

        self.save_project_button = HoverButton("ui/icon/save.png")  # Replace with your save icon path
        self.save_project_button.clicked.connect(self.save_project_dialog)
        self.right_layout.addWidget(self.save_project_button)

        self.load_project_button = HoverButton("ui/icon/open.png")  # Replace with your load icon path
        self.load_project_button.clicked.connect(self.load_project_dialog)
        self.right_layout.addWidget(self.load_project_button)

        # Right layout: Buttons and controls
        self.open_button = HoverButton("ui/icon/image.png")
        
        self.open_button.clicked.connect(self.open_image)
        self.right_layout.addWidget(self.open_button)

        self.load_gcp_button = HoverButton("ui/icon/pin.png")
        self.load_gcp_button.clicked.connect(self.load_gcp_file)
        self.right_layout.addWidget(self.load_gcp_button)

        self.toggle_table_button = HoverButton("ui/icon/eye.png")
        self.toggle_table_button.clicked.connect(self.toggle_table_visibility)
        self.toggle_table_button.setVisible(False)
        self.right_layout.addWidget(self.toggle_table_button)
        last_layout = QVBoxLayout()

        self.forward_button = HoverButton("ui/icon/regress.png")  # "Forward" button
        self.forward_button.clicked.connect(self.perform_regression)
        self.right_layout.addWidget(self.forward_button)
        
        self.ga_button = HoverButton("ui/icon/GA.png")
        self.ga_button.clicked.connect(self.run_ga_workflow)
        self.ga_runner = GARunner(self)
        self.right_layout.addWidget(self.ga_button)
        
        self.split_line_button = HoverButton("ui/icon/piece.png", self)
        self.split_line_button.clicked.connect(self.enable_split_line_mode)
        self.right_layout.addWidget(self.split_line_button)
        
        self.resampling_button = HoverButton("ui/icon/resample.png", self) 
        self.resampling_button.clicked.connect(self.perform_resampling)
        self.right_layout.addWidget(self.resampling_button)

        self.degree_slider = QSlider(Qt.Vertical, self) 
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
    
    def open_split_line_window(self):

        if not self.image_viewer.pixmap:
            QMessageBox.warning(self, "Warning", "Please load an image before splitting.")
            return

        gcp_points = self.get_gcp_points()
        icp_points = self.get_icp_points()

        # Create the line-split dialog
        dialog = SplitLineWindow(
            qpixmap=self.image_viewer.pixmap, 
            gcp_points=gcp_points,
            icp_points=icp_points,
            scene=self.image_scene,
            degree=self.degree_slider.value(),
            parent=self
        )
        dialog.exec()


    def enable_split_line_mode(self):
        """
        Enables a mode in which the user can click two points on the image
        to define a line that splits the image into two parts.
        """
        if not self.image_scene.items():
            QMessageBox.warning(self, "Warning", "Please load an image first.")
            return

        self.line_points.clear()
        self.split_line_mode = True

        QMessageBox.information(
            self, "Split-Line Mode",
            "Click two points on the image to define a line that will split the image."
        )

    def run_ga_workflow(self):
        """
        Opens the GA parameter dialog, then runs GA if confirmed.
        """
        if self.ga_runner.open_parameter_dialog():
            self.ga_runner.run_ga()


    def perform_resampling(self):
        """
        Perform resampling using the Polynomial model in a separate thread.
        """
        if not self.image_viewer.pixmap:
            QMessageBox.warning(self, "Warning", "Please load an image before performing resampling.")
            return

        gcp_points = self.get_gcp_points()
        if not gcp_points:
            QMessageBox.warning(self, "Warning", "No GCP points available for resampling.")
            return

        step, ok = QInputDialog.getDouble(
            self, "Input", "Enter satellite GSD (resolution):", 1.0, 0.1, 500.0, 2
        )
        if not ok:
            return

        # Create a progress dialog
        self.progress_dialog = QProgressDialog("Resampling in progress...", "", 0, 100, self)
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.show()

        # Create the worker and thread
        self.resampling_worker = ResamplingWorker(
            image=self.image,
            gcp_points=gcp_points,
            icp_points=self.get_icp_points(),
            step=step,
            degree=self.degree_slider.value()
        )
        self.resampling_thread = QThread()

        self.resampling_worker.moveToThread(self.resampling_thread)

        self.resampling_thread.started.connect(self.resampling_worker.run)
        self.resampling_worker.finished.connect(self.resampling_thread.quit)
        self.progress_dialog.canceled.connect(self.resampling_worker.cancel)
        self.progress_dialog.rejected.connect(self.resampling_worker.cancel)
        self.resampling_worker.finished.connect(self.resampling_worker.deleteLater)
        self.resampling_thread.finished.connect(self.resampling_thread.deleteLater)
        self.resampling_worker.error.connect(self.handle_resampling_error)
        self.resampling_worker.progress.connect(self.progress_dialog.setValue)
        self.resampling_worker.resampled.connect(self.show_resampled_grid)

        self.resampling_thread.start()

    def handle_resampling_error(self, error_message):
        """Handle errors during resampling."""
        QMessageBox.critical(self, "Error", f"An error occurred during resampling: {error_message}")
        self.progress_dialog.close()

    def show_resampled_grid(self, grd_image):
        try:
            if np.all(grd_image == 0):
                return 
            
            if grd_image.ndim == 3 and grd_image.shape[2] == 3:
                # Convert RGB to single-channel grayscale by average
                grd_image = grd_image.mean(axis=2).astype(np.uint8)
            
            if grd_image.ndim == 3:
                height, width, _ = grd_image.shape
            else:
                height, width = grd_image.shape

            bytes_per_line = width 

            qimage = QImage(grd_image.data, width, height, bytes_per_line, QImage.Format_Grayscale8)

            pixmap = QPixmap.fromImage(qimage)

            dialog = QDialog(self)
            dialog.setWindowTitle("Resampled Grid Image (Scrollable)")

            label = QLabel()
            label.setPixmap(pixmap)
            label.setAlignment(Qt.AlignCenter)

            scroll_area = QScrollArea()
            scroll_area.setWidget(label)
            scroll_area.setWidgetResizable(True)

            layout = QVBoxLayout(dialog)
            layout.addWidget(scroll_area)
            dialog.setLayout(layout)

            dialog.resize(6000, 6000)

            dialog.exec()

        except Exception as e:
            print(f"Error displaying resampled grid: {e}")


    
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
        self.image_path = image_path
        if image_path:
            pixmap = QPixmap(image_path)
            self.image_scene.clear()
            self.image_viewer.set_pixmap(pixmap)

            pixmap_item = QGraphicsPixmapItem(pixmap)
            self.image_scene.addItem(pixmap_item)
            self.image_viewer.setScene(self.image_scene)
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
                    checkbox.stateChanged.connect(lambda state, row=row: self.update_icon(row, state))
                    self.table_widget.setCellWidget(row, 6, checkbox)

                    # Draw scaled icons on the image
                    if len(values) >= 3:  # Ensure there are at least x, y coordinates
                        x, y = int(float(values[1])), int(float(values[2]))
                        idx = values[0]

                        # Load, scale, and place the icon
                        icon_path = "ui/icon/redpin.png"  # Replace with the path to your icon
                        icon_pixmap = QPixmap(icon_path)
                        scaled_pixmap = icon_pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)  # Resize to 20x20
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

    def update_icon(self, row, state):
        """
        Updates the icon of the point based on the checkbox state.
        """
        # Determine the new icon path based on the checkbox state
        if state == Qt.Checked:
            icon_path = "ui/icon/redpin.png"  # Replace with the path to your selected icon
        else:
            icon_path = "ui/icon/bluepin.png"  # Replace with the path to your unselected icon

        # Get the x, y coordinates from the table
        x = float(self.table_widget.item(row, 1).text())
        y = float(self.table_widget.item(row, 2).text())

        # Load the new icon pixmap
        icon_pixmap = QPixmap(icon_path)
        if icon_pixmap.isNull():
            print(f"Failed to load icon from path: {icon_path}")
            return

        # Scale the icon pixmap
        scaled_pixmap = icon_pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        # Find and update the corresponding icon in the scene
        for item in self.image_scene.items():
            if isinstance(item, QGraphicsPixmapItem):
                # Calculate the item's center position
                item_center_x = item.offset().x() + item.pixmap().width() // 2
                item_center_y = item.offset().y() + item.pixmap().height() // 2

                # Check if the item's position matches the target coordinates
                if abs(item_center_x - x) < 1 and abs(item_center_y - y) < 1:
                    # Update the pixmap of the item
                    item.setPixmap(scaled_pixmap)
                    break  # Stop searching once the correct item is updated

        # Force the scene to update
        self.image_scene.update()


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
        and display quiver plots for forward and backward transformations side by side.
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
        
        coeffs_x_forward, coeffs_y_forward, coeffs_x_backward, coeffs_y_backward = polynomial.regress_polynomial()

        # Evaluate forward polynomial on ICP points
        predicted_x_forward, predicted_y_forward = polynomial.evaluate(
            (coeffs_x_forward, coeffs_y_forward), icp_points, forward=True
        )

        # Evaluate backward polynomial on GCP points
        predicted_x_backward, predicted_y_backward = polynomial.evaluate(
            (coeffs_x_backward, coeffs_y_backward), icp_points, forward=False
        )

        self.project.forward_coeffs = (coeffs_x_forward, coeffs_y_forward)
        self.project.backward_coeffs = (coeffs_x_backward, coeffs_y_backward)
        self.project.normalization_factor = polynomial.normalization_factors
        self.project.degree = degree

        actual_X = np.array([point['x'] for point in icp_points])
        actual_Y = np.array([point['y'] for point in icp_points])
        rmse_X_forward, rmse_Y_forward = polynomial.rmse(predicted_x_forward, predicted_y_forward, actual_X, actual_Y)

        actual_x = np.array([point['X'] for point in icp_points])
        actual_y = np.array([point['Y'] for point in icp_points])
        rmse_X_backward, rmse_Y_backward = polynomial.rmse(predicted_x_backward, predicted_y_backward, actual_x, actual_y)

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Evaluation Results")
        msg_box.setText(
            f"<b>Evaluation Summary:</b><br><br>"
            f"<b>Forward Transformation:</b><br>"
            f"RMSE (X): {rmse_X_forward:.4f}, RMSE (Y): {rmse_Y_forward:.4f}<br><br>"
            f"<b>Backward Transformation:</b><br>"
            f"RMSE (X): {rmse_X_backward:.4f}, RMSE (Y): {rmse_Y_backward:.4f}"
        )
        msg_box.exec()

        self.show_quiver_plots(icp_points, predicted_x_forward, predicted_y_forward, predicted_x_backward, predicted_y_backward)

    def show_quiver_plots(self, icp_points, predicted_x_forward, predicted_y_forward, predicted_x_backward, predicted_y_backward):
        """
        Show two quiver plots side-by-side in a PyQt canvas.
        One for the forward transformation and one for the backward transformation.
        """

        # Create a new dialog for the plots
        dialog = QDialog(self)
        dialog.setWindowTitle("Quiver Plots")
        dialog.setMinimumSize(1200, 600)  # Adjusted size for side-by-side plots

        # Create a QLabel to display the plots
        label = QLabel(dialog)

        # Create the figure for the plots
        fig, axes = plt.subplots(1, 2, figsize=(15, 8))
        fig.patch.set_facecolor('#2E2E2E')  # Dark gray background for the figure

        # Forward transformation plot
        x_forward = [point['x'] for point in icp_points]
        y_forward = [point['y'] for point in icp_points]
        u_forward = predicted_x_forward - np.array([point['x'] for point in icp_points])
        v_forward = predicted_y_forward - np.array([point['y'] for point in icp_points])

        image = self.image_viewer.pixmap.toImage()
        self.image = image 
        image_array = np.array(image.bits()).reshape(image.height(), image.width(), 4)[..., :3]

        # Display the image as the background
        axes[0].imshow(image_array, extent=[0, image.width(), 0, image.height()], origin='upper')
        axes[0].quiver(x_forward, y_forward, u_forward, v_forward, angles='xy', scale_units='xy', scale=1, color='cyan')
        axes[0].set_title("Forward Transformation", color='white')
        axes[0].set_xlabel("x", color='white')
        axes[0].set_ylabel("y", color='white')
        axes[0].tick_params(axis='both', colors='white')
        axes[0].grid(color='gray', linestyle='--', linewidth=0.5)

        # Backward transformation plot
        x_backward = [point['X'] for point in icp_points]
        y_backward = [point['Y'] for point in icp_points]
        u_backward = predicted_x_backward - np.array([point['X'] for point in icp_points])
        v_backward = predicted_y_backward - np.array([point['Y'] for point in icp_points])

        axes[1].quiver(x_backward, y_backward, u_backward, v_backward, angles='xy', scale_units='xy', scale=1, color='orange')
        axes[1].set_title("Backward Transformation", color='white')
        axes[1].set_xlabel("X", color='white')
        axes[1].set_ylabel("Y", color='white')
        axes[1].tick_params(axis='both', colors='white')
        axes[1].grid(color='gray', linestyle='--', linewidth=0.5)

        # Render the plot onto a QPixmap
        fig.canvas.draw()
        width, height = fig.canvas.get_width_height()
        plot_data = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8).reshape(height, width, 3)
        plt.close(fig)

        # Convert the plot data to a QImage and then a QPixmap
        plot_image = QImage(plot_data, width, height, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(plot_image)

        label.setPixmap(pixmap)
        label.setAlignment(Qt.AlignCenter)

        # Set up the dialog layout
        layout = QVBoxLayout()
        layout.addWidget(label)
        dialog.setLayout(layout)

        # Show the dialog
        dialog.exec()
        
    def save_project_dialog(self):
        """Open a file dialog to save the project."""
        filename, _ = QFileDialog.getSaveFileName(self, "Save Project", "", "Project Files (*.proj)")
        if filename:
            self.save_project(filename)

    def load_project_dialog(self):
        """Open a file dialog to load the project."""
        filename, _ = QFileDialog.getOpenFileName(self, "Load Project", "", "Project Files (*.proj)")
        if filename:
            self.load_project(filename)

    def update_ui_from_project(self):
        """Update the UI based on the state of the Project instance."""
        if self.project.image_path:
            self.open_image()  # Reload the image
        if self.project.gcp_points:
            self.load_gcp_file()  # Reload GCP points
        if self.project.degree:
            self.degree_slider.setValue(self.project.degree)
    
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
            
    def perform_split_line_regression(self, x1, y1, x2, y2):
        """
        Splits GCP/ICP points based on which side of the line (x1,y1)->(x2,y2) they fall on.
        Performs polynomial regression separately for each side, and displays RMSE results.
        """
        # 1) Grab GCP/ICP from the table
        gcp_points = self.get_gcp_points()
        icp_points = self.get_icp_points()
        degree = self.degree_slider.value()

        if not gcp_points:
            QMessageBox.warning(self, "Warning", "No GCP points available.")
            return
        
        if not icp_points:
            QMessageBox.warning(self, "Warning", "No ICP points available.")
            return

        # 2) Separate GCPs into two sides
        gcp_side_a = []
        gcp_side_b = []
        for gcp in gcp_points:
            sign = self._side_of_line(gcp["x"], gcp["y"], x1, y1, x2, y2)
            if sign >= 0:
                gcp_side_a.append(gcp)
            else:
                gcp_side_b.append(gcp)

        # 3) Separate ICPs into two sides
        icp_side_a = []
        icp_side_b = []
        for icp in icp_points:
            sign = self._side_of_line(icp["x"], icp["y"], x1, y1, x2, y2)
            if sign >= 0:
                icp_side_a.append(icp)
            else:
                icp_side_b.append(icp)

        # 4) Regress & compute RMSE
        rmseA_forward, rmseA_backward = self._regress_and_rmse(gcp_side_a, icp_side_a, degree)
        rmseB_forward, rmseB_backward = self._regress_and_rmse(gcp_side_b, icp_side_b, degree)

        # 5) Show results
        text_lines = []
        text_lines.append("<b>Split Line Regression Results</b><br>")

        if rmseA_forward is None:
            text_lines.append("<b>Side A</b>: Not enough GCP/ICP for regression.<br><br>")
        else:
            fx, fy = rmseA_forward
            bx, by = rmseA_backward
            text_lines.append(
                f"<b>Side A</b> (GCPs={len(gcp_side_a)}, ICPs={len(icp_side_a)})<br>"
                f"Forward RMSE: X={fx:.4f}, Y={fy:.4f}<br>"
                f"Backward RMSE: X={bx:.4f}, Y={by:.4f}<br><br>"
            )

        if rmseB_forward is None:
            text_lines.append("<b>Side B</b>: Not enough GCP/ICP for regression.<br><br>")
        else:
            fx, fy = rmseB_forward
            bx, by = rmseB_backward
            text_lines.append(
                f"<b>Side B</b> (GCPs={len(gcp_side_b)}, ICPs={len(icp_side_b)})<br>"
                f"Forward RMSE: X={fx:.4f}, Y={fy:.4f}<br>"
                f"Backward RMSE: X={bx:.4f}, Y={by:.4f}<br><br>"
            )

        QMessageBox.information(self, "Split Regression RMSE", "".join(text_lines))

    def _regress_and_rmse(self, gcp_list, icp_list, degree):
        """
        Utility to regress a polynomial from gcp_list and evaluate RMSE on icp_list.
        Returns: ( (rmseX_fwd, rmseY_fwd), (rmseX_bwd, rmseY_bwd) ) or (None, None) if not enough points.
        """
        if len(gcp_list) < 2 or len(icp_list) < 1:
            return None, None  # Not enough data

        poly = Polynomial(gcp_list, degree)
        fx, fy, bx, by = poly.regress_polynomial()

        px_fwd, py_fwd = poly.evaluate((fx, fy), icp_list, forward=True)
        px_bwd, py_bwd = poly.evaluate((bx, by), icp_list, forward=False)

        actual_x = np.array([p["x"] for p in icp_list])
        actual_y = np.array([p["y"] for p in icp_list])
        rmseX_fwd, rmseY_fwd = poly.rmse(px_fwd, py_fwd, actual_x, actual_y)

        actual_X = np.array([p["X"] for p in icp_list])
        actual_Y = np.array([p["Y"] for p in icp_list])
        rmseX_bwd, rmseY_bwd = poly.rmse(px_bwd, py_bwd, actual_X, actual_Y)

        return (rmseX_fwd, rmseY_fwd), (rmseX_bwd, rmseY_bwd)
    
    def _side_of_line(self, px, py, x1, y1, x2, y2):
        """
        Returns the signed cross product to indicate which side
        of the line (x1,y1)->(x2,y2) the point (px,py) is on.
        Positive => left side, negative => right side, 0 => on the line.
        """
        return (px - x1) * (y2 - y1) - (py - y1) * (x2 - x1)