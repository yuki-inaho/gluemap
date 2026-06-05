# 作業計画書兼記録書: GLUEMAP PR#3 取り込みと L4/tomato 再構成 smoke

- 作成日時: 2026-06-05 12:00:02 UTC+0000
- repo: `/home/kasm-user/Desktop/gluemap`
- fork: `git@github.com:yuki-inaho/gluemap.git`
- upstream: `https://github.com/colmap/gluemap`
- 対象PR: `https://github.com/colmap/gluemap/pull/3`
- 作業ブランチ: `cu129-l4`
- 現PC GPU: NVIDIA L4, 23034 MiB, driver 580.159.04

## ゴール

1. `colmap/gluemap` の PR #3 (Pixi project files / Ceres+CUDSS+COLMAP source build) を `yuki-inaho/gluemap` に取り込む。
2. このPCの NVIDIA L4 で使える `cu*` ブランチを作成する。
3. 後続で他GPU CUDA arch でも使いやすいよう、`sm_89` 固定ではなく `GLUEMAP_CUDA_ARCH` で差し替え可能な構成にする。
4. 上流 issue を確認し、24GB級GPUで動かしやすい低メモリ設定や既知の罠を反映する。
5. トマト NYX660 データで再構成 smoke を実行し、成果物/失敗理由を記録する。
6. 必要な更新を commit & push する。

## 参照した上流情報

- PR #3: draft, head `S-o-T:pixi_torch-sm120_cudss`, commit `8b91d76b...`
  - 追加/変更: `.gitattributes`, `.gitignore`, `.gitmodules`, `INSTALL.md`, `pixi.toml`, `pixi.lock`, Ceres/COLMAP/pyceres submodules, `gluemap/pybind/CMakeLists.txt`, Kornia import fix.
  - PRコメント: `pixi add ninja cmake`, 必要なら `cxx-compiler`, Blackwellでは `-DCMAKE_CUDA_ARCHITECTURES=120` が必要、checkpoint download task があるとよい。
- Issue #5: `camera_model: PINHOLE` で `camera.focal_length` が複数焦点に対して失敗。
- Issue #6: 200枚で SIFT/BA が重い。GPU pycolmap, solver type, cuDSS/CUDA Ceres が論点。
- Issue #7: RTX 3090 24GB で default inference 中に DataLoader pin-memory thread が OOM。

## 完了の定義 (DoD)

- [x] Desktop配下に `yuki-inaho/gluemap` が recursive clone 済み。
- [x] `cu*` ブランチ上で PR #3 相当の Pixi/Ceres/COLMAP/pyceres 取り込みが完了。
- [x] CUDA arch は `GLUEMAP_CUDA_ARCH` で `89`, `120`, 複数archを切替可能。
- [x] 上流 issue 由来の動かしやすさ改善を少なくとも1つ以上実装し、docsに記録。
- [x] Tomato NYX660 の入力サブセット生成手順が repo 内 task として再現可能。
- [x] Pixi環境の install/check または失敗ログを取得し、原因を記録。
- [x] Tomato reconstruction smoke を実行し、成功成果物または明確な失敗原因を記録。
- [x] `pytest`/静的確認など、変更に見合う検証を実施。
- [x] 生成物を混ぜずに commit & push 済み。

## 作業チェックリスト

