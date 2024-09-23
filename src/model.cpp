#include "model.hpp"

Eigen::VectorXd &AbstractModel::solve(const Eigen::MatrixXd &A, const Eigen::VectorXd &Y)
{
    coefficients = A.bdcSvd(Eigen::ComputeThinU | Eigen::ComputeThinV).solve(Y);
    return coefficients;

}
