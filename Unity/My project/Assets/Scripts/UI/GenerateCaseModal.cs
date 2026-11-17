using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// Bảng Điền Thông Tin Sinh Vụ Án Mới Bằng AI (Case Generator Modal):
/// 1. Hiển thị Model AI đang dùng & cho phép chọn nhanh các model phổ biến (Gemini, Llama, GPT, Ollama).
/// 2. Nhập bối cảnh & gợi ý vị trí địa điểm (Biệt thự Blackwood, Tàu đêm, Bệnh viện cũ, Lab AI...).
/// 3. Bộ lọc cách thức gây án & thể loại bí ẩn (Phòng kín, Đầu độc, Hung khí biến mất, Biệt thự bão...).
/// 4. Năm xảy ra vụ án (cho phép gõ số năm hoặc bấm chọn nhanh thời kỳ).
/// 5. Khi bấm Sinh vụ án: Hiển thị màn hình chờ tải kèm nhạc Conan và nạp hồ sơ lên bảng trinh thám.
/// </summary>
public class GenerateCaseModal : MonoBehaviour
{
    private static GenerateCaseModal _instance;
    public static GenerateCaseModal Instance
    {
        get
        {
            if (_instance == null)
            {
                _instance = FindObjectOfType<GenerateCaseModal>(true);
            }
            return _instance;
        }
        private set => _instance = value;
    }

    private Font font;
    private RectTransform root;

    // UI Controls
    private Text modelDisplayTxt;
    private readonly List<Image> modelBtnImages = new List<Image>();
    private readonly List<string> modelBtnKeys = new List<string>();

    private Dropdown countryDropdown;
    private InputField yearInput;
    private string selectedEra = "Hiện đại (2020s)";
    private InputField settingInput;
    private Dropdown mysteryDropdown;
    private Text feedbackText;

    private static readonly Color BgOverlay = new Color(0.04f, 0.04f, 0.05f, 0.94f);
    private static readonly Color CardColor = new Color(0.10f, 0.10f, 0.12f, 0.98f);
    private static readonly Color FieldColor = new Color(0.15f, 0.16f, 0.19f, 1f);
    private static readonly Color BorderColor = new Color(0.24f, 0.25f, 0.28f, 1f);
    private static readonly Color TitleGold = new Color(0.96f, 0.82f, 0.38f);
    private static readonly Color TextWhite = new Color(0.93f, 0.93f, 0.90f);
    private static readonly Color TextMuted = new Color(0.65f, 0.65f, 0.60f);

    private static readonly Color BtnGreen = new Color(0.14f, 0.55f, 0.32f);
    private static readonly Color BtnBlue = new Color(0.20f, 0.28f, 0.38f);
    private static readonly Color BtnRed = new Color(0.40f, 0.18f, 0.18f);

    private static readonly Color ChipSelected = new Color(0.14f, 0.50f, 0.32f);
    private static readonly Color ChipNormal = new Color(0.18f, 0.20f, 0.24f);

    public bool IsOpen => root != null && root.gameObject.activeSelf;

    public void Initialize(Font uiFont)
    {
        font = uiFont;
        Instance = this;
    }

    private void Awake()
    {
        if (_instance == null) _instance = this;
    }

    public void Open()
    {
        _instance = this;
        gameObject.SetActive(true);

        if (root == null) BuildUI();

        if (root != null)
        {
            // Deactivate any legacy scene placeholder children
            foreach (Transform child in transform)
            {
                if (child != root && child.gameObject != root.gameObject)
                {
                    child.gameObject.SetActive(false);
                }
            }

            root.SetAsLastSibling();
            root.gameObject.SetActive(true);
        }

        RefreshModelDisplay();
        if (feedbackText != null) feedbackText.text = "";
    }

    public void Close()
    {
        if (root != null) root.gameObject.SetActive(false);
        TitleMenuModal titleMenu = TitleMenuModal.Instance ?? FindObjectOfType<TitleMenuModal>(true);
        titleMenu?.Open();
    }

    private void Update()
    {
        if (IsOpen)
        {
#if ENABLE_INPUT_SYSTEM
            if (UnityEngine.InputSystem.Keyboard.current != null && UnityEngine.InputSystem.Keyboard.current.escapeKey.wasPressedThisFrame)
            {
                Close();
            }
#else
            if (Input.GetKeyDown(KeyCode.Escape))
            {
                Close();
            }
#endif
        }
    }

