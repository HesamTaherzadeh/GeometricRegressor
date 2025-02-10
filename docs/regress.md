# **Polynomial Regression for Ground Control Points (GCP)**

## **Overview**
This script implements **polynomial regression** to transform **Ground Control Points (GCPs)** between image and real-world coordinates. It performs **bidirectional mapping**:
- **Forward Transformation:** Maps real-world coordinates \((X, Y)\) to image coordinates \((x, y)\).
- **Backward Transformation:** Maps image coordinates \((x, y)\) to real-world coordinates \((X, Y)\).

The model utilizes polynomial regression of **degree \(d\)** and normalizes data before fitting.

---

## **Mathematical Formulation**

### **1. Normalization**
To improve numerical stability, data is normalized using **mean** and **standard deviation**:

```math
\hat{x} = \frac{x - \mu_x}{\sigma_x}, \quad \hat{y} = \frac{y - \mu_y}{\sigma_y}
```

```math
\hat{X} = \frac{X - \mu_X}{\sigma_X}, \quad \hat{Y} = \frac{Y - \mu_Y}{\sigma_Y}
```

where:
- \( \mu \) is the mean.
- \( \sigma \) is the standard deviation.

---

### **2. Polynomial Basis Expansion**
The **design matrix \(A\)** consists of polynomial basis functions up to a given degree \(d\):

```math
A[i, j] = X^p Y^q, \quad \text{where} \quad p+q \leq d
```

The number of terms in the polynomial:

```math
N = \frac{(d+1)(d+2)}{2}
```

For **degree \(d=2\)**, the design matrix takes the form:

```math
A =
\begin{bmatrix}
1 & X & Y & X^2 & XY & Y^2
\end{bmatrix}
```

### **3. Polynomial Regression**
The transformation is modeled as:

```math
x = A \cdot c_x, \quad y = A \cdot c_y
```

```math
X = A' \cdot c_X, \quad Y = A' \cdot c_Y
```

where:
- \( A \) and \( A' \) are the design matrices.
- \( c_x, c_y, c_X, c_Y \) are the regression coefficients computed using **least squares estimation**:

```math
c = (A^T A)^{-1} A^T b
```

---

### **4. Evaluation**
Given a new input \((X, Y)\) or \((x, y)\), the estimated output is:

```math
\hat{x} = A \cdot c_x, \quad \hat{y} = A \cdot c_y
```

```math
\hat{X} = A' \cdot c_X, \quad \hat{Y} = A' \cdot c_Y
```

Denormalization is applied to restore original values:

```math
x = \hat{x} \cdot \sigma_x + \mu_x, \quad y = \hat{y} \cdot \sigma_y + \mu_y
```

```math
X = \hat{X} \cdot \sigma_X + \mu_X, \quad Y = \hat{Y} \cdot \sigma_Y + \mu_Y
```

---

### **5. Root Mean Square Error (RMSE)**
The error is measured using **Root Mean Square Error (RMSE)**:

```math
\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^{N} (y_i - \hat{y}_i)^2}
```

where:
- \( y_i \) is the actual value.
- \( \hat{y}_i \) is the predicted value.

---
