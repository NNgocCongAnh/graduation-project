using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// Bảng Cài đặt Toàn diện 5 Tab (Universal Settings Modal):
/// 1. Giao diện (Graphics: Fullscreen, Resolution, Dây chỉ đỏ)
/// 2. Âm thanh (Audio: Master, BGM, SFX, Chọn nhạc: Detective Noir / Conan Theme)
/// 3. Điều khiển (Controls: Bảng phím tắt)
/// 4. Hướng dẫn (Tutorial: Quy trình phá án, công thức Henssge)
/// 5. Mô hình AI (AI Engine: OpenRouter Free, Ollama Offline, Gateway, Host)
/// Phía dưới: Nút [Áp dụng] và [Đóng] (quay lại đúng Menu trước đó, không đè cửa sổ).
/// </summary>
public class SettingsModal : MonoBehaviour
{
    private static readonly Color PanelColor = new Color(0.08f, 0.08f, 0.09f, 0.98f);
    private static readonly Color TabActiveColor = new Color(0.18f, 0.48f, 0.35f);
    private static readonly Color TabInactiveColor = new Color(0.14f, 0.15f, 0.17f);
    private static readonly Color FieldColor = new Color(0.14f, 0.14f, 0.15f);
    private static readonly Color TextColor = new Color(0.92f, 0.90f, 0.84f);
    private static readonly Color TitleGold = new Color(0.96f, 0.82f, 0.38f);
    private static readonly Color MutedColor = new Color(0.65f, 0.65f, 0.60f);

    private Font font;
    private RectTransform root;

    // Tabs
    private enum TabIndex { Graphics, Audio, Controls, Tutorial, AI }
    private TabIndex currentTab = TabIndex.Graphics;
    private GameObject[] tabPanels = new GameObject[5];
    private Image[] tabButtons = new Image[5];

    // Inputs - AI
    private InputField modelField;
    private InputField apiBaseField;
    private InputField apiKeyField;
    private InputField hostField;
    private Text aiStatusText;

    // Audio UI
    private Slider masterSlider;
    private Slider bgmSlider;
    private Text currentTrackText;

    // Graphics UI
    private Toggle fullscreenToggle;
    private Toggle redStringsToggle;
    private int selectedWidth = 1920;
    private int selectedHeight = 1080;

    private bool openedFromMainMenu = false;

    public static SettingsModal Instance { get; private set; }
    public bool IsOpen => root != null && root.gameObject.activeSelf;

    public void Initialize(Font uiFont)
    {
        font = uiFont;
        Instance = this;
    }

    public void Toggle()
    {
        if (IsOpen) Close();
        else Open();
    }

    public void Open()
    {
        if (root == null) BuildUI();

        // Check if opened from Main Menu
        TitleMenuModal title = FindObjectOfType<TitleMenuModal>();
        openedFromMainMenu = (title != null && (title.IsOpen || !FindObjectOfType<GameController>().isCaseLoaded));

        LoadCurrentValues();
        transform.SetAsLastSibling();
        root.gameObject.SetActive(true);
        SwitchTab(TabIndex.Graphics);
    }

    public void Close()
    {
        if (root != null) root.gameObject.SetActive(false);

        // Return to previous screen
        if (openedFromMainMenu)
        {
            FindObjectOfType<TitleMenuModal>()?.Open();
        }
        else
        {
            FindObjectOfType<InGamePauseModal>()?.Open();
        }
    }

    private void LoadCurrentValues()
    {
        if (modelField != null) modelField.text = ServerConfig.SelectedModel;
        if (apiBaseField != null) apiBaseField.text = ServerConfig.ApiBase;
        if (apiKeyField != null) apiKeyField.text = ServerConfig.ApiKey;
        if (hostField != null) hostField.text = ServerConfig.Host;

        if (masterSlider != null && AudioManager.Instance != null) masterSlider.value = AudioManager.Instance.MasterVolume;
        if (bgmSlider != null && AudioManager.Instance != null) bgmSlider.value = AudioManager.Instance.BgmVolume;
        UpdateTrackText();

        if (fullscreenToggle != null) fullscreenToggle.isOn = Screen.fullScreen;
        if (redStringsToggle != null && CorkboardManager.Instance != null) redStringsToggle.isOn = CorkboardManager.Instance.showRedStrings;
    }

    private void UpdateTrackText()
    {
        if (currentTrackText == null || AudioManager.Instance == null) return;
        string tName = AudioManager.Instance.GetTrackDisplayName(AudioManager.Instance.CurrentTrack);
        string modeStr = AudioManager.Instance.CurrentPlayMode == AudioManager.PlaybackMode.Shuffle ? "🔀 Ngẫu nhiên" :
                         AudioManager.Instance.CurrentPlayMode == AudioManager.PlaybackMode.Sequential ? "🔁 Tuần tự" : "🔂 Lặp 1 bài";
        currentTrackText.text = $"Đang phát: <b>{tName}</b>\nChế độ: <b>{modeStr}</b> · <i>(Bấm phím <b>N</b> để đổi bài ngay lập tức)</i>";
    }

