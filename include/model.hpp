#include <iostream>
#include <Eigen/Dense>

class AbstractModel {
public:
    AbstractModel() = default;

    virtual Eigen::VectorXd& solve(const Eigen::MatrixXd& A, const Eigen::VectorXd& Y);

    virtual Eigen::MatrixXd& constructA(const Eigen::VectorXd& X, const Eigen::VectorXd& Y) = 0;

    virtual Eigen::VectorXd& inference(const Eigen::MatrixXd& A, const Eigen::VectorXd& X) = 0;

    virtual ~AbstractModel() = default;

protected:
    Eigen::VectorXd coefficients, results;

    Eigen::MatrixXd A;

private:
};

