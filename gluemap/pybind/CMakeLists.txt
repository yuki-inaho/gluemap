# setup PYTHON_EXECUTABLE
cmake_minimum_required(VERSION 3.18)

project(pygluemap)
cmake_policy(SET CMP0057 NEW)  # Fix IN_LIST handling

set(CMAKE_BUILD_TYPE Release)

find_package(Python COMPONENTS Interpreter Development.Module REQUIRED)
message(STATUS "Python_EXECUTABLE: " ${Python_EXECUTABLE})

find_package(pybind11 CONFIG REQUIRED)
find_package(Eigen3)
find_package(Ceres REQUIRED)
find_package(Boost REQUIRED)
find_package(OpenMP REQUIRED)

pybind11_add_module(pygluemap MODULE "bindings.cc" "track_selection.cc")

target_include_directories(pygluemap PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/vendor
)
target_link_libraries(pygluemap PRIVATE pybind11::module Eigen3::Eigen ${CERES_LIBRARIES} Boost::headers)
target_compile_definitions(pygluemap PRIVATE cxx_std_17)
set(CERES_HAS_CUDA FALSE)
get_target_property(
    CERES_INTERFACE_LINK_LIBRARIES
    Ceres::ceres
    INTERFACE_LINK_LIBRARIES
)
if (CERES_INTERFACE_LINK_LIBRARIES)
    string(FIND "${CERES_INTERFACE_LINK_LIBRARIES}" "cudss" CERES_CUDSS_POS)
    if (NOT "${CERES_CUDSS_POS}" STREQUAL "-1")
        set(CERES_HAS_CUDA TRUE)
    endif()
endif()
if (TARGET Ceres::ceres_cuda_kernels)
    set(CERES_HAS_CUDA TRUE)
endif()
message(STATUS "Ceres CUDA support: ${CERES_HAS_CUDA}")

if (CERES_HAS_CUDA)
    target_compile_definitions(pygluemap PRIVATE CERES_HAS_CUDA)
endif()

# Bake the directories of linked libraries (Ceres, etc.) into the
# extension's RPATH so loading pygluemap also picks up the matching
# libstdc++ / libceres from $CONDA_PREFIX/lib at runtime, without
# requiring the user to set LD_LIBRARY_PATH.
set_target_properties(pygluemap PROPERTIES
    BUILD_WITH_INSTALL_RPATH TRUE
    INSTALL_RPATH_USE_LINK_PATH TRUE
)

# scikit-build-core sets CMAKE_INSTALL_PREFIX to the wheel staging dir;
# combined with `wheel.install-dir = "/"` in pyproject.toml, this lands
# pygluemap at the top of site-packages (matching the legacy install).
install(TARGETS pygluemap DESTINATION .)
