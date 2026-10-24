using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;

namespace SnakeLauncherWPF
{
    /// <summary>
    /// 设计系统运行时辅助（Emil Kowalski design-eng 规范落地）：
    /// <list type="bullet">
    /// <item>统一字体（Segoe UI Variable / 回退 Segoe UI / 微软雅黑）</item>
    /// <item>把旧版硬编码的纯灰/纯黑文字映射到 Token：
    ///       近黑 → TextPrimary、中灰 → TextSecondary、浅灰 → TextTertiary</item>
    /// <item>把硬灰边框替换为半透明 BorderSubtle，消除"网页 2005 灰线"观感</item>
    /// <item>代码动态生成的页面在挂载后调用 <see cref="NormalizePage"/> 即可整体归一</item>
    /// </list>
    /// 只做"颜色/字体/描边"级别归一，不改变布局与交互，避免破坏既有功能。
    /// </summary>
    internal static class Ui
    {
        private static ResourceDictionary R => Application.Current?.Resources ?? new ResourceDictionary();

        private static T Get<T>(string key) where T : class => (R[key] as T);

        public static Brush Brush(string key) => Get<Brush>(key) ?? Brushes.Transparent;
        public static Brush TextPrimary => Brush("TextPrimaryBrush");
        public static Brush TextSecondary => Brush("TextSecondaryBrush");
        public static Brush TextTertiary => Brush("TextTertiaryBrush");
        public static Brush Surface => Brush("SurfaceBrush");
        public static Brush SurfaceHover => Brush("SurfaceHoverBrush");
        public static Brush SurfaceSunken => Brush("SurfaceSunkenBrush");
        public static Brush BorderSubtle => Brush("BorderSubtleBrush");
        public static Brush BorderStrong => Brush("BorderStrongBrush");
        public static Brush Accent => Brush("AccentBrush");
        public static Brush AccentSoft => Brush("AccentSoftBrush");
        public static Brush Positive => Brush("PositiveBrush");
        public static Brush Negative => Brush("NegativeBrush");
        public static FontFamily Font => Get<FontFamily>("AppFontFamily") ?? new FontFamily("Segoe UI");

        public static CornerRadius CardRadius => new CornerRadius(12);

        private static Color? ColorOf(Brush b) => (b as SolidColorBrush)?.Color;

        /// <summary>近似灰度（R≈G≈B），用于识别旧版硬编码的黑/灰文字与边框。</summary>
        private static bool IsGrayish(Color c, int tolerance = 14)
            => Math.Abs(c.R - c.G) <= tolerance && Math.Abs(c.G - c.B) <= tolerance;

        /// <summary>对一棵已挂载的 UI 子树做设计系统归一。</summary>
        public static void NormalizePage(DependencyObject root)
        {
            if (root == null) return;
            try
            {
                Apply(root);
                int count = VisualTreeHelper.GetChildrenCount(root);
                for (int i = 0; i < count; i++)
                    NormalizePage(VisualTreeHelper.GetChild(root, i));
            }
            catch { /* 视觉树不可用时静默跳过，不影响功能 */ }
        }

