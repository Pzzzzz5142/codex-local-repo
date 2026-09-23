# Repackages OpenAI's official Linux desktop distribution (includes Codex).
pkgname=chatgpt-desktop-bin
pkgver=26.917.61114
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
source=('chatgpt_26.917.61114_amd64.deb::https://persistent.oaistatic.com/codex-app-prod/linux/deb/pool/main/c/chatgpt/chatgpt_26.917.61114_amd64.deb')
sha256sums=('7bea2eff4a46abe0f28e39ec65eb6e6e51c97bbcdad89d25abe5bec4318955c9')

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
