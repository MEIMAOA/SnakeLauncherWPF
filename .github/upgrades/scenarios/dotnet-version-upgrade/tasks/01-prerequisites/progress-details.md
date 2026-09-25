# 任务 01 进度

## 完成内容
- 验证 .NET SDK 10.0.401、MSBuild 18.9.11 和 Windows Desktop runtime 10.0.12 已安装。
- 确认仓库没有 global.json。
- 确认解决方案包含根目录主项目及相邻目录 Updater 项目；两个项目均为 net48 旧式项目、无项目引用。
- 确认主项目使用 packages.config，Updater 无 NuGet 包引用；两个项目均需要使用 Visual Studio MSBuild 处理 WPF/XAML。

## 验证结果
- SDK 兼容性验证：通过。
- 升级前解决方案构建：未通过，失败位置为 `MarkdownRenderer.cs`，原因是项目配置 C# 7.3，而代码使用 C# 8 switch expression（CS8370）。该问题已记录，将在后续 SDK-style/TFM 迁移任务中处理。
- 测试：未发现独立测试项目。

## 修改文件
- `.github/upgrades/scenarios/dotnet-version-upgrade/scenario-instructions.md`
- `.github/upgrades/scenarios/dotnet-version-upgrade/tasks/01-prerequisites/task.md`
- `.github/upgrades/scenarios/dotnet-version-upgrade/tasks/01-prerequisites/progress-details.md`
