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
        self.gcp_coords_xy = np.array([[p['x'], p['y']] for p in gcps])
        self.gcp_coords_XY = np.array([[p['X'], p['Y']] for p in gcps])
        self.icp_coords_xy = np.array([[p['x'], p['y']] for p in icps])
        self.icp_coords_XY = np.array([[p['X'], p['Y']] for p in icps])
    
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
        Perform the multiquadratic interpolation to estimate dx, dy, dX, dY for ICPs.
        """
        dist_matrix_xy = self.compute_distance_matrix(self.gcp_coords_xy, self.gcp_coords_xy)
        dist_matrix_XY = self.compute_distance_matrix(self.gcp_coords_XY, self.gcp_coords_XY)

        coeffs_dx = np.linalg.solve(dist_matrix_xy, self.dx)
        coeffs_dy = np.linalg.solve(dist_matrix_xy, self.dy)
        coeffs_dX = np.linalg.solve(dist_matrix_XY, self.dX)
        coeffs_dY = np.linalg.solve(dist_matrix_XY, self.dY)
        
        icp_dist_matrix_xy = self.compute_distance_matrix(self.icp_coords_xy, self.gcp_coords_xy)
        icp_dist_matrix_XY = self.compute_distance_matrix(self.icp_coords_XY, self.gcp_coords_XY)
        print(self.icp_coords_xy.shape, icp_dist_matrix_xy.shape, icp_dist_matrix_xy.shape)

        icp_dx = icp_dist_matrix_xy @ coeffs_dx
        icp_dy = icp_dist_matrix_xy @ coeffs_dy
        icp_dX = icp_dist_matrix_XY @ coeffs_dX
        icp_dY = icp_dist_matrix_XY @ coeffs_dY
        
        return icp_dx, icp_dy, icp_dX, icp_dY

    def find_four_closest(self, icp, r):
        """
        Find the 4 closest GCPs that are in different quadrants around an ICP.
        :param icp: A single ICP point (x, y)
        :param r: Norm order for distance calculation
        :return: 4 selected GCPs and their dx, dy, dX, dY values
        """
        distances = np.linalg.norm(self.gcp_coords_xy - icp, axis=1, ord=r)
        quadrants = [[], [], [], []]
        
        for i, (gcp, dist) in enumerate(zip(self.gcp_coords_xy, distances)):
            if gcp[0] >= icp[0] and gcp[1] >= icp[1]:
                quadrants[0].append((i, dist)) 
            elif gcp[0] < icp[0] and gcp[1] >= icp[1]:
                quadrants[1].append((i, dist)) 
            elif gcp[0] < icp[0] and gcp[1] < icp[1]:
                quadrants[2].append((i, dist))  
            elif gcp[0] >= icp[0] and gcp[1] < icp[1]:
                quadrants[3].append((i, dist))  
        
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
        :return: Interpolated dx, dy, dX, dY for each ICP
        """
        icp_dx = []
        icp_dy = []
        icp_dX = []
        icp_dY = []
        
        for icp in self.icp_coords_xy:
            indices = self.find_four_closest(icp, r)
            selected_gcps = self.gcp_coords_xy[indices]
            selected_dx = self.dx[indices]
            selected_dy = self.dy[indices]
            selected_dX = self.dX[indices]
            selected_dY = self.dY[indices]
            
            distances = np.linalg.norm(selected_gcps - icp, axis=1, ord=r)
            weights = 1 / (distances + 1e-10)  # Avoid division by zero
            
            weighted_dx = np.sum(weights * selected_dx) / np.sum(weights)
            weighted_dy = np.sum(weights * selected_dy) / np.sum(weights)
            weighted_dX = np.sum(weights * selected_dX) / np.sum(weights)
            weighted_dY = np.sum(weights * selected_dY) / np.sum(weights)
            
            icp_dx.append(weighted_dx)
            icp_dy.append(weighted_dy)
            icp_dX.append(weighted_dX)
            icp_dY.append(weighted_dY)
        
        return np.array(icp_dx), np.array(icp_dy), np.array(icp_dX), np.array(icp_dY)
