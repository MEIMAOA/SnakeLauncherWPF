# v6.0.0.2 — 修复自更新失败

## 修复
- 点击更新后提示「启动更新程序失败: 操作已被用户取消」（Win32 1223）
  - 启动 Updater 改为 `UseShellExecute = false`，避免 SmartScreen 拦截；仅在需要管理员权限（740）时回退 ShellExecute 触发 UAC；
  - 启动前删除临时 `SnakeLauncherWPF.Updater.exe` 的 `Zone.Identifier`（“来自 Internet”标记）。
- 更新到 78% 提示「替换文件失败（SnakeLauncherWPF.Updater.exe）：正由另一进程使用」
  - 更新器替换被占用文件时先重命名为 `.old_时间戳` 再写入，并最多重试 3 次；
  - Updater 自身的 exe/dll 被占用时跳过替换，继续完成主程序更新，不再整体回滚失败。
- 版本号更新至 6.0.0.2（主程序与 Updater 同步）。

## 旧版本升级说明
`v5.2.0.1` 等旧版本内置的更新器本身有缺陷，无法通过自更新修复；请手动下载 `SnakeLauncherWPF_6.0.0.2-Windows*.zip` 解压覆盖安装一次。升级到 6.0.0.2 之后，后续版本可正常自更新。

## 下载（三架构）
- SnakeLauncherWPF_6.0.0.2-Windows64.zip（Windows x64）
- SnakeLauncherWPF_6.0.0.2-Windows32.zip（Windows x86）
- SnakeLauncherWPF_6.0.0.2-WindowsARM64.zip（Windows on ARM）

以上均为框架依赖发布，解压后运行 SnakeLauncherWPF.exe，需要安装 .NET 10 Desktop Runtime。