    public void RefreshModelDisplay()
    {
        string currentModel = ServerConfig.SelectedModel;
        if (string.IsNullOrEmpty(currentModel)) currentModel = ServerConfig.DefaultModel;

        if (modelDisplayTxt != null)
        {
            modelDisplayTxt.text = $"⚡ Mô hình đang kích hoạt: <color=#f5d061><b>{currentModel}</b></color>";
        }

        // Highlight selected model button
        for (int i = 0; i < modelBtnKeys.Count; i++)
        {
            if (i < modelBtnImages.Count && modelBtnImages[i] != null)
            {
                bool isMatch = string.Equals(modelBtnKeys[i], currentModel, StringComparison.OrdinalIgnoreCase);
                modelBtnImages[i].color = isMatch ? ChipSelected : ChipNormal;
            }
        }
    }

    private void SelectModel(string modelId)
    {
        ServerConfig.SaveModelConfig(modelId, null, null);
        AudioManager.Instance?.PlayPinClick();
        RefreshModelDisplay();
    }

    private void OnStartGenerateClicked()
    {
        string country = countryDropdown != null ? countryDropdown.options[countryDropdown.value].text : "Việt Nam";
        string mystery = mysteryDropdown != null ? mysteryDropdown.options[mysteryDropdown.value].text : "Án mạng phòng kín (Locked-Room Mystery)";
        string yearStr = yearInput != null ? yearInput.text.Trim() : "2026";
        if (string.IsNullOrEmpty(yearStr)) yearStr = "2026";
        string setting = settingInput != null ? settingInput.text.Trim() : "Biệt thự cổ Blackwood";
        if (string.IsNullOrEmpty(setting)) setting = "Biệt thự cổ Blackwood";

        string eraWithYear = $"{selectedEra} (Năm {yearStr})";
        string finalTheme = $"Năm {yearStr} tại {country}: {setting} - {mystery}";

        GenerateCaseRequest payload = new GenerateCaseRequest
        {
            country = country,
            mystery_type = mystery,
            era = eraWithYear,
            setting_type = setting,
            theme = finalTheme,
            model = ServerConfig.SelectedModel,
            api_base = ServerConfig.ApiBase,
            api_key = ServerConfig.ApiKey
        };

        string json = JsonUtility.ToJson(payload);

        // Hide form and show cinematic loading screen with Conan music
        if (root != null) root.gameObject.SetActive(false);

        GameLoadingScreen.Instance?.Show($"ĐANG SINH VỤ ÁN: {mystery.ToUpper()} ({yearStr})...");

        DetectiveAPIManager api = DetectiveAPIManager.Instance ?? FindObjectOfType<DetectiveAPIManager>();
        if (api == null)
        {
            GameObject apiGo = new GameObject("DetectiveAPIManager_Runtime");
            api = apiGo.AddComponent<DetectiveAPIManager>();
        }

        api.GenerateCase(json, (success, dossier) =>
        {
            GameLoadingScreen.Instance?.Hide();
            if (success && dossier != null)
            {
                HotkeyTaskbar.Instance?.SetTaskbarVisuals(true);
                GameController controller = GameController.Instance ?? FindObjectOfType<GameController>();
                controller?.LoadCaseFromData(dossier);
            }
            else
            {
                Open();
                if (feedbackText != null)
                {
                    feedbackText.text = $"⚠️ Không thể kết nối Backend tại {ServerConfig.HttpBaseUrl}.\nHãy kiểm tra Backend đang chạy hoặc bấm 'VỤ ÁN MẪU (CHƠI NGAY)' bên dưới để chơi ngay!";
                }
            }
        });
    }

