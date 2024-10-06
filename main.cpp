#include <iostream>
#include "conformal.hpp"


int main() {
    Conformal model;
    Eigen::VectorXd X(3);
    Eigen::VectorXd Y(3);

    X << 1.0, 2.0, 3.0;
    Y << 4.0, 5.0, 6.0;

    // Construct the A matrix
    Status status = model.constructA(X, Y);
    if (!status) {
        std::cerr << "Error constructing A: " << status.getMessage() << std::endl;
        return 1;
    }

    // Solve for coefficients
    status = model.solve(*(model.A), Y);
    if (!status) {
        std::cerr << "Error solving for coefficients: " << status.getMessage() << std::endl;
        return 1;
    }

    // Perform inference
    status = model.inference(*(model.A), X);
    if (!status) {
        std::cerr << "Error performing inference: " << status.getMessage() << std::endl;
        return 1;
    }

    std::cout << "Coefficients:\n" << *(model.coefficients) << std::endl;
    std::cout << "Inference Result:\n" << *(model.results) << std::endl;

    return 0;
}
