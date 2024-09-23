#include <iostream>
#include "conformal.hpp"


int main() {
    Eigen::VectorXd X(3), Y(3), target_Y(6);
    X << 1.0, 2.0, 3.0;
    Y << 4.0, 5.0, 6.0;
    target_Y << 4.0, 5.0, 6.0, 7.0, 8.0, 9.0;

    Conformal conformalModel;
    Eigen::MatrixXd A = conformalModel.constructA(X, Y);

    Eigen::VectorXd coefficients = conformalModel.solve(A, target_Y);
    std::cout << "Conformal Coefficients: \n" << coefficients << std::endl;

    Eigen::VectorXd inferred_Y = conformalModel.inference(A, coefficients);
    std::cout << "Inferred Y (using the coefficients): \n" << inferred_Y << std::endl;

    return 0;
}