    private void BuildUI()
    {
        Canvas canvas = GetComponentInParent<Canvas>() ?? FindObjectOfType<Canvas>(true);
        if (canvas == null) return;
        if (transform.parent != canvas.transform)
        {
            transform.SetParent(canvas.transform, false);
        }

        // Root Overlay
        GameObject rootGo = new GameObject("SettingsModal_Root", typeof(RectTransform), typeof(Image));
        root = rootGo.GetComponent<RectTransform>();
        root.SetParent(canvas.transform, false);
        root.anchorMin = Vector2.zero;
        root.anchorMax = Vector2.one;
        root.sizeDelta = Vector2.zero;
        rootGo.GetComponent<Image>().color = new Color(0.04f, 0.04f, 0.05f, 0.95f);

        // Center Panel (680 x 580)
        GameObject panelGo = new GameObject("CenterPanel", typeof(RectTransform), typeof(Image));
        RectTransform panel = panelGo.GetComponent<RectTransform>();
        panel.SetParent(root, false);
        panel.anchorMin = new Vector2(0.5f, 0.5f);
        panel.anchorMax = new Vector2(0.5f, 0.5f);
        panel.pivot = new Vector2(0.5f, 0.5f);
        panel.sizeDelta = new Vector2(680f, 580f);
        panelGo.GetComponent<Image>().color = PanelColor;

        // Header Title
        CreateText(panel, "CÀI ĐẶT HỆ THỐNG", 22, TitleGold, FontStyle.Bold, new Vector2(0f, 255f), new Vector2(500f, 30f));

        // Top 5-Tab Bar
        GameObject tabBarGo = new GameObject("TabBar", typeof(RectTransform), typeof(HorizontalLayoutGroup));
        RectTransform tabBar = tabBarGo.GetComponent<RectTransform>();
        tabBar.SetParent(panel, false);
        tabBar.anchorMin = new Vector2(0.04f, 0.82f);
        tabBar.anchorMax = new Vector2(0.96f, 0.89f);
        tabBar.sizeDelta = Vector2.zero;

        HorizontalLayoutGroup hlg = tabBarGo.GetComponent<HorizontalLayoutGroup>();
        hlg.spacing = 6f;
        hlg.childControlWidth = true;
        hlg.childControlHeight = true;

        tabButtons[0] = CreateTabButton(tabBarGo.transform, "🎨 Giao diện", () => SwitchTab(TabIndex.Graphics));
        tabButtons[1] = CreateTabButton(tabBarGo.transform, "🔊 Âm thanh", () => SwitchTab(TabIndex.Audio));
        tabButtons[2] = CreateTabButton(tabBarGo.transform, "🎮 Điều khiển", () => SwitchTab(TabIndex.Controls));
        tabButtons[3] = CreateTabButton(tabBarGo.transform, "📖 Hướng dẫn", () => SwitchTab(TabIndex.Tutorial));
        tabButtons[4] = CreateTabButton(tabBarGo.transform, "🧠 Mô hình AI", () => SwitchTab(TabIndex.AI));

        // Tab Content Area (0.04 to 0.96, 0.12 to 0.80)
        RectTransform contentArea = CreateContainer(panel, "ContentArea", new Vector2(0.04f, 0.12f), new Vector2(0.96f, 0.80f));

        // Build 5 Tab Panels
        tabPanels[0] = BuildGraphicsTab(contentArea);
        tabPanels[1] = BuildAudioTab(contentArea);
        tabPanels[2] = BuildControlsTab(contentArea);
        tabPanels[3] = BuildTutorialTab(contentArea);
        tabPanels[4] = BuildAITab(contentArea);

        // Bottom Action Buttons: [Áp dụng] and [Đóng]
        GameObject bottomBar = new GameObject("BottomBar", typeof(RectTransform));
        RectTransform bbrt = bottomBar.GetComponent<RectTransform>();
        bbrt.SetParent(panel, false);
        bbrt.anchorMin = new Vector2(0.04f, 0.02f);
        bbrt.anchorMax = new Vector2(0.96f, 0.09f);
        bbrt.sizeDelta = Vector2.zero;

        // Apply Button
        CreateActionButton(bottomBar.transform, "💾  ÁP DỤNG", new Color(0.14f, 0.50f, 0.32f), new Vector2(0.68f, 0f), new Vector2(0.98f, 1f), ApplyAllSettings);

        // Close Button
        CreateActionButton(bottomBar.transform, "✕  ĐÓNG", new Color(0.38f, 0.20f, 0.20f), new Vector2(0.35f, 0f), new Vector2(0.65f, 1f), Close);
    }

    private void SwitchTab(TabIndex tab)
    {
        currentTab = tab;
        for (int i = 0; i < tabPanels.Length; i++)
        {
            if (tabPanels[i] != null) tabPanels[i].SetActive(i == (int)tab);
            if (tabButtons[i] != null) tabButtons[i].color = (i == (int)tab) ? TabActiveColor : TabInactiveColor;
        }
    }

