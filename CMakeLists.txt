cmake_minimum_required(VERSION 3.10)

project(TransformationSolverProject VERSION 1.0)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED True)

find_package(Eigen3 3.3 REQUIRED NO_MODULE)

find_package(Ceres REQUIRED)

add_executable(TransformationSolver main.cpp src/model.cpp src/conformal.cpp)

target_include_directories(TransformationSolver PUBLIC ${EIGEN3_INCLUDE_DIR} ${CERES_INCLUDE_DIRS} include)

target_link_libraries(TransformationSolver ${CERES_LIBRARIES} Eigen3::Eigen)
