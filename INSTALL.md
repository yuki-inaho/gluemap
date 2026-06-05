# Installation

GLUEMAP is a Python package with a C++/pybind11 extension (`pygluemap`)
that links against Ceres, Eigen, Boost, and OpenMP. It also depends on
several feed-forward models that are vendored as git submodules.

## 1. Clone with submodules

```
git clone https://github.com/colmap/gluemap.git
cd gluemap
git submodule update --init --recursive
```

The submodules under `thirdparty/` (pi3, vggt, mapanything,
doppelgangers-plusplus, salad) are required at runtime — they are added
to `sys.path` by `thirdparty/path_to_thirdparty.py`. Skipping this step
will cause `ImportError` on first run.

## 2. Install C/C++ build dependencies

You need development headers + CMake configs for:

- CMake ≥ 3.18
- A C++17 compiler
- Eigen3
- Ceres (CUDA support optional — see note below)
- METIS (Ceres pulls it in transitively)
- Boost (headers only)
- OpenMP
- pybind11 ≥ 3.0 (also fetched automatically as a build dep, but it's
  fine to have it in the env)

### Option A — conda / micromamba (recommended)

Versions below are pinned to the known-good `gluemap` env so installs
stay reproducible alongside the pinned Python deps in
`pyproject.toml`. GLUEMAP requires CUDA at runtime — the GPU PyTorch
build is the only supported configuration:

```
micromamba install -n <env> -c conda-forge \
    eigen=3.4.0 \
    ceres-solver=2.2.0 \
    metis=5.1.0 \
    boost=1.85.0 \
    libstdcxx-ng=15.2.0 \
    pytorch-gpu=2.4.1 \
    torchvision=0.19.1 \
    cuda-version=12.4
```

Installing PyTorch from conda-forge (rather than pip) is strongly
recommended: it links against the same `libstdc++` as conda-forge's
Ceres, which avoids a runtime ABI clash where `import torch` loads the
older system `libstdc++` first and then `import pygluemap` fails with
``version `CXXABI_1.3.15' not found``. See the troubleshooting section
if you hit this.

If you want CMake to discover the C++ deps without setting
`CMAKE_PREFIX_PATH` manually, also install the conda compilers (their
activate scripts export `CMAKE_PREFIX_PATH=$CONDA_PREFIX`):

```
micromamba install -n <env> -c conda-forge compilers
```

### Option B — system packages (Ubuntu/Debian)

```
sudo apt install \
    cmake \
    build-essential \
    libeigen3-dev \
    libceres-dev \
    libmetis-dev \
    libboost-dev \
    pybind11-dev
```

### Note on Ceres + CUDA

CUDA support is auto-detected at configure time (CMake prints
`-- Ceres CUDA support: TRUE/FALSE`). With CUDA, `pygluemap` uses
Ceres' GPU linear solvers; without it, it falls back to CPU. The
default conda-forge `ceres-solver` is CPU-only — for the CUDA path,
build Ceres from source against your CUDA toolkit and point
`CMAKE_PREFIX_PATH` at it.

### Option C — Pixi package manager

As an alternative, Pixi can create a self-contained CUDA 12 environment,
build Ceres/COLMAP/pyceres from submodules, and install GLUEMAP. The
default CUDA architecture is `89` for NVIDIA L4/Ada. Override
`GLUEMAP_CUDA_ARCH` for other GPUs:

```
# L4 / Ada (default)
pixi install
pixi run install-gluemap

# Blackwell example
GLUEMAP_CUDA_ARCH=120 pixi run install-gluemap

