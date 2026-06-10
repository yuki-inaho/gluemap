# Local Build Patches

This document records the local patches that are intentionally applied to
vendored third-party code for the current Pixi/CUDA workstation flow.

## Context

The target workstation is Ubuntu 20.04 / GLIBC 2.31 with an NVIDIA L4-class
GPU. GLUEMAP is installed through Pixi with CUDA 12.9 packages and builds
vendored Ceres, COLMAP/pycolmap, and Doppelgangers++ dependencies.

During the TVA_NYX650 400-frame reconstruction setup, three local build/runtime
patches were required before the pipeline could be installed and checked
reliably:

1. Ceres must respect the GPU architecture requested by the caller.
2. COLMAP must link against the system OpenImageIO package available on Ubuntu
   20.04 instead of requiring a conda-forge OpenImageIO build that needs a newer
   GLIBC.
3. Doppelgangers++ / MAST3R checkpoint loading must opt out of PyTorch's safe
   `weights_only` path when loading trusted upstream checkpoints that include
   non-tensor metadata.

These are not reconstruction outputs. They are source patches for local build
compatibility. They explain why `git status` can show dirty submodules after
`pixi run install-gluemap`.

## Patch Inventory

| Patch | Applies in | Why it exists | Normal application path |
| --- | --- | --- | --- |
| `patches/ceres-respect-cuda-architectures.patch` | `thirdparty/ceres-solver` | Upstream Ceres rewrites `CMAKE_CUDA_ARCHITECTURES`, making `GLUEMAP_CUDA_ARCH=89`, `120`, or a multi-arch list ineffective. | `pixi run patch-ceres-cuda-arch` |
| `patches/colmap-openimageio-ubuntu2004.patch` | `thirdparty/colmap` | Ubuntu 20.04 provides `libopenimageio-dev` without `OpenImageIOConfig.cmake`, and its OIIO headers do not support the newer `OIIO_MAKE_VERSION(...)` guard used by this COLMAP checkout. | `pixi run patch-colmap-system-openimageio` |
| `patches/doppelgangers-mast3r-torch-load.patch` | `thirdparty/doppelgangers-plusplus` | New PyTorch versions default toward safer checkpoint loading; MAST3R checkpoints used here include trusted metadata, so `weights_only=False` is required. | `pixi run fix-mast3r-for-new-pytorch` |

The Pixi tasks are the primary mechanism. The patch files are checked in as
reviewable evidence and as a fallback if the helper scripts need to be audited
or refreshed.

## Expected Dirty State

After installing GLUEMAP, this top-level status is expected unless the submodule
patches are reverted:

```text
 m thirdparty/ceres-solver
 m thirdparty/colmap
 m thirdparty/doppelgangers-plusplus
```

The relevant file-level changes are:

```text
thirdparty/ceres-solver/CMakeLists.txt
thirdparty/colmap/src/colmap/sensor/bitmap.cc
thirdparty/colmap/src/colmap/util/oiio_utils.cc
thirdparty/colmap/cmake/FindOpenImageIO.cmake
thirdparty/doppelgangers-plusplus/mast3r/model.py
```

Generated root logs such as `install_gluemap.log` and `tva_*.log` are ignored
and should not be committed.

## Verification

Use the just recipes from the repository root:

```bash
just patch-status
just check-local-patches
just check-tva400-reconstruction
```

The TVA 400-frame reconstruction is considered valid when pycolmap reports:

```text
images 400
registered 400
points3D 41333
```

The COLMAP analyzer log for the same run recorded:

```text
Registered images: 400
Points: 41333
Mean reprojection error: 1.147551px
```

## Refreshing Patch Files

If the helper scripts are changed, regenerate the patch files from the currently
applied submodule diffs:

```bash
just refresh-local-patches
```

Then review:

```bash
git diff -- patches docs/local_patches.md justfile .gitignore
```

Do not commit reconstruction outputs, checkpoints, TensorBoard files, or
dataset images. Those belong under ignored `data/`, `results/`, `checkpoints/`,
or local log files.
