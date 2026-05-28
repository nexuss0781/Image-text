cmake_minimum_required(VERSION 3.15)
project(alvs VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Find pybind11
find_package(pybind11 REQUIRED)

# Add the main library
pybind11_add_module(alvs_cpp 
    bindings.cpp
    alvs_core.cpp
)

# Include directories
target_include_directories(alvs_cpp PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})

# Compiler optimizations
if(CMAKE_BUILD_TYPE MATCHES Release)
    if(MSVC)
        target_compile_options(alvs_cpp PRIVATE /O2)
    else()
        target_compile_options(alvs_cpp PRIVATE -O3 -march=native)
    endif()
endif()

# Install target
install(TARGETS alvs_cpp LIBRARY DESTINATION .)
