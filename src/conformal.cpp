#include "conformal.hpp"

Eigen::MatrixXd& Conformal::constructA(const Eigen::VectorXd &X, const Eigen::VectorXd &Y)
{
    int n = X.size();
    A.resize(2 * n, 4);

    for (int i = 0; i < n; ++i) {
        A(2 * i, 0) = X(i);
        A(2 * i, 1) = -Y(i);
        A(2 * i, 2) = 1.0;
        A(2 * i, 3) = 0.0;

        A(2 * i + 1, 0) = Y(i);
        A(2 * i + 1, 1) = X(i);
        A(2 * i + 1, 2) = 0.0;
        A(2 * i + 1, 3) = 1.0;
    }

    return A;
}

Eigen::VectorXd& Conformal::solve(const Eigen::MatrixXd &A, const Eigen::VectorXd &Y)
{
        coefficients = A.bdcSvd(Eigen::ComputeThinU | Eigen::ComputeThinV).solve(Y);
        return coefficients;
}

Eigen::VectorXd& Conformal::inference(const Eigen::MatrixXd &A, const Eigen::VectorXd &X)
{
    results = A * X;
    return results;
}