    // -------------------------------------------------------------------------
    // TAB 1: GIAO DIỆN (GRAPHICS)
    // -------------------------------------------------------------------------
    private GameObject BuildGraphicsTab(Transform parent)
    {
        GameObject go = new GameObject("Tab_Graphics", typeof(RectTransform));
        RectTransform rt = go.GetComponent<RectTransform>();
        rt.SetParent(parent, false);
        rt.anchorMin = Vector2.zero;
        rt.anchorMax = Vector2.one;
        rt.sizeDelta = Vector2.zero;

        CreateText(go.transform, "TÙY CHỈNH HÌNH ẢNH & ĐỒ HỌA", 16, TitleGold, FontStyle.Bold, new Vector2(0f, 150f), new Vector2(400f, 25f));

        // Fullscreen Toggle
        fullscreenToggle = CreateToggle(go.transform, "Chế độ Toàn màn hình (Borderless Fullscreen)", new Vector2(0f, 105f), val =>
        {
            // Value saved on Apply
        });

        // Quick resolution presets row
        CreateText(go.transform, "Độ phân giải & Chế độ cửa sổ:", 12, TextColor, FontStyle.Bold, new Vector2(0f, 60f), new Vector2(400f, 20f));

        GameObject resRow = new GameObject("ResRow", typeof(RectTransform), typeof(HorizontalLayoutGroup));
        RectTransform rrt = resRow.GetComponent<RectTransform>();
        rrt.SetParent(go.transform, false);
        rrt.anchoredPosition = new Vector2(0f, 30f);
        rrt.sizeDelta = new Vector2(580f, 30f);
        HorizontalLayoutGroup rhlg = resRow.GetComponent<HorizontalLayoutGroup>();
        rhlg.spacing = 6f;
        rhlg.childControlWidth = true;
        rhlg.childControlHeight = true;

        CreateSmallButton(resRow.transform, "🖥️ Toàn màn hình", () =>
        {
            if (fullscreenToggle != null) fullscreenToggle.isOn = true;
            Resolution native = Screen.currentResolution;
            selectedWidth = native.width > 0 ? native.width : 1920;
            selectedHeight = native.height > 0 ? native.height : 1080;
        });
        CreateSmallButton(resRow.transform, "🪟 1920 x 1080", () =>
        {
            if (fullscreenToggle != null) fullscreenToggle.isOn = false;
            selectedWidth = 1920;
            selectedHeight = 1080;
        });
        CreateSmallButton(resRow.transform, "🪟 1600 x 900", () =>
        {
            if (fullscreenToggle != null) fullscreenToggle.isOn = false;
            selectedWidth = 1600;
            selectedHeight = 900;
        });
        CreateSmallButton(resRow.transform, "🪟 1280 x 720 (Chuẩn)", () =>
        {
            if (fullscreenToggle != null) fullscreenToggle.isOn = false;
            selectedWidth = 1280;
            selectedHeight = 720;
        });

        // Red Strings Toggle
        redStringsToggle = CreateToggle(go.transform, "Hiển thị Dây chỉ đỏ nối chứng cứ trên Bảng", new Vector2(0f, -20f), val =>
        {
            if (CorkboardManager.Instance != null) CorkboardManager.Instance.showRedStrings = val;
        });

        // Visual Style Note
        CreateText(go.transform, "💡 Chế độ Toàn màn hình không viền tự động tối ưu hóa theo màn hình của bạn.\nBấm 'ÁP DỤNG' để lưu cấu hình và đóng bảng cài đặt mượt mà.", 11, MutedColor, FontStyle.Italic, new Vector2(0f, -80f), new Vector2(560f, 40f));

        return go;
    }