# Multi-arch build when needed
GLUEMAP_CUDA_ARCH='89;120' pixi run install-gluemap
```

The Pixi task includes `cmake`, `ninja`, and a C++ compiler, which are
needed by the source builds. After populating and activating the
environment, go to step 4.

On Ubuntu 20.04 / GLIBC 2.31 hosts, use the distro OpenImageIO package
instead of the conda-forge one:

```
sudo apt-get install -y libopenimageio-dev
```

The Pixi manifest intentionally does not depend on conda-forge
`openimageio`, because current conda-forge OpenImageIO pulls a newer
GLIBC than Ubuntu 20.04 provides. The Pixi build task installs a local
`FindOpenImageIO.cmake` fallback so COLMAP/pycolmap can link against the
system `libOpenImageIO.so.2.1`. If you change CUDA architecture or swap
OpenImageIO implementations, rerun `pixi run install-pycolmap`; the task
clears stale editable `_core` artifacts before rebuilding.

## 3. Install GLUEMAP

From the repo root, in your active Python ≥ 3.10 environment:

```
CMAKE_PREFIX_PATH=$CONDA_PREFIX pip install -e .
```

The `CMAKE_PREFIX_PATH=$CONDA_PREFIX` prefix is needed when the conda
compilers are not installed — Ceres' bundled `FindMETIS.cmake` only
honours `CMAKE_PREFIX_PATH`/system paths, so without this it can't
locate METIS even when it's installed in the env.

For a non-editable install drop the `-e`.

### Optional extras

```
pip install -e ".[dev]"   # ruff + pytest
```

## 4. Download model checkpoints

The demo configs (`configs/base.yaml`) expect four checkpoints under
`checkpoints/`. They are not bundled — download them from each model's
upstream release:

| Config key | File | Source |
|---|---|---|
| `path_feedforward` | `pi3.safetensors` | HF `yyfz233/Pi3` |
| `path_retrieval` | `dino_salad.ckpt` | github.com/serizba/salad release `v1.0.0` |
| `path_tracker` | `vggsfm_v2_0_0_track_predictor.bin` | HF `facebook/VGGSfM` (`vggsfm_v2_tracker.pt`, renamed) |
| `path_dg` | `checkpoint-dg+visym.pth` | HF `doppelgangers25/doppelgangers_plusplus` |

Quickest setup from the repo root:

```
mkdir -p checkpoints

# SALAD retrieval
wget -O checkpoints/dino_salad.ckpt \
    https://github.com/serizba/salad/releases/download/v1.0.0/dino_salad.ckpt

# VGGSfM tracker (renamed to match base.yaml)
wget -O checkpoints/vggsfm_v2_0_0_track_predictor.bin \
    https://huggingface.co/facebook/VGGSfM/resolve/main/vggsfm_v2_tracker.pt

# Pi3 multiview model (huggingface_hub already in env)
hf download yyfz233/Pi3 model.safetensors --local-dir checkpoints
mv checkpoints/model.safetensors checkpoints/pi3.safetensors

# Doppelgangers++
hf download doppelgangers25/doppelgangers_plusplus \
    checkpoint-dg+visym.pth --local-dir checkpoints
```

With Pixi, the same downloads are wrapped as reproducible tasks:

```
pixi run download-checkpoints-minimal  # Pi3 + SALAD, enough for low-memory smoke
pixi run download-checkpoints-full     # Pi3 + SALAD + VGGSfM + Doppelgangers++
```

If you switch `chosen_model` to `vggt` or `map_anything`, fetch the
matching backbone instead of `pi3.safetensors`:

- VGGT: `https://huggingface.co/facebook/VGGT-1B/resolve/main/model.pt`
- MapAnything: set `path_feedforward: facebook/map-anything` (it's a HF
  repo ID, not a file path — `MapAnything.from_pretrained` resolves it).

## 5. Verify

```
python -c "import gluemap; import pygluemap; print(pygluemap.__file__)"
gluemap-demo --help
gluemap-benchmark --help
pytest tests/
```

### L4 / 24GB tomato smoke

On the Desktop workstation used for the tomato experiments, the NYX660
RGB frames live at
`/home/kasm-user/Desktop/NYX660_2025_12_01_17_33_27_0135/Color`. The
low-memory smoke config uses a small symlink subset, sequential matching,
`batch_size=1`, no pinned memory, skips Doppelgangers++, uses dummy
tracks, and stops at coarse reconstruction:

