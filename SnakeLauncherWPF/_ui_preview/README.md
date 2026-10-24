# 贪吃蛇启动器 v6.0.0 · 鹰角式 UI

参考《明日方舟 / 终末地 / 泡姆泡姆》启动器布局重绘窗口外壳，并包含：
**一键下载安装**、**浅色模式**、**GitHub 版本资讯 / 每个版本的更新说明**、**自定义启动器背景（图片 / 视频）**、
**大圆角无边框窗口（R=32）与启动渐入 / 关闭渐出动画**。

> 当前程序集版本：**6.0.0**（启动画面、关于页、设置页底部版本号均读取程序集版本）。

## 窗口动效

- **直接启动**：不再显示启动画面、**没有 3 秒等待**，主窗口在启动时立即创建（实测约 0.8 秒可见）；
- **大 R 角**：主窗口外壳与整窗裁剪半径 22 → **32**（启动画面 22 → 28），配合无边框 + 外层软阴影；
- **启动渐入**：窗口在构造时先设为透明，加载后整体 `Opacity 0 → 1`，**1 秒** CubicEase.EaseOut（不会先闪现再淡入）；
- **关闭渐出**：点击 X / Alt+F4 / 任务栏关闭时先播放 **1 秒**淡出，再真正关闭并保存窗口尺寸与配置；
  淡出过程中重复点击不会重入；系统关闭动画或窗口最小化时直接关闭。
- **左侧导航栏半透明**：深色 `#BF0E0E11` / 浅色 `#C4FFFFFF`，自定义图片或视频背景会从导航栏后透出。
- **左右分栏（参考鹰角启动器）**：左侧导航栏与右侧内容区为两个独立圆角面板——四周与两者之间统一留 **12px**（与窗口边框同宽），内面板圆角 R=20、窗口外框 R=32（同心），主视觉 / 自定义背景只在内容面板内显示并圆角裁剪。

## 预览

| 文件 | 内容 |
| --- | --- |
| `01-home.png` | 深色首页 |
| `02-settings.png` | 设置弹窗 |
| `03-version-library.png` | 版本库抽屉 |
| `04-version-detail.png` | 本机版本详情 |
| `05-splash.png` | 启动画面（已停用：现在启动不再显示启动画面） |
| `06-home-en.png` | 英文界面 |
| `07-stats.png` / `08-download.png` / `09-about.png` | 数据 / 下载 / 关于（v6.0.0） |
| `10-download-game-state.png` | 无游戏：按钮变「下载游戏」 |
| `11-downloading.png` | 自动下载进度 |
| `12-installed.png` | 自动安装完成 |
| `13-light-home.png` / `14-light-settings.png` / `15-light-library.png` | 浅色模式 |
| `16-home-release-feed.png` | 版本资讯/公告（GitHub 两个仓库） |
| `17-release-notes.png` | 版本资讯与更新说明面板 |
| `18-news-beta.png` | 「新闻」页签：仅预发布 |
| `19-release-notes-python.png` | Python 版本详情（无说明占位） |
| `20-custom-background-image.png` | **自定义背景：图片** |
| `21-settings-background.png` | **设置中的「启动器背景」** |
| `22-custom-background-video.png` | **自定义背景：视频**（静音循环） |
| `23-light-video-no-filter.png` | 浅色视频背景（已去掉白色滤镜） |
| `24-rail-translucent.png` | 左侧导航栏半透明 |
| `25-separated-panels.png` | **左右分栏**：独立导航栏 + 独立内容面板（深色） |
| `26-light-separated-panels.png` | 左右分栏（浅色 + 自定义背景） |

## 自定义启动器背景（图片 / 视频）

位置：右上角 ⚙ 设置 → **启动器背景**

- **选择图片…**：PNG / JPG / JPEG / BMP / GIF / TIF；按 `UniformToFill` 铺满窗口并自动裁切；
- **选择视频…**：MP4 / WMV / AVI / MOV / M4V；`MediaPlayer + VideoDrawing` 渲染（兼容无边框圆角透明窗口），**静音、自动循环**，窗口最小化时暂停、恢复时继续；
- **恢复默认背景**：回到默认主视觉（蛇形光带 + 山脉）；
- 选择立即生效并写入 `launcher_config.json`（`BackgroundType`: none/image/video，`BackgroundPath`）；
- **自定义背景不叠加任何白色滤镜 / 压暗层，视频与图片保持原色**；只有默认主视觉使用可读性遮罩；
- 启动时自动应用；文件缺失/视频解码失败时自动回退默认主视觉并提示；
- 图片与视频都叠加可读性压暗层与明暗渐变，浅色/深色主题下 UI 均可读。

## 版本资讯 / 公告 / 更新说明

数据源（`GitHubReleaseService.Repos`）：

- **C# / Unity 版**：https://github.com/MEIMAOA/SnakeGame/releases
- **Python 版**：https://github.com/MEIMAOA/Snake-Game-Python-Edition-/releases

- 启动后后台拉取两个仓库全部发行版并按发布时间倒序合并（10 分钟缓存，工具栏刷新可强制重拉）；
- 首页「版本资讯」卡显示最新发行版（`v9.1.0-beta · C# / Unity 版 · 10/24`）；
- 公告面板三个页签：**公告**（全部发行版，含平台标记 C#/PY 与预发布标记）、**新闻**（仅预发布）、**资讯**（本机已安装版本）；
- 点击任意版本或「更多 ›」打开**版本资讯与更新说明面板**：左侧全部版本、右侧 Markdown 渲染的 Release Notes，并可跳转 GitHub。

## 一键下载并安装最新版

无游戏时开始按钮变为「下载游戏」，副标题显示本机架构；点击后自动：正式版优先 → 按架构选 Windows 包 → 下载（按钮内百分比）→ 校验 → 解压 → 扫描 → 恢复「开始游戏」。

命名兼容：

```
SnakeGame-9.1.0-beta-Windows64.zip / Windows32.zip / Android.apk
SnakeGame-v9.0.0-Windows64.zip / Windows32.zip
SnakeGameWpf_8.0.0.0.zip、SnakeGame_1.1.0.zip
```

架构策略：32 位 → Windows32/x86；64 位 → Windows64/x64（可回退 32 位）；ARM64 → ARM64 → x64 → x86；Android/apk 在 Windows 端被过滤。

## 浅色模式

外壳与主视觉独立色板（`ApplyShellTheme`）：深色 = 深墨底 + 白字 + 青色光带；浅色 = 珍珠白 + 墨色字 + 柔和蓝灰山体。
包含版本资讯面板、通知、详情、自定义背景压暗层在内均随主题切换（设置 → 主题模式 → 浅色，保存后自动重启）。

## 构建与运行

```powershell
cd E:\KernelDeleteDriver\SnakeLauncherWPF
dotnet build SnakeLauncherWPF.csproj -c Release
.\bin\Release\net10.0-windows\SnakeLauncherWPF.exe
```

最小窗口尺寸 **1260 × 700**；配置文件为 exe 同目录的 `launcher_config.json`。

> 截图说明：自定义背景与版本资讯截图使用独立配置的测试实例采集，未改动你本机的配置。
