#pragma once 

#include <iostream>


enum class StatusCode {
    SUCCESS,
    FAILURE,
    INVALID_INPUT,
    OUT_OF_MEMORY,
    OPERATION_NOT_SUPPORTED,
};


class Status {
public:
    Status() : success(true), code(StatusCode::SUCCESS), message("Operation successful") {}

    Status(bool success, StatusCode code, const std::string& msg)
        : success(success), code(code), message(msg) {}

    static Status Ok() {
        return Status(true, StatusCode::SUCCESS, "Operation successful");
    }

    operator bool() const {
        return success; 
    }
    
    static Status Error(StatusCode code, const std::string& msg) {
        return Status(false, StatusCode::SUCCESS, msg);
    }

    bool isSuccessful() const {
        return success;
    }

    StatusCode getCode() const {
        return code;
    }

    std::string getMessage() const {
        return message;
    }

    void printStatus() const {
        if (success) {
            std::cout << "Success: " << message << std::endl;
        } else {
            std::cout << "Error: " << message << " (Code: " << static_cast<int>(code) << ")" << std::endl;
        }
    }

private:
    bool success;
    StatusCode code;
    std::string message;
};