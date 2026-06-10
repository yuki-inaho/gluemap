# Onboarding

## Ubuntu / Debian prerequisite

Before running the Pixi install flow on Ubuntu 20.04 / GLIBC 2.31 hosts, install the system OpenImageIO package so COLMAP/pycolmap can link against the distro `libOpenImageIO.so.2.1` instead of conda-forge OpenImageIO:

```bash
sudo apt-get update
sudo apt-get install -y libopenimageio-dev
```

Then continue with:

```bash
pixi install
GLUEMAP_CUDA_ARCH=89 pixi run install-gluemap
pixi run check-gluemap
```

## Local third-party patches

This Pixi workflow intentionally applies local patches to vendored Ceres,
COLMAP, and Doppelgangers++ sources. They were needed on the Ubuntu 20.04 /
GLIBC 2.31 + CUDA 12.9 workstation used for the TVA_NYX650 400-frame
reconstruction.

The short version:

- Ceres must respect `GLUEMAP_CUDA_ARCH` / `CMAKE_CUDA_ARCHITECTURES`.
- COLMAP needs a system OpenImageIO fallback for Ubuntu 20.04.
- MAST3R checkpoint loading needs `weights_only=False` with the trusted upstream
  checkpoint format used by Doppelgangers++.

See [`docs/local_patches.md`](local_patches.md) for the context, patch files,
expected dirty submodule state, and verification commands.

Useful entry points:

```bash
just patch-status
just check-local-patches
just check-tva400-reconstruction
```
