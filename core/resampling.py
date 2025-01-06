import numpy as np
from PySide6.QtWidgets import QGraphicsPixmapItem
from core.project import Project
from core.polynomial import Polynomial
from scipy.ndimage import map_coordinates
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtGui import QImage

global canceled
canceled = None 

class ResamplingWorker(QObject):
    finished = Signal()           
    progress = Signal(float)
    error = Signal(str)         
    resampled = Signal(np.ndarray)

    def __init__(self, image, gcp_points, icp_points, step, degree):
        super().__init__()
        self.image = image
        self.gcp_points = gcp_points
        self.icp_points = icp_points
        self.step = step
        self.degree = degree
        self._is_cancelled = False 

    @Slot()
    def run(self):
        """
        Perform the resampling in the background using backward parameters.
        """
        try:
            resampling = Resampling(
                image=self.image,
                gcp_points=self.gcp_points,
                icp_points=self.icp_points,
                degree=self.degree
            )

            grd_image = resampling.resample(
                step=self.step,
                progress_callback=self.progress.emit,
                cancel_flag=lambda: self._is_cancelled
            )

            if not self._is_cancelled and grd_image is not None:
                np.save("resampled_grid.npy", grd_image)
                self.resampled.emit(grd_image)

            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))

    def cancel(self):
        """
        Set the cancellation flag to stop the resampling process.
        """
        self._is_cancelled = True

