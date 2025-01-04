import numpy as np
from PySide6.QtWidgets import QGraphicsPixmapItem
from core.project import Project  
from core.polynomial import Polynomial
from scipy.ndimage import map_coordinates
from PySide6.QtCore import QObject, Signal, Slot

class ResamplingWorker(QObject):
    finished = Signal()            # Signal emitted when resampling is complete
    progress = Signal(int)         # Signal to update progress
    error = Signal(str)            # Signal to report errors
    resampled = Signal(np.ndarray) # Signal to emit the resampled grid (RGB)

    def __init__(self, image_scene, gcp_points, icp_points, step, degree):
        super().__init__()
        self.image_scene = image_scene
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
                image_scene=self.image_scene,
                gcp_points=self.gcp_points,
                icp_points=self.icp_points
            )
            resampling.load_image()

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
    def __init__(self, image_scene, gcp_points, icp_points):
        """
        Initialize the Resampling class with backward transform coefficients.

        :param image_scene: QGraphicsScene containing the image (QGraphicsPixmapItem).
        :param gcp_points:  List of ground control points [{ 'X': ..., 'Y': ... }, ...].
        :param icp_points:  List of independent check points (not used here but kept for consistency).
        """
        self.image_scene = image_scene
        self.gcp_points = gcp_points
        self.icp_points = icp_points
        
        # We will keep an RGB image instead of grayscale.
        self.image = None
        self.image_height = None
        self.image_width = None

        # Retrieve backward parameters from the Project singleton
        project = Project.get_instance()
        # backward = (coeffs_x, coeffs_y) that map (X, Y) -> (x, y)
        self.backward_coeffs = project.backward_coeffs
        self.degree = project.degree

    def load_image(self):
        """
        Load the image from QGraphicsScene and store full RGB data (float32).
        """
        for item in self.image_scene.items():
            if isinstance(item, QGraphicsPixmapItem):
                pixmap = item.pixmap()

                # Convert QImage -> NumPy array with shape (height, width, 4).
                qimage = pixmap.toImage()
                width, height = qimage.width(), qimage.height()

                # Get a memory view of the raw bits.
                ptr = qimage.bits()

                # Determine how many bytes the image has in total.
                nbytes = qimage.sizeInBytes()  # or qimage.byteCount()

                # Convert the memory view to a buffer of the correct size,
                # then create a NumPy array from that buffer.
                arr = np.frombuffer(ptr, dtype=np.uint8, count=nbytes)

                # Finally, reshape to (height, width, 4) for RGBA (or (height, width, 3) if RGB).
                arr = arr.reshape((height, width, 4))


                # Keep only first 3 channels for RGB
                self.image = arr[..., :3].astype(np.float32)
                self.image_height, self.image_width, _ = self.image.shape

                return

        raise ValueError("No image found in the QGraphicsScene.")

    def resample(self, step=1.0, progress_callback=None, cancel_flag=None, chunk_size=500):
        """
        Create an output map grid in ground coordinates, then use the backward model
        to find corresponding image coords and sample the original image's RGB.

        :param step:            Satellite GSD (resolution).
        :param progress_callback: Function to report progress.
        :param cancel_flag:     Function returning True if the operation should be canceled.
        :param chunk_size:      Number of rows to process at once to avoid large memory usage.
        :return:                A 3D numpy array with shape (rows, cols, 3), the resampled RGB image.
        """
        if self.image is None:
            raise ValueError("No image loaded for resampling.")
        if self.backward_coeffs is None:
            raise ValueError("Backward coefficients are not available in the Project instance.")

        # 1) Determine bounding box in ground space
        gcp_array = np.array([[p["X"], p["Y"]] for p in self.gcp_points], dtype=np.float32)
        min_x, min_y = np.min(gcp_array, axis=0)
        max_x, max_y = np.max(gcp_array, axis=0)

        # 2) Create grid of (X, Y) in ground space
        grd_x_net, grd_y_net = np.meshgrid(
            np.arange(min_x, max_x, step),
            np.arange(max_y, min_y, -step)
        )
        rows, cols = grd_x_net.shape

        # 3) Allocate output array for RGB (float32 or uint8). We'll do float32 here.
        grd_image = np.zeros((rows, cols, 3), dtype=np.float32)

        # Flatten for chunk-based processing
        for start_row in range(0, rows, chunk_size):
            end_row = min(start_row + chunk_size, rows)

            # Extract subset (chunk) in ground coords
            chunk_x = grd_x_net[start_row:end_row, :]
            chunk_y = grd_y_net[start_row:end_row, :]

            # Flatten chunk to 1D for vectorized transform
            X = chunk_x.ravel()
            Y = chunk_y.ravel()

            # 4) Evaluate backward transform: (X, Y) -> (x, y) in image space
            img_x, img_y = self.evaluate_backward_vectorized(X, Y)

            # 5) Clip to valid image boundaries
            valid_mask = (
                (img_x >= 0) & (img_x < self.image_width) &
                (img_y >= 0) & (img_y < self.image_height)
            )

            valid_indices = np.where(valid_mask)[0]
            if valid_indices.size == 0:
                # Nothing valid in this chunk
                # Update progress and continue to next chunk
                if progress_callback:
                    pct = int((end_row / rows) * 100)
                    progress_callback(pct)
                continue

            valid_img_x = img_x[valid_mask]
            valid_img_y = img_y[valid_mask]

            # 6) Bilinear interpolation for each color channel
            # map_coordinates expects [row, col] => [y, x].
            interpolated_chunk = np.zeros((valid_indices.size, 3), dtype=np.float32)
            for c in range(3):
                channel_data = self.image[..., c]
                interpolated_chunk[:, c] = map_coordinates(
                    channel_data,
                    [valid_img_y, valid_img_x],
                    order=1,
                    mode='nearest'
                )

            # 7) Place interpolated RGB values back into the correct positions of grd_image
            # Flatten the chunk portion in the output
            chunk_flat = grd_image[start_row:end_row, :].reshape(-1, 3)
            chunk_flat[valid_indices, :] = interpolated_chunk

            # 8) Check for cancellation
            if cancel_flag and cancel_flag():
                return None

            # 9) Update progress
            if progress_callback:
                pct = int((end_row / rows) * 100)
                progress_callback(pct)

        return grd_image

    def evaluate_backward_vectorized(self, X, Y):
        """
        Evaluate the backward polynomial at arrays X, Y.
        This maps ground coords -> image coords.
        
        :param X: np.ndarray of ground X
        :param Y: np.ndarray of ground Y
        :return:  (x, y) in image space, as float arrays.
        """
        coeffs_x, coeffs_y = self.backward_coeffs
        degree = self.degree

        # Number of polynomial terms for a 2D polynomial of given degree
        num_terms = (degree + 1) * (degree + 2) // 2
        A = np.zeros((len(X), num_terms), dtype=np.float32)

        idx = 0
        # Build design matrix for 2D polynomial: X^i * Y^j
        for i in range(degree + 1):
            for j in range(degree + 1 - i):
                A[:, idx] = (X ** i) * (Y ** j)
                idx += 1

        # Evaluate
        x = A @ coeffs_x
        y = A @ coeffs_y
        return x, y
