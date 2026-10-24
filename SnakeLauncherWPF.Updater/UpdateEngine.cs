using System;
using System.Diagnostics;
using System.IO;
using System.IO.Compression;
using System.Threading;

namespace SnakeLauncherWPF.Updater
{
    public enum UpdateStage
    {
        WaitingForMainExit,
        CleaningOldBackups,   // ★ 新增
        Extracting,
        BackingUp,
        CopyingFiles,
        Launching,
        Completed
    }

    public class UpdateProgress
    {
        public UpdateStage Stage { get; set; }
        public string Message { get; set; }
        /// <summary>0~100；-1 表示不确定进度（显示"处理中..."）</summary>
        public double Percentage { get; set; } = -1;
    }

    public class UpdateEngine
    {
        public event Action<UpdateProgress> ProgressChanged;
        public string LastError { get; private set; }

        public bool Run(string appDir, string zipPath, string exeName)
        {
            LastError = null;
            string extractDir = null;
            string backupDir = null;

            try
            {
                appDir = appDir.TrimEnd('\\', '/');
                string processName = Path.GetFileNameWithoutExtension(exeName);

                // ========== 1. 等待主程序退出 ==========
                Report(UpdateStage.WaitingForMainExit, "正在等待启动器退出...", -1);
                WaitForProcessExit(processName, 60000);

                // 额外等待，确保文件句柄完全释放
                Thread.Sleep(1500);

                // ========== 1.5 ★ 清理上次更新残留的备份 ==========
                Report(UpdateStage.CleaningOldBackups, "正在清理旧的更新备份...", -1);
                CleanupOldBackups(appDir);

                // ========== 2. 解压 ==========
                Report(UpdateStage.Extracting, "正在解压更新包...", 0);
                extractDir = Path.Combine(Path.GetTempPath(),
                    "SnakeLauncherUpdate_" + Guid.NewGuid().ToString("N").Substring(0, 8));
                Directory.CreateDirectory(extractDir);

                try
                {
                    ZipFile.ExtractToDirectory(zipPath, extractDir);
                }
                catch (Exception ex)
                {
                    LastError = $"解压失败: {ex.Message}";
                    return false;
                }

                // ========== 3. 备份旧文件 ==========
                Report(UpdateStage.BackingUp, "正在备份旧文件...", -1);
                backupDir = Path.Combine(appDir, "_backup_" + DateTime.Now.ToString("yyyyMMdd_HHmmss"));
                Directory.CreateDirectory(backupDir);

                string[] files = Directory.GetFiles(extractDir, "*", SearchOption.AllDirectories);
                int total = files.Length;
                int processed = 0;

                // 备份：只备份将被覆盖的文件
                foreach (string srcFile in files)
                {
                    string relPath = srcFile.Substring(extractDir.Length).TrimStart('\\', '/');
                    string dstFile = Path.Combine(appDir, relPath);
                    if (File.Exists(dstFile))
                    {
                        string backupFile = Path.Combine(backupDir, relPath);
                        string backupSubDir = Path.GetDirectoryName(backupFile);
                        if (!Directory.Exists(backupSubDir))
                            Directory.CreateDirectory(backupSubDir);
                        try { File.Copy(dstFile, backupFile, overwrite: true); }
                        catch { /* 备份单个文件失败不阻塞 */ }
                    }
                }

                // ========== 4. 覆盖新文件 ==========
                Report(UpdateStage.CopyingFiles, "正在替换文件...", 0);
                int skippedUpdaterFiles = 0;
                foreach (string srcFile in files)
                {
                    string relPath = srcFile.Substring(extractDir.Length).TrimStart('\\', '/');
                    string dstFile = Path.Combine(appDir, relPath);

                    string dstSubDir = Path.GetDirectoryName(dstFile);
                    if (!Directory.Exists(dstSubDir))
                        Directory.CreateDirectory(dstSubDir);

                    if (!TryReplaceFile(srcFile, dstFile))
                    {
                        // Updater 自身的 exe/dll 可能正被占用（例如从安装目录启动的旧版本），
                        // 这类文件替换失败时跳过，不能因此让整个启动器更新失败。
                        if (IsUpdaterOwnFile(relPath))
                        {
                            skippedUpdaterFiles++;
                            continue;
                        }

                        // 其它文件（主程序 / 依赖）替换失败则回滚
                        LastError = $"替换文件失败 ({relPath}): 文件可能正被占用";
                        TryRollback(backupDir, appDir);
                        return false;
                    }

                    processed++;
                    double pct = total > 0 ? (processed * 100.0 / total) : 100;
                    Report(UpdateStage.CopyingFiles,
                        $"正在替换文件 ({processed}/{total})...",
                        pct);
                }

                if (skippedUpdaterFiles > 0)
                    Debug.WriteLine($"有 {skippedUpdaterFiles} 个 Updater 自身文件因占用被跳过，主程序已更新");

                // ========== 5. 启动新版本 ==========
                Report(UpdateStage.Launching, "正在启动新版本...", 100);

                string newExePath = Path.Combine(appDir, exeName);
                if (!File.Exists(newExePath))
                {
                    LastError = $"新版本主程序未找到: {newExePath}";
                    TryRollback(backupDir, appDir);
                    return false;
                }

                var psi = new ProcessStartInfo
                {
                    FileName = newExePath,
                    WorkingDirectory = appDir,
                    UseShellExecute = true
                };

                try
                {
                    Process.Start(psi);
                }
                catch (Exception ex)
                {
                    LastError = $"启动新版本失败: {ex.Message}";
                    return false;
                }

                // ========== 6. 清理临时文件（备份目录不删，由新主程序启动时清理） ==========
                TryCleanup(extractDir, zipPath);

                Report(UpdateStage.Completed, "更新完成", 100);
                Thread.Sleep(800);

                return true;
            }
            catch (Exception ex)
            {
                LastError = $"更新器异常: {ex.Message}";
                return false;
            }
        }