```
pixi run make-tomato-smoke-subset
pixi run gluemap-tomato-smoke
```

If the environment is already installed and you want to avoid rerunning
the build dependencies, call the demo directly:

```
pixi run gluemap-demo --config configs/tomato_l4_smoke.yaml --rerun_from retrieval
```

For full-quality runs, start from `configs/l4_lowmem.yaml` and
incrementally relax `skip_doppelgangers`, `use_dummy_tracks`,
`coarse_only`, `sample_frequency`, `num_neighbors*`, and the subset size
after the smoke path succeeds.

## Troubleshooting

- **`Could NOT find Eigen3 / Ceres`** — install the dev packages (step 2)
  and make sure CMake can see them: `CMAKE_PREFIX_PATH=$CONDA_PREFIX`
  or the equivalent install prefix.
- **`Could NOT find METIS (missing: METIS_INCLUDE_DIR METIS_LIBRARY)`** —
  METIS is installed but `CMAKE_PREFIX_PATH` is not set. Re-run with
  `CMAKE_PREFIX_PATH=$CONDA_PREFIX pip install -e .`, or pass hints:
  `CMAKE_ARGS="-DMETIS_INCLUDE_DIR=$CONDA_PREFIX/include -DMETIS_LIBRARY=$CONDA_PREFIX/lib/libmetis.so" pip install -e .`.
- **`No matching distribution found for lightglue`** — `lightglue` is
  installed from `git+https://github.com/cvg/LightGlue.git` (declared
  in `pyproject.toml`). Make sure pip can reach GitHub.
- **`ImportError: pi3 / vggt / mapanything is not initialized`** — you
  forgot `git submodule update --init --recursive`.
- **CUDA architecture mismatch while building Ceres/COLMAP** — set
  `GLUEMAP_CUDA_ARCH` before the Pixi install task, for example
  `GLUEMAP_CUDA_ARCH=89 pixi run install-gluemap` for L4/Ada or
  `GLUEMAP_CUDA_ARCH=120 ...` for Blackwell. Multiple archs are accepted
  as a CMake semicolon list, e.g. `GLUEMAP_CUDA_ARCH='89;120'`.
- **`pycolmap` imports `libOpenImageIO.so.3.1` and fails on GLIBC** —
  remove conda-forge OpenImageIO from the Pixi env, install
  `libopenimageio-dev`, and rerun `pixi run install-pycolmap`. A healthy
  build on Ubuntu 20.04 links `_core` to
  `/usr/lib/x86_64-linux-gnu/libOpenImageIO.so.2.1`.
- **CUDA OOM in DataLoader pin-memory thread** — try
  `--no-pin_memory --num_workers 0 --batch_size 1`, or inherit
  `configs/l4_lowmem.yaml`. This mirrors the upstream issue where a
  24GB GPU ran out of memory during default two-view inference.
- **`camera_model: PINHOLE` normalized reprojection errors crash on
  `camera.focal_length`** — this branch normalizes by a representative
  focal length, averaging `fx`/`fy` for two-focal camera models.
- **`ImportError: /lib64/libstdc++.so.6: version 'CXXABI_1.3.15' not
  found (required by .../libceres.so.4)`** — you have PyTorch installed
  from pip, which pulls in the system `libstdc++` at import time, and
  then conda-forge's newer `libceres` can't load against it. The
  durable fix is to install PyTorch from conda-forge so it shares a
  toolchain with Ceres:

  ```
  pip uninstall -y torch torchvision
  micromamba install -n <env> -c conda-forge \
      pytorch-gpu=2.4.1 \
      torchvision=0.19.1 \
      cuda-version=12.4
  ```

  As a per-shell workaround you can also force the conda libstdc++ to
  load first: `export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$LD_LIBRARY_PATH`.
