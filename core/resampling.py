import numpy as np
from PySide6.QtWidgets import QGraphicsPixmapItem
from core.project import Project  
from core.polynomial import Polynomial
from scipy.ndimage import map_coordinates
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtGui import QImage

class ResamplingWorker(QObject):
    finished = Signal()           
    progress = Signal(int)
    error = Signal(str)         
    resampled = Signal(np.ndarray)

    def __init__(self, image, gcp_points, icp_points, step, degree):
        super().__init__()
        self.image = image
        self.gcp_points = gcp_points
        self.icp_points = icp_points
        self.step = step
        self.degree = degree
        self._is_cancelled = False  # Flag to handle cancellation

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

            # Perform resampling with progress updates
            grd_image = resampling.resample(
                step=self.step,
                progress_callback=self.progress.emit,
                cancel_flag=lambda: self._is_cancelled
            )

            if not self._is_cancelled and grd_image is not None:
                # Save the result for debugging or further processing
                np.save("resampled_grid.npy", grd_image)
                # Emit the resampled (RGB) grid
                self.resampled.emit(grd_image)

            # Emit the finished signal
            self.finished.emit()

        except Exception as e:
            # Emit the error signal if something goes wrong
            self.error.emit(str(e))

    def cancel(self):
        """
        Set the cancellation flag to stop the resampling process.
        """
        self._is_cancelled = True