    private void OnLoadSampleClicked()
    {
        if (root != null) root.gameObject.SetActive(false);

        GameLoadingScreen.Instance?.Show("ĐANG NẠP HỒ SƠ VỤ ÁN MẪU...");

        DetectiveAPIManager api = DetectiveAPIManager.Instance ?? FindObjectOfType<DetectiveAPIManager>();
        if (api == null)
        {
            GameObject apiGo = new GameObject("DetectiveAPIManager_Runtime");
            api = apiGo.AddComponent<DetectiveAPIManager>();
        }

        api.GetSampleCase((success, dossier) =>
        {
            GameLoadingScreen.Instance?.Hide();
            if (success && dossier != null)
            {
                HotkeyTaskbar.Instance?.SetTaskbarVisuals(true);
                GameController controller = GameController.Instance ?? FindObjectOfType<GameController>();
                controller?.LoadCaseFromData(dossier);
            }
            else
            {
                Open();
                if (feedbackText != null)
                {
                    feedbackText.text = "⚠️ Không thể tải hồ sơ vụ án mẫu!";
                }
            }
        });
    }

    private void BuildUI()
    {
        Canvas canvas = GetComponentInParent<Canvas>() ?? FindObjectOfType<Canvas>(true);
        if (canvas == null) return;
        if (transform.parent != canvas.transform)
        {
            transform.SetParent(canvas.transform, false);
        }

        // Fullscreen Root Overlay
        GameObject rootGo = new GameObject("GenerateCaseModal_Root", typeof(RectTransform), typeof(Image));
        root = rootGo.GetComponent<RectTransform>();
        root.SetParent(canvas.transform, false);
        root.anchorMin = Vector2.zero;
        root.anchorMax = Vector2.one;
        root.sizeDelta = Vector2.zero;
        rootGo.GetComponent<Image>().color = BgOverlay;

        // Center Panel (700 x 640)
        GameObject panelGo = new GameObject("CenterPanel", typeof(RectTransform), typeof(Image));
        RectTransform panel = panelGo.GetComponent<RectTransform>();
        panel.SetParent(root, false);
        panel.anchorMin = new Vector2(0.5f, 0.5f);
        panel.anchorMax = new Vector2(0.5f, 0.5f);
        panel.pivot = new Vector2(0.5f, 0.5f);
        panel.sizeDelta = new Vector2(700f, 640f);
        panelGo.GetComponent<Image>().color = CardColor;

        // Header Title & Subtitle
        CreateText(panel, "TÙY BIẾN VỤ ÁN MỚI BẰNG AI", 20, TitleGold, FontStyle.Bold, new Vector2(0f, 285f), new Vector2(640f, 30f), TextAnchor.MiddleCenter);
        CreateText(panel, "Hệ thống trinh thám tích hợp mô hình ngôn ngữ lớn (LLM) & Y pháp nhiệt học Henssge", 11, TextMuted, FontStyle.Normal, new Vector2(0f, 258f), new Vector2(640f, 20f), TextAnchor.MiddleCenter);
        CreateDivider(panel, new Vector2(0f, 242f), 640f);

        // =========================================================================
        // SECTION 1: MÔ HÌNH AI ĐANG DÙNG & TÙY CHỌN
        // =========================================================================
        CreateText(panel, "MÔ HÌNH AI ĐANG DÙNG & TÙY CHỌN:", 12, TitleGold, FontStyle.Bold, new Vector2(0f, 222f), new Vector2(640f, 20f), TextAnchor.MiddleLeft);

        // Model Display Badge Box
        GameObject modelBadge = new GameObject("ModelBadgeBox", typeof(RectTransform), typeof(Image));
        RectTransform mbrt = modelBadge.GetComponent<RectTransform>();
        mbrt.SetParent(panel, false);
        mbrt.anchoredPosition = new Vector2(0f, 198f);
        mbrt.sizeDelta = new Vector2(640f, 26f);
        modelBadge.GetComponent<Image>().color = FieldColor;

        modelDisplayTxt = CreateText(mbrt, "⚡ Mô hình đang kích hoạt: " + ServerConfig.SelectedModel, 11, TextWhite, FontStyle.Normal, Vector2.zero, new Vector2(620f, 24f), TextAnchor.MiddleLeft);
        modelDisplayTxt.supportRichText = true;

        // Row of 4 Popular Model Chips
        GameObject modelChipGroup = new GameObject("ModelChips", typeof(RectTransform), typeof(HorizontalLayoutGroup));
        RectTransform mcgrt = modelChipGroup.GetComponent<RectTransform>();
        mcgrt.SetParent(panel, false);
        mcgrt.anchoredPosition = new Vector2(0f, 168f);
        mcgrt.sizeDelta = new Vector2(640f, 28f);
        HorizontalLayoutGroup mchlg = modelChipGroup.GetComponent<HorizontalLayoutGroup>();
        mchlg.spacing = 8f;
        mchlg.childControlWidth = true;
        mchlg.childControlHeight = true;

        modelBtnImages.Clear();
        modelBtnKeys.Clear();
        RegisterModelChip(modelChipGroup.transform, "⚡ Gemini 2.0 Flash", "google/gemini-2.0-flash-exp:free");
        RegisterModelChip(modelChipGroup.transform, "⭐ Llama 3.3 (70B)", "meta-llama/llama-3.3-70b-instruct:free");
        RegisterModelChip(modelChipGroup.transform, "🧠 GPT-4o-mini", "openai/gpt-4o-mini");
        RegisterModelChip(modelChipGroup.transform, "💻 Ollama Offline", "llama3.2:latest");

        CreateDivider(panel, new Vector2(0f, 145f), 640f);

        // =========================================================================
        // SECTION 2: BỐI CẢNH, ĐỊA ĐIỂM & NĂM XẢY RA VỤ ÁN
        // =========================================================================
        // Row 1: Quốc gia (Country) & Năm xảy ra vụ án (Year)
        CreateText(panel, "Quốc gia bối cảnh:", 12, TextWhite, FontStyle.Bold, new Vector2(-225f, 122f), new Vector2(150f, 24f), TextAnchor.MiddleLeft);
        countryDropdown = CreateDropdown(panel, new Vector2(-75f, 122f), new Vector2(160f, 30f), new List<string> {
            "Việt Nam",
            "Nhật Bản",
            "Anh Quốc",
            "Pháp",
            "Hoa Kỳ"
        });

        CreateText(panel, "Năm xảy ra vụ án:", 12, TextWhite, FontStyle.Bold, new Vector2(95f, 122f), new Vector2(130f, 24f), TextAnchor.MiddleLeft);
        yearInput = CreateInputField(panel, new Vector2(245f, 122f), new Vector2(150f, 30f), "2026", "2026");

        // Row 2: Era quick chips
        CreateText(panel, "Gợi ý thời kỳ:", 11, TextMuted, FontStyle.Italic, new Vector2(-240f, 85f), new Vector2(120f, 24f), TextAnchor.MiddleLeft);
        GameObject eraChipGroup = new GameObject("EraChips", typeof(RectTransform), typeof(HorizontalLayoutGroup));
        RectTransform ecrt = eraChipGroup.GetComponent<RectTransform>();
        ecrt.SetParent(panel, false);
        ecrt.anchoredPosition = new Vector2(70f, 85f);
        ecrt.sizeDelta = new Vector2(500f, 26f);
        HorizontalLayoutGroup echlg = eraChipGroup.GetComponent<HorizontalLayoutGroup>();
        echlg.spacing = 6f;
        echlg.childControlWidth = true;
        echlg.childControlHeight = true;

        CreateChip(eraChipGroup.transform, "📱 2026 (Hiện đại)", () => { yearInput.text = "2026"; selectedEra = "Hiện đại (2020s)"; });
        CreateChip(eraChipGroup.transform, "📼 1996 (Thập niên 90)", () => { yearInput.text = "1996"; selectedEra = "Thập niên 1990"; });
        CreateChip(eraChipGroup.transform, "🕰️ 1930 (Cổ điển)", () => { yearInput.text = "1930"; selectedEra = "Đông Dương / Cổ điển (1930s)"; });
        CreateChip(eraChipGroup.transform, "📜 1895 (Victoria)", () => { yearInput.text = "1895"; selectedEra = "Thời đại Victoria (Cuối TK 19)"; });

        // Row 3: Setting / Location Input
        CreateText(panel, "Bối cảnh & Vị trí địa điểm:", 12, TextWhite, FontStyle.Bold, new Vector2(-195f, 48f), new Vector2(250f, 22f), TextAnchor.MiddleLeft);
        settingInput = CreateInputField(panel, new Vector2(0f, 20f), new Vector2(640f, 32f), "Nhập bối cảnh địa điểm hoặc chọn gợi ý bên dưới...", "Biệt thự cổ Blackwood");

        // Row 4: Location quick suggestion chips
        GameObject locChipGroup = new GameObject("LocationChips", typeof(RectTransform), typeof(HorizontalLayoutGroup));
        RectTransform lcrt = locChipGroup.GetComponent<RectTransform>();
        lcrt.SetParent(panel, false);
        lcrt.anchoredPosition = new Vector2(0f, -14f);
        lcrt.sizeDelta = new Vector2(640f, 26f);
        HorizontalLayoutGroup lchlg = locChipGroup.GetComponent<HorizontalLayoutGroup>();
        lchlg.spacing = 6f;
        lchlg.childControlWidth = true;
        lchlg.childControlHeight = true;

        CreateChip(locChipGroup.transform, "🏰 Biệt thự Blackwood", () => settingInput.text = "Biệt thự cổ Blackwood ven đồi");
        CreateChip(locChipGroup.transform, "🚂 Tàu đêm Bắc-Nam", () => settingInput.text = "Chuyến tàu đêm Thống Nhất Bắc - Nam");
        CreateChip(locChipGroup.transform, "🏥 Bệnh viện cũ", () => settingInput.text = "Bệnh viện đa khoa cũ bỏ hoang");
        CreateChip(locChipGroup.transform, "🔬 Viện nghiên cứu AI", () => settingInput.text = "Phòng thí nghiệm AI tối mật");
        CreateChip(locChipGroup.transform, "🎭 Nhà hát Đà Lạt", () => settingInput.text = "Nhà hát Opera Đà Lạt trong đêm mưa");
        CreateChip(locChipGroup.transform, "🏢 Tập đoàn công nghệ", () => settingInput.text = "Trụ sở tập đoàn công nghệ cao");

        CreateDivider(panel, new Vector2(0f, -42f), 640f);

        // =========================================================================
        // SECTION 3: BỘ LỌC CÁCH THỨC GÂY ÁN & THỂ LOẠI BÍ ẨN
        // =========================================================================
        CreateText(panel, "BỘ LỌC CÁCH THỨC GÂY ÁN & THỂ LOẠI BÍ ẨN:", 12, TitleGold, FontStyle.Bold, new Vector2(0f, -60f), new Vector2(640f, 20f), TextAnchor.MiddleLeft);
        mysteryDropdown = CreateDropdown(panel, new Vector2(0f, -90f), new Vector2(640f, 32f), new List<string> {
            "Án mạng phòng kín (Locked-Room Mystery)",
            "Đầu độc bí ẩn không màu không mùi (Poisoning)",
            "Hung khí biến mất không dấu vết (Vanishing Weapon)",
            "Biệt thự cô lập giữa đêm mưa bão (Isolated Manor)",
            "Hiện trường giả & Alibi ngoại phạm giả (Staged Crime & False Alibi)",
            "Tranh chấp thừa kế gia tộc thượng lưu (Family Inheritance Feud)"
        });

        CreateDivider(panel, new Vector2(0f, -125f), 640f);

        // =========================================================================
        // SECTION 4: THÔNG BÁO / FEEDBACK TRẠNG THÁI
        // =========================================================================
        GameObject fbGo = new GameObject("FeedbackText", typeof(RectTransform), typeof(Text));
        RectTransform fbrt = fbGo.GetComponent<RectTransform>();
        fbrt.SetParent(panel, false);
        fbrt.anchoredPosition = new Vector2(0f, -155f);
        fbrt.sizeDelta = new Vector2(640f, 36f);
        feedbackText = fbGo.GetComponent<Text>();
        feedbackText.font = font ?? DetectiveAssetBank.GetDefaultUIFont();
        feedbackText.fontSize = 11;
        feedbackText.alignment = TextAnchor.MiddleCenter;
        feedbackText.color = new Color(1f, 0.45f, 0.45f);
        feedbackText.text = "";

        // =========================================================================
        // SECTION 5: CÁC NÚT HÀNH ĐỘNG
        // =========================================================================
        // [✕ HỦY & QUAY LẠI]
        CreateActionButton(panel, "✕  HỦY & QUAY LẠI", BtnRed, new Vector2(-220f, -215f), new Vector2(185f, 44f), Close);

        // [📜 VỤ ÁN MẪU (CHƠI NGAY)]
        CreateActionButton(panel, "📜  VỤ ÁN MẪU (CHƠI NGAY)", BtnBlue, new Vector2(0f, -215f), new Vector2(215f, 44f), OnLoadSampleClicked);

        // [✨ BẮT ĐẦU SINH VỤ ÁN]
        CreateActionButton(panel, "✨  SINH VỤ ÁN BẰNG AI", BtnGreen, new Vector2(220f, -215f), new Vector2(195f, 44f), OnStartGenerateClicked);
    }

