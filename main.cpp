#include <iostream>
#include "conformal.hpp"
#include "context.hpp"  


/**
 * Adapt to real dataset 
 */
int main() {
    ModelContext context;
    std::shared_ptr<Conformal> model = std::make_shared<Conformal>();
    context.setModel(model);

    Eigen::VectorXd X(3), Xt(3), Xp(3);
    Eigen::VectorXd Y(3), Yt(3), Yp(3);
    Eigen::VectorXd XYT(6), XYp(6);

    X << 1.0, 2.0, 3.0;
    Y << 4.0, 5.0, 6.0;

    Xt << 5.0, 10.0, 6.0;
    Yt = Y * 2;

    Xp << 5.0, 10.0, 6.0;
    Yp << 5.0, 10.0, 6.0;

    // Prepare the vectors XYT and XYp
    for (int i = 0; i < X.size(); i++) {
        XYT[2 * i] = Xt[i];
        XYT[2 * i + 1] = Yt[i];

        XYp[2 * i] = Xp[i];
        XYp[2 * i + 1] = Yp[i];
    }

    Status status = context.constructA(X, Y);
    if (!status) {
        std::cerr << "Error constructing A: " << status.getMessage() << std::endl;
        return 1;
    }

    status = context.solve(*(model->A), XYT);
    if (!status) {
        std::cerr << "Error solving for coefficients: " << status.getMessage() << std::endl;
        return 1;
    }

    status = context.inference(*(model->A));
    if (!status) {
        std::cerr << "Error performing inference: " << status.getMessage() << std::endl;
        return 1;
    }

    std::cout << "Coefficients:\n" << *(model->coefficients) << std::endl;
    std::cout << "Inference Result:\n" << *(model->results) << std::endl;

    return 0;
}
