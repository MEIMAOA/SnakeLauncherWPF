using System.Windows;

namespace SnakeLauncherWPF
{
    public partial class SplashWindow : Window
    {
        public SplashWindow()
        {
            InitializeComponent();

            // ★ 应用多语言
            ApplyLocalization();
        }

        private void ApplyLocalization()
        {
            try
            {
                this.Title = Lang.T("App.Launching");
                if (TxtSplashTitle != null) TxtSplashTitle.Text = Lang.T("Splash.Title");
                if (TxtSplashSubtitle != null) TxtSplashSubtitle.Text = Lang.T("Splash.Subtitle");
                if (TxtSplashVersion != null)
                    TxtSplashVersion.Text = "OFFICIAL  /  v" + UpdateService.GetCurrentVersion().ToString();
            }
            catch { }
        }
    }
}