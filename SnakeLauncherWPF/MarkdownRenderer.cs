using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;
using System.Windows;
using System.Windows.Documents;
using System.Windows.Media;

namespace SnakeLauncherWPF
{
    /// <summary>
    /// 极简 Markdown → FlowDocument 渲染器
    /// 支持：# 标题、**粗体**、*斜体*、`行内代码`、
    ///       - 列表、1. 有序列表、> 引用、``` 代码块、
    ///       [链接](url)、水平线 ---
    /// </summary>
    public static class MarkdownRenderer
    {
        public static FlowDocument Render(string markdown, Brush foreground, Brush accent,
            double fontSize = 13)
        {
            var doc = new FlowDocument
            {
                FontFamily = new FontFamily("Microsoft YaHei UI"),
                FontSize = fontSize,
                Foreground = foreground,
                PagePadding = new Thickness(16),
                LineHeight = fontSize * 1.55
            };

            if (string.IsNullOrWhiteSpace(markdown))
            {
                doc.Blocks.Add(new Paragraph(new Run("（空）")));
                return doc;
            }

            string[] lines = markdown.Replace("\r\n", "\n").Replace('\r', '\n').Split('\n');
            int i = 0;

            while (i < lines.Length)
            {
                string line = lines[i];

                // ============ 代码块 ``` ============
                if (line.TrimStart().StartsWith("```"))
                {
                    var codeLines = new List<string>();
                    i++;
                    while (i < lines.Length && !lines[i].TrimStart().StartsWith("```"))
                    {
                        codeLines.Add(lines[i]);
                        i++;
                    }
                    i++; // 跳过结尾 ```
                    AddCodeBlock(doc, string.Join("\n", codeLines), foreground);
                    continue;
                }

                // ============ 水平线 --- ============
                if (Regex.IsMatch(line.Trim(), @"^[-*_]{3,}$"))
                {
                    doc.Blocks.Add(new Paragraph(new Run(""))
                    {
                        BorderBrush = accent,
                        BorderThickness = new Thickness(0, 0, 0, 1),
                        Margin = new Thickness(0, 8, 0, 8)
                    });
                    i++;
                    continue;
                }

                // ============ 标题 # ## ### ... ============
                var headingMatch = Regex.Match(line, @"^(#{1,6})\s+(.*)$");
                if (headingMatch.Success)
                {
                    int level = headingMatch.Groups[1].Value.Length;
                    string text = headingMatch.Groups[2].Value;
                    double size = level switch
                    {
                        1 => fontSize + 11,
                        2 => fontSize + 7,
                        3 => fontSize + 4,
                        4 => fontSize + 2,
                        _ => fontSize + 1
                    };
                    var p = new Paragraph
                    {
                        FontSize = size,
                        FontWeight = FontWeights.Bold,
                        Margin = new Thickness(0, level == 1 ? 10 : 8, 0, 4)
                    };
                    AddInlineMarkdown(p, text, foreground, accent, fontSize);
                    doc.Blocks.Add(p);
                    i++;
                    continue;
                }

                // ============ 引用 > ============
                if (line.TrimStart().StartsWith(">"))
                {
                    var quoteLines = new List<string>();
                    while (i < lines.Length && lines[i].TrimStart().StartsWith(">"))
                    {
                        quoteLines.Add(lines[i].TrimStart().TrimStart('>').TrimStart());
                        i++;
                    }
                    var p = new Paragraph
                    {
                        BorderBrush = accent,
                        BorderThickness = new Thickness(3, 0, 0, 0),
                        Padding = new Thickness(10, 4, 0, 4),
                        Margin = new Thickness(0, 4, 0, 4),
                        FontStyle = FontStyles.Italic,
                        Foreground = foreground
                    };
                    AddInlineMarkdown(p, string.Join(" ", quoteLines), foreground, accent, fontSize);
                    doc.Blocks.Add(p);
                    continue;
                }

                // ============ 无序列表 - * + ============
                if (Regex.IsMatch(line, @"^\s*[-*+]\s+"))
                {
                    var p = new Paragraph { Margin = new Thickness(20, 2, 0, 2) };
                    p.Inlines.Add(new Run("• ") { Foreground = accent });
                    string content = Regex.Replace(line, @"^\s*[-*+]\s+", "");
                    AddInlineMarkdown(p, content, foreground, accent, fontSize);
                    doc.Blocks.Add(p);
                    i++;
                    continue;
                }

                // ============ 有序列表 1. ============
                var olMatch = Regex.Match(line, @"^\s*(\d+)\.\s+(.*)$");
                if (olMatch.Success)
                {
                    var p = new Paragraph { Margin = new Thickness(20, 2, 0, 2) };
                    p.Inlines.Add(new Run(olMatch.Groups[1].Value + ". ") { Foreground = accent });
                    AddInlineMarkdown(p, olMatch.Groups[2].Value, foreground, accent, fontSize);
                    doc.Blocks.Add(p);
                    i++;
                    continue;
                }

                // ============ 空行 ============
                if (string.IsNullOrWhiteSpace(line))
                {
                    i++;
                    continue;
                }

                // ============ 普通段落（合并连续行） ============
                var paraLines = new List<string>();
                while (i < lines.Length && !string.IsNullOrWhiteSpace(lines[i])
                    && !lines[i].TrimStart().StartsWith("#")
                    && !lines[i].TrimStart().StartsWith(">")
                    && !lines[i].TrimStart().StartsWith("```")
                    && !Regex.IsMatch(lines[i], @"^\s*[-*+]\s+")
                    && !Regex.IsMatch(lines[i], @"^\s*\d+\.\s+"))
                {
                    paraLines.Add(lines[i]);
                    i++;
                }
                if (paraLines.Count > 0)
                {
                    var p = new Paragraph { Margin = new Thickness(0, 3, 0, 3) };
                    AddInlineMarkdown(p, string.Join(" ", paraLines), foreground, accent, fontSize);
                    doc.Blocks.Add(p);
                }
            }

            return doc;
        }