    private void RegisterModelChip(Transform parent, string label, string modelKey)
    {
        GameObject go = new GameObject("Chip_" + label, typeof(RectTransform), typeof(Image), typeof(Button));
        go.transform.SetParent(parent, false);
        Image img = go.GetComponent<Image>();
        img.color = ChipNormal;
        modelBtnImages.Add(img);
        modelBtnKeys.Add(modelKey);

        Button btn = go.GetComponent<Button>();
        btn.onClick.AddListener(() => SelectModel(modelKey));

        GameObject textGo = new GameObject("Text", typeof(RectTransform), typeof(Text));
        RectTransform rt = textGo.GetComponent<RectTransform>();
        rt.SetParent(go.transform, false);
        rt.anchorMin = Vector2.zero;
        rt.anchorMax = Vector2.one;
        rt.sizeDelta = Vector2.zero;

        Text txt = textGo.GetComponent<Text>();
        txt.font = font ?? DetectiveAssetBank.GetDefaultUIFont();
        txt.fontSize = 11;
        txt.fontStyle = FontStyle.Bold;
        txt.color = TextWhite;
        txt.alignment = TextAnchor.MiddleCenter;
        txt.text = label;
    }

    private Dropdown CreateDropdown(Transform parent, Vector2 pos, Vector2 sizeDelta, List<string> options)
    {
        GameObject go = new GameObject("Dropdown", typeof(RectTransform), typeof(Image), typeof(Dropdown));
        RectTransform rt = go.GetComponent<RectTransform>();
        rt.SetParent(parent, false);
        rt.anchoredPosition = pos;
        rt.sizeDelta = sizeDelta;
        go.GetComponent<Image>().color = FieldColor;

        Dropdown dd = go.GetComponent<Dropdown>();

        GameObject labelGo = new GameObject("Label", typeof(RectTransform), typeof(Text));
        RectTransform lrt = labelGo.GetComponent<RectTransform>();
        lrt.SetParent(go.transform, false);
        lrt.anchorMin = Vector2.zero;
        lrt.anchorMax = Vector2.one;
        lrt.offsetMin = new Vector2(10f, 2f);
        lrt.offsetMax = new Vector2(-28f, -2f);

        Text label = labelGo.GetComponent<Text>();
        label.font = font ?? DetectiveAssetBank.GetDefaultUIFont();
        label.fontSize = 12;
        label.color = TextWhite;
        label.alignment = TextAnchor.MiddleLeft;

        // Down arrow icon
        CreateText(go.transform, "▼", 10, TextMuted, FontStyle.Normal, new Vector2(sizeDelta.x / 2f - 14f, 0f), new Vector2(20f, 20f), TextAnchor.MiddleCenter);

        dd.captionText = label;
        dd.ClearOptions();
        dd.AddOptions(options);

        // Template for popup
        GameObject template = new GameObject("Template", typeof(RectTransform), typeof(Image), typeof(ScrollRect));
        RectTransform trt = template.GetComponent<RectTransform>();
        trt.SetParent(go.transform, false);
        trt.anchorMin = new Vector2(0f, 0f);
        trt.anchorMax = new Vector2(1f, 0f);
        trt.pivot = new Vector2(0.5f, 1f);
        trt.anchoredPosition = new Vector2(0f, 0f);
        trt.sizeDelta = new Vector2(0f, 160f);
        template.GetComponent<Image>().color = new Color(0.12f, 0.12f, 0.14f, 0.98f);

        GameObject viewport = new GameObject("Viewport", typeof(RectTransform), typeof(RectMask2D), typeof(Image));
        RectTransform vrt = viewport.GetComponent<RectTransform>();
        vrt.SetParent(template.transform, false);
        vrt.anchorMin = Vector2.zero;
        vrt.anchorMax = Vector2.one;
        vrt.sizeDelta = Vector2.zero;
        viewport.GetComponent<Image>().color = Color.clear;

        GameObject content = new GameObject("Content", typeof(RectTransform));
        RectTransform crt = content.GetComponent<RectTransform>();
        crt.SetParent(viewport.transform, false);
        crt.anchorMin = new Vector2(0f, 1f);
        crt.anchorMax = new Vector2(1f, 1f);
        crt.pivot = new Vector2(0.5f, 1f);
        crt.sizeDelta = new Vector2(0f, 28f);

        VerticalLayoutGroup vlg = content.AddComponent<VerticalLayoutGroup>();
        vlg.spacing = 2f;
        vlg.childControlWidth = true;
        vlg.childControlHeight = false;
        vlg.childForceExpandHeight = false;

        ContentSizeFitter csf = content.AddComponent<ContentSizeFitter>();
        csf.verticalFit = ContentSizeFitter.FitMode.PreferredSize;

        ScrollRect sr = template.GetComponent<ScrollRect>();
        sr.content = crt;
        sr.viewport = vrt;
        sr.horizontal = false;
        sr.vertical = true;

        GameObject item = new GameObject("Item", typeof(RectTransform), typeof(Toggle), typeof(Image));
        RectTransform irt = item.GetComponent<RectTransform>();
        irt.SetParent(content.transform, false);
        irt.anchorMin = new Vector2(0f, 0.5f);
        irt.anchorMax = new Vector2(1f, 0.5f);
        irt.sizeDelta = new Vector2(0f, 28f);
        item.GetComponent<Image>().color = new Color(0.16f, 0.17f, 0.20f);

        LayoutElement le = item.AddComponent<LayoutElement>();
        le.minHeight = 28f;
        le.preferredHeight = 28f;

        GameObject itemLabel = new GameObject("Item Label", typeof(RectTransform), typeof(Text));
        RectTransform ilrt = itemLabel.GetComponent<RectTransform>();
        ilrt.SetParent(item.transform, false);
        ilrt.anchorMin = Vector2.zero;
        ilrt.anchorMax = Vector2.one;
        ilrt.offsetMin = new Vector2(10f, 2f);
        ilrt.offsetMax = new Vector2(-10f, -2f);

        Text itemTxt = itemLabel.GetComponent<Text>();
        itemTxt.font = font ?? DetectiveAssetBank.GetDefaultUIFont();
        itemTxt.fontSize = 12;
        itemTxt.color = TextWhite;
        itemTxt.alignment = TextAnchor.MiddleLeft;

        Toggle toggle = item.GetComponent<Toggle>();
        toggle.targetGraphic = item.GetComponent<Image>();

        dd.template = trt;
        dd.itemText = itemTxt;

        template.SetActive(false);
        return dd;
    }

    private InputField CreateInputField(Transform parent, Vector2 pos, Vector2 sizeDelta, string placeholder, string defaultVal = "")
    {
        GameObject go = new GameObject("InputField", typeof(RectTransform), typeof(Image), typeof(InputField));
        RectTransform rt = go.GetComponent<RectTransform>();
        rt.SetParent(parent, false);
        rt.anchoredPosition = pos;
        rt.sizeDelta = sizeDelta;
        go.GetComponent<Image>().color = FieldColor;

        InputField input = go.GetComponent<InputField>();

        // Text
        GameObject textGo = new GameObject("Text", typeof(RectTransform), typeof(Text));
        RectTransform trt = textGo.GetComponent<RectTransform>();
        trt.SetParent(go.transform, false);
        trt.anchorMin = Vector2.zero;
        trt.anchorMax = Vector2.one;
        trt.offsetMin = new Vector2(10f, 2f);
        trt.offsetMax = new Vector2(-10f, -2f);

        Text txt = textGo.GetComponent<Text>();
        txt.font = font ?? DetectiveAssetBank.GetDefaultUIFont();
        txt.fontSize = 12;
        txt.color = TextWhite;
        txt.alignment = TextAnchor.MiddleLeft;

        // Placeholder
        GameObject phGo = new GameObject("Placeholder", typeof(RectTransform), typeof(Text));
        RectTransform phrt = phGo.GetComponent<RectTransform>();
        phrt.SetParent(go.transform, false);
        phrt.anchorMin = Vector2.zero;
        phrt.anchorMax = Vector2.one;
        phrt.offsetMin = new Vector2(10f, 2f);
        phrt.offsetMax = new Vector2(-10f, -2f);

        Text phTxt = phGo.GetComponent<Text>();
        phTxt.font = font ?? DetectiveAssetBank.GetDefaultUIFont();
        phTxt.fontSize = 12;
        phTxt.fontStyle = FontStyle.Italic;
        phTxt.color = TextMuted;
        phTxt.alignment = TextAnchor.MiddleLeft;
        phTxt.text = placeholder;

        input.textComponent = txt;
        input.placeholder = phTxt;
        if (!string.IsNullOrEmpty(defaultVal)) input.text = defaultVal;

        return input;
    }