        private static void Apply(DependencyObject d)
        {
            switch (d)
            {
                case TextBlock tb:
                {
                    if (tb.FontFamily == null || tb.FontFamily.Source.IndexOf("YaHei", StringComparison.OrdinalIgnoreCase) >= 0)
                        tb.FontFamily = Font;

                    var c = ColorOf(tb.Foreground);
                    if (c.HasValue)
                    {
                        Color col = c.Value;
                        // 白色/近白（多为主色按钮上的文字）保持不变
                        if (col.R >= 235 && col.G >= 235 && col.B >= 235) return;
                        if (IsGrayish(col))
                        {
                            if (col.R < 70) tb.Foreground = TextPrimary;
                            else if (col.R < 185) tb.Foreground = TextSecondary;
                            else tb.Foreground = TextTertiary;
                        }
                    }

                    // 大字号视为标题：统一半粗 + 主文字色
                    if (tb.FontSize >= 18 && tb.FontWeight != FontWeights.Bold)
                    {
                        tb.FontWeight = FontWeights.SemiBold;
                        tb.Foreground = TextPrimary;
                    }
                    break;
                }
                case Button btn:
                    if (btn.FontFamily == null) btn.FontFamily = Font;
                    break;

                case TextBox box:
                    box.FontFamily = Font;
                    break;

                case ComboBox cb:
                    cb.FontFamily = Font;
                    break;

                case ListBoxItem li:
                    li.FontFamily = Font;
                    break;

                case ProgressBar pb:
                    if (pb.Style == null && R["CustomProgressBarStyle"] is Style ps) pb.Style = ps;
                    break;

                case Border border:
                {
                    // 只处理"有背景、有 1px 硬灰边"的容器：把描边换成半透明 Token
                    var bc = ColorOf(border.BorderBrush);
                    if (bc.HasValue && border.BorderThickness.Left > 0 && IsGrayish(bc.Value)
                        && bc.Value.R > 120 && bc.Value.R < 240)
                    {
                        border.BorderBrush = BorderSubtle;
                    }
                    break;
                }
            }
        }

        // ================= 代码建 UI 的便捷构造器（新页面/补丁用） =================

        public static TextBlock Text(string text, double size = 13, FontWeight? weight = null, Brush brush = null)
            => new TextBlock
            {
                Text = text,
                FontSize = size,
                FontFamily = Font,
                FontWeight = weight ?? FontWeights.Normal,
                Foreground = brush ?? TextPrimary,
                TextWrapping = TextWrapping.Wrap,
            };

        public static TextBlock Heading(string text, double size = 20)
            => Text(text, size, FontWeights.SemiBold, TextPrimary);

        public static TextBlock Caption(string text)
            => Text(text, 12, FontWeights.Normal, TextTertiary);

        /// <summary>带网格列号的文字（代码里往 Grid 里加控件时用）。</summary>
        public static TextBlock Text(string text, double size, FontWeight weight, Brush brush, int gridColumn)
        {
            var tb = Text(text, size, weight, brush);
            System.Windows.Controls.Grid.SetColumn(tb, gridColumn);
            return tb;
        }

        /// <summary>区块卡片：标题 + 内容，统一内边距与卡片质感（替代默认 GroupBox）。</summary>
        public static Border SectionCard(string header, UIElement content)
        {
            var body = new StackPanel();
            body.Children.Add(new TextBlock
            {
                Text = header,
                FontSize = 14,
                FontWeight = FontWeights.SemiBold,
                FontFamily = Font,
                Foreground = TextPrimary,
                Margin = new Thickness(0, 0, 0, 10),
            });
            body.Children.Add(content);
            var b = Card(body, new Thickness(18, 16, 18, 18));
            b.Margin = new Thickness(0, 0, 0, 14);
            return b;
        }

        /// <summary>统一卡片容器：12 圆角、半透明细边框、低不透明度软阴影。</summary>
        public static Border Card(UIElement child, Thickness? padding = null)
        {
            var b = new Border
            {
                Background = Surface,
                BorderBrush = BorderSubtle,
                BorderThickness = new Thickness(1),
                CornerRadius = CardRadius,
                Padding = padding ?? new Thickness(16),
                Child = child,
                Effect = new System.Windows.Media.Effects.DropShadowEffect
                {
                    ShadowDepth = 2,
                    BlurRadius = 12,
                    Opacity = 0.05,
                    Color = Colors.Black,
                },
            };
            return b;
        }

        /// <summary>状态小胶囊（架构 / 已上传 / 未解锁 等）。</summary>
        public static Border Pill(string text, Brush foreground = null, Brush background = null)
        {
            return new Border
            {
                CornerRadius = new CornerRadius(999),
                Padding = new Thickness(8, 2, 8, 2),
                Background = background ?? AccentSoft,
                Child = new TextBlock
                {
                    Text = text,
                    FontSize = 11,
                    FontFamily = Font,
                    FontWeight = FontWeights.SemiBold,
                    Foreground = foreground ?? Accent,
                },
            };
        }
    }
}
