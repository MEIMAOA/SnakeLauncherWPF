# v6.0.0.1 — 紧急修复

## 修复
- 修复「仓库文档」面板中鼠标移出 .md 文件行时崩溃的问题：
  - `InvalidCastException: 无法将类型 'GitHubRelease' 的对象强制转换为类型 'System.String'`
  - 原因：文件行 `Tag` 保存的是 `GitHubRepoFile`，鼠标移出时却被强制转换为 `string` 用于与当前文件名比较；
  - 已改为 `(row.Tag as GitHubRepoFile)?.Name` 安全比较。

## 其它
- 版本号：6.0.0.1

## 下载（三架构）
- SnakeLauncherWPF_6.0.0.1-Windows64.zip（Windows x64）
- SnakeLauncherWPF_6.0.0.1-Windows32.zip（Windows x86）
- SnakeLauncherWPF_6.0.0.1-WindowsARM64.zip（Windows on ARM）

以上均为框架依赖发布，解压后运行 SnakeLauncherWPF.exe，需要安装 .NET 10 Desktop Runtime。