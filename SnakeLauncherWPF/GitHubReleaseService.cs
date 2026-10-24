using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;

namespace SnakeLauncherWPF
{
    // ==================== 仓库配置 ====================
    public class GitHubRepoConfig
    {
        /// <summary>仓库所有者</summary>
        public string Owner { get; set; }

        /// <summary>仓库名</summary>
        public string Repo { get; set; }

        /// <summary>显示名称</summary>
        public string DisplayName { get; set; }

        /// <summary>是否为 Python 仓库（需要自动安装依赖）</summary>
        public bool IsPythonRepo { get; set; }

        /// <summary>游戏包 zip 文件名正则匹配</summary>
        public Regex GamePackagePattern { get; set; }

        /// <summary>提取版本号的正则分组索引（默认 1）</summary>
        public int VersionGroupIndex { get; set; } = 1;
    }

    // ==================== GitHub Release 模型 ====================
    public class GitHubRelease
    {
        public long Id { get; set; }
        public string TagName { get; set; }
        public string Name { get; set; }
        public string Body { get; set; }
        public bool Draft { get; set; }
        public bool Prerelease { get; set; }

        /// <summary>供 UI 直接读取的便捷属性</summary>
        public bool IsPrerelease => Prerelease;

        public DateTime PublishedAt { get; set; }

        /// <summary>GitHub 上该发行版的页面地址（用于"在 GitHub 查看"）。</summary>
        public string HtmlUrl { get; set; }

        public List<GitHubReleaseAsset> Assets { get; set; } = new List<GitHubReleaseAsset>();

        /// <summary>解析后的版本号（去掉 v 前缀）</summary>
        public Version ParsedVersion { get; set; }

        /// <summary>所属仓库配置</summary>
        public GitHubRepoConfig RepoConfig { get; set; }
    }

    public class GitHubReleaseAsset
    {
        public string Name { get; set; }
        public string BrowserDownloadUrl { get; set; }

        /// <summary>压缩包对应架构：x64 / x86 / arm64 / any（由文件名识别）。</summary>
        public string Architecture { get; set; } = "any";

        /// <summary>目标平台：windows / android / any（由文件名后缀识别）。</summary>
        public string Platform { get; set; } = "windows";
        public long Size { get; set; }
        public string ContentType { get; set; }
        public int DownloadCount { get; set; }

        /// <summary>从文件名解析出的版本号，用于标识游戏包</summary>
        public Version ParsedVersion { get; set; }

        /// <summary>是否符合命名规范（游戏包）</summary>
        public bool IsGamePackage { get; set; }

        /// <summary>所属仓库配置</summary>
        public GitHubRepoConfig RepoConfig { get; set; }
    }

    // ==================== 原始 JSON 模型（匹配 GitHub API 返回结构） ====================
    internal class RawGitHubRelease
    {
        public long id { get; set; }
        public string tag_name { get; set; }
        public string name { get; set; }
        public string body { get; set; }
        public bool draft { get; set; }
        public bool prerelease { get; set; }
        public DateTime published_at { get; set; }
        public string html_url { get; set; }
        public List<RawGitHubAsset> assets { get; set; }
    }

    internal class RawGitHubAsset
    {
        public string name { get; set; }
        public string browser_download_url { get; set; }
        public long size { get; set; }
        public string content_type { get; set; }
        public int download_count { get; set; }
    }

    // ==================== 服务 ====================
    public static class GitHubReleaseService
    {
        // ============================================================
        // ★ 仓库列表配置
        // ============================================================
        public static readonly List<GitHubRepoConfig> Repos = new List<GitHubRepoConfig>
        {
            // 仓库 1：SnakeGame（C# / Unity 版）
            new GitHubRepoConfig
            {
                Owner = "MEIMAOA",
                Repo = "SnakeGame",
                DisplayName = "SnakeGame（C# / Unity）",
                IsPythonRepo = false,
                GamePackagePattern = new Regex(
                    @"^SnakeGame(?:Wpf|Launcher)?[-_ ]?v?(\d+(?:\.\d+){0,3})(?:[-_ ]?(?:beta|alpha|rc|preview|pre)[-_ ]?\d*)?(?:[-_ ]?(?:Windows[-_ ]?(?:32|64|86|arm64|x86|x64)|Win(?:32|64)|x86|x64|arm64|Android))?\.(?:zip|apk)$",
                    RegexOptions.IgnoreCase | RegexOptions.Compiled),
                VersionGroupIndex = 1
            },

            // 仓库 2：Snake-Game-Python-Edition-（Python 游戏）
            new GitHubRepoConfig
            {
                Owner = "MEIMAOA",
                Repo = "Snake-Game-Python-Edition-",
                DisplayName = "贪吃蛇 Python 版",
                IsPythonRepo = true,
                GamePackagePattern = new Regex(
                    @"^SnakeGamePython_(\d+(?:\.\d+){1,3})\.zip$",
                    RegexOptions.IgnoreCase | RegexOptions.Compiled),
                VersionGroupIndex = 1
            }
        };

