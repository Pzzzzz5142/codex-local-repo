#!/usr/bin/env bash
# Run as root inside archlinux:base-devel, with the checkout mounted at /work.
set -euo pipefail
cd /work
pacman-key --init
pacman-key --populate archlinux
pacman -Syu --noconfirm --needed git python sudo
id builder &>/dev/null || useradd -m builder
printf 'builder ALL=(ALL) NOPASSWD: /usr/bin/pacman\n' > /etc/sudoers.d/builder
# Build in a disposable directory, leaving mounted checkout ownership unchanged.
install -d -o builder -g builder /build
cp PKGBUILD /build/
if [[ -d .cache ]]; then
    find .cache -maxdepth 1 -name 'chatgpt_*.deb' -exec cp '{}' /build/ \;
fi
chown -R builder:builder /build
cd /build
runuser -u builder -- makepkg --syncdeps --noconfirm --cleanbuild
runuser -u builder -- makepkg --printsrcinfo > /work/.SRCINFO
mapfile -t packages < <(runuser -u builder -- makepkg --packagelist)
names=("${packages[@]##*/}")
mkdir -p /work/out
cp "${packages[@]}" /work/out/
cd /work/out
repo-add codex-local.db.tar.gz "${names[@]}"
# Release assets must be real files, not repo-add symlinks.
cp --remove-destination codex-local.db.tar.gz codex-local.db
cp --remove-destination codex-local.files.tar.gz codex-local.files
sha256sum "${names[@]}" > SHA256SUMS
