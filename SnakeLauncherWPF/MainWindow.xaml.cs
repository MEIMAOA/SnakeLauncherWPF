using Microsoft.VisualBasic;
using Microsoft.Win32;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Net.Http;
using System.Reflection;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Controls.Primitives;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Animation;
using System.Windows.Media.Effects;
using System.Windows.Media.Imaging;
using static SnakeLauncherWPF.GitHubReleaseService;

namespace SnakeLauncherWPF
{
    // ========== 配置类 ==========
    public class ConfigData
    {
        public List<string> Directories { get; set; } = new List<string>();
        public int CurrentDirIndex { get; set; } = 0;
        public string ThemeMode { get; set; } = "dark";
        public string AccentColor { get; set; } = "#0078d4";
        public bool ApplyText { get; set; } = false;
        public string WindowSize { get; set; } = "1100x700";
        public string SyncFolder { get; set; } = "";
        public string SaveFolder { get; set; } = "";
        public string UpdateIndexUrl { get; set; } = "http://192.168.190.130:8081/versions.txt";
        public string DownloadPath { get; set; } = "";
        public int WindowWidth { get; set; } = 1100;
        public int WindowHeight { get; set; } = 700;
        public double WindowLeft { get; set; } = double.NaN;
        public double WindowTop { get; set; } = double.NaN;

        public bool AutoCheckUpdate { get; set; } = true;
        public string SkipUpdateVersion { get; set; } = "";
        public DateTime LastUpdateCheck { get; set; } = DateTime.MinValue;

        // ★ 语言
        public string Language { get; set; } = "zh-CN";

        // ★ 自定义启动器背景：none / image / video
        public string BackgroundType { get; set; } = "none";
        public string BackgroundPath { get; set; } = "";
    }

    // ========== 配置管理器 ==========
    public static class ConfigManager
    {
        private static string _customConfigPath;
        private static readonly object _ioLock = new object();

        public static void SetSyncFolder(string folder)
        {
            if (string.IsNullOrWhiteSpace(folder)) _customConfigPath = null;
            else _customConfigPath = Path.Combine(folder, "launcher_config.json");
        }

        public static string ConfigPath =>
            _customConfigPath ?? Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "launcher_config.json");

        public static ConfigData Load()
        {
            if (!File.Exists(ConfigPath)) return new ConfigData();
            try
            {
                string json;
                using (var fs = new FileStream(ConfigPath, FileMode.Open, FileAccess.Read,
                    FileShare.ReadWrite, 4096, FileOptions.SequentialScan))
                using (var sr = new StreamReader(fs, Encoding.UTF8))
                {
                    json = sr.ReadToEnd();
                }

                var config = JsonSerializer.Deserialize<ConfigData>(json);
                if (config == null) return new ConfigData();
                if (config.Directories == null) config.Directories = new List<string>();
                if (config.Directories.Count == 0) config.Directories.Add(Directory.GetCurrentDirectory());
                if (config.CurrentDirIndex >= config.Directories.Count) config.CurrentDirIndex = 0;
                if (string.IsNullOrWhiteSpace(config.UpdateIndexUrl))
                    config.UpdateIndexUrl = "http://192.168.190.130:8081/versions.txt";
                if (config.WindowWidth <= 0) config.WindowWidth = 1100;
                if (config.WindowHeight <= 0) config.WindowHeight = 700;
                if (string.IsNullOrWhiteSpace(config.DownloadPath))
                    config.DownloadPath = Path.Combine(Path.GetTempPath(), "SnakeGameDownloads");
                // ★ 语言默认值
                if (string.IsNullOrWhiteSpace(config.Language))
                    config.Language = "zh-CN";
                // ★ 鹰角式深色外壳：默认深色主题（仍可在设置中切换回浅色）
                if (string.IsNullOrWhiteSpace(config.ThemeMode))
                    config.ThemeMode = "dark";
                // ★ 自定义背景默认值
                if (string.IsNullOrWhiteSpace(config.BackgroundType))
                    config.BackgroundType = "none";
                if (config.BackgroundPath == null)
                    config.BackgroundPath = "";
                return config;
            }
            catch { return new ConfigData(); }
        }

        public static void Save(ConfigData config)
        {
            lock (_ioLock)
            {
                try
                {
                    string json = JsonSerializer.Serialize(config,
                        new JsonSerializerOptions { WriteIndented = true });

                    string tempPath = ConfigPath + ".tmp";
                    using (var fs = new FileStream(tempPath, FileMode.Create, FileAccess.Write,
                        FileShare.Read, 4096, FileOptions.WriteThrough))
                    using (var sw = new StreamWriter(fs, new UTF8Encoding(false)))
                    {
                        sw.Write(json);
                        sw.Flush();
                        fs.Flush(true);
                    }

                    for (int i = 0; i < 5; i++)
                    {
                        try
                        {
                            if (File.Exists(ConfigPath))
                                File.Replace(tempPath, ConfigPath, null, ignoreMetadataErrors: true);
                            else
                                File.Move(tempPath, ConfigPath);
                            return;
                        }
                        catch (IOException)
                        {
                            System.Threading.Thread.Sleep(50 * (i + 1));
                        }
                    }

                    try
                    {
                        File.Copy(tempPath, ConfigPath, overwrite: true);
                        File.Delete(tempPath);
                    }
                    catch { }
                }
                catch { }
            }
        }

