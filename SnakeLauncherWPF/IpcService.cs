using System;
using System.IO;
using System.IO.Pipes;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Windows;

namespace SnakeLauncherWPF
{
    public class GameStatsData
    {
        public int Fps { get; set; } = 0;
        public int Score { get; set; } = 0;
        public int Kills { get; set; } = 0;
        public string Mode { get; set; } = "";
    }

    public static class IpcService
    {
        private static NamedPipeServerStream _server;
        private static StreamReader _reader;
        private static CancellationTokenSource _cts;

        public static event Action<GameStatsData> StatsReceived;
        public static event Action Disconnected;

        // ★ 新增：检测到作弊时触发
        public static event Action<string> CheatDetected;

        // ★ 新增：会话追踪器（用于检测分数/击杀异常增长）
        public static GameSessionTracker SessionTracker { get; } = new GameSessionTracker();

        public static bool IsConnected => _server?.IsConnected ?? false;

        /// <summary>
        /// 启动命名管道服务器（带自动重试，解决"管道正在使用"和"无法访问关闭的管道"问题）
        /// </summary>
        public static async Task StartAsync()
        {
            // ★ 每次启动会话重置追踪器
            SessionTracker.Reset();

            int retryCount = 3;
            for (int i = 0; i < retryCount; i++)
            {
                try
                {
                    Stop();

                    _server = new NamedPipeServerStream(
                        "SnakeGameFPSPipe",
                        PipeDirection.In,
                        maxNumberOfServerInstances: 1,
                        PipeTransmissionMode.Byte,
                        PipeOptions.Asynchronous
                    );

                    await _server.WaitForConnectionAsync();
                    break;
                }
                catch (IOException ex) when (ex.Message.Contains("正在使用"))
                {
                    await Task.Delay(1000 * (i + 1));
                }
                catch (Exception ex) when (ex is ObjectDisposedException || ex.Message.Contains("关闭"))
                {
                    Stop();
                    await Task.Delay(500);
                }
                catch (Exception ex)
                {
                    Stop();
                    MessageBox.Show($"IPC 服务启动失败: {ex.Message}", "通信错误");
                    return;
                }
            }

            if (_server == null || !_server.IsConnected)
            {
                Stop();
                return;
            }

            _reader = new StreamReader(_server, Encoding.UTF8);
            _cts = new CancellationTokenSource();

            _ = Task.Run(async () =>
            {
                try
                {
                    while (_server.IsConnected && !_cts.Token.IsCancellationRequested)
                    {
                        string line;
                        try
                        {
                            line = await _reader.ReadLineAsync();
                        }
                        catch (IOException) { break; }
                        catch (ObjectDisposedException) { break; }
                        catch (InvalidOperationException) { break; }

                        if (line == null) break;

                        // ============================================================
                        // ★ 反作弊：先校验签名与时间戳
                        // ============================================================
                        if (!AntiCheat.VerifyIpcLine(line, out string cleanPayload, out string reason))
                        {
                            string capturedReason = reason;
                            Application.Current?.Dispatcher?.Invoke(() =>
                            {
                                try { CheatDetected?.Invoke(capturedReason); } catch { }
                            });
                            continue;
                        }

                        var stats = ParseLine(cleanPayload);

                        // ★ 追踪数据合理性
                        long ts = ExtractTimestamp(cleanPayload);
                        SessionTracker.Feed(ts, stats.Score, stats.Kills);
                        if (SessionTracker.IsSuspicious)
                        {
                            string why = SessionTracker.SuspiciousReason;
                            Application.Current?.Dispatcher?.Invoke(() =>
                            {
                                try { CheatDetected?.Invoke(why); } catch { }
                            });
                        }

                        Application.Current.Dispatcher.Invoke(() => StatsReceived?.Invoke(stats));
                    }
                }
                catch { }
                finally
                {
                    Stop();
                    Application.Current?.Dispatcher?.Invoke(() => Disconnected?.Invoke());
                }
            });
        }

        private static GameStatsData ParseLine(string line)
        {
            var data = new GameStatsData();
            var parts = line.Split(',');
            foreach (var part in parts)
            {
                var kv = part.Split(':');
                if (kv.Length == 2)
                {
                    switch (kv[0].ToUpper())
                    {
                        case "FPS":
                            if (int.TryParse(kv[1], out int fps)) data.Fps = fps;
                            break;
                        case "SCORE":
                            if (int.TryParse(kv[1], out int score)) data.Score = score;
                            break;
                        case "KILLS":
                            if (int.TryParse(kv[1], out int kills)) data.Kills = kills;
                            break;
                        case "MODE":
                            data.Mode = kv[1];
                            break;
                    }
                }
            }
            return data;
        }

        /// <summary>
        /// ★ 从 payload 中提取时间戳
        /// </summary>
        private static long ExtractTimestamp(string payload)
        {
            if (string.IsNullOrEmpty(payload)) return 0;
            int idx = payload.LastIndexOf(",TS:", StringComparison.OrdinalIgnoreCase);
            if (idx < 0) return 0;
            if (!long.TryParse(payload.Substring(idx + 4), out long ts)) return 0;
            return ts;
        }

        /// <summary>
        /// 停止管道并释放所有资源
        /// </summary>
        public static void Stop()
        {
            _cts?.Cancel();
            try { _reader?.Dispose(); } catch { }

            try
            {
                if (_server != null)
                {
                    if (_server.IsConnected)
                    {
                        try { _server.Disconnect(); } catch { }
                    }
                    _server.Dispose();
                }
            }
            catch { }
            finally
            {
                _reader = null;
                _server = null;
                _cts?.Dispose();
                _cts = null;
            }
        }
    }
}