    // -------------------------------------------------------------------------
    // TAB 2: ÂM THANH (AUDIO)
    // -------------------------------------------------------------------------
    private GameObject BuildAudioTab(Transform parent)
    {
        GameObject go = new GameObject("Tab_Audio", typeof(RectTransform));
        RectTransform rt = go.GetComponent<RectTransform>();
        rt.SetParent(parent, false);
        rt.anchorMin = Vector2.zero;
        rt.anchorMax = Vector2.one;
        rt.sizeDelta = Vector2.zero;

        CreateText(go.transform, "TÙY CHỈNH ÂM THANH & DANH SÁCH NHẠC NỀN", 16, TitleGold, FontStyle.Bold, new Vector2(0f, 150f), new Vector2(450f, 25f));

        // Master Volume
        CreateText(go.transform, "Âm lượng tổng (Master):", 12, TextColor, FontStyle.Normal, new Vector2(-150f, 110f), new Vector2(240f, 20f));
        masterSlider = CreateSlider(go.transform, new Vector2(100f, 110f), val => AudioManager.Instance?.SetMasterVolume(val));

        // BGM Volume
        CreateText(go.transform, "Âm lượng Nhạc (BGM):", 12, TextColor, FontStyle.Normal, new Vector2(-150f, 75f), new Vector2(240f, 20f));
        bgmSlider = CreateSlider(go.transform, new Vector2(100f, 75f), val => AudioManager.Instance?.SetBgmVolume(val));

        // Playback Mode Controls
        CreateText(go.transform, "Chế độ phát nhạc:", 12, TextColor, FontStyle.Bold, new Vector2(0f, 38f), new Vector2(400f, 20f));

        GameObject modeRow = new GameObject("ModeRow", typeof(RectTransform), typeof(HorizontalLayoutGroup));
        RectTransform mrt = modeRow.GetComponent<RectTransform>();
        mrt.SetParent(go.transform, false);
        mrt.anchoredPosition = new Vector2(0f, 12f);
        mrt.sizeDelta = new Vector2(580f, 28f);
        HorizontalLayoutGroup mhlg = modeRow.GetComponent<HorizontalLayoutGroup>();
        mhlg.spacing = 6f;
        mhlg.childControlWidth = true;
        mhlg.childControlHeight = true;

        CreateSmallButton(modeRow.transform, "🔀 Ngẫu nhiên (Shuffle)", () =>
        {
            AudioManager.Instance?.SetPlaybackMode(AudioManager.PlaybackMode.Shuffle);
            UpdateTrackText();
        });
        CreateSmallButton(modeRow.transform, "🔁 Tuần tự (Playlist)", () =>
        {
            AudioManager.Instance?.SetPlaybackMode(AudioManager.PlaybackMode.Sequential);
            UpdateTrackText();
        });
        CreateSmallButton(modeRow.transform, "🔂 Lặp 1 bài", () =>
        {
            AudioManager.Instance?.SetPlaybackMode(AudioManager.PlaybackMode.SingleLoop);
            UpdateTrackText();
        });
        CreateSmallButton(modeRow.transform, "⏭️ Đổi bài (N)", () =>
        {
            AudioManager.Instance?.PlayNextTrack();
            UpdateTrackText();
        });

        // Track Selector Buttons
        CreateText(go.transform, "Chọn bài hát muốn nghe ngay:", 12, TextColor, FontStyle.Bold, new Vector2(0f, -22f), new Vector2(400f, 20f));

        GameObject trackRow1 = new GameObject("TrackRow1", typeof(RectTransform), typeof(HorizontalLayoutGroup));
        RectTransform trt1 = trackRow1.GetComponent<RectTransform>();
        trt1.SetParent(go.transform, false);
        trt1.anchoredPosition = new Vector2(0f, -48f);
        trt1.sizeDelta = new Vector2(580f, 28f);
        HorizontalLayoutGroup thlg1 = trackRow1.GetComponent<HorizontalLayoutGroup>();
        thlg1.spacing = 6f;
        thlg1.childControlWidth = true;
        thlg1.childControlHeight = true;

        CreateSmallButton(trackRow1.transform, "🌸 Ran's Theme (Nhẹ)", () =>
        {
            AudioManager.Instance?.SwitchTrack(AudioManager.BgmTrack.ConanRan);
            UpdateTrackText();
        });
        CreateSmallButton(trackRow1.transform, "🌙 Conan's Dream (Êm dịu)", () =>
        {
            AudioManager.Instance?.SwitchTrack(AudioManager.BgmTrack.ConanDream);
            UpdateTrackText();
        });
        CreateSmallButton(trackRow1.transform, "⚡ Conan Main Theme", () =>
        {
            AudioManager.Instance?.SwitchTrack(AudioManager.BgmTrack.ConanMain);
            UpdateTrackText();
        });

        GameObject trackRow2 = new GameObject("TrackRow2", typeof(RectTransform), typeof(HorizontalLayoutGroup));
        RectTransform trt2 = trackRow2.GetComponent<RectTransform>();
        trt2.SetParent(go.transform, false);
        trt2.anchoredPosition = new Vector2(0f, -80f);
        trt2.sizeDelta = new Vector2(580f, 28f);
        HorizontalLayoutGroup thlg2 = trackRow2.GetComponent<HorizontalLayoutGroup>();
        thlg2.spacing = 6f;
        thlg2.childControlWidth = true;
        thlg2.childControlHeight = true;

        CreateSmallButton(trackRow2.transform, "⚔️ Showdown (Gay cấn)", () =>
        {
            AudioManager.Instance?.SwitchTrack(AudioManager.BgmTrack.ConanShowdown);
            UpdateTrackText();
        });
        CreateSmallButton(trackRow2.transform, "🎷 Noir Jazz", () =>
        {
            AudioManager.Instance?.SwitchTrack(AudioManager.BgmTrack.NoirJazz);
            UpdateTrackText();
        });
        CreateSmallButton(trackRow2.transform, "🔇 Tắt Nhạc", () =>
        {
            AudioManager.Instance?.SwitchTrack(AudioManager.BgmTrack.Mute);
            UpdateTrackText();
        });

        // Current track display
        GameObject ctg = new GameObject("CurrentTrackText", typeof(RectTransform), typeof(Text));
        RectTransform ctr = ctg.GetComponent<RectTransform>();
        ctr.SetParent(go.transform, false);
        ctr.anchoredPosition = new Vector2(0f, -125f);
        ctr.sizeDelta = new Vector2(560f, 36f);
        currentTrackText = ctg.GetComponent<Text>();
        currentTrackText.font = font ?? DetectiveAssetBank.GetDefaultUIFont();
        currentTrackText.fontSize = 11;
        currentTrackText.alignment = TextAnchor.MiddleCenter;
        currentTrackText.color = TitleGold;
        UpdateTrackText();

        return go;
    }