        private static readonly HttpClient _http = CreateHttpClient();

        // ============================================================
        //  ★ 发行版压缩包命名兼容层
        //  已支持的历史/现有命名：
        //    SnakeGameWpf_8.0.0.0.zip          （旧 WPF 版）
        //    SnakeGameWpf_7.0.0.0.zip
        //    SnakeGame-v9.0.0-Windows64.zip    （v9.0.0 正式版，64 位）
        //    SnakeGame-v9.0.0-Windows32.zip    （v9.0.0 正式版，32 位）
        //    SnakeGame_1.1.0.zip / SnakeGame-9.0.0.zip
        // ============================================================

        /// <summary>从文件名识别目标平台（apk / Android → android，其余 → windows）。</summary>
        public static string DetectPlatform(string fileName)
        {
            if (string.IsNullOrWhiteSpace(fileName)) return "windows";
            string n = fileName.ToLowerInvariant();
            if (n.EndsWith(".apk") || n.Contains("android")) return "android";
            return "windows";
        }

        /// <summary>从文件名识别目标架构。</summary>
        public static string DetectArchitecture(string fileName)
        {
            if (string.IsNullOrWhiteSpace(fileName)) return "any";
            string n = fileName.ToLowerInvariant();
            if (n.Contains("arm64") || n.Contains("aarch64")) return "arm64";
            if (n.Contains("windows32") || n.Contains("win32") || n.Contains("x86") || n.Contains("-32") || n.Contains("_32") || n.Contains("32bit"))
                return "x86";
            if (n.Contains("windows64") || n.Contains("win64") || n.Contains("x64") || n.Contains("-64") || n.Contains("_64") || n.Contains("64bit"))
                return "x64";
            return "any";
        }

        /// <summary>
        /// 从一次 Release 的所有资产里挑出"最适合当前系统"的游戏包：
        /// 优先本机架构（64 位系统优先 Windows64；ARM64 系统优先原生 ARM64、其次 x64、最后 x86），
        /// 同架构内按版本号从高到低。
        /// </summary>
        public static GitHubReleaseAsset PickBestAsset(IEnumerable<GitHubReleaseAsset> assets, string osArch = null, string platform = "windows")
        {
            if (assets == null) return null;
            var list = assets.Where(a => a != null && a.IsGamePackage);
            if (!string.IsNullOrEmpty(platform))
            {
                list = list.Where(a => string.IsNullOrEmpty(a.Platform) ||
                                       string.Equals(a.Platform, platform, StringComparison.OrdinalIgnoreCase));
            }
            var candidates = list.ToList();
            if (candidates.Count == 0) return null;

            string prefer = osArch;
            if (string.IsNullOrEmpty(prefer))
            {
                var pa = System.Runtime.InteropServices.RuntimeInformation.ProcessArchitecture;
                prefer = pa == System.Runtime.InteropServices.Architecture.Arm64
                    ? "arm64"
                    : (Environment.Is64BitOperatingSystem ? "x64" : "x86");
            }

            int Score(GitHubReleaseAsset a)
            {
                string arch = string.IsNullOrEmpty(a.Architecture) ? "any" : a.Architecture;
                if (arch == prefer) return 100;
                if (arch == "any") return 50;
                if (prefer == "x64" && arch == "x86") return 20;     // 64 位系统可跑 32 位包
                if (prefer == "arm64" && arch == "x64") return 30;   // ARM64 可仿真跑 x64
                if (prefer == "arm64" && arch == "x86") return 10;
                if (prefer == "x86" && arch == "x64") return 5;
                return 0;
            }

            return candidates
                .OrderByDescending(Score)
                .ThenByDescending(a => a.ParsedVersion ?? new Version(0, 0, 0, 0))
                .FirstOrDefault();
        }

