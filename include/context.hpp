#pragma once
#include "model.hpp"

class ModelContext {
public:
    ModelContext() = default;
    
    void setModel(std::shared_ptr<AbstractModel> model) {
        currentModel = model;
    }

    Status constructA(const Eigen::VectorXd& X, const Eigen::VectorXd& Y) {
        if (!currentModel) {
            return Status::Error(StatusCode::NULL_POINTER, "No model set");
        }
        return currentModel->constructA(X, Y);
    }

    Status solve(const Eigen::MatrixXd& A, const Eigen::VectorXd& Y) {
        if (!currentModel) {
            return Status::Error(StatusCode::NULL_POINTER, "No model set");
        }
        return currentModel->solve(A, Y);
    }

    Status inference(const Eigen::MatrixXd& A) {
        if (!currentModel) {
            return Status::Error(StatusCode::NULL_POINTER, "No model set");
        }
        return currentModel->inference(A);
    }

private:
    std::shared_ptr<AbstractModel> currentModel;  
};