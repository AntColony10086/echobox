#!/usr/bin/env bash
# Download GECO2 (and SAM2) pretrained weights into .data/weights/
set -euo pipefail

WEIGHTS_DIR="${ECHOBOX_WEIGHTS_DIR:-./.data/weights}"
mkdir -p "$WEIGHTS_DIR"

GECO2_URL="${ECHOBOX_GECO2_WEIGHTS_URL:-https://github.com/jerpelhan/GECO2/releases/download/v1.0/geco2.pth}"
SAM2_URL="${ECHOBOX_SAM2_WEIGHTS_URL:-https://dl.fbaipublicfiles.com/segment_anything_2/072824/sam2_hiera_tiny.pt}"

GECO2_FILE="$WEIGHTS_DIR/geco2.pth"
SAM2_FILE="$WEIGHTS_DIR/sam2_hiera_tiny.pt"

download() {
  local url="$1"
  local dest="$2"
  if [ -f "$dest" ]; then
    echo "==> already exists: $dest"
    return
  fi
  echo "==> downloading $url -> $dest"
  curl -L --fail -o "$dest.tmp" "$url" && mv "$dest.tmp" "$dest"
}

download "$SAM2_URL" "$SAM2_FILE"
download "$GECO2_URL" "$GECO2_FILE"

echo ""
echo "Weights ready in $WEIGHTS_DIR/"
echo "Set in your .env:"
echo "  ECHOBOX_ML_GECO2_WEIGHTS=$GECO2_FILE"
echo "  ECHOBOX_ML_SAM2_WEIGHTS=$SAM2_FILE"
