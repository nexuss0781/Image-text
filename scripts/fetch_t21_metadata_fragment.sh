#!/usr/bin/env bash
# Fetch only a bounded public metadata fragment for the T2.1 review queue.
# This tool never requests image, annotation-mask, embedding, or model artifacts.
set -euo pipefail

readonly SOURCE_URL="https://storage.googleapis.com/openimages/2018_04/train/train-images-boxable-with-rotation.csv"
readonly MAX_BYTES=262143  # 256 KiB metadata-only fragment; source range request is capped.

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <output_csv>" >&2
  exit 64
fi

output_csv="$1"
output_dir="$(dirname "$output_csv")"
mkdir -p "$output_dir"
tmp_file="${output_csv}.range.tmp"
headers_file="${output_csv}.headers.txt"

cleanup() {
  rm -f "$tmp_file"
}
trap cleanup EXIT

curl --fail --silent --show-error --location \
  --range "0-${MAX_BYTES}" \
  --dump-header "$headers_file" \
  "$SOURCE_URL" \
  --output "$tmp_file"

if ! grep -qi '^content-range:' "$headers_file"; then
  echo "Server did not honour the bounded range request; refusing to retain content." >&2
  exit 65
fi

# Preserve the header plus at most 1,000 complete metadata records. No partial final row is retained.
{ head -n 1001 "$tmp_file" || true; } > "$output_csv"
if [[ $(tail -c 1 "$output_csv" | wc -l) -eq 0 ]]; then
  sed -i '$d' "$output_csv"
fi

printf 'Bounded metadata-only review input created: %s\n' "$output_csv"
printf 'Rows including header: %s\n' "$(wc -l < "$output_csv")"
printf 'Media downloads: 0\nEmbeddings generated: 0\nModel training: 0\n'
