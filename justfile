set shell := ["bash", "-cu"]

patch-status:
    git status --short --branch
    git -C thirdparty/ceres-solver status --short --branch
    git -C thirdparty/colmap status --short --branch
    git -C thirdparty/doppelgangers-plusplus status --short --branch

apply-local-patches:
    pixi run patch-ceres-cuda-arch
    pixi run patch-colmap-system-openimageio
    pixi run fix-mast3r-for-new-pytorch

check-local-patches:
    grep -n "NOT CMAKE_CUDA_ARCHITECTURES" thirdparty/ceres-solver/CMakeLists.txt
    grep -n "OIIO_VERSION >= 30000" thirdparty/colmap/src/colmap/sensor/bitmap.cc
    grep -n "OIIO_VERSION >= 20503" thirdparty/colmap/src/colmap/util/oiio_utils.cc
    test -f thirdparty/colmap/cmake/FindOpenImageIO.cmake
    grep -n "weights_only=False" thirdparty/doppelgangers-plusplus/mast3r/model.py

refresh-local-patches:
    mkdir -p patches
    { git -C thirdparty/colmap diff -- src/colmap/sensor/bitmap.cc src/colmap/util/oiio_utils.cc; git -C thirdparty/colmap diff --no-index -- /dev/null cmake/FindOpenImageIO.cmake || true; } > patches/colmap-openimageio-ubuntu2004.patch
    git -C thirdparty/ceres-solver diff -- CMakeLists.txt > patches/ceres-respect-cuda-architectures.patch
    git -C thirdparty/doppelgangers-plusplus diff -- mast3r/model.py > patches/doppelgangers-mast3r-torch-load.patch

check-tva400-reconstruction:
    pixi run python -c "import pycolmap; r = pycolmap.Reconstruction('results/tva_nyx650_400_aliked_lightglue_glomap/sparse/0'); print('images', r.num_images()); print('registered', r.num_reg_images()); print('points3D', r.num_points3D())"