class Resampling:
    def __init__(self, image, gcp_points, icp_points, degree):
        """
        Initialize the Resampling class with backward transform coefficients.
        """
        self.image = self.qimage_to_numpy(image)
        self.gcp_points = gcp_points
        self.icp_points = icp_points
        self.poly = Polynomial(gcp_points, degree)

        # Extract image dimensions
        if self.image is not None:
            self.image_height, self.image_width, _ = self.image.shape
        else:
            self.image_height = None
            self.image_width = None

        print("Loaded image shape:", self.image.shape)

        project = Project.get_instance()
        self.normalization_factors = project.normalization_factor
        self.backward_coeffs = project.backward_coeffs
        self.forward_coeffs = project.forward_coeffs
        self.degree = project.degree

    @staticmethod
    def qimage_to_numpy(image) -> np.ndarray:
        """
        Convert a QImage to a NumPy array (height, width, 3) for RGB.
        """
        if image is None or image.isNull():
            raise ValueError("Invalid QImage provided.")
        
        image = image.convertToFormat(QImage.Format.Format_RGB32)
        
        width, height = image.width(), image.height()
        
        ptr = image.bits()  # Returns a sip.voidptr
        arr = np.frombuffer(ptr, dtype=np.uint8).reshape((height, width, 4))  # (H, W, 4)
        return arr[..., :3].astype(np.float32)

    def build_design_matrix(self, x, y):
        """Build the design matrix for polynomial regression."""
        num_terms = (self.degree + 1) * (self.degree + 2) // 2
        A = np.zeros((len(x), num_terms), dtype=np.float32)

        idx = 0
        for i in range(self.degree + 1):
            for j in range(self.degree + 1 - i):
                A[:, idx] = (x ** i) * (y ** j)
                idx += 1

        return A
    
    def evaluate(self, coeffs, points, forward=True):
        coeffs_1, coeffs_2 = coeffs

        x, y = points[:, 0], points[:, 1]

        # Normalize input
        if forward:
            x = (x - self.normalization_factors["X_mean"]) / self.normalization_factors["X_std"]
            y = (y - self.normalization_factors["Y_mean"]) / self.normalization_factors["Y_std"]
        else:
            x = (x - self.normalization_factors["x_mean"]) / self.normalization_factors["x_std"]
            y = (y - self.normalization_factors["y_mean"]) / self.normalization_factors["y_std"]

        A = self.build_design_matrix(x, y)

        evaluated_1 = A @ coeffs_1
        evaluated_2 = A @ coeffs_2

        # Denormalize output
        if forward:
            evaluated_1 = (evaluated_1 * self.normalization_factors["x_std"]) + self.normalization_factors["x_mean"]
            evaluated_2 = (evaluated_2 * self.normalization_factors["y_std"]) + self.normalization_factors["y_mean"]
        else:
            evaluated_1 = (evaluated_1 * self.normalization_factors["X_std"]) + self.normalization_factors["X_mean"]
            evaluated_2 = (evaluated_2 * self.normalization_factors["Y_std"]) + self.normalization_factors["Y_mean"]

        return evaluated_1, evaluated_2

    def resample(self, step=1.0, progress_callback=None, cancel_flag=None, chunk_size=500):
        """
        Resample the image using pre-computed polynomial transforms.
        Vectorized bilinear interpolation is used to speed up processing.
        """
        if self.image is None:
            raise ValueError("No image loaded for resampling.")

        corners_pixel = np.array([
            [0,                  0],
            [self.image_width-1, 0],
            [0,                  self.image_height-1],
            [self.image_width-1, self.image_height-1]
        ], dtype=np.float32)

        ground_x_corners, ground_y_corners = self.evaluate(
            self.backward_coeffs, corners_pixel, forward=False
        )

        minX, maxX = ground_x_corners.min(), ground_x_corners.max()
        minY, maxY = ground_y_corners.min(), ground_y_corners.max()

        print("Ground corners bounding box (minX, maxX, minY, maxY):",
              minX, maxX, minY, maxY)

        # 2) Create output grid coordinates (in ground space)
        x_vals = np.arange(minX, maxX + step, step, dtype=np.float32)
        y_vals = np.arange(maxY, minY - step, -step, dtype=np.float32)

        out_h = len(y_vals) 
        out_w = len(x_vals)  

        resampled_img = np.zeros((out_h, out_w, 3), dtype=np.float32)

        total_rows = out_h
        for start_row in range(0, out_h, chunk_size):
            if cancel_flag and cancel_flag():
                print("Resampling cancelled at row:", start_row)
                break


            end_row = min(start_row + chunk_size, out_h)
            current_chunk_size = end_row - start_row

           
            yy = np.repeat(y_vals[start_row:end_row], out_w)
            xx = np.tile(x_vals, current_chunk_size)
            ground_pts = np.column_stack((xx, yy)).astype(np.float32)

            img_x_vals, img_y_vals = self.evaluate(
                self.forward_coeffs, ground_pts, forward=True
            )

            img_x_vals = img_x_vals.reshape(current_chunk_size, out_w)
            img_y_vals = img_y_vals.reshape(current_chunk_size, out_w)

          
            valid_mask = (
                (img_x_vals >= 0) &
                (img_x_vals < (self.image_width - 1)) &
                (img_y_vals >= 0) &
                (img_y_vals < (self.image_height - 1))
            )

            x_floor = np.floor(img_x_vals[valid_mask]).astype(np.int32)
            y_floor = np.floor(img_y_vals[valid_mask]).astype(np.int32)
            dx = img_x_vals[valid_mask] - x_floor
            dy = img_y_vals[valid_mask] - y_floor

            top_left     = self.image[y_floor, x_floor]
            top_right    = self.image[y_floor, x_floor + 1]
            bottom_left  = self.image[y_floor + 1, x_floor]
            bottom_right = self.image[y_floor + 1, x_floor + 1]

            top    = top_left + dx[:, None] * (top_right - top_left)
            bottom = bottom_left + dx[:, None] * (bottom_right - bottom_left)
            pixel_vals = top + dy[:, None] * (bottom - top)

            resampled_chunk = np.zeros((current_chunk_size, out_w, 3), dtype=np.float32)

          
            valid_flat = valid_mask.reshape(-1)
            resampled_chunk_flat = resampled_chunk.reshape(-1, 3)

            resampled_chunk_flat[valid_flat] = pixel_vals

            resampled_img[start_row:end_row, :, :] = resampled_chunk

            progress_callback((float(end_row) / float(total_rows)) * 100)

        resampled_img_uint8 = np.clip(resampled_img, 0, 255).astype(np.uint8)
        
        return resampled_img_uint8
