import pickle

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

    def save_to_file(self, filename):
        """Save the current state of the Project instance to a file using pickle."""
        with open(filename, 'wb') as file:
            pickle.dump(self.__dict__, file)

    def load_from_file(self, filename):
        """Load the state of the Project instance from a file using pickle."""
        with open(filename, 'rb') as file:
            data = pickle.load(file)
            self.__dict__.update(data)