    // -------------------------------------------------------------------------
    // TAB 3: ĐIỀU KHIỂN (CONTROLS)
    // -------------------------------------------------------------------------
    private GameObject BuildControlsTab(Transform parent)
    {
        GameObject go = new GameObject("Tab_Controls", typeof(RectTransform));
        RectTransform rt = go.GetComponent<RectTransform>();
        rt.SetParent(parent, false);
        rt.anchorMin = Vector2.zero;
        rt.anchorMax = Vector2.one;
        rt.sizeDelta = Vector2.zero;

        CreateText(go.transform, "BẢNG PHÍM TẮT & THAO TÁC", 16, TitleGold, FontStyle.Bold, new Vector2(0f, 150f), new Vector2(400f, 25f));

        string cheatSheet =
            "• <b>Chuột trái (Kéo/Thả):</b> Di chuyển thẻ chứng cứ và nghi phạm trên bảng điều tra.\n" +
            "• <b>Cuộn chuột (Scroll):</b> Thu phóng camera bảng án (Zoom In / Out).\n" +
            "• <b>Click Đèn bàn (Bankers Lamp):</b> Giật dây xích bật/tắt bóng đèn vintage.\n" +
            "• <b>Click Gạt tàn thuốc:</b> Gõ tàn thuốc và thổi ra làn khói bay lượn.\n" +
            "• <b>Phím ESC / M:</b> Mở Menu Tạm dừng / Menu Chính.\n" +
            "• <b>Phím L:</b> Mở danh sách Phòng điều tra Co-op (LAN/Cloud).\n" +
            "• <b>Phím T:</b> Mở khung Chat trao đổi thám tử.\n" +
            "• <b>Phím O:</b> Mở nhanh Bảng Cài đặt.\n" +
            "• <b>Phím V (Giữ):</b> Đàm thoại Micro Voice chat (Push-to-Talk) trong phòng Co-op.";

        CreateText(go.transform, cheatSheet, 13, TextColor, FontStyle.Normal, new Vector2(0f, -10f), new Vector2(560f, 260f), TextAnchor.MiddleLeft);

        return go;
    }

    // -------------------------------------------------------------------------
    // TAB 4: HƯỚNG DẪN (TUTORIAL)
    // -------------------------------------------------------------------------
    private GameObject BuildTutorialTab(Transform parent)
    {
        GameObject go = new GameObject("Tab_Tutorial", typeof(RectTransform));
        RectTransform rt = go.GetComponent<RectTransform>();
        rt.SetParent(parent, false);
        rt.anchorMin = Vector2.zero;
        rt.anchorMax = Vector2.one;
        rt.sizeDelta = Vector2.zero;

        CreateText(go.transform, "QUY TRÌNH PHÁ ÁN Y PHÁP 4 BƯỚC", 16, TitleGold, FontStyle.Bold, new Vector2(0f, 150f), new Vector2(400f, 25f));

        string guide =
            "1. <b>BƯỚC 1: KHÁM NGHIỆM TỬ THI HENSSGE</b>\n" +
            "   Đọc kỹ nhiệt độ trực tràng, nhiệt độ môi trường và cân nặng của nạn nhân. Dùng đồ thị 2 số mũ Henssge để xác định cửa sổ tử vong chính xác (Time of Death Window).\n\n" +
            "2. <b>BƯỚC 2: RÀ SOÁT CHỨNG CỨ NGOẠI PHẠM (ALIBI)</b>\n" +
            "   Kiểm tra thẻ nghi phạm và các mốc thời gian. Nghi phạm nào không có bằng chứng ngoại phàm khớp với cửa sổ tử vong sẽ bị đưa vào diện tình nghi hàng đầu.\n\n" +
            "3. <b>BƯỚC 3: DÂY CHỈ ĐỎ LIÊN KẾT MANH MỐI</b>\n" +
            "   Kéo thẻ lại gần nhau để nối dây chỉ đỏ giữa: Động cơ $\\leftrightarrow$ Vật chứng $\\leftrightarrow$ Hiện trường.\n\n" +
            "4. <b>BƯỚC 4: KẾT TỘI HUNG THỦ</b>\n" +
            "   Chọn đúng nghi phạm và đính kèm ít nhất 2 chứng cứ quyết định để đóng hồ sơ vụ án!";

        CreateText(go.transform, guide, 12, TextColor, FontStyle.Normal, new Vector2(0f, -10f), new Vector2(560f, 260f), TextAnchor.MiddleLeft);

        return go;
    }

