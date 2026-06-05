#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: $0 <source-dir> <build-dir> [extra-cmake-args...]" >&2
  exit 2
fi

source_dir="$1"
build_dir="$2"
shift 2

# Default to NVIDIA L4/Ada on this workstation, but keep the build portable:
#   GLUEMAP_CUDA_ARCH=89          # L4 / Ada
#   GLUEMAP_CUDA_ARCH=120         # Blackwell
#   GLUEMAP_CUDA_ARCH='89;120'    # multi-arch build
#   GLUEMAP_CUDA_ARCH=native      # CMake native detection, when supported
cuda_arch="${GLUEMAP_CUDA_ARCH:-89}"

echo "[configure] source=$source_dir build=$build_dir cuda_arch=$cuda_arch"
cmake -S "$source_dir" -B "$build_dir" -G Ninja \
  -DCMAKE_CUDA_ARCHITECTURES="$cuda_arch" \
  "$@"
