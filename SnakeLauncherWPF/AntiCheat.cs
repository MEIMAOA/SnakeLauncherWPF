using System;
using System.Collections.Generic;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace SnakeLauncherWPF
{
    public static class AntiCheat
    {
        // ★ 必须和游戏端 SimpleIpcClient.RootKey 完全一致
        private static readonly byte[] RootKey = new byte[32]
        {
            0xA3, 0x71, 0x0F, 0xC5, 0x2D, 0x88, 0xE6, 0x14,
            0x59, 0xBB, 0x93, 0x27, 0xF0, 0x44, 0x6A, 0xD8,
            0x1C, 0xE2, 0x75, 0x38, 0xAF, 0x06, 0x5B, 0x90,
            0x8D, 0x33, 0x4F, 0xCA, 0x11, 0x7E, 0x62, 0xB5
        };

        private const long TimestampToleranceSeconds = 30;

        private static Dictionary<string, string> _allowedHashes;

        /// <summary>启动时加载 game_hashes.json（位于启动器根目录）</summary>
        public static void LoadAllowedHashes()
        {
            _allowedHashes = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            try
            {
                string path = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "game_hashes.json");
                if (!File.Exists(path)) return;

                var json = File.ReadAllText(path);
                using (var doc = JsonDocument.Parse(json))
                {
                    if (doc.RootElement.ValueKind != JsonValueKind.Object) return;
                    foreach (var p in doc.RootElement.EnumerateObject())
                        _allowedHashes[p.Name] = p.Value.GetString();
                }
            }
            catch { }
        }

        /// <summary>
        /// 校验游戏 exe 文件哈希。返回 null 表示通过，否则返回错误描述。
        /// 只校验白名单里有的文件名；不在白名单里的游戏不阻止。
        /// </summary>
        public static string VerifyGameExe(string exePath)
        {
            if (string.IsNullOrEmpty(exePath) || !File.Exists(exePath))
                return null;

            if (_allowedHashes == null || _allowedHashes.Count == 0)
                return null;

            string fileName = Path.GetFileName(exePath);
            if (!_allowedHashes.TryGetValue(fileName, out var expected))
                return null;

            string actual = ComputeFileSha256(exePath);
            if (string.IsNullOrEmpty(actual))
                return "无法计算游戏文件哈希";

            if (!string.Equals(actual, expected, StringComparison.OrdinalIgnoreCase))
                return $"游戏文件已被修改\n" +
                       $"预期: {expected.Substring(0, 16)}…\n" +
                       $"实际: {actual.Substring(0, 16)}…";

            return null;
        }

        /// <summary>验证一行 IPC 消息的签名与时间戳。通过返回 true，并输出剥离签名的干净 payload。</summary>
        public static bool VerifyIpcLine(string line, out string cleanPayload, out string errorReason)
        {
            cleanPayload = null;
            errorReason = null;

            if (string.IsNullOrEmpty(line)) { errorReason = "空消息"; return false; }

            int sigIdx = line.LastIndexOf(",SIG:", StringComparison.OrdinalIgnoreCase);
            if (sigIdx < 0) { errorReason = "缺少签名"; return false; }

            string payload = line.Substring(0, sigIdx);
            string providedSig = line.Substring(sigIdx + 5).Trim();

            int tsIdx = payload.LastIndexOf(",TS:", StringComparison.OrdinalIgnoreCase);
            if (tsIdx < 0) { errorReason = "缺少时间戳"; return false; }

            string tsStr = payload.Substring(tsIdx + 4);
            if (!long.TryParse(tsStr, out long ts)) { errorReason = "时间戳非法"; return false; }

            long now = DateTimeOffset.UtcNow.ToUnixTimeSeconds();
            if (Math.Abs(now - ts) > TimestampToleranceSeconds)
            {
                errorReason = "时间戳过期（可能重放）";
                return false;
            }

            string expectedSig = ComputeHmac(payload);
            if (!string.Equals(expectedSig, providedSig, StringComparison.OrdinalIgnoreCase))
            {
                errorReason = "签名不匹配";
                return false;
            }

            cleanPayload = payload.Substring(0, tsIdx);
            return true;
        }

        private static string ComputeHmac(string payload)
        {
            using (var h = new HMACSHA256(RootKey))
            {
                byte[] mac = h.ComputeHash(Encoding.UTF8.GetBytes(payload));
                var sb = new StringBuilder(mac.Length * 2);
                foreach (var b in mac) sb.Append(b.ToString("x2"));
                return sb.ToString();
            }
        }

        private static string ComputeFileSha256(string path)
        {
            try
            {
                using (var fs = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite))
                using (var sha = SHA256.Create())
                {
                    byte[] hash = sha.ComputeHash(fs);
                    var sb = new StringBuilder(hash.Length * 2);
                    foreach (var b in hash) sb.Append(b.ToString("x2"));
                    return sb.ToString();
                }
            }
            catch { return null; }
        }
    }

    /// <summary>追踪游戏会话数据合理性</summary>
    public class GameSessionTracker
    {
        private long _lastTs;
        private int _lastScore;
        private int _lastKills;

        private const double MaxScoreRatePerSecond = 800.0;   // 分数每秒最大增长
        private const double MaxKillRatePerSecond = 8.0;      // 击杀每秒最大增长

        public bool IsSuspicious { get; private set; }
        public string SuspiciousReason { get; private set; }

        public void Reset()
        {
            _lastTs = 0; _lastScore = 0; _lastKills = 0;
            IsSuspicious = false; SuspiciousReason = null;
        }

        public void Feed(long ts, int score, int kills)
        {
            if (_lastTs > 0 && ts > _lastTs)
            {
                double dt = ts - _lastTs;
                if (dt > 0)
                {
                    double scoreRate = (score - _lastScore) / dt;
                    double killRate = (kills - _lastKills) / dt;

                    if (scoreRate > MaxScoreRatePerSecond)
                    {
                        IsSuspicious = true;
                        SuspiciousReason = $"分数增速异常 ({scoreRate:F0}/秒)";
                    }
                    else if (killRate > MaxKillRatePerSecond)
                    {
                        IsSuspicious = true;
                        SuspiciousReason = $"击杀增速异常 ({killRate:F1}/秒)";
                    }
                }
            }
            _lastTs = ts; _lastScore = score; _lastKills = kills;
        }
    }
}