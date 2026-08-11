cmake_minimum_required(VERSION 3.16)
project(alvs VERSION 1.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

option(ALVS_BUILD_PYTHON_MODULE "Build the pybind11 Python extension" ON)
option(ALVS_BUILD_STAGE1_EVALUATION "Build the Stage 1 native evaluation harness" ON)

add_library(alvs_core STATIC alvs_core.cpp)
target_include_directories(alvs_core PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

target_compile_options(alvs_core PRIVATE
    $<$<CXX_COMPILER_ID:GNU,Clang>:-Wall;-Wextra;-Wpedantic>
    $<$<CXX_COMPILER_ID:MSVC>:/W4>
)

if(CMAKE_BUILD_TYPE MATCHES "Release|RelWithDebInfo")
    if(MSVC)
        target_compile_options(alvs_core PRIVATE /O2)
    else()
        target_compile_options(alvs_core PRIVATE -O3 -march=native)
    endif()
endif()

if(ALVS_BUILD_PYTHON_MODULE)
    find_package(pybind11 CONFIG REQUIRED)
    pybind11_add_module(alvs_cpp bindings.cpp)
    target_link_libraries(alvs_cpp PRIVATE alvs_core)
    target_include_directories(alvs_cpp PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
    if(CMAKE_BUILD_TYPE MATCHES "Release|RelWithDebInfo")
        if(MSVC)
            target_compile_options(alvs_cpp PRIVATE /O2)
        else()
            target_compile_options(alvs_cpp PRIVATE -O3 -march=native)
        endif()
    endif()
    install(TARGETS alvs_cpp LIBRARY DESTINATION .)
endif()

if(ALVS_BUILD_STAGE1_EVALUATION)
    add_executable(stage1_evaluation stage1_evaluation.cpp)
    target_link_libraries(stage1_evaluation PRIVATE alvs_core)
    target_compile_options(stage1_evaluation PRIVATE
        $<$<CXX_COMPILER_ID:GNU,Clang>:-Wall;-Wextra;-Wpedantic>
        $<$<CXX_COMPILER_ID:MSVC>:/W4>
    )
    if(CMAKE_BUILD_TYPE MATCHES "Release|RelWithDebInfo")
        if(MSVC)
            target_compile_options(stage1_evaluation PRIVATE /O2)
        else()
            target_compile_options(stage1_evaluation PRIVATE -O3 -march=native)
        endif()
    endif()

    include(CTest)
    if(BUILD_TESTING)
        add_test(NAME stage1_native_evaluation COMMAND stage1_evaluation --quick)
    endif()
endif()
