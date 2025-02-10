# **Split-Line Regression with Polynomial Transformations**

## **Overview**
This module performs **split-line regression**, dividing **Ground Control Points (GCPs)** and **Independent Check Points (ICPs)** into separate regions based on a **user-defined splitting line**. Each region is then independently transformed using **polynomial regression**, which is detailed in the [Polynomial Regression README](regress.md).

## **Mathematical Formulation**

### **1. Defining the Splitting Line**
The user selects two points `(x₁, y₁)` and `(x₂, y₂)` to define a **splitting line** in image space. The equation of the line is given by:

```math
y = m x + b
```

where:
- The **slope** `m` is computed as:

  ```math
  m = \frac{y_2 - y_1}{x_2 - x_1}
  ```

- The **intercept** `b` is:

  ```math
  b = y_1 - m x_1
  ```

### **2. Classifying Points Based on the Line**
Each **GCP** and **ICP** is classified into one of two regions based on its position relative to the line.

For a given point `(xₚ, yₚ)`, the **signed distance** from the line is computed as:

```math
d = (x_p - x_1) (y_2 - y_1) - (y_p - y_1) (x_2 - x_1)
```

- If `d > 0`, the point is on the **left side**.
- If `d < 0`, the point is on the **right side**.
- If `d = 0`, the point lies **exactly on the line**.

The dataset is **split into two sets** based on this classification.

---

### **3. Polynomial Regression in Each Region**
For each **region**, a separate **polynomial regression model** is fitted. The transformation functions for **forward and backward mapping** are:

```math
X = \sum_{i=0}^{d} \sum_{j=0}^{d-i} c_{ij} x^i y^j
```

```math
Y = \sum_{i=0}^{d} \sum_{j=0}^{d-i} c'_{ij} x^i y^j
```

where:
- `d` is the **polynomial degree**.
- `c_{ij}, c'_{ij}` are the **polynomial coefficients** estimated separately for **each side of the split**.

The polynomial regression method used here follows the detailed mathematical formulation described in the **[Polynomial Regression README](regress.md)**.

---

### **4. Evaluating Accuracy Using RMSE**
To assess transformation accuracy, the **Root Mean Square Error (RMSE)** is computed separately for each **region** using the corresponding ICPs:

```math
\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^{N} (y_i - \hat{y}_i)^2}
```

where:
- `yᵢ` represents the **true coordinate values**.
- `ŷᵢ` represents the **predicted values from polynomial regression**.

The **total RMSE** for each region is reported separately, allowing a comparison of transformation accuracy.

---

### **5. Extending to Multiple Splitting Lines**
If multiple **splitting lines** are drawn, each ICP/GCP is classified into **multiple sub-regions** using **recursive classification**:

1. Each line divides the space into two sub-regions.
2. If additional lines exist, each sub-region is further divided.
3. Polynomial regression is performed separately for each **final sub-region**.

For `N` splitting lines, a point belongs to **one of `2^N` possible regions**.

---