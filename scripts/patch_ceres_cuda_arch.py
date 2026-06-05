#!/usr/bin/env python3
"""Patch vendored Ceres so CMAKE_CUDA_ARCHITECTURES is respected.

Ceres 2.3.0 currently rewrites ``CMAKE_CUDA_ARCHITECTURES`` inside its
top-level CMakeLists when CUDA is found. That is inconvenient for GLUEMAP's
Pixi workflow because users need to target the local GPU architecture
(``89`` on L4/Ada, ``120`` on Blackwell, or a multi-arch list). This script is
idempotent and runs after submodule checkout, before Ceres configure.
"""

from __future__ import annotations

from pathlib import Path


CERES_CMAKE = Path("thirdparty/ceres-solver/CMakeLists.txt")

OLD = """\
      if (CMAKE_VERSION VERSION_GREATER_EQUAL "3.18")
        set(CMAKE_CUDA_ARCHITECTURES "")
        if (CUDAToolkit_VERSION VERSION_LESS "13.0")
"""

NEW = """\
      if (CMAKE_VERSION VERSION_GREATER_EQUAL "3.18")
        if (NOT CMAKE_CUDA_ARCHITECTURES)
          set(CMAKE_CUDA_ARCHITECTURES "")
        endif()
        if (NOT CMAKE_CUDA_ARCHITECTURES AND CUDAToolkit_VERSION VERSION_LESS "13.0")
"""

OLD_END = """\
        if (CUDAToolkit_VERSION VERSION_GREATER_EQUAL "10.0")
          # Support Turing  GPUs.
          list(APPEND CMAKE_CUDA_ARCHITECTURES "75")
        endif(CUDAToolkit_VERSION VERSION_GREATER_EQUAL "10.0")
        if (CUDAToolkit_VERSION VERSION_GREATER_EQUAL "11.0")
          # Support Ampere GPUs.
          list(APPEND CMAKE_CUDA_ARCHITECTURES "80")
        endif(CUDAToolkit_VERSION VERSION_GREATER_EQUAL "11.0")
        if (CUDAToolkit_VERSION VERSION_GREATER_EQUAL "11.8")
          # Support Hopper GPUs.
          list(APPEND CMAKE_CUDA_ARCHITECTURES "90")
        endif(CUDAToolkit_VERSION VERSION_GREATER_EQUAL "11.8")
        message("-- Setting CUDA Architecture to ${CMAKE_CUDA_ARCHITECTURES}")
"""

NEW_END = """\
        if (NOT CMAKE_CUDA_ARCHITECTURES)
          if (CUDAToolkit_VERSION VERSION_GREATER_EQUAL "10.0")
            # Support Turing GPUs.
            list(APPEND CMAKE_CUDA_ARCHITECTURES "75")
          endif(CUDAToolkit_VERSION VERSION_GREATER_EQUAL "10.0")
          if (CUDAToolkit_VERSION VERSION_GREATER_EQUAL "11.0")
            # Support Ampere GPUs.
            list(APPEND CMAKE_CUDA_ARCHITECTURES "80")
          endif(CUDAToolkit_VERSION VERSION_GREATER_EQUAL "11.0")
          if (CUDAToolkit_VERSION VERSION_GREATER_EQUAL "11.8")
            # Support Hopper GPUs.
            list(APPEND CMAKE_CUDA_ARCHITECTURES "90")
          endif(CUDAToolkit_VERSION VERSION_GREATER_EQUAL "11.8")
        endif()
        message("-- Setting CUDA Architecture to ${CMAKE_CUDA_ARCHITECTURES}")
"""


def main() -> None:
    if not CERES_CMAKE.exists():
        raise FileNotFoundError(CERES_CMAKE)

    text = CERES_CMAKE.read_text()
    if "if (NOT CMAKE_CUDA_ARCHITECTURES)" in text:
        text_new = text.replace(
            '        endif(CUDAToolkit_VERSION VERSION_LESS "13.0")',
            "        endif()",
        )
        if text_new != text:
            CERES_CMAKE.write_text(text_new)
            print(f"[patch] normalized CUDA architecture endif in {CERES_CMAKE}")
        else:
            print(f"[skip] {CERES_CMAKE} already respects CMAKE_CUDA_ARCHITECTURES")
        return

    if OLD not in text or OLD_END not in text:
        raise RuntimeError(
            "Could not find the expected Ceres CUDA architecture block; "
            "inspect thirdparty/ceres-solver/CMakeLists.txt before building."
        )

    text = text.replace(OLD, NEW).replace(OLD_END, NEW_END)
    text = text.replace(
        '        endif(CUDAToolkit_VERSION VERSION_LESS "13.0")',
        "        endif()",
    )
    CERES_CMAKE.write_text(text)
    print(f"[patch] {CERES_CMAKE} now respects CMAKE_CUDA_ARCHITECTURES")


if __name__ == "__main__":
    main()
