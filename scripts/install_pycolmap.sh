#!/usr/bin/env bash
set -euo pipefail

cuda_arch="${GLUEMAP_CUDA_ARCH:-89}"

echo "[install-pycolmap] cuda_arch=${cuda_arch}"
echo "[install-pycolmap] disabling stub generation to avoid host GLIBC leakage during build-time imports"
echo "[install-pycolmap] clearing stale editable extension artifacts"

site_packages="$(python3 - <<'PY'
import sysconfig
print(sysconfig.get_paths()["purelib"])
PY
)"

rm -rf \
  "${site_packages}/pycolmap" \
  "${site_packages}"/pycolmap-*.dist-info \
  "${site_packages}/_pycolmap_editable.py" \
  "${site_packages}/_pycolmap_editable.pth"
rm -rf python/build

pip3 install -e . \
  --force-reinstall \
  --no-cache-dir \
  --no-deps \
  --config-settings=cmake.define.CMAKE_CUDA_ARCHITECTURES="${cuda_arch}" \
  --config-settings=cmake.define.GENERATE_STUBS=OFF