- [x] 2026-06-05 11:51:54 UTC+0000: PC/GPU/CUDA確認。NVIDIA L4 23GB、driver 580.159.04、system `nvcc` なし、cmake 3.16.3。
- [x] 2026-06-05 11:52頃: `/home/kasm-user/Desktop/gluemap` に `git clone --recursive git@github.com:yuki-inaho/gluemap.git`。
- [x] PR #3 と上流 issue #4-#7 を確認。
- [x] `cu129-l4` ブランチ作成。
- [x] PR #3 commit `8b91d76b...` を `--no-commit` で取り込み。
- [x] `pixi.toml` に missing deps (`python`, `cmake`, `ninja`, `cxx-compiler`, `git`, `wget`) を追加。
- [x] Ceres/COLMAP configure を共通 `scripts/configure_cuda_project.sh` に切り出し、`GLUEMAP_CUDA_ARCH` で arch 切替可能にした。
- [x] `gluemap/pybind/CMakeLists.txt` の Ceres CUDA/cuDSS 検出を堅牢化。
- [x] `configs/l4_lowmem.yaml`, `configs/tomato_l4_smoke.yaml` を追加。
- [x] `scripts/make_image_subset.py` で NYX660 Color の symlink subset を生成可能にした。
- [x] `scripts/download_checkpoints.sh` で minimal/full checkpoint download task を追加。
- [x] `--pin_memory/--no-pin_memory` CLI を追加し、DataLoader に反映。
- [x] `PINHOLE` 等の複数焦点 camera model で normalized reprojection error が落ちないよう代表焦点 helper を追加。
- [x] `README.md` / `INSTALL.md` に Pixi arch 切替、L4/tomato smoke、issue由来の注意点を追記。
- [x] 2026-06-05 12:29頃: Pixi 0.70.1 を `/home/kasm-user/.pixi/bin/pixi` に導入し、`pytorch-gpu 2.10.0 / CUDA 12.9` で `torch.cuda.is_available() == True`, GPU `NVIDIA L4` を確認。
- [x] 2026-06-05 12:30-12:55頃: `GLUEMAP_CUDA_ARCH=89 pixi run install-gluemap` 系のビルドを実行。Ceres/COLMAP は `CMAKE_CUDA_ARCHITECTURES=89` で configure/build/install 成功。
- [x] 2026-06-05 12:36頃: conda-forge `libOpenImageIO.so.3.1` が Ubuntu 20.04 の GLIBC 2.31 と不整合 (`GLIBC_2.32` 要求) で `pycolmap` import 失敗することを確認。
- [x] 2026-06-05 12:37頃: `openimageio=2.5.*` への downgrade は `libboost`/`fmt`/torch 周辺の solve conflict で不採用。`sudo apt-get install -y libopenimageio-dev` と Pixi env から conda OpenImageIO を外す方針に切替。
- [x] 2026-06-05 12:55頃: `scripts/patch_colmap_system_openimageio.py` を追加/更新。source と `$CONDA_PREFIX/share/colmap/cmake` の両方に `FindOpenImageIO.cmake` を生成し、system `libOpenImageIO.so.2.1` を利用。C++ のみ `-idirafter /usr/include` を使い、CUDA compile には伝播しないよう修正。
- [x] 2026-06-05 12:56頃: `scripts/install_pycolmap.sh` を更新。CUDA arch を `GLUEMAP_CUDA_ARCH` から渡し、`GENERATE_STUBS=OFF`、stale editable `_core` を削除してから `--force-reinstall --no-cache-dir` で再ビルドするようにした。
- [x] 2026-06-05 12:57頃: `pycolmap` import 成功。`ldd .pixi/envs/default/lib/python3.11/site-packages/pycolmap/_core*.so` で `libOpenImageIO.so.2.1 => /usr/lib/x86_64-linux-gnu/libOpenImageIO.so.2.1` を確認。
- [x] 2026-06-05 12:58頃: `pixi add pytest` で検証依存を追加し、`pixi run pytest tests/test_reprojection_error_focal.py -q` -> `3 passed in 0.15s`。
- [x] 2026-06-05 12:58頃: `pixi run make-tomato-smoke-subset` -> `data/tomato_nyx660_color_smoke` に 12画像 symlink subset を作成。
- [x] 2026-06-05 12:58頃: `pixi run download-checkpoints-minimal` -> `checkpoints/pi3.safetensors` と `checkpoints/dino_salad.ckpt` を取得。
- [x] 2026-06-05 12:58-12:59頃: `pixi run gluemap-demo --config configs/tomato_l4_smoke.yaml --rerun_from retrieval` を実行し成功。12画像、global rotations 12、global centers 12、valid virtual points 3770、`coarse_only` により refinement はスキップ。出力: `results/tomato_l4_smoke/coarse/{cameras,frames,images,points3D,rigs}.bin`, `pipeline_timing.pth`, `salad_descriptors.pt`, `star_result.pth`。