        public static bool ExportTo(string targetPath)
        {
            try
            {
                if (!File.Exists(ConfigPath)) return false;

                string json;
                using (var fs = new FileStream(ConfigPath, FileMode.Open, FileAccess.Read,
                    FileShare.ReadWrite, 4096, FileOptions.SequentialScan))
                using (var sr = new StreamReader(fs, Encoding.UTF8))
                {
                    json = sr.ReadToEnd();
                }

                using (var fs = new FileStream(targetPath, FileMode.Create, FileAccess.Write,
                    FileShare.Read, 4096))
                using (var sw = new StreamWriter(fs, new UTF8Encoding(false)))
                {
                    sw.Write(json);
                }
                return true;
            }
            catch
            {
                return false;
            }
        }
    }

    // ========== 主题管理器 ==========
    public static class ThemeManager
    {
        public static event Action ThemeChanged;

        public static void ApplyTheme(ConfigData config)
        {
            var resources = Application.Current.Resources;
            var accent = (Color)ColorConverter.ConvertFromString(config.AccentColor);

            if (config.ThemeMode == "light")
                SetLightTheme(resources);
            else
                SetDarkTheme(resources);

            resources["AccentBrush"] = new SolidColorBrush(accent);
            resources["AccentLightBrush"] = new SolidColorBrush(Color.FromArgb(30, accent.R, accent.G, accent.B));
            // ★ 强调色的柔和底/描边跟随强调色，而不是固定蓝色（鹰角式外壳大量使用）
            resources["AccentSoftBrush"] = new SolidColorBrush(Color.FromArgb(0x26, accent.R, accent.G, accent.B));
            resources["ButtonHoverBrush"] = new SolidColorBrush(accent) { Opacity = 0.8 };

            resources["AccentHoverBrush"] = new SolidColorBrush(AdjustBrightness(accent, 1.18));
            resources["AccentPressedBrush"] = new SolidColorBrush(AdjustBrightness(accent, 0.78));

            double luminance = (0.299 * accent.R + 0.587 * accent.G + 0.114 * accent.B) / 255.0;
            resources["AccentForegroundBrush"] = new SolidColorBrush(
                luminance > 0.6 ? Colors.Black : Colors.White);

            if (config.ApplyText)
            {
                resources["ForegroundBrush"] = resources["AccentBrush"];
                resources["MenuForegroundBrush"] = resources["AccentBrush"];
            }

            ThemeChanged?.Invoke();
        }

        private static Color AdjustBrightness(Color c, double factor)
        {
            byte r = (byte)Math.Min(255, Math.Max(0, c.R * factor));
            byte g = (byte)Math.Min(255, Math.Max(0, c.G * factor));
            byte b = (byte)Math.Min(255, Math.Max(0, c.B * factor));
            return Color.FromRgb(r, g, b);
        }

        private static void SetLightTheme(ResourceDictionary resources)
        {
            resources["BackgroundBrush"] = new SolidColorBrush(Color.FromRgb(243, 243, 243));

            // ★ 设计系统 Token（浅色）
            resources["TextPrimaryBrush"] = new SolidColorBrush(Color.FromRgb(0x18, 0x18, 0x1B));
            resources["TextSecondaryBrush"] = new SolidColorBrush(Color.FromRgb(0x5C, 0x5C, 0x66));
            resources["TextTertiaryBrush"] = new SolidColorBrush(Color.FromRgb(0x8C, 0x8C, 0x96));
            resources["SurfaceBrush"] = new SolidColorBrush(Colors.White);
            resources["SurfaceHoverBrush"] = new SolidColorBrush(Color.FromRgb(0xF4, 0xF4, 0xF6));
            resources["SurfacePressedBrush"] = new SolidColorBrush(Color.FromRgb(0xEC, 0xEC, 0xEF));
            resources["SurfaceSunkenBrush"] = new SolidColorBrush(Color.FromRgb(0xF0, 0xF0, 0xF3));
            resources["BorderSubtleBrush"] = new SolidColorBrush(Color.FromArgb(0x14, 0, 0, 0));
            resources["BorderStrongBrush"] = new SolidColorBrush(Color.FromArgb(0x26, 0, 0, 0));
            resources["AccentSoftBrush"] = new SolidColorBrush(Color.FromArgb(0x14, 0x00, 0x78, 0xD4));
            resources["ScrimBrush"] = new SolidColorBrush(Color.FromArgb(0xA6, 0, 0, 0));
            resources["PositiveBrush"] = new SolidColorBrush(Color.FromRgb(0x0F, 0x7B, 0x4F));
            resources["NegativeBrush"] = new SolidColorBrush(Color.FromRgb(0xD1, 0x34, 0x38));
            resources["ForegroundBrush"] = new SolidColorBrush(Color.FromRgb(31, 31, 31));
            resources["SecondaryForegroundBrush"] = new SolidColorBrush(Color.FromRgb(102, 102, 102));
            resources["MenuBackgroundBrush"] = new SolidColorBrush(Color.FromRgb(247, 247, 247));
            resources["MenuForegroundBrush"] = new SolidColorBrush(Color.FromRgb(31, 31, 31));
            resources["CardBackgroundBrush"] = new SolidColorBrush(Color.FromRgb(255, 255, 255));
            resources["CardBorderBrush"] = new SolidColorBrush(Color.FromRgb(224, 224, 224));
            resources["SeparatorBrush"] = new SolidColorBrush(Color.FromRgb(208, 208, 208));
            resources["ScrollBarBackgroundBrush"] = new SolidColorBrush(Color.FromRgb(240, 240, 240));
            resources["ScrollBarThumbBrush"] = new SolidColorBrush(Color.FromRgb(192, 192, 192));
            resources["TextBoxBackgroundBrush"] = new SolidColorBrush(Color.FromRgb(255, 255, 255));
            resources["TextBoxBorderBrush"] = new SolidColorBrush(Color.FromRgb(208, 208, 208));
            resources["GroupBoxHeaderBackgroundBrush"] = new SolidColorBrush(Color.FromRgb(240, 240, 240));

            resources["ButtonBackgroundBrush"] = new SolidColorBrush(Color.FromRgb(0xFF, 0xFF, 0xFF));
            resources["ButtonHoverBackgroundBrush"] = new SolidColorBrush(Color.FromRgb(0xF0, 0xF0, 0xF0));
            resources["ButtonPressedBackgroundBrush"] = new SolidColorBrush(Color.FromRgb(0xE0, 0xE0, 0xE0));
            resources["ButtonBorderBrush"] = new SolidColorBrush(Color.FromRgb(0xD0, 0xD0, 0xD0));
            resources["ButtonNeutralHoverBrush"] = new SolidColorBrush(Color.FromArgb(0x20, 0, 0, 0));

            resources["SplashShadowColor"] = Color.FromRgb(0x1A, 0x2A, 0x44);

            var lightBg = new LinearGradientBrush { StartPoint = new Point(0, 0), EndPoint = new Point(1, 1) };
            lightBg.GradientStops.Add(new GradientStop(Color.FromArgb(0xF5, 0xFF, 0xFF, 0xFF), 0));
            lightBg.GradientStops.Add(new GradientStop(Color.FromArgb(0xE0, 0xFF, 0xFF, 0xFF), 0.55));
            lightBg.GradientStops.Add(new GradientStop(Color.FromArgb(0xCC, 0xFF, 0xFF, 0xFF), 1));
            lightBg.Freeze();
            resources["SplashGlassBackgroundBrush"] = lightBg;

            var lightBorder = new LinearGradientBrush { StartPoint = new Point(0, 0), EndPoint = new Point(0, 1) };
            lightBorder.GradientStops.Add(new GradientStop(Color.FromArgb(0xFF, 0xFF, 0xFF, 0xFF), 0));
            lightBorder.GradientStops.Add(new GradientStop(Color.FromArgb(0x30, 0xFF, 0xFF, 0xFF), 1));
            lightBorder.Freeze();
            resources["SplashGlassBorderBrush"] = lightBorder;

            resources["SplashBlob1Brush"] = new SolidColorBrush(Color.FromArgb(0x55, 0x77, 0xC4, 0xFF));
            resources["SplashBlob2Brush"] = new SolidColorBrush(Color.FromArgb(0x55, 0xFF, 0xA8, 0xC4));
            resources["SplashTrackBrush"] = new SolidColorBrush(Color.FromArgb(0x22, 0, 0, 0));

            ApplyShellTheme(resources, light: true);
        }

        private static void SetDarkTheme(ResourceDictionary resources)
        {
            resources["BackgroundBrush"] = new SolidColorBrush(Color.FromRgb(24, 24, 27));

            // ★ 设计系统 Token（深色）
            resources["TextPrimaryBrush"] = new SolidColorBrush(Color.FromRgb(0xF4, 0xF4, 0xF5));
            resources["TextSecondaryBrush"] = new SolidColorBrush(Color.FromRgb(0xA6, 0xA6, 0xB0));
            resources["TextTertiaryBrush"] = new SolidColorBrush(Color.FromRgb(0x78, 0x78, 0x84));
            resources["SurfaceBrush"] = new SolidColorBrush(Color.FromRgb(0x2A, 0x2A, 0x2E));
            resources["SurfaceHoverBrush"] = new SolidColorBrush(Color.FromRgb(0x33, 0x33, 0x38));
            resources["SurfacePressedBrush"] = new SolidColorBrush(Color.FromRgb(0x3A, 0x3A, 0x40));
            resources["SurfaceSunkenBrush"] = new SolidColorBrush(Color.FromRgb(0x1F, 0x1F, 0x23));
            resources["BorderSubtleBrush"] = new SolidColorBrush(Color.FromArgb(0x1A, 0xFF, 0xFF, 0xFF));
            resources["BorderStrongBrush"] = new SolidColorBrush(Color.FromArgb(0x30, 0xFF, 0xFF, 0xFF));
            resources["AccentSoftBrush"] = new SolidColorBrush(Color.FromArgb(0x24, 0x00, 0x78, 0xD4));
            resources["ScrimBrush"] = new SolidColorBrush(Color.FromArgb(0xB3, 0, 0, 0));
            resources["PositiveBrush"] = new SolidColorBrush(Color.FromRgb(0x4C, 0xC3, 0x8A));
            resources["NegativeBrush"] = new SolidColorBrush(Color.FromRgb(0xF0, 0x6A, 0x6A));
            resources["ForegroundBrush"] = new SolidColorBrush(Color.FromRgb(224, 224, 224));
            resources["SecondaryForegroundBrush"] = new SolidColorBrush(Color.FromRgb(160, 160, 160));
            resources["MenuBackgroundBrush"] = new SolidColorBrush(Color.FromRgb(45, 45, 45));
            resources["MenuForegroundBrush"] = new SolidColorBrush(Color.FromRgb(224, 224, 224));
            resources["CardBackgroundBrush"] = new SolidColorBrush(Color.FromRgb(42, 42, 42));
            resources["CardBorderBrush"] = new SolidColorBrush(Color.FromRgb(58, 58, 58));
            resources["SeparatorBrush"] = new SolidColorBrush(Color.FromRgb(58, 58, 58));
            resources["ScrollBarBackgroundBrush"] = new SolidColorBrush(Color.FromRgb(45, 45, 45));
            resources["ScrollBarThumbBrush"] = new SolidColorBrush(Color.FromRgb(80, 80, 80));
            resources["TextBoxBackgroundBrush"] = new SolidColorBrush(Color.FromRgb(45, 45, 45));
            resources["TextBoxBorderBrush"] = new SolidColorBrush(Color.FromRgb(58, 58, 58));
            resources["GroupBoxHeaderBackgroundBrush"] = new SolidColorBrush(Color.FromRgb(45, 45, 45));

            resources["ButtonBackgroundBrush"] = new SolidColorBrush(Color.FromRgb(0x3A, 0x3A, 0x3A));
            resources["ButtonHoverBackgroundBrush"] = new SolidColorBrush(Color.FromRgb(0x4A, 0x4A, 0x4A));
            resources["ButtonPressedBackgroundBrush"] = new SolidColorBrush(Color.FromRgb(0x28, 0x28, 0x28));
            resources["ButtonBorderBrush"] = new SolidColorBrush(Color.FromRgb(0x55, 0x55, 0x55));
            resources["ButtonNeutralHoverBrush"] = new SolidColorBrush(Color.FromArgb(0x28, 0xFF, 0xFF, 0xFF));

            resources["SplashShadowColor"] = Colors.Black;

            var darkBg = new LinearGradientBrush { StartPoint = new Point(0, 0), EndPoint = new Point(1, 1) };
            darkBg.GradientStops.Add(new GradientStop(Color.FromArgb(0xF0, 0x22, 0x24, 0x2E), 0));
            darkBg.GradientStops.Add(new GradientStop(Color.FromArgb(0xE6, 0x1C, 0x1E, 0x28), 0.55));
            darkBg.GradientStops.Add(new GradientStop(Color.FromArgb(0xDD, 0x16, 0x18, 0x20), 1));
            darkBg.Freeze();
            resources["SplashGlassBackgroundBrush"] = darkBg;

            var darkBorder = new LinearGradientBrush { StartPoint = new Point(0, 0), EndPoint = new Point(0, 1) };
            darkBorder.GradientStops.Add(new GradientStop(Color.FromArgb(0x45, 0xFF, 0xFF, 0xFF), 0));
            darkBorder.GradientStops.Add(new GradientStop(Color.FromArgb(0x12, 0xFF, 0xFF, 0xFF), 1));
            darkBorder.Freeze();
            resources["SplashGlassBorderBrush"] = darkBorder;

            resources["SplashBlob1Brush"] = new SolidColorBrush(Color.FromArgb(0x60, 0x5A, 0x9E, 0xFF));
            resources["SplashBlob2Brush"] = new SolidColorBrush(Color.FromArgb(0x60, 0xFF, 0x7E, 0xB0));
            resources["SplashTrackBrush"] = new SolidColorBrush(Color.FromArgb(0x22, 0xFF, 0xFF, 0xFF));

            ApplyShellTheme(resources, light: false);
        }

        // ==================== ★ 鹰角式外壳 / 主视觉的明暗两套色板 ====================

        /// <summary>
        /// 外壳与主视觉不跟随普通页面 Token，而是使用这套固定色板；
        /// 浅色模式下整体翻转为"珍珠白 + 深墨字 + 柔和蓝灰山体"，强调色保持不变。
        /// </summary>
        private static void ApplyShellTheme(ResourceDictionary r, bool light)
        {
            if (light)
            {
                r["ShellWindowBrush"] = Solid(0xF6, 0xF7, 0xF8);
                r["ShellRailBrush"] = Solid(0xC4, 0xFF, 0xFF, 0xFF);
                r["ShellGlassBrush"] = Solid(0xBD, 0xFF, 0xFF, 0xFF);
                r["ShellGlassStrongBrush"] = Solid(0xF7, 0xFF, 0xFF, 0xFF);
                r["ShellCapsuleBrush"] = Solid(0xF2, 0xFF, 0xFF, 0xFF);
                r["ShellTextBrush"] = Solid(0x1B, 0x24, 0x30);
                r["ShellTextDimBrush"] = Solid(0x5D, 0x6B, 0x78);
                r["ShellTextFaintBrush"] = Solid(0x8C, 0x98, 0xA4);
                r["ShellHairlineBrush"] = Solid(0x1A, 0, 0, 0);
                r["ShellHairlineSoftBrush"] = Solid(0x0D, 0, 0, 0);
                r["ShellHoverBrush"] = Solid(0x12, 0, 0, 0);
                r["ShellPressedBrush"] = Solid(0x20, 0, 0, 0);
                r["ShellScrimBrush"] = Solid(0x66, 0, 0, 0);
                r["ShellScrimStrongBrush"] = Solid(0x80, 0, 0, 0);
                r["ShellSunkenBrush"] = Solid(0x0A, 0, 0, 0);

                r["ShellArtBrush"] = Gradient(
                    Color.FromRgb(0xF3, 0xF7, 0xFA), Color.FromRgb(0xE9, 0xF0, 0xF5), Color.FromRgb(0xE1, 0xEA, 0xF0));
                r["ShellArtAccentWashBrush"] = new LinearGradientBrush(
                    new GradientStopCollection
                    {
                        new GradientStop(Color.FromArgb(0x00, 0xFF, 0xFF, 0xFF), 0),
                        new GradientStop(Color.FromArgb(0x55, 0xFF, 0xFF, 0xFF), 0.55),
                        new GradientStop(Color.FromArgb(0x80, 0xFF, 0xFF, 0xFF), 1),
                    },
                    new Point(0, 1), new Point(1, 0));
                r["HeroTitleBrush"] = Gradient(
                    Color.FromRgb(0x10, 0x19, 0x23), Color.FromRgb(0x2B, 0x39, 0x47), Color.FromRgb(0x5A, 0x6E, 0x7D));
                r["DotGridBrush"] = DotGrid(Color.FromArgb(0x22, 0, 0, 0));
                r["LineGridBrush"] = LineGrid(Color.FromArgb(0x14, 0, 0, 0));

                r["ArtGhostTextBrush"] = Solid(0x0F, 0, 0, 0);
                r["ArtHighlightBrush"] = Solid(0x2E, 0xFF, 0xFF, 0xFF);
                r["ArtMountainBrush1"] = Solid(0xD7, 0xE1, 0xE9);
                r["ArtMountainBrush2"] = Solid(0xC6, 0xD2, 0xDC);
                r["ArtMountainLineBrush"] = Solid(0x33, 0x6E, 0x86, 0x96);
                r["ArtAnnotationBrush"] = Solid(0x66, 0, 0, 0);
                r["ArtBigNumberBrush"] = Solid(0x22, 0, 0, 0);
                r["PromoBigNumberBrush"] = Solid(0x1F, 0, 0, 0);
                r["PromoCardBackgroundBrush"] = Gradient(
                    Color.FromRgb(0xFD, 0xFE, 0xFF), Color.FromRgb(0xEE, 0xF4, 0xF8), Color.FromRgb(0xE4, 0xEC, 0xF2));
                r["SplashProgressTrackBrush"] = Solid(0x22, 0, 0, 0);
                r["ScrollThumbBrush"] = Solid(0x33, 0, 0, 0);
                r["ScrollThumbHoverBrush"] = Solid(0x66, 0, 0, 0);
                r["ScrollThumbDragBrush"] = Solid(0x99, 0, 0, 0);
                r["CustomBackgroundScrimBrush"] = Solid(0x3D, 0xFF, 0xFF, 0xFF);

                r["ArtVignetteVerticalBrush"] = VerticalVignette(
                    Color.FromArgb(0x66, 0xFF, 0xFF, 0xFF),
                    Color.FromArgb(0x1A, 0xFF, 0xFF, 0xFF),
                    Color.FromArgb(0x00, 0xFF, 0xFF, 0xFF),
                    Color.FromArgb(0x55, 0xFF, 0xFF, 0xFF));
                r["ArtVignetteHorizontalBrush"] = new LinearGradientBrush(
                    new GradientStopCollection
                    {
                        new GradientStop(Color.FromArgb(0x80, 0xFF, 0xFF, 0xFF), 0),
                        new GradientStop(Color.FromArgb(0x00, 0xFF, 0xFF, 0xFF), 0.46),
                    },
                    new Point(0, 0), new Point(1, 0));
            }
            else
            {
                r["ShellWindowBrush"] = Solid(0x0A, 0x0A, 0x0C);
                r["ShellRailBrush"] = Solid(0xBF, 0x0E, 0x0E, 0x11);
                r["ShellGlassBrush"] = Solid(0xB8, 0x11, 0x11, 0x14);
                r["ShellGlassStrongBrush"] = Solid(0xEF, 0x12, 0x12, 0x16);
                r["ShellCapsuleBrush"] = Solid(0xD9, 0x14, 0x14, 0x18);
                r["ShellTextBrush"] = Solid(0xF3, 0xF3, 0xEE);
                r["ShellTextDimBrush"] = Solid(0xA6, 0xA6, 0xA0);
                r["ShellTextFaintBrush"] = Solid(0x6C, 0x6C, 0x68);
                r["ShellHairlineBrush"] = Solid(0x22, 0xFF, 0xFF, 0xFF);
                r["ShellHairlineSoftBrush"] = Solid(0x12, 0xFF, 0xFF, 0xFF);
                r["ShellHoverBrush"] = Solid(0x1A, 0xFF, 0xFF, 0xFF);
                r["ShellPressedBrush"] = Solid(0x2B, 0xFF, 0xFF, 0xFF);
                r["ShellScrimBrush"] = Solid(0x99, 0, 0, 0);
                r["ShellScrimStrongBrush"] = Solid(0xA6, 0, 0, 0);
                r["ShellSunkenBrush"] = Solid(0x14, 0xFF, 0xFF, 0xFF);

                r["ShellArtBrush"] = Gradient(
                    Color.FromRgb(0x0C, 0x1A, 0x1B), Color.FromRgb(0x0A, 0x12, 0x14), Color.FromRgb(0x0B, 0x0F, 0x10));
                r["ShellArtAccentWashBrush"] = new LinearGradientBrush(
                    new GradientStopCollection
                    {
                        new GradientStop(Color.FromArgb(0x00, 0xFF, 0xFF, 0xFF), 0),
                        new GradientStop(Color.FromArgb(0x0D, 0xFF, 0xFF, 0xFF), 0.55),
                        new GradientStop(Color.FromArgb(0x18, 0xFF, 0xFF, 0xFF), 1),
                    },
                    new Point(0, 1), new Point(1, 0));
                r["HeroTitleBrush"] = Gradient(
                    Color.FromRgb(0xFF, 0xFF, 0xFF), Color.FromRgb(0xD8, 0xE7, 0xE4), Color.FromRgb(0x8F, 0xA5, 0xA2));
                r["DotGridBrush"] = DotGrid(Color.FromArgb(0x14, 0xFF, 0xFF, 0xFF));
                r["LineGridBrush"] = LineGrid(Color.FromArgb(0x0D, 0xFF, 0xFF, 0xFF));

                r["ArtGhostTextBrush"] = Solid(0x08, 0xFF, 0xFF, 0xFF);
                r["ArtHighlightBrush"] = Solid(0x07, 0xFF, 0xFF, 0xFF);
                r["ArtMountainBrush1"] = Solid(0x0B, 0x14, 0x15);
                r["ArtMountainBrush2"] = Solid(0x07, 0x0D, 0x0E);
                r["ArtMountainLineBrush"] = Solid(0x22, 0xFF, 0xFF, 0xFF);
                r["ArtAnnotationBrush"] = Solid(0x2E, 0xFF, 0xFF, 0xFF);
                r["ArtBigNumberBrush"] = Solid(0x1A, 0xFF, 0xFF, 0xFF);
                r["PromoBigNumberBrush"] = Solid(0x14, 0xFF, 0xFF, 0xFF);
                r["PromoCardBackgroundBrush"] = Gradient(
                    Color.FromRgb(0x12, 0x26, 0x28), Color.FromRgb(0x0B, 0x14, 0x16), Color.FromRgb(0x0A, 0x0E, 0x0F));
                r["SplashProgressTrackBrush"] = Solid(0x20, 0xFF, 0xFF, 0xFF);
                r["ScrollThumbBrush"] = Solid(0x33, 0xFF, 0xFF, 0xFF);
                r["ScrollThumbHoverBrush"] = Solid(0x66, 0xFF, 0xFF, 0xFF);
                r["ScrollThumbDragBrush"] = Solid(0x99, 0xFF, 0xFF, 0xFF);
                r["CustomBackgroundScrimBrush"] = Solid(0x4D, 0, 0, 0);

                r["ArtVignetteVerticalBrush"] = VerticalVignette(
                    Color.FromArgb(0x8C, 0, 0, 0),
                    Color.FromArgb(0x26, 0, 0, 0),
                    Color.FromArgb(0x00, 0, 0, 0),
                    Color.FromArgb(0xB3, 0, 0, 0));
                r["ArtVignetteHorizontalBrush"] = new LinearGradientBrush(
                    new GradientStopCollection
                    {
                        new GradientStop(Color.FromArgb(0x73, 0, 0, 0), 0),
                        new GradientStop(Color.FromArgb(0x00, 0, 0, 0), 0.46),
                    },
                    new Point(0, 0), new Point(1, 0));
            }
        }

        private static SolidColorBrush Solid(byte a, byte r, byte g, byte b)
            => new SolidColorBrush(Color.FromArgb(a, r, g, b));

        private static SolidColorBrush Solid(byte r, byte g, byte b)
            => new SolidColorBrush(Color.FromRgb(r, g, b));

        private static LinearGradientBrush Gradient(Color c0, Color c1, Color c2)
            => new LinearGradientBrush(new GradientStopCollection
            {
                new GradientStop(c0, 0),
                new GradientStop(c1, 0.45),
                new GradientStop(c2, 1),
            }, new Point(0, 0), new Point(1, 1));

        private static LinearGradientBrush VerticalVignette(Color c0, Color c1, Color c2, Color c3)
            => new LinearGradientBrush(new GradientStopCollection
            {
                new GradientStop(c0, 0),
                new GradientStop(c1, 0.22),
                new GradientStop(c2, 0.55),
                new GradientStop(c3, 1),
            }, new Point(0, 0), new Point(0, 1));

        private static DrawingBrush DotGrid(Color color)
        {
            var brush = new DrawingBrush
            {
                TileMode = TileMode.Tile,
                Stretch = Stretch.None,
                Viewport = new Rect(0, 0, 26, 26),
                ViewportUnits = BrushMappingMode.Absolute,
                Drawing = new GeometryDrawing(
                    new SolidColorBrush(color),
                    null,
                    new EllipseGeometry(new Point(2, 2), 1.1, 1.1)),
            };
            return brush;
        }

        private static DrawingBrush LineGrid(Color color)
        {
            var group = new GeometryGroup();
            group.Children.Add(new LineGeometry(new Point(0, 0), new Point(72, 0)));
            group.Children.Add(new LineGeometry(new Point(0, 0), new Point(0, 72)));
            var brush = new DrawingBrush
            {
                TileMode = TileMode.Tile,
                Stretch = Stretch.None,
                Viewport = new Rect(0, 0, 72, 72),
                ViewportUnits = BrushMappingMode.Absolute,
                Drawing = new GeometryDrawing(null, new Pen(new SolidColorBrush(color), 1), group),
            };
            return brush;
        }
    }

    // ========== 游戏文件信息 ==========
    public class GameFileInfo
    {
        public Version Version { get; set; }
        public string DisplayName { get; set; }
        public string FullPath { get; set; }
        public bool IsPython { get; set; }
    }

    // ========== 游戏统计 ==========
    public class PlayRecord
    {
        public string GamePath { get; set; }
        public int LaunchCount { get; set; }
        public double TotalPlayMinutes { get; set; }
        public DateTime LastPlayed { get; set; }
    }

    public class GameSessionRecord
    {
        public DateTime StartTime { get; set; }
        public double DurationMinutes { get; set; }
        public int FinalScore { get; set; }
        public int FinalKills { get; set; }
        public string Mode { get; set; }
        public string GamePath { get; set; }
    }

    public static class GameStatsManager
    {
        private static readonly string StatsPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "game_stats.json");
        private static readonly string HistoryPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "game_history.json");
        private static List<PlayRecord> _records = new List<PlayRecord>();
        private static List<GameSessionRecord> _sessions = new List<GameSessionRecord>();

        public static List<PlayRecord> LoadRecords()
        {
            try
            {
                if (File.Exists(StatsPath))
                    _records = JsonSerializer.Deserialize<List<PlayRecord>>(File.ReadAllText(StatsPath)) ?? new List<PlayRecord>();
                else _records = new List<PlayRecord>();
            }
            catch { _records = new List<PlayRecord>(); }
            return _records;
        }

        public static List<GameSessionRecord> LoadSessions()
        {
            try
            {
                if (File.Exists(HistoryPath))
                    _sessions = JsonSerializer.Deserialize<List<GameSessionRecord>>(File.ReadAllText(HistoryPath)) ?? new List<GameSessionRecord>();
                else _sessions = new List<GameSessionRecord>();
            }
            catch { _sessions = new List<GameSessionRecord>(); }
            return _sessions;
        }

        public static void SaveRecords()
        {
            try
            {
                string json = JsonSerializer.Serialize(_records,
                    new JsonSerializerOptions { WriteIndented = true });
                using (var fs = new FileStream(StatsPath, FileMode.Create, FileAccess.Write,
                    FileShare.Read, 4096))
                using (var sw = new StreamWriter(fs, new UTF8Encoding(false)))
                {
                    sw.Write(json);
                }
            }
            catch { }
        }

        public static void SaveSessions()
        {
            try
            {
                string json = JsonSerializer.Serialize(_sessions,
                    new JsonSerializerOptions { WriteIndented = true });
                using (var fs = new FileStream(HistoryPath, FileMode.Create, FileAccess.Write,
                    FileShare.Read, 4096))
                using (var sw = new StreamWriter(fs, new UTF8Encoding(false)))
                {
                    sw.Write(json);
                }
            }
            catch { }
        }

        public static PlayRecord GetRecord(string path) => _records?.FirstOrDefault(r => r.GamePath == path);

        public static void RecordLaunch(string path)
        {
            if (_records == null) _records = new List<PlayRecord>();
            var record = GetRecord(path);
            if (record == null) { record = new PlayRecord { GamePath = path }; _records.Add(record); }
            record.LaunchCount++;
            record.LastPlayed = DateTime.Now;
            SaveRecords();
        }

        public static void RecordPlayDuration(string path, double minutes)
        {
            var record = GetRecord(path);
            if (record != null) { record.TotalPlayMinutes += minutes; SaveRecords(); }
        }

        public static void AddSession(GameSessionRecord session)
        {
            if (_sessions == null) _sessions = new List<GameSessionRecord>();
            _sessions.Insert(0, session);
            if (_sessions.Count > 50) _sessions = _sessions.Take(50).ToList();
            SaveSessions();
        }

        public static List<GameSessionRecord> GetSessionsForGame(string path)
        {
            return _sessions?.Where(s => s.GamePath == path).OrderByDescending(s => s.StartTime).ToList();
        }

        public static void RemoveRecordsByPath(string path)
        {
            if (string.IsNullOrEmpty(path)) return;
            try
            {
                _records?.RemoveAll(r => string.Equals(r.GamePath, path, StringComparison.OrdinalIgnoreCase));
                SaveRecords();
            }
            catch { }
        }

        public static void RemoveSessionsByPath(string path)
        {
            if (string.IsNullOrEmpty(path)) return;
            try
            {
                _sessions?.RemoveAll(s => string.Equals(s.GamePath, path, StringComparison.OrdinalIgnoreCase));
                SaveSessions();
            }
            catch { }
        }
    }

    // ========== 游戏启动器 ==========
    public static class GameLauncher
    {
        public static Process StartProcess(string filePath, bool isPython)
        {
            var psi = new ProcessStartInfo
            {
                FileName = isPython ? "python.exe" : filePath,
                Arguments = isPython ? $"\"{filePath}\"" : "",
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true,
                WorkingDirectory = Path.GetDirectoryName(filePath)
            };
            return Process.Start(psi);
        }
    }

    // ========== 下载相关 ==========
    public class VersionInfo
    {
        public string Version { get; set; }
        public string DisplayName { get; set; }
        public string ReleaseNotes { get; set; }
        public string DownloadUrl { get; set; }
        public long FileSize { get; set; }
        public string Sha256 { get; set; }
    }

    public class UpdateIndex
    {
        public VersionInfo Latest { get; set; }
        public List<VersionInfo> History { get; set; }
    }

    public class DownloadProgressEventArgs : EventArgs
    {
        public double ProgressPercentage { get; set; }
        public long DownloadedBytes { get; set; }
        public long TotalBytes { get; set; }
    }

    public class DownloadManager
    {
        private readonly HttpClient _httpClient;
        public event EventHandler<DownloadProgressEventArgs> ProgressChanged;
        public event EventHandler<string> DownloadCompleted;
        public event EventHandler<string> DownloadFailed;

        public DownloadManager()
        {
            var handler = new HttpClientHandler { AllowAutoRedirect = true };
            _httpClient = new HttpClient(handler) { Timeout = TimeSpan.FromMinutes(30) };
        }

        public async Task DownloadFileAsync(string url, string savePath, CancellationToken cancellationToken = default)
        {
            try
            {
                using (var response = await _httpClient.GetAsync(url, HttpCompletionOption.ResponseHeadersRead, cancellationToken))
                {
                    response.EnsureSuccessStatusCode();
                    long totalBytes = response.Content.Headers.ContentLength ?? -1;
                    using (var contentStream = await response.Content.ReadAsStreamAsync())
                    using (var fileStream = new FileStream(savePath, FileMode.Create, FileAccess.Write, FileShare.None, 8192, true))
                    {
                        var buffer = new byte[8192];
                        long totalRead = 0;
                        int bytesRead;
                        while ((bytesRead = await contentStream.ReadAsync(buffer, 0, buffer.Length, cancellationToken)) > 0)
                        {
                            await fileStream.WriteAsync(buffer, 0, bytesRead, cancellationToken);
                            totalRead += bytesRead;
                            if (totalBytes > 0)
                            {
                                double progress = (double)totalRead / totalBytes * 100;
                                ProgressChanged?.Invoke(this, new DownloadProgressEventArgs
                                {
                                    ProgressPercentage = progress,
                                    DownloadedBytes = totalRead,
                                    TotalBytes = totalBytes
                                });
                            }
                        }
                    }
                }
                DownloadCompleted?.Invoke(this, savePath);
            }
            catch (OperationCanceledException) { }
            catch (Exception ex)
            {
                DownloadFailed?.Invoke(this, ex.Message);
                if (File.Exists(savePath)) { try { File.Delete(savePath); } catch { } }
            }
        }
    }

    public class VersionDownloadState
    {
        public VersionInfo Info { get; set; }
        public bool IsDownloading { get; set; }
        public bool IsDownloaded { get; set; }
        public bool IsInstalled { get; set; }
        public double Progress { get; set; }
        public CancellationTokenSource Cts { get; set; }
        public string DownloadedFilePath { get; set; }
    }

    // ========== 下载路径选择枚举 ==========
    public enum DownloadPathChoice
    {
        Confirm,
        Change,
        Cancel
    }

    // ========== 主窗口 ==========
    public partial class MainWindow : Window
    {
        private bool _autoUpdateCheckRunning;
        private Version _latestReleaseVersion;
        private bool _autoUpdatePromptShown;
        private UpdateCheckResult _pendingAutoUpdate;
        private ConfigData _config;
        private List<GameFileInfo> _gameFiles = new List<GameFileInfo>();
        private GameFileInfo _selectedGame;
        private bool _autoDownloadBusy;
        private List<GitHubRelease> _releaseFeed = new List<GitHubRelease>();
        private bool _releaseFeedLoading;
        private DateTime _releaseFeedLoadedAt = DateTime.MinValue;

        // ★ 游戏更新检测结果
        private GitHubRelease _latestGameRelease;
        private GitHubReleaseAsset _latestGameAsset;
        private Version _latestGameVersion;
        private bool _gameUpdateAvailable;
        private int _newsTabIndex;
        private Border _releaseNotesOverlay;
        private StackPanel _releaseNotesList;
        private FlowDocumentScrollViewer _releaseNotesViewer;
        private TextBlock _releaseNotesTitle;
        private TextBlock _releaseNotesMeta;
        private Button _releaseNotesGithubButton;
        private GitHubRelease _releaseNotesCurrent;

        // ★ 自定义启动器背景（图片 / 视频）
        private MediaPlayer _bgMediaPlayer;
        private VideoDrawing _bgVideoDrawing;
        private bool _bgVideoFallbackShown;

        // ★ 启动渐入 / 关闭渐出
        private bool _allowClose;
        private bool _isFadingOut;
        private Panel _cardPanel;
        private TranslateTransform _librarySlide;
        private Label _currentPathLabel;
        private ToggleButton _sortButton;
        private Popup _sortPopup;
        private ListBox _sortListBox;

        private Process _currentGameProcess;
        private DateTime _gameStartTime;

        // ★ 页面切换动画 / 游戏运行状态
        private int _currentTabIndex = -1;
        private bool _isGameRunning;
        private System.Windows.Threading.DispatcherTimer _playTimer;
        private System.Windows.Threading.DispatcherTimer _healthCheckTimer;
        private System.Windows.Threading.DispatcherTimer _performanceTimer;

        private List<int> _fpsHistory = new List<int>();
        private List<long> _memoryHistory = new List<long>();
        private int _lastScore, _lastKills;
        private StringBuilder _logBuilder = new StringBuilder();

        private StackPanel _downloadListPanel;
        private DownloadManager _downloadManager;
        private Dictionary<string, VersionDownloadState> _versionStates = new Dictionary<string, VersionDownloadState>();
        private VersionDownloadState _currentDownloadState;
        private Border _downloadDetailOverlay;
        private TextBlock _popupTitle, _popupSize, _popupNotes, _popupStatus;
        private Button _popupDownloadBtn, _popupCancelBtn;
        private ProgressBar _popupProgressBar;
        private CancellationTokenSource _downloadCts;
        private ScaleTransform _popupScaleTransform;

        private Grid _rootGrid;
        private bool _popupCreated = false;
        private Border _compatibilityDialog;
        private TextBlock _compatibilityMessage;
        private TaskCompletionSource<bool> _compatibilityTcs;
        private Border _confirmDialog;
        private TextBlock _confirmMessage;
        private TaskCompletionSource<bool> _confirmTcs;
        private Border _infoDialog;
        private TextBlock _infoMessage;
        private TaskCompletionSource<bool> _infoTcs;
        private readonly List<Border> _accentSwatches = new List<Border>();
        private readonly Random _blobRandom = new Random();
        private System.Windows.Threading.DispatcherTimer _notificationTimer;
        private string _currentDetailGamePath;
        // ========== 仓库文档面板相关 ==========
        private Border _repoDocsOverlay;
        private StackPanel _repoDocsFileList;
        private FlowDocumentScrollViewer _repoDocsViewer;
        private TextBlock _repoDocsTitle;
        private GitHubRepoConfig _repoDocsCurrentRepo;
        private string _repoDocsCurrentFile;
        // ★ 对话框按钮字段（用于语言切换时刷新文本）
        private Button _compatibilityOkBtn;
        private Button _confirmYesBtn;
        private Button _confirmNoBtn;
        private Button _infoOkBtn;

        // ========== 构造函数 ==========
        public MainWindow()
        {
            try
            {
                _config = ConfigManager.Load();
                if (!string.IsNullOrWhiteSpace(_config.SyncFolder))
                    ConfigManager.SetSyncFolder(_config.SyncFolder);

                // ★ 应用语言
                Lang.SetLanguage(_config.Language);

                ThemeManager.ApplyTheme(_config);
                InitializeComponent();

                // ★ 启动渐入：先隐藏窗口再显示，避免先闪现全不透明再淡入
                Opacity = 0;

                this.Width = _config.WindowWidth;
                this.Height = _config.WindowHeight;
                // ★ 窗口尺寸限制在当前工作区内，避免旧配置把窗口撑到屏幕外
                var workArea = SystemParameters.WorkArea;
                if (double.IsNaN(this.Width) || this.Width > workArea.Width - 24)
                    this.Width = Math.Max(this.MinWidth, workArea.Width - 24);
                if (double.IsNaN(this.Height) || this.Height > workArea.Height - 24)
                    this.Height = Math.Max(this.MinHeight, workArea.Height - 24);
                this.WindowStartupLocation = WindowStartupLocation.CenterScreen;

                GameStatsManager.LoadRecords();
                GameStatsManager.LoadSessions();

                ThemeManager.ThemeChanged += RefreshCards;
                IpcService.StatsReceived += OnStatsReceived;
                IpcService.Disconnected += OnIpcDisconnected;

                LoadDirectories();
                _ = ScanGamesAsync();

                _playTimer = new System.Windows.Threading.DispatcherTimer { Interval = TimeSpan.FromSeconds(1) };
                _playTimer.Tick += PlayTimer_Tick;

                _healthCheckTimer = new System.Windows.Threading.DispatcherTimer { Interval = TimeSpan.FromSeconds(2) };
                _healthCheckTimer.Tick += HealthCheck_Tick;

                _performanceTimer = new System.Windows.Threading.DispatcherTimer { Interval = TimeSpan.FromSeconds(1) };
                _performanceTimer.Tick += PerformanceTimer_Tick;

                _downloadManager = new DownloadManager();

                this.Loaded += OnMainWindowLoaded;
            }
            catch (Exception ex)
            {
                MessageBox.Show($"启动失败: {ex.Message}\n\n{ex.StackTrace}", "严重错误", MessageBoxButton.OK, MessageBoxImage.Error);
                Application.Current.Shutdown();
            }
        }

        /// <summary>
        /// 显示仓库 Markdown 文档面板
        /// </summary>
        private async Task ShowRepoDocsPanelAsync(GitHubRepoConfig repo)
        {
            if (repo == null) return;

            // ========== 面板已存在则先移除 ==========
            if (_repoDocsOverlay != null)
            {
                try { _rootGrid.Children.Remove(_repoDocsOverlay); } catch { }
                _repoDocsOverlay = null;
            }

            _repoDocsCurrentRepo = repo;
            _repoDocsCurrentFile = null;

            // ========== 遮罩层 ==========
            _repoDocsOverlay = new Border
            {
                Background = new SolidColorBrush(Color.FromArgb(0xA6, 0x12, 0x1A, 0x2B)),
                Visibility = Visibility.Visible,
                Opacity = 0,
                VerticalAlignment = VerticalAlignment.Stretch,
                HorizontalAlignment = HorizontalAlignment.Stretch
            };
            _repoDocsOverlay.MouseLeftButtonDown += (s, e) =>
            {
                if (e.OriginalSource == _repoDocsOverlay)
                    CloseRepoDocsPanel();
            };

            // ========== 主面板 ==========
            var panel = new Border
            {
                Width = Math.Min(1200, _rootGrid.ActualWidth - 80),
                Height = Math.Min(720, _rootGrid.ActualHeight - 80),
                Background = SafeFindBrush("CardBackgroundBrush"),
                BorderBrush = SafeFindBrush("CardBorderBrush"),
                BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(18),
                Padding = new Thickness(20),
                HorizontalAlignment = HorizontalAlignment.Center,
                VerticalAlignment = VerticalAlignment.Center,
                RenderTransformOrigin = new Point(0.5, 0.5)
            };
            panel.Effect = new DropShadowEffect
            {
                ShadowDepth = 10,
                BlurRadius = 40,
                Opacity = 0.4,
                Color = Color.FromRgb(0x0F, 0x1B, 0x33)
            };
            var scale = new ScaleTransform(0.85, 0.85);
            panel.RenderTransform = scale;

            var layoutGrid = new Grid();
            layoutGrid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            layoutGrid.RowDefinitions.Add(new RowDefinition { Height = new GridLength(1, GridUnitType.Star) });
            layoutGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(240) });
            layoutGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1) });
            layoutGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });

            // ========== 标题栏 ==========
            var titleBar = new Grid();
            titleBar.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            titleBar.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
            titleBar.Margin = new Thickness(0, 0, 0, 14);

            _repoDocsTitle = new TextBlock
            {
                Text = $"{repo.DisplayName} · 仓库文档",
                FontSize = 18,
                FontWeight = FontWeights.Bold,
                Foreground = SafeFindBrush("ForegroundBrush"),
                VerticalAlignment = VerticalAlignment.Center
            };
            Grid.SetColumn(_repoDocsTitle, 0);
            titleBar.Children.Add(_repoDocsTitle);

            var btnClose = new Button
            {
                Content = "✕",
                Width = 32,
                Height = 32,
                FontSize = 14,
                Background = Brushes.Transparent,
                Foreground = SafeFindBrush("ForegroundBrush"),
                BorderThickness = new Thickness(0),
                Cursor = Cursors.Hand
            };
            btnClose.Click += (s, e) => CloseRepoDocsPanel();
            Grid.SetColumn(btnClose, 1);
            titleBar.Children.Add(btnClose);

            Grid.SetRow(titleBar, 0);
            Grid.SetColumnSpan(titleBar, 3);
            layoutGrid.Children.Add(titleBar);

            // ========== 左侧：文件列表 ==========
            var leftPanel = new Border
            {
                Background = SafeFindBrush("BackgroundBrush"),
                CornerRadius = new CornerRadius(10),
                Padding = new Thickness(8),
                Margin = new Thickness(0, 0, 14, 0)
            };
            _repoDocsFileList = new StackPanel();
            var scrollLeft = new ScrollViewer
            {
                Content = _repoDocsFileList,
                VerticalScrollBarVisibility = ScrollBarVisibility.Auto,
                HorizontalScrollBarVisibility = ScrollBarVisibility.Disabled
            };
            leftPanel.Child = scrollLeft;

            Grid.SetRow(leftPanel, 1);
            Grid.SetColumn(leftPanel, 0);
            layoutGrid.Children.Add(leftPanel);

            // ========== 中间分隔线 ==========
            var sep = new Border
            {
                Background = SafeFindBrush("CardBorderBrush"),
                Width = 1,
                Margin = new Thickness(0, 0, 14, 0)
            };
            Grid.SetRow(sep, 1);
            Grid.SetColumn(sep, 1);
            layoutGrid.Children.Add(sep);

            // ========== 右侧：Markdown 内容 ==========
            var rightBorder = new Border
            {
                Background = SafeFindBrush("BackgroundBrush"),
                CornerRadius = new CornerRadius(10),
                Padding = new Thickness(4)
            };
            _repoDocsViewer = new FlowDocumentScrollViewer
            {
                VerticalScrollBarVisibility = ScrollBarVisibility.Auto,
                HorizontalScrollBarVisibility = ScrollBarVisibility.Disabled,
                IsToolBarVisible = false,
                Padding = new Thickness(0)
            };
            rightBorder.Child = _repoDocsViewer;

            Grid.SetRow(rightBorder, 1);
            Grid.SetColumn(rightBorder, 2);
            layoutGrid.Children.Add(rightBorder);

            panel.Child = layoutGrid;

            var overlayChild = new Grid();
            overlayChild.Children.Add(panel);
            _repoDocsOverlay.Child = overlayChild;

            _rootGrid.Children.Add(_repoDocsOverlay);
            Grid.SetRowSpan(_repoDocsOverlay, int.MaxValue);
            Grid.SetColumnSpan(_repoDocsOverlay, int.MaxValue);

            // 显示动画
            var fadeIn = new DoubleAnimation(0, 1, TimeSpan.FromMilliseconds(200));
            var scaleIn = new DoubleAnimation(0.96, 1.0, TimeSpan.FromMilliseconds(200))
            {
                EasingFunction = new BackEase { EasingMode = EasingMode.EaseOut, Amplitude = 0.3 }
            };
            _repoDocsOverlay.BeginAnimation(OpacityProperty, fadeIn);
            scale.BeginAnimation(ScaleTransform.ScaleXProperty, scaleIn);
            scale.BeginAnimation(ScaleTransform.ScaleYProperty, scaleIn);

            // ========== 加载文件列表 ==========
            _repoDocsFileList.Children.Clear();
            _repoDocsFileList.Children.Add(new TextBlock
            {
                Text = "正在加载文件列表...",
                FontSize = 12,
                Foreground = SafeFindBrush("SecondaryForegroundBrush"),
                Margin = new Thickness(8, 8, 8, 8)
            });

            try
            {
                var files = await GitHubReleaseService.GetRepoMarkdownFilesAsync(repo);
                _repoDocsFileList.Children.Clear();

                if (files.Count == 0)
                {
                    _repoDocsFileList.Children.Add(new TextBlock
                    {
                        Text = "该仓库根目录暂无 .md 文件",
                        FontSize = 12,
                        Foreground = SafeFindBrush("SecondaryForegroundBrush"),
                        Margin = new Thickness(8, 8, 8, 8),
                        TextWrapping = TextWrapping.Wrap
                    });
                    ShowRepoDocsEmpty();
                    return;
                }

                foreach (var file in files)
                {
                    _repoDocsFileList.Children.Add(CreateRepoDocFileRow(file, repo));
                }

                // 自动选中第一个
                if (files.Count > 0)
                    await LoadRepoDocFileAsync(files[0], repo);
            }
            catch (Exception ex)
            {
                _repoDocsFileList.Children.Clear();
                _repoDocsFileList.Children.Add(new TextBlock
                {
                    Text = $"加载失败: {ex.Message}",
                    FontSize = 12,
                    Foreground = new SolidColorBrush(Color.FromRgb(0xD1, 0x34, 0x38)),
                    Margin = new Thickness(8, 8, 8, 8),
                    TextWrapping = TextWrapping.Wrap
                });
                ShowRepoDocsEmpty();
            }
        }

        /// <summary>
        /// 创建一个 .md 文件行
        /// </summary>
        private Border CreateRepoDocFileRow(GitHubRepoFile file, GitHubRepoConfig repo)
        {
            var row = new Border
            {
                Padding = new Thickness(10, 8, 10, 8),
                Margin = new Thickness(0, 1, 0, 1),
                CornerRadius = new CornerRadius(6),
                Cursor = Cursors.Hand,
                Background = Brushes.Transparent,
                Tag = file
            };

            var text = new TextBlock
            {
                Text = file.Name,
                FontSize = 13,
                Foreground = SafeFindBrush("ForegroundBrush"),
                TextTrimming = TextTrimming.CharacterEllipsis
            };
            row.Child = text;

            row.MouseEnter += (s, e) =>
                row.Background = SafeFindBrush("ButtonHoverBackgroundBrush");
            row.MouseLeave += (s, e) =>
            {
                if ((row.Tag as GitHubRepoFile)?.Name != _repoDocsCurrentFile)
                    row.Background = Brushes.Transparent;
            };
            row.MouseLeftButtonUp += async (s, e) =>
            {
                await LoadRepoDocFileAsync(file, repo);
            };

            return row;
        }

        /// <summary>
        /// 加载并渲染指定的 .md 文件
        /// </summary>
        private async Task LoadRepoDocFileAsync(GitHubRepoFile file, GitHubRepoConfig repo)
        {
            if (file == null || _repoDocsViewer == null) return;

            _repoDocsCurrentFile = file.Name;

            // 高亮当前选中项
            if (_repoDocsFileList != null)
            {
                foreach (var child in _repoDocsFileList.Children)
                {
                    if (child is Border b)
                    {
                        if ((b.Tag as GitHubRepoFile)?.Name == file.Name)
                            b.Background = SafeFindBrush("AccentLightBrush");
                        else
                            b.Background = Brushes.Transparent;
                    }
                }
            }

            // 加载内容
            _repoDocsViewer.Document = new FlowDocument(new Paragraph(new Run("加载中..."))
            {
                Foreground = SafeFindBrush("SecondaryForegroundBrush"),
                Padding = new Thickness(20)
            });

            try
            {
                string content = await GitHubReleaseService.GetFileTextAsync(file.DownloadUrl);
                var doc = MarkdownRenderer.Render(
                    content,
                    SafeFindBrush("ForegroundBrush"),
                    SafeFindBrush("AccentBrush"),
                    13);
                _repoDocsViewer.Document = doc;
            }
            catch (Exception ex)
            {
                var errDoc = new FlowDocument(new Paragraph(new Run($"加载失败: {ex.Message}"))
                {
                    Foreground = new SolidColorBrush(Color.FromRgb(0xD1, 0x34, 0x38)),
                    Padding = new Thickness(20)
                });
                _repoDocsViewer.Document = errDoc;
            }
        }

        /// <summary>
        /// 显示空占位
        /// </summary>
        private void ShowRepoDocsEmpty()
        {
            if (_repoDocsViewer == null) return;
            var doc = new FlowDocument(new Paragraph(new Run("请从左侧选择一个 Markdown 文件"))
            {
                Foreground = SafeFindBrush("SecondaryForegroundBrush"),
                Padding = new Thickness(20)
            });
            _repoDocsViewer.Document = doc;
        }

        /// <summary>
        /// 关闭仓库文档面板
        /// </summary>
        private void CloseRepoDocsPanel()
        {
            if (_repoDocsOverlay == null) return;

            var overlay = _repoDocsOverlay;
            _repoDocsOverlay = null;
            _repoDocsFileList = null;
            _repoDocsViewer = null;

            var fadeOut = new DoubleAnimation(1, 0, TimeSpan.FromMilliseconds(150));
            fadeOut.Completed += (s, e) =>
            {
                try { _rootGrid.Children.Remove(overlay); } catch { }
            };
            overlay.BeginAnimation(OpacityProperty, fadeOut);
        }

        private void OnCheatDetected(string reason)
        {
            ShowNotification("检测到可疑数据：" + reason);
            // 也可以选择弹出详情窗口
            // ShowDetailPanel("反作弊告警", "游戏上报数据异常：\n" + reason);
        }

        // ========== Loaded 事件 ==========
        /// <summary>
        /// 窗口圆角裁剪：内容尺寸变化时同步更新。
        /// 启动时立刻应用一次，避免出现"移动窗口或缩放后才变圆角"的问题。
        /// </summary>
        private void UpdateWindowClip()
        {
            try
            {
                if (_rootGrid == null) return;

                double w = _rootGrid.ActualWidth;
                double h = _rootGrid.ActualHeight;
                if (w <= 0 || h <= 0) return;

                var geometry = _rootGrid.Clip as RectangleGeometry;
                if (geometry == null)
                {
                    geometry = new RectangleGeometry();
                    _rootGrid.Clip = geometry;
                }
                geometry.Rect = new Rect(0, 0, w, h);
                geometry.RadiusX = 32;
                geometry.RadiusY = 32;

                UpdateContentBackdropClip();
            }
            catch { }
        }

        /// <summary>内容区面板（与左侧栏分离的圆角区域）裁剪。</summary>
        private void UpdateContentBackdropClip()
        {
            try
            {
                if (ContentBackdrop == null) return;

                double w = ContentBackdrop.ActualWidth;
                double h = ContentBackdrop.ActualHeight;
                if (w <= 0 || h <= 0) return;

                var geometry = ContentBackdrop.Clip as RectangleGeometry;
                if (geometry == null)
                {
                    geometry = new RectangleGeometry();
                    ContentBackdrop.Clip = geometry;
                }
                geometry.Rect = new Rect(0, 0, w, h);
                geometry.RadiusX = 20;
                geometry.RadiusY = 20;
            }
            catch { }
        }

        private void OnMainWindowLoaded(object sender, RoutedEventArgs e)
        {
            try
            {
                if (this.Content == null) { Application.Current.Shutdown(); return; }

                var border = this.Content as Border;
                if (border == null) { Application.Current.Shutdown(); return; }

                _rootGrid = border.Child as Grid;
                if (_rootGrid == null) { Application.Current.Shutdown(); return; }

                // ★ 启动渐入
                BeginWindowFadeIn();

                // ★ 鹰角式外壳：整窗圆角裁剪（AllowsTransparency 下 Border 不会自动裁子元素）
                _rootGrid.SizeChanged += (s, args) => UpdateWindowClip();

                // 启动时立即裁剪；Loaded 阶段布局可能刚完成，再在 Loaded 优先级补一次
                UpdateWindowClip();
                Dispatcher.BeginInvoke(new Action(UpdateWindowClip),
                    System.Windows.Threading.DispatcherPriority.Loaded);

                if (ContentBackdrop != null)
                {
                    ContentBackdrop.SizeChanged += (s, args) => UpdateContentBackdropClip();
                    UpdateContentBackdropClip();
                }

                // ★ 版本库抽屉的列表宿主 & 入场位移动画
                if (LibraryList != null) _cardPanel = LibraryList;
                if (LibraryPanel != null && LibraryPanel.RenderTransform as TranslateTransform == null)
                {
                    _librarySlide = new TranslateTransform(40, 0);
                    LibraryPanel.RenderTransform = _librarySlide;
                }

                // ★ 应用顶部栏多语言
                ApplyTopBarTexts();

                SelectTab(0);

                // ★ 后台加载两个仓库的版本资讯（公告 / 更新说明）
                _ = LoadReleaseFeedAsync();

                // ===== 初始化兼容性自绘对话框 =====
                _compatibilityDialog = new Border
                {
                    Background = new SolidColorBrush(Color.FromArgb(0xA6, 0x12, 0x1A, 0x2B)),
                    Visibility = Visibility.Collapsed,
                    Opacity = 0,
                    VerticalAlignment = VerticalAlignment.Stretch,
                    HorizontalAlignment = HorizontalAlignment.Stretch
                };

                var panel = new Border
                {
                    Width = 440,
                    MaxHeight = 500,
                    Background = SafeFindBrush("CardBackgroundBrush"),
                    BorderBrush = SafeFindBrush("CardBorderBrush"),
                    BorderThickness = new Thickness(1),
                    CornerRadius = new CornerRadius(22),
                    Padding = new Thickness(24),
                    HorizontalAlignment = HorizontalAlignment.Center,
                    VerticalAlignment = VerticalAlignment.Center,
                    RenderTransformOrigin = new Point(0.5, 0.5)
                };
                panel.Effect = new DropShadowEffect { ShadowDepth = 10, BlurRadius = 36, Opacity = 0.35, Color = Color.FromRgb(0x0F, 0x1B, 0x33) };
                var scaleTransform = new ScaleTransform(0.8, 0.8);
                panel.RenderTransform = scaleTransform;

                var grid = new Grid();
                grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
                grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
                grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });

                var title = new TextBlock
                {
                    Text = Lang.T("Dialog.Compatibility"),
                    FontSize = 18,
                    FontWeight = FontWeights.Bold,
                    Foreground = SafeFindBrush("ForegroundBrush")
                };
                _compatibilityMessage = new TextBlock
                {
                    TextWrapping = TextWrapping.Wrap,
                    Foreground = SafeFindBrush("ForegroundBrush"),
                    Margin = new Thickness(0, 12, 0, 12)
                };
                var btnOk = new Button
                {
                    Content = Lang.T("Dialog.Ok"),
                    Style = SafeFindStyle("RoundedButton"),
                    Width = 100,
                    Height = 38,
                    HorizontalAlignment = HorizontalAlignment.Center
                };
                _compatibilityOkBtn = btnOk;
                btnOk.Click += (s, args) =>
                {
                    CloseCompatibilityDialog();
                    _compatibilityTcs?.TrySetResult(true);
                };

                Grid.SetRow(title, 0);
                Grid.SetRow(_compatibilityMessage, 1);
                Grid.SetRow(btnOk, 2);
                grid.Children.Add(title);
                grid.Children.Add(_compatibilityMessage);
                grid.Children.Add(btnOk);

                panel.Child = grid;
                var overlayGrid = new Grid();
                overlayGrid.Children.Add(panel);
                _compatibilityDialog.Child = overlayGrid;

                _rootGrid.Children.Add(_compatibilityDialog);
                Grid.SetRowSpan(_compatibilityDialog, int.MaxValue);
                Grid.SetColumnSpan(_compatibilityDialog, int.MaxValue);

                // ===== 初始化确认自绘对话框 =====
                _confirmDialog = new Border
                {
                    Background = new SolidColorBrush(Color.FromArgb(0xA6, 0x12, 0x1A, 0x2B)),
                    Visibility = Visibility.Collapsed,
                    Opacity = 0,
                    VerticalAlignment = VerticalAlignment.Stretch,
                    HorizontalAlignment = HorizontalAlignment.Stretch
                };

                var confirmPanel = new Border
                {
                    Width = 440,
                    MaxHeight = 500,
                    Background = SafeFindBrush("CardBackgroundBrush"),
                    BorderBrush = SafeFindBrush("CardBorderBrush"),
                    BorderThickness = new Thickness(1),
                    CornerRadius = new CornerRadius(22),
                    Padding = new Thickness(24),
                    HorizontalAlignment = HorizontalAlignment.Center,
                    VerticalAlignment = VerticalAlignment.Center,
                    RenderTransformOrigin = new Point(0.5, 0.5)
                };
                confirmPanel.Effect = new DropShadowEffect { ShadowDepth = 10, BlurRadius = 36, Opacity = 0.35, Color = Color.FromRgb(0x0F, 0x1B, 0x33) };
                var confirmScale = new ScaleTransform(0.8, 0.8);
                confirmPanel.RenderTransform = confirmScale;

                var confirmGrid = new Grid();
                confirmGrid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
                confirmGrid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
                confirmGrid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });

                var confirmTitle = new TextBlock
                {
                    Text = Lang.T("Dialog.Confirm"),
                    FontSize = 18,
                    FontWeight = FontWeights.Bold,
                    Foreground = SafeFindBrush("ForegroundBrush")
                };
                _confirmMessage = new TextBlock
                {
                    TextWrapping = TextWrapping.Wrap,
                    Foreground = SafeFindBrush("ForegroundBrush"),
                    Margin = new Thickness(0, 12, 0, 12)
                };

                var buttonPanel = new StackPanel
                {
                    Orientation = Orientation.Horizontal,
                    HorizontalAlignment = HorizontalAlignment.Center,
                    Margin = new Thickness(0, 12, 0, 0)
                };

                var btnYes = new Button
                {
                    Content = Lang.T("Dialog.Yes"),
                    Style = SafeFindStyle("RoundedButton"),
                    Width = 90,
                    Height = 38,
                    Margin = new Thickness(0, 0, 12, 0)
                };
                _confirmYesBtn = btnYes;
                btnYes.Click += (s, args) =>
                {
                    CloseConfirmDialog();
                    _confirmTcs?.TrySetResult(true);
                };

                var btnNo = new Button
                {
                    Content = Lang.T("Dialog.No"),
                    Style = SafeFindStyle("RoundedButton"),
                    Width = 90,
                    Height = 38
                };
                _confirmNoBtn = btnNo;
                btnNo.Click += (s, args) =>
                {
                    CloseConfirmDialog();
                    _confirmTcs?.TrySetResult(false);
                };

                buttonPanel.Children.Add(btnYes);
                buttonPanel.Children.Add(btnNo);

                Grid.SetRow(confirmTitle, 0);
                Grid.SetRow(_confirmMessage, 1);
                Grid.SetRow(buttonPanel, 2);
                confirmGrid.Children.Add(confirmTitle);
                confirmGrid.Children.Add(_confirmMessage);
                confirmGrid.Children.Add(buttonPanel);

                confirmPanel.Child = confirmGrid;
                var confirmOverlayGrid = new Grid();
                confirmOverlayGrid.Children.Add(confirmPanel);
                _confirmDialog.Child = confirmOverlayGrid;

                _rootGrid.Children.Add(_confirmDialog);
                Grid.SetRowSpan(_confirmDialog, int.MaxValue);
                Grid.SetColumnSpan(_confirmDialog, int.MaxValue);

                // ===== 初始化信息自绘对话框 =====
                _infoDialog = new Border
                {
                    Background = new SolidColorBrush(Color.FromArgb(0xA6, 0x12, 0x1A, 0x2B)),
                    Visibility = Visibility.Collapsed,
                    Opacity = 0,
                    VerticalAlignment = VerticalAlignment.Stretch,
                    HorizontalAlignment = HorizontalAlignment.Stretch
                };

                var infoPanel = new Border
                {
                    Width = 440,
                    MaxHeight = 500,
                    Background = SafeFindBrush("CardBackgroundBrush"),
                    BorderBrush = SafeFindBrush("CardBorderBrush"),
                    BorderThickness = new Thickness(1),
                    CornerRadius = new CornerRadius(22),
                    Padding = new Thickness(24),
                    HorizontalAlignment = HorizontalAlignment.Center,
                    VerticalAlignment = VerticalAlignment.Center,
                    RenderTransformOrigin = new Point(0.5, 0.5)
                };
                infoPanel.Effect = new DropShadowEffect { ShadowDepth = 10, BlurRadius = 36, Opacity = 0.35, Color = Color.FromRgb(0x0F, 0x1B, 0x33) };
                var infoScale = new ScaleTransform(0.8, 0.8);
                infoPanel.RenderTransform = infoScale;

                var infoGrid = new Grid();
                infoGrid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
                infoGrid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
                infoGrid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });

                var infoTitle = new TextBlock
                {
                    Text = Lang.T("Dialog.Confirm"),
                    FontSize = 18,
                    FontWeight = FontWeights.Bold,
                    Foreground = SafeFindBrush("ForegroundBrush")
                };
                _infoMessage = new TextBlock
                {
                    TextWrapping = TextWrapping.Wrap,
                    Foreground = SafeFindBrush("ForegroundBrush"),
                    Margin = new Thickness(0, 12, 0, 12)
                };

                var btnInfoOk = new Button
                {
                    Content = Lang.T("Dialog.Ok"),
                    Style = SafeFindStyle("RoundedButton"),
                    Width = 100,
                    Height = 38,
                    HorizontalAlignment = HorizontalAlignment.Center
                };
                _infoOkBtn = btnInfoOk;
                btnInfoOk.Click += (s, args) =>
                {
                    CloseInfoDialog();
                    _infoTcs?.TrySetResult(true);
                };

                Grid.SetRow(infoTitle, 0);
                Grid.SetRow(_infoMessage, 1);
                Grid.SetRow(btnInfoOk, 2);
                infoGrid.Children.Add(infoTitle);
                infoGrid.Children.Add(_infoMessage);
                infoGrid.Children.Add(btnInfoOk);

                infoPanel.Child = infoGrid;
                var infoOverlayGrid = new Grid();
                infoOverlayGrid.Children.Add(infoPanel);
                _infoDialog.Child = infoOverlayGrid;

                _rootGrid.Children.Add(_infoDialog);
                Grid.SetRowSpan(_infoDialog, int.MaxValue);
                Grid.SetColumnSpan(_infoDialog, int.MaxValue);
                // 应用本地化到详情弹窗按钮
                ApplyLocalizedTexts();

                StartBlobAnimation();
                StartAutoUpdateCheck();

                // ★ 应用自定义启动器背景（图片 / 视频）
                ApplyCustomBackground();
            }
            catch (Exception ex)
            {
                MessageBox.Show($"加载页面时出错: {ex.Message}\n\n{ex.StackTrace}", "严重错误", MessageBoxButton.OK, MessageBoxImage.Error);
                Application.Current.Shutdown();
            }
        }

        /// <summary>
        /// ★ 应用顶部栏和 IPC 状态栏的多语言文本
        /// </summary>
        private void ApplyTopBarTexts()
        {
            try
            {
                if (TxtAppTitle != null) TxtAppTitle.Text = Lang.T("App.Title");

                // 左侧导航（图标下的小字）
                if (TxtNavLaunch != null) TxtNavLaunch.Text = Lang.T("Tab.Launch");
                if (TxtNavStats != null) TxtNavStats.Text = Lang.T("Tab.Stats");
                if (TxtNavSettings != null) TxtNavSettings.Text = Lang.T("Tab.Settings");
                if (TxtNavAbout != null) TxtNavAbout.Text = Lang.T("Tab.About");

                // 首页主视觉
                if (TxtHomeBadge != null) TxtHomeBadge.Text = Lang.T("Home.Badge");
                if (TxtHomeTagline != null) TxtHomeTagline.Text = Lang.T("Home.Tagline");
                if (TxtHeroKicker != null) TxtHeroKicker.Text = Lang.T("Home.HeroKicker");
                if (TxtHeroTitle != null) TxtHeroTitle.Text = Lang.T("Home.HeroTitle");
                if (TxtHeroEn != null) TxtHeroEn.Text = Lang.T("Home.HeroEn");
                if (TxtMore != null) TxtMore.Text = Lang.T("Home.More");
                if (BtnPromoDetail != null) BtnPromoDetail.Content = Lang.T("Home.ViewDetail");
                if (TxtPromoKicker != null) TxtPromoKicker.Text = Lang.T("Home.PromoKicker");
                if (TxtNewsTab1 != null) TxtNewsTab1.Text = Lang.T("Home.News.Announcement");
                if (TxtNewsTab2 != null) TxtNewsTab2.Text = Lang.T("Home.News.News");
                if (TxtNewsTab3 != null) TxtNewsTab3.Text = Lang.T("Home.News.Info");
                if (TxtStartGame != null) TxtStartGame.Text = Lang.T("Home.StartGame");

                // 胶囊栏 / 版本库 / 设置导航
                if (TxtAccount != null) TxtAccount.Text = Lang.T("Shell.Account");
                if (TxtLibraryTitle != null) TxtLibraryTitle.Text = Lang.T("Home.LibraryTitle");
                if (TxtLibraryDesc != null) TxtLibraryDesc.Text = Lang.T("Home.LibraryDesc");
                if (BtnNavLauncher != null) BtnNavLauncher.Content = Lang.T("Home.SettingsNav.Launcher");
                if (BtnNavAbout != null) BtnNavAbout.Content = Lang.T("Tab.About");
                if (TxtSettingsVersion != null)
                    TxtSettingsVersion.Text = "v" + UpdateService.GetCurrentVersion().ToString();

                // 版本库排序控件（语言切换时重建，保留"最近 / 最常"排序能力）
                if (LibrarySortHost != null)
                {
                    LibrarySortHost.Children.Clear();
                    var sortControl = CreateCustomSortControl();
                    if (sortControl is FrameworkElement fe)
                    {
                        fe.Width = 128;
                        fe.Margin = new Thickness(0, 0, 0, 0);
                    }
                    LibrarySortHost.Children.Add(sortControl);
                }

                // 悬停提示
                if (BtnTabLaunch != null) BtnTabLaunch.ToolTip = Lang.T("Tab.Launch");
                if (BtnTabStats != null) BtnTabStats.ToolTip = Lang.T("Tab.Stats");
                if (BtnMenuGameSettings != null) BtnMenuGameSettings.Content = Lang.T("Menu.GameSettings");
                if (BtnMenuShortcut != null) BtnMenuShortcut.Content = Lang.T("Menu.CreateShortcut");
                if (BtnMenuVerify != null) BtnMenuVerify.Content = Lang.T("Menu.VerifyGame");
                if (BtnMenuClearCache != null) BtnMenuClearCache.Content = Lang.T("Menu.ClearCache");
                if (BtnTabSettings != null) BtnTabSettings.ToolTip = Lang.T("Tab.Settings");
                if (BtnTabAbout != null) BtnTabAbout.ToolTip = Lang.T("Tab.About");
                if (BtnAllGames != null) BtnAllGames.ToolTip = Lang.T("Home.LibraryTitle");
                if (BtnUtilLibrary != null) BtnUtilLibrary.ToolTip = Lang.T("Home.LibraryTitle");
                if (BtnUtilRefresh != null) BtnUtilRefresh.ToolTip = Lang.T("Home.Tip.Refresh");
                if (BtnUtilAdd != null) BtnUtilAdd.ToolTip = Lang.T("Launch.ManualAdd");
                if (BtnUtilFolder != null) BtnUtilFolder.ToolTip = Lang.T("Home.Tip.Folder");
                if (BtnUtilUpdate != null) BtnUtilUpdate.ToolTip = Lang.T("Home.Tip.Update");
                if (BtnUtilAbout != null) BtnUtilAbout.ToolTip = Lang.T("Tab.About");
                if (BtnStartMenu != null) BtnStartMenu.ToolTip = Lang.T("Home.LibraryTitle");
                if (BtnSettings != null) BtnSettings.ToolTip = Lang.T("Tab.Settings");
                if (TxtHomeStatus != null && _gameFiles.Count == 0) TxtHomeStatus.Text = Lang.T("Home.DownloadReady");

                if (TxtIpcFpsLabel != null) TxtIpcFpsLabel.Text = Lang.T("Ipc.Fps");
                if (TxtIpcScoreLabel != null) TxtIpcScoreLabel.Text = Lang.T("Ipc.Score");
                if (TxtIpcKillsLabel != null) TxtIpcKillsLabel.Text = Lang.T("Ipc.Kills");
                if (TxtIpcModeLabel != null) TxtIpcModeLabel.Text = Lang.T("Ipc.Mode");
                if (TxtIpcTimeLabel != null) TxtIpcTimeLabel.Text = Lang.T("Ipc.PlayTime");
                if (TxtIpcConnLabel != null) TxtIpcConnLabel.Text = Lang.T("Ipc.Connection");
            }
            catch { }
        }

        /// <summary>
        /// ★ 应用本地化到固定控件（详情弹窗按钮、对话框按钮）
        /// </summary>
        private void ApplyLocalizedTexts()
        {
            try
            {
                // 详情弹窗按钮
                if (BtnOpenFolder != null) BtnOpenFolder.Content = Lang.T("Detail.OpenFolder");
                if (BtnDeleteGame != null) BtnDeleteGame.Content = Lang.T("Detail.DeleteGame");

                // 兼容性对话框按钮
                if (_compatibilityOkBtn != null) _compatibilityOkBtn.Content = Lang.T("Dialog.Ok");

                // 确认对话框按钮
                if (_confirmYesBtn != null) _confirmYesBtn.Content = Lang.T("Dialog.Yes");
                if (_confirmNoBtn != null) _confirmNoBtn.Content = Lang.T("Dialog.No");

                // 信息对话框按钮
                if (_infoOkBtn != null) _infoOkBtn.Content = Lang.T("Dialog.Ok");
            }
            catch { }
        }

        // ========== 背景球体缓慢随机漂移 ==========
        private void StartBlobAnimation()
        {
            AnimateBlobLoop(BgBlob1Transform, 6.0, 11.0, 150);
            AnimateBlobLoop(BgBlob2Transform, 7.5, 13.0, 130);
            AnimateBlobLoop(BgBlob3Transform, 8.0, 15.0, 170);
        }

        private void AnimateBlobLoop(TranslateTransform transform, double minSec, double maxSec, double range)
        {
            if (transform == null) return;

            double targetX = (_blobRandom.NextDouble() - 0.5) * 2 * range;
            double targetY = (_blobRandom.NextDouble() - 0.5) * 2 * range;

            double seconds = minSec + _blobRandom.NextDouble() * (maxSec - minSec);
            var duration = TimeSpan.FromSeconds(seconds);

            double fromX = transform.X;
            double fromY = transform.Y;

            var animX = new DoubleAnimation(fromX, targetX, duration)
            {
                EasingFunction = new SineEase { EasingMode = EasingMode.EaseInOut },
                FillBehavior = FillBehavior.HoldEnd
            };
            var animY = new DoubleAnimation(fromY, targetY, duration)
            {
                EasingFunction = new SineEase { EasingMode = EasingMode.EaseInOut },
                FillBehavior = FillBehavior.HoldEnd
            };

            animX.Completed += (s, e) => AnimateBlobLoop(transform, minSec, maxSec, range);

            transform.BeginAnimation(TranslateTransform.XProperty, animX);
            transform.BeginAnimation(TranslateTransform.YProperty, animY);
        }

        /// <summary>启动渐入：窗口整体从透明淡入（系统关闭动画时直接显示）。</summary>
        private void BeginWindowFadeIn()
        {
            if (!SystemParameters.ClientAreaAnimation)
            {
                BeginAnimation(OpacityProperty, null);
                Opacity = 1;
                return;
            }

            Opacity = 0;
            var fadeIn = new DoubleAnimation(0, 1, TimeSpan.FromMilliseconds(1000))
            {
                EasingFunction = new CubicEase { EasingMode = EasingMode.EaseOut },
                FillBehavior = FillBehavior.HoldEnd,
            };
            fadeIn.Completed += (s, e) =>
            {
                try
                {
                    // 动画结束后把基值落到 1，后续关闭淡出从 1 开始，避免回到 0
                    BeginAnimation(OpacityProperty, null);
                    Opacity = 1;
                }
                catch { }
            };
            BeginAnimation(OpacityProperty, fadeIn);
        }

        protected override void OnClosing(System.ComponentModel.CancelEventArgs e)
        {
            // ★ 关闭渐出：先播放淡出动画，动画结束后再真正关闭
            if (!_allowClose)
            {
                if (_isFadingOut)
                {
                    e.Cancel = true;
                    return;
                }

                if (SystemParameters.ClientAreaAnimation && IsVisible &&
                    WindowState != WindowState.Minimized)
                {
                    e.Cancel = true;
                    _isFadingOut = true;

                    var fadeOut = new DoubleAnimation(Opacity, 0, TimeSpan.FromMilliseconds(1000))
                    {
                        EasingFunction = new CubicEase { EasingMode = EasingMode.EaseIn },
                    };
                    fadeOut.Completed += (s, args) =>
                    {
                        _allowClose = true;
                        _isFadingOut = false;
                        try { Close(); } catch { }
                    };
                    BeginAnimation(OpacityProperty, fadeOut);
                    return;
                }
            }

            base.OnClosing(e);
            StopBackgroundVideo();

            _config.WindowWidth = (int)this.Width;
            _config.WindowHeight = (int)this.Height;
            _config.WindowLeft = this.Left;
            _config.WindowTop = this.Top;
            ConfigManager.Save(_config);

            _playTimer?.Stop();
            _healthCheckTimer?.Stop();
            _performanceTimer?.Stop();
            _downloadCts?.Cancel();
            IpcService.Stop();
        }

        /// <summary>最小化时暂停背景视频，恢复窗口时继续播放，避免无谓解码占用。</summary>
        protected override void OnStateChanged(EventArgs e)
        {
            base.OnStateChanged(e);
            try
            {
                UpdateWindowClip();

                if (_bgMediaPlayer == null) return;
                if (WindowState == WindowState.Minimized)
                    _bgMediaPlayer.Pause();
                else if (_bgMediaPlayer.Source != null)
                    _bgMediaPlayer.Play();
            }
            catch { }
        }

        // ========== 安全获取资源 ==========
        private object SafeFindResource(object key)
        {
            try { return this.TryFindResource(key) ?? Application.Current.TryFindResource(key); }
            catch { return null; }
        }
        private Style SafeFindStyle(object key) => SafeFindResource(key) as Style ?? new Style();
        private Brush SafeFindBrush(object key) => SafeFindResource(key) as Brush ?? Brushes.Transparent;

        // ========== ★ 语言切换 ==========
        private void SwitchLanguage(string langCode)
        {
            if (Lang.CurrentLanguage == langCode) return;

            Lang.SetLanguage(langCode);
            _config.Language = langCode;
            ConfigManager.Save(_config);

            CloseReleaseNotesPanel();

            // 重建顶部栏
            ApplyTopBarTexts();

            // ★ 应用本地化到固定控件
            ApplyLocalizedTexts();

            // 重建当前标签页
            int currentTab = GetCurrentTabIndex();
            SelectTab(currentTab);

            ShowNotification(Lang.T("Settings.Language.Changed"));
        }

        private int GetCurrentTabIndex()
        {
            if (BtnTabLaunch?.Tag?.ToString() == "Selected") return 0;
            if (BtnTabStats?.Tag?.ToString() == "Selected") return 1;
            if (BtnTabSettings?.Tag?.ToString() == "Selected") return 2;
            if (BtnTabAbout?.Tag?.ToString() == "Selected") return 3;
            return 0;
        }

        // ========== 排序控件 ==========
        private UIElement CreateCustomSortControl()
        {
            _sortButton = new ToggleButton
            {
                Content = Lang.T("Launch.Sort.Default"),
                Style = SafeFindStyle("SortToggleStyle"),
                Width = 128,
                Height = 34,
            };

            _sortPopup = new Popup
            {
                PlacementTarget = _sortButton,
                Placement = PlacementMode.Bottom,
                StaysOpen = false,
                AllowsTransparency = true
            };

            _sortListBox = new ListBox
            {
                ItemsSource = new[]
                {
                    Lang.T("Launch.Sort.Default"),
                    Lang.T("Launch.Sort.Recent"),
                    Lang.T("Launch.Sort.MostPlayed")
                },
                Background = SafeFindBrush("CardBackgroundBrush"),
                BorderBrush = SafeFindBrush("CardBorderBrush"),
                BorderThickness = new Thickness(1),
                MinWidth = 120,
                ItemContainerStyle = SafeFindStyle("CustomListBoxItemStyle"),
                Padding = new Thickness(4)
            };
            _sortListBox.SelectionChanged += (s, e) =>
            {
                if (_sortListBox.SelectedItem != null)
                {
                    _sortButton.Content = _sortListBox.SelectedItem.ToString();
                    _sortPopup.IsOpen = false;
                    ApplySort();
                    RefreshCards();
                    UpdateHomePage();
                }
            };
            _sortPopup.Child = _sortListBox;
            _sortButton.Click += (s, e) => _sortPopup.IsOpen = !_sortPopup.IsOpen;
            return _sortButton;
        }

        // ========== 定时器事件 ==========
        private void PlayTimer_Tick(object sender, EventArgs e) => TxtPlayTime.Text = (DateTime.Now - _gameStartTime).ToString(@"hh\:mm\:ss");

        private void HealthCheck_Tick(object sender, EventArgs e)
        {
            if (_currentGameProcess != null && !_currentGameProcess.HasExited && !_currentGameProcess.Responding)
                Dispatcher.Invoke(() =>
                {
                    if (MessageBox.Show(Lang.T("Game.NotResponding"), Lang.T("Game.NotRespondingTitle"), MessageBoxButton.YesNo) == MessageBoxResult.Yes)
                        try { _currentGameProcess.Kill(); } catch { }
                });
        }

        // ========== 模式名转显示名 ==========
        private static string GetModeDisplayName(string mode)
        {
            if (string.IsNullOrEmpty(mode)) return "--";
            string key = mode.Trim().ToLowerInvariant();
            if (string.IsNullOrEmpty(key)) return "--";

            switch (key)
            {
                case "classic": return Lang.T("Mode.Classic");
                case "survival": return Lang.T("Mode.Survival");
                case "timed": return Lang.T("Mode.Timed");
                case "endless": return Lang.T("Mode.Endless");
                case "battle": return Lang.T("Mode.Battle");
                case "multiplayer": return Lang.T("Mode.Multiplayer");
                case "team4v4": return Lang.T("Mode.Team4v4");
                case "extreme": return Lang.T("Mode.Extreme");
                case "extraction": return Lang.T("Mode.Extraction");
                default: return key;
            }
        }

        // ========== IPC 事件 ==========
        private void OnStatsReceived(GameStatsData stats)
        {
            Dispatcher.Invoke(() =>
            {
                TxtFps.Text = stats.Fps.ToString();
                TxtScore.Text = stats.Score.ToString();
                TxtKills.Text = stats.Kills.ToString();
                TxtMode.Text = GetModeDisplayName(stats.Mode);

                StatusLight.Fill = new SolidColorBrush(Color.FromRgb(0x34, 0xC7, 0x59));
                TxtStatus.Text = Lang.T("Ipc.Connected");
                _lastScore = stats.Score;
                _lastKills = stats.Kills;
            });
        }

        private void OnIpcDisconnected()
        {
            Dispatcher.Invoke(() =>
            {
                _playTimer.Stop(); _healthCheckTimer.Stop(); _performanceTimer.Stop();
                IpcStatusBar.Visibility = Visibility.Collapsed;
            });
        }

        // ========== 游戏启动 ==========
        private async Task LaunchGame(string filePath, bool isPython)
        {
            // ========== 1. 已有游戏在运行时先处理 ==========
            if (_currentGameProcess != null && !_currentGameProcess.HasExited)
            {
                bool killOld = await ShowConfirmDialogAsync(Lang.T("Game.AlreadyRunning"));
                if (killOld)
                {
                    try
                    {
                        _currentGameProcess.Exited -= OnGameProcessExited;
                        _currentGameProcess.Kill();
                        await Task.Run(() => _currentGameProcess.WaitForExit(3000));
                        if (!_currentGameProcess.HasExited)
                            _currentGameProcess.Close();
                    }
                    catch (Exception ex) { Debug.WriteLine($"终止旧进程失败: {ex.Message}"); }
                    finally
                    {
                        _currentGameProcess?.Dispose();
                        _currentGameProcess = null;
                        _playTimer?.Stop();
                        _healthCheckTimer?.Stop();
                        _performanceTimer?.Stop();
                        IpcService.Stop();
                        IpcStatusBar.Visibility = Visibility.Collapsed;
                        SetGameRunning(false);
                    }
                }
                else return;
            }

            // ============================================================
            // ★ 2. 检测游戏文件是否存在；不存在则尝试自动下载
            // ============================================================
            if (!File.Exists(filePath))
            {
                string newPath = await EnsureGameExistsAsync(filePath, isPython);
                if (string.IsNullOrEmpty(newPath))
                {
                    // 用户取消，或下载失败，直接返回
                    return;
                }
                filePath = newPath;
            }

            try
            {
                // ========== 3. 在已扫描列表中查找游戏信息 ==========
                var gameInfo = _gameFiles.FirstOrDefault(g =>
                    string.Equals(g.FullPath, filePath, StringComparison.OrdinalIgnoreCase)
                    && g.IsPython == isPython);

                if (gameInfo == null)
                {
                    MessageBox.Show(Lang.T("Game.Unknown"), Lang.T("Game.UnknownTitle"),
                        MessageBoxButton.OK, MessageBoxImage.Warning);
                    return;
                }

                // ============================================================
                // ★ 4. 反作弊：校验游戏 exe 哈希（仅非 Python）
                // ============================================================
                if (!isPython)
                {
                    string tamperErr = AntiCheat.VerifyGameExe(filePath);
                    if (tamperErr != null)
                    {
                        await ShowCompatibilityDialogAsync(
                            "⚠ 游戏文件完整性校验失败，已阻止启动。\n\n" +
                            tamperErr + "\n\n" +
                            "如果你是自己修改过的版本，请同步更新启动器目录下的 game_hashes.json；\n" +
                            "否则请从官方渠道重新下载游戏。");
                        return;
                    }
                }

                // ========== 5. 版本兼容性检查 ==========
                if (!IsVersionCompatible(gameInfo.Version))
                {
                    await ShowCompatibilityDialogAsync(Lang.T("Dialog.CompatibilityMsg"));
                }

                // ========== 6. 启动游戏进程 ==========
                _currentGameProcess = GameLauncher.StartProcess(filePath, isPython);
                if (_currentGameProcess == null)
                {
                    MessageBox.Show(Lang.T("Game.StartFailed"), Lang.T("Game.StartFailedTitle"),
                        MessageBoxButton.OK, MessageBoxImage.Error);
                    return;
                }

                _gameStartTime = DateTime.Now;
                _lastScore = _lastKills = 0;
                _fpsHistory.Clear();
                _memoryHistory.Clear();
                _logBuilder.Clear();

                GameStatsManager.RecordLaunch(filePath);

                IpcStatusBar.Visibility = Visibility.Visible;
                TxtFps.Text = "--";
                TxtScore.Text = "0";
                TxtKills.Text = "0";
                TxtMode.Text = "--";
                TxtPlayTime.Text = "00:00:00";
                StatusLight.Fill = new SolidColorBrush(Colors.Gray);
                TxtStatus.Text = Lang.T("Ipc.Waiting");

                // 启动 IPC 服务（内部会重置 SessionTracker）
                _ = IpcService.StartAsync();

                _playTimer.Start();
                _healthCheckTimer.Start();
                _performanceTimer.Start();

                _ = Task.Run(() => ReadStream(_currentGameProcess.StandardOutput));
                _ = Task.Run(() => ReadStream(_currentGameProcess.StandardError));

                _currentGameProcess.EnableRaisingEvents = true;
                _currentGameProcess.Exited += OnGameProcessExited;

                SetGameRunning(true);
                ShowNotification(Lang.T("Game.Launching"));
            }
            catch (Exception ex)
            {
                MessageBox.Show(Lang.T("Game.LaunchError", ex.Message), "Error",
                    MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        /// <summary>
        /// 检测游戏文件是否存在；不存在则尝试从 GitHub 自动下载并重新安装。
        /// 返回：重新扫描后可用的游戏路径；失败或用户取消返回 null。
        /// </summary>
        private async Task<string> EnsureGameExistsAsync(string originalPath, bool isPython)
        {
            // ========== 1. 询问用户 ==========
            string fileName = Path.GetFileName(originalPath);
            bool download = await ShowConfirmDialogAsync(
                $"未找到游戏文件：\n{fileName}\n\n" +
                $"完整路径：\n{originalPath}\n\n" +
                "该文件可能已被移动或删除。\n\n" +
                "是否从 GitHub 自动下载并重新安装？");

            if (!download) return null;

            // ========== 2. 推断目标版本号 ==========
            Version targetVersion = ExtractVersionFromPath(originalPath);
            if (targetVersion != null)
            {
                Debug.WriteLine($"从路径推断版本：{targetVersion}");
            }

            // ========== 3. 选择仓库 ==========
            GitHubRepoConfig repo = null;
            try
            {
                repo = isPython
                    ? GitHubReleaseService.Repos.FirstOrDefault(r => r.IsPythonRepo)
                    : GitHubReleaseService.Repos.FirstOrDefault(r => !r.IsPythonRepo);

                // 兜底：如果只有一个仓库，用它
                if (repo == null && GitHubReleaseService.Repos.Count > 0)
                    repo = GitHubReleaseService.Repos[0];
            }
            catch { }

            if (repo == null)
            {
                ShowDetailPanel("下载失败", "启动器未配置可用的游戏仓库。");
                return null;
            }

            // ========== 4. 拉取 Release 列表 ==========
            List<GitHubRelease> releases = null;
            try
            {
                ShowNotification("正在从 GitHub 查找可用版本...");
                releases = await GitHubReleaseService.GetReleasesAsync(repo);
            }
            catch (Exception ex)
            {
                ShowDetailPanel("下载失败", $"无法获取版本列表：\n{ex.Message}");
                return null;
            }

            if (releases == null || releases.Count == 0)
            {
                ShowDetailPanel("下载失败", "GitHub 上暂无可用版本。");
                return null;
            }

            // ========== 5. 找到匹配的 Release ==========
            GitHubRelease targetRelease = FindMatchingRelease(releases, targetVersion);

            if (targetRelease == null)
            {
                ShowDetailPanel("下载失败", "未找到匹配的版本，且无可用回退版本。");
                return null;
            }

            // ========== 6. 找到匹配的 asset ==========
            // ★ 按当前系统架构优先挑选：Windows64 → Windows32 → ARM64，同架构取最高版本
            GitHubReleaseAsset asset = GitHubReleaseService.PickBestAsset(targetRelease.Assets);

            if (asset == null)
            {
                ShowDetailPanel("下载失败",
                    $"版本 {targetRelease.TagName} 中没有符合命名规范的游戏包。");
                return null;
            }

            // ========== 7. 静默下载 + 安装 ==========
            string installedFolder = await DownloadAndInstallAssetSilentlyAsync(asset, targetRelease);
            if (string.IsNullOrEmpty(installedFolder)) return null;

            // ========== 8. 重新扫描 ==========
            await ScanGamesAsync();

            // ========== 9. 在新列表里查找 ==========
            var newGame = _gameFiles.FirstOrDefault(g =>
                g.IsPython == isPython
                && (asset.ParsedVersion == null || g.Version == asset.ParsedVersion));

            if (newGame == null)
            {
                // 兜底：按文件名再找一次
                string newFileName = Path.GetFileName(originalPath);
                newGame = _gameFiles.FirstOrDefault(g =>
                    g.IsPython == isPython
                    && string.Equals(Path.GetFileName(g.FullPath), newFileName,
                        StringComparison.OrdinalIgnoreCase));
            }

            if (newGame == null)
            {
                ShowDetailPanel("下载完成但扫描不到",
                    "游戏已下载解压，但未在扫描列表中找到。\n\n" +
                    "你可以手动到下载目录查看，或点击\"刷新\"。");
                return null;
            }

            ShowNotification($"已重新安装 {fileName}");
            return newGame.FullPath;
        }

        /// <summary>
        /// 从文件路径推断版本号。
        /// 支持：
        ///   ...\7.0.0\SnakeGame.exe    → 7.0.0
        ///   ...\1.0.0\贪吃蛇(1.0.0).py → 1.0.0
        ///   SnakeGameWpf_7.0.0.0.exe   → 7.0.0.0
        /// </summary>
        private static Version ExtractVersionFromPath(string filePath)
        {
            if (string.IsNullOrEmpty(filePath)) return null;

            try
            {
                // 优先从父目录名解析
                string parentDir = Path.GetDirectoryName(filePath);
                if (!string.IsNullOrEmpty(parentDir))
                {
                    string dirName = Path.GetFileName(parentDir);
                    var m = Regex.Match(dirName, @"^(\d+)\.(\d+)\.(\d+)$");
                    if (m.Success)
                    {
                        return new Version(
                            int.Parse(m.Groups[1].Value),
                            int.Parse(m.Groups[2].Value),
                            int.Parse(m.Groups[3].Value));
                    }
                }

                // 回退：从文件名解析
                string fileName = Path.GetFileName(filePath);
                var m2 = Regex.Match(fileName, @"(\d+)\.(\d+)\.(\d+)");
                if (m2.Success)
                {
                    return new Version(
                        int.Parse(m2.Groups[1].Value),
                        int.Parse(m2.Groups[2].Value),
                        int.Parse(m2.Groups[3].Value));
                }
            }
            catch { }

            return null;
        }

        /// <summary>
        /// 在 Release 列表里找匹配的版本。
        /// 找不到精确匹配时回退到最新版。
        /// </summary>
        private static GitHubRelease FindMatchingRelease(List<GitHubRelease> releases, Version targetVersion)
        {
            if (releases == null || releases.Count == 0) return null;

            // 精确匹配目标版本
            if (targetVersion != null)
            {
                var matched = releases.FirstOrDefault(r => r.ParsedVersion == targetVersion);
                if (matched != null) return matched;
            }

            // 回退：最新版
            return releases
                .OrderByDescending(r => r.ParsedVersion ?? new Version(0, 0, 0, 0))
                .FirstOrDefault();
        }

        /// <summary>
        /// 静默下载并安装 asset（不弹路径确认对话框）。
        /// 用于"文件缺失时自动重装"的场景。
        /// 返回 true 表示下载、校验、解压全部成功。
        /// </summary>
        /// <summary>下载并静默安装一个游戏包；成功返回版本目录名（如 9.0.0），失败返回 null。</summary>
        private async Task<string> DownloadAndInstallAssetSilentlyAsync(
            GitHubReleaseAsset asset, GitHubRelease release, Action<string, double> onProgress = null)
        {
            void Report(string stage, double percent) => onProgress?.Invoke(stage, percent);

            try
            {
                if (asset == null || !asset.IsGamePackage)
                {
                    ShowDetailPanel(Lang.T("Home.DownloadFailedTitle"), Lang.T("Home.DownloadInvalidAsset"));
                    return null;
                }

                string downloadDir = ResolveDownloadDirectory();
                Directory.CreateDirectory(downloadDir);
                string zipPath = Path.Combine(downloadDir, asset.Name);

                // 清理旧文件
                if (File.Exists(zipPath))
                {
                    try { File.Delete(zipPath); } catch { }
                }

                // ========== 下载 ==========
                Report(Lang.T("Home.Downloading"), 0);
                ShowNotification(Lang.T("Download.Checking", asset.Name));
                var progress = new Progress<double>(p =>
                {
                    Report(Lang.T("Home.Downloading"), p);
                    ShowNotification(Lang.T("Download.Progress", asset.Name, p));
                });
                await DownloadWithProgressAsync(asset.BrowserDownloadUrl, zipPath, progress);

                // ========== 校验 ==========
                var (isValid, message, rootFiles) = ValidateGamePackage(zipPath);
                if (!isValid)
                {
                    try { File.Delete(zipPath); } catch { }
                    ShowDetailPanel(Lang.T("Validate.Title"), Lang.T("Validate.Failed", message, rootFiles));
                    return null;
                }

                // ========== 解压 ==========
                string versionFolder = asset.ParsedVersion?.ToString(3)
                    ?? release?.ParsedVersion?.ToString(3)
                    ?? "unknown";
                string extractDir = Path.Combine(downloadDir, versionFolder);

                if (Directory.Exists(extractDir))
                {
                    try
                    {
                        foreach (var f in Directory.GetFiles(extractDir, "*", SearchOption.AllDirectories))
                        {
                            try { File.SetAttributes(f, FileAttributes.Normal); } catch { }
                        }
                        Directory.Delete(extractDir, true);
                    }
                    catch { }
                }
                Directory.CreateDirectory(extractDir);

                Report(Lang.T("Home.DownloadInstalling", versionFolder), 100);
                ShowNotification(Lang.T("Download.Extracting", versionFolder));
                await Task.Run(() =>
                {
                    using (var archive = ZipFile.OpenRead(zipPath))
                    {
                        foreach (ZipArchiveEntry entry in archive.Entries)
                        {
                            string destPath = Path.GetFullPath(
                                Path.Combine(extractDir, entry.FullName));

                            if (!destPath.StartsWith(extractDir, StringComparison.OrdinalIgnoreCase))
                                throw new InvalidOperationException("Invalid path: out of extract dir");

                            if (string.IsNullOrEmpty(entry.Name))
                            {
                                Directory.CreateDirectory(destPath);
                            }
                            else
                            {
                                Directory.CreateDirectory(Path.GetDirectoryName(destPath));
                                entry.ExtractToFile(destPath, overwrite: true);
                            }
                        }
                    }
                });
                FlattenSingleSubfolder(extractDir);

                // ========== 删除 zip ==========
                try { File.Delete(zipPath); } catch { }

                // ========== 确保下载目录在扫描列表里 ==========
                if (!_config.Directories.Any(d =>
                        string.Equals(d, downloadDir, StringComparison.OrdinalIgnoreCase)))
                {
                    _config.Directories.Add(downloadDir);
                    ConfigManager.Save(_config);
                }

                // ========== Python 依赖 ==========
                if (asset.RepoConfig != null && asset.RepoConfig.IsPythonRepo)
                {
                    try { await EnsurePythonDependenciesAsync(); }
                    catch { /* 依赖安装失败不阻塞下载 */ }
                }

                return versionFolder;
            }
            catch (Exception ex)
            {
                ShowDetailPanel(Lang.T("Home.DownloadFailedTitle"), ex.Message);
                return null;
            }
        }

        /// <summary>下载目录：优先配置的下载路径，否则回退到系统临时目录。</summary>
        private string ResolveDownloadDirectory()
        {
            string dir = _config.DownloadPath;
            if (string.IsNullOrWhiteSpace(dir))
                dir = Path.Combine(Path.GetTempPath(), "SnakeGameDownloads");
            return dir;
        }

        // ==================== ★ 一键下载并安装最新版（未检测到游戏时） ====================

        /// <summary>当前系统优先使用的包架构：arm64 / x64 / x86。</summary>
        private static string GetPreferredArchitecture()
        {
            var osArch = System.Runtime.InteropServices.RuntimeInformation.OSArchitecture;
            if (osArch == System.Runtime.InteropServices.Architecture.Arm64) return "arm64";
            return Environment.Is64BitOperatingSystem ? "x64" : "x86";
        }

        private string GetArchDisplayName()
        {
            var osArch = System.Runtime.InteropServices.RuntimeInformation.OSArchitecture;
            if (osArch == System.Runtime.InteropServices.Architecture.Arm64) return Lang.T("Home.ArchArm64");
            return Environment.Is64BitOperatingSystem ? Lang.T("Home.Arch64") : Lang.T("Home.Arch32");
        }

        /// <summary>
        /// 在所有仓库/发行版中挑选"最新且适配本机"的 Windows 游戏包：
        /// 正式版优先，其次预发布版；同组按版本号从高到低。
        /// </summary>
        private async Task<(GitHubRelease Release, GitHubReleaseAsset Asset)> FindLatestGameAssetAsync(bool? preferPython = null)
        {
            string arch = GetPreferredArchitecture();
            var candidates = new List<(GitHubRelease Release, GitHubReleaseAsset Asset)>();

            foreach (var repo in GitHubReleaseService.Repos)
            {
                if (preferPython.HasValue && repo.IsPythonRepo != preferPython.Value) continue;
                try
                {
                    var releases = await GitHubReleaseService.GetReleasesAsync(repo);
                    foreach (var rel in releases)
                    {
                        var asset = GitHubReleaseService.PickBestAsset(rel.Assets, arch, "windows");
                        if (asset != null) candidates.Add((rel, asset));
                    }
                }
                catch (Exception ex)
                {
                    Debug.WriteLine($"获取仓库 {repo.DisplayName} 发行版失败: {ex.Message}");
                }
            }

            if (candidates.Count == 0) return (null, null);

            Version VerOf((GitHubRelease Release, GitHubReleaseAsset Asset) c)
                => c.Asset?.ParsedVersion ?? c.Release?.ParsedVersion ?? new Version(0, 0, 0, 0);

            // 正式版优先；没有正式版再用最新的预发布版
            var stable = candidates
                .Where(c => c.Release != null && !c.Release.Prerelease)
                .OrderByDescending(VerOf)
                .ThenByDescending(c => c.Release.PublishedAt)
                .FirstOrDefault();
            if (stable.Asset != null) return stable;

            return candidates
                .OrderByDescending(VerOf)
                .ThenByDescending(c => c.Release?.PublishedAt ?? DateTime.MinValue)
                .First();
        }

        private void SetStartButtonBusy(string mainText, string subText)
        {
            if (BtnStartGame != null) BtnStartGame.IsEnabled = false;
            if (BtnStartMenu != null) BtnStartMenu.IsEnabled = false;
            if (TxtStartGame != null && mainText != null) TxtStartGame.Text = mainText;
            if (TxtStartVersion != null && subText != null) TxtStartVersion.Text = subText;
            if (TxtHomeStatus != null) TxtHomeStatus.Text = Lang.T("Home.DownloadBusy");
        }

        private void ResetStartButton()
        {
            if (BtnStartGame != null) BtnStartGame.IsEnabled = true;
            if (BtnStartMenu != null) BtnStartMenu.IsEnabled = true;
        }

        /// <summary>未检测到游戏时点击"下载游戏"：自动下载并安装最新发布版。</summary>
        private async Task DownloadAndInstallLatestGameAsync(bool? preferPython = null)
        {
            if (_autoDownloadBusy) return;
            _autoDownloadBusy = true;
            try
            {
                SetStartButtonBusy(_gameUpdateAvailable ? Lang.T("Home.UpdateGame") : Lang.T("Home.DownloadGame"),
                    Lang.T("Home.DownloadFetchingSub"));

                GitHubRelease release;
                GitHubReleaseAsset asset;

                // 按钮上显示的是哪个版本就安装哪个版本（含预发布），避免"提示 beta 却装了旧正式版"
                if (_gameUpdateAvailable && _latestGameRelease != null && _latestGameAsset != null
                    && (!preferPython.HasValue || _latestGameRelease.RepoConfig?.IsPythonRepo == preferPython.Value))
                {
                    release = _latestGameRelease;
                    asset = _latestGameAsset;
                }
                else
                {
                    (release, asset) = await FindLatestGameAssetAsync(preferPython);
                }
                if (asset == null)
                {
                    ShowDetailPanel(Lang.T("Home.DownloadFailedTitle"),
                        Lang.T("Home.DownloadNoAsset", GetArchDisplayName()));
                    return;
                }

                SetStartButtonBusy(Lang.T("Home.Downloading"),
                    Lang.T("Home.DownloadForArch", GetArchDisplayName()));

                string versionFolder = await DownloadAndInstallAssetSilentlyAsync(
                    asset, release,
                    (stage, percent) =>
                    {
                        if (TxtStartGame != null) TxtStartGame.Text = stage;
                        if (TxtStartVersion != null)
                            TxtStartVersion.Text = Lang.T("Home.DownloadProgress", percent);
                    });

                if (string.IsNullOrEmpty(versionFolder)) return;

                await ScanGamesAsync();

                // 选中刚刚安装的版本
                string expectedRoot = Path.Combine(ResolveDownloadDirectory(), versionFolder);
                var installed = _gameFiles.FirstOrDefault(g =>
                    g.FullPath.StartsWith(expectedRoot, StringComparison.OrdinalIgnoreCase));
                if (installed != null) _selectedGame = installed;

                ShowNotification(Lang.T("Home.DownloadDone", versionFolder));
            }
            catch (Exception ex)
            {
                ShowDetailPanel(Lang.T("Home.DownloadFailedTitle"), ex.Message);
            }
            finally
            {
                _autoDownloadBusy = false;
                ResetStartButton();
                UpdateHomePage();
            }
        }

        private async void ReadStream(StreamReader reader)
        {
            try
            {
                while (!reader.EndOfStream)
                {
                    string line = await reader.ReadLineAsync();
                    if (line != null) Dispatcher.Invoke(() => _logBuilder.AppendLine(line));
                }
            }
            catch { }
        }

        private void OnGameProcessExited(object sender, EventArgs e)
        {
            Dispatcher.InvokeAsync(() =>
            {
                _playTimer.Stop(); _healthCheckTimer.Stop(); _performanceTimer.Stop();
                IpcService.Stop();
                IpcStatusBar.Visibility = Visibility.Collapsed;

                // ★ 游戏已退出：恢复开始按钮
                SetGameRunning(false);

                double minutes = (DateTime.Now - _gameStartTime).TotalMinutes;
                if (_currentGameProcess != null)
                {
                    string filePath = _currentGameProcess.StartInfo.FileName;
                    if (_currentGameProcess.StartInfo.Arguments.StartsWith("\""))
                        filePath = _currentGameProcess.StartInfo.Arguments.Trim('"');
                    GameStatsManager.RecordPlayDuration(filePath, minutes);
                    GameStatsManager.AddSession(new GameSessionRecord
                    {
                        StartTime = _gameStartTime,
                        DurationMinutes = minutes,
                        FinalScore = _lastScore,
                        FinalKills = _lastKills,
                        Mode = TxtMode.Text,
                        GamePath = filePath
                    });
                    int exitCode = _currentGameProcess.ExitCode;
                    _currentGameProcess.Dispose();
                    _currentGameProcess = null;
                    if (exitCode != 0)
                    {
                        string log = _logBuilder.ToString();
                        string crashMessage = Lang.T("Game.CrashedMsg", exitCode,
                            string.IsNullOrEmpty(log) ? Lang.T("Game.NoOutput") : log);
                        ShowDetailPanel(Lang.T("Game.Crashed"), crashMessage);
                    }
                }
            });
        }

        private void PerformanceTimer_Tick(object sender, EventArgs e)
        {
            if (_currentGameProcess != null && !_currentGameProcess.HasExited)
            {
                _currentGameProcess.Refresh();
                long memory = _currentGameProcess.WorkingSet64 / (1024 * 1024);
                _memoryHistory.Add(memory);
                int fps = 0;
                Dispatcher.Invoke(() => int.TryParse(TxtFps.Text, out fps));
                _fpsHistory.Add(fps);
                if (_fpsHistory.Count > 60) _fpsHistory.RemoveAt(0);
                if (_memoryHistory.Count > 60) _memoryHistory.RemoveAt(0);
            }
        }

        // ========== 通知 ==========
        public void ShowNotification(string message)
        {
            NotificationText.Text = message;

            if (_notificationTimer == null)
            {
                _notificationTimer = new System.Windows.Threading.DispatcherTimer
                {
                    Interval = TimeSpan.FromSeconds(3)
                };
                _notificationTimer.Tick += (s, ev) =>
                {
                    _notificationTimer.Stop();
                    HideNotification();
                };
            }
            else
            {
                _notificationTimer.Stop();
            }

            NotificationBar.UpdateLayout();
            double exitOffset = NotificationBar.ActualWidth > 0
                ? NotificationBar.ActualWidth + 40
                : 300;

            NotificationTransform.X = exitOffset;

            var slideIn = new DoubleAnimation
            {
                To = 0,
                Duration = TimeSpan.FromMilliseconds(450),
                EasingFunction = new CubicEase { EasingMode = EasingMode.EaseOut }
            };
            var fadeIn = new DoubleAnimation(0, 1, TimeSpan.FromMilliseconds(220));

            NotificationBar.BeginAnimation(OpacityProperty, fadeIn);
            NotificationTransform.BeginAnimation(TranslateTransform.XProperty, slideIn);

            _notificationTimer.Start();
        }

        private void HideNotification()
        {
            double exitOffset = NotificationBar.ActualWidth > 0
                ? NotificationBar.ActualWidth + 40
                : 300;

            var slideOut = new DoubleAnimation
            {
                To = exitOffset,
                Duration = TimeSpan.FromMilliseconds(320),
                EasingFunction = new QuadraticEase { EasingMode = EasingMode.EaseIn }
            };
            var fadeOut = new DoubleAnimation(1, 0, TimeSpan.FromMilliseconds(220));

            NotificationTransform.BeginAnimation(TranslateTransform.XProperty, slideOut);
            NotificationBar.BeginAnimation(OpacityProperty, fadeOut);
        }

        // ========== 详情面板 ==========
        public void ShowDetailPanel(string title, string message)
        {
            DetailTitle.Text = title;
            DetailTextBox.Text = message;
            DetailOverlay.Visibility = Visibility.Visible;
            var overlayFadeIn = new DoubleAnimation(0, 1, TimeSpan.FromMilliseconds(220));
            DetailOverlay.BeginAnimation(OpacityProperty, overlayFadeIn);
            var scaleXAnim = new DoubleAnimation(0.96, 1.0, TimeSpan.FromMilliseconds(200))
            { EasingFunction = new CubicEase { EasingMode = EasingMode.EaseOut } };
            var scaleYAnim = scaleXAnim.Clone();
            DetailScale.BeginAnimation(ScaleTransform.ScaleXProperty, scaleXAnim);
            DetailScale.BeginAnimation(ScaleTransform.ScaleYProperty, scaleYAnim);
        }

        private void HideDetailPanel()
        {
            var scaleXOut = new DoubleAnimation(1.0, 0.8, TimeSpan.FromMilliseconds(200))
            { EasingFunction = new QuadraticEase { EasingMode = EasingMode.EaseIn } };
            var scaleYOut = scaleXOut.Clone();
            var overlayFadeOut = new DoubleAnimation(1, 0, TimeSpan.FromMilliseconds(200));
            overlayFadeOut.Completed += (s, e) => DetailOverlay.Visibility = Visibility.Collapsed;
            DetailScale.BeginAnimation(ScaleTransform.ScaleXProperty, scaleXOut);
            DetailScale.BeginAnimation(ScaleTransform.ScaleYProperty, scaleYOut);
            DetailOverlay.BeginAnimation(OpacityProperty, overlayFadeOut);
        }

        private void DetailOverlay_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        { if (e.OriginalSource == DetailOverlay) HideDetailPanel(); }
        private void CloseDetailPanel_Click(object sender, RoutedEventArgs e) => HideDetailPanel();

        // ========== 确认对话框 ==========
        private void CloseConfirmDialog()
        {
            var fadeOut = new DoubleAnimation(1, 0, TimeSpan.FromMilliseconds(150));
            fadeOut.Completed += (s, e) => _confirmDialog.Visibility = Visibility.Collapsed;
            var scaleXOut = new DoubleAnimation(1.0, 0.8, TimeSpan.FromMilliseconds(150))
            { EasingFunction = new QuadraticEase { EasingMode = EasingMode.EaseIn } };
            var scaleYOut = new DoubleAnimation(1.0, 0.8, TimeSpan.FromMilliseconds(150))
            { EasingFunction = new QuadraticEase { EasingMode = EasingMode.EaseIn } };

            _confirmDialog.BeginAnimation(OpacityProperty, fadeOut);
            var transform = (_confirmDialog.Child as Grid)?.Children[0]?.RenderTransform as ScaleTransform;
            transform?.BeginAnimation(ScaleTransform.ScaleXProperty, scaleXOut);
            transform?.BeginAnimation(ScaleTransform.ScaleYProperty, scaleYOut);
        }

        private Task<bool> ShowConfirmDialogAsync(string message)
        {
            _confirmTcs = new TaskCompletionSource<bool>();
            _confirmMessage.Text = message;

            _confirmDialog.Visibility = Visibility.Visible;
            var fadeIn = new DoubleAnimation(0, 1, TimeSpan.FromMilliseconds(200));
            var scaleXAnim = new DoubleAnimation(0.8, 1.0, TimeSpan.FromMilliseconds(280))
            { EasingFunction = new CubicEase { EasingMode = EasingMode.EaseOut } };
            var scaleYAnim = new DoubleAnimation(0.8, 1.0, TimeSpan.FromMilliseconds(280))
            { EasingFunction = new CubicEase { EasingMode = EasingMode.EaseOut } };

            _confirmDialog.BeginAnimation(OpacityProperty, fadeIn);
            var transform = (_confirmDialog.Child as Grid)?.Children[0]?.RenderTransform as ScaleTransform;
            transform?.BeginAnimation(ScaleTransform.ScaleXProperty, scaleXAnim);
            transform?.BeginAnimation(ScaleTransform.ScaleYProperty, scaleYAnim);

            return _confirmTcs.Task;
        }

        // ========== 兼容性对话框 ==========
        private void CloseCompatibilityDialog()
        {
            var fadeOut = new DoubleAnimation(1, 0, TimeSpan.FromMilliseconds(150));
            fadeOut.Completed += (s, e) => _compatibilityDialog.Visibility = Visibility.Collapsed;
            var scaleXOut = new DoubleAnimation(1.0, 0.8, TimeSpan.FromMilliseconds(150))
            { EasingFunction = new QuadraticEase { EasingMode = EasingMode.EaseIn } };
            var scaleYOut = new DoubleAnimation(1.0, 0.8, TimeSpan.FromMilliseconds(150))
            { EasingFunction = new QuadraticEase { EasingMode = EasingMode.EaseIn } };

            _compatibilityDialog.BeginAnimation(OpacityProperty, fadeOut);
            var transform = (_compatibilityDialog.Child as Grid)?.Children[0]?.RenderTransform as ScaleTransform;
            transform?.BeginAnimation(ScaleTransform.ScaleXProperty, scaleXOut);
            transform?.BeginAnimation(ScaleTransform.ScaleYProperty, scaleYOut);
        }

        private Task ShowCompatibilityDialogAsync(string message)
        {
            _compatibilityTcs = new TaskCompletionSource<bool>();
            _compatibilityMessage.Text = message;

            _compatibilityDialog.Visibility = Visibility.Visible;
            var fadeIn = new DoubleAnimation(0, 1, TimeSpan.FromMilliseconds(200));
            var scaleXAnim = new DoubleAnimation(0.8, 1.0, TimeSpan.FromMilliseconds(280))
            { EasingFunction = new CubicEase { EasingMode = EasingMode.EaseOut } };
            var scaleYAnim = new DoubleAnimation(0.8, 1.0, TimeSpan.FromMilliseconds(280))
            { EasingFunction = new CubicEase { EasingMode = EasingMode.EaseOut } };

            _compatibilityDialog.BeginAnimation(OpacityProperty, fadeIn);
            var transform = (_compatibilityDialog.Child as Grid)?.Children[0]?.RenderTransform as ScaleTransform;
            transform?.BeginAnimation(ScaleTransform.ScaleXProperty, scaleXAnim);
            transform?.BeginAnimation(ScaleTransform.ScaleYProperty, scaleYAnim);

            return _compatibilityTcs.Task;
        }

        // ========== 信息对话框 ==========
        private void CloseInfoDialog()
        {
            if (_infoDialog == null) return;
            var fadeOut = new DoubleAnimation(1, 0, TimeSpan.FromMilliseconds(150));
            fadeOut.Completed += (s, e) => _infoDialog.Visibility = Visibility.Collapsed;
            var scaleXOut = new DoubleAnimation(1.0, 0.8, TimeSpan.FromMilliseconds(150))
            { EasingFunction = new QuadraticEase { EasingMode = EasingMode.EaseIn } };
            var scaleYOut = new DoubleAnimation(1.0, 0.8, TimeSpan.FromMilliseconds(150))
            { EasingFunction = new QuadraticEase { EasingMode = EasingMode.EaseIn } };

            _infoDialog.BeginAnimation(OpacityProperty, fadeOut);
            var transform = (_infoDialog.Child as Grid)?.Children[0]?.RenderTransform as ScaleTransform;
            transform?.BeginAnimation(ScaleTransform.ScaleXProperty, scaleXOut);
            transform?.BeginAnimation(ScaleTransform.ScaleYProperty, scaleYOut);
        }

        private Task ShowInfoDialogAsync(string message)
        {
            _infoTcs = new TaskCompletionSource<bool>();
            _infoMessage.Text = message;

            _infoDialog.Visibility = Visibility.Visible;
            var fadeIn = new DoubleAnimation(0, 1, TimeSpan.FromMilliseconds(200));
            var scaleXAnim = new DoubleAnimation(0.8, 1.0, TimeSpan.FromMilliseconds(280))
            { EasingFunction = new CubicEase { EasingMode = EasingMode.EaseOut } };
            var scaleYAnim = new DoubleAnimation(0.8, 1.0, TimeSpan.FromMilliseconds(280))
            { EasingFunction = new CubicEase { EasingMode = EasingMode.EaseOut } };

            _infoDialog.BeginAnimation(OpacityProperty, fadeIn);
            var transform = (_infoDialog.Child as Grid)?.Children[0]?.RenderTransform as ScaleTransform;
            transform?.BeginAnimation(ScaleTransform.ScaleXProperty, scaleXAnim);
            transform?.BeginAnimation(ScaleTransform.ScaleYProperty, scaleYAnim);

            return _infoTcs.Task;
        }

        private void RestartLauncher()
        {
            try
            {
                string exePath = Process.GetCurrentProcess().MainModule.FileName;
                var psi = new ProcessStartInfo
                {
                    FileName = exePath,
                    UseShellExecute = true,
                    WorkingDirectory = AppDomain.CurrentDomain.BaseDirectory
                };
                Process.Start(psi);
            }
            catch (Exception ex)
            {
                MessageBox.Show(
                    Lang.T("Theme.Restart.Fail", ex.Message),
                    Lang.T("Theme.Restart.Title"),
                    MessageBoxButton.OK,
                    MessageBoxImage.Warning);
            }

            Application.Current.Shutdown();
        }

        /// <summary>
        /// 页面切换进场动画：透明度 0→1 + 上移 8px→0，180ms ease-out。
        /// 只动画 transform/opacity（性能规则），且从 0.96 以上的"可见形态"起步，不出现 scale(0)。
        /// </summary>
        private void AnimatePageIn(FrameworkElement page)
        {
            if (page == null) return;
            if (SystemParameters.ClientAreaAnimation == false) { page.Opacity = 1; return; }

            page.BeginAnimation(OpacityProperty, null);
            page.Opacity = 0;
            var tt = new TranslateTransform(0, 8);
            page.RenderTransform = tt;
            var ease = new CubicEase { EasingMode = EasingMode.EaseOut };

            page.BeginAnimation(OpacityProperty,
                new DoubleAnimation(0, 1, TimeSpan.FromMilliseconds(200)) { EasingFunction = ease });
            tt.BeginAnimation(TranslateTransform.YProperty,
                new DoubleAnimation(8, 0, TimeSpan.FromMilliseconds(200)) { EasingFunction = ease });

            // ★ 卡片/区块依次淡入（20ms 间隔，最多 12 个）：只动画 opacity + transform
            var panel = page as Panel;
            if (panel == null) return;
            int stagger = 0;
            foreach (UIElement child in panel.Children)
            {
                var fe = child as FrameworkElement;
                if (fe == null || stagger >= 12) continue;
                if (fe.Height > 0 && fe.Height < 40 && fe.ActualHeight != 0 && fe.ActualHeight < 40) continue; // 跳过小控件
                fe.Opacity = 0;
                var childTt = new TranslateTransform(0, 6);
                fe.RenderTransform = childTt;
                var delay = TimeSpan.FromMilliseconds(30 + stagger * 20);
                fe.BeginAnimation(OpacityProperty, new DoubleAnimation(0, 1, TimeSpan.FromMilliseconds(160))
                { BeginTime = delay, EasingFunction = ease });
                childTt.BeginAnimation(TranslateTransform.YProperty, new DoubleAnimation(6, 0, TimeSpan.FromMilliseconds(160))
                { BeginTime = delay, EasingFunction = ease });
                stagger++;
            }
        }

        /// <summary>旧页面淡出后从 ContentGrid 移除，实现子页面交叉淡化。</summary>
        private void FadeOutAndRemove(UIElement element)
        {
            if (element == null || ContentGrid == null) return;
            if (!SystemParameters.ClientAreaAnimation || !(element is FrameworkElement fe))
            {
                ContentGrid.Children.Remove(element);
                return;
            }

            var fade = new DoubleAnimation(fe.Opacity, 0, TimeSpan.FromMilliseconds(140))
            { EasingFunction = new CubicEase { EasingMode = EasingMode.EaseIn } };
            fade.Completed += (s, e) =>
            {
                try { ContentGrid.Children.Remove(element); } catch { }
            };
            fe.BeginAnimation(OpacityProperty, fade);
        }

        /// <summary>子页面整体淡出（返回首页时）。</summary>
        private void AnimatePagesOut()
        {
            if (PagesLayer == null) return;
            if (!SystemParameters.ClientAreaAnimation)
            {
                PagesLayer.BeginAnimation(OpacityProperty, null);
                PagesLayer.Opacity = 1;
                PagesLayer.Visibility = Visibility.Collapsed;
                return;
            }

            var fade = new DoubleAnimation(PagesLayer.Opacity <= 0.01 ? 1 : PagesLayer.Opacity, 0, TimeSpan.FromMilliseconds(150))
            { EasingFunction = new CubicEase { EasingMode = EasingMode.EaseIn } };
            fade.Completed += (s, e) =>
            {
                if (_currentTabIndex == 0 && PagesLayer != null)
                {
                    PagesLayer.BeginAnimation(OpacityProperty, null);
                    PagesLayer.Opacity = 1;
                    PagesLayer.Visibility = Visibility.Collapsed;
                }
            };
            PagesLayer.BeginAnimation(OpacityProperty, fade);
        }

        /// <summary>子页面整体淡入（从首页进入子页面时）。</summary>
        private void AnimatePagesIn()
        {
            if (PagesLayer == null) return;
            PagesLayer.BeginAnimation(OpacityProperty, null);

            if (!SystemParameters.ClientAreaAnimation)
            {
                PagesLayer.Opacity = 1;
                return;
            }

            PagesLayer.Opacity = 0;
            var ease = new CubicEase { EasingMode = EasingMode.EaseOut };
            PagesLayer.BeginAnimation(OpacityProperty,
                new DoubleAnimation(0, 1, TimeSpan.FromMilliseconds(220)) { EasingFunction = ease });

            if (PageHost != null)
            {
                var tt = PageHost.RenderTransform as TranslateTransform;
                if (tt == null) { tt = new TranslateTransform(0, 10); PageHost.RenderTransform = tt; }
                tt.BeginAnimation(TranslateTransform.YProperty,
                    new DoubleAnimation(10, 0, TimeSpan.FromMilliseconds(240)) { EasingFunction = ease });
            }
        }

        /// <summary>首页淡入 + 轻微上移。</summary>
        private void AnimateHomeIn()
        {
            if (HomeLayer == null) return;
            HomeLayer.BeginAnimation(OpacityProperty, null);

            if (!SystemParameters.ClientAreaAnimation)
            {
                HomeLayer.Opacity = 1;
                return;
            }

            HomeLayer.Opacity = 0;
            var ease = new CubicEase { EasingMode = EasingMode.EaseOut };
            var tt = HomeLayer.RenderTransform as TranslateTransform;
            if (tt == null) { tt = new TranslateTransform(0, 8); HomeLayer.RenderTransform = tt; }
            tt.BeginAnimation(TranslateTransform.YProperty,
                new DoubleAnimation(8, 0, TimeSpan.FromMilliseconds(260)) { EasingFunction = ease });
            HomeLayer.BeginAnimation(OpacityProperty,
                new DoubleAnimation(0, 1, TimeSpan.FromMilliseconds(260)) { EasingFunction = ease });
        }

        /// <summary>首页淡出（进入子页面时）。</summary>
        private void AnimateHomeOut()
        {
            if (HomeLayer == null) return;
            if (!SystemParameters.ClientAreaAnimation)
            {
                HomeLayer.Visibility = Visibility.Collapsed;
                HomeLayer.Opacity = 1;
                return;
            }

            var fade = new DoubleAnimation(HomeLayer.Opacity <= 0.01 ? 1 : HomeLayer.Opacity, 0, TimeSpan.FromMilliseconds(140))
            { EasingFunction = new CubicEase { EasingMode = EasingMode.EaseIn } };
            fade.Completed += (s, e) =>
            {
                if (_currentTabIndex != 0 && HomeLayer != null)
                {
                    HomeLayer.Visibility = Visibility.Collapsed;
                    HomeLayer.Opacity = 1;
                }
            };
            HomeLayer.BeginAnimation(OpacityProperty, fade);
        }

        // ========== Tab 切换 ==========
        private void TabButton_Click(object sender, RoutedEventArgs e)
        {
            var btn = sender as Button;
            if (btn == null) return;
            int index = 0;
            if (btn == BtnTabLaunch) index = 0;
            else if (btn == BtnTabStats) index = 1;
            else if (btn == BtnTabSettings) index = 2;
            else if (btn == BtnTabAbout) index = 3;
            SelectTab(index);
        }

        private void SelectTab(int index)
        {
            try
            {
                _downloadCts?.Cancel(); _downloadCts?.Dispose(); _downloadCts = null;
                CloseDownloadDetailPopup();

                if (HomeLayer == null || PagesLayer == null || ContentGrid == null)
                {
                    return;
                }

                HideLibrary();
                CloseReleaseNotesPanel();

                int previous = _currentTabIndex;
                _currentTabIndex = index;
                bool home = index == 0;

                BtnTabLaunch.Tag = index == 0 ? "Selected" : "Unselected";
                BtnTabStats.Tag = index == 1 ? "Selected" : "Unselected";
                BtnTabSettings.Tag = index == 2 ? "Selected" : "Unselected";
                BtnTabAbout.Tag = index == 3 ? "Selected" : "Unselected";

                if (home)
                {
                    // 子页面 → 首页：页面淡出，首页淡入
                    if (PagesLayer.Visibility == Visibility.Visible)
                        AnimatePagesOut();

                    if (HomeLayer.Visibility != Visibility.Visible)
                        HomeLayer.Visibility = Visibility.Visible;
                    AnimateHomeIn();
                    UpdateHomePage();
                }
                else
                {
                    // 首页 → 子页面：首页淡出，页面淡入
                    if (previous == 0 && HomeLayer.Visibility == Visibility.Visible)
                        AnimateHomeOut();

                    PagesLayer.Visibility = Visibility.Visible;
                    if (previous <= 0)
                        AnimatePagesIn();
                    else if (!SystemParameters.ClientAreaAnimation)
                        PagesLayer.Opacity = 1;

                    UIElement newPage = null;
                    switch (index)
                    {
                        case 1: newPage = CreateStatsPage(); break;
                        case 2: newPage = CreateSettingsPage(); break;
                        case 3: newPage = CreateAboutPage(); break;
                    }

                    if (newPage != null)
                    {
                        // 子页面之间切换：旧页面淡出、新页面淡入
                        UIElement oldPage = ContentGrid.Children.Count > 0 ? ContentGrid.Children[0] : null;
                        var fe = newPage as FrameworkElement;
                        if (fe != null) fe.Opacity = 0;
                        ContentGrid.Children.Add(newPage);
                        AnimatePageIn(fe);
                        if (oldPage != null)
                            FadeOutAndRemove(oldPage);
                    }

                    UpdatePageChrome(index);
                }

                // 左侧导航指示条：竖向滑动（58 高 + 上下 3 边距 = 64 步进）
                if (TabSlider != null)
                {
                    double top = index * 64 + 20;
                    var ease = new CubicEase { EasingMode = EasingMode.EaseInOut };
                    TabSlider.BeginAnimation(FrameworkElement.MarginProperty,
                        new ThicknessAnimation(new Thickness(6, top, 0, 0), TimeSpan.FromMilliseconds(260))
                        { EasingFunction = ease });
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"切换标签页出错: {ex.Message}", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        // ========== ★ 鹰角式首页 / 版本库 ==========

        /// <summary>页面头与设置导航状态（数据 / 设置 / 关于）。</summary>
        private void UpdatePageChrome(int index)
        {
            try
            {
                string title;
                string kicker;
                switch (index)
                {
                    case 1: title = Lang.T("Tab.Stats"); kicker = "PLAYER DATA"; break;
                    case 2: title = Lang.T("Tab.Settings"); kicker = "SETTINGS"; break;
                    case 3: title = Lang.T("Tab.About"); kicker = "ABOUT"; break;
                    default: title = Lang.T("Tab.Launch"); kicker = "SNAKE LAUNCHER"; break;
                }

                if (TxtPageTitle != null) TxtPageTitle.Text = title;
                if (TxtPageKicker != null) TxtPageKicker.Text = kicker;

                // 设置 / 关于：显示鹰角式左侧导航（启动器设置 / 关于）
                bool settingsLike = index == 2 || index == 3;
                if (SettingsNav != null)
                    SettingsNav.Visibility = settingsLike ? Visibility.Visible : Visibility.Collapsed;
                if (BtnNavLauncher != null)
                    BtnNavLauncher.Tag = index == 2 ? "Selected" : "Unselected";
                if (BtnNavAbout != null)
                    BtnNavAbout.Tag = index == 3 ? "Selected" : "Unselected";
                if (TxtSettingsVersion != null)
                    TxtSettingsVersion.Text = "v" + UpdateService.GetCurrentVersion().ToString();
            }
            catch { }
        }

        private static string FormatGameVersion(GameFileInfo g)
        {
            if (g == null) return "--";
            var v = g.Version;
            if (v == null) return "--";
            if (v.Major == 9999) return "SnakeGame";
            try { return v.ToString(3); }
            catch { return v.ToString(); }
        }

        /// <summary>显示用版本标签：数字版本加 v 前缀；"SnakeGame" 这类名称保持原样。</summary>
        private static string VersionLabel(string ver)
        {
            if (string.IsNullOrWhiteSpace(ver)) return ver;
            if (ver.StartsWith("v", StringComparison.OrdinalIgnoreCase)) return ver;
            return ver == "SnakeGame" ? ver : "v" + ver;
        }

        /// <summary>当前选中的游戏版本；未手动选择时取最新 EXE（其次最新 Python）。</summary>
        private GameFileInfo GetActiveGame()
        {
            if (_gameFiles == null || _gameFiles.Count == 0) return null;

            if (_selectedGame != null)
            {
                var again = _gameFiles.FirstOrDefault(g =>
                    string.Equals(g.FullPath, _selectedGame.FullPath, StringComparison.OrdinalIgnoreCase));
                if (again != null) return again;
                _selectedGame = null;
            }

            return _gameFiles.Where(g => !g.IsPython).OrderByDescending(g => g.Version).FirstOrDefault()
                   ?? _gameFiles.OrderByDescending(g => g.Version).FirstOrDefault();
        }

        /// <summary>刷新首页主视觉（版本号、开始按钮、更新状态、版本资讯、公告）。</summary>
        private void UpdateHomePage()
        {
            if (TxtStartGame == null || TxtHomeVersion == null) return;

            var active = GetActiveGame();
            RefreshGameUpdateState(active);
            bool has = active != null;
            string ver = has ? FormatGameVersion(active) : "--";

            TxtHomeVersion.Text = has
                ? string.Format(Lang.T("Home.CurrentVersion"), VersionLabel(ver))
                : Lang.T("Home.NotInstalled");
            if (HomeStatusDot != null)
                HomeStatusDot.Fill = _gameUpdateAvailable
                    ? SafeFindBrush("AccentBrush")
                    : (has ? SafeFindBrush("PositiveBrush") : SafeFindBrush("ShellTextFaintBrush"));
            if (TxtHomeLatest != null)
                TxtHomeLatest.Text = has
                    ? (_gameUpdateAvailable ? Lang.T("Home.NewVersion") : Lang.T("Home.Latest"))
                    : Lang.T("Home.Downloadable");

            if (_isGameRunning)
            {
                TxtStartGame.Text = Lang.T("Home.GameRunning");
                if (TxtStartVersion != null) TxtStartVersion.Text = has ? VersionLabel(ver) : "SnakeGame";
                if (TxtHomeStatus != null) TxtHomeStatus.Text = Lang.T("Home.GameRunning");
            }
            else if (_gameUpdateAvailable)
            {
                TxtStartGame.Text = Lang.T("Home.UpdateGame");
                if (TxtStartVersion != null)
                    TxtStartVersion.Text = _latestGameRelease != null
                        ? VersionLabel(ver) + "  →  " + _latestGameRelease.TagName
                        : VersionLabel(ver);
                if (TxtHomeStatus != null)
                    TxtHomeStatus.Text = Lang.T("Home.UpdateAvailable", _latestGameRelease?.TagName ?? "");
            }
            else
            {
                TxtStartGame.Text = has ? Lang.T("Home.StartGame") : Lang.T("Home.DownloadGame");
                if (TxtStartVersion != null)
                    TxtStartVersion.Text = has ? VersionLabel(ver) : Lang.T("Home.DownloadForArch", GetArchDisplayName());
                if (TxtHomeStatus != null)
                    TxtHomeStatus.Text = has ? Lang.T("Home.Ready") : Lang.T("Home.DownloadReady");
            }

            if (TxtPromoTitle != null) TxtPromoTitle.Text = has ? Lang.T("Home.PromoTitle") : Lang.T("Home.DownloadGame");
            if (TxtPromoDesc != null) TxtPromoDesc.Text = has ? (ver + " · " + Lang.T("Home.Installed")) : Lang.T("Home.DownloadForArch", GetArchDisplayName());

            if (BtnStartGame != null)
            {
                BtnStartGame.IsEnabled = !_autoDownloadBusy && !_isGameRunning;
                if (!_isGameRunning)
                {
                    BtnStartGame.ToolTip = _gameUpdateAvailable
                        ? Lang.T("Home.UpdateHint", _latestGameRelease?.TagName ?? "")
                        : Lang.T("Home.StartGame");
                }
            }

            UpdateHomePromo();
            UpdateAnnouncements();
        }

        /// <summary>根据已安装游戏与 Release 列表，计算是否存在游戏更新。</summary>
        private void RefreshGameUpdateState(GameFileInfo active)
        {
            _latestGameRelease = null;
            _latestGameAsset = null;
            _latestGameVersion = null;
            _gameUpdateAvailable = false;

            if (active?.Version == null || active.Version.Major == 9999) return;
            if (_releaseFeed == null || _releaseFeed.Count == 0) return;

            try
            {
                string arch = GetPreferredArchitecture();
                var matching = _releaseFeed
                    .Where(r => r != null && r.RepoConfig != null && r.RepoConfig.IsPythonRepo == active.IsPython)
                    .OrderByDescending(r => r.ParsedVersion ?? new Version(0, 0, 0))
                    .ThenByDescending(r => r.PublishedAt)
                    .ToList();

                foreach (var rel in matching)
                {
                    var asset = GitHubReleaseService.PickBestAsset(rel.Assets, arch, "windows");
                    if (asset == null) continue;

                    var latest = asset.ParsedVersion ?? rel.ParsedVersion;
                    if (latest == null) continue;

                    if (latest > active.Version)
                    {
                        _latestGameRelease = rel;
                        _latestGameAsset = asset;
                        _latestGameVersion = latest;
                        _gameUpdateAvailable = true;
                    }
                    break;
                }
            }
            catch { }
        }

        /// <summary>
        /// 游戏运行状态：开始按钮变灰并显示"正在游戏"，游戏退出后恢复。
        /// </summary>
        private void SetGameRunning(bool running)
        {
            if (_isGameRunning == running) return;
            _isGameRunning = running;

            try
            {
                bool animate = SystemParameters.ClientAreaAnimation;

                if (StartPillGreyOverlay != null)
                {
                    StartPillGreyOverlay.BeginAnimation(OpacityProperty, null);

                    if (running)
                    {
                        StartPillGreyOverlay.Visibility = Visibility.Visible;
                        if (animate)
                        {
                            StartPillGreyOverlay.Opacity = 0;
                            StartPillGreyOverlay.BeginAnimation(OpacityProperty,
                                new DoubleAnimation(0, 1, TimeSpan.FromMilliseconds(200))
                                { EasingFunction = new CubicEase { EasingMode = EasingMode.EaseOut } });
                        }
                        else
                        {
                            StartPillGreyOverlay.Opacity = 1;
                        }
                    }
                    else
                    {
                        if (animate && StartPillGreyOverlay.Opacity > 0.01)
                        {
                            var fade = new DoubleAnimation(StartPillGreyOverlay.Opacity, 0, TimeSpan.FromMilliseconds(180))
                            { EasingFunction = new CubicEase { EasingMode = EasingMode.EaseIn } };
                            fade.Completed += (s, e) =>
                            {
                                if (!_isGameRunning && StartPillGreyOverlay != null)
                                    StartPillGreyOverlay.Visibility = Visibility.Collapsed;
                            };
                            StartPillGreyOverlay.BeginAnimation(OpacityProperty, fade);
                        }
                        else
                        {
                            StartPillGreyOverlay.Opacity = 0;
                            StartPillGreyOverlay.Visibility = Visibility.Collapsed;
                        }
                    }
                }

                if (BtnStartGame != null)
                {
                    BtnStartGame.IsEnabled = !running && !_autoDownloadBusy;
                    BtnStartGame.ToolTip = running ? Lang.T("Home.GameRunningHint") : Lang.T("Home.StartGame");
                }

                UpdateHomePage();
            }
            catch { }
        }

        // ==================== ★ 自定义启动器背景（图片 / 视频） ====================

        /// <summary>
        /// 自定义背景（图片/视频）下移除所有压暗/白色滤镜，让素材保持原色；
        /// 恢复默认主视觉时重新显示可读性遮罩。
        /// </summary>
        private void SetCustomBackgroundChrome(bool customActive)
        {
            if (LegibilityLayer != null)
                LegibilityLayer.Visibility = customActive ? Visibility.Collapsed : Visibility.Visible;
            if (CustomBackgroundScrim != null)
                CustomBackgroundScrim.Visibility = customActive ? Visibility.Collapsed : Visibility.Visible;
        }

        /// <summary>按配置应用自定义背景；类型为 none 或加载失败时回到默认主视觉。</summary>
        private void ApplyCustomBackground(bool notify = false)
        {
            if (CustomBackgroundLayer == null) return;

            StopBackgroundVideo();
            SetCustomBackgroundChrome(false);

            CustomBackgroundImage.Source = null;
            CustomBackgroundImage.Visibility = Visibility.Collapsed;
            CustomBackgroundVideoRect.Fill = null;
            CustomBackgroundVideoRect.Visibility = Visibility.Collapsed;
            CustomBackgroundLayer.Visibility = Visibility.Collapsed;
            if (ArtLayer != null) ArtLayer.Visibility = Visibility.Visible;

            string type = _config.BackgroundType ?? "none";
            string path = _config.BackgroundPath ?? "";

            if (string.Equals(type, "none", StringComparison.OrdinalIgnoreCase) ||
                string.IsNullOrWhiteSpace(path))
            {
                if (notify) ShowNotification(Lang.T("Background.Applied.Default"));
                return;
            }

            if (!File.Exists(path))
            {
                _config.BackgroundType = "none";
                _config.BackgroundPath = "";
                ConfigManager.Save(_config);
                if (notify) ShowNotification(Lang.T("Background.Missing"));
                return;
            }

            if (string.Equals(type, "image", StringComparison.OrdinalIgnoreCase))
            {
                try
                {
                    var bmp = new BitmapImage();
                    bmp.BeginInit();
                    bmp.CacheOption = BitmapCacheOption.OnLoad;
                    bmp.CreateOptions = BitmapCreateOptions.IgnoreImageCache;
                    bmp.UriSource = new Uri(path, UriKind.Absolute);
                    bmp.EndInit();
                    bmp.Freeze();

                    CustomBackgroundImage.Source = bmp;
                    CustomBackgroundImage.Visibility = Visibility.Visible;
                    CustomBackgroundLayer.Visibility = Visibility.Visible;
                    if (ArtLayer != null) ArtLayer.Visibility = Visibility.Collapsed;
                    SetCustomBackgroundChrome(true);
                    if (notify) ShowNotification(Lang.T("Background.Applied.Image"));
                }
                catch (Exception ex)
                {
                    _config.BackgroundType = "none";
                    _config.BackgroundPath = "";
                    ConfigManager.Save(_config);
                    if (notify) ShowNotification(Lang.T("Background.Failed", ex.Message));
                }
            }
            else if (string.Equals(type, "video", StringComparison.OrdinalIgnoreCase))
            {
                StartBackgroundVideo(path, notify);
            }
        }

        /// <summary>
        /// 用 MediaPlayer + VideoDrawing 播放背景视频：
        /// 这样在 AllowsTransparency 的圆角窗口里也能正常合成，并且可以静音循环。
        /// </summary>
        private void StartBackgroundVideo(string path, bool notify)
        {
            try
            {
                _bgVideoFallbackShown = false;
                _bgMediaPlayer = new MediaPlayer { IsMuted = true, Volume = 0 };
                _bgVideoDrawing = new VideoDrawing
                {
                    Player = _bgMediaPlayer,
                    Rect = new Rect(0, 0, 16, 9),
                };
                CustomBackgroundVideoRect.Fill = new DrawingBrush(_bgVideoDrawing)
                {
                    Stretch = Stretch.UniformToFill,
                    AlignmentX = AlignmentX.Center,
                    AlignmentY = AlignmentY.Center,
                };

                _bgMediaPlayer.MediaOpened += (s, e) =>
                {
                    try
                    {
                        double w = _bgMediaPlayer?.NaturalVideoWidth ?? 0;
                        double h = _bgMediaPlayer?.NaturalVideoHeight ?? 0;
                        if (_bgVideoDrawing != null && w > 0 && h > 0)
                            _bgVideoDrawing.Rect = new Rect(0, 0, w, h);
                    }
                    catch { }
                };

                _bgMediaPlayer.MediaEnded += (s, e) =>
                {
                    try
                    {
                        if (_bgMediaPlayer != null)
                        {
                            _bgMediaPlayer.Position = TimeSpan.Zero;
                            _bgMediaPlayer.Play();
                        }
                    }
                    catch { }
                };

                _bgMediaPlayer.MediaFailed += (s, e) =>
                {
                    if (_bgVideoFallbackShown) return;
                    _bgVideoFallbackShown = true;
                    StopBackgroundVideo();
                    CustomBackgroundLayer.Visibility = Visibility.Collapsed;
                    if (ArtLayer != null) ArtLayer.Visibility = Visibility.Visible;
                    SetCustomBackgroundChrome(false);
                    _config.BackgroundType = "none";
                    _config.BackgroundPath = "";
                    ConfigManager.Save(_config);
                    ShowNotification(Lang.T("Background.VideoFailed"));
                };

                _bgMediaPlayer.Open(new Uri(path));
                _bgMediaPlayer.Play();

                CustomBackgroundVideoRect.Visibility = Visibility.Visible;
                CustomBackgroundLayer.Visibility = Visibility.Visible;
                if (ArtLayer != null) ArtLayer.Visibility = Visibility.Collapsed;
                SetCustomBackgroundChrome(true);
                if (notify) ShowNotification(Lang.T("Background.Applied.Video"));
            }
            catch (Exception ex)
            {
                StopBackgroundVideo();
                CustomBackgroundLayer.Visibility = Visibility.Collapsed;
                if (ArtLayer != null) ArtLayer.Visibility = Visibility.Visible;
                SetCustomBackgroundChrome(false);
                if (notify) ShowNotification(Lang.T("Background.Failed", ex.Message));
            }
        }

        private void StopBackgroundVideo()
        {
            if (_bgMediaPlayer == null) return;
            try { _bgMediaPlayer.Stop(); } catch { }
            try { _bgMediaPlayer.Close(); } catch { }
            _bgMediaPlayer = null;
            _bgVideoDrawing = null;
            if (CustomBackgroundVideoRect != null)
            {
                CustomBackgroundVideoRect.Fill = null;
                CustomBackgroundVideoRect.Visibility = Visibility.Collapsed;
            }
        }

        private void PickBackgroundImage()
        {
            var ofd = new OpenFileDialog
            {
                Title = Lang.T("Settings.Background.Image"),
                Filter = "图片|*.png;*.jpg;*.jpeg;*.bmp;*.gif;*.tif;*.tiff|所有文件|*.*",
            };
            if (ofd.ShowDialog() == true) SetCustomBackground("image", ofd.FileName);
        }

        private void PickBackgroundVideo()
        {
            var ofd = new OpenFileDialog
            {
                Title = Lang.T("Settings.Background.Video"),
                Filter = "视频|*.mp4;*.wmv;*.avi;*.mov;*.m4v|所有文件|*.*",
            };
            if (ofd.ShowDialog() == true) SetCustomBackground("video", ofd.FileName);
        }

        private void ResetCustomBackground() => SetCustomBackground("none", "");

        private void SetCustomBackground(string type, string path)
        {
            _config.BackgroundType = type ?? "none";
            _config.BackgroundPath = path ?? "";
            ConfigManager.Save(_config);

            ApplyCustomBackground(notify: true);

            // 设置页正在显示时重建，以刷新"当前背景"描述
            if (GetCurrentTabIndex() == 2) SelectTab(2);
        }

        private string GetBackgroundDescription()
        {
            string type = _config.BackgroundType ?? "none";
            string path = _config.BackgroundPath ?? "";
            if (string.Equals(type, "image", StringComparison.OrdinalIgnoreCase) && !string.IsNullOrWhiteSpace(path))
                return string.Format(Lang.T("Background.ImagePath"), Path.GetFileName(path));
            if (string.Equals(type, "video", StringComparison.OrdinalIgnoreCase) && !string.IsNullOrWhiteSpace(path))
                return string.Format(Lang.T("Background.VideoPath"), Path.GetFileName(path));
            return Lang.T("Settings.Background.None");
        }

        // ==================== ★ 版本资讯 / 公告（GitHub Releases） ====================

        /// <summary>首页左下"版本资讯"卡：优先展示 GitHub 最新发行版。</summary>
        private void UpdateHomePromo()
        {
            if (TxtPromoTitle == null || TxtPromoDesc == null) return;
            var latest = _releaseFeed.FirstOrDefault();
            if (latest == null) return; // 保留 UpdateHomePage 写入的本机兜底文案

            TxtPromoTitle.Text = Lang.T("Home.PromoTitle");
            TxtPromoDesc.Text = string.Format(Lang.T("Home.Release.PromoDesc"),
                "v" + FormatReleaseVersion(latest),
                GetEditionLabel(latest),
                latest.PublishedAt.ToLocalTime().ToString("MM/dd"));
        }

        /// <summary>发行版版本号（去掉 tag 的 v 前缀）。</summary>
        private static string FormatReleaseVersion(GitHubRelease rel)
        {
            if (rel == null) return "--";
            string tag = rel.TagName?.Trim() ?? "";
            if (tag.StartsWith("v", StringComparison.OrdinalIgnoreCase)) tag = tag.Substring(1);
            if (!string.IsNullOrWhiteSpace(tag)) return tag;
            if (rel.ParsedVersion != null) return rel.ParsedVersion.ToString(3);
            return rel.Name ?? "--";
        }

        private string GetEditionLabel(GitHubRelease rel)
            => Lang.T(rel?.RepoConfig?.IsPythonRepo == true
                ? "Home.Release.EditionPython"
                : "Home.Release.EditionCSharp");

        private string GetEditionPill(GitHubRelease rel)
            => rel?.RepoConfig?.IsPythonRepo == true ? "PY" : "C#";

        /// <summary>
        /// 公告面板：
        /// 0 公告 = 两个仓库的全部发行版（最新在前，点击查看该版本更新说明）
        /// 1 新闻 = 预发布 / 测试版
        /// 2 资讯 = 本机已安装版本
        /// </summary>
        private void UpdateAnnouncements()
        {
            if (AnnouncementList == null) return;
            AnnouncementList.Children.Clear();
            UpdateNewsTabStyles();

            if (_newsTabIndex == 2)
            {
                AddInstalledAnnouncementRows();
                return;
            }

            if (_releaseFeed.Count == 0)
            {
                if (_releaseFeedLoading)
                {
                    AddAnnouncementPlaceholder(Lang.T("Home.Release.Loading"));
                    return;
                }
                if (_newsTabIndex == 0)
                    AddInstalledAnnouncementRows();
                else
                    AddAnnouncementPlaceholder(Lang.T("Home.Release.NoBeta"));
                return;
            }

            IEnumerable<GitHubRelease> source = _newsTabIndex == 1
                ? _releaseFeed.Where(r => r.Prerelease)
                : _releaseFeed;
            var items = source.Take(6).ToList();
            if (items.Count == 0)
            {
                AddAnnouncementPlaceholder(_newsTabIndex == 1
                    ? Lang.T("Home.Release.NoBeta")
                    : Lang.T("Home.Release.Empty"));
                return;
            }

            foreach (var rel in items) AddReleaseAnnouncementRow(rel);
        }

        private void AddAnnouncementPlaceholder(string text)
        {
            AnnouncementList.Children.Add(new TextBlock
            {
                Text = text,
                FontSize = 12,
                Foreground = SafeFindBrush("ShellTextDimBrush"),
                Margin = new Thickness(2, 12, 0, 0),
                TextWrapping = TextWrapping.Wrap,
            });
        }

        /// <summary>本机已安装版本（资讯页 / 无网络时的公告回退）。</summary>
        private void AddInstalledAnnouncementRows()
        {
            var ordered = _gameFiles.OrderByDescending(g => g.Version).Take(3).ToList();
            if (ordered.Count == 0)
            {
                AddAnnouncementPlaceholder(Lang.T("Home.NoAnnouncements"));
                return;
            }

            Brush titleBrush = SafeFindBrush("ShellTextBrush");
            Brush dateBrush = SafeFindBrush("ShellTextFaintBrush");
            Brush dotBrush = SafeFindBrush("AccentBrush");

            foreach (var g in ordered)
            {
                var row = new Button
                {
                    Style = SafeFindStyle("AnnouncementRow"),
                    HorizontalAlignment = HorizontalAlignment.Stretch,
                    Margin = new Thickness(0, 1, 0, 1),
                };

                var grid = new Grid();
                grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
                grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
                grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

                var dot = new Border
                {
                    Width = 5, Height = 5, CornerRadius = new CornerRadius(2.5),
                    Background = dotBrush, VerticalAlignment = VerticalAlignment.Center,
                    Margin = new Thickness(2, 0, 10, 0),
                };
                Grid.SetColumn(dot, 0);
                grid.Children.Add(dot);

                var title = new TextBlock
                {
                    Text = string.Format(Lang.T("Home.Announcement.Version"), VersionLabel(FormatGameVersion(g))),
                    FontSize = 12,
                    Foreground = titleBrush,
                    TextTrimming = TextTrimming.CharacterEllipsis,
                    VerticalAlignment = VerticalAlignment.Center,
                };
                Grid.SetColumn(title, 1);
                grid.Children.Add(title);

                string date = "";
                try { if (File.Exists(g.FullPath)) date = File.GetLastWriteTime(g.FullPath).ToString("MM/dd"); }
                catch { }
                var dateBlock = new TextBlock
                {
                    Text = date,
                    FontSize = 10.5,
                    Foreground = dateBrush,
                    VerticalAlignment = VerticalAlignment.Center,
                    Margin = new Thickness(10, 0, 2, 0),
                };
                Grid.SetColumn(dateBlock, 2);
                grid.Children.Add(dateBlock);

                row.Content = grid;
                var captured = g;
                row.Click += (s, e) => ShowVersionDetail(captured);
                AnnouncementList.Children.Add(row);
            }
        }

        /// <summary>GitHub 发行版公告行：版本 / 预发布 / 平台 / 日期。</summary>
        private void AddReleaseAnnouncementRow(GitHubRelease rel)
        {
            Brush titleBrush = SafeFindBrush("ShellTextBrush");
            Brush dateBrush = SafeFindBrush("ShellTextFaintBrush");
            Brush accentBrush = SafeFindBrush("AccentBrush");

            var row = new Button
            {
                Style = SafeFindStyle("AnnouncementRow"),
                HorizontalAlignment = HorizontalAlignment.Stretch,
                Margin = new Thickness(0, 1, 0, 1),
            };

            var grid = new Grid();
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

            var pill = new Border
            {
                Background = SafeFindBrush("AccentSoftBrush"),
                CornerRadius = new CornerRadius(4),
                Padding = new Thickness(5, 1, 5, 1),
                VerticalAlignment = VerticalAlignment.Center,
                Child = new TextBlock
                {
                    Text = GetEditionPill(rel),
                    FontSize = 9,
                    FontWeight = FontWeights.SemiBold,
                    Foreground = accentBrush,
                }
            };
            Grid.SetColumn(pill, 0);
            grid.Children.Add(pill);

            var titlePanel = new StackPanel
            {
                Orientation = Orientation.Horizontal,
                VerticalAlignment = VerticalAlignment.Center,
                Margin = new Thickness(9, 0, 0, 0),
            };
            titlePanel.Children.Add(new TextBlock
            {
                Text = "v" + FormatReleaseVersion(rel),
                FontSize = 12,
                Foreground = titleBrush,
                TextTrimming = TextTrimming.CharacterEllipsis,
            });
            if (rel.Prerelease)
            {
                titlePanel.Children.Add(new TextBlock
                {
                    Text = Lang.T("Home.Release.Prerelease"),
                    FontSize = 9,
                    Foreground = accentBrush,
                    VerticalAlignment = VerticalAlignment.Center,
                    Margin = new Thickness(6, 1, 0, 0),
                });
            }
            Grid.SetColumn(titlePanel, 1);
            grid.Children.Add(titlePanel);

            var dateBlock = new TextBlock
            {
                Text = rel.PublishedAt.ToLocalTime().ToString("MM/dd"),
                FontSize = 10.5,
                Foreground = dateBrush,
                VerticalAlignment = VerticalAlignment.Center,
                Margin = new Thickness(10, 0, 2, 0),
            };
            Grid.SetColumn(dateBlock, 2);
            grid.Children.Add(dateBlock);

            row.Content = grid;
            var captured = rel;
            row.Click += (s, e) => _ = ShowReleaseNotesPanelAsync(captured);
            AnnouncementList.Children.Add(row);
        }

        private void UpdateNewsTabStyles()
        {
            var tabs = new[] { TxtNewsTab1, TxtNewsTab2, TxtNewsTab3 };
            Brush selectedBrush = SafeFindBrush("AccentBrush");
            Brush dimBrush = SafeFindBrush("ShellTextDimBrush");
            for (int i = 0; i < tabs.Length; i++)
            {
                if (tabs[i] == null) continue;
                bool selected = i == _newsTabIndex;
                tabs[i].Foreground = selected ? selectedBrush : dimBrush;
                tabs[i].FontWeight = selected ? FontWeights.SemiBold : FontWeights.Normal;
            }
        }

        private void NewsTab_Click(object sender, MouseButtonEventArgs e)
        {
            if (sender is FrameworkElement fe && int.TryParse(fe.Tag?.ToString(), out int index))
            {
                _newsTabIndex = index;
                UpdateAnnouncements();
            }
        }

        private void MoreAnnouncements_Click(object sender, MouseButtonEventArgs e)
            => _ = ShowReleaseNotesPanelAsync(_releaseFeed.FirstOrDefault());

        /// <summary>拉取两个仓库的发行版（版本资讯 / 公告数据源），10 分钟内复用缓存。</summary>
        private async Task LoadReleaseFeedAsync(bool force = false)
        {
            if (_releaseFeedLoading) return;
            if (!force && _releaseFeed.Count > 0 &&
                (DateTime.Now - _releaseFeedLoadedAt).TotalMinutes < 10)
            {
                UpdateAnnouncements();
                return;
            }

            _releaseFeedLoading = true;
            UpdateAnnouncements();

            var all = new List<GitHubRelease>();
            foreach (var repo in GitHubReleaseService.Repos)
            {
                try
                {
                    var releases = await GitHubReleaseService.GetReleasesAsync(repo);
                    if (releases != null)
                        all.AddRange(releases.Where(r => r != null && !r.Draft));
                }
                catch (Exception ex)
                {
                    Debug.WriteLine($"获取 {repo.DisplayName} 版本资讯失败: {ex.Message}");
                }
            }

            if (all.Count > 0)
            {
                _releaseFeed = all
                    .OrderByDescending(r => r.PublishedAt)
                    .ThenByDescending(r => r.ParsedVersion ?? new Version(0, 0, 0, 0))
                    .ToList();
                _releaseFeedLoadedAt = DateTime.Now;
            }
            _releaseFeedLoading = false;

            UpdateHomePromo();
            UpdateAnnouncements();
            if (_releaseNotesOverlay != null) PopulateReleaseNotesList(_releaseNotesCurrent);

            // ★ Release 列表更新后重新判断游戏是否有新版本
            UpdateHomePage();
        }

        // ==================== ★ 版本资讯与更新说明面板 ====================

        /// <summary>打开"版本资讯与更新说明"面板（左侧版本列表 + 右侧 Markdown 更新说明）。</summary>
        private async Task ShowReleaseNotesPanelAsync(GitHubRelease release = null)
        {
            CloseReleaseNotesPanel();

            if (_releaseFeed.Count == 0)
                await LoadReleaseFeedAsync(force: true);

            if (_releaseFeed.Count == 0)
            {
                ShowNotification(Lang.T("Home.Release.LoadFailed"));
                return;
            }

            Brush glass = SafeFindBrush("ShellGlassStrongBrush");
            Brush hairline = SafeFindBrush("ShellHairlineBrush");
            Brush surface = SafeFindBrush("BackgroundBrush");

            _releaseNotesOverlay = new Border
            {
                Background = SafeFindBrush("ShellScrimStrongBrush"),
                Visibility = Visibility.Visible,
                Opacity = 0,
                HorizontalAlignment = HorizontalAlignment.Stretch,
                VerticalAlignment = VerticalAlignment.Stretch,
            };
            _releaseNotesOverlay.MouseLeftButtonDown += (s, e) =>
            {
                if (ReferenceEquals(e.OriginalSource, _releaseNotesOverlay)) CloseReleaseNotesPanel();
            };

            var panel = new Border
            {
                Width = Math.Min(920, Math.Max(680, _rootGrid.ActualWidth - 120)),
                Height = Math.Min(620, Math.Max(480, _rootGrid.ActualHeight - 120)),
                Background = glass,
                BorderBrush = hairline,
                BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(20),
                Padding = new Thickness(18),
                HorizontalAlignment = HorizontalAlignment.Center,
                VerticalAlignment = VerticalAlignment.Center,
                RenderTransformOrigin = new Point(0.5, 0.5),
            };
            panel.Effect = new DropShadowEffect
            {
                ShadowDepth = 14,
                BlurRadius = 46,
                Opacity = 0.5,
                Color = Colors.Black
            };
            var scale = new ScaleTransform(0.96, 0.96);
            panel.RenderTransform = scale;

            var layout = new Grid();
            layout.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            layout.RowDefinitions.Add(new RowDefinition { Height = new GridLength(1, GridUnitType.Star) });

            // 标题栏
            var header = new Grid { Margin = new Thickness(2, 0, 2, 14) };
            header.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            header.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

            var headerLeft = new StackPanel { Orientation = Orientation.Horizontal, VerticalAlignment = VerticalAlignment.Center };
            headerLeft.Children.Add(new Border
            {
                Width = 6, Height = 6, CornerRadius = new CornerRadius(2),
                Background = SafeFindBrush("AccentBrush"),
                VerticalAlignment = VerticalAlignment.Center,
                Margin = new Thickness(0, 0, 10, 0),
            });
            headerLeft.Children.Add(new TextBlock
            {
                Text = Lang.T("Home.Release.PanelTitle"),
                FontSize = 16,
                FontWeight = FontWeights.SemiBold,
                Foreground = SafeFindBrush("ShellTextBrush"),
                VerticalAlignment = VerticalAlignment.Center,
            });
            Grid.SetColumn(headerLeft, 0);
            header.Children.Add(headerLeft);

            var closeBtn = new Button
            {
                Style = SafeFindStyle("WindowIconButton"),
                Content = new TextBlock { Text = "✕", FontFamily = new FontFamily("Segoe UI"), FontSize = 13 },
                HorizontalAlignment = HorizontalAlignment.Right,
                VerticalAlignment = VerticalAlignment.Center,
            };
            closeBtn.Click += (s, e) => CloseReleaseNotesPanel();
            Grid.SetColumn(closeBtn, 1);
            header.Children.Add(closeBtn);

            Grid.SetRow(header, 0);
            layout.Children.Add(header);

            // 主体：左侧列表 + 右侧更新说明
            var body = new Grid();
            body.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(280) });
            body.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(14) });
            body.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });

            var leftBorder = new Border
            {
                Background = surface,
                BorderBrush = hairline,
                BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(12),
                Padding = new Thickness(8),
            };
            _releaseNotesList = new StackPanel();
            leftBorder.Child = new ScrollViewer
            {
                Content = _releaseNotesList,
                VerticalScrollBarVisibility = ScrollBarVisibility.Auto,
                HorizontalScrollBarVisibility = ScrollBarVisibility.Disabled,
            };
            Grid.SetColumn(leftBorder, 0);
            body.Children.Add(leftBorder);

            var rightGrid = new Grid();
            rightGrid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            rightGrid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            rightGrid.RowDefinitions.Add(new RowDefinition { Height = new GridLength(1, GridUnitType.Star) });

            _releaseNotesTitle = new TextBlock
            {
                FontSize = 20,
                FontWeight = FontWeights.SemiBold,
                Foreground = SafeFindBrush("ShellTextBrush"),
                Margin = new Thickness(2, 0, 0, 4),
                TextTrimming = TextTrimming.CharacterEllipsis,
            };
            Grid.SetRow(_releaseNotesTitle, 0);
            rightGrid.Children.Add(_releaseNotesTitle);

            var metaRow = new Grid { Margin = new Thickness(2, 0, 0, 10) };
            metaRow.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            metaRow.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

            _releaseNotesMeta = new TextBlock
            {
                FontSize = 11,
                Foreground = SafeFindBrush("ShellTextDimBrush"),
                VerticalAlignment = VerticalAlignment.Center,
                TextTrimming = TextTrimming.CharacterEllipsis,
            };
            Grid.SetColumn(_releaseNotesMeta, 0);
            metaRow.Children.Add(_releaseNotesMeta);

            _releaseNotesGithubButton = new Button
            {
                Style = SafeFindStyle("PromoLinkButton"),
                HorizontalAlignment = HorizontalAlignment.Right,
                VerticalAlignment = VerticalAlignment.Center,
            };
            _releaseNotesGithubButton.Click += (s, e) =>
            {
                try
                {
                    if (!string.IsNullOrWhiteSpace(_releaseNotesCurrent?.HtmlUrl))
                        Process.Start(_releaseNotesCurrent.HtmlUrl);
                }
                catch { }
            };
            Grid.SetColumn(_releaseNotesGithubButton, 1);
            metaRow.Children.Add(_releaseNotesGithubButton);

            Grid.SetRow(metaRow, 1);
            rightGrid.Children.Add(metaRow);

            var viewerBorder = new Border
            {
                Background = surface,
                BorderBrush = hairline,
                BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(12),
                Padding = new Thickness(4),
            };
            _releaseNotesViewer = new FlowDocumentScrollViewer
            {
                VerticalScrollBarVisibility = ScrollBarVisibility.Auto,
                HorizontalScrollBarVisibility = ScrollBarVisibility.Disabled,
                IsToolBarVisible = false,
                Padding = new Thickness(0),
            };
            viewerBorder.Child = _releaseNotesViewer;
            Grid.SetRow(viewerBorder, 2);
            rightGrid.Children.Add(viewerBorder);

            Grid.SetColumn(rightGrid, 2);
            body.Children.Add(rightGrid);

            Grid.SetRow(body, 1);
            layout.Children.Add(body);

            panel.Child = layout;
            _releaseNotesOverlay.Child = panel;
            _rootGrid.Children.Add(_releaseNotesOverlay);
            Grid.SetRowSpan(_releaseNotesOverlay, int.MaxValue);
            Grid.SetColumnSpan(_releaseNotesOverlay, int.MaxValue);

            var target = release ?? _releaseFeed.FirstOrDefault();
            PopulateReleaseNotesList(target);
            UpdateReleaseNotesContent(target);

            if (SystemParameters.ClientAreaAnimation)
            {
                _releaseNotesOverlay.BeginAnimation(OpacityProperty,
                    new DoubleAnimation(0, 1, TimeSpan.FromMilliseconds(150)));
                scale.BeginAnimation(ScaleTransform.ScaleXProperty,
                    new DoubleAnimation(0.96, 1, TimeSpan.FromMilliseconds(190))
                    { EasingFunction = new CubicEase { EasingMode = EasingMode.EaseOut } });
                scale.BeginAnimation(ScaleTransform.ScaleYProperty,
                    new DoubleAnimation(0.96, 1, TimeSpan.FromMilliseconds(190))
                    { EasingFunction = new CubicEase { EasingMode = EasingMode.EaseOut } });
            }
            else
            {
                _releaseNotesOverlay.Opacity = 1;
            }
        }

        /// <summary>左侧版本列表（两个仓库合并，最多 80 条）。</summary>
        private void PopulateReleaseNotesList(GitHubRelease selected)
        {
            if (_releaseNotesList == null) return;
            _releaseNotesList.Children.Clear();

            var rows = _releaseFeed.Take(80).ToList();
            foreach (var rel in rows)
            {
                var row = new Button
                {
                    Style = SafeFindStyle("SettingsNavItem"),
                    Height = 44,
                    Margin = new Thickness(0, 2, 0, 2),
                    HorizontalContentAlignment = HorizontalAlignment.Left,
                    Tag = selected != null && rel == selected ? "Selected" : "Unselected",
                };

                var stack = new StackPanel { VerticalAlignment = VerticalAlignment.Center };
                stack.Children.Add(new TextBlock
                {
                    Text = "v" + FormatReleaseVersion(rel) +
                           (rel.Prerelease ? "  " + Lang.T("Home.Release.Prerelease") : ""),
                    FontSize = 12,
                    Foreground = SafeFindBrush("ShellTextBrush"),
                    TextTrimming = TextTrimming.CharacterEllipsis,
                });
                stack.Children.Add(new TextBlock
                {
                    Text = $"{GetEditionPill(rel)}  ·  {rel.PublishedAt.ToLocalTime():MM/dd}",
                    FontSize = 9.5,
                    Foreground = SafeFindBrush("ShellTextFaintBrush"),
                    Margin = new Thickness(0, 2, 0, 0),
                });
                row.Content = stack;

                var captured = rel;
                row.Click += (s, e) => SelectReleaseNote(captured);
                _releaseNotesList.Children.Add(row);
            }
        }

        private void SelectReleaseNote(GitHubRelease rel)
        {
            if (rel == null) return;
            _releaseNotesCurrent = rel;
            UpdateReleaseNotesContent(rel);
            PopulateReleaseNotesList(rel);
        }

        /// <summary>右侧：渲染该版本的更新说明（Markdown）。</summary>
        private void UpdateReleaseNotesContent(GitHubRelease rel)
        {
            if (rel == null || _releaseNotesViewer == null) return;

            _releaseNotesCurrent = rel;
            if (_releaseNotesTitle != null)
                _releaseNotesTitle.Text = "v" + FormatReleaseVersion(rel);

            string meta = GetEditionLabel(rel) + "  ·  " +
                          Lang.T("Home.Release.Published",
                              rel.PublishedAt.ToLocalTime().ToString("yyyy-MM-dd HH:mm"));
            if (rel.Prerelease) meta = Lang.T("Home.Release.Prerelease") + "  ·  " + meta;
            if (_releaseNotesMeta != null) _releaseNotesMeta.Text = meta;

            if (_releaseNotesGithubButton != null)
            {
                _releaseNotesGithubButton.Content = Lang.T("Home.Release.OpenGitHub");
                _releaseNotesGithubButton.Visibility = string.IsNullOrWhiteSpace(rel.HtmlUrl)
                    ? Visibility.Collapsed
                    : Visibility.Visible;
            }

            string body = rel.Body;
            if (string.IsNullOrWhiteSpace(body))
                body = "*" + Lang.T("Home.Release.NoNotes") + "*";

            try
            {
                _releaseNotesViewer.Document = MarkdownRenderer.Render(
                    body,
                    SafeFindBrush("ForegroundBrush"),
                    SafeFindBrush("AccentBrush"),
                    12.5);
            }
            catch
            {
                _releaseNotesViewer.Document = new FlowDocument(new Paragraph(new Run(body)));
            }
        }

        private void CloseReleaseNotesPanel()
        {
            if (_releaseNotesOverlay == null) return;
            try { _rootGrid.Children.Remove(_releaseNotesOverlay); } catch { }
            _releaseNotesOverlay = null;
            _releaseNotesList = null;
            _releaseNotesViewer = null;
            _releaseNotesTitle = null;
            _releaseNotesMeta = null;
            _releaseNotesGithubButton = null;
            _releaseNotesCurrent = null;
        }

        /// <summary>版本详情弹窗（复用现有详情面板）。</summary>
        private void ShowVersionDetail(GameFileInfo g)
        {
            if (g == null)
            {
                ShowLibrary();
                return;
            }

            var sb = new StringBuilder();
            sb.AppendLine(Lang.T("Home.VersionLabel") + ":  " + VersionLabel(FormatGameVersion(g)));
            sb.AppendLine(Lang.T("Home.TypeLabel") + ":  " + Lang.T(g.IsPython ? "Home.TypePython" : "Home.TypeExe"));
            sb.AppendLine(Lang.T("Home.PathLabel") + ":  " + g.FullPath);
            try
            {
                if (File.Exists(g.FullPath))
                {
                    var fi = new FileInfo(g.FullPath);
                    sb.AppendLine(Lang.T("Home.SizeLabel") + ":  " + (fi.Length / 1024.0).ToString("N1") + " KB");
                    sb.AppendLine(Lang.T("Home.ModifiedLabel") + ":  " + fi.LastWriteTime.ToString("yyyy-MM-dd HH:mm"));
                }
            }
            catch { }
            sb.AppendLine();
            sb.AppendLine(Lang.T("Home.DetailHint"));

            ShowDetailPanel(Lang.T("Home.VersionDetail") + "  ·  " + VersionLabel(FormatGameVersion(g)), sb.ToString());
        }

        /// <summary>打开右侧版本库抽屉。</summary>
        private void ShowLibrary()
        {
            if (LibraryOverlay == null) return;

            if (LibraryList != null) _cardPanel = LibraryList;
            ApplySort();
            RefreshCards();

            LibraryOverlay.Visibility = Visibility.Visible;

            if (SystemParameters.ClientAreaAnimation)
            {
                LibraryOverlay.BeginAnimation(OpacityProperty,
                    new DoubleAnimation(0, 1, TimeSpan.FromMilliseconds(140)));
                if (_librarySlide != null)
                    _librarySlide.BeginAnimation(TranslateTransform.XProperty,
                        new DoubleAnimation(40, 0, TimeSpan.FromMilliseconds(180))
                        { EasingFunction = new CubicEase { EasingMode = EasingMode.EaseOut } });
            }
            else
            {
                LibraryOverlay.Opacity = 1;
            }
        }

        /// <summary>关闭版本库抽屉。</summary>
        private void HideLibrary()
        {
            if (LibraryOverlay == null) return;
            if (LibraryOverlay.Visibility != Visibility.Visible) return;

            LibraryOverlay.BeginAnimation(OpacityProperty, null);
            LibraryOverlay.Opacity = 1;
            LibraryOverlay.Visibility = Visibility.Collapsed;
        }

        private static T FindAncestor<T>(DependencyObject d) where T : DependencyObject
        {
            try
            {
                while (d != null)
                {
                    if (d is T t) return t;
                    d = (d is Visual || d is System.Windows.Media.Media3D.Visual3D)
                        ? VisualTreeHelper.GetParent(d)
                        : LogicalTreeHelper.GetParent(d);
                }
            }
            catch { }
            return null;
        }

        // ---- 首页 / 外壳交互 ----

        private async void BtnStartGame_Click(object sender, RoutedEventArgs e)
        {
            if (_isGameRunning || _autoDownloadBusy) return;

            var active = GetActiveGame();
            RefreshGameUpdateState(active);
            if (active == null || _gameUpdateAvailable)
            {
                // 未安装游戏：下载；已安装但检测到新版本：更新
                await DownloadAndInstallLatestGameAsync(active?.IsPython);
                return;
            }
            _selectedGame = active;
            await LaunchGame(active.FullPath, active.IsPython);
        }

        private void BtnStartMenu_Click(object sender, RoutedEventArgs e) => ShowGameMenu();

        // ==================== 三条杠：游戏操作菜单 ====================
        private void ShowGameMenu()
        {
            var active = GetActiveGame();
            if (active == null)
            {
                ShowNotification(Lang.T("Menu.NoGame"));
                return;
            }

            if (GameMenuPopup != null)
            {
                GameMenuPopup.PlacementTarget = BtnStartMenu;
                GameMenuPopup.IsOpen = true;
            }
        }

        private void CloseGameMenu()
        {
            if (GameMenuPopup != null) GameMenuPopup.IsOpen = false;
        }

        private void GameMenuSettings_Click(object sender, RoutedEventArgs e)
        {
            CloseGameMenu();
            var game = GetActiveGame();
            if (game == null) return;

            ShowDetailPanel(Lang.T("Menu.GameSettings"),
                $"版本: {VersionLabel(FormatGameVersion(game))}\n" +
                $"路径: {game.FullPath}\n" +
                $"类型: {(game.IsPython ? "Python" : "C# / Unity")}\n\n" +
                "如需修改游戏内画面、音量等设置，请启动游戏后在游戏设置中调整。");
        }

        private void GameMenuShortcut_Click(object sender, RoutedEventArgs e)
        {
            CloseGameMenu();
            var game = GetActiveGame();
            if (game == null) return;

            try
            {
                string desktop = Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory);
                string shortcutPath = Path.Combine(desktop,
                    $"SnakeGame - {FormatGameVersion(game)}.lnk");

                Type shellType = Type.GetTypeFromProgID("WScript.Shell");
                if (shellType == null) throw new InvalidOperationException("WScript.Shell 不可用");

                dynamic shell = Activator.CreateInstance(shellType);
                dynamic shortcut = shell.CreateShortcut(shortcutPath);
                shortcut.TargetPath = game.FullPath;
                shortcut.WorkingDirectory = Path.GetDirectoryName(game.FullPath);
                shortcut.Description = "SnakeGame";
                shortcut.Save();

                ShowNotification(Lang.T("Menu.ShortcutDone"));
            }
            catch (Exception ex)
            {
                ShowNotification(Lang.T("Menu.ShortcutFailed", ex.Message));
            }
        }

        private void GameMenuVerify_Click(object sender, RoutedEventArgs e)
        {
            CloseGameMenu();
            var game = GetActiveGame();
            if (game == null) return;

            try
            {
                if (!File.Exists(game.FullPath))
                {
                    ShowDetailPanel(Lang.T("Menu.VerifyGame"), Lang.T("Menu.VerifyFailed", "文件不存在"));
                    return;
                }

                var fi = new FileInfo(game.FullPath);
                string hash;
                using (var sha = System.Security.Cryptography.SHA256.Create())
                using (var fs = File.OpenRead(game.FullPath))
                    hash = BitConverter.ToString(sha.ComputeHash(fs)).Replace("-", "");

                string tamper = AntiCheat.VerifyGameExe(game.FullPath);
                string text = $"文件: {fi.Name}\n" +
                              $"大小: {(fi.Length / 1024.0):N1} KB\n" +
                              $"修改时间: {fi.LastWriteTime:yyyy-MM-dd HH:mm}\n" +
                              $"SHA256: {hash}\n\n" +
                              (tamper == null ? Lang.T("Menu.VerifyOk") : Lang.T("Menu.VerifyFailed", tamper));

                ShowDetailPanel(Lang.T("Menu.VerifyGame"), text);
            }
            catch (Exception ex)
            {
                ShowDetailPanel(Lang.T("Menu.VerifyGame"), Lang.T("Menu.VerifyFailed", ex.Message));
            }
        }

        private void GameMenuClearCache_Click(object sender, RoutedEventArgs e)
        {
            CloseGameMenu();

            try
            {
                UpdateService.CleanupTempFiles();
                UpdateService.CleanupUpdaterTempDirs();

                string temp = Path.GetTempPath();
                foreach (var pattern in new[] { "SnakeLauncherUpdate_*", "SnakeLauncherUpdater_*" })
                {
                    foreach (var dir in Directory.GetDirectories(temp, pattern))
                    {
                        try { Directory.Delete(dir, true); } catch { }
                    }
                }

                ShowNotification(Lang.T("Menu.CacheCleared"));
            }
            catch (Exception ex)
            {
                ShowNotification(Lang.T("Menu.CacheClearFailed", ex.Message));
            }
        }

        private void BtnPromoDetail_Click(object sender, RoutedEventArgs e)
        {
            var latest = _releaseFeed.FirstOrDefault();
            if (latest != null)
            {
                _ = ShowReleaseNotesPanelAsync(latest);
                return;
            }
            ShowVersionDetail(GetActiveGame());
        }

        private void PromoCard_MouseLeftButtonUp(object sender, MouseButtonEventArgs e)
        {
            if (e.OriginalSource is DependencyObject src && FindAncestor<Button>(src) != null) return;
            var latest = _releaseFeed.FirstOrDefault();
            if (latest != null)
            {
                _ = ShowReleaseNotesPanelAsync(latest);
                return;
            }
            ShowVersionDetail(GetActiveGame());
        }

        private void BtnAllGames_Click(object sender, RoutedEventArgs e) => ShowLibrary();
        private void BtnUtilLibrary_Click(object sender, RoutedEventArgs e) => ShowLibrary();

        private void BtnUtilRefresh_Click(object sender, RoutedEventArgs e)
        {
            ShowNotification(Lang.T("Home.Refreshing"));
            _ = ScanGamesAsync();
            _ = LoadReleaseFeedAsync(force: true);
        }

        private void BtnUtilAdd_Click(object sender, RoutedEventArgs e) => ManualAdd();

        private void BtnUtilFolder_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                if (_config.Directories != null && _config.CurrentDirIndex < _config.Directories.Count)
                {
                    string dir = _config.Directories[_config.CurrentDirIndex];
                    if (Directory.Exists(dir)) Process.Start("explorer.exe", dir);
                    else ShowNotification(Lang.T("Home.FolderMissing"));
                }
            }
            catch (Exception ex) { ShowNotification(ex.Message); }
        }

        private void BtnUtilUpdate_Click(object sender, RoutedEventArgs e) => StartAutoUpdateCheck();
        private void BtnUtilAbout_Click(object sender, RoutedEventArgs e) => SelectTab(3);
        private void BtnSettings_Click(object sender, RoutedEventArgs e) => SelectTab(2);
        private void BtnMessages_Click(object sender, RoutedEventArgs e) => ShowNotification(Lang.T("Home.NoMessages"));

        private async void BtnAccount_Click(object sender, RoutedEventArgs e)
        {
            await ShowInfoDialogAsync(Lang.T("Home.Account.Local"));
        }

        private void BtnClosePage_Click(object sender, RoutedEventArgs e) => SelectTab(0);
        private void SettingsNavLauncher_Click(object sender, RoutedEventArgs e) => SelectTab(2);
        private void SettingsNavAbout_Click(object sender, RoutedEventArgs e) => SelectTab(3);
        private void BtnCloseLibrary_Click(object sender, RoutedEventArgs e) => HideLibrary();

        private void LibraryOverlay_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            if (ReferenceEquals(e.OriginalSource, LibraryOverlay)) HideLibrary();
        }

        // ========== 启动页面 ==========
        private void ApplySort()
        {
            string sort = _sortButton?.Content?.ToString() ?? Lang.T("Launch.Sort.Default");

            if (sort == Lang.T("Launch.Sort.Recent"))
            {
                _gameFiles = _gameFiles.OrderByDescending(g => GameStatsManager.GetRecord(g.FullPath)?.LastPlayed ?? DateTime.MinValue).ToList();
            }
            else if (sort == Lang.T("Launch.Sort.MostPlayed"))
            {
                _gameFiles = _gameFiles.OrderByDescending(g => GameStatsManager.GetRecord(g.FullPath)?.LaunchCount ?? 0).ToList();
            }
            else
            {
                _gameFiles = _gameFiles.OrderByDescending(g => g.Version).ToList();
            }
        }

        private void RefreshCards()
        {
            if (_cardPanel == null) return;
            _cardPanel.Children.Clear();
            if (_gameFiles.Count == 0)
            {
                _cardPanel.Children.Add(new TextBlock
                {
                    Text = Lang.T("Launch.NoGames"),
                    Foreground = SafeFindBrush("SecondaryForegroundBrush"),
                    TextAlignment = TextAlignment.Center,
                    Margin = new Thickness(20)
                });
                return;
            }
            foreach (var g in _gameFiles)
            {
                string ver = g.Version.Major == 9999 ? "SnakeGame" : $"{g.Version}";
                var card = CreateGameCard(ver, g.DisplayName, g.FullPath, g.IsPython);
                _cardPanel.Children.Add(card);
            }
        }

        private Border CreateGameCard(string versionStr, string displayName, string fullPath, bool isPython)
        {
            var activeForCard = GetActiveGame();
            bool isSelected = activeForCard != null &&
                              string.Equals(activeForCard.FullPath, fullPath, StringComparison.OrdinalIgnoreCase);

            var card = new Border
            {
                Style = SafeFindStyle("GameCardStyle"),
                Height = 88,
                Margin = new Thickness(0, 0, 0, 10),
                Padding = new Thickness(16, 12, 14, 12),
                Cursor = Cursors.Hand,
                HorizontalAlignment = HorizontalAlignment.Stretch,
            };
            if (isSelected) card.BorderBrush = SafeFindBrush("AccentBrush");

            var grid = new Grid();
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

            var versionBlock = new TextBlock
            {
                Text = versionStr,
                FontSize = 21,
                FontWeight = FontWeights.Bold,
                Foreground = SafeFindBrush("ForegroundBrush"),
                VerticalAlignment = VerticalAlignment.Center,
                MinWidth = 108,
                Margin = new Thickness(2, 0, 14, 0),
            };
            Grid.SetColumn(versionBlock, 0);
            grid.Children.Add(versionBlock);

            var info = new StackPanel { VerticalAlignment = VerticalAlignment.Center, Margin = new Thickness(0, 0, 12, 0) };
            info.Children.Add(new TextBlock
            {
                Text = displayName,
                FontSize = 12.5,
                Foreground = SafeFindBrush("SecondaryForegroundBrush"),
                TextTrimming = TextTrimming.CharacterEllipsis,
            });
            info.Children.Add(new TextBlock
            {
                Text = fullPath,
                FontSize = 10.5,
                Foreground = SafeFindBrush("TextTertiaryBrush"),
                TextTrimming = TextTrimming.CharacterEllipsis,
                Margin = new Thickness(0, 4, 0, 0),
            });
            if (isSelected)
            {
                info.Children.Add(new TextBlock
                {
                    Text = Lang.T("Home.CurrentVersionShort"),
                    FontSize = 10,
                    FontWeight = FontWeights.SemiBold,
                    Foreground = SafeFindBrush("AccentBrush"),
                    Margin = new Thickness(0, 4, 0, 0),
                });
            }
            Grid.SetColumn(info, 1);
            grid.Children.Add(info);

            var btnPanel = new StackPanel
            {
                Orientation = Orientation.Horizontal,
                VerticalAlignment = VerticalAlignment.Center,
            };
            var launchBtn = new Button { Content = Lang.T("Launch.Card.Start"), Style = SafeFindStyle("RoundedButton"), Width = 78, Height = 32 };
            launchBtn.Click += async (s, ev) => await LaunchGame(fullPath, isPython);
            var detailBtn = new Button
            {
                Content = Lang.T("Launch.Card.Detail"),
                Style = SafeFindStyle("RoundedButton"),
                Width = 62, Height = 32,
                Margin = new Thickness(6, 0, 0, 0),
            };
            detailBtn.Click += (s, ev) => ShowDetailWindow(fullPath);
            btnPanel.Children.Add(launchBtn);
            btnPanel.Children.Add(detailBtn);
            Grid.SetColumn(btnPanel, 2);
            grid.Children.Add(btnPanel);

            var contextMenu = new ContextMenu();
            var renameItem = new MenuItem { Header = Lang.T("Launch.Menu.Rename") };
            renameItem.Click += (s, ev) =>
            {
                string newName = Interaction.InputBox(Lang.T("Launch.Rename.Prompt"), Lang.T("Launch.Rename.Title"), displayName);
                if (!string.IsNullOrWhiteSpace(newName))
                {
                    var game = _gameFiles.FirstOrDefault(g => g.FullPath == fullPath);
                    if (game != null) { game.DisplayName = newName; RefreshCards(); UpdateHomePage(); }
                }
            };
            var openFolderItem = new MenuItem { Header = Lang.T("Launch.Menu.OpenFolder") };
            openFolderItem.Click += (s, ev) => Process.Start("explorer.exe", $"/select,\"{fullPath}\"");
            contextMenu.Items.Add(renameItem);
            contextMenu.Items.Add(openFolderItem);
            card.ContextMenu = contextMenu;

            // 点击卡片 = 选中该版本（启动按钮随之切换）
            card.MouseLeftButtonUp += (s, ev) =>
            {
                if (ev.OriginalSource is DependencyObject src && FindAncestor<Button>(src) != null) return;
                var game = _gameFiles.FirstOrDefault(g => string.Equals(g.FullPath, fullPath, StringComparison.OrdinalIgnoreCase));
                if (game == null) return;
                _selectedGame = game;
                UpdateHomePage();
                HideLibrary();
                ShowNotification(string.Format(Lang.T("Home.Selected"), versionStr));
            };

            card.Child = grid;
            return card;
        }

        private void ShowDetailWindow(string path)
        {
            var game = _gameFiles.FirstOrDefault(g => g.FullPath == path);
            var stats = GameStatsManager.GetRecord(path);

            _currentDetailGamePath = path;

            string info = Lang.T("Detail.Info",
                game?.Version,
                game?.DisplayName,
                path,
                stats?.LastPlayed.ToString("g") ?? Lang.T("Detail.Never"),
                stats?.LaunchCount ?? 0,
                stats?.TotalPlayMinutes ?? 0);

            string parentDir = Path.GetDirectoryName(path);
            bool hasValidParent = !string.IsNullOrEmpty(parentDir)
                && !string.Equals(parentDir, Path.GetPathRoot(path), StringComparison.OrdinalIgnoreCase);

            if (hasValidParent)
            {
                info += Lang.T("Detail.DeleteWarning", parentDir);
            }

            ShowDetailPanel(Lang.T("Detail.Title"), info);
        }

        private void BtnOpenFolder_Click(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrEmpty(_currentDetailGamePath)) return;
            try
            {
                Process.Start("explorer.exe", $"/select,\"{_currentDetailGamePath}\"");
            }
            catch (Exception ex)
            {
                ShowNotification(Lang.T("Detail.OpenFailed", ex.Message));
            }
        }

        private async void BtnDeleteGame_Click(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrEmpty(_currentDetailGamePath))
            {
                ShowNotification(Lang.T("Detail.NotSelected"));
                return;
            }

            string gamePath = _currentDetailGamePath;
            if (!File.Exists(gamePath) && !Directory.Exists(gamePath))
            {
                ShowNotification(Lang.T("Detail.FileGone"));
                HideDetailPanel();
                await ScanGamesAsync();
                return;
            }

            string parentDir = Path.GetDirectoryName(gamePath);
            string root = Path.GetPathRoot(gamePath);

            if (string.IsNullOrEmpty(parentDir)
                || string.Equals(parentDir, root, StringComparison.OrdinalIgnoreCase))
            {
                ShowNotification(Lang.T("Detail.RootRefused"));
                return;
            }

            string launcherDir = AppDomain.CurrentDomain.BaseDirectory.TrimEnd('\\', '/');
            string parentDirTrimmed = parentDir.TrimEnd('\\', '/');
            if (string.Equals(parentDirTrimmed, launcherDir, StringComparison.OrdinalIgnoreCase))
            {
                ShowNotification(Lang.T("Detail.LauncherDirRefused"));
                return;
            }

            // 判断父目录是否还有其他游戏
            bool hasOtherGames = false;
            try
            {
                var siblings = Directory.GetFiles(parentDir, "*", SearchOption.TopDirectoryOnly);
                foreach (var s in siblings)
                {
                    string sn = Path.GetFileName(s).ToLowerInvariant();
                    if (sn != Path.GetFileName(gamePath).ToLowerInvariant()
                        && (sn.EndsWith(".exe") || sn.EndsWith(".py")))
                    {
                        hasOtherGames = true;
                        break;
                    }
                }
                var subDirs = Directory.GetDirectories(parentDir);
                if (subDirs.Length > 0) hasOtherGames = true;
            }
            catch { }

            bool deleteWholeDir = !hasOtherGames;
            string confirmMsg = deleteWholeDir
                ? Lang.T("Detail.DeleteConfirm", parentDir)
                : Lang.T("Detail.DeleteConfirmPartial", gamePath);

            bool confirm = await ShowConfirmDialogAsync(confirmMsg);
            if (!confirm) return;

            try
            {
                ShowNotification(Lang.T("Detail.Deleting"));

                if (_currentGameProcess != null && !_currentGameProcess.HasExited)
                {
                    try
                    {
                        string runningExe = _currentGameProcess.StartInfo.FileName;
                        if (string.Equals(runningExe, gamePath, StringComparison.OrdinalIgnoreCase))
                        {
                            _currentGameProcess.Exited -= OnGameProcessExited;
                            _currentGameProcess.Kill();
                            await Task.Run(() => _currentGameProcess.WaitForExit(3000));
                            SetGameRunning(false);
                        }
                    }
                    catch { }
                }

                await Task.Run(() =>
                {
                    try
                    {
                        foreach (var f in Directory.GetFiles(parentDir, "*", SearchOption.AllDirectories))
                        {
                            try { File.SetAttributes(f, FileAttributes.Normal); } catch { }
                        }
                    }
                    catch { }
                });

                bool deleteOk = await Task.Run(() =>
                {
                    try
                    {
                        if (deleteWholeDir) Directory.Delete(parentDir, true);
                        else File.Delete(gamePath);
                        return true;
                    }
                    catch (IOException)
                    {
                        System.Threading.Thread.Sleep(500);
                        try
                        {
                            if (deleteWholeDir) Directory.Delete(parentDir, true);
                            else File.Delete(gamePath);
                            return true;
                        }
                        catch { return false; }
                    }
                    catch { return false; }
                });

                if (deleteOk)
                {
                    try
                    {
                        GameStatsManager.RemoveRecordsByPath(gamePath);
                        GameStatsManager.RemoveSessionsByPath(gamePath);
                    }
                    catch { }

                    HideDetailPanel();
                    _currentDetailGamePath = null;

                    await ScanGamesAsync();
                    ShowNotification(Lang.T("Detail.Deleted"));
                }
                else
                {
                    ShowDetailPanel(Lang.T("Detail.DeleteFailed"),
                        Lang.T("Detail.DeleteFailedMsg", parentDir));
                }
            }
            catch (Exception ex)
            {
                ShowDetailPanel(Lang.T("Detail.DeleteFailed"), ex.Message);
            }
        }

        private async Task ScanGamesAsync()
        {
            var list = new List<GameFileInfo>();
            var dirs = _config.Directories;

            await Task.Run(() =>
            {
                var exeDirPattern = new Regex(@"^(\d+)\.(\d+)\.(\d+)$");
                var pyPattern = new Regex(@"贪吃蛇[（(](\d+)\.(\d+)\.(\d+)[）)]\.py$", RegexOptions.IgnoreCase);

                foreach (string baseDir in dirs)
                {
                    if (!Directory.Exists(baseDir)) continue;
                    string baseDirTrimmed = baseDir.TrimEnd('\\', '/');
                    string baseDirName = Path.GetFileName(baseDirTrimmed);

                    try
                    {
                        // A. <baseDir>/<版本目录>/dist/贪吃蛇.exe
                        foreach (var subDir in Directory.GetDirectories(baseDir))
                        {
                            var dirName = Path.GetFileName(subDir);
                            var match = exeDirPattern.Match(dirName);
                            if (!match.Success) continue;

                            string exePath = Path.Combine(subDir, "dist", "贪吃蛇.exe");
                            if (File.Exists(exePath))
                            {
                                list.Add(new GameFileInfo
                                {
                                    Version = new Version(int.Parse(match.Groups[1].Value), int.Parse(match.Groups[2].Value), int.Parse(match.Groups[3].Value)),
                                    DisplayName = Path.GetFileName(exePath),
                                    FullPath = exePath,
                                    IsPython = false
                                });
                            }
                        }

                        // B. <baseDir>/SnakeGame.exe
                        string snakePath = Path.Combine(baseDir, "SnakeGame.exe");
                        if (File.Exists(snakePath))
                        {
                            list.Add(new GameFileInfo
                            {
                                Version = new Version(9999, 9999, 9999),
                                DisplayName = "SnakeGame.exe",
                                FullPath = snakePath,
                                IsPython = false
                            });
                        }

                        // C. 递归 *.py
                        foreach (var file in Directory.GetFiles(baseDir, "*.py", SearchOption.AllDirectories))
                        {
                            var match = pyPattern.Match(Path.GetFileName(file));
                            if (!match.Success) continue;

                            list.Add(new GameFileInfo
                            {
                                Version = new Version(int.Parse(match.Groups[1].Value), int.Parse(match.Groups[2].Value), int.Parse(match.Groups[3].Value)),
                                DisplayName = Path.GetFileName(file),
                                FullPath = file,
                                IsPython = true
                            });
                        }

                        // D. SnakeGameWpf.exe
                        foreach (var exePath in Directory.GetFiles(baseDir, "SnakeGameWpf.exe", SearchOption.AllDirectories))
                        {
                            AddExeGameFromPath(list, exePath, baseDirTrimmed, baseDirName, exeDirPattern);
                        }

                        // E. 版本目录里的 SnakeGame.exe
                        foreach (var exePath in Directory.GetFiles(baseDir, "SnakeGame.exe", SearchOption.AllDirectories))
                        {
                            string exeDir = Path.GetDirectoryName(exePath)?.TrimEnd('\\', '/');
                            if (string.Equals(exeDir, baseDirTrimmed, StringComparison.OrdinalIgnoreCase))
                                continue;

                            AddExeGameFromPath(list, exePath, baseDirTrimmed, baseDirName, exeDirPattern);
                        }
                    }
                    catch (Exception ex)
                    {
                        Debug.WriteLine($"扫描目录 {baseDir} 出错: {ex.Message}");
                    }
                }

                var byPath = list
                    .GroupBy(g => g.FullPath, StringComparer.OrdinalIgnoreCase)
                    .Select(g => g.First())
                    .ToList();

                list = byPath
                    .GroupBy(g => g.Version)
                    .Select(g => g.FirstOrDefault(x => !x.IsPython) ?? g.First())
                    .ToList();
            });

            Dispatcher.Invoke(() =>
            {
                _gameFiles = list;
                ApplySort();
                RefreshCards();
                UpdateHomePage();
            });
        }

        private static void AddExeGameFromPath(
            List<GameFileInfo> list,
            string exePath,
            string baseDirTrimmed,
            string baseDirName,
            Regex exeDirPattern)
        {
            string parentDirName = Path.GetFileName(Path.GetDirectoryName(exePath) ?? "");
            Version ver;

            var dirMatch = exeDirPattern.Match(parentDirName);
            if (dirMatch.Success)
            {
                ver = new Version(int.Parse(dirMatch.Groups[1].Value), int.Parse(dirMatch.Groups[2].Value), int.Parse(dirMatch.Groups[3].Value), 0);
            }
            else
            {
                ver = GetExeFileVersion(exePath);
            }

            list.Add(new GameFileInfo
            {
                Version = ver,
                DisplayName = Path.GetFileName(exePath),
                FullPath = exePath,
                IsPython = false
            });
        }

        private void ManualAdd()
        {
            var ofd = new OpenFileDialog { Filter = "Game Files|*.exe;*.py|All Files|*.*" };
            if (ofd.ShowDialog() == true)
            {
                var path = ofd.FileName;
                _gameFiles.Add(new GameFileInfo { Version = new Version(0, 0, 0), DisplayName = Path.GetFileName(path), FullPath = path, IsPython = path.EndsWith(".py") });
                ApplySort(); RefreshCards(); UpdateHomePage();
            }
        }

        // ========== 数据页面 ==========
        // ========== 数据页面 ==========
        private UIElement CreateStatsPage()
        {
            var scrollViewer = new ScrollViewer
            {
                VerticalScrollBarVisibility = ScrollBarVisibility.Auto,
                HorizontalScrollBarVisibility = ScrollBarVisibility.Disabled
            };
            var stack = new StackPanel { Margin = new Thickness(4, 4, 4, 16) };

            var records = GameStatsManager.LoadRecords() ?? new List<PlayRecord>();
            var sessions = GameStatsManager.LoadSessions() ?? new List<GameSessionRecord>();

            double totalMinutes = records.Sum(r => r.TotalPlayMinutes);
            int totalLaunches = records.Sum(r => r.LaunchCount);
            int bestScore = sessions.Count > 0 ? sessions.Max(s => s.FinalScore) : 0;
            int totalKills = sessions.Sum(s => s.FinalKills);

            // 页头
            var header = new StackPanel { Margin = new Thickness(2, 0, 2, 14) };
            header.Children.Add(Ui.Heading(Lang.T("Stats.Overview"), 20));
            header.Children.Add(Ui.Text(
                Lang.T("Stats.Continue") + " · " + sessions.Count + " 场对局记录",
                12, FontWeights.Normal, Ui.TextTertiary, 0));
            stack.Children.Add(header);

            // 概览：4 张统计卡片
            var overviewPanel = new UniformGrid { Rows = 1, Columns = 4 };
            overviewPanel.Children.Add(CreateStatCard(Lang.T("Stats.TotalPlaytime"),
                FormatDurationValue(totalMinutes), FormatDurationUnit(totalMinutes), Ui.Accent));
            overviewPanel.Children.Add(CreateStatCard(Lang.T("Stats.LaunchCount"),
                totalLaunches.ToString(), "", Ui.Positive));
            overviewPanel.Children.Add(CreateStatCard(Lang.T("Stats.BestScore"),
                bestScore.ToString(), "", Ui.Accent));
            overviewPanel.Children.Add(CreateStatCard(Lang.T("Stats.TotalKills"),
                totalKills.ToString(), "", Ui.Negative));
            stack.Children.Add(overviewPanel);

            // 继续上一次对局
            var recentRecord = records.OrderByDescending(r => r.LastPlayed).FirstOrDefault();
            if (recentRecord != null && !string.IsNullOrEmpty(recentRecord.GamePath)
                && File.Exists(recentRecord.GamePath))
            {
                var quickPanel = new Grid();
                quickPanel.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
                quickPanel.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

                var infoStack = new StackPanel { VerticalAlignment = VerticalAlignment.Center };
                infoStack.Children.Add(Ui.Text(Path.GetFileName(recentRecord.GamePath), 15, FontWeights.SemiBold, Ui.TextPrimary, 0));
                infoStack.Children.Add(Ui.Text(Lang.T("Stats.LastPlayed", recentRecord.LastPlayed,
                    recentRecord.LaunchCount,
                    FormatDurationValue(recentRecord.TotalPlayMinutes),
                    FormatDurationUnit(recentRecord.TotalPlayMinutes)),
                    12, FontWeights.Normal, Ui.TextTertiary, 0));
                Grid.SetColumn(infoStack, 0);
                quickPanel.Children.Add(infoStack);

                var btnContinue = new Button
                {
                    Content = Lang.T("Stats.Continue"),
                    Style = SafeFindStyle("RoundedButton"),
                    Width = 140,
                    Height = 38,
                    VerticalAlignment = VerticalAlignment.Center,
                };
                string recentPath = recentRecord.GamePath;
                bool isPython = recentPath.EndsWith(".py", StringComparison.OrdinalIgnoreCase);
                btnContinue.Click += async (s, e) => await LaunchGame(recentPath, isPython);
                Grid.SetColumn(btnContinue, 1);
                quickPanel.Children.Add(btnContinue);

                var quickSection = Ui.SectionCard(Lang.T("Stats.Continue"), quickPanel);
                stack.Children.Add(quickSection);
            }

            // 最佳成绩
            var bestStack = new StackPanel();
            if (sessions.Count == 0)
            {
                bestStack.Children.Add(Ui.Text(Lang.T("Stats.NoSessions"), 13, FontWeights.Normal, Ui.TextTertiary, 0));
            }
            else
            {
                var byGame = sessions
                    .Where(s => !string.IsNullOrEmpty(s.GamePath))
                    .GroupBy(s => s.GamePath)
                    .Select(g => new
                    {
                        Path = g.Key,
                        Best = g.OrderByDescending(s => s.FinalScore).First(),
                        TotalMinutes = g.Sum(s => s.DurationMinutes),
                        SessionCount = g.Count()
                    })
                    .OrderByDescending(x => x.Best.FinalScore)
                    .ToList();

                foreach (var grp in byGame)
                {
                    bestStack.Children.Add(CreateBestScoreRow(grp.Path, grp.Best, grp.TotalMinutes, grp.SessionCount));
                }
            }
            stack.Children.Add(Ui.SectionCard(Lang.T("Stats.BestScores"), bestStack));

            // 最近对局
            var recentStack = new StackPanel();
            if (sessions.Count == 0)
            {
                recentStack.Children.Add(Ui.Text(Lang.T("Stats.NoRecent"), 13, FontWeights.Normal, Ui.TextTertiary, 0));
            }
            else
            {
                foreach (var session in sessions.OrderByDescending(s => s.StartTime).Take(15))
                {
                    recentStack.Children.Add(CreateSessionRow(session));
                }
            }
            stack.Children.Add(Ui.SectionCard(Lang.T("Stats.RecentSessions"), recentStack));

            scrollViewer.Content = stack;
            return scrollViewer;
        }

        private Border CreateStatCard(string label, string value, string unit, Brush accent)
        {
            var stack = new StackPanel();
            stack.Children.Add(Ui.Text(label, 12, FontWeights.Normal, Ui.TextSecondary, 0));

            var valuePanel = new StackPanel { Orientation = Orientation.Horizontal, Margin = new Thickness(0, 6, 0, 0) };
            valuePanel.Children.Add(new TextBlock
            {
                Text = value,
                FontSize = 30,
                FontWeight = FontWeights.SemiBold,
                FontFamily = Ui.Font,
                Foreground = accent,
            });
            if (!string.IsNullOrEmpty(unit))
            {
                valuePanel.Children.Add(new TextBlock
                {
                    Text = unit,
                    FontSize = 12,
                    FontFamily = Ui.Font,
                    Foreground = Ui.TextTertiary,
                    VerticalAlignment = VerticalAlignment.Bottom,
                    Margin = new Thickness(4, 0, 0, 5),
                });
            }
            stack.Children.Add(valuePanel);

            var card = Ui.Card(stack, new Thickness(18, 14, 18, 14));
            card.Margin = new Thickness(5);
            return card;
        }

        private Border CreateBestScoreRow(string path, GameSessionRecord best, double totalMinutes, int sessionCount)
        {
            var row = new Border
            {
                Padding = new Thickness(14, 11, 14, 11),
                Margin = new Thickness(0, 3, 0, 3),
                CornerRadius = new CornerRadius(10),
                Background = Ui.SurfaceSunken,
            };
            row.MouseEnter += (s, e) => row.Background = Ui.SurfaceHover;
            row.MouseLeave += (s, e) => row.Background = Ui.SurfaceSunken;

            var grid = new Grid();
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

            var nameStack = new StackPanel { VerticalAlignment = VerticalAlignment.Center, Margin = new Thickness(0, 0, 12, 0) };
            var nameText = Ui.Text(Path.GetFileName(path), 13, FontWeights.SemiBold, Ui.TextPrimary, 0);
            nameText.TextTrimming = TextTrimming.CharacterEllipsis;
            nameStack.Children.Add(nameText);
            nameStack.Children.Add(Ui.Text(Lang.T("Stats.SessionCount", sessionCount,
                FormatDurationValue(totalMinutes), FormatDurationUnit(totalMinutes)),
                11, FontWeights.Normal, Ui.TextTertiary, 0));
            Grid.SetColumn(nameStack, 0);
            grid.Children.Add(nameStack);

            var scoreStack = new StackPanel { VerticalAlignment = VerticalAlignment.Center, Margin = new Thickness(16, 0, 16, 0) };
            var scoreLabel = Ui.Text(Lang.T("Stats.BestLabel"), 10, FontWeights.Normal, Ui.TextTertiary, 1);
            scoreLabel.HorizontalAlignment = HorizontalAlignment.Center;
            scoreStack.Children.Add(scoreLabel);
            var scoreValue = Ui.Text(best.FinalScore.ToString(), 20, FontWeights.SemiBold, Ui.Accent, 1);
            scoreValue.HorizontalAlignment = HorizontalAlignment.Center;
            scoreStack.Children.Add(scoreValue);
            Grid.SetColumn(scoreStack, 1);
            grid.Children.Add(scoreStack);

            var killStack = new StackPanel { VerticalAlignment = VerticalAlignment.Center, Margin = new Thickness(16, 0, 16, 0) };
            var killLabel = Ui.Text(Lang.T("Stats.KillLabel"), 10, FontWeights.Normal, Ui.TextTertiary, 2);
            killLabel.HorizontalAlignment = HorizontalAlignment.Center;
            killStack.Children.Add(killLabel);
            var killValue = Ui.Text(best.FinalKills.ToString(), 20, FontWeights.SemiBold, Ui.TextPrimary, 2);
            killValue.HorizontalAlignment = HorizontalAlignment.Center;
            killStack.Children.Add(killValue);
            Grid.SetColumn(killStack, 2);
            grid.Children.Add(killStack);

            var btnStart = new Button
            {
                Content = Lang.T("Launch.Card.Start"),
                Style = SafeFindStyle("RoundedButton"),
                Width = 84,
                Height = 34,
                VerticalAlignment = VerticalAlignment.Center,
            };
            string gamePath = path;
            bool isPython = gamePath.EndsWith(".py", StringComparison.OrdinalIgnoreCase);
            btnStart.Click += async (s, e) => await LaunchGame(gamePath, isPython);
            Grid.SetColumn(btnStart, 3);
            grid.Children.Add(btnStart);

            row.Child = grid;
            return row;
        }

        private Border CreateSessionRow(GameSessionRecord session)
        {
            var row = new Border
            {
                Padding = new Thickness(14, 9, 14, 9),
                Margin = new Thickness(0, 2, 0, 2),
                CornerRadius = new CornerRadius(10),
                Background = Ui.SurfaceSunken,
            };
            row.Background = Ui.SurfaceSunken;
            // 悬停轻微高亮（100ms 内心反馈，不移动布局）
            row.MouseEnter += (s, e) => row.Background = Ui.SurfaceHover;
            row.MouseLeave += (s, e) => row.Background = Ui.SurfaceSunken;

            var grid = new Grid();
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(140) });
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(100) });
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(80) });
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(110) });

            grid.Children.Add(Ui.Text(session.StartTime.ToString("MM-dd HH:mm"), 12, FontWeights.Normal, Ui.TextTertiary, 0));

            string gameName = string.IsNullOrEmpty(session.GamePath) ? "未知" : Path.GetFileNameWithoutExtension(session.GamePath);
            var nameBlock = Ui.Text(gameName, 12, FontWeights.Normal, Ui.TextPrimary, 1);
            nameBlock.TextTrimming = TextTrimming.CharacterEllipsis;
            nameBlock.Margin = new Thickness(0, 0, 8, 0);
            grid.Children.Add(nameBlock);

            var modeBlock = Ui.Text(GetModeDisplayName(session.Mode), 12, FontWeights.Normal, Ui.TextSecondary, 2);
            modeBlock.HorizontalAlignment = HorizontalAlignment.Center;
            grid.Children.Add(modeBlock);

            var durBlock = Ui.Text($"{session.DurationMinutes:F1}", 12, FontWeights.Normal, Ui.TextSecondary, 3);
            durBlock.HorizontalAlignment = HorizontalAlignment.Center;
            grid.Children.Add(durBlock);

            var scoreBlock = Ui.Text($"{session.FinalScore} / {session.FinalKills}", 12, FontWeights.SemiBold, Ui.Accent, 4);
            scoreBlock.HorizontalAlignment = HorizontalAlignment.Right;
            scoreBlock.Margin = new Thickness(0, 0, 6, 0);
            grid.Children.Add(scoreBlock);

            row.Child = grid;
            return row;
        }

        private static string FormatDurationValue(double minutes)
        {
            if (minutes < 1) return "0";
            if (minutes < 60) return ((int)Math.Round(minutes)).ToString();
            return (minutes / 60.0).ToString("F1");
        }

        private static string FormatDurationUnit(double minutes)
        {
            if (minutes < 60) return Lang.T("Unit.Minute");
            return Lang.T("Unit.Hour");
        }

        // ========== 下载页面 ==========
        private UIElement CreateDownloadPage()
        {
            var mainGrid = new Grid();
            mainGrid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            mainGrid.RowDefinitions.Add(new RowDefinition { Height = new GridLength(1, GridUnitType.Star) });

            var topPanel = new StackPanel { Orientation = Orientation.Horizontal, Margin = new Thickness(0, 0, 0, 12) };

            var repoCombo = new ComboBox
            {
                Width = 220,
                Height = 34,
                Margin = new Thickness(0, 0, 8, 0),
                Style = SafeFindStyle("CustomComboBoxStyle")
            };
            foreach (var repo in GitHubReleaseService.Repos)
            {
                repoCombo.Items.Add(new ComboBoxItem { Content = repo.DisplayName, Tag = repo });
            }
            repoCombo.SelectedIndex = 0;

            repoCombo.SelectionChanged += async (s, e) =>
            {
                var selected = (repoCombo.SelectedItem as ComboBoxItem)?.Tag as GitHubRepoConfig;
                if (selected != null)
                    await LoadGitHubReleasesAsync(selected);
            };

            var btnRefresh = new Button
            {
                Content = Lang.T("Download.Refresh"),
                Style = SafeFindStyle("RoundedButton"),
                Width = 108,
                Height = 34,
                Margin = new Thickness(0, 0, 8, 0)
            };
            btnRefresh.Click += async (s, e) =>
            {
                var selected = (repoCombo.SelectedItem as ComboBoxItem)?.Tag as GitHubRepoConfig;
                if (selected != null)
                    await LoadGitHubReleasesAsync(selected);
            };

            var btnOpenRepo = new Button
            {
                Content = Lang.T("Download.OpenRepo"),
                Style = SafeFindStyle("RoundedButton"),
                Width = 108,
                Height = 34
            };
            btnOpenRepo.Click += (s, e) =>
            {
                var selected = (repoCombo.SelectedItem as ComboBoxItem)?.Tag as GitHubRepoConfig;
                if (selected == null) return;
                try
                {
                    Process.Start(new ProcessStartInfo
                    {
                        FileName = $"https://github.com/{selected.Owner}/{selected.Repo}/releases",
                        UseShellExecute = true
                    });
                }
                catch { }
            };

            topPanel.Children.Add(repoCombo);
            topPanel.Children.Add(btnRefresh);
            topPanel.Children.Add(btnOpenRepo);

            // ★ 仓库文档按钮
            var btnRepoDocs = new Button
            {
                Content = "仓库文档",
                Style = SafeFindStyle("RoundedButton"),
                Width = 108,
                Height = 34,
                Margin = new Thickness(8, 0, 0, 0)
            };
            btnRepoDocs.Click += async (s, e) =>
            {
                var selected = (repoCombo.SelectedItem as ComboBoxItem)?.Tag as GitHubRepoConfig;
                if (selected != null)
                    await ShowRepoDocsPanelAsync(selected);
            };
            topPanel.Children.Add(btnRepoDocs);

            _downloadListPanel = new StackPanel { Margin = new Thickness(0) };
            var scrollViewer = new ScrollViewer
            {
                Content = _downloadListPanel,
                VerticalScrollBarVisibility = ScrollBarVisibility.Auto,
                HorizontalScrollBarVisibility = ScrollBarVisibility.Disabled
            };

            Grid.SetRow(topPanel, 0);
            Grid.SetRow(scrollViewer, 1);
            mainGrid.Children.Add(topPanel);
            mainGrid.Children.Add(scrollViewer);

            _ = LoadGitHubReleasesAsync(GitHubReleaseService.Repos[0]);

            return mainGrid;
        }

        private async Task LoadGitHubReleasesAsync(GitHubRepoConfig repoConfig)
        {
            if (_downloadListPanel == null) return;

            _downloadListPanel.Children.Clear();
            _downloadListPanel.Children.Add(new TextBlock
            {
                Text = Lang.T("Download.Loading"),
                FontSize = 13,
                Foreground = SafeFindBrush("SecondaryForegroundBrush"),
                HorizontalAlignment = HorizontalAlignment.Center,
                Margin = new Thickness(0, 40, 0, 0)
            });

            try
            {
                var releases = await GitHubReleaseService.GetReleasesAsync(repoConfig);

                _downloadListPanel.Children.Clear();

                if (releases == null || releases.Count == 0)
                {
                    _downloadListPanel.Children.Add(new TextBlock
                    {
                        Text = Lang.T("Download.NoReleases"),
                        FontSize = 13,
                        Foreground = SafeFindBrush("SecondaryForegroundBrush"),
                        HorizontalAlignment = HorizontalAlignment.Center,
                        Margin = new Thickness(0, 40, 0, 0)
                    });
                    return;
                }

                // ★ 只统计非预发布版本中的最高版本号
                _latestReleaseVersion = releases
                    .Where(r => !r.IsPrerelease && r.ParsedVersion != null)
                    .Select(r => r.ParsedVersion)
                    .OrderByDescending(v => v)
                    .FirstOrDefault();

                // 兜底：如果全是预发布版本，就用所有版本里最高的
                if (_latestReleaseVersion == null)
                {
                    _latestReleaseVersion = releases
                        .Where(r => r.ParsedVersion != null)
                        .Select(r => r.ParsedVersion)
                        .OrderByDescending(v => v)
                        .FirstOrDefault();
                }

                foreach (var release in releases)
                {
                    var card = CreateReleaseCard(release);
                    _downloadListPanel.Children.Add(card);
                }
            }
            catch (Exception ex)
            {
                _downloadListPanel.Children.Clear();
                _downloadListPanel.Children.Add(new TextBlock
                {
                    Text = Lang.T("Download.LoadFailed", ex.Message),
                    FontSize = 13,
                    Foreground = new SolidColorBrush(Color.FromRgb(0xD1, 0x34, 0x38)),
                    HorizontalAlignment = HorizontalAlignment.Center,
                    Margin = new Thickness(0, 40, 0, 0),
                    TextWrapping = TextWrapping.Wrap
                });
            }
        }

        private Border CreateReleaseCard(GitHubRelease release)
        {
            var card = new Border
            {
                Style = SafeFindStyle("GameCardStyle"),
                Margin = new Thickness(0, 0, 0, 10),
                Padding = new Thickness(16, 12, 16, 12),
                HorizontalAlignment = HorizontalAlignment.Stretch
            };

            var grid = new Grid();
            grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });

            // ===== 标题行 =====
            var titleBar = new Grid();
            titleBar.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            titleBar.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

            var titleStack = new StackPanel { Orientation = Orientation.Horizontal };
            titleStack.Children.Add(new TextBlock
            {
                Text = release.TagName ?? "",
                FontSize = 16,
                FontWeight = FontWeights.Bold,
                Foreground = SafeFindBrush("ForegroundBrush"),
                VerticalAlignment = VerticalAlignment.Center
            });

            // ★ 预发布标签（橙色）
            if (release.IsPrerelease)
            {
                titleStack.Children.Add(new Border
                {
                    Background = new SolidColorBrush(Color.FromRgb(0xFF, 0x8C, 0x00)),
                    CornerRadius = new CornerRadius(999),
                    Padding = new Thickness(6, 2, 6, 2),
                    Margin = new Thickness(8, 0, 0, 0),
                    VerticalAlignment = VerticalAlignment.Center,
                    Child = new TextBlock
                    {
                        Text = "预发布",
                        FontSize = 10,
                        FontWeight = FontWeights.SemiBold,
                        Foreground = Brushes.White
                    }
                });
            }
            // ★ 最新标签（仅正式版本且为最新时显示）
            else if (release.ParsedVersion != null && _latestReleaseVersion != null
                && release.ParsedVersion >= _latestReleaseVersion)
            {
                titleStack.Children.Add(new Border
                {
                    Background = SafeFindBrush("AccentBrush"),
                    CornerRadius = new CornerRadius(999),
                    Padding = new Thickness(6, 2, 6, 2),
                    Margin = new Thickness(8, 0, 0, 0),
                    VerticalAlignment = VerticalAlignment.Center,
                    Child = new TextBlock
                    {
                        Text = Lang.T("Download.Latest"),
                        FontSize = 10,
                        FontWeight = FontWeights.SemiBold,
                        Foreground = Brushes.White
                    }
                });
            }

            titleStack.Children.Add(new TextBlock
            {
                Text = release.PublishedAt.ToString("yyyy-MM-dd"),
                FontSize = 11,
                Foreground = SafeFindBrush("SecondaryForegroundBrush"),
                VerticalAlignment = VerticalAlignment.Center,
                Margin = new Thickness(12, 0, 0, 0)
            });

            Grid.SetColumn(titleStack, 0);
            titleBar.Children.Add(titleStack);

            var expandBtn = new Button
            {
                Content = "▾",
                Width = 32,
                Height = 28,
                FontSize = 14,
                Background = Brushes.Transparent,
                Foreground = SafeFindBrush("ForegroundBrush"),
                BorderThickness = new Thickness(0),
                Cursor = Cursors.Hand,
                VerticalAlignment = VerticalAlignment.Center
            };
            Grid.SetColumn(expandBtn, 1);
            titleBar.Children.Add(expandBtn);

            Grid.SetRow(titleBar, 0);
            grid.Children.Add(titleBar);

            // ===== 说明 =====
            var notesText = new TextBlock
            {
                Text = string.IsNullOrWhiteSpace(release.Body) ? Lang.T("Download.NoNotes") : release.Body,
                FontSize = 12,
                Foreground = SafeFindBrush("SecondaryForegroundBrush"),
                TextWrapping = TextWrapping.Wrap,
                MaxHeight = 60,
                TextTrimming = TextTrimming.CharacterEllipsis,
                Margin = new Thickness(0, 8, 0, 0)
            };
            Grid.SetRow(notesText, 1);
            grid.Children.Add(notesText);

            // ===== assets 容器（默认隐藏） =====
            var assetsPanel = new StackPanel
            {
                Margin = new Thickness(0, 10, 0, 0),
                Visibility = Visibility.Collapsed
            };

            var gameAssets = release.Assets?
                .Where(a => a.IsGamePackage &&
                            (string.IsNullOrEmpty(a.Platform) ||
                             string.Equals(a.Platform, "windows", StringComparison.OrdinalIgnoreCase)))
                .OrderByDescending(a => a.ParsedVersion ?? new Version(0, 0, 0, 0))
                .ToList() ?? new List<GitHubReleaseAsset>();

            if (gameAssets.Count > 0)
            {
                foreach (var asset in gameAssets)
                {
                    assetsPanel.Children.Add(CreateAssetRow(asset, release));
                }
            }
            else
            {
                assetsPanel.Children.Add(new TextBlock
                {
                    Text = Lang.T("Download.Asset.NotGamePackage"),
                    FontSize = 12,
                    Foreground = SafeFindBrush("SecondaryForegroundBrush"),
                    Margin = new Thickness(0, 4, 0, 4),
                    TextWrapping = TextWrapping.Wrap
                });
            }

            Grid.SetRow(assetsPanel, 2);
            grid.Children.Add(assetsPanel);

            // 展开/收起
            bool expanded = false;
            expandBtn.Click += (s, e) =>
            {
                expanded = !expanded;
                assetsPanel.Visibility = expanded ? Visibility.Visible : Visibility.Collapsed;
                expandBtn.Content = expanded ? "▴" : "▾";
                notesText.MaxHeight = expanded ? double.PositiveInfinity : 60;
                notesText.TextTrimming = expanded ? TextTrimming.None : TextTrimming.CharacterEllipsis;
            };

            card.Child = grid;
            return card;
        }

        private Border CreateAssetRow(GitHubReleaseAsset asset, GitHubRelease release)
        {
            var row = new Border
            {
                Padding = new Thickness(10, 8, 10, 8),
                Margin = new Thickness(0, 2, 0, 2),
                CornerRadius = new CornerRadius(6),
                Background = new SolidColorBrush(Color.FromArgb(0x08, 0, 0, 0))
            };

            var grid = new Grid();
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

            var leftStack = new StackPanel { VerticalAlignment = VerticalAlignment.Center };
            leftStack.Children.Add(new TextBlock
            {
                Text = asset.Name,
                FontSize = 12,
                FontWeight = FontWeights.SemiBold,
                Foreground = SafeFindBrush("ForegroundBrush"),
                TextTrimming = TextTrimming.CharacterEllipsis
            });

            if (asset.ParsedVersion != null)
            {
                leftStack.Children.Add(new TextBlock
                {
                    Text = Lang.T("Download.Asset.Version", asset.ParsedVersion),
                    FontSize = 10,
                    Foreground = SafeFindBrush("SecondaryForegroundBrush"),
                    Margin = new Thickness(0, 2, 0, 0)
                });
            }

            Grid.SetColumn(leftStack, 0);
            grid.Children.Add(leftStack);

            string sizeStr = asset.Size > 0 ? $"{asset.Size / 1048576.0:F1} MB" : Lang.T("Download.Size.Unknown");
            var sizeText = new TextBlock
            {
                Text = sizeStr,
                FontSize = 11,
                Foreground = SafeFindBrush("SecondaryForegroundBrush"),
                VerticalAlignment = VerticalAlignment.Center,
                Margin = new Thickness(12, 0, 12, 0)
            };
            Grid.SetColumn(sizeText, 1);
            grid.Children.Add(sizeText);

            var btnDownload = new Button
            {
                Content = Lang.T("Download.Asset.Download"),
                Style = SafeFindStyle("RoundedButton"),
                Width = 80,
                Height = 30
            };
            btnDownload.Click += async (s, e) =>
            {
                await DownloadGitHubAssetAsync(asset, release);
            };
            Grid.SetColumn(btnDownload, 2);
            grid.Children.Add(btnDownload);

            row.Child = grid;
            return row;
        }

        private async Task DownloadGitHubAssetAsync(GitHubReleaseAsset asset, GitHubRelease release)
        {
            try
            {
                if (!asset.IsGamePackage || asset.ParsedVersion == null)
                {
                    ShowDetailPanel(Lang.T("Validate.Title"),
                        Lang.T("Validate.NotGamePackage", asset.Name));
                    return;
                }

                string downloadDir = _config.DownloadPath;
                if (string.IsNullOrWhiteSpace(downloadDir))
                    downloadDir = Path.Combine(Path.GetTempPath(), "SnakeGameDownloads");

                var pathChoice = await ShowDownloadPathConfirmAsync(downloadDir);

                if (pathChoice == DownloadPathChoice.Cancel)
                {
                    ShowNotification(Lang.T("Download.Cancelled"));
                    return;
                }

                if (pathChoice == DownloadPathChoice.Change)
                {
                    using (var dialog = new System.Windows.Forms.FolderBrowserDialog())
                    {
                        dialog.Description = Lang.T("Download.Folder.Pick");
                        dialog.SelectedPath = downloadDir;
                        if (dialog.ShowDialog() == System.Windows.Forms.DialogResult.OK)
                        {
                            downloadDir = dialog.SelectedPath;
                            _config.DownloadPath = downloadDir;

                            if (!_config.Directories.Any(d =>
                                    string.Equals(d, downloadDir, StringComparison.OrdinalIgnoreCase)))
                            {
                                _config.Directories.Add(downloadDir);
                            }

                            ConfigManager.Save(_config);
                        }
                        else
                        {
                            ShowNotification(Lang.T("Download.Cancelled"));
                            return;
                        }
                    }
                }

                Directory.CreateDirectory(downloadDir);
                string zipPath = Path.Combine(downloadDir, asset.Name);

                if (File.Exists(zipPath))
                {
                    try { File.Delete(zipPath); } catch { }
                }

                ShowNotification(Lang.T("Download.Checking", asset.Name));
                var progress = new Progress<double>(p =>
                {
                    ShowNotification(Lang.T("Download.Progress", asset.Name, p));
                });
                await DownloadWithProgressAsync(asset.BrowserDownloadUrl, zipPath, progress);

                var (isValid, message, rootFiles) = ValidateGamePackage(zipPath);
                if (!isValid)
                {
                    try { File.Delete(zipPath); } catch { }
                    ShowDetailPanel(Lang.T("Validate.Title"),
                        Lang.T("Validate.Failed", message, rootFiles));
                    return;
                }

                string versionFolder = asset.ParsedVersion.ToString(3);
                string extractDir = Path.Combine(downloadDir, versionFolder);

                if (Directory.Exists(extractDir))
                {
                    try
                    {
                        foreach (var f in Directory.GetFiles(extractDir, "*", SearchOption.AllDirectories))
                        {
                            try { File.SetAttributes(f, FileAttributes.Normal); } catch { }
                        }
                        Directory.Delete(extractDir, true);
                    }
                    catch { }
                }
                Directory.CreateDirectory(extractDir);

                ShowNotification(Lang.T("Download.Extracting", versionFolder));
                await Task.Run(() =>
                {
                    using (var archive = ZipFile.OpenRead(zipPath))
                    {
                        foreach (ZipArchiveEntry entry in archive.Entries)
                        {
                            string destPath = Path.GetFullPath(Path.Combine(extractDir, entry.FullName));
                            if (!destPath.StartsWith(extractDir, StringComparison.OrdinalIgnoreCase))
                                throw new InvalidOperationException("Invalid path");

                            if (string.IsNullOrEmpty(entry.Name))
                            {
                                Directory.CreateDirectory(destPath);
                            }
                            else
                            {
                                Directory.CreateDirectory(Path.GetDirectoryName(destPath));
                                entry.ExtractToFile(destPath, overwrite: true);
                            }
                        }
                    }
                });
                FlattenSingleSubfolder(extractDir);

                try { File.Delete(zipPath); } catch { }

                // Python 依赖自动安装
                if (asset.RepoConfig != null && asset.RepoConfig.IsPythonRepo)
                {
                    await EnsurePythonDependenciesAsync();
                }

                bool addedDir = false;
                if (!_config.Directories.Any(d =>
                        string.Equals(d, downloadDir, StringComparison.OrdinalIgnoreCase)))
                {
                    _config.Directories.Add(downloadDir);
                    ConfigManager.Save(_config);
                    addedDir = true;
                }

                await ScanGamesAsync();

                string extraMsg = addedDir ? "\n" + Lang.T("Download.AddedDir", downloadDir) : "";
                ShowNotification(Lang.T("Download.Installed", versionFolder) + extraMsg);

                SelectTab(0);
            }
            catch (Exception ex)
            {
                ShowDetailPanel(Lang.T("Validate.Title"), ex.Message);
            }
        }

        private async Task DownloadWithProgressAsync(string url, string savePath, IProgress<double> progress)
        {
            using (var http = new HttpClient())
            {
                http.Timeout = TimeSpan.FromMinutes(30);
                http.DefaultRequestHeaders.UserAgent.ParseAdd("SnakeLauncherWPF-Downloader/1.0");

                using (var response = await http.GetAsync(url, HttpCompletionOption.ResponseHeadersRead))
                {
                    response.EnsureSuccessStatusCode();
                    long totalBytes = response.Content.Headers.ContentLength ?? -1;

                    using (var contentStream = await response.Content.ReadAsStreamAsync())
                    using (var fileStream = new FileStream(savePath, FileMode.Create, FileAccess.Write, FileShare.None, 81920, true))
                    {
                        byte[] buffer = new byte[81920];
                        long totalRead = 0;
                        int bytesRead;

                        while ((bytesRead = await contentStream.ReadAsync(buffer, 0, buffer.Length)) > 0)
                        {
                            await fileStream.WriteAsync(buffer, 0, bytesRead);
                            totalRead += bytesRead;

                            if (totalBytes > 0)
                                progress?.Report((double)totalRead / totalBytes * 100);
                        }
                    }
                }
            }
        }

        private static Version GetExeFileVersion(string exePath)
        {
            try
            {
                var fvi = System.Diagnostics.FileVersionInfo.GetVersionInfo(exePath);
                if (!string.IsNullOrWhiteSpace(fvi.FileVersion)
                    && Version.TryParse(fvi.FileVersion, out var v))
                {
                    int major = v.Major;
                    int minor = v.Minor >= 0 ? v.Minor : 0;
                    int build = v.Build >= 0 ? v.Build : 0;
                    int revision = v.Revision >= 0 ? v.Revision : 0;
                    return new Version(major, minor, build, revision);
                }
            }
            catch { }
            return new Version(0, 0, 0);
        }

        /// <summary>
        /// 检测 ZIP 压缩包根目录是否符合游戏包规范
        /// 支持两种包：
        ///   1) C# exe 包：根目录有 SnakeGame.exe/SnakeGameWpf.exe + .json/.dll + 必须依赖
        ///   2) Python 包：根目录有任意 .py 文件
        /// </summary>
        /// <summary>
        /// 校验 GitHub 发行版压缩包。★ 兼容两种结构：
        ///   · 旧 WPF 版：根目录直接放 SnakeGameWpf.exe + SnakeGame.dll + Newtonsoft.Json.dll
        ///   · 新 v9 版：Unity 包，可能在根目录或一层文件夹内（Windows64/SnakeGame.exe + UnityPlayer.dll + SnakeGame_Data/）
        /// </summary>
        private static (bool IsValid, string Message, string RootFiles) ValidateGamePackage(string zipPath)
        {
            try
            {
                using (var archive = ZipFile.OpenRead(zipPath))
                {
                    bool hasExe = false;
                    bool hasPy = false;
                    bool hasNewtonsoftJson = false;
                    bool hasGameDll = false;
                    bool hasRuntimeConfig = false;
                    bool hasUnityPlayer = false;
                    bool hasDataFolder = false;

                    string exeName = null;
                    string pySampleName = null;
                    var rootFiles = new List<string>();
                    var topEntries = new List<string>();

                    foreach (var entry in archive.Entries)
                    {
                        string fullName = entry.FullName.Replace('\\', '/');
                        string lowFull = fullName.ToLowerInvariant();
                        if (lowFull.Contains("_data/") || lowFull.EndsWith("_data"))
                            hasDataFolder = true;

                        string[] parts = fullName.Split('/');
                        int depth = parts.Length - 1;   // 0 = 根目录

                        if (string.IsNullOrEmpty(entry.Name))
                        {
                            if (depth == 0) topEntries.Add(fullName.TrimEnd('/'));
                            continue;
                        }

                        string name = entry.Name;
                        string lower = name.ToLowerInvariant();

                        if (depth == 0) rootFiles.Add(name);
                        else if (depth == 1 && rootFiles.Count < 12) rootFiles.Add(fullName);

                        if (lower == "unityplayer.dll" || lower == "tuanjieplayer.dll") hasUnityPlayer = true;

                        if (lower == "snakegame.exe" || lower == "snakegamewpf.exe")
                        {
                            hasExe = true;
                            if (exeName == null) exeName = name;
                        }
                        else if (lower == "newtonsoft.json.dll") { hasNewtonsoftJson = true; }
                        else if (lower == "snakegame.dll" || lower == "snakegamewpf.dll") { hasGameDll = true; }
                        else if (lower == "snakegame.runtimeconfig.json" || lower == "snakegamewpf.runtimeconfig.json")
                        { hasRuntimeConfig = true; }
                        else if (lower.EndsWith(".py")) { hasPy = true; if (pySampleName == null) pySampleName = name; }
                    }

                    string rootSummary = rootFiles.Count > 0
                        ? string.Join("、", rootFiles.Take(10)) + (rootFiles.Count > 10 ? " …" : "")
                        : string.Join("、", topEntries.Take(10));

                    if (rootFiles.Count == 0 && topEntries.Count == 0)
                        return (false, "压缩包为空。", "（无）");

                    if (hasPy)
                        return (true, "Python 脚本包：" + (pySampleName ?? "脚本"), rootSummary);

                    if (!hasExe)
                        return (false,
                            "未找到 SnakeGame.exe 或 SnakeGameWpf.exe。\n" +
                            "压缩包根目录或第一层文件夹里必须包含这个可执行文件。",
                            rootSummary);

                    // Unity 包（v9.0.0 起）：有 UnityPlayer.dll 或 *_Data 目录即为合法
                    if (hasUnityPlayer || hasDataFolder)
                    {
                        string detail = exeName ?? "SnakeGame.exe";
                        if (hasUnityPlayer) detail += " + UnityPlayer.dll";
                        if (hasDataFolder) detail += " + 游戏数据目录";
                        return (true, "Unity 游戏包（" + detail + "）", rootSummary);
                    }

                    // 旧 WPF/.NET 包：严格校验
                    if (!hasNewtonsoftJson)
                        return (false, "缺少依赖库 Newtonsoft.Json.dll。\n该文件是游戏的必需依赖，缺失会导致启动崩溃。", rootSummary);
                    if (!hasGameDll)
                        return (false, "缺少主程序集 SnakeGame.dll。\nSnakeGame.exe 只是启动外壳，真正的代码在 SnakeGame.dll 中。", rootSummary);
                    if (!hasRuntimeConfig)
                        return (false, "缺少 SnakeGame.runtimeconfig.json。\n该文件告诉 .NET 运行时如何加载程序，缺失会导致启动失败。", rootSummary);

                    return (true, "根目录文件：" + exeName + "、SnakeGame.dll、Newtonsoft.Json.dll", rootSummary);
                }
            }
            catch (Exception ex)
            {
                return (false, $"无法读取压缩包: {ex.Message}", "");
            }
        }

        /// <summary>
        /// 解压后如果只有一层子文件夹（如 Windows64/），把内容上移到版本目录，
        /// 保证扫描器能直接在版本目录下找到 SnakeGame.exe。
        /// </summary>
        private static void FlattenSingleSubfolder(string dir)
        {
            try
            {
                if (!Directory.Exists(dir)) return;
                var files = Directory.GetFiles(dir);
                var dirs = Directory.GetDirectories(dir);
                if (files.Length != 0 || dirs.Length != 1) return;

                string inner = dirs[0];
                foreach (var f in Directory.GetFiles(inner, "*", SearchOption.AllDirectories))
                {
                    string rel = f.Substring(inner.Length).TrimStart('\\', '/');
                    string dest = Path.Combine(dir, rel);
                    string parent = Path.GetDirectoryName(dest);
                    if (!string.IsNullOrEmpty(parent)) Directory.CreateDirectory(parent);
                    if (File.Exists(dest)) File.Delete(dest);
                    File.Move(f, dest);
                }
                Directory.Delete(inner, true);
            }
            catch { /* 扁平化失败不阻塞：扫描器仍会递归查找 */ }
        }

        private async Task EnsurePythonDependenciesAsync()
        {
            ShowNotification(Lang.T("Python.Checking"));

            bool pythonOk = await PythonDependencyManager.IsPythonAvailableAsync();
            if (!pythonOk)
            {
                var result = await ShowConfirmDialogAsync(Lang.T("Python.NotInstalled"));
                if (result)
                {
                    try
                    {
                        Process.Start(new ProcessStartInfo
                        {
                            FileName = "https://www.python.org/downloads/",
                            UseShellExecute = true
                        });
                    }
                    catch { }
                }
                return;
            }

            ShowNotification(Lang.T("Python.CheckDeps"));
            var missing = await PythonDependencyManager.GetMissingPackagesAsync();

            if (missing.Count == 0)
            {
                ShowNotification(Lang.T("Python.DepsReady"));
                return;
            }

            string pkgList = string.Join(", ", missing);
            bool install = await ShowConfirmDialogAsync(Lang.T("Python.MissingDeps", pkgList));

            if (!install)
            {
                ShowNotification(Lang.T("Python.SkipInstall"));
                return;
            }

            foreach (var pkg in missing)
            {
                bool ok = await PythonDependencyManager.InstallPackageAsync(pkg, msg =>
                {
                    Dispatcher.Invoke(() => ShowNotification(msg));
                });

                if (!ok)
                {
                    ShowDetailPanel(Lang.T("Python.DepInstallFailed"),
                        Lang.T("Python.DepInstallFailedMsg", pkg));
                    return;
                }
            }

            ShowNotification(Lang.T("Python.AllInstalled"));
        }

        // ========== 下载路径确认对话框 ==========
        private Task<DownloadPathChoice> ShowDownloadPathConfirmAsync(string path)
        {
            var tcs = new TaskCompletionSource<DownloadPathChoice>();

            var overlay = new Border
            {
                Background = new SolidColorBrush(Color.FromArgb(0xA6, 0x12, 0x1A, 0x2B)),
                Visibility = Visibility.Visible,
                Opacity = 0,
                VerticalAlignment = VerticalAlignment.Stretch,
                HorizontalAlignment = HorizontalAlignment.Stretch
            };

            var panel = new Border
            {
                Width = 500,
                MaxHeight = 420,
                Background = SafeFindBrush("CardBackgroundBrush"),
                BorderBrush = SafeFindBrush("CardBorderBrush"),
                BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(22),
                Padding = new Thickness(26),
                HorizontalAlignment = HorizontalAlignment.Center,
                VerticalAlignment = VerticalAlignment.Center,
                RenderTransformOrigin = new Point(0.5, 0.5)
            };
            panel.Effect = new DropShadowEffect
            {
                ShadowDepth = 10,
                BlurRadius = 36,
                Opacity = 0.35,
                Color = Color.FromRgb(0x0F, 0x1B, 0x33)
            };
            var scale = new ScaleTransform(0.8, 0.8);
            panel.RenderTransform = scale;

            var grid = new Grid();
            grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });

            var title = new TextBlock
            {
                Text = Lang.T("Download.Path.Title"),
                FontSize = 18,
                FontWeight = FontWeights.Bold,
                Foreground = SafeFindBrush("ForegroundBrush")
            };
            Grid.SetRow(title, 0);
            grid.Children.Add(title);

            var pathStack = new StackPanel { Margin = new Thickness(0, 12, 0, 18) };
            pathStack.Children.Add(new TextBlock
            {
                Text = Lang.T("Download.Path.Desc"),
                FontSize = 13,
                Foreground = SafeFindBrush("SecondaryForegroundBrush"),
                Margin = new Thickness(0, 0, 0, 8)
            });
            pathStack.Children.Add(new Border
            {
                Background = SafeFindBrush("BackgroundBrush"),
                CornerRadius = new CornerRadius(6),
                Padding = new Thickness(10, 8, 10, 8),
                Child = new TextBlock
                {
                    Text = path,
                    FontSize = 12,
                    Foreground = SafeFindBrush("ForegroundBrush"),
                    TextWrapping = TextWrapping.Wrap,
                    FontFamily = new FontFamily("Consolas, Microsoft YaHei UI")
                }
            });
            Grid.SetRow(pathStack, 1);
            grid.Children.Add(pathStack);

            var btnRow = new StackPanel
            {
                Orientation = Orientation.Horizontal,
                HorizontalAlignment = HorizontalAlignment.Right
            };

            bool closed = false;
            void CloseDialog()
            {
                if (closed) return;
                closed = true;

                var fadeOut = new DoubleAnimation(1, 0, TimeSpan.FromMilliseconds(150));
                fadeOut.Completed += (s, e) =>
                {
                    try { _rootGrid.Children.Remove(overlay); } catch { }
                };
                var scaleOut = new DoubleAnimation(1.0, 0.85, TimeSpan.FromMilliseconds(150))
                {
                    EasingFunction = new QuadraticEase { EasingMode = EasingMode.EaseIn }
                };
                overlay.BeginAnimation(OpacityProperty, fadeOut);
                scale.BeginAnimation(ScaleTransform.ScaleXProperty, scaleOut);
                scale.BeginAnimation(ScaleTransform.ScaleYProperty, scaleOut);
            }

            var btnCancel = new Button
            {
                Content = Lang.T("Download.Path.Cancel"),
                Style = SafeFindStyle("RoundedButton"),
                Width = 90,
                Height = 38,
                Margin = new Thickness(0, 0, 8, 0)
            };
            btnCancel.Click += (s, e) => { CloseDialog(); tcs.TrySetResult(DownloadPathChoice.Cancel); };

            var btnChange = new Button
            {
                Content = Lang.T("Download.Path.Change"),
                Style = SafeFindStyle("RoundedButton"),
                Width = 110,
                Height = 38,
                Margin = new Thickness(0, 0, 8, 0)
            };
            btnChange.Click += (s, e) => { CloseDialog(); tcs.TrySetResult(DownloadPathChoice.Change); };

            var btnConfirm = new Button
            {
                Content = Lang.T("Download.Path.Confirm"),
                Style = SafeFindStyle("RoundedButton"),
                Width = 110,
                Height = 38
            };
            btnConfirm.Click += (s, e) => { CloseDialog(); tcs.TrySetResult(DownloadPathChoice.Confirm); };

            btnRow.Children.Add(btnCancel);
            btnRow.Children.Add(btnChange);
            btnRow.Children.Add(btnConfirm);
            Grid.SetRow(btnRow, 2);
            grid.Children.Add(btnRow);

            panel.Child = grid;
            var overlayGrid = new Grid();
            overlayGrid.Children.Add(panel);
            overlay.Child = overlayGrid;

            _rootGrid.Children.Add(overlay);
            Grid.SetRowSpan(overlay, int.MaxValue);
            Grid.SetColumnSpan(overlay, int.MaxValue);

            var fadeIn = new DoubleAnimation(0, 1, TimeSpan.FromMilliseconds(200));
            var scaleIn = new DoubleAnimation(0.8, 1.0, TimeSpan.FromMilliseconds(280))
            {
                EasingFunction = new BackEase { EasingMode = EasingMode.EaseOut, Amplitude = 0.3 }
            };
            overlay.BeginAnimation(OpacityProperty, fadeIn);
            scale.BeginAnimation(ScaleTransform.ScaleXProperty, scaleIn);
            scale.BeginAnimation(ScaleTransform.ScaleYProperty, scaleIn);

            return tcs.Task;
        }

        // ========== 设置页面 ==========
        private UIElement CreateSettingsPage()
        {
            var scrollViewer = new ScrollViewer { VerticalScrollBarVisibility = ScrollBarVisibility.Auto };
            var stack = new StackPanel { Margin = new Thickness(4, 4, 4, 12) };

            // 1. 游戏目录
            var dirGroup = new GroupBox { Header = Lang.T("Settings.GameDirs"), Margin = new Thickness(0, 0, 0, 18) };
            var dirListBox = new ListBox
            {
                Height = 140,
                Margin = new Thickness(0, 10, 0, 10),
                ItemContainerStyle = SafeFindStyle("CustomListBoxItemStyle")
            };
            foreach (var d in _config.Directories) dirListBox.Items.Add(d);
            dirListBox.SelectedIndex = _config.CurrentDirIndex;

            var dirBtnPanel = new StackPanel { Orientation = Orientation.Horizontal, Margin = new Thickness(0, 0, 0, 6) };
            var btnAdd = new Button { Content = Lang.T("Settings.AddDir"), Style = SafeFindStyle("RoundedButton"), Margin = new Thickness(0, 0, 8, 0) };
            btnAdd.Click += (s, e) => AddDirectory(dirListBox);
            var btnRemove = new Button { Content = Lang.T("Settings.RemoveDir"), Style = SafeFindStyle("RoundedButton"), Margin = new Thickness(0, 0, 8, 0) };
            btnRemove.Click += (s, e) => RemoveDirectory(dirListBox);
            var btnApply = new Button { Content = Lang.T("Settings.ApplyDir"), Style = SafeFindStyle("RoundedButton") };
            btnApply.Click += (s, e) => ApplyDirectory(dirListBox);
            dirBtnPanel.Children.Add(btnAdd);
            dirBtnPanel.Children.Add(btnRemove);
            dirBtnPanel.Children.Add(btnApply);

            var dirContentPanel = new StackPanel();
            dirContentPanel.Children.Add(dirListBox);
            dirContentPanel.Children.Add(dirBtnPanel);
            dirGroup.Content = dirContentPanel;

            // 2. 下载路径
            var dlGroup = new GroupBox { Header = Lang.T("Settings.DownloadPath"), Margin = new Thickness(0, 0, 0, 18) };
            var dlPanel = new StackPanel();
            var dlPathText = new TextBlock
            {
                Text = _config.DownloadPath,
                Foreground = SafeFindBrush("ForegroundBrush"),
                Margin = new Thickness(0, 0, 0, 10),
                TextTrimming = TextTrimming.CharacterEllipsis,
                FontSize = 12
            };
            var btnSetDlPath = new Button
            {
                Content = Lang.T("Settings.PickFolder"),
                Style = SafeFindStyle("RoundedButton"),
                Width = 130,
                Height = 34,
                HorizontalAlignment = HorizontalAlignment.Left
            };
            btnSetDlPath.Click += (s, e) =>
            {
                using (var dialog = new System.Windows.Forms.FolderBrowserDialog())
                {
                    dialog.Description = Lang.T("Download.Folder.Pick");
                    if (dialog.ShowDialog() == System.Windows.Forms.DialogResult.OK)
                    {
                        _config.DownloadPath = dialog.SelectedPath;
                        dlPathText.Text = _config.DownloadPath;
                        ConfigManager.Save(_config);
                    }
                }
            };
            dlPanel.Children.Add(dlPathText);
            dlPanel.Children.Add(btnSetDlPath);
            dlGroup.Content = dlPanel;

            // 2.5 自定义启动器背景（图片 / 视频）
            var bgGroup = new GroupBox { Header = Lang.T("Settings.Background"), Margin = new Thickness(0, 0, 0, 18) };
            var bgPanel = new StackPanel();
            bgPanel.Children.Add(new TextBlock
            {
                Text = GetBackgroundDescription(),
                Foreground = SafeFindBrush("ForegroundBrush"),
                FontSize = 12,
                Margin = new Thickness(0, 0, 0, 6),
                TextTrimming = TextTrimming.CharacterEllipsis,
            });
            bgPanel.Children.Add(new TextBlock
            {
                Text = Lang.T("Settings.Background.Desc"),
                Foreground = SafeFindBrush("TextTertiaryBrush"),
                FontSize = 11,
                TextWrapping = TextWrapping.Wrap,
                Margin = new Thickness(0, 0, 0, 10),
            });
            var bgBtnPanel = new StackPanel { Orientation = Orientation.Horizontal };
            var btnBgImage = new Button
            {
                Content = Lang.T("Settings.Background.Image"),
                Style = SafeFindStyle("RoundedButton"),
                Height = 34,
                Margin = new Thickness(0, 0, 10, 0),
            };
            btnBgImage.Click += (s, e) => PickBackgroundImage();
            var btnBgVideo = new Button
            {
                Content = Lang.T("Settings.Background.Video"),
                Style = SafeFindStyle("RoundedButton"),
                Height = 34,
                Margin = new Thickness(0, 0, 10, 0),
            };
            btnBgVideo.Click += (s, e) => PickBackgroundVideo();
            var btnBgReset = new Button
            {
                Content = Lang.T("Settings.Background.Reset"),
                Style = SafeFindStyle("RoundedButton"),
                Height = 34,
            };
            btnBgReset.Click += (s, e) => ResetCustomBackground();
            bgBtnPanel.Children.Add(btnBgImage);
            bgBtnPanel.Children.Add(btnBgVideo);
            bgBtnPanel.Children.Add(btnBgReset);
            bgPanel.Children.Add(bgBtnPanel);
            bgGroup.Content = bgPanel;

            // 3. 主题模式
            var themeGroup = new GroupBox { Header = Lang.T("Settings.Theme"), Margin = new Thickness(0, 0, 0, 18) };
            var themePanel = new StackPanel { Orientation = Orientation.Horizontal };
            var btnLight = new Button { Content = Lang.T("Settings.Theme.Light"), Style = SafeFindStyle("RoundedButton"), Width = 90, Margin = new Thickness(0, 0, 10, 0) };
            btnLight.Click += (s, e) => SetTheme("light");
            var btnDark = new Button { Content = Lang.T("Settings.Theme.Dark"), Style = SafeFindStyle("RoundedButton"), Width = 90 };
            btnDark.Click += (s, e) => SetTheme("dark");
            themePanel.Children.Add(btnLight);
            themePanel.Children.Add(btnDark);
            themeGroup.Content = themePanel;

            // 4. 语言（简体中文 / English (US) / Deutsch / Français / Русский）
            var langGroup = new GroupBox { Header = Lang.T("Settings.Language"), Margin = new Thickness(0, 0, 0, 18) };
            var langPanel = new WrapPanel();

            var btnChinese = new Button
            {
                Content = "简体中文",
                Style = SafeFindStyle("RoundedButton"),
                MinWidth = 110,
                Height = 34,
                Margin = new Thickness(0, 0, 10, 6)
            };
            btnChinese.Click += (s, e) => SwitchLanguage("zh-CN");

            var btnEnglish = new Button
            {
                Content = "English (United States)",
                Style = SafeFindStyle("RoundedButton"),
                MinWidth = 110,
                Height = 34,
                Margin = new Thickness(0, 0, 10, 6)
            };
            btnEnglish.Click += (s, e) => SwitchLanguage("en-US");

            var btnGerman = new Button
            {
                Content = "Deutsch (Deutschland)",
                Style = SafeFindStyle("RoundedButton"),
                MinWidth = 110,
                Height = 34,
                Margin = new Thickness(0, 0, 10, 6)
            };
            btnGerman.Click += (s, e) => SwitchLanguage("de-DE");

            var btnFrench = new Button
            {
                Content = "Français",
                Style = SafeFindStyle("RoundedButton"),
                MinWidth = 110,
                Height = 34,
                Margin = new Thickness(0, 0, 10, 6)
            };
            btnFrench.Click += (s, e) => SwitchLanguage("fr-FR");

            var btnRussian = new Button
            {
                Content = "Русский",
                Style = SafeFindStyle("RoundedButton"),
                MinWidth = 110,
                Height = 34,
                Margin = new Thickness(0, 0, 10, 6)
            };
            btnRussian.Click += (s, e) => SwitchLanguage("ru-RU");

            langPanel.Children.Add(btnChinese);
            langPanel.Children.Add(btnEnglish);
            langPanel.Children.Add(btnGerman);
            langPanel.Children.Add(btnFrench);
            langPanel.Children.Add(btnRussian);

            langGroup.Content = langPanel;

            // 5. 主题色
            var colorGroup = new GroupBox { Header = Lang.T("Settings.AccentColor"), Margin = new Thickness(0, 0, 0, 18) };
            var colorPanel = new WrapPanel();
            _accentSwatches.Clear();

            var presetColors = new Dictionary<string, string>
            {
                { "#0078d4", "Blue" }, { "#ff4343", "Red" }, { "#00cc6a", "Green" },
                { "#886ce4", "Purple" }, { "#ff763b", "Orange" }, { "#00b7c3", "Cyan" }
            };
            foreach (var kv in presetColors)
            {
                var border = new Border
                {
                    Width = 40,
                    Height = 40,
                    CornerRadius = new CornerRadius(10),
                    Background = (SolidColorBrush)new BrushConverter().ConvertFromString(kv.Key),
                    Margin = new Thickness(4, 4, 8, 4),
                    Cursor = Cursors.Hand,
                    Tag = kv.Key
                };
                border.Effect = new DropShadowEffect
                {
                    ShadowDepth = 2,
                    BlurRadius = 8,
                    Opacity = 0.35,
                    Color = (Color)ColorConverter.ConvertFromString(kv.Key)
                };

                border.MouseLeftButtonUp += (s, e) =>
                {
                    _config.AccentColor = kv.Key;
                    ApplyTheme();
                    RefreshAccentSwatches();
                };

                _accentSwatches.Add(border);
                colorPanel.Children.Add(border);
            }

            RefreshAccentSwatches();
            colorGroup.Content = colorPanel;

            // 6. 强调色应用到文字
            var applyCheck = new CheckBox
            {
                Content = Lang.T("Settings.ApplyText"),
                IsChecked = _config.ApplyText,
                Margin = new Thickness(4, 0, 0, 18)
            };
            applyCheck.Checked += (s, e) => { _config.ApplyText = true; ApplyTheme(); };
            applyCheck.Unchecked += (s, e) => { _config.ApplyText = false; ApplyTheme(); };

            // 7. 配置管理
            var configGroup = new GroupBox { Header = Lang.T("Settings.ConfigMgmt"), Margin = new Thickness(0, 0, 0, 18) };
            var configPanel = new StackPanel { Orientation = Orientation.Horizontal };
            var btnExport = new Button
            {
                Content = Lang.T("Settings.ExportConfig"),
                Style = SafeFindStyle("RoundedButton"),
                Width = 110,
                Margin = new Thickness(0, 0, 8, 0)
            };
            btnExport.Click += (s, e) =>
            {
                var sfd = new SaveFileDialog
                {
                    Filter = "JSON|*.json",
                    FileName = "launcher_config.json"
                };
                if (sfd.ShowDialog() == true)
                {
                    if (ConfigManager.ExportTo(sfd.FileName))
                        ShowNotification(Lang.T("Settings.ExportOk"));
                    else
                        ShowNotification(Lang.T("Settings.ExportFail"));
                }
            };

            var btnImport = new Button
            {
                Content = Lang.T("Settings.ImportConfig"),
                Style = SafeFindStyle("RoundedButton"),
                Width = 110,
                Margin = new Thickness(0, 0, 8, 0)
            };
            btnImport.Click += (s, e) =>
            {
                var ofd = new OpenFileDialog { Filter = "JSON|*.json" };
                if (ofd.ShowDialog() == true)
                {
                    try
                    {
                        string json;
                        using (var fs = new FileStream(ofd.FileName, FileMode.Open, FileAccess.Read, FileShare.ReadWrite))
                        using (var sr = new StreamReader(fs, Encoding.UTF8))
                        {
                            json = sr.ReadToEnd();
                        }

                        lock (typeof(ConfigManager))
                        {
                            using (var fs = new FileStream(ConfigManager.ConfigPath, FileMode.Create, FileAccess.Write, FileShare.Read, 4096))
                            using (var sw = new StreamWriter(fs, new UTF8Encoding(false)))
                            {
                                sw.Write(json);
                            }
                        }

                        _config = ConfigManager.Load();
                        ConfigManager.SetSyncFolder(_config.SyncFolder);
                        Lang.SetLanguage(_config.Language);
                        ThemeManager.ApplyTheme(_config);
                        ApplyTopBarTexts();
                        LoadDirectories();
                        SelectTab(0);
                        ShowNotification(Lang.T("Settings.ImportOk"));
                    }
                    catch (Exception ex)
                    {
                        ShowNotification(Lang.T("Settings.ImportFail", ex.Message));
                    }
                }
            };

            var btnSync = new Button
            {
                Content = Lang.T("Settings.SyncFolder"),
                Style = SafeFindStyle("RoundedButton"),
                Width = 130
            };
            btnSync.Click += (s, e) =>
            {
                using (var dialog = new System.Windows.Forms.FolderBrowserDialog())
                {
                    if (dialog.ShowDialog() == System.Windows.Forms.DialogResult.OK)
                    {
                        _config.SyncFolder = dialog.SelectedPath;
                        ConfigManager.SetSyncFolder(dialog.SelectedPath);
                        ConfigManager.Save(_config);
                        ShowNotification(Lang.T("Settings.SyncOk"));
                    }
                }
            };
            configPanel.Children.Add(btnExport);
            configPanel.Children.Add(btnImport);
            configPanel.Children.Add(btnSync);
            configGroup.Content = configPanel;

            // 8. 启动器更新
            var updateGroup = new GroupBox { Header = "启动器更新", Margin = new Thickness(0, 0, 0, 18) };
            var updatePanel = new StackPanel();

            var currentVersion = UpdateService.GetCurrentVersion();
            var updateInfoText = new TextBlock
            {
                Text = Lang.T("Update.CurrentVersion", currentVersion),
                Foreground = SafeFindBrush("SecondaryForegroundBrush"),
                Margin = new Thickness(0, 0, 0, 10),
                FontSize = 12
            };

            var updateStatusText = new TextBlock
            {
                Text = "",
                Foreground = SafeFindBrush("ForegroundBrush"),
                Margin = new Thickness(0, 6, 0, 0),
                FontSize = 12,
                TextWrapping = TextWrapping.Wrap
            };

            var updateProgressBar = new ProgressBar
            {
                Height = 16,
                Margin = new Thickness(0, 8, 0, 0),
                Visibility = Visibility.Collapsed,
                Maximum = 100
            };

            var updateBtnPanel = new StackPanel
            {
                Orientation = Orientation.Horizontal,
                HorizontalAlignment = HorizontalAlignment.Left
            };

            var btnCheckUpdate = new Button
            {
                Content = Lang.T("Update.Check"),
                Style = SafeFindStyle("RoundedButton"),
                Width = 120,
                Height = 34,
                Margin = new Thickness(0, 0, 8, 0)
            };

            var btnReleasePage = new Button
            {
                Content = Lang.T("Update.OpenRelease"),
                Style = SafeFindStyle("RoundedButton"),
                Width = 130,
                Height = 34
            };
            btnReleasePage.Click += (s, e) =>
            {
                try
                {
                    Process.Start(new ProcessStartInfo
                    {
                        FileName = UpdateService.GetReleasePageUrl(),
                        UseShellExecute = true
                    });
                }
                catch (Exception ex)
                {
                    ShowNotification(Lang.T("Detail.OpenFailed", ex.Message));
                }
            };

            btnCheckUpdate.Click += async (s, e) =>
            {
                btnCheckUpdate.IsEnabled = false;
                btnReleasePage.IsEnabled = false;
                updateStatusText.Text = Lang.T("Update.Checking");
                updateProgressBar.Visibility = Visibility.Collapsed;
                updateProgressBar.Value = 0;

                UpdateCheckResult update = null;
                try
                {
                    update = await UpdateService.CheckForUpdateAsync();
                }
                catch (Exception ex)
                {
                    updateStatusText.Text = Lang.T("Update.CheckFailed", ex.Message);
                    btnCheckUpdate.IsEnabled = true;
                    btnReleasePage.IsEnabled = true;
                    return;
                }

                if (update == null || !update.HasUpdate)
                {
                    updateStatusText.Text = Lang.T("Update.UpToDate", UpdateService.GetCurrentVersion());
                    btnCheckUpdate.IsEnabled = true;
                    btnReleasePage.IsEnabled = true;
                    return;
                }

                updateStatusText.Text = Lang.T("Update.Found", update.LatestVersion);

                // ★ 启动器强制更新：不提供"稍后/跳过"，直接下载并启动更新程序
                updateProgressBar.Visibility = Visibility.Visible;
                try
                {
                    await RunUpdateFromAutoCheckAsync(update);
                }
                finally
                {
                    btnCheckUpdate.IsEnabled = true;
                    btnReleasePage.IsEnabled = true;
                }
            };

            updateBtnPanel.Children.Add(btnCheckUpdate);
            updateBtnPanel.Children.Add(btnReleasePage);

            updatePanel.Children.Add(updateInfoText);
            updatePanel.Children.Add(updateBtnPanel);
            updatePanel.Children.Add(updateProgressBar);
            updatePanel.Children.Add(updateStatusText);
            updateGroup.Content = updatePanel;

            // 组装
            stack.Children.Add(dirGroup);
            stack.Children.Add(dlGroup);
            stack.Children.Add(bgGroup);
            stack.Children.Add(themeGroup);
            stack.Children.Add(langGroup);
            stack.Children.Add(colorGroup);
            stack.Children.Add(applyCheck);
            stack.Children.Add(configGroup);
            stack.Children.Add(updateGroup);

            scrollViewer.Content = stack;
            return scrollViewer;
        }

        private void AddDirectory(ListBox listBox)
        {
            using (var dialog = new System.Windows.Forms.FolderBrowserDialog())
            {
                dialog.Description = Lang.T("Settings.GameDirs");
                if (dialog.ShowDialog() == System.Windows.Forms.DialogResult.OK)
                {
                    string path = dialog.SelectedPath;
                    if (!_config.Directories.Contains(path))
                    {
                        _config.Directories.Add(path);
                        listBox.Items.Add(path);
                        ConfigManager.Save(_config);
                    }
                }
            }
        }

        private void RefreshAccentSwatches()
        {
            foreach (var b in _accentSwatches)
            {
                if ((b.Tag as string) == _config.AccentColor)
                {
                    b.BorderBrush = SafeFindBrush("ForegroundBrush");
                    b.BorderThickness = new Thickness(2);
                }
                else
                {
                    b.BorderBrush = null;
                    b.BorderThickness = new Thickness(0);
                }
            }
        }

        private void RemoveDirectory(ListBox listBox)
        {
            if (listBox.SelectedIndex >= 0 && _config.Directories.Count > 1)
            {
                int idx = listBox.SelectedIndex;
                _config.Directories.RemoveAt(idx);
                listBox.Items.RemoveAt(idx);
                if (_config.CurrentDirIndex >= _config.Directories.Count) _config.CurrentDirIndex = _config.Directories.Count - 1;
                ConfigManager.Save(_config);
                _ = ScanGamesAsync();
                if (_currentPathLabel != null && _config.CurrentDirIndex < _config.Directories.Count)
                    _currentPathLabel.Content = _config.Directories[_config.CurrentDirIndex];
            }
        }

        private void ApplyDirectory(ListBox listBox)
        {
            if (listBox.SelectedIndex >= 0 && listBox.SelectedIndex < _config.Directories.Count)
            {
                _config.CurrentDirIndex = listBox.SelectedIndex;
                ConfigManager.Save(_config);
                if (_currentPathLabel != null) _currentPathLabel.Content = _config.Directories[_config.CurrentDirIndex];
                _ = ScanGamesAsync();
            }
        }

        private async void SetTheme(string mode)
        {
            if (_config.ThemeMode == mode) return;

            _config.ThemeMode = mode;
            ApplyTheme();

            string message = mode == "dark"
                ? Lang.T("Theme.Restart.Dark")
                : Lang.T("Theme.Restart.Light");

            await ShowInfoDialogAsync(message);

            RestartLauncher();
        }

        private void ApplyTheme() { ThemeManager.ApplyTheme(_config); ConfigManager.Save(_config); }

        private static BitmapImage BitmapToImageSource(System.Drawing.Bitmap bitmap)
        {
            using (var ms = new MemoryStream())
            {
                bitmap.Save(ms, System.Drawing.Imaging.ImageFormat.Png);
                ms.Position = 0;
                var bi = new BitmapImage();
                bi.BeginInit();
                bi.StreamSource = ms;
                bi.CacheOption = BitmapCacheOption.OnLoad;
                bi.EndInit();
                bi.Freeze();
                return bi;
            }
        }

        // ========== 关于页面 ==========
        private UIElement CreateAboutPage()
        {
            var outer = new Grid();
            var panel = new StackPanel
            {
                MaxWidth = 560,
                HorizontalAlignment = HorizontalAlignment.Center,
                VerticalAlignment = VerticalAlignment.Center,
            };

            // 头像（圆角 20 + 软阴影，替代原来的硬阴影直角）
            try
            {
                var bmp = Properties.Resources.MMA1;
                var img = new Image
                {
                    Source = BitmapToImageSource(bmp),
                    Width = 156,
                    Height = 156,
                };
                var imgBorder = new Border
                {
                    CornerRadius = new CornerRadius(20),
                    ClipToBounds = true,
                    HorizontalAlignment = HorizontalAlignment.Center,
                    Margin = new Thickness(0, 0, 0, 18),
                    Effect = new DropShadowEffect { ShadowDepth = 4, BlurRadius = 24, Opacity = 0.16, Color = Colors.Black },
                };
                imgBorder.Child = img;
                panel.Children.Add(imgBorder);
            }
            catch { }

            panel.Children.Add(new TextBlock
            {
                Text = Lang.T("About.Title"),
                FontSize = 24,
                FontWeight = FontWeights.SemiBold,
                FontFamily = Ui.Font,
                Foreground = Ui.TextPrimary,
                HorizontalAlignment = HorizontalAlignment.Center,
            });

            var versionPill = Ui.Pill("v" + UpdateService.GetCurrentVersion().ToString());
            versionPill.HorizontalAlignment = HorizontalAlignment.Center;
            versionPill.Margin = new Thickness(0, 10, 0, 8);
            panel.Children.Add(versionPill);

            panel.Children.Add(new TextBlock
            {
                Text = Lang.T("About.Edition"),
                FontSize = 12,
                FontFamily = Ui.Font,
                Foreground = Ui.TextTertiary,
                HorizontalAlignment = HorizontalAlignment.Center,
                Margin = new Thickness(0, 0, 0, 24),
            });

            panel.Children.Add(new Border
            {
                Height = 1,
                Width = 120,
                Background = Ui.BorderSubtle,
                HorizontalAlignment = HorizontalAlignment.Center,
                Margin = new Thickness(0, 0, 0, 20),
            });

            panel.Children.Add(new TextBlock
            {
                Text = Lang.T("About.Author"),
                FontSize = 13,
                FontFamily = Ui.Font,
                Foreground = Ui.TextPrimary,
                HorizontalAlignment = HorizontalAlignment.Center,
            });
            panel.Children.Add(new TextBlock
            {
                Text = Lang.T("About.Copyright"),
                FontSize = 12,
                FontFamily = Ui.Font,
                Foreground = Ui.TextTertiary,
                HorizontalAlignment = HorizontalAlignment.Center,
                Margin = new Thickness(0, 4, 0, 0),
            });

            outer.Children.Add(panel);
            return outer;
        }

        private bool IsVersionCompatible(Version version)
        {
            if (version.Major == 9999 && version.Minor == 9999 && version.Build == 9999)
                return true;

            var v1 = new Version(2, 15, 4);
            var v2 = new Version(3, 0, 5);
            if (version >= v1 && version <= v2) return true;

            var v3 = new Version(2, 2, 0);
            var v4 = new Version(2, 4, 0);
            if (version >= v3 && version <= v4) return true;

            return false;
        }

        private void LoadDirectories()
        {
            if (_config.Directories == null || _config.Directories.Count == 0)
                _config.Directories = new List<string> { Directory.GetCurrentDirectory() };

            if (_config.CurrentDirIndex >= _config.Directories.Count)
                _config.CurrentDirIndex = 0;

            try
            {
                string downloadDir = _config.DownloadPath;
                if (!string.IsNullOrWhiteSpace(downloadDir)
                    && !_config.Directories.Any(d =>
                        string.Equals(d, downloadDir, StringComparison.OrdinalIgnoreCase)))
                {
                    _config.Directories.Add(downloadDir);
                    ConfigManager.Save(_config);
                }
            }
            catch { }
        }

        // ========== 自动更新（强制） ==========
        private async void StartAutoUpdateCheck()
        {
            if (_autoUpdateCheckRunning) return;
            _autoUpdateCheckRunning = true;

            try
            {
                await Task.Delay(TimeSpan.FromSeconds(4));

                // 游戏运行中不打断玩家，退出后再检查
                if (_currentGameProcess != null && !_currentGameProcess.HasExited) return;

                var update = await UpdateService.CheckForUpdateAsync();
                _config.LastUpdateCheck = DateTime.UtcNow;
                ConfigManager.Save(_config);

                if (update == null || !update.HasUpdate) return;

                // ★ 强制更新：不询问、不允许跳过/稍后，直接下载并启动更新程序
                ShowNotification(Lang.T("Update.ForcedFound", update.LatestVersion));
                await RunUpdateFromAutoCheckAsync(update);
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"自动检查更新失败: {ex.Message}");
            }
            finally
            {
                _autoUpdateCheckRunning = false;
            }
        }

        private async Task PromptAutoUpdateAsync(UpdateCheckResult update)
        {
            var dialog = new Border
            {
                Background = new SolidColorBrush(Color.FromArgb(0xA6, 0x12, 0x1A, 0x2B)),
                Visibility = Visibility.Collapsed,
                Opacity = 0,
                VerticalAlignment = VerticalAlignment.Stretch,
                HorizontalAlignment = HorizontalAlignment.Stretch
            };

            var panel = new Border
            {
                Width = 480,
                MaxHeight = 560,
                Background = SafeFindBrush("CardBackgroundBrush"),
                BorderBrush = SafeFindBrush("CardBorderBrush"),
                BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(22),
                Padding = new Thickness(26),
                HorizontalAlignment = HorizontalAlignment.Center,
                VerticalAlignment = VerticalAlignment.Center,
                RenderTransformOrigin = new Point(0.5, 0.5)
            };
            panel.Effect = new DropShadowEffect
            {
                ShadowDepth = 10,
                BlurRadius = 36,
                Opacity = 0.35,
                Color = Color.FromRgb(0x0F, 0x1B, 0x33)
            };
            var scale = new ScaleTransform(0.8, 0.8);
            panel.RenderTransform = scale;

            var grid = new Grid();
            grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });

            var title = new TextBlock
            {
                Text = Lang.T("AutoUpdate.Title"),
                FontSize = 18,
                FontWeight = FontWeights.Bold,
                Foreground = SafeFindBrush("ForegroundBrush")
            };
            Grid.SetRow(title, 0);
            grid.Children.Add(title);

            var versionLine = new TextBlock
            {
                Text = $"v{UpdateService.GetCurrentVersion()}  →  v{update.LatestVersion}",
                FontSize = 13,
                Foreground = SafeFindBrush("AccentBrush"),
                Margin = new Thickness(0, 8, 0, 12),
                FontWeight = FontWeights.SemiBold
            };
            Grid.SetRow(versionLine, 1);
            grid.Children.Add(versionLine);

            var notesScroll = new ScrollViewer
            {
                MaxHeight = 200,
                VerticalScrollBarVisibility = ScrollBarVisibility.Auto,
                Margin = new Thickness(0, 0, 0, 14)
            };
            var notesText = new TextBlock
            {
                Text = string.IsNullOrWhiteSpace(update.ReleaseNotes)
                    ? Lang.T("AutoUpdate.NoNotes")
                    : update.ReleaseNotes,
                TextWrapping = TextWrapping.Wrap,
                FontSize = 13,
                Foreground = SafeFindBrush("ForegroundBrush"),
                LineHeight = 20
            };
            notesScroll.Content = notesText;
            Grid.SetRow(notesScroll, 2);
            grid.Children.Add(notesScroll);

            if (update.FileSize > 0)
            {
                var sizeText = new TextBlock
                {
                    Text = Lang.T("AutoUpdate.SizeLabel", update.FileSize / 1048576.0),
                    FontSize = 12,
                    Foreground = SafeFindBrush("SecondaryForegroundBrush"),
                    Margin = new Thickness(0, 0, 0, 14)
                };
                Grid.SetRow(sizeText, 3);
                grid.Children.Add(sizeText);
            }

            var btnRow = new StackPanel
            {
                Orientation = Orientation.Horizontal,
                HorizontalAlignment = HorizontalAlignment.Right
            };

            var tcs = new TaskCompletionSource<string>();

            var btnLater = new Button
            {
                Content = Lang.T("AutoUpdate.Later"),
                Style = SafeFindStyle("RoundedButton"),
                Width = 100,
                Height = 36,
                Margin = new Thickness(0, 0, 8, 0)
            };
            btnLater.Click += (s, e) => { CloseDialog(); tcs.TrySetResult("later"); };

            var btnSkip = new Button
            {
                Content = Lang.T("AutoUpdate.Skip"),
                Style = SafeFindStyle("RoundedButton"),
                Width = 110,
                Height = 36,
                Margin = new Thickness(0, 0, 8, 0)
            };
            btnSkip.Click += (s, e) => { CloseDialog(); tcs.TrySetResult("skip"); };

            var btnUpdate = new Button
            {
                Content = Lang.T("AutoUpdate.Update"),
                Style = SafeFindStyle("RoundedButton"),
                Width = 100,
                Height = 36
            };
            btnUpdate.Click += (s, e) => { CloseDialog(); tcs.TrySetResult("update"); };

            btnRow.Children.Add(btnLater);
            btnRow.Children.Add(btnSkip);
            btnRow.Children.Add(btnUpdate);
            Grid.SetRow(btnRow, 4);
            grid.Children.Add(btnRow);

            panel.Child = grid;
            var overlayGrid = new Grid();
            overlayGrid.Children.Add(panel);
            dialog.Child = overlayGrid;

            _rootGrid.Children.Add(dialog);
            Grid.SetRowSpan(dialog, int.MaxValue);
            Grid.SetColumnSpan(dialog, int.MaxValue);

            dialog.Visibility = Visibility.Visible;
            var fadeIn = new DoubleAnimation(0, 1, TimeSpan.FromMilliseconds(220));
            var scaleIn = new DoubleAnimation(0.8, 1.0, TimeSpan.FromMilliseconds(300))
            {
                EasingFunction = new BackEase { EasingMode = EasingMode.EaseOut, Amplitude = 0.35 }
            };
            dialog.BeginAnimation(OpacityProperty, fadeIn);
            scale.BeginAnimation(ScaleTransform.ScaleXProperty, scaleIn);
            scale.BeginAnimation(ScaleTransform.ScaleYProperty, scaleIn);

            void CloseDialog()
            {
                var fadeOut = new DoubleAnimation(1, 0, TimeSpan.FromMilliseconds(180));
                fadeOut.Completed += (s, e) => _rootGrid.Children.Remove(dialog);
                var scaleOut = new DoubleAnimation(1.0, 0.85, TimeSpan.FromMilliseconds(180))
                {
                    EasingFunction = new QuadraticEase { EasingMode = EasingMode.EaseIn }
                };
                dialog.BeginAnimation(OpacityProperty, fadeOut);
                scale.BeginAnimation(ScaleTransform.ScaleXProperty, scaleOut);
                scale.BeginAnimation(ScaleTransform.ScaleYProperty, scaleOut);
            }

            string choice = await tcs.Task;

            if (choice == "skip")
            {
                _config.SkipUpdateVersion = update.LatestVersion;
                ConfigManager.Save(_config);
                ShowNotification(Lang.T("AutoUpdate.Skipped", update.LatestVersion));
                return;
            }

            if (choice == "later")
            {
                ShowNotification(Lang.T("AutoUpdate.LaterDone"));
                return;
            }

            _pendingAutoUpdate = update;
            await RunUpdateFromAutoCheckAsync(update);
        }

        private async Task RunUpdateFromAutoCheckAsync(UpdateCheckResult update)
        {
            if (string.IsNullOrEmpty(update.DownloadUrl))
            {
                ShowNotification(Lang.T("Update.NoDownloadUrl"));
                return;
            }

            try
            {
                ShowNotification(Lang.T("Update.Downloading"));

                var progress = new Progress<double>(p =>
                {
                    ShowNotification(Lang.T("Update.DownloadProgress", p));
                });

                string zipPath = await UpdateService.DownloadUpdateAsync(
                    update.DownloadUrl, progress, CancellationToken.None);

                if (!string.IsNullOrEmpty(update.Sha256))
                {
                    ShowNotification(Lang.T("Update.Verifying"));
                    bool ok = await Task.Run(() => UpdateService.VerifySha256(zipPath, update.Sha256));
                    if (!ok)
                    {
                        try { File.Delete(zipPath); } catch { }
                        ShowDetailPanel(Lang.T("AutoUpdate.Failed"), Lang.T("Update.VerifyFailed"));
                        return;
                    }
                }

                ShowNotification(Lang.T("Update.Launching"));
                await Task.Delay(600);

                UpdateService.LaunchUpdater(zipPath);
            }
            catch (Exception ex)
            {
                ShowDetailPanel(Lang.T("AutoUpdate.Failed"), Lang.T("AutoUpdate.FailedMsg", ex.Message));
            }
        }

        // ========== 窗口控制 ==========
        private void TitleBar_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            if (e.LeftButton == MouseButtonState.Pressed)
            {
                if (e.ClickCount == 2)
                {
                    WindowState = WindowState == WindowState.Maximized ? WindowState.Normal : WindowState.Maximized;
                    return;
                }
                DragMove();
            }
        }
        private void Minimize_Click(object sender, RoutedEventArgs e) => WindowState = WindowState.Minimized;
        private void Close_Click(object sender, RoutedEventArgs e) => Close();

        // ========== 下载详情弹窗（保留空实现避免编译错误） ==========
        private void EnsurePopupCreated() { }
        private void CloseDownloadDetailPopup() { }
    }
}