        private static HttpClient CreateHttpClient()
        {
            var handler = new HttpClientHandler
            {
                AllowAutoRedirect = true,
                AutomaticDecompression = System.Net.DecompressionMethods.GZip | System.Net.DecompressionMethods.Deflate
            };
            var client = new HttpClient(handler) { Timeout = TimeSpan.FromSeconds(30) };
            client.DefaultRequestHeaders.UserAgent.ParseAdd("SnakeLauncherWPF-Downloader/1.0");
            client.DefaultRequestHeaders.Accept.ParseAdd("application/vnd.github.v3+json");
            return client;
        }

        /// <summary>
        /// 获取指定仓库的所有 Release（含预发布，不含草稿）
        /// 按版本号降序排列
        /// </summary>
        public static async Task<List<GitHubRelease>> GetReleasesAsync(
            GitHubRepoConfig repoConfig,
            CancellationToken ct = default)
        {
            if (repoConfig == null)
                throw new ArgumentNullException(nameof(repoConfig));

            string url = $"https://api.github.com/repos/{repoConfig.Owner}/{repoConfig.Repo}/releases?per_page=100";

            using (var response = await _http.GetAsync(url, ct).ConfigureAwait(false))
            {
                response.EnsureSuccessStatusCode();
                string json = await response.Content.ReadAsStringAsync().ConfigureAwait(false);

                var rawList = JsonSerializer.Deserialize<List<RawGitHubRelease>>(json,
                    new JsonSerializerOptions { PropertyNameCaseInsensitive = true });

                if (rawList == null) return new List<GitHubRelease>();

                var result = new List<GitHubRelease>();

                foreach (var raw in rawList)
                {
                    // ★ 只过滤草稿；预发布保留，并在 UI 上打标
                    if (raw.draft) continue;

                    var release = new GitHubRelease
                    {
                        Id = raw.id,
                        TagName = raw.tag_name,
                        Name = string.IsNullOrWhiteSpace(raw.name) ? raw.tag_name : raw.name,
                        Body = raw.body ?? "",
                        Draft = raw.draft,
                        Prerelease = raw.prerelease,
                        PublishedAt = raw.published_at,
                        HtmlUrl = raw.html_url,
                        ParsedVersion = ParseTagVersion(raw.tag_name),
                        RepoConfig = repoConfig
                    };

                    if (raw.assets != null)
                    {
                        foreach (var a in raw.assets)
                        {
                            var asset = new GitHubReleaseAsset
                            {
                                Name = a.name,
                                BrowserDownloadUrl = a.browser_download_url,
                                Size = a.size,
                                ContentType = a.content_type,
                                DownloadCount = a.download_count,
                                RepoConfig = repoConfig
                            };

                            // 用仓库配置的正则匹配游戏包
                            asset.Architecture = DetectArchitecture(a.name);
                            asset.Platform = DetectPlatform(a.name);
                            var pkgVersion = ParseAssetVersion(a.name,
                                repoConfig.GamePackagePattern,
                                repoConfig.VersionGroupIndex);

                            asset.ParsedVersion = pkgVersion;
                            asset.IsGamePackage = pkgVersion != null;

                            release.Assets.Add(asset);
                        }
                    }

                    result.Add(release);
                }

                return result
                    .OrderByDescending(r => r.ParsedVersion ?? new Version(0, 0, 0, 0))
                    .ThenByDescending(r => r.PublishedAt)
                    .ToList();
            }
        }

        /// <summary>
        /// 兼容旧调用：无参数时使用第一个仓库
        /// </summary>
        public static Task<List<GitHubRelease>> GetReleasesAsync(CancellationToken ct = default)
        {
            if (Repos == null || Repos.Count == 0)
                return Task.FromResult(new List<GitHubRelease>());
            return GetReleasesAsync(Repos[0], ct);
        }

        /// <summary>
        /// 用指定正则从文件名解析版本号
        /// </summary>
        public static Version ParseAssetVersion(string fileName, Regex pattern, int groupIndex = 1)
        {
            if (string.IsNullOrWhiteSpace(fileName)) return null;
            if (pattern == null) return null;

            var m = pattern.Match(fileName.Trim());
            if (!m.Success) return null;

            string verStr = m.Groups[groupIndex].Value;
            return ParseVersionString(verStr);
        }

        /// <summary>
        /// 解析 tag 名称为版本号（支持 v7.0.0.0 / v7.0.0 / v7.0）
        /// </summary>
        public static Version ParseTagVersion(string tag)
        {
            if (string.IsNullOrWhiteSpace(tag)) return null;
            string clean = tag.Trim().TrimStart('v', 'V');
            return ParseVersionString(clean);
        }