        private void Report(UpdateStage stage, string message, double percentage)
        {
            ProgressChanged?.Invoke(new UpdateProgress
            {
                Stage = stage,
                Message = message,
                Percentage = percentage
            });
        }

        /// <summary>判断是否是 Updater 自身的文件（exe/dll/deps/runtimeconfig）。</summary>
        private static bool IsUpdaterOwnFile(string relPath)
        {
            string name = Path.GetFileName(relPath) ?? "";
            return name.StartsWith("SnakeLauncherWPF.Updater", StringComparison.OrdinalIgnoreCase);
        }

        /// <summary>
        /// 替换单个文件：优先直接覆盖；被占用时把旧文件改名后重试，最多 3 次。
        /// </summary>
        private static bool TryReplaceFile(string srcFile, string dstFile)
        {
            for (int attempt = 0; attempt < 3; attempt++)
            {
                try
                {
                    if (File.Exists(dstFile))
                        File.SetAttributes(dstFile, FileAttributes.Normal);
                    File.Copy(srcFile, dstFile, overwrite: true);
                    return true;
                }
                catch { }

                // 被占用：把旧文件重命名为 .old_*，让新文件可以写入
                try
                {
                    if (File.Exists(dstFile))
                    {
                        string oldFile = dstFile + ".old_" + DateTime.Now.ToString("yyyyMMddHHmmssfff");
                        File.SetAttributes(dstFile, FileAttributes.Normal);
                        File.Move(dstFile, oldFile);
                    }
                }
                catch { }

                try
                {
                    if (File.Exists(dstFile))
                        File.SetAttributes(dstFile, FileAttributes.Normal);
                    File.Copy(srcFile, dstFile, overwrite: true);
                    return true;
                }
                catch { }

                Thread.Sleep(300);
            }

            return false;
        }

        private static void WaitForProcessExit(string processName, int maxWaitMs)        {
            int waited = 0;
            const int intervalMs = 300;

            while (waited < maxWaitMs)
            {
                var procs = Process.GetProcessesByName(processName);
                if (procs.Length == 0)
                {
                    foreach (var p in procs) p.Dispose();
                    return;
                }
                foreach (var p in procs) p.Dispose();
                Thread.Sleep(intervalMs);
                waited += intervalMs;
            }

            // 超时后强制结束残留进程
            var remaining = Process.GetProcessesByName(processName);
            foreach (var p in remaining)
            {
                try { p.Kill(); } catch { }
                p.Dispose();
            }
            Thread.Sleep(1000);
        }

        /// <summary>
        /// ★ 新增：清理安装目录里上次更新残留的 _backup_* 和 *.old_*
        /// </summary>
        private static void CleanupOldBackups(string appDir)
        {
            try
            {
                // 1) 清理 _backup_* 目录
                foreach (var dir in Directory.GetDirectories(appDir, "_backup_*"))
                {
                    try
                    {
                        foreach (var f in Directory.GetFiles(dir, "*", SearchOption.AllDirectories))
                        {
                            try { File.SetAttributes(f, FileAttributes.Normal); } catch { }
                        }
                        Directory.Delete(dir, true);
                    }
                    catch { /* 使用中则跳过 */ }
                }

                // 2) 清理 *.old_* 文件
                foreach (var file in Directory.GetFiles(appDir, "*.old_*"))
                {
                    try
                    {
                        File.SetAttributes(file, FileAttributes.Normal);
                        File.Delete(file);
                    }
                    catch { }
                }
            }
            catch { }
        }

        private static void TryRollback(string backupDir, string appDir)
        {
            try
            {
                if (!Directory.Exists(backupDir)) return;
                foreach (string filePath in Directory.GetFiles(backupDir, "*", SearchOption.AllDirectories))
                {
                    string rel = filePath.Substring(backupDir.Length).TrimStart('\\', '/');
                    string dst = Path.Combine(appDir, rel);
                    string dstDir = Path.GetDirectoryName(dst);
                    if (!Directory.Exists(dstDir))
                        Directory.CreateDirectory(dstDir);
                    try { File.Copy(filePath, dst, overwrite: true); } catch { }
                }
            }
            catch { /* 回滚尽力而为 */ }
        }

        /// <summary>
        /// 只清理解压临时目录和 zip，保留 _backup_* 让新主程序启动时清理
        /// </summary>
        private static void TryCleanup(string extractDir, string zipPath)
        {
            try { if (Directory.Exists(extractDir)) Directory.Delete(extractDir, true); } catch { }
            try { if (File.Exists(zipPath)) File.Delete(zipPath); } catch { }
        }
    }
}