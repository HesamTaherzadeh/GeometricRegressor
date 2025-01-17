import numpy as np
import thirdparty.GA.build.genetic_algorithm as ga
from PySide6.QtWidgets import QDialog, QMessageBox, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout
from core.project import Project

class GARunner:
    """
    Encapsulates the entire workflow for running Genetic Algorithm regressions.
    Provides methods for setting parameters, running the GA, and displaying results.
    """

    def __init__(self, parent):
        """
        Initialize the GARunner with the main window as its parent.
        """
        self.parent = parent
        self.params = {
            "n": 5,
            "m": 5,
            "population_size": 100,
            "generations": 100,
            "mutation_rate": 0.05,
            "tournament_size": 3,
            "patience": 80,
            "coeff_lambda": 1.0,
            "rmse_lambda": 0.1,
        }

    def open_parameter_dialog(self):
        """
        Opens a dialog for setting GA parameters. Updates `self.params` if the user confirms.
        """
        dialog = QDialog(self.parent)
        dialog.setWindowTitle("Genetic Algorithm Parameters")
        dialog.resize(400, 300)

        layout = QVBoxLayout()
        inputs = {}

        # Create input fields for each parameter
        for key, default_val in self.params.items():
            row_layout = QHBoxLayout()
            label = QLabel(f"{key}:")
            edit = QLineEdit(str(default_val))
            inputs[key] = edit
            row_layout.addWidget(label)
            row_layout.addWidget(edit)
            layout.addLayout(row_layout)

        # OK and Cancel buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        dialog.setLayout(layout)

        # Connect signals
        def on_ok():
            try:
                # Parse inputs and update params
                for key, edit in inputs.items():
                    val = edit.text().strip()
                    self.params[key] = float(val) if "." in val or "e" in val.lower() else int(val)
                dialog.accept()
            except ValueError:
                QMessageBox.warning(dialog, "Error", "Invalid input. Please check your values.")
                return

        ok_button.clicked.connect(on_ok)
        cancel_button.clicked.connect(dialog.reject)

        if dialog.exec() == QDialog.Accepted:
            return True  # Parameters successfully updated
        return False  # User canceled

    def run_ga(self):
        """
        Runs four GA regressions using only GCP points from the main toolbox.
        Displays the best coefficients for each equation.
        """
        # Get GCP points from the parent (ToolBoxMainWindow)
        gcp_points = self.parent.get_gcp_points()
        if not gcp_points:
            QMessageBox.warning(self.parent, "Warning", "No GCP points available for GA.")
            return

        # Set random seed
        np.random.seed(42)

        def normalize_data(gcp_points):
            """Normalize the GCP data and keep normalization factors."""
            x = np.array([point['x'] for point in gcp_points])
            y = np.array([point['y'] for point in gcp_points])
            X = np.array([point['X'] for point in gcp_points])
            Y = np.array([point['Y'] for point in gcp_points])

            normalization_factors = {
                "x_mean": x.mean(), "x_std": x.std(),
                "y_mean": y.mean(), "y_std": y.std(),
                "X_mean": X.mean(), "X_std": X.std(),
                "Y_mean": Y.mean(), "Y_std": Y.std(),
            }

            x = (x - normalization_factors["x_mean"]) / normalization_factors["x_std"]
            y = (y - normalization_factors["y_mean"]) / normalization_factors["y_std"]
            X = (X - normalization_factors["X_mean"]) / normalization_factors["X_std"]
            Y = (Y - normalization_factors["Y_mean"]) / normalization_factors["Y_std"]

            return x, y, X, Y, normalization_factors

        def prepare_data(x, y, X, Y, target_key, predictor_keys):
            """
            Prepare X_data (predictor matrix) and Z_data (target vector) from normalized data.

            Args:
                x, y, X, Y (np.array): Normalized coordinate arrays.
                target_key (str): The key for the target variable (e.g., "x", "y", "X", "Y").
                predictor_keys (list of str): The keys for the predictor variables (e.g., ["X", "Y"]).

            Returns:
                tuple: X_data (2D numpy array), Z_data (1D numpy array).
            """
            data_map = {"x": x, "y": y, "X": X, "Y": Y}

            Z_data = data_map[target_key]
            X_data = np.column_stack([data_map[key] for key in predictor_keys])

            return X_data, Z_data

        def run_one_equation(X_data, Z_data, eq_name):
            """Run GA for a single equation and return results."""
            # Create the GeneticAlgorithm instance
            ga_instance = ga.GeneticAlgorithm(
                X_data,
                Z_data,
                self.params["n"],
                self.params["m"],
                self.params["population_size"],
                self.params["generations"],
                self.params["mutation_rate"],
                self.params["tournament_size"],
                self.params["patience"],
                self.params["coeff_lambda"],
                self.params["rmse_lambda"],
            )
            ga_instance.setFileLogPath("/home/hesam/Desktop/Space_models/" + eq_name + ".log")
            ga_instance.run()
            coeffs = ga_instance.get_coefficients()
            print(ga_instance.get_selected_terms())
            intercept = ga_instance.get_intercept()
            return coeffs, intercept

        # Normalize the data
        x, y, X, Y, normalization_factors = normalize_data(gcp_points)

        results = []

        equations = [
            ("x=f(X,Y)", "x", ["X", "Y"]),
            ("y=f(X,Y)", "y", ["X", "Y"]),
            ("X=f(x,y)", "X", ["x", "y"]),
            ("Y=f(x,y)", "Y", ["x", "y"]),
        ]

        project = Project.get_instance()
        project.gcp_points = gcp_points
        project.normalization_factor = normalization_factors

        for eq_name, target_key, predictor_keys in equations:
            X_data, Z_data = prepare_data(x, y, X, Y, target_key, predictor_keys)
            coeffs, intercept = run_one_equation(X_data, Z_data, eq_name)
            results.append((eq_name, coeffs, intercept))

            if "x = f(X, Y)" in eq_name or "y = f(X, Y)" in eq_name:
                project.forward_coeffs = results
            else:
                project.backward_coeffs = results

        # Display results in a QMessageBox
        result_text = "<b>Genetic Algorithm Regression Results:</b><br><br>"
        for eq_name, coeffs, intercept in results:
            result_text += f"<b>{eq_name}</b><br>"
            result_text += f"Coefficients: {coeffs}<br>"
            result_text += f"Intercept: {intercept}<br><br>"

        QMessageBox.information(self.parent, "GA Results", result_text)