## Struggles / Findings / Tips

### Struggles

- PR #3 は Blackwell `sm_120` 前提の色が強く、このPCの L4 `sm_89` にそのまま固定して取り込むと後続PCで再利用しにくい。Ceres/COLMAP/pycolmap の各ビルド経路へ `GLUEMAP_CUDA_ARCH` を通す必要があった。
- Ubuntu 20.04 / GLIBC 2.31 と conda-forge `OpenImageIO 3.1` が不整合で、`pycolmap` import 時に `GLIBC_2.32` 要求で落ちた。単純な conda downgrade は依存衝突が大きく、system `libOpenImageIO.so.2.1` へ逃がす方針に切り替えた。
- `OpenImageIO` の include path を CMake target に載せる際、C++ 向け compile option が CUDA compile に伝播し、`nvcc fatal: A single input file is required ...` を引き起こした。generator expression で C++ のみに限定する必要があった。
- Pixi task の依存関係上、`gluemap-tomato-smoke` は install task も再実行しやすい。ビルド済み環境で smoke だけ確認する場合は `gluemap-demo` を直接呼ぶ方が安全だった。
- 24GB GPU でも default 設定のままでは上流 issue #7 と同様の OOM リスクがあるため、tomato smoke は低メモリ設定から始める必要があった。

### Findings

- L4 は compute capability `sm_89`。PR #3 は Blackwell `sm_120` を主対象にしているため、そのまま固定するのではなく `GLUEMAP_CUDA_ARCH` で可変化する必要がある。
- 上流 issue #7 と同じ 24GB級GPUでは default `batch_size=30`, `pin_memory=True`, `num_workers=4` は危険。smoke は `batch_size=1`, `num_workers=0`, `pin_memory=false`, `skip_doppelgangers=true`, `use_dummy_tracks=true`, `coarse_only=true` から始める。
- トマト入力候補は `/home/kasm-user/Desktop/NYX660_2025_12_01_17_33_27_0135/Color`。全1220枚を直投入せず、まず 12枚程度の stride subset で pipeline を検証する。
- Ubuntu 20.04 / GLIBC 2.31 では conda-forge OpenImageIO 3.1 が使えない。`libopenimageio-dev` の system OIIO 2.1 に逃がし、COLMAP/pycolmap 用の `FindOpenImageIO.cmake` を source と install prefix の両方へ生成する必要がある。
- 生成物サイズ: `.pixi` 13G、`checkpoints` 3.9G、`results/tomato_l4_smoke` 2.3M、`data/tomato_nyx660_color_smoke` は symlink subset で 8K。これらは `.gitignore` 対象で commit しない。

### Tips

- CUDA arch は `GLUEMAP_CUDA_ARCH=89 pixi run install-gluemap` のように指定する。Blackwell は `120`、複数GPU向け配布は `GLUEMAP_CUDA_ARCH='89;120'` のような CMake semicolon list を使う。
- 既に install 済みの環境で tomato smoke だけ再実行する場合は、`pixi run gluemap-demo --config configs/tomato_l4_smoke.yaml --rerun_from retrieval` を使う。
- `pycolmap` 周りを再ビルドした後は、`pixi run check-gluemap` と `ldd .pixi/envs/default/lib/python3.11/site-packages/pycolmap/_core*.so | grep OpenImageIO` で import と OIIO 解決先を確認する。
- L4 で最初に再構成を試すなら `configs/tomato_l4_smoke.yaml` の 12枚 coarse-only smoke から始め、成功後に枚数・batch・Doppelgangers/refinement を段階的に戻す。
- 作業終了時点の diary コピーは `/home/kasm-user/Desktop/diary/diary_Jun05-2026_gluemap_pr3_l4_tomato_reconstruction.md` に配置する。

## Diary copy

- 2026-06-05 13:10:00 UTC+0000: 本作業書に Struggles / Findings / Tips を明示追記し、Desktop diary 側にも同内容を残す。
