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
