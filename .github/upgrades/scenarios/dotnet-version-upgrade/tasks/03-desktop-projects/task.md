# 03-desktop-projects: 将桌面项目升级到 .NET 10 Windows 并修复迁移问题

升级 Tier 1 中的两个项目到 `net10.0-windows`，保留 WPF 与 Windows Forms 支持以及 x86/x64/ARM64 配置。依据评估报告处理主项目约 6,890+ 行、Updater 约 464+ 行的 API 兼容问题；将简单替换直接修复，复杂变更以可编译的临时实现和后续解析记录处理。同步更新评估中建议的包版本，并保持 Nullable 关闭及按项目包管理。

## 研究发现
- 两个项目均已是 SDK-style，目标框架属性位于各自项目文件第 3 行，目前都是 `<TargetFramework>net48</TargetFramework>`，属于单目标框架替换，不应改成 `TargetFrameworks`。
- `SnakeLauncherWPF.csproj` 已声明 `<UseWindowsForms>true</UseWindowsForms>` 和 `<UseWPF>true</UseWPF>`，包含 10 个 PackageReference；保留这些桌面工作负载设置即可支持 WPF/WinForms。
- `SnakeLauncherWPF.Updater.csproj` 已声明 `<UseWPF>true</UseWPF>`，无 NuGet 包引用，保留现有 x86/x64 输出配置。
- 评估报告显示主项目有 6,802 个二进制不兼容、67 个源代码不兼容和 21 个行为变化发现；Updater 有 457 个二进制不兼容、3 个源代码不兼容和 4 个行为变化发现。迁移先验证 TFM 和还原，随后根据实际编译错误处理简单替换，复杂变更必须记录。
- 评估建议将 `Microsoft.Bcl.AsyncInterfaces`、`System.IO.Pipelines`、`System.Text.Encodings.Web` 和 `System.Text.Json` 从 10.0.8 升级到 10.0.12；包版本升级与本次目标框架替换分开验证，避免掩盖 TFM 问题。

**完成标准**: 两个项目均以 `net10.0-windows` 作为目标框架，包还原成功；简单 API 迁移完成，复杂变更均有明确跟踪项；项目编译错误已解决且无新增警告。
