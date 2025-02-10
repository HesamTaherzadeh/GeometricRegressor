# **Pointwise Displacement Estimation Using Interpolation**

## **Overview**
This script implements **pointwise displacement estimation** using **interpolation techniques** to refine transformations between **Ground Control Points (GCPs)** and **Independent Check Points (ICPs)**. Two interpolation methods are available:
- **Multiquadratic Interpolation (MQ)**
- **Local Distance Weighted Interpolation (LDW)**

These methods estimate residual displacements `dx, dy, dX, dY` for ICPs based on the surrounding GCPs.

---

## **Mathematical Formulation**

### **1. Euclidean Distance Matrix**
The **pairwise Euclidean distance** between all points is computed to establish relationships between GCPs and ICPs. The **distance matrix `D`** is defined as:

```math
D_{ij} = \sqrt{(x_i - x_j)^2 + (y_i - y_j)^2}
```

For a given set of `N` GCPs and `M` ICPs, the **distance matrix** takes the form:

```math
D =
\begin{bmatrix}
d_{11} & d_{12} & \dots  & d_{1N} \\
d_{21} & d_{22} & \dots  & d_{2N} \\
\vdots & \vdots & \ddots & \vdots \\
d_{M1} & d_{M2} & \dots  & d_{MN}
\end{bmatrix}
```

where each element `d_{ij}` represents the Euclidean distance between the **i-th ICP** and the **j-th GCP**.

---

### **2. Multiquadratic Interpolation (MQ)**
Multiquadratic interpolation is a **global interpolation method** that uses radial basis functions based on distances.

The **displacement function** is assumed to be a linear combination of radial basis functions:

```math
dx = A \cdot c_{dx}, \quad dy = A \cdot c_{dy}, \quad dX = A \cdot c_{dX}, \quad dY = A \cdot c_{dY}
```

where:
- `A` is the distance matrix computed between GCPs.
- `c_{dx}, c_{dy}, c_{dX}, c_{dY}` are unknown coefficients.

The coefficients are obtained by solving:

```math
A \cdot c = b
```

where:
- `b` is the vector of known residual displacements from GCPs.

For an ICP, the estimated displacement is:

```math
\hat{dx} = A' \cdot c_{dx}, \quad \hat{dy} = A' \cdot c_{dy}, \quad \hat{dX} = A' \cdot c_{dX}, \quad \hat{dY} = A' \cdot c_{dY}
```

where `A'` is the **distance matrix between ICPs and GCPs**.

---

### **3. Local Distance Weighted Interpolation (LDW)**
LDW selects the **four closest GCPs** in different quadrants and assigns weights based on inverse distance.

#### **Finding the Four Closest GCPs**
Each ICP is analyzed based on **quadrants**:

### **Quadrant Selection Conditions**
To identify the four closest **Ground Control Points (GCPs)** surrounding an **Independent Check Point (ICP)**, we categorize GCPs into four quadrants based on their coordinates:

#### **Mathematical Formulation for Quadrant Assignment**
Each **GCP `(x_g, y_g)`** relative to an **ICP `(x_{icp}, y_{icp})`** is classified into one of four quadrants:

- **First Quadrant (Top-Right):**
  
  ```math
  x_g \geq x_{icp}, \quad y_g \geq y_{icp}
  ```

- **Second Quadrant (Top-Left):**
  
  ```math
  x_g < x_{icp}, \quad y_g \geq y_{icp}
  ```

- **Third Quadrant (Bottom-Left):**
  
  ```math
  x_g < x_{icp}, \quad y_g < y_{icp}
  ```

- **Fourth Quadrant (Bottom-Right):**
  
  ```math
  x_g \geq x_{icp}, \quad y_g < y_{icp}
  ```

Once classified, the closest **one GCP per quadrant** is selected based on the **Euclidean distance**:

```math
D_i = \sqrt{(x_g - x_{icp})^2 + (y_g - y_{icp})^2}
```

If fewer than four quadrants contain GCPs, the remaining closest GCPs are chosen to ensure at least four points contribute to the interpolation.

#### **Weight Calculation**
For each **selected** GCP, the weight is computed as:

```math
w_i = \frac{1}{D_i + \epsilon}
```

where:
- `D_i` is the distance from the ICP to the `i-th` GCP.
- `ε` is a small constant to prevent division by zero.

The interpolated displacement is computed as:

```math
\hat{dx} = \frac{\sum w_i \cdot dx_i}{\sum w_i}, \quad \hat{dy} = \frac{\sum w_i \cdot dy_i}{\sum w_i}
```

```math
\hat{dX} = \frac{\sum w_i \cdot dX_i}{\sum w_i}, \quad \hat{dY} = \frac{\sum w_i \cdot dY_i}{\sum w_i}
```

where:
- `dx_i, dy_i, dX_i, dY_i` are displacements of the selected GCPs.

---

# **Refinement of Regressed Coordinates Using Pointwise Displacement Interpolation**

## **Mathematical Formulation**

After performing **polynomial regression**, we obtain an initial estimate of the transformed coordinates:

```math
\hat{x} = f(X, Y), \quad \hat{y} = g(X, Y)
```

```math
\hat{X} = f^{-1}(x, y), \quad \hat{Y} = g^{-1}(x, y)
```

where:
- `(x̂, ŷ)` are the **predicted image coordinates** from real-world points `(X, Y)`.
- `(X̂, Ŷ)` are the **predicted real-world coordinates** from image points `(x, y)`.

However, these predictions may contain errors due to **model approximation**. To refine them, we apply **pointwise correction displacements** obtained via **interpolation methods**:

```math
dx = h(x, y), \quad dy = k(x, y)
```

```math
dX = h'(X, Y), \quad dY = k'(X, Y)
```

where:
- `dx, dy` are residual corrections in image space.
- `dX, dY` are residual corrections in real-world space.

---

## **Final Refinement of Coordinates**
To obtain the final, corrected coordinates, we apply the interpolated displacements:

```math
x_{\text{final}} = \hat{x} + dx, \quad y_{\text{final}} = \hat{y} + dy
```

```math
X_{\text{final}} = \hat{X} + dX, \quad Y_{\text{final}} = \hat{Y} + dY
```

---

## **Error Measurement**
The improvement in accuracy is measured using **Root Mean Square Error (RMSE)**:

```math
\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^{N} (y_i - \hat{y}_i)^2}
```

where:
- `y_i` represents the true coordinate values.
- `ŷ_i` represents the refined estimates.

A lower RMSE after applying pointwise interpolation indicates a **more precise transformation**. 🚀