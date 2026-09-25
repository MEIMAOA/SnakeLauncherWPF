# Upgrade Options — SnakeLauncherWPF

Assessment: 2 .NET Framework 4.8 classic desktop projects, both non-SDK-style; 7,259 binary-incompatible API findings and 4 package upgrades recommended.

## Strategy

### Upgrade Strategy
Multiple .NET Framework projects require dependency-first migration with validation between project groups.

| Value | Description |
|-------|-------------|
| **Bottom-Up** (selected) | Upgrade leaf projects first, then dependent projects, validating each tier independently. |

## Project Structure

### Project Approach
Both projects are standalone desktop applications without project references, so they will be migrated in place rather than run side-by-side.

| Value | Description |
|-------|-------------|
| **In-place** (selected) | Replace the legacy project format and target framework directly in each desktop project. |
| Multi-targeting | Keep the .NET Framework target alongside the modern target during transition. |

### Package Management
The solution uses legacy packages.config and old-style project files; central package management would add unnecessary migration churn.

| Value | Description |
|-------|-------------|
| **Per-Project (defer CPM to post-migration)** (selected) | Convert package references during SDK-style migration and defer Directory.Packages.props until the solution is stable. |
| Central Package Management | Centralize package versions in Directory.Packages.props during this upgrade. |

## Compatibility

### Unsupported API Handling
The assessment reports many API compatibility findings across the desktop codebase, so complex changes are deferred behind compilable stubs while straightforward replacements are applied inline.

| Value | Description |
|-------|-------------|
| **Defer Complex Changes** (selected) | Apply simple replacements immediately and create tracked resolution work for complex API changes. |
| Fix Inline | Resolve every API change in the same upgrade task. |

### Windows Native APIs
The application uses WPF, Windows Forms, System.Drawing, and native Windows integration and has no stated cross-platform requirement.

| Value | Description |
|-------|-------------|
| **Windows Compatibility Pack** (selected) | Preserve Windows-specific APIs during migration through Microsoft.Windows.Compatibility where required. |
| No Compatibility Pack | Require all Windows-specific API usages to be replaced immediately. |

## Modernization

### Nullable Reference Types
The solution is a large, high-risk migration, so nullable analysis is kept separate from the framework upgrade.

| Value | Description |
|-------|-------------|
| **Leave Disabled** (selected) | Preserve existing null handling and defer nullable adoption to a separate effort. |
| Enable Nullable Reference Types | Enable nullable annotations and resolve resulting warnings during this upgrade. |
