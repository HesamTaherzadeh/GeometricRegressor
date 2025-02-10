# **Resampling with Polynomial Transformations and Multithreading**

## **Overview**
This module performs **image resampling** using **polynomial regression-based transformations** while leveraging **multithreading** for efficiency. The transformation process is executed in the background to ensure smooth execution without freezing the user interface.

## **Mathematical Formulation**

### **1. Polynomial Transformation for Resampling**
Resampling requires **forward and backward transformations** to map **ground coordinates to image space** and vice versa.

The **backward transformation** maps image pixels `(x, y)` to real-world coordinates `(X, Y)`:

```math
X = f(x, y), \quad Y = g(x, y)
```

The **forward transformation** maps real-world coordinates `(X, Y)` back to image space:

```math
x = f^{-1}(X, Y), \quad y = g^{-1}(X, Y)
```

The transformation functions are modeled using **polynomial regression**:

```math
X = \sum_{i=0}^{d} \sum_{j=0}^{d-i} c_{ij} x^i y^j
```

```math
Y = \sum_{i=0}^{d} \sum_{j=0}^{d-i} c'_{ij} x^i y^j
```

where:
- `d` is the **degree** of the polynomial.
- `c_{ij}, c'_{ij}` are the **polynomial coefficients** estimated from **Ground Control Points (GCPs)**.

---

### **2. Grid Generation for Resampling**
To resample an image, an **output grid** is generated in the **ground coordinate space**. The **bounding box** of the transformed image is computed by transforming the **four corner pixels** using the backward polynomial transformation:

```math
X_{\text{min}}, X_{\text{max}} = \min(X_{\text{corners}}), \max(X_{\text{corners}})
```

```math
Y_{\text{min}}, Y_{\text{max}} = \min(Y_{\text{corners}}), \max(Y_{\text{corners}})
```

A uniform grid of ground coordinates `(X, Y)` is then created with a specified **resampling step**:

```math
X_{\text{grid}} = X_{\text{min}} + k \cdot \text{step}, \quad k = 0, 1, \dots
```

```math
Y_{\text{grid}} = Y_{\text{max}} - k \cdot \text{step}, \quad k = 0, 1, \dots
```

where:
- **step** controls the resolution of the resampled image.

Each grid point `(X, Y)` is then mapped back to the original image space `(x, y)` using the **forward polynomial transformation**.

---

### **3. Bilinear Interpolation for Intensity Estimation**
Once the transformed pixel positions `(x, y)` are obtained, **bilinear interpolation** is used to estimate intensity values.

For a given point `(x, y)`, the four neighboring pixels are:

- **Top-left:** `(x_0, y_0)`
- **Top-right:** `(x_1, y_0)`
- **Bottom-left:** `(x_0, y_1)`
- **Bottom-right:** `(x_1, y_1)`

The pixel intensity is computed using:

```math
I(x, y) = (1 - dx)(1 - dy) I(x_0, y_0) + dx (1 - dy) I(x_1, y_0) 
        + (1 - dx) dy I(x_0, y_1) + dx dy I(x_1, y_1)
```

where:

```math
dx = x - x_0, \quad dy = y - y_0
```

This ensures smooth interpolation of pixel intensities.

---

### **4. Multithreading for Efficient Computation**
To improve performance, the **resampling process is parallelized**. The image is divided into **chunks**, and each chunk is processed in parallel using a **worker thread**.

#### **Thread Execution Process**
1. **Initialize Worker Thread**:
   - The **worker thread** receives the **image, GCPs, ICPs, polynomial degree, and resampling step**.
   - A `cancel` flag is set to allow **early termination**.

2. **Chunk Processing**:
   - The resampling process iterates over the **output grid** row by row.
   - Each **chunk of rows** is processed independently.
   - The `progress` is updated after each chunk.

3. **Thread-Safe Execution**:
   - The `cancel` flag is checked before processing each chunk.
   - If `cancel` is triggered, the process **stops immediately**.
