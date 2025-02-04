import numpy as np

class Pointwise:
    def __init__(self, gcps, icps, dx, dy, dX, dY):
        """
        Initialize the Pointwise class.
        :param gcps: List of GCP points [{'x': ..., 'y': ..., 'X': ..., 'Y': ..., 'Z': ...}, ...]
        :param icps: List of ICP points [{'x': ..., 'y': ..., 'X': ..., 'Y': ...}, ...]
        :param dx: List of dx values corresponding to GCPs
        :param dy: List of dy values corresponding to GCPs
        :param dX: List of dX values corresponding to GCPs
        :param dY: List of dY values corresponding to GCPs
        """
        self.gcps = gcps
        self.icps = icps
        self.dx = np.array(dx)
        self.dy = np.array(dy)
        self.dX = np.array(dX)
        self.dY = np.array(dY)
        self.gcp_coords = np.array([[p['x'], p['y']] for p in gcps])
        self.icp_coords = np.array([[p['x'], p['y']] for p in icps])
    
    def compute_distance_matrix(self, src, dest):
        """
        Compute the pairwise Euclidean distance matrix.
        :param src: Source points (N x 2 array)
        :param dest: Destination points (M x 2 array)
        :return: Distance matrix (N x M)
        """
        dist_matrix = np.linalg.norm(src[:, None, :] - dest[None, :, :], axis=2)
        return dist_matrix

    def multiquadratic(self):
        """
        Perform the multiquadratic interpolation to estimate dx, dy for ICPs.
        """
        dist_matrix = self.compute_distance_matrix(self.gcp_coords, self.gcp_coords)
        
        coeffs_x = np.linalg.solve(dist_matrix, self.dx)
        coeffs_y = np.linalg.solve(dist_matrix, self.dy)
        
        icp_dist_matrix = self.compute_distance_matrix(self.icp_coords, self.gcp_coords)
        
        icp_dx = icp_dist_matrix @ coeffs_x
        icp_dy = icp_dist_matrix @ coeffs_y
        
        return icp_dx, icp_dy

    def find_four_closest(self, icp, r):
        """
        Find the 4 closest GCPs that are in different quadrants around an ICP.
        :param icp: A single ICP point (x, y)
        :param r: Norm order for distance calculation
        :return: 4 selected GCPs and their dx, dy values
        """
        distances = np.linalg.norm(self.gcp_coords - icp, axis=1, ord=r)
        quadrants = [[], [], [], []]
        
        for i, (gcp, dist) in enumerate(zip(self.gcp_coords, distances)):
            if gcp[0] >= icp[0] and gcp[1] >= icp[1]:
                quadrants[0].append((i, dist))  # Top right
            elif gcp[0] < icp[0] and gcp[1] >= icp[1]:
                quadrants[1].append((i, dist))  # Top left
            elif gcp[0] < icp[0] and gcp[1] < icp[1]:
                quadrants[2].append((i, dist))  # Bottom left
            elif gcp[0] >= icp[0] and gcp[1] < icp[1]:
                quadrants[3].append((i, dist))  # Bottom right
        
        selected = []
        for quad in quadrants:
            if quad:
                quad.sort(key=lambda x: x[1])
                selected.append(quad[0][0])
        
        if len(selected) < 4:
            selected = sorted(range(len(distances)), key=lambda i: distances[i])[:4]
        
        return selected
    
    def LDW(self, n, r):
        """
        Perform Local Distance Weighted interpolation.
        :param n: Number of closest points to use
        :param r: Norm order for distance calculation
        :return: Interpolated dx, dy for each ICP
        """
        icp_dx = []
        icp_dy = []
        
        for icp in self.icp_coords:
            indices = self.find_four_closest(icp, r)
            selected_gcps = self.gcp_coords[indices]
            selected_dx = self.dx[indices]
            selected_dy = self.dy[indices]
            
            distances = np.linalg.norm(selected_gcps - icp, axis=1, ord=r)
            weights = 1 / (distances + 1e-10)  # Avoid division by zero
            
            weighted_dx = np.sum(weights * selected_dx) / np.sum(weights)
            weighted_dy = np.sum(weights * selected_dy) / np.sum(weights)
            
            icp_dx.append(weighted_dx)
            icp_dy.append(weighted_dy)
        
        return np.array(icp_dx), np.array(icp_dy)