class Resampling:
    def __init__(self, image , gcp_points, icp_points, degree):
        """
        Initialize the Resampling class with backward transform coefficients.

        :param image:       QImage containing the input image data.
        :param gcp_points:  List of ground control points [{ 'X': ..., 'Y': ... }, ...].
        :param icp_points:  List of independent check points (not used here but kept for consistency).
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
        print(self.image.shape)

        project = Project.get_instance()
        self.normalization_factors = project.normalization_factor
        self.backward_coeffs = project.backward_coeffs
        self.forward_coeffs = project.forward_coeffs
        self.degree = project.degree

    @staticmethod
    def qimage_to_numpy(image) -> np.ndarray:
        """
        Convert a QImage to a NumPy array (height, width, 3) for RGB.

        :param image: QImage object
        :return: NumPy array representation of the image
        """
        if image is None or image.isNull():
            raise ValueError("Invalid QImage provided.")
        
        # Ensure the QImage is in RGB32 format
        image = image.convertToFormat(QImage.Format.Format_RGB32)
        
        width, height = image.width(), image.height()
        
        # Access the raw buffer data
        ptr = image.bits()  # Returns a sip.voidptr
        arr = np.frombuffer(ptr, dtype=np.uint8).reshape((height, width, 4))  # Shape as (H, W, 4)

        # Extract RGB channels (drop alpha channel)
        return arr[..., :3].astype(np.float32)

    def build_design_matrix(self, x, y):
        """Build the design matrix for polynomial regression."""
        num_terms = (self.degree + 1) * (self.degree + 2) // 2  # Number of terms in the polynomial
        A = np.zeros((len(x), num_terms))

        idx = 0
        for i in range(self.degree + 1):
            for j in range(self.degree + 1 - i):
                A[:, idx] = (x ** i) * (y ** j)
                idx += 1

        return A
    
    def evaluate(self, coeffs, points, forward=True):
        coeffs_1, coeffs_2 = coeffs

        x, y = points[:, 0], points[:, 1]

        if forward:
            x = (x - self.normalization_factors["X_mean"]) / self.normalization_factors["X_std"]
            y = (y - self.normalization_factors["Y_mean"]) / self.normalization_factors["Y_std"]
        else:
            x = (x - self.normalization_factors["x_mean"]) / self.normalization_factors["x_std"]
            y = (y - self.normalization_factors["y_mean"]) / self.normalization_factors["y_std"]

        A = self.build_design_matrix(x, y)

        evaluated_1 = A @ coeffs_1
        evaluated_2 = A @ coeffs_2

        if forward:
            evaluated_1 = (evaluated_1 * self.normalization_factors["x_std"]) + self.normalization_factors["x_mean"]
            evaluated_2 = (evaluated_2 * self.normalization_factors["y_std"]) + self.normalization_factors["y_mean"]
        else:
            evaluated_1 = (evaluated_1 * self.normalization_factors["X_std"]) + self.normalization_factors["X_mean"]
            evaluated_2 = (evaluated_2 * self.normalization_factors["Y_std"]) + self.normalization_factors["Y_mean"]

        return evaluated_1, evaluated_2


    def resample(self, step=1.0, progress_callback=None, cancel_flag=None, chunk_size=500):

        if self.image is None:
            raise ValueError("No image loaded for resampling.")

        # -----------------------------------------------------------
        # 1) Compute the bounding box in ground coords using forward transform
        #    corners in pixel coordinates: (x=col, y=row)
        # -----------------------------------------------------------
        # shape: self.image_height x self.image_width, so:
        #   - width  = number of columns  = self.image_width
        #   - height = number of rows     = self.image_height
        corners_pixel = np.array([
            [0,                  0                 ],  # top-left
            [self.image_width-1, 0                 ],  # top-right
            [0,                  self.image_height-1],  # bottom-left
            [self.image_width-1, self.image_height-1]
        ], dtype=np.float32)

        ground_x_corners, ground_y_corners = self.evaluate(
            self.backward_coeffs, corners_pixel, forward=False
        )

        minX, maxX = ground_x_corners.min(), ground_x_corners.max()
        minY, maxY = ground_y_corners.min(), ground_y_corners.max()

        print(minX, maxX, minY, maxY)
        
        x_vals = np.arange(minX, maxX + step, step, dtype=np.float32)
        y_vals = np.arange(maxY, minY - step, -step, dtype=np.float32)

        out_h = len(y_vals)  # number of rows in output
        out_w = len(x_vals)  # number of columns in output

        resampled_img = np.zeros((out_h, out_w, 3), dtype=np.float32)

        total_rows = out_h
        for start_row in range(0, out_h, chunk_size):
            # if cancel_flag and cancel_flag.is_set():
            #     # If there's a cancel signal, abort.
            #     break

            end_row = min(start_row + chunk_size, out_h)
            current_chunk_size = end_row - start_row

            # Build ground coordinates for all pixels in [start_row, end_row)
            # We'll have a grid of size (current_chunk_size x out_w).
            # Flatten them to shape N x 2 for calling self.evaluate() once.
            yy = np.repeat(y_vals[start_row:end_row], out_w)
            xx = np.tile(x_vals, current_chunk_size)

            ground_pts = np.column_stack((xx, yy)).astype(np.float32)

            img_x_vals, img_y_vals = self.evaluate(
                self.forward_coeffs, ground_pts, forward=True
            )

            img_x_vals = img_x_vals.reshape(current_chunk_size, out_w)
            img_y_vals = img_y_vals.reshape(current_chunk_size, out_w)

            # Interpolate each row of the chunk
            for r in range(current_chunk_size):
                for c in range(out_w):
                    px = img_x_vals[r, c]
                    py = img_y_vals[r, c]

                    # Check if (py, px) is inside the image bounds
                    if (0 <= px < self.image_width - 1) and (0 <= py < self.image_height - 1):
                        # Bilinear interpolation
                        x_floor = int(np.floor(px))
                        x_ceil  = x_floor + 1
                        y_floor = int(np.floor(py))
                        y_ceil  = y_floor + 1

                        dx = px - x_floor
                        dy = py - y_floor

                        # 4 corners of the interpolation
                        top_left     = self.image[y_floor, x_floor, :]
                        top_right    = self.image[y_floor, x_ceil,  :]
                        bottom_left  = self.image[y_ceil,  x_floor, :]
                        bottom_right = self.image[y_ceil,  x_ceil,  :]

                        # Linear interpolation in x-direction
                        top    = top_left    + dx * (top_right    - top_left)
                        bottom = bottom_left + dx * (bottom_right - bottom_left)

                        # Then linear interpolation in y-direction
                        pixel_val = top + dy * (bottom - top)

                        resampled_img[start_row + r, c, :] = pixel_val
                    else:
                        resampled_img[start_row + r, c, :] = [0, 0, 0]

            if progress_callback:
                progress_callback(float(end_row) / float(total_rows))

        resampled_img_uint8 = np.clip(resampled_img, 0, 255).astype(np.uint8)
        
        return resampled_img_uint8

        
