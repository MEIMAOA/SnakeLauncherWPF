# .NET Version Upgrade Plan

## Overview

**Target**: 将 SnakeLauncherWPF 解决方案从 .NET Framework 4.8 迁移到 .NET 10 Windows 桌面目标。
**Scope**: 2 个非 SDK-style 桌面项目，约 9,232 行代码；主项目包含 WPF、Windows Forms、System.Drawing、旧式配置和 packages.config。

### Selected Strategy
**Bottom-Up (Dependency-First)** — 先处理无项目引用的叶节点项目，再进行解决方案级验证。
**Rationale**: 2 个项目均无项目引用，构成单一依赖层；迁移仍需将 SDK-style 结构转换与 TFM/API 迁移分离，以便在每个结构阶段验证。

**Dependency graph**:

```text
Tier 1: SnakeLauncherWPF.Updater, SnakeLauncherWPF
		 (both have zero project references)
```

**Tier 1 completion criteria**: 两个项目均完成 SDK-style 转换及 `net10.0-windows` 目标框架迁移，包还原成功，解决方案编译无错误且测试（如存在）通过。

## Tasks

### 01-prerequisites: 验证 .NET 10 工具链与升级前基线

确认 .NET 10 SDK、global.json 和解决方案加载状态满足迁移要求，并记录当前两个 .NET Framework 4.8 项目的构建基线。研究主项目的 WPF/WinForms 混合桌面配置、Updater 项目位置及现有包还原方式，确保后续转换不会遗漏项目资产。

**Done when**: .NET 10 SDK 与 SDK 选择验证通过，升级前基线结果已记录，两个项目及其包管理方式已明确。

---

### 02-sdk-style-conversion: 转换两个桌面项目为 SDK-style

将 `SnakeLauncherWPF.csproj` 和 `SnakeLauncherWPF.Updater.csproj` 从旧式 MSBuild 项目转换为 SDK-style，同时保持当前 .NET Framework 4.8 目标以隔离项目结构变化。转换范围包括 packages.config 到 PackageReference、WPF/WinForms 构建属性、资源与 XAML 项目项、平台配置和现有程序集元数据；不得把此任务与 TFM/API 迁移合并。

**Done when**: 两个项目均为 SDK-style、旧式导入和 packages.config 依赖已处理，仍能在当前基线下还原并编译，且资源和 XAML 均被正确识别。

---

### 03-desktop-projects: 将桌面项目升级到 .NET 10 Windows 并修复迁移问题

升级 Tier 1 中的两个项目到 `net10.0-windows`，保留 WPF 与 Windows Forms 支持以及 x86/x64/ARM64 配置。依据评估报告处理主项目约 6,890+ 行、Updater 约 464+ 行的 API 兼容问题；将简单替换直接修复，复杂变更以可编译的临时实现和后续解析记录处理。同步更新评估中建议的包版本，并保持 Nullable 关闭及按项目包管理。

**Done when**: 两个项目均以 `net10.0-windows` 作为目标框架，包还原成功；简单 API 迁移完成，复杂变更均有明确跟踪项；项目编译错误已解决且无新增警告。

---

### 04-solution-validation: 执行完整解决方案验证并记录延期工作

执行完整解决方案还原、构建和可用测试；检查 WPF/WinForms 启动、App.config 替代或兼容策略、System.Drawing/本机 API 行为，以及各发布平台配置。整理复杂 API 解析、CPM 和 Nullable 等明确延期事项，确保最终状态可复现且没有被警告抑制隐藏的问题。

**Done when**: 全解决方案构建无错误且无警告，测试通过（如存在），关键桌面启动路径完成验证，延期事项已记录。
