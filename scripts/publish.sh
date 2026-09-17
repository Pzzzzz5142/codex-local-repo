#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if ! gh release view arch-repo >/dev/null 2>&1; then
    gh release create arch-repo --target "$GITHUB_SHA" \
        --title 'Arch Linux repository (x86_64)' \
        --notes 'Official OpenAI Linux desktop, repackaged for Arch. See the repository README for pacman/yay setup.'
fi
# Retain previous package assets so clients holding an older database still work.
# Never silently overwrite a package under the same version: bump pkgrel instead.
for package in out/*.pkg.tar.zst; do
    name=$(basename "$package")
    url=$(gh release view arch-repo --json assets --jq ".assets[] | select(.name == \"$name\") | .url")
    if [[ -n "$url" ]]; then
        directory=$(mktemp -d)
        gh release download arch-repo --pattern "$name" --dir "$directory"
        # Rebuild timestamps can differ. Keep the previously published package.
        cp "$directory/$name" "$package"
        rm -rf "$directory"
    else
        gh release upload arch-repo "$package"
    fi
done
# Rebuild database from the actual published bytes, including retried releases.
docker run --rm -v "$PWD/out:/repo" -w /repo archlinux:base-devel bash -c '
  set -euo pipefail
  rm -f codex-local.db* codex-local.files*
  repo-add codex-local.db.tar.gz ./*.pkg.tar.zst
  cp --remove-destination codex-local.db.tar.gz codex-local.db
  cp --remove-destination codex-local.files.tar.gz codex-local.files
  sha256sum ./*.pkg.tar.zst > SHA256SUMS
'
gh release upload arch-repo out/PKGBUILD out/.SRCINFO out/upstream.json out/SHA256SUMS --clobber
gh release upload arch-repo out/codex-local.files out/codex-local.files.tar.gz --clobber
gh release upload arch-repo out/codex-local.db.tar.gz --clobber
gh release upload arch-repo out/codex-local.db --clobber
# Completion markers are written only after the database is fully published.
# A later scheduled run retries any publication interrupted before this point.
for package in out/*.pkg.tar.zst; do
    sha256sum "$package" > "$package.ready"
    gh release upload arch-repo "$package.ready" --clobber
done