        /// <summary>
        /// 内部：解析任意版本字符串，补齐为四段
        /// </summary>
        private static Version ParseVersionString(string s)
        {
            if (string.IsNullOrWhiteSpace(s)) return null;

            // 提取开头的 x.x.x.x 部分（忽略可能的 -beta 等后缀）
            var m = Regex.Match(s.Trim(), @"^(\d+(?:\.\d+){0,3})");
            if (!m.Success) return null;

            if (!Version.TryParse(m.Groups[1].Value, out var v)) return null;

            int major = v.Major;
            int minor = v.Minor >= 0 ? v.Minor : 0;
            int build = v.Build >= 0 ? v.Build : 0;
            int revision = v.Revision >= 0 ? v.Revision : 0;
            return new Version(major, minor, build, revision);
        }

        /// <summary>
        /// 从 Release Body 中提取 SHA256（可选约定：&lt;!-- SHA256:xxx --&gt;）
        /// </summary>
        public static string ExtractSha256(string body)
        {
            if (string.IsNullOrWhiteSpace(body)) return null;
            var m = Regex.Match(body,
                @"<!--\s*SHA256\s*:\s*([a-fA-F0-9]{64})\s*-->",
                RegexOptions.IgnoreCase);
            return m.Success ? m.Groups[1].Value.ToLowerInvariant() : null;
        }
        // ==================== 仓库文件模型 ====================
        public class GitHubRepoFile
        {
            public string Name { get; set; }
            public string Path { get; set; }
            public string DownloadUrl { get; set; }
            public long Size { get; set; }
        }

        // ==================== 原始 JSON 模型 ====================
        internal class RawGitHubContent
        {
            public string name { get; set; }
            public string path { get; set; }
            public string type { get; set; }        // "file" / "dir" / "symlink" / "submodule"
            public string download_url { get; set; }
            public long size { get; set; }
        }
        /// <summary>
        /// 获取仓库根目录下所有 .md 文件列表
        /// </summary>
        public static async Task<List<GitHubRepoFile>> GetRepoMarkdownFilesAsync(
            GitHubRepoConfig repoConfig,
            CancellationToken ct = default)
        {
            if (repoConfig == null)
                throw new ArgumentNullException(nameof(repoConfig));

            string url = $"https://api.github.com/repos/{repoConfig.Owner}/{repoConfig.Repo}/contents/";

            using (var response = await _http.GetAsync(url, ct).ConfigureAwait(false))
            {
                response.EnsureSuccessStatusCode();
                string json = await response.Content.ReadAsStringAsync().ConfigureAwait(false);

                var rawList = JsonSerializer.Deserialize<List<RawGitHubContent>>(json,
                    new JsonSerializerOptions { PropertyNameCaseInsensitive = true });

                if (rawList == null) return new List<GitHubRepoFile>();

                return rawList
                    .Where(f => f.type == "file"
                             && !string.IsNullOrEmpty(f.name)
                             && f.name.EndsWith(".md", StringComparison.OrdinalIgnoreCase))
                    .Select(f => new GitHubRepoFile
                    {
                        Name = f.name,
                        Path = f.path,
                        DownloadUrl = f.download_url,
                        Size = f.size
                    })
                    .OrderBy(f => GetMdSortPriority(f.Name))
                    .ThenBy(f => f.Name, StringComparer.OrdinalIgnoreCase)
                    .ToList();
            }
        }

        /// <summary>
        /// README 优先排在前面
        /// </summary>
        private static int GetMdSortPriority(string name)
        {
            string lower = (name ?? "").ToLowerInvariant();
            if (lower == "readme.md") return 0;
            if (lower.StartsWith("readme")) return 1;
            if (lower.Contains("changelog")) return 2;
            if (lower.Contains("license")) return 3;
            return 10;
        }

        /// <summary>
        /// 下载文件文本内容（用于 .md 预览）
        /// </summary>
        public static async Task<string> GetFileTextAsync(string rawUrl, CancellationToken ct = default)
        {
            if (string.IsNullOrWhiteSpace(rawUrl)) return "";
            try
            {
                using (var response = await _http.GetAsync(rawUrl, ct).ConfigureAwait(false))
                {
                    response.EnsureSuccessStatusCode();
                    return await response.Content.ReadAsStringAsync().ConfigureAwait(false);
                }
            }
            catch (Exception ex)
            {
                return $"（无法加载内容: {ex.Message}）";
            }
        }
    }
}