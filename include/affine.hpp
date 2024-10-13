#pragma once

#include <Eigen/Dense>
#include "model.hpp"
#include <memory>

class Affine : public AbstractModel{
public:
    Status constructA(const Eigen::VectorXd &X, const Eigen::VectorXd &Y) override;
    Status solve(const Eigen::MatrixXd &A, const Eigen::VectorXd &Y) override;
    Status inference(const Eigen::MatrixXd &A) override;
};