    // -------------------------------------------------------------------------
    // TAB 5: MÔ HÌNH AI (AI ENGINE)
    // -------------------------------------------------------------------------
    private GameObject BuildAITab(Transform parent)
    {
        GameObject go = new GameObject("Tab_AI", typeof(RectTransform));
        RectTransform rt = go.GetComponent<RectTransform>();
        rt.SetParent(parent, false);
        rt.anchorMin = Vector2.zero;
        rt.anchorMax = Vector2.one;
        rt.sizeDelta = Vector2.zero;

        CreateText(go.transform, "CẤU HÌNH MÔ HÌNH AI (LLM)", 16, TitleGold, FontStyle.Bold, new Vector2(0f, 160f), new Vector2(400f, 25f));

        // 1. Provider Selection Chips
        CreateText(go.transform, "Chọn Nhà cung cấp AI phổ biến:", 13, TextColor, FontStyle.Bold, new Vector2(0f, 120f), new Vector2(500f, 20f));

        GameObject provGroup = new GameObject("ProviderGroup", typeof(RectTransform), typeof(HorizontalLayoutGroup));
        RectTransform prt = provGroup.GetComponent<RectTransform>();
        prt.SetParent(go.transform, false);
        prt.anchoredPosition = new Vector2(0f, 85f);
        prt.sizeDelta = new Vector2(580f, 32f);
        HorizontalLayoutGroup phlg = provGroup.GetComponent<HorizontalLayoutGroup>();
        phlg.spacing = 6f;
        phlg.childControlWidth = true;
        phlg.childControlHeight = true;

        CreateSmallButton(provGroup.transform, "🟢 OpenAI (ChatGPT)", () => SetModelPreset("gpt-4o-mini", "https://api.openai.com/v1", ""));
        CreateSmallButton(provGroup.transform, "🔵 Google Gemini", () => SetModelPreset("gemini-2.0-flash", "https://generativelanguage.googleapis.com/v1beta/openai/", ""));
        CreateSmallButton(provGroup.transform, "💻 Ollama (Offline)", () => SetModelPreset("qwen2.5:7b", "http://localhost:11434/v1", "ollama"));
        CreateSmallButton(provGroup.transform, "⭐ OpenRouter (Free)", () => SetModelPreset("meta-llama/llama-3.3-70b-instruct:free", "https://openrouter.ai/api/v1", ""));
        CreateSmallButton(provGroup.transform, "🎓 9Router (Luận văn)", () => SetModelPreset("gh/gpt-4o-mini", "http://localhost:20128/v1", "sk-9router-local"));

        // 2. Base URL
        CreateText(go.transform, "Đường dẫn API (Base URL):", 12, TextColor, FontStyle.Bold, new Vector2(-190f, 30f), new Vector2(180f, 24f));
        apiBaseField = CreateInputField(go.transform, new Vector2(70f, 30f), new Vector2(360f, 32f));

        // 3. API Key
        CreateText(go.transform, "Khóa bí mật (API Key):", 12, TextColor, FontStyle.Bold, new Vector2(-190f, -20f), new Vector2(180f, 24f));
        apiKeyField = CreateInputField(go.transform, new Vector2(70f, -20f), new Vector2(360f, 32f));

        // Model name (read-only display)
        CreateText(go.transform, "Tên mô hình đang dùng:", 12, TextColor, FontStyle.Bold, new Vector2(-190f, -70f), new Vector2(180f, 24f));
        modelField = CreateInputField(go.transform, new Vector2(70f, -70f), new Vector2(360f, 32f));

        // AI Status Text
        GameObject stg = new GameObject("AIStatusText", typeof(RectTransform), typeof(Text));
        RectTransform strt = stg.GetComponent<RectTransform>();
        strt.SetParent(go.transform, false);
        strt.anchoredPosition = new Vector2(0f, -125f);
        strt.sizeDelta = new Vector2(560f, 24f);
        aiStatusText = stg.GetComponent<Text>();
        aiStatusText.font = font ?? DetectiveAssetBank.GetDefaultUIFont();
        aiStatusText.fontSize = 12;
        aiStatusText.alignment = TextAnchor.MiddleCenter;
        aiStatusText.color = new Color(0.4f, 0.9f, 0.5f);
        aiStatusText.text = "✓ Chọn Provider ở trên, điền Base URL & API Key rồi bấm ÁP DỤNG.";

        return go;
    }

    private void SetModelPreset(string model, string apiBase, string apiKey = "")
    {
        if (modelField != null) modelField.text = model;
        if (apiBaseField != null) apiBaseField.text = apiBase;
        if (apiKeyField != null && !string.IsNullOrEmpty(apiKey)) apiKeyField.text = apiKey;
        if (aiStatusText != null) aiStatusText.text = $"✓ Đã chọn cấu hình {model}. Hãy bấm ÁP DỤNG.";
    }

    private void ApplyAllSettings()
    {
        // 1. Audio
        if (AudioManager.Instance != null)
        {
            if (masterSlider != null) AudioManager.Instance.SetMasterVolume(masterSlider.value);
            if (bgmSlider != null) AudioManager.Instance.SetBgmVolume(bgmSlider.value);
        }

        // 2. Graphics
        if (fullscreenToggle != null)
        {
            bool isFs = fullscreenToggle.isOn;
            if (isFs)
            {
                Resolution native = Screen.currentResolution;
                int w = (native.width > 0) ? native.width : 1920;
                int h = (native.height > 0) ? native.height : 1080;
                Screen.SetResolution(w, h, FullScreenMode.FullScreenWindow);
            }
            else
            {
                int w = selectedWidth > 0 ? selectedWidth : 1280;
                int h = selectedHeight > 0 ? selectedHeight : 720;
                Screen.SetResolution(w, h, FullScreenMode.Windowed);
            }
            PlayerPrefs.SetInt("graphics.fullscreen", isFs ? 1 : 0);
            PlayerPrefs.Save();
        }
        if (redStringsToggle != null && CorkboardManager.Instance != null)
        {
            CorkboardManager.Instance.showRedStrings = redStringsToggle.isOn;
        }

        // 3. AI & Host
        string chosenModel = modelField != null ? modelField.text.Trim() : ServerConfig.DefaultModel;
        string chosenBase = apiBaseField != null ? apiBaseField.text.Trim() : ServerConfig.DefaultApiBase;
        string chosenKey = apiKeyField != null ? apiKeyField.text.Trim() : ServerConfig.DefaultApiKey;
        string chosenHost = hostField != null ? hostField.text.Trim() : ServerConfig.Host;

        ServerConfig.Save(chosenHost, ServerConfig.PlayerName, ServerConfig.RoomId);
        ServerConfig.SaveModelConfig(chosenModel, chosenBase, chosenKey);

        DetectiveAPIManager.Instance?.UpdateBackendSettings(chosenModel, chosenBase, chosenKey, null);

        // Smoothly close settings modal and return to previous game/menu view
        Close();
    }