        /// <summary>
        /// 解析行内 Markdown：**粗体**、*斜体*、`代码`、[链接](url)、~~删除线~~
        /// </summary>
        private static void AddInlineMarkdown(Paragraph p, string text, Brush foreground,
            Brush accent, double fontSize)
        {
            if (string.IsNullOrEmpty(text)) return;

            // 用一个统一的正则按顺序匹配所有行内标记
            var pattern = new Regex(
                @"(\*\*(.+?)\*\*)|(__\s*(.+?)\s*__)|(\*(.+?)\*)|(_(.+?)_)|(`(.+?)`)|(\[(.+?)\]\((.+?)\))|(~~(.+?)~~)",
                RegexOptions.Compiled);

            int lastIndex = 0;

            foreach (Match m in pattern.Matches(text))
            {
                if (m.Index > lastIndex)
                {
                    p.Inlines.Add(new Run(text.Substring(lastIndex, m.Index - lastIndex))
                    {
                        Foreground = foreground
                    });
                }

                if (m.Groups[2].Success)  // **bold**
                {
                    p.Inlines.Add(new Run(m.Groups[2].Value)
                    {
                        FontWeight = FontWeights.Bold,
                        Foreground = foreground
                    });
                }
                else if (m.Groups[4].Success)  // __bold__
                {
                    p.Inlines.Add(new Run(m.Groups[4].Value)
                    {
                        FontWeight = FontWeights.Bold,
                        Foreground = foreground
                    });
                }
                else if (m.Groups[6].Success)  // *italic*
                {
                    p.Inlines.Add(new Run(m.Groups[6].Value)
                    {
                        FontStyle = FontStyles.Italic,
                        Foreground = foreground
                    });
                }
                else if (m.Groups[8].Success)  // _italic_
                {
                    p.Inlines.Add(new Run(m.Groups[8].Value)
                    {
                        FontStyle = FontStyles.Italic,
                        Foreground = foreground
                    });
                }
                else if (m.Groups[10].Success)  // `code`
                {
                    p.Inlines.Add(new Run(m.Groups[10].Value)
                    {
                        FontFamily = new FontFamily("Consolas, Microsoft YaHei UI"),
                        Background = new SolidColorBrush(Color.FromArgb(0x20, 0x80, 0x80, 0x80)),
                        Foreground = accent
                    });
                }
                else if (m.Groups[12].Success)  // [text](url)
                {
                    var link = new Hyperlink(new Run(m.Groups[12].Value))
                    {
                        Foreground = accent,
                        TextDecorations = null,
                        Cursor = System.Windows.Input.Cursors.Hand,
                        ToolTip = m.Groups[13].Value
                    };
                    string url = m.Groups[13].Value;
                    link.Click += (s, e) =>
                    {
                        try
                        {
                            System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo
                            {
                                FileName = url,
                                UseShellExecute = true
                            });
                        }
                        catch { }
                    };
                    p.Inlines.Add(link);
                }
                else if (m.Groups[15].Success)  // ~~strikethrough~~
                {
                    p.Inlines.Add(new Run(m.Groups[15].Value)
                    {
                        TextDecorations = TextDecorations.Strikethrough,
                        Foreground = foreground
                    });
                }

                lastIndex = m.Index + m.Length;
            }

            if (lastIndex < text.Length)
            {
                p.Inlines.Add(new Run(text.Substring(lastIndex)) { Foreground = foreground });
            }
        }

        private static void AddCodeBlock(FlowDocument doc, string code, Brush foreground)
        {
            var p = new Paragraph
            {
                FontFamily = new FontFamily("Consolas, Microsoft YaHei UI"),
                FontSize = 12,
                Background = new SolidColorBrush(Color.FromArgb(0x18, 0x80, 0x80, 0x80)),
                Padding = new Thickness(10, 6, 10, 6),
                Margin = new Thickness(0, 6, 0, 6),
                Foreground = foreground
            };
            p.Inlines.Add(new Run(code));
            doc.Blocks.Add(p);
        }
    }
}