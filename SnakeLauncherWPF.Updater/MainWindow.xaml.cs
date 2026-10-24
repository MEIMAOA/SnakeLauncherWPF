using System;
using System.ComponentModel;
using System.Diagnostics;
using System.Windows;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Animation;

namespace SnakeLauncherWPF.Updater
{
    public partial class MainWindow : Window
    {
        private readonly string _appDir;
        private readonly string _zipPath;
        private readonly string _exeName;
        private readonly string _tempDir;
        private UpdateEngine _engine;
        private bool _completed;

        public MainWindow(string[] args)
        {
            InitializeComponent();

            _appDir = GetArg(args, "--app-dir");
            _zipPath = GetArg(args, "--zip");
            _exeName = GetArg(args, "--exe") ?? "SnakeLauncherWPF.exe";
            _tempDir = GetArg(args, "--temp-dir");

            Loaded += OnLoaded;

            Opacity = 0;
            Loaded += (s, e) =>
            {
                var fade = new DoubleAnimation(0, 1, TimeSpan.FromMilliseconds(280));
                BeginAnimation(OpacityProperty, fade);
            };
        }

        private async void OnLoaded(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrWhiteSpace(_appDir))
            {
                ShowError("缺少参数: --app-dir");
                return;
            }
            if (string.IsNullOrWhiteSpace(_zipPath))
            {
                ShowError("缺少参数: --zip");
                return;
            }
            if (!System.IO.File.Exists(_zipPath))
            {
                ShowError($"更新包不存在:\n{_zipPath}");
                return;
            }
            if (!System.IO.Directory.Exists(_appDir))
            {
                ShowError($"应用目录不存在:\n{_appDir}");
                return;
            }

            await RunUpdateAsync();
        }

        private async System.Threading.Tasks.Task RunUpdateAsync()
        {
            BottomButtons.Visibility = Visibility.Collapsed;
            TxtError.Visibility = Visibility.Collapsed;
            TxtError.Text = "";
            TxtHint.Text = "更新期间请勿关闭此窗口";
            ProgressFill.Width = 0;
            TxtPercent.Text = "0%";

            // ★ 恢复进度条为强调色（首次启动或上次失败后重试）
            ProgressFill.SetResourceReference(BackgroundProperty, "ProgressFillBrush");

            _engine = new UpdateEngine();
            _engine.ProgressChanged += OnProgressChanged;

            bool success = false;
            string error = null;

            try
            {
                success = await System.Threading.Tasks.Task.Run(
                    () => _engine.Run(_appDir, _zipPath, _exeName));
                error = _engine.LastError;
            }
            catch (Exception ex)
            {
                error = ex.Message;
            }

            if (success)
            {
                _completed = true;
                ScheduleTempDirCleanup(_tempDir);
                await System.Threading.Tasks.Task.Delay(1200);
                Environment.Exit(0);
            }
            else
            {
                ShowError(error ?? "未知错误");
            }
        }

        private void OnProgressChanged(UpdateProgress p)
        {
            Dispatcher.Invoke(() =>
            {
                TxtStatus.Text = p.Message ?? "";

                if (p.Percentage >= 0)
                {
                    double trackWidth = ProgressTrack.ActualWidth;
                    if (trackWidth <= 0) trackWidth = 460;

                    double targetWidth = trackWidth * Math.Min(100, p.Percentage) / 100.0;
                    var anim = new DoubleAnimation(ProgressFill.Width, targetWidth,
                        TimeSpan.FromMilliseconds(220))
                    {
                        EasingFunction = new CubicEase { EasingMode = EasingMode.EaseOut }
                    };
                    ProgressFill.BeginAnimation(WidthProperty, anim);

                    TxtPercent.Text = $"{p.Percentage:F0}%";
                }
                else
                {
                    TxtPercent.Text = "处理中...";
                }
            });
        }

        /// <summary>
        /// 用一个独立的 cmd 脚本延迟删除临时目录（本进程退出后才能真正删除）
        /// </summary>
        private static void ScheduleTempDirCleanup(string tempDir)
        {
            if (string.IsNullOrWhiteSpace(tempDir)) return;
            if (!System.IO.Directory.Exists(tempDir)) return;

            try
            {
                string batPath = System.IO.Path.Combine(
                    System.IO.Path.GetTempPath(),
                    "cleanup_updater_" + Guid.NewGuid().ToString("N").Substring(0, 8) + ".bat");

                string script =
                    "@echo off\r\n" +
                    "ping 127.0.0.1 -n 3 > nul\r\n" +
                    $"rmdir /s /q \"{tempDir}\" 2>nul\r\n" +
                    $"del /f /q \"%~f0\" 2>nul\r\n";

                System.IO.File.WriteAllText(batPath, script, System.Text.Encoding.Default);

                var psi = new ProcessStartInfo
                {
                    FileName = "cmd.exe",
                    Arguments = $"/c \"{batPath}\"",
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    WindowStyle = ProcessWindowStyle.Hidden
                };
                Process.Start(psi);
            }
            catch { }
        }

        private void ShowError(string message)
        {
            Dispatcher.Invoke(() =>
            {
                TxtStatus.Text = "更新失败";
                TxtError.Text = message;
                TxtError.Visibility = Visibility.Visible;
                BottomButtons.Visibility = Visibility.Visible;
                TxtHint.Text = "更新未完成，可重试或关闭窗口";

                // ★ 进度条变红（深色/浅色都用同一个偏亮的红）
                ProgressFill.Background = new SolidColorBrush(Color.FromRgb(0xD1, 0x34, 0x38));
            });
        }

        private void Window_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            if (e.LeftButton == MouseButtonState.Pressed)
            {
                try { DragMove(); } catch { }
            }
        }

        private async void BtnRetry_Click(object sender, RoutedEventArgs e)
        {
            await RunUpdateAsync();
        }

        private void BtnClose_Click(object sender, RoutedEventArgs e)
        {
            _completed = true;
            Close();
        }

        protected override void OnClosing(CancelEventArgs e)
        {
            if (!_completed)
            {
                e.Cancel = true;
                return;
            }
            base.OnClosing(e);
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