    private void CreateChip(Transform parent, string label, Action onClick)
    {
        GameObject go = new GameObject("Chip_" + label, typeof(RectTransform), typeof(Image), typeof(Button));
        go.transform.SetParent(parent, false);
        go.GetComponent<Image>().color = ChipNormal;
        Button btn = go.GetComponent<Button>();
        btn.onClick.AddListener(() =>
        {
            AudioManager.Instance?.PlayPinClick();
            onClick?.Invoke();
        });

        GameObject textGo = new GameObject("Text", typeof(RectTransform), typeof(Text));
        RectTransform rt = textGo.GetComponent<RectTransform>();
        rt.SetParent(go.transform, false);
        rt.anchorMin = Vector2.zero;
        rt.anchorMax = Vector2.one;
        rt.sizeDelta = Vector2.zero;

        Text txt = textGo.GetComponent<Text>();
        txt.font = font ?? DetectiveAssetBank.GetDefaultUIFont();
        txt.fontSize = 10;
        txt.color = TextWhite;
        txt.alignment = TextAnchor.MiddleCenter;
        txt.text = label;
    }

    private void CreateActionButton(Transform parent, string label, Color color, Vector2 pos, Vector2 sizeDelta, Action onClick)
    {
        GameObject go = new GameObject("Btn_" + label, typeof(RectTransform), typeof(Image), typeof(Button));
        RectTransform rt = go.GetComponent<RectTransform>();
        rt.SetParent(parent, false);
        rt.anchoredPosition = pos;
        rt.sizeDelta = sizeDelta;

        go.GetComponent<Image>().color = color;
        Button btn = go.GetComponent<Button>();
        btn.onClick.AddListener(() =>
        {
            AudioManager.Instance?.PlayPinClick();
            onClick?.Invoke();
        });

        GameObject textGo = new GameObject("Text", typeof(RectTransform), typeof(Text));
        RectTransform trt = textGo.GetComponent<RectTransform>();
        trt.SetParent(go.transform, false);
        trt.anchorMin = Vector2.zero;
        trt.anchorMax = Vector2.one;
        trt.sizeDelta = Vector2.zero;

        Text txt = textGo.GetComponent<Text>();
        txt.font = font ?? DetectiveAssetBank.GetDefaultUIFont();
        txt.fontSize = 12;
        txt.fontStyle = FontStyle.Bold;
        txt.color = Color.white;
        txt.alignment = TextAnchor.MiddleCenter;
        txt.text = label;
    }

    private Text CreateText(Transform parent, string text, int size, Color color, FontStyle style, Vector2 pos, Vector2 sizeDelta, TextAnchor alignment)
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
        return txt;
    }

    private void CreateDivider(Transform parent, Vector2 pos, float width)
    {
        GameObject div = new GameObject("Divider", typeof(RectTransform), typeof(Image));
        RectTransform drt = div.GetComponent<RectTransform>();
        drt.SetParent(parent, false);
        drt.anchoredPosition = pos;
        drt.sizeDelta = new Vector2(width, 1.5f);
        div.GetComponent<Image>().color = BorderColor;
    }
}
