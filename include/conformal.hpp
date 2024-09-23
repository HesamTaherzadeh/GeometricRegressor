#include "model.hpp"

class Conformal : public AbstractModel {
public:
    Eigen::MatrixXd& constructA(const Eigen::VectorXd& X, const Eigen::VectorXd& Y) override;

    Eigen::VectorXd& solve(const Eigen::MatrixXd& A, const Eigen::VectorXd& Y) override;

    Eigen::VectorXd& inference(const Eigen::MatrixXd& A, const Eigen::VectorXd& X) override;
};