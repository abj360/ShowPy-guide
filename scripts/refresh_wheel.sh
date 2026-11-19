#!/usr/bin/env bash
#
# refresh_wheel.sh --- builds the showpy wheel from a ShowPy ref and vendors it into vendor/
#
# Usage: scripts/refresh_wheel.sh <showpy-repository> <ref>
#   <showpy-repository>  a local path or clone URL of the ShowPy repository
#   <ref>                a branch or tag to build, such as v0.3.0
#
# Clones the ref with its tags (the version comes from them), builds the wheel, replaces the
# wheel in vendor/, rewrites vendor/SHA256SUMS, points pyproject.toml at the new file and
# re-locks. Then run the checks and rebuild the PDF.

set -euo pipefail

if [[ $# -ne 2 ]]; then
    echo "E: usage: scripts/refresh_wheel.sh <showpy-repository> <ref>" >&2
    exit 2
fi

source_repo=$1
ref=$2
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

git clone --quiet --branch "$ref" "$source_repo" "$work/showpy"
echo "Building showpy $(git -C "$work/showpy" describe --tags --always)"
uv build --quiet --wheel --out-dir "$work/dist" "$work/showpy"

wheels=("$work"/dist/showpy-*-py3-none-any.whl)
if [[ ${#wheels[@]} -ne 1 ]]; then
    echo "E: expected one wheel, found ${#wheels[@]}" >&2
    exit 1
fi
wheel=$(basename "${wheels[0]}")
version=$(echo "$wheel" | cut -d- -f2)

rm -f "$root"/vendor/showpy-*.whl
mkdir -p "$root/vendor"
cp "${wheels[0]}" "$root/vendor/$wheel"
(cd "$root/vendor" && sha256sum "$wheel" > SHA256SUMS)

sed -i -E \
    -e "s|\"showpy==[^\"]*\"|\"showpy==$version\"|" \
    -e "s|vendor/showpy-[^\"]*\\.whl|vendor/$wheel|" \
    "$root/pyproject.toml"
(cd "$root" && uv lock --quiet)
echo "Vendored $wheel"
cat "$root/vendor/SHA256SUMS"