    // -------------------------------------------------------------------------
    // UI BUILDER HELPERS
    // -------------------------------------------------------------------------
    private Image CreateTabButton(Transform parent, string label, System.Action onClick)
    {
        GameObject go = new GameObject("TabBtn_" + label, typeof(RectTransform), typeof(Image), typeof(Button));
        go.transform.SetParent(parent, false);

        Image img = go.GetComponent<Image>();
        img.color = TabInactiveColor;

        Button btn = go.GetComponent<Button>();
        btn.onClick.AddListener(() => onClick?.Invoke());

        GameObject textGo = new GameObject("Text", typeof(RectTransform), typeof(Text));
        RectTransform rt = textGo.GetComponent<RectTransform>();
        rt.SetParent(go.transform, false);
        rt.anchorMin = Vector2.zero;
        rt.anchorMax = Vector2.one;
        rt.sizeDelta = Vector2.zero;

        Text txt = textGo.GetComponent<Text>();
        txt.font = font ?? DetectiveAssetBank.GetDefaultUIFont();
        txt.fontSize = 13;
        txt.fontStyle = FontStyle.Bold;
        txt.color = TextColor;
        txt.alignment = TextAnchor.MiddleCenter;
        txt.text = label;

        return img;
    }

    private void CreateSmallButton(Transform parent, string label, System.Action onClick)
    {
        GameObject go = new GameObject("Btn_" + label, typeof(RectTransform), typeof(Image), typeof(Button));
        go.transform.SetParent(parent, false);

        go.GetComponent<Image>().color = new Color(0.20f, 0.22f, 0.26f);
        Button btn = go.GetComponent<Button>();
        btn.onClick.AddListener(() => onClick?.Invoke());

        GameObject textGo = new GameObject("Text", typeof(RectTransform), typeof(Text));
        RectTransform rt = textGo.GetComponent<RectTransform>();
        rt.SetParent(go.transform, false);
        rt.anchorMin = Vector2.zero;
        rt.anchorMax = Vector2.one;
        rt.sizeDelta = Vector2.zero;

        Text txt = textGo.GetComponent<Text>();
        txt.font = font ?? DetectiveAssetBank.GetDefaultUIFont();
        txt.fontSize = 11;
        txt.color = TextColor;
        txt.alignment = TextAnchor.MiddleCenter;
        txt.text = label;
    }

    private void CreateActionButton(Transform parent, string label, Color color, Vector2 anchorMin, Vector2 anchorMax, System.Action onClick)
    {
        GameObject go = new GameObject("ActionBtn_" + label, typeof(RectTransform), typeof(Image), typeof(Button));
        RectTransform rt = go.GetComponent<RectTransform>();
        rt.SetParent(parent, false);
        rt.anchorMin = anchorMin;
        rt.anchorMax = anchorMax;
        rt.sizeDelta = Vector2.zero;

        go.GetComponent<Image>().color = color;
        Button btn = go.GetComponent<Button>();
        btn.onClick.AddListener(() => onClick?.Invoke());

        GameObject textGo = new GameObject("Text", typeof(RectTransform), typeof(Text));
        RectTransform trt = textGo.GetComponent<RectTransform>();
        trt.SetParent(go.transform, false);
        trt.anchorMin = Vector2.zero;
        trt.anchorMax = Vector2.one;
        trt.sizeDelta = Vector2.zero;

        Text txt = textGo.GetComponent<Text>();
        txt.font = font ?? DetectiveAssetBank.GetDefaultUIFont();
        txt.fontSize = 14;
        txt.fontStyle = FontStyle.Bold;
        txt.color = Color.white;
        txt.alignment = TextAnchor.MiddleCenter;
        txt.text = label;
    }

    private RectTransform CreateContainer(Transform parent, string name, Vector2 anchorMin, Vector2 anchorMax)
    {
        GameObject go = new GameObject(name, typeof(RectTransform));
        RectTransform rt = go.GetComponent<RectTransform>();
        rt.SetParent(parent, false);
        rt.anchorMin = anchorMin;
        rt.anchorMax = anchorMax;
        rt.sizeDelta = Vector2.zero;
        return rt;
    }

    private InputField CreateInputField(Transform parent, Vector2 pos, Vector2 sizeDelta)
    {
        GameObject go = new GameObject("InputField", typeof(RectTransform), typeof(Image), typeof(InputField));
        RectTransform rt = go.GetComponent<RectTransform>();
        rt.SetParent(parent, false);
        rt.anchoredPosition = pos;
        rt.sizeDelta = sizeDelta;

        go.GetComponent<Image>().color = FieldColor;
        InputField input = go.GetComponent<InputField>();

        GameObject textGo = new GameObject("Text", typeof(RectTransform), typeof(Text));
        RectTransform trt = textGo.GetComponent<RectTransform>();
        trt.SetParent(go.transform, false);
        trt.anchorMin = Vector2.zero;
        trt.anchorMax = Vector2.one;
        trt.offsetMin = new Vector2(8f, 2f);
        trt.offsetMax = new Vector2(-8f, -2f);

        Text txt = textGo.GetComponent<Text>();
        txt.font = font ?? DetectiveAssetBank.GetDefaultUIFont();
        txt.fontSize = 12;
        txt.color = TextColor;
        txt.alignment = TextAnchor.MiddleLeft;

        input.textComponent = txt;
        return input;
    }

