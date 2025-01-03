import numpy as np

class Polynomial:
    def __init__(self, gcp_points, degree):
        self.gcp_points = gcp_points
        self.degree = degree
        self.normalization_factors = None
        self.design_matrix = None

    def normalize_data(self):
        """Normalize the GCP data and keep normalization factors."""
        x = np.array([point['x'] for point in self.gcp_points])
        y = np.array([point['y'] for point in self.gcp_points])
        X = np.array([point['X'] for point in self.gcp_points])
        Y = np.array([point['Y'] for point in self.gcp_points])

        self.normalization_factors = {
            "x_mean": x.mean(), "x_std": x.std(),
            "y_mean": y.mean(), "y_std": y.std(),
            "X_mean": X.mean(), "X_std": X.std(),
            "Y_mean": Y.mean(), "Y_std": Y.std(),
        }

        x = (x - self.normalization_factors["x_mean"]) / self.normalization_factors["x_std"]
        y = (y - self.normalization_factors["y_mean"]) / self.normalization_factors["y_std"]
        X = (X - self.normalization_factors["X_mean"]) / self.normalization_factors["X_std"]
        Y = (Y - self.normalization_factors["Y_mean"]) / self.normalization_factors["Y_std"]

        return x, y, X, Y

    def build_design_matrix(self, x, y):
        """Build the design matrix for polynomial regression."""
        num_terms = (self.degree + 1) * (self.degree + 2) // 2  # Number of terms in the polynomial
        A = np.zeros((len(x), num_terms))

        idx = 0
        for i in range(self.degree + 1):
            for j in range(self.degree + 1 - i):
                A[:, idx] = (x ** i) * (y ** j)
                idx += 1

        self.design_matrix = A
        return A

    def regress_polynomial(self):
        """Perform polynomial regression using the design matrix."""
        x, y, X, Y = self.normalize_data()
        A = self.build_design_matrix(x, y)

        # Solve for the coefficients
        coeffs_X, _, _, _ = np.linalg.lstsq(A, X, rcond=None)
        coeffs_Y, _, _, _ = np.linalg.lstsq(A, Y, rcond=None)

        return coeffs_X, coeffs_Y

    def evaluate(self, coeffs_X, coeffs_Y, points):
        """
        Evaluate the polynomial at given points.

        Parameters:
        coeffs_X, coeffs_Y (np.array): Polynomial coefficients.
        points (list of dict): List of points with 'x' and 'y'.

        Returns:
        evaluated_X, evaluated_Y (np.array): Evaluated X and Y values.
        """
        x = np.array([point['x'] for point in points])
        y = np.array([point['y'] for point in points])

        # Normalize inputs
        x = (x - self.normalization_factors["x_mean"]) / self.normalization_factors["x_std"]
        y = (y - self.normalization_factors["y_mean"]) / self.normalization_factors["y_std"]

        A = self.build_design_matrix(x, y)

        evaluated_X = A @ coeffs_X
        evaluated_Y = A @ coeffs_Y

        # Denormalize outputs
        evaluated_X = (evaluated_X * self.normalization_factors["X_std"]) + self.normalization_factors["X_mean"]
        evaluated_Y = (evaluated_Y * self.normalization_factors["Y_std"]) + self.normalization_factors["Y_mean"]

        return evaluated_X, evaluated_Y

    def rmse(self, predicted_X, predicted_Y, actual_X, actual_Y):
        """Calculate the RMSE."""
        rmse_X = np.sqrt(np.mean((predicted_X - actual_X) ** 2))
        rmse_Y = np.sqrt(np.mean((predicted_Y - actual_Y) ** 2))
        return rmse_X, rmse_Y
