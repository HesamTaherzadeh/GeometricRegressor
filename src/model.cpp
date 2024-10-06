#include "model.hpp"

Status AbstractModel::solve(const Eigen::MatrixXd &A, const Eigen::VectorXd &Y)
{
    *coefficients = A.bdcSvd(Eigen::ComputeThinU | Eigen::ComputeThinV).solve(Y);

    return Status::Ok();

}

