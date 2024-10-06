#include <iostream>
#include <Eigen/Dense>
#include <memory>
#include "utils.hpp"


class AbstractModel {
public:
    AbstractModel() = default;
    AbstractModel(AbstractModel&& obj) noexcept 
        : coefficients(std::move(obj.coefficients)),
          results(std::move(obj.results)),
          A(std::move(obj.A)) {
        obj.coefficients = nullptr;
        obj.results = nullptr;
        obj.A = nullptr;
    }

    AbstractModel* ptr(){
        return this;
    }

    virtual Status solve(const Eigen::MatrixXd& A, const Eigen::VectorXd& Y);

    virtual Status constructA(const Eigen::VectorXd& X, const Eigen::VectorXd& Y) = 0;

    virtual Status inference(const Eigen::MatrixXd& A, const Eigen::VectorXd& X) = 0;

    virtual ~AbstractModel() = default;
    
    std::shared_ptr<Eigen::VectorXd> coefficients, results;
    std::shared_ptr<Eigen::MatrixXd> A;

private:
};