    private Slider CreateSlider(Transform parent, Vector2 pos, System.Action<float> onValueChanged)
    {
        GameObject sliderGo = new GameObject("Slider", typeof(RectTransform), typeof(Slider));
        RectTransform srt = sliderGo.GetComponent<RectTransform>();
        srt.SetParent(parent, false);
        srt.anchoredPosition = pos;
        srt.sizeDelta = new Vector2(240f, 20f);

        Slider s = sliderGo.GetComponent<Slider>();
        s.minValue = 0f;
        s.maxValue = 1f;

        // Background
        GameObject bgGo = new GameObject("Background", typeof(RectTransform), typeof(Image));
        RectTransform bgrt = bgGo.GetComponent<RectTransform>();
        bgrt.SetParent(sliderGo.transform, false);
        bgrt.anchorMin = Vector2.zero;
        bgrt.anchorMax = Vector2.one;
        bgrt.sizeDelta = Vector2.zero;
        bgGo.GetComponent<Image>().color = new Color(0.2f, 0.2f, 0.22f);

        // Fill Area
        GameObject fillAreaGo = new GameObject("Fill Area", typeof(RectTransform));
        RectTransform fart = fillAreaGo.GetComponent<RectTransform>();
        fart.SetParent(sliderGo.transform, false);
        fart.anchorMin = Vector2.zero;
        fart.anchorMax = Vector2.one;
        fart.sizeDelta = Vector2.zero;

        GameObject fillGo = new GameObject("Fill", typeof(RectTransform), typeof(Image));
        RectTransform frt = fillGo.GetComponent<RectTransform>();
        frt.SetParent(fillAreaGo.transform, false);
        frt.sizeDelta = Vector2.zero;
        fillGo.GetComponent<Image>().color = TabActiveColor;
        s.fillRect = frt;

        s.onValueChanged.AddListener(val => onValueChanged?.Invoke(val));
        return s;
    }

    private Toggle CreateToggle(Transform parent, string label, Vector2 pos, System.Action<bool> onValueChanged)
    {
        GameObject toggleGo = new GameObject("Toggle", typeof(RectTransform), typeof(Toggle));
        RectTransform trt = toggleGo.GetComponent<RectTransform>();
        trt.SetParent(parent, false);
        trt.anchoredPosition = pos;
        trt.sizeDelta = new Vector2(400f, 30f);

        Toggle toggle = toggleGo.GetComponent<Toggle>();

        // Checkbox background
        GameObject bgGo = new GameObject("Background", typeof(RectTransform), typeof(Image));
        RectTransform bgrt = bgGo.GetComponent<RectTransform>();
        bgrt.SetParent(toggleGo.transform, false);
        bgrt.anchorMin = new Vector2(0f, 0.5f);
        bgrt.anchorMax = new Vector2(0f, 0.5f);
        bgrt.pivot = new Vector2(0f, 0.5f);
        bgrt.anchoredPosition = new Vector2(0f, 0f);
        bgrt.sizeDelta = new Vector2(24f, 24f);
        bgGo.GetComponent<Image>().color = FieldColor;

        // Checkmark
        GameObject checkmarkGo = new GameObject("Checkmark", typeof(RectTransform), typeof(Image));
        RectTransform cmrt = checkmarkGo.GetComponent<RectTransform>();
        cmrt.SetParent(bgGo.transform, false);
        cmrt.anchorMin = new Vector2(0.2f, 0.2f);
        cmrt.anchorMax = new Vector2(0.8f, 0.8f);
        cmrt.sizeDelta = Vector2.zero;
        checkmarkGo.GetComponent<Image>().color = TitleGold;

        toggle.graphic = checkmarkGo.GetComponent<Image>();
        toggle.targetGraphic = bgGo.GetComponent<Image>();

        // Label
        GameObject labelGo = new GameObject("Label", typeof(RectTransform), typeof(Text));
        RectTransform lrt = labelGo.GetComponent<RectTransform>();
        lrt.SetParent(toggleGo.transform, false);
        lrt.anchorMin = Vector2.zero;
        lrt.anchorMax = Vector2.one;
        lrt.offsetMin = new Vector2(34f, 0f);
        lrt.offsetMax = Vector2.zero;

        Text txt = labelGo.GetComponent<Text>();
        txt.font = font ?? DetectiveAssetBank.GetDefaultUIFont();
        txt.fontSize = 13;
        txt.color = TextColor;
        txt.alignment = TextAnchor.MiddleLeft;
        txt.text = label;

        toggle.onValueChanged.AddListener(val => onValueChanged?.Invoke(val));
        return toggle;
    }

    private void CreateText(Transform parent, string text, int size, Color color, FontStyle style, Vector2 pos, Vector2 sizeDelta, TextAnchor alignment = TextAnchor.MiddleCenter)
    {
        GameObject go = new GameObject("Text", typeof(RectTransform), typeof(Text));
        RectTransform rt = go.GetComponent<RectTransform>();
        rt.SetParent(parent, false);
        rt.anchoredPosition = pos;
        rt.sizeDelta = sizeDelta;

        Text txt = go.GetComponent<Text>();
        txt.font = font ?? DetectiveAssetBank.GetDefaultUIFont();
        txt.fontSize = size;
        txt.color = color;
        txt.fontStyle = style;
        txt.alignment = alignment;
        txt.text = text;
        txt.supportRichText = true;
    }
}
