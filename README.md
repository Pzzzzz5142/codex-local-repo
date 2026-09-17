# Codex local repo

将 OpenAI 官方 Linux 桌面版 `.deb` 重打包为 Arch 软件包，自动跟踪官方稳定版。
官方当前将桌面产品命名为 **ChatGPT**，其中包含 Codex；因此包名为
`chatgpt-desktop-bin`，启动命令为 `chatgpt`。这个仓库不是 Codex CLI 的 Rust 构建。

## 已实现的 CI

- Push / PR：工作流静态检查、更新脚本测试、Arch Docker 构建和安装验证。
- 每小时 / 手动触发：读取官方稳定版 APT 索引，有更新时构建并发布。
- 验证固定公钥签署的 `InRelease` → `Packages` SHA256 → `.deb` SHA256。
- 同一 APT 索引存在多个版本时自动选择数字版本最高的稳定版。
- 无更新时跳过 Docker 构建，发布中断则在下一轮检查自动重试。
- 固定版本下载地址；拒绝版本回退、同版本文件被替换、意外包名或架构变化。
- 在官方 `archlinux:base-devel` 容器内以普通用户运行 `makepkg`。
- 在另一个干净 Arch 容器里通过 `pacman` 安装生成的仓库，检查文件、动态库、
  desktop 文件，再使用 Xvfb 进行无账号的 GUI 启动测试。
- 测试通过后向 GitHub Release `arch-repo` 上传 Arch 包和 `repo-add` 数据库，
  并提交更新后的 `PKGBUILD`、`.SRCINFO`、`upstream.json`。
- 包先上传，数据库最后上传；保留旧包，便于已有旧数据库的客户端下载。
- PR 没有发布权限；发布 job 才具有 `contents: write`。Dependabot 每周检查 Actions。

当前只构建 **x86_64**。官方有 ARM64 `.deb`，但本仓库尚未添加 Arch Linux ARM 验证。

## 放到 GitHub

在此目录创建自己的 GitHub 仓库并推送 `main`，然后在 Actions 手动运行
**Build and publish Arch repository**，或等待 push 自动运行。
不需要额外 PAT，也不需要 GitHub Pages；使用内置 `GITHUB_TOKEN` 发布 Release。

```bash
git add .
git commit -m 'Add official desktop Arch packaging and CI'
git remote add origin git@github.com:OWNER/codex-local-repo.git
git push -u origin main
```

仓库需要允许 Actions 写入内容。如果 `main` 的保护规则禁止机器人直接提交，
发布后的自动提交会失败，需要允许该机器人更新这三个包元数据文件，或自行改为 PR 流程。
GitHub 定时任务只在默认分支运行；公共仓库长期无活动可能被 GitHub 暂停定时任务。

## 用 yay / pacman 安装

本项目的公开仓库为 [Pzzzzz5142/codex-local-repo](https://github.com/Pzzzzz5142/codex-local-repo)。
GitHub Actions 自动构建并把包、数据库发布到固定的 `arch-repo` Release。
本机无需 `gh` 登录，也无需手动下载或同步文件。

首次 CI 发布成功后，在 `/etc/pacman.conf` 末尾添加一次：

```ini
[codex-local]
SigLevel = Optional
Server = https://github.com/Pzzzzz5142/codex-local-repo/releases/download/arch-repo
```

```bash
yay -Syu chatgpt-desktop-bin
# 后续跟随正常系统更新
yay -Syu
```

这是 pacman 自定义二进制仓库，yay 会自动使用它；仅把 PKGBUILD 放到 GitHub
不会让 `yay -S` 在 AUR 中找到它。也可直接在本地 `makepkg -si`。

当前输出的 Arch 包和数据库**未签名**，`SigLevel = Optional` 仅应用于此仓库；
上游输入的 GPG/SHA256 校验并不等同于 Arch 包签名。下载依赖 GitHub HTTPS 的可信性。
不要修改全局 SigLevel。若以后用于多人分发，可以再配置自己的 pacman 签名密钥。

## 本地复现 CI

需要 Docker，并能下载 Arch 镜像及官方 `.deb`（约 400 MB，解包约 1.3 GB）。
更新元数据另需 Python 3、curl 和 gpgv。

```bash
python scripts/update.py
python -m unittest discover -s tests -v
docker run --rm -v "$PWD:/work" -w /work archlinux:base-devel bash scripts/build.sh
docker run --rm -v "$PWD:/work:ro" -w /work archlinux:base-devel bash scripts/verify.sh
```

产物在 `out/`。构建容器会以 root 身份写入该目录和 `.SRCINFO`，需要时执行：

```bash
sudo chown -R "$(id -u):$(id -g)" out .SRCINFO
```

也可以把它作为本地源：

```ini
[codex-local]
SigLevel = Optional
Server = file:///绝对路径/codex-local-repo/out
```

## 自动跟进的边界

正常的新版本无需手改版本号或 SHA256：每小时检查，验证成功后自动发布，
客户端在 `yay -Syu` 时更新。GitHub 调度可能延迟，并非实时推送；本仓库不在客户端
安装自动执行系统升级的定时器。

上游换签名密钥、改安装路径或新增未覆盖的系统依赖时，需要一次维护；
CI 会阻止有问题的新包替换可用版本，下次定时运行会再次尝试。
例如 26.911.61220 新增 OpenSSL/TPM 依赖，本次已补上 `openssl` 与 `tpm2-tss`。

## 维护约定

- 修改打包方式、依赖或安装文件时递增 `PKGBUILD` 的 `pkgrel`。
  同名已发布包会被保留，重复运行不会覆盖它；新版本自动将 `pkgrel` 重置为 1。
- `upstream.json` 记录实际下载来源、版本、依赖和校验值。
- `.SRCINFO` 由 `makepkg --printsrcinfo` 生成，不手写。
- 公钥 `keys/openai-linux.gpg` 来自校验后的官方 `.deb` 的 `postinst`，指纹为
  `3BFA0E4AE8B8CC16A2D9BA684A3B4A566C4660E4`。上游换钥时需要核实后更新。
- 不执行 Debian 安装脚本，不配置 APT，也不安装仅用于 Debian/Ubuntu 的 AppArmor 文件。
- 保留上游 Electron、资源、许可说明和桌面入口，不覆盖系统 `codex` 命令。
- GUI CI 为无账号 Xvfb 启动检查，不能代替实际登录、Wayland 或完整功能验证。
  `--no-sandbox` 只用于 Docker 内的 smoke test，不写入安装后的启动器。
- GitHub Release 的旧包会持续保留；需要时手动清理确定不再使用的旧版本。

## 调研来源

最近核对日期：2026-09-17。当时官方 APT 包：`chatgpt 26.911.61220`。
实时跟踪的版本以 `PKGBUILD` 和 `upstream.json` 为准。

- [官方 Linux 桌面安装与更新文档](https://learn.chatgpt.com/docs/linux/linux-app)：
  提供 Debian/Ubuntu `.deb`、Fedora `.rpm`，支持 x64/ARM64；Arch 不在正式支持列表中。
- [官方 APT 索引](https://persistent.oaistatic.com/codex-app-prod/linux/deb/dists/stable/main/binary-amd64/Packages)：
  版本、依赖、固定下载路径和 SHA256。
- [官方签名元数据](https://persistent.oaistatic.com/codex-app-prod/linux/deb/dists/stable/InRelease)。
- [Arch 自定义本地仓库](https://wiki.archlinux.org/title/Pacman/Tips_and_tricks#Custom_local_repository)。

本项目是个人打包配置，不是 OpenAI 官方 Arch 仓库；应用与内置组件的许可仍归各自上游。
