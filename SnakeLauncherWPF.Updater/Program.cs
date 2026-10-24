using System;
using System.Diagnostics;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Threading;

namespace SnakeLauncherWPF.Updater
{
    internal class Program
    {
        static int Main(string[] args)
        {
            try
            {
                string appDir = GetArg(args, "--app-dir");
                string zipPath = GetArg(args, "--zip");
                string exeName = GetArg(args, "--exe") ?? "SnakeLauncherWPF.exe";

                if (string.IsNullOrWhiteSpace(appDir) || string.IsNullOrWhiteSpace(zipPath))
                {
                    Console.Error.WriteLine("缺少必要参数: --app-dir 或 --zip");
                    return 1;
                }

                if (!File.Exists(zipPath))
                {
                    Console.Error.WriteLine($"更新包不存在: {zipPath}");
                    return 2;
                }

                if (!Directory.Exists(appDir))
                {
                    Console.Error.WriteLine($"应用目录不存在: {appDir}");
                    return 3;
                }

                // 步骤1: 等待主程序完全退出
                WaitForMainProcessExit(exeName);

                // 额外等待，确保文件句柄释放
                Thread.Sleep(1500);

                // 步骤2: 解压到临时目录
                string extractDir = Path.Combine(Path.GetTempPath(),
                    "SnakeLauncherUpdate_" + Guid.NewGuid().ToString("N").Substring(0, 8));
                Directory.CreateDirectory(extractDir);

                try
                {
                    ZipFile.ExtractToDirectory(zipPath, extractDir);
                }
                catch (Exception ex)
                {
                    Console.Error.WriteLine($"解压失败: {ex.Message}");
                    return 4;
                }

                // 步骤3: 备份旧文件 + 覆盖新文件
                string backupDir = Path.Combine(appDir, "_backup_" + DateTime.Now.ToString("yyyyMMdd_HHmmss"));
                Directory.CreateDirectory(backupDir);

                try
                {
                    CopyDirectoryWithBackup(extractDir, appDir, backupDir);
                }
                catch (Exception ex)
                {
                    Console.Error.WriteLine($"替换文件失败: {ex.Message}");
                    // 尝试回滚
                    TryRollback(backupDir, appDir);
                    return 5;
                }

                // 步骤4: 启动新版本
                string newExePath = Path.Combine(appDir, exeName);
                if (File.Exists(newExePath))
                {
                    Process.Start(new ProcessStartInfo
                    {
                        FileName = newExePath,
                        WorkingDirectory = appDir,
                        UseShellExecute = true
                    });
                }
                else
                {
                    Console.Error.WriteLine($"新版本主程序未找到: {newExePath}");
                    return 6;
                }

                // 步骤5: 清理临时文件
                TryCleanup(extractDir, zipPath, backupDir);

                return 0;
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine($"更新器异常: {ex.Message}");
                return 99;
            }
        }

        /// <summary>
        /// 等待指定名称的进程全部退出，最多等待 60 秒
        /// </summary>
        private static void WaitForMainProcessExit(string processName)
        {
            string name = Path.GetFileNameWithoutExtension(processName);
            int waited = 0;
            const int maxWaitMs = 60000;
            const int intervalMs = 500;

            while (waited < maxWaitMs)
            {
                var processes = Process.GetProcessesByName(name);
                if (processes.Length == 0)
                {
                    foreach (var p in processes) p.Dispose();
                    return;
                }

                foreach (var p in processes) p.Dispose();
                Thread.Sleep(intervalMs);
                waited += intervalMs;
            }

            // 超时后强制结束残留进程
            var remaining = Process.GetProcessesByName(name);
            foreach (var p in remaining)
            {
                try { p.Kill(); } catch { }
                p.Dispose();
            }
            Thread.Sleep(1000);
        }

        /// <summary>
        /// 将 sourceDir 中的文件复制到 targetDir，覆盖前备份旧文件到 backupDir
        /// </summary>
        private static void CopyDirectoryWithBackup(string sourceDir, string targetDir, string backupDir)
        {
            Directory.CreateDirectory(targetDir);

            foreach (string dirPath in Directory.GetDirectories(sourceDir, "*", SearchOption.AllDirectories))
            {
                Directory.CreateDirectory(dirPath.Replace(sourceDir, targetDir));
            }

            foreach (string filePath in Directory.GetFiles(sourceDir, "*.*", SearchOption.AllDirectories))
            {
                string relativePath = filePath.Substring(sourceDir.Length).TrimStart('\\', '/');
                string destPath = Path.Combine(targetDir, relativePath);
                string backupPath = Path.Combine(backupDir, relativePath);

                // 备份旧文件
                if (File.Exists(destPath))
                {
                    string backupSubDir = Path.GetDirectoryName(backupPath);
                    if (!Directory.Exists(backupSubDir))
                        Directory.CreateDirectory(backupSubDir);
                    File.Copy(destPath, backupPath, overwrite: true);
                }

                // 覆盖新文件
                string destSubDir = Path.GetDirectoryName(destPath);
                if (!Directory.Exists(destSubDir))
                    Directory.CreateDirectory(destSubDir);

                // 清除只读属性
                if (File.Exists(destPath))
                {
                    try { File.SetAttributes(destPath, FileAttributes.Normal); } catch { }
                }

                File.Copy(filePath, destPath, overwrite: true);
            }
        }

        /// <summary>
        /// 从备份目录回滚
        /// </summary>
        private static void TryRollback(string backupDir, string appDir)
        {
            try
            {
                if (!Directory.Exists(backupDir)) return;
                foreach (string filePath in Directory.GetFiles(backupDir, "*.*", SearchOption.AllDirectories))
                {
                    string relativePath = filePath.Substring(backupDir.Length).TrimStart('\\', '/');
                    string destPath = Path.Combine(appDir, relativePath);
                    string destSubDir = Path.GetDirectoryName(destPath);
                    if (!Directory.Exists(destSubDir))
                        Directory.CreateDirectory(destSubDir);
                    File.Copy(filePath, destPath, overwrite: true);
                }
                Console.WriteLine("已回滚到旧版本");
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine($"回滚也失败了: {ex.Message}");
            }
        }

        /// <summary>
        /// 清理临时文件，保留备份目录以便手动恢复
        /// </summary>
        private static void TryCleanup(string extractDir, string zipPath, string backupDir)
        {
            try { if (Directory.Exists(extractDir)) Directory.Delete(extractDir, true); } catch { }
            try { if (File.Exists(zipPath)) File.Delete(zipPath); } catch { }
            // 备份目录保留，用户可以手动恢复；下次启动时可清理超过 3 份的旧备份
        }

        private static string GetArg(string[] args, string key)
        {
            for (int i = 0; i < args.Length - 1; i++)
            {
                if (args[i].Equals(key, StringComparison.OrdinalIgnoreCase))
                    return args[i + 1];
            }
            return null;
        }
    }
}