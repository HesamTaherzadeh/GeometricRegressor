# **Geospatial Polynomial Transformation Toolbox**

## **Overview**
The **Geospatial Polynomial Transformation Toolbox** provides a robust framework for **geospatial image transformation, resampling, and interpolation** using **polynomial regression**. This toolbox enables users to perform **coordinate transformations**, **pointwise corrections**, **resampling**, and **piecewise regression** to improve georeferencing accuracy.

---

## **Dependencies & Installation**

### **1. Clone the Repository**
To ensure all required submodules (including the **Genetic Algorithm (GA) regression module**) are included, clone the repository **recursively**:

```bash
git clone --recursive https://github.com/HesamTaherzadeh/GeometricRegressor.git
cd GeometricRegressor
```

### **2. Install Python Dependencies**
Ensure that the required Python packages are installed:

```bash
pip install numpy matplotlib PySide6
```

---

### **3. Install and Build the Genetic Algorithm (GA) Submodule**
The Genetic Algorithm (GA) module is located in `thirdparty/GA`. Navigate to the submodule and follow the build instructions:

```bash
cd thirdparty/GA
mkdir build && cd build
cmake ..
make
```

After building, you can run the GA binary as follows:

```bash
./genetic_algorithm ../config/cfg.yaml
```

To run tests for GA:

```bash
./runTests
```

#### **Python Setup for GA**
To use the **Python bindings** for the Genetic Algorithm, follow these steps:

```bash
cd ..
python3 -m pip install pybind11 numpy
python3 setup.py build
python3 setup.py install --user
```

To verify the installation:

```python
import genetic_algorithm as ga
print("Python bindings successfully imported!")
```

---

## **Key Features**
- **Polynomial Regression** for **forward and backward** coordinate transformation.
- **Pointwise Interpolation** using **Multiquadratic (MQ)** and **Local Distance Weighted (LDW)** methods.
- **Resampling** with **bilinear interpolation** and **multithreading** for efficient processing.
- **Piecewise Regression**, enabling **adaptive transformations** for different spatial regions.
- **Graphical User Interface (GUI)** for **interactive visualization** of transformation results.

---

## **Modules & Documentation**
Each algorithm is documented in its respective file:

1. **[Polynomial Regression](docs/regress.md)**  
   - Implements **forward and backward transformations** using **polynomial equations**.  
   - Forms the basis for all other modules.

2. **[Pointwise Interpolation](docs/pointwise.md)**  
   - Computes **localized displacement corrections** using **MQ** and **LDW interpolation**.  
   - Enhances **ICP coordinate accuracy**.

3. **[Resampling](docs/resampling.md)**  
   - Performs **image resampling** with **polynomial transformations**.  
   - Uses **multithreading** for optimal performance.

4. **[Piecewise Regression](docs/piecewise.md)**  
   - Allows **dataset splitting** into **multiple regions** based on user-defined lines.  
   - Conducts **localized polynomial regression** for improved accuracy.
5. **[UI Tutorial](docs/ui.md)**
   - A set of **GIFs** to showcase the power of the code 

---

## **Usage**
1. **Load an Image and Ground Control Points (GCPs).**
2. **Perform Polynomial Regression** to compute transformations.
3. **Apply Pointwise Correction** to refine the transformation accuracy.
4. **Resample the Image** to generate a **transformed grid**.
5. **Use Piecewise Regression** to analyze spatial variations.
6. **Visualize results interactively** with **quiver plots**.
