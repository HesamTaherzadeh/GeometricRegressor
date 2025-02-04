import numpy as np

class Polynomial:
    def __init__(self, gcp_points, degree):
        self.gcp_points = gcp_points
        self.degree = degree
        self.normalization_factors = None
        self.design_matrix_forward = None
        self.design_matrix_backward = None

    def normalize_data(self):
        """
        Normalize the GCP data and keep normalization factors.
        """
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
        """
        Build the design matrix for polynomial regression.
        """
        num_terms = (self.degree + 1) * (self.degree + 2) // 2
        A = np.zeros((len(x), num_terms))

        idx = 0
        for i in range(self.degree + 1):
            for j in range(self.degree + 1 - i):
                A[:, idx] = (x ** i) * (y ** j)
                idx += 1

        return A

    def regress_polynomial(self):
        """
        Perform polynomial regression for both forward and backward transformations.
        """
        x, y, X, Y = self.normalize_data()

        A_forward = self.build_design_matrix(X, Y)
        self.design_matrix_forward = A_forward

        coeffs_x_forward, _, _, _ = np.linalg.lstsq(A_forward, x, rcond=None)
        coeffs_y_forward, _, _, _ = np.linalg.lstsq(A_forward, y, rcond=None)

        A_backward = self.build_design_matrix(x, y)
        self.design_matrix_backward = A_backward

        coeffs_X_backward, _, _, _ = np.linalg.lstsq(A_backward, X, rcond=None)
        coeffs_Y_backward, _, _, _ = np.linalg.lstsq(A_backward, Y, rcond=None)

        return coeffs_x_forward, coeffs_y_forward, coeffs_X_backward, coeffs_Y_backward

    def evaluate(self, coeffs, points, forward=True):
        """
        Evaluate the polynomial at given points.
        """
        coeffs_1, coeffs_2 = coeffs

        if forward:
            x = np.array([point['X'] for point in points])
            y = np.array([point['Y'] for point in points])
            x = (x - self.normalization_factors["X_mean"]) / self.normalization_factors["X_std"]
            y = (y - self.normalization_factors["Y_mean"]) / self.normalization_factors["Y_std"]
        else:
            x = np.array([point['x'] for point in points])
            y = np.array([point['y'] for point in points])
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


    def rmse(self, predicted_1, predicted_2, actual_1, actual_2):
        """
        Calculate RMSE.
        """
        rmse_1 = np.sqrt(np.mean((predicted_1 - actual_1) ** 2))
        rmse_2 = np.sqrt(np.mean((predicted_2 - actual_2) ** 2))
        return rmse_1, rmse_2
