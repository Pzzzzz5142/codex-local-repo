# Repackages OpenAI's official Linux desktop distribution (includes Codex).
pkgname=chatgpt-desktop-bin
pkgver=26.915.31945
pkgrel=1
pkgdesc='Official ChatGPT desktop application with Codex, repackaged for Arch Linux'
arch=('x86_64')
url='https://learn.chatgpt.com/docs/linux/linux-app'
license=('custom')
depends=('alsa-lib' 'at-spi2-core' 'cairo' 'libcups' 'dbus' 'expat' 'gcc-libs'
         'gdk-pixbuf2' 'glib2' 'glibc' 'gtk3' 'libdrm' 'libglvnd' 'libnotify'
         'libusb' 'libx11' 'libxcb' 'libxcomposite' 'libxdamage' 'libxext'
         'libxfixes' 'libxkbcommon' 'libxrandr' 'mesa' 'nspr' 'nss' 'pango'
         'systemd-libs' 'openssl' 'tpm2-tss' 'vulkan-icd-loader' 'xdg-utils' 'xz')
optdepends=('git: Git integration' 'gnome-keyring: secret storage'
            'libpulse: PulseAudio support' 'xorg-xwayland: run under Wayland')
provides=("chatgpt=$pkgver")
conflicts=('chatgpt' 'chatgpt-bin')
options=('!strip' '!debug')
source=('chatgpt_26.915.31945_amd64.deb::https://persistent.oaistatic.com/codex-app-prod/linux/deb/pool/main/c/chatgpt/chatgpt_26.915.31945_amd64.deb')
sha256sums=('d27a9c02919cfe484dcc5f34584b9ea9fd0d7a65c69dcc872b5bdcfa0efb5983')

package() {
    # Extract only the application payload. Debian maintainer scripts are not run.
    bsdtar -xf data.tar.* -C "$pkgdir" ./usr
    rm -rf "$pkgdir/usr/share/lintian"
    install -Dm644 "$pkgdir/usr/share/doc/chatgpt/copyright" \
        "$pkgdir/usr/share/licenses/$pkgname/copyright"
    test -x "$pkgdir/usr/lib/chatgpt/ChatGPT"
    test -e "$pkgdir/usr/share/applications/chatgpt.desktop"
    test "$(readlink "$pkgdir/usr/bin/chatgpt")" = '../lib/chatgpt/codex-launcher'
}
