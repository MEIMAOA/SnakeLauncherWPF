using System;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;
using System.Windows;
using System.Windows.Media;

namespace SnakeLauncherWPF.Updater
{
    public partial class App : System.Windows.Application
    {
        protected override void OnStartup(StartupEventArgs e)
        {
            base.OnStartup(e);

            // 全局异常兜底
            DispatcherUnhandledException += (s, ex) =>
            {
                System.Windows.MessageBox.Show(
                    $"更新程序异常:\n{ex.Exception.Message}",
                    "错误",
                    System.Windows.MessageBoxButton.OK,
                    System.Windows.MessageBoxImage.Error);
                ex.Handled = true;
                Shutdown(1);
            };

            // ★ 根据参数 + 配置文件应用主题
            ApplyTheme(e.Args);

            var window = new MainWindow(e.Args);
            MainWindow = window;
            window.Show();
        }

        /// <summary>
        /// 应用主题：
        ///   1) 先读 --app-dir 下的 launcher_config.json（优先）
        ///   2) 读不到则用命令行参数 --theme / --accent
        ///   3) 都没有则用默认浅色 + 蓝色
        /// </summary>
        private static void ApplyTheme(string[] args)
        {
            // 默认值
            string theme = "light";
            string accentHex = "#0078d4";

            // ========== 1) 命令行参数（作为兜底） ==========
            string argTheme = GetArg(args, "--theme");
            string argAccent = GetArg(args, "--accent");
            if (!string.IsNullOrWhiteSpace(argTheme))
                theme = argTheme;
            if (!string.IsNullOrWhiteSpace(argAccent))
                accentHex = argAccent;

            // ========== 2) 配置文件优先 ==========
            string appDir = GetArg(args, "--app-dir");
            if (!string.IsNullOrWhiteSpace(appDir))
            {
                try
                {
                    string configPath = Path.Combine(appDir.TrimEnd('\\', '/'), "launcher_config.json");
                    if (File.Exists(configPath))
                    {
                        // 用 FileShare.ReadWrite 允许其他进程同时读
                        string json;
                        using (var fs = new FileStream(configPath, FileMode.Open, FileAccess.Read,
                            FileShare.ReadWrite, 4096, FileOptions.SequentialScan))
                        using (var sr = new StreamReader(fs, Encoding.UTF8))
                        {
                            json = sr.ReadToEnd();
                        }

                        string cfgTheme = ExtractJsonString(json, "ThemeMode");
                        string cfgAccent = ExtractJsonString(json, "AccentColor");

                        if (!string.IsNullOrWhiteSpace(cfgTheme))
                            theme = cfgTheme;
                        if (!string.IsNullOrWhiteSpace(cfgAccent))
                            accentHex = cfgAccent;
                    }
                }
                catch
                {
                    // 读配置失败，保持使用命令行参数或默认值
                }
            }

            // ========== 3) 应用主题 ==========
            Color accent;
            try
            {
                accent = (Color)ColorConverter.ConvertFromString(accentHex);
            }
            catch
            {
                accent = Color.FromRgb(0x00, 0x78, 0xD4);
            }

            var resources = Current.Resources;

            // 强调色
            resources["AccentBrush"] = new SolidColorBrush(accent);
            resources["ProgressFillBrush"] = new SolidColorBrush(accent);

            // 根据强调色亮度自动选黑/白前景色
            double luminance = (0.299 * accent.R + 0.587 * accent.G + 0.114 * accent.B) / 255.0;
            Color btnFore = luminance > 0.6 ? Colors.Black : Colors.White;
            resources["PrimaryButtonForegroundBrush"] = new SolidColorBrush(btnFore);

            if (theme.Equals("dark", StringComparison.OrdinalIgnoreCase))
            {
                // ================= 深色 =================
                resources["TitleForegroundBrush"] = new SolidColorBrush(Color.FromRgb(0xF0, 0xF0, 0xF0));
                resources["SubtitleForegroundBrush"] = new SolidColorBrush(Color.FromRgb(0xA0, 0xA0, 0xA0));
                resources["StatusForegroundBrush"] = new SolidColorBrush(Color.FromRgb(0xE0, 0xE0, 0xE0));
                resources["PercentForegroundBrush"] = new SolidColorBrush(Color.FromRgb(0xA0, 0xA0, 0xA0));
                resources["ErrorForegroundBrush"] = new SolidColorBrush(Color.FromRgb(0xFF, 0x6B, 0x6B));

                resources["ProgressTrackBrush"] = new SolidColorBrush(Color.FromArgb(0x28, 0xFF, 0xFF, 0xFF));
                resources["ProgressFillBrush"] = new SolidColorBrush(accent);

                resources["SecondaryButtonBackgroundBrush"] = new SolidColorBrush(Color.FromArgb(0x28, 0xFF, 0xFF, 0xFF));
                resources["SecondaryButtonForegroundBrush"] = new SolidColorBrush(Color.FromRgb(0xE0, 0xE0, 0xE0));

                var darkBg = new LinearGradientBrush { StartPoint = new Point(0, 0), EndPoint = new Point(1, 1) };
                darkBg.GradientStops.Add(new GradientStop(Color.FromArgb(0xF0, 0x22, 0x24, 0x2E), 0));
                darkBg.GradientStops.Add(new GradientStop(Color.FromArgb(0xE6, 0x1C, 0x1E, 0x28), 0.55));
                darkBg.GradientStops.Add(new GradientStop(Color.FromArgb(0xDD, 0x16, 0x18, 0x20), 1));
                darkBg.Freeze();
                resources["GlassBackgroundBrush"] = darkBg;

                var darkBorder = new LinearGradientBrush { StartPoint = new Point(0, 0), EndPoint = new Point(0, 1) };
                darkBorder.GradientStops.Add(new GradientStop(Color.FromArgb(0x45, 0xFF, 0xFF, 0xFF), 0));
                darkBorder.GradientStops.Add(new GradientStop(Color.FromArgb(0x12, 0xFF, 0xFF, 0xFF), 1));
                darkBorder.Freeze();
                resources["GlassBorderBrush"] = darkBorder;

                resources["ShadowColor"] = Colors.Black;

                resources["Blob1Brush"] = new SolidColorBrush(Color.FromArgb(0x60, 0x5A, 0x9E, 0xFF));
                resources["Blob2Brush"] = new SolidColorBrush(Color.FromArgb(0x60, 0xFF, 0x7E, 0xB0));
            }
            else
            {
                // ================= 浅色 =================
                resources["TitleForegroundBrush"] = new SolidColorBrush(Color.FromRgb(0x1F, 0x1F, 0x1F));
                resources["SubtitleForegroundBrush"] = new SolidColorBrush(Color.FromRgb(0x66, 0x66, 0x66));
                resources["StatusForegroundBrush"] = new SolidColorBrush(Color.FromRgb(0x1F, 0x1F, 0x1F));
                resources["PercentForegroundBrush"] = new SolidColorBrush(Color.FromRgb(0x66, 0x66, 0x66));
                resources["ErrorForegroundBrush"] = new SolidColorBrush(Color.FromRgb(0xD1, 0x34, 0x38));

                resources["ProgressTrackBrush"] = new SolidColorBrush(Color.FromArgb(0x22, 0x00, 0x00, 0x00));
                resources["ProgressFillBrush"] = new SolidColorBrush(accent);

                resources["SecondaryButtonBackgroundBrush"] = new SolidColorBrush(Color.FromArgb(0x22, 0x00, 0x00, 0x00));
                resources["SecondaryButtonForegroundBrush"] = new SolidColorBrush(Color.FromRgb(0x1F, 0x1F, 0x1F));

                var lightBg = new LinearGradientBrush { StartPoint = new Point(0, 0), EndPoint = new Point(1, 1) };
                lightBg.GradientStops.Add(new GradientStop(Color.FromArgb(0xF5, 0xFF, 0xFF, 0xFF), 0));
                lightBg.GradientStops.Add(new GradientStop(Color.FromArgb(0xE0, 0xFF, 0xFF, 0xFF), 0.55));
                lightBg.GradientStops.Add(new GradientStop(Color.FromArgb(0xCC, 0xFF, 0xFF, 0xFF), 1));
                lightBg.Freeze();
                resources["GlassBackgroundBrush"] = lightBg;

                var lightBorder = new LinearGradientBrush { StartPoint = new Point(0, 0), EndPoint = new Point(0, 1) };
                lightBorder.GradientStops.Add(new GradientStop(Color.FromArgb(0xFF, 0xFF, 0xFF, 0xFF), 0));
                lightBorder.GradientStops.Add(new GradientStop(Color.FromArgb(0x30, 0xFF, 0xFF, 0xFF), 1));
                lightBorder.Freeze();
                resources["GlassBorderBrush"] = lightBorder;

                resources["ShadowColor"] = Color.FromRgb(0x1A, 0x2A, 0x44);

                resources["Blob1Brush"] = new SolidColorBrush(Color.FromArgb(0x55, 0x77, 0xC4, 0xFF));
                resources["Blob2Brush"] = new SolidColorBrush(Color.FromArgb(0x55, 0xFF, 0xA8, 0xC4));
            }
        }

        /// <summary>
        /// 从 JSON 文本中提取简单字符串字段的值（不依赖 JSON 库）
        /// 匹配格式：  "key" : "value"
        /// </summary>
        private static string ExtractJsonString(string json, string key)
        {
            if (string.IsNullOrWhiteSpace(json) || string.IsNullOrWhiteSpace(key))
                return null;

            try
            {
                var pattern = "\"" + Regex.Escape(key) + "\"\\s*:\\s*\"([^\"]*)\"";
                var m = Regex.Match(json, pattern, RegexOptions.IgnoreCase);
                if (m.Success)
                    return m.Groups[1].Value;
            }
            catch { }

            return null;
        }

        private static string GetArg(string[] args, string key)
        {
            if (args == null) return null;
            for (int i = 0; i < args.Length - 1; i++)
            {
                if (args[i].Equals(key, StringComparison.OrdinalIgnoreCase))
                    return args[i + 1];
            }
            return null;
        }
    }
}