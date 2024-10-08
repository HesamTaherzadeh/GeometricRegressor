#include "conformal.hpp"
#include <Eigen/Dense>
#include <memory>

Status Conformal::constructA(const Eigen::VectorXd &X, const Eigen::VectorXd &Y)
{
    int n = X.size();

    if (X.size() != Y.size()) {
        return Status::Error(StatusCode::INVALID_INPUT, "X and Y must have the same size.");
    }

    if (!A) {
        A = std::make_shared<Eigen::MatrixXd>(2 * n, 4);
    } else {
        A->resize(2 * n, 4);
    }

    for (int i = 0; i < n; ++i) {
        (*A)(2 * i, 0) = X(i);
        (*A)(2 * i, 1) = -Y(i);
        (*A)(2 * i, 2) = 1.0;
        (*A)(2 * i, 3) = 0.0;

        (*A)(2 * i + 1, 0) = Y(i);
        (*A)(2 * i + 1, 1) = X(i);
        (*A)(2 * i + 1, 2) = 0.0;
        (*A)(2 * i + 1, 3) = 1.0;
    }

    return Status::Ok();
}

Status Conformal::solve(const Eigen::MatrixXd &A, const Eigen::VectorXd &Y) {
    if (A.rows() != Y.size()) {
        return Status::Error(StatusCode::INVALID_INPUT, "A rows and Y size must match.");
    }

    Eigen::MatrixXd AtA = A.transpose() * A;
    Eigen::VectorXd AtY = A.transpose() * Y;

    if (!coefficients) {
        coefficients = std::make_shared<Eigen::VectorXd>(AtY.size());
    }

    try {
        *coefficients = AtA.ldlt().solve(AtY);
    } catch (const std::exception& e) {
        return Status::Error(StatusCode::FAILURE, e.what());
    }

    return Status::Ok();
}

Status Conformal::inference(const Eigen::MatrixXd &A)
{
    if (A.cols() != coefficients->size()) {
        return Status::Error(StatusCode::INVALID_INPUT, "A columns and X size must match.");
    }

    if (!results) {
        results = std::make_shared<Eigen::VectorXd>(A.rows());
    }

    try {
        *results = A * *(coefficients);
    } catch (const std::exception& e) {
        return Status::Error(StatusCode::FAILURE, e.what());
    }

    return Status::Ok();
}
