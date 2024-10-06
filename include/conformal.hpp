#include <Eigen/Dense>
#include <memory>
#include "model.hpp"
#include "utils.hpp"  // Assuming Status is defined in utils.hpp

/**
 * @class Conformal
 * 
 * @brief The model for Conformal 2D-2D transformation
 * 
 * @note This class is derived from the AbstractModel class
 */
class Conformal : public AbstractModel {
public:
    /**
     * @brief Construction of A (jacobian) matrix based on observation vectors 
     * 
     * @param X The X vector 
     * @param Y The Y vector
     * @return Status The status of the operation
     */
    Status constructA(const Eigen::VectorXd& X, const Eigen::VectorXd& Y) override;

    /**
     * @brief Solves the model to find the coefficients using the A matrix and Y vector
     * 
     * @param A The A matrix
     * @param Y The Y vector
     * @return Status The status of the operation
     */
    Status solve(const Eigen::MatrixXd& A, const Eigen::VectorXd& Y) override;

    /**
     * @brief Perform inference (apply the transformation)
     * 
     * @param A The transformation matrix
     * @param X The input vector
     * @return Status The status of the operation
     */
    Status inference(const Eigen::MatrixXd& A, const Eigen::VectorXd& X) override;
};
