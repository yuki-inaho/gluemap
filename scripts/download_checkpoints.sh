#!/usr/bin/env bash
set -euo pipefail

mode="${1:-minimal}"
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

mkdir -p checkpoints

download_if_missing() {
  local output="$1"
  local url="$2"
  if [[ -s "$output" ]]; then
    echo "[skip] $output"
    return
  fi
  echo "[get]  $output"
  wget -O "$output" "$url"
}

download_pi3() {
  if [[ -s checkpoints/pi3.safetensors ]]; then
    echo "[skip] checkpoints/pi3.safetensors"
    return
  fi
  echo "[get]  checkpoints/pi3.safetensors"
  hf download yyfz233/Pi3 model.safetensors --local-dir checkpoints
  mv checkpoints/model.safetensors checkpoints/pi3.safetensors
}

download_salad() {
  download_if_missing \
    checkpoints/dino_salad.ckpt \
    https://github.com/serizba/salad/releases/download/v1.0.0/dino_salad.ckpt
}

download_tracker() {
  download_if_missing \
    checkpoints/vggsfm_v2_0_0_track_predictor.bin \
    https://huggingface.co/facebook/VGGSfM/resolve/main/vggsfm_v2_tracker.pt
}

download_doppelgangers() {
  if [[ -s checkpoints/checkpoint-dg+visym.pth ]]; then
    echo "[skip] checkpoints/checkpoint-dg+visym.pth"
    return
  fi
  echo "[get]  checkpoints/checkpoint-dg+visym.pth"
  hf download doppelgangers25/doppelgangers_plusplus \
    checkpoint-dg+visym.pth --local-dir checkpoints
}

case "$mode" in
  minimal)
    download_pi3
    download_salad
    ;;
  full)
    download_pi3
    download_salad
    download_tracker
    download_doppelgangers
    ;;
  *)
    echo "usage: $0 [minimal|full]" >&2
    exit 2
    ;;
esac

echo "[done] checkpoints mode=$mode"
