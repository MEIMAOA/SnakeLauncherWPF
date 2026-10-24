# v6.0.0 — 鹰角风格 UI 重构 / 直接启动 / 自定义背景

## 界面
- 参考鹰角网络启动器重新布局：无边框大 R 角窗口（R=32），左侧独立导航栏与右侧内容面板由 12px 窗口边框带分隔，无描边线条
- 左侧导航栏半透明（深色 / 浅色主题分别适配）
- 移除启动画面与 3 秒等待：直接启动；启动 1 秒渐入、关闭 1 秒渐出
- 完整支持浅色模式与主题切换

## 功能
- 一键下载安装：未检测到游戏时按钮变为「下载游戏」，自动获取最新发布版并安装
  - 自动识别 x64 / x86 / ARM64
  - 适配 `SnakeGame-X.X.X-beta-系统（Windows32 / Windows64 / Android）.zip / .apk`
- 版本资讯 / 公告 / 更新说明：接入 `MEIMAOA/SnakeGame` 与 `MEIMAOA/Snake-Game-Python-Edition-` 的 GitHub Releases
- 自定义启动器背景：图片或视频（静音循环、最小化暂停），不叠加白色滤镜
- 版本库、详情、打开目录、删除版本；启动 / 停止 / IPC 实时状态
- 多语言：简体中文 / English / Deutsch / Français / Русский

## 技术
- 升级至 .NET 10（net10.0-windows），版本号 6.0.0
- 程序集版本：6.0.0.0

## 下载
- `SnakeLauncherWPF-v6.0.0-win-x64.zip`：解压后运行 `SnakeLauncherWPF.exe`（需 .NET 10 Desktop Runtime）
## 下载（三架构）
- SnakeLauncherWPF_6.0.0-Windows64.zip（Windows x64）
- SnakeLauncherWPF_6.0.0-Windows32.zip（Windows x86）
- SnakeLauncherWPF_6.0.0-WindowsARM64.zip（Windows on ARM）

以上均为框架依赖发布，解压后运行 SnakeLauncherWPF.exe，需要安装 .NET 10 Desktop Runtime。