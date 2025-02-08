import pickle
import numpy as np
class Project:
    _instance = None

    @staticmethod
    def get_instance():
        if Project._instance is None:
            Project._instance = Project()
        return Project._instance

    def __init__(self):
        if Project._instance is not None:
            raise Exception("This class is a singleton!")
        self.forward_coeffs = None
        self.backward_coeffs = None
        self.gcp_points = None
        self.icp_points = None
        self.degree = None
        self.image_path = None
        self.normalization_factor = None
        self.dx = None
        self.dy = None
        self.dX = None
        self.dY = None
        self.predicted_x = None
        self.predicted_X = None 
        self.predicted_Y = None
        self.predicted_y = None
        self.actual_X = None
        self.actual_Y = None
        self.actual_x = None
        self.actual_y = None
        self.rmse_X_forward = None
        self.rmse_Y_forward = None
        self.rmse_X_backward = None
        self.rmse_Y_backward = None
        
    def set_predicted(self, X, x, Y, y):
        self.predicted_x = x
        self.predicted_X = X 
        self.predicted_Y = Y
        self.predicted_y = y
    
    def get_predicted(self):
        return (self.predicted_x, self.predicted_y), (self.predicted_X, self.predicted_Y)

    def set_gt_icp(self, actual_X, actual_Y, actual_x, actual_y):
        self.actual_X = actual_X
        self.actual_Y = actual_Y
        self.actual_x = actual_x
        self.actual_y = actual_y
    
    def set_displacement_values(self, dx, dy, dX, dY):
        """
        Set displacement values for GCPs.
        """
        self.dx = np.array(dx)
        self.dy = np.array(dy)
        self.dX = np.array(dX)
        self.dY = np.array(dY)

    def save_to_file(self, filename):
        """
        Save the current state of the Project instance to a file using pickle.
        """
        with open(filename, 'wb') as file:
            pickle.dump(self.__dict__, file)

    def load_from_file(self, filename):
        """
        Load the state of the Project instance from a file using pickle.
        """
        with open(filename, 'rb') as file:
            data = pickle.load(file)
            self.__dict__.update(data)
