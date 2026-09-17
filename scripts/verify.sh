#!/usr/bin/env bash
# A separate clean Arch container installs through the generated repository.
set -euo pipefail
# The Docker image omits documentation by default; verify the complete package.
sed -i '/^NoExtract[[:space:]]*=/d' /etc/pacman.conf
pacman-key --init
pacman-key --populate archlinux
pacman -Syu --noconfirm
cat >> /etc/pacman.conf <<'CONFIG'

[codex-local]
SigLevel = Optional
Server = file:///work/out
CONFIG
pacman -Syu --noconfirm chatgpt-desktop-bin
pacman -S --noconfirm --needed desktop-file-utils xorg-server-xvfb
expected_version=$(awk '$1 == "pkgver" {v=$3} $1 == "pkgrel" {r=$3} END {print v "-" r}' /work/.SRCINFO)
installed_version=$(pacman -Q chatgpt-desktop-bin | cut -d ' ' -f2)
test "$installed_version" = "$expected_version"
pacman -Qkk chatgpt-desktop-bin
sh -n /usr/lib/chatgpt/codex-launcher
libraries=$(ldd /usr/lib/chatgpt/ChatGPT)
printf '%s\n' "$libraries"
if [[ "$libraries" == *'not found'* ]]; then exit 1; fi
desktop-file-validate /usr/share/applications/chatgpt.desktop
test -x /usr/bin/chatgpt
test ! -e /etc/apt/sources.list.d/chatgpt.sources
useradd -m smoke
# The Docker runner cannot provide the production desktop sandbox. Only this
# isolated, credential-free smoke test disables it; no installed launcher does.
set +e
timeout 20s runuser -u smoke -- xvfb-run -a chatgpt --no-sandbox --disable-gpu \
    > /tmp/chatgpt-smoke.log 2>&1
result=$?
set -e
cat /tmp/chatgpt-smoke.log
# Staying alive until timeout is the expected result for the GUI event loop.
test "$result" -eq 124
