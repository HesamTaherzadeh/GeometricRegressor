import numpy as np
from PySide6.QtWidgets import QGraphicsPixmapItem

class Resampling:
    def __init__(self, polynomial, image_scene, gcp_points, icp_points):
        """
        Initialize the Resampling class.

        Parameters:
        polynomial (Polynomial): Polynomial object for transformations.
        image_scene (QGraphicsScene): Scene containing the image.
        gcp_points (list): List of GCP points.
        icp_points (list): List of ICP points.
        """
        self.polynomial = polynomial
        self.image_scene = image_scene
        self.gcp_points = gcp_points
        self.icp_points = icp_points
        self.gray_image = None
        self.image_height = None
        self.image_width = None

    def load_image(self):
        """Load the image from QGraphicsScene and convert it to grayscale."""
        items = self.image_scene.items()
        for item in items:
            if isinstance(item, QGraphicsPixmapItem):
                pixmap = item.pixmap()
                image = pixmap.toImage()
                width, height = image.width(), image.height()
                image = np.array(image.bits()).reshape(height, width, 4)[..., :3]  # Convert to RGB
                self.gray_image = np.mean(image, axis=-1).astype(np.float32)  # Convert to grayscale
                self.image_height, self.image_width = self.gray_image.shape
                return
        raise ValueError("No image found in the QGraphicsScene.")

    def resample(self, step=1.0):
        """
        Perform resampling based on the polynomial model.

        Parameters:
        step (float): The satellite GSD (resolution) for resampling.

        Returns:
        np.ndarray: Resampled grid image.
        """
        if self.gray_image is None:
            raise ValueError("Gray image is not loaded.")

        # Create resampling grid
        min_x, min_y = np.min([[p['X'], p['Y']] for p in self.gcp_points], axis=0)
        max_x, max_y = np.max([[p['X'], p['Y']] for p in self.gcp_points], axis=0)

        grd_x_net, grd_y_net = np.meshgrid(
            np.arange(min_x, max_x, step),
            np.arange(max_y, min_y, -step)
        )
        p, q = grd_x_net.shape

        # Initialize grid image
        grd_image = np.zeros((p, q), dtype=np.float32)

        # Resampling
        for u in range(p):
            for v in range(q):
                grd_net = np.array([grd_x_net[u, v], grd_y_net[u, v]])
                x, y = self.polynomial.evaluate_inverse(grd_net)  # Perform inverse transformation

                if 0 <= x < self.image_height and 0 <= y < self.image_width:
                    grd_image[u, v] = self.bilinear_interpolate(x, y)

        return grd_image

    def bilinear_interpolate(self, x, y):
        """Perform bilinear interpolation."""
        x1, x2 = int(np.floor(x)), int(np.ceil(x))
        y1, y2 = int(np.floor(y)), int(np.ceil(y))

        q11 = self.gray_image[x1, y1] if x1 < self.image_height and y1 < self.image_width else 0
        q21 = self.gray_image[x2, y1] if x2 < self.image_height and y1 < self.image_width else 0
        q12 = self.gray_image[x1, y2] if x1 < self.image_height and y2 < self.image_width else 0
        q22 = self.gray_image[x2, y2] if x2 < self.image_height and y2 < self.image_width else 0

        interpolated = (
            q11 * (x2 - x) * (y2 - y) +
            q21 * (x - x1) * (y2 - y) +
            q12 * (x2 - x) * (y - y1) +
            q22 * (x - x1) * (y - y1)
        )
        return interpolated
