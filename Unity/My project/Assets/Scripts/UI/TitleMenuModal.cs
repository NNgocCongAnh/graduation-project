using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// Màn hình Chính / Khởi đầu Trò chơi (Main Title Menu):
/// Cung cấp 5 tùy chọn chuẩn:
/// 1. Chơi Mới (Vụ án Mẫu hoặc Sinh vụ án mới bằng AI)
/// 2. Mở File Save (Danh sách các hồ sơ án đã lưu trên máy)
/// 3. Chơi Coop (LAN / Online - Tạo phòng hoặc Vào phòng)
/// 4. Cài Đặt (5 Tab - Mở ẩn Menu chính, đóng hiện lại)
/// 5. Thoát Game
/// </summary>
public class TitleMenuModal : MonoBehaviour
{
    private static readonly Color OverlayColor = new Color(0.04f, 0.04f, 0.05f, 0.96f);
    private static readonly Color CardColor = new Color(0.10f, 0.10f, 0.12f, 0.98f);
    private static readonly Color TitleGold = new Color(0.96f, 0.82f, 0.38f);
    private static readonly Color TextWhite = new Color(0.93f, 0.93f, 0.90f);
    private static readonly Color TextMuted = new Color(0.65f, 0.65f, 0.60f);

    private static readonly Color BtnPrimary = new Color(0.14f, 0.50f, 0.32f);
    private static readonly Color BtnSecondary = new Color(0.20f, 0.22f, 0.26f);
    private static readonly Color BtnDanger = new Color(0.48f, 0.16f, 0.16f);

    private Font font;
    private RectTransform root;

    // Sub-panels
    private GameObject mainButtonGroup;
    private GameObject newGameSubPanel;
    private GameObject loadSaveSubPanel;
    private GameObject coopSubPanel;
    private Transform saveListContainer;

    public static TitleMenuModal Instance { get; private set; }
    public bool IsOpen => root != null && root.gameObject.activeSelf;
    public bool IsInSubPanel => (newGameSubPanel != null && newGameSubPanel.activeSelf) ||
                                (loadSaveSubPanel != null && loadSaveSubPanel.activeSelf) ||
                                (coopSubPanel != null && coopSubPanel.activeSelf);

    public void Initialize(Font uiFont)
    {
        font = uiFont;
        Instance = this;

        // Proactively ensure Audio, LoadingScreen, and Ashtray are present
        EnsureAudioManager();
        EnsureLoadingScreen();
        EnsureAshtrayProp();
        EnsureAPIManager();
    }

    private void EnsureLoadingScreen()
    {
        GameLoadingScreen ls = FindObjectOfType<GameLoadingScreen>(true);
        if (ls == null)
        {
            Canvas canvas = GetComponentInParent<Canvas>() ?? FindObjectOfType<Canvas>(true);
            GameObject loadGo = new GameObject("GameLoadingScreen_Runtime", typeof(RectTransform));
            if (canvas != null) loadGo.transform.SetParent(canvas.transform, false);
            ls = loadGo.AddComponent<GameLoadingScreen>();
        }
        ls.Initialize(font);
    }

    private void EnsureGenerateCaseModal()
    {
        GenerateCaseModal m = GenerateCaseModal.Instance ?? FindObjectOfType<GenerateCaseModal>(true);
        if (m == null)
        {
            Canvas canvas = GetComponentInParent<Canvas>() ?? FindObjectOfType<Canvas>(true);
            GameObject genGo = new GameObject("GenerateCase_Modal", typeof(RectTransform));
            if (canvas != null) genGo.transform.SetParent(canvas.transform, false);
            m = genGo.AddComponent<GenerateCaseModal>();
        }
        if (m != null)
        {
            m.gameObject.SetActive(true);
            m.Initialize(font);
        }
    }

    private void EnsureAPIManager()
    {
        if (DetectiveAPIManager.Instance == null && FindObjectOfType<DetectiveAPIManager>() == null)
        {
            GameObject apiGo = new GameObject("DetectiveAPIManager_Runtime");
            apiGo.AddComponent<DetectiveAPIManager>();
        }
    }

    private void EnsureAudioManager()
    {
        if (FindObjectOfType<AudioManager>() == null)
        {
            GameObject audioGo = new GameObject("AudioManager_Runtime");
            audioGo.AddComponent<AudioManager>();
        }
    }

    private void EnsureAshtrayProp()
    {
        if (FindObjectOfType<AshtrayPropController>() == null)
        {
            Transform desk = GameObject.Find("Layer_2_DetectiveDesk")?.transform;
            if (desk != null)
            {
                GameObject ashtrayGo = new GameObject("Ashtray_Prop", typeof(RectTransform));
                ashtrayGo.transform.SetParent(desk, false);
                ashtrayGo.AddComponent<AshtrayPropController>();
            }
        }
    }

    public void Toggle()
    {
        if (IsOpen) Close();
        else Open();
    }

    public void Open()
    {
        if (root == null) BuildUI();
        transform.SetAsLastSibling();

        // Ensure in-game HUD taskbar visuals are hidden while in Main Menu (without killing taskbar GameObject!)
        HotkeyTaskbar.Instance?.SetTaskbarVisuals(false);

        ShowMainMenuButtons();
        if (root != null) root.gameObject.SetActive(true);
    }

    public void Close()
    {
        if (root != null) root.gameObject.SetActive(false);
    }

    private void Update()
    {
        if (IsOpen)
        {
#if ENABLE_INPUT_SYSTEM
            if (UnityEngine.InputSystem.Keyboard.current != null && UnityEngine.InputSystem.Keyboard.current.escapeKey.wasPressedThisFrame)
            {
                if (IsInSubPanel) ShowMainMenuButtons();
            }
#else
            if (Input.GetKeyDown(KeyCode.Escape))
            {
                if (IsInSubPanel) ShowMainMenuButtons();
            }
#endif
        }
    }

    public void StartGameWithCase(CaseDossier dossier)
    {
        Close();

        // Show in-game HUD taskbar
        HotkeyTaskbar.Instance?.SetTaskbarVisuals(true);

        // Load case into investigation corkboard
        GameController controller = GameController.Instance ?? FindObjectOfType<GameController>();
        controller?.LoadCaseFromData(dossier);
    }

    private void ShowMainMenuButtons()
    {
        if (mainButtonGroup != null) mainButtonGroup.SetActive(true);
        if (newGameSubPanel != null) newGameSubPanel.SetActive(false);
        if (loadSaveSubPanel != null) loadSaveSubPanel.SetActive(false);
        if (coopSubPanel != null) coopSubPanel.SetActive(false);
    }

    private void BuildUI()
    {
        Canvas canvas = GetComponentInParent<Canvas>() ?? FindObjectOfType<Canvas>(true);
        if (canvas == null) return;
        if (transform.parent != canvas.transform)
        {
            transform.SetParent(canvas.transform, false);
        }

        // Fullscreen Background Overlay
        GameObject rootGo = new GameObject("TitleMenuModal_Root", typeof(RectTransform), typeof(Image));
        root = rootGo.GetComponent<RectTransform>();
        root.SetParent(canvas.transform, false);
        root.anchorMin = Vector2.zero;
        root.anchorMax = Vector2.one;
        root.sizeDelta = Vector2.zero;
        rootGo.GetComponent<Image>().color = OverlayColor;

        // Central Card Panel
        GameObject panelGo = new GameObject("CenterPanel", typeof(RectTransform), typeof(Image));
        RectTransform panel = panelGo.GetComponent<RectTransform>();
        panel.SetParent(root, false);
        panel.anchorMin = new Vector2(0.5f, 0.5f);
        panel.anchorMax = new Vector2(0.5f, 0.5f);
        panel.pivot = new Vector2(0.5f, 0.5f);
        panel.sizeDelta = new Vector2(580f, 620f);
        panelGo.GetComponent<Image>().color = CardColor;

        // Header / Game Title
        GameObject headerGo = new GameObject("Header", typeof(RectTransform));
        RectTransform header = headerGo.GetComponent<RectTransform>();
        header.SetParent(panel, false);
        header.anchorMin = new Vector2(0f, 1f);
        header.anchorMax = new Vector2(1f, 1f);
        header.pivot = new Vector2(0.5f, 1f);
        header.anchoredPosition = new Vector2(0f, -22f);
        header.sizeDelta = new Vector2(0f, 140f);

        CreateText(headerGo.transform, "HỒ SƠ ÁN CHƯA CÓ LỜI GIẢI", 26, TitleGold, FontStyle.Bold, new Vector2(0f, 40f));
        CreateText(headerGo.transform, "UNSOLVED CASE FILES AI — HỆ THỐNG TRINH THÁM TỰ ĐỘNG", 13, TextWhite, FontStyle.Normal, new Vector2(0f, 12f));
        CreateText(headerGo.transform, "Đồ án Tốt nghiệp CNTT — Phenikaa University | Dr. Tánh Nguyễn & SV. Nguyễn Ngọc Công Anh", 11, TextMuted, FontStyle.Italic, new Vector2(0f, -14f));

        // 1. MAIN BUTTON GROUP (5 CORE BUTTONS)
        mainButtonGroup = new GameObject("MainButtonGroup", typeof(RectTransform), typeof(VerticalLayoutGroup));
        RectTransform btnRect = mainButtonGroup.GetComponent<RectTransform>();
        btnRect.SetParent(panel, false);
        btnRect.anchorMin = new Vector2(0.1f, 0.08f);
        btnRect.anchorMax = new Vector2(0.9f, 0.72f);
        btnRect.sizeDelta = Vector2.zero;

        VerticalLayoutGroup vlg = mainButtonGroup.GetComponent<VerticalLayoutGroup>();
        vlg.spacing = 11f;
        vlg.childControlWidth = true;
        vlg.childControlHeight = true;
        vlg.childForceExpandHeight = false;

        // Button 1: Chơi Mới
        CreateMenuButton(mainButtonGroup.transform, "▶️  CHƠI MỚI", "Bắt đầu vụ án mẫu hoặc tạo mới bằng AI", BtnPrimary, () =>
        {
            mainButtonGroup.SetActive(false);
            if (newGameSubPanel != null) newGameSubPanel.SetActive(true);
        });

        // Button 2: Mở File Save
        CreateMenuButton(mainButtonGroup.transform, "📂  MỞ FILE SAVE (TIẾP TỤC)", "Xem danh sách hồ sơ vụ án đã lưu trên máy", BtnSecondary, () =>
        {
            mainButtonGroup.SetActive(false);
            if (loadSaveSubPanel != null)
            {
                loadSaveSubPanel.SetActive(true);
                PopulateSaveList();
            }
        });

        // Button 3: Chơi Coop (LAN)
        CreateMenuButton(mainButtonGroup.transform, "👥  CHƠI CO-OP (LAN / ONLINE)", "Tạo phòng mới hoặc tham gia phòng đồng đội", BtnSecondary, () =>
        {
            mainButtonGroup.SetActive(false);
            if (coopSubPanel != null) coopSubPanel.SetActive(true);
        });

        // Button 4: Cài Đặt (5 Tab)
        CreateMenuButton(mainButtonGroup.transform, "⚙️  CÀI ĐẶT", "Giao diện, âm thanh, điều khiển, hướng dẫn, mô hình AI", BtnSecondary, () =>
        {
            // Hide main menu while in settings to eliminate overlapping
            Close();
            FindObjectOfType<SettingsModal>()?.Open();
        });

        // Button 5: Thoát
        CreateMenuButton(mainButtonGroup.transform, "❌  THOÁT GAME", "Đóng trò chơi", BtnDanger, () =>
        {
#if UNITY_EDITOR
            UnityEditor.EditorApplication.isPlaying = false;
#else
            Application.Quit();
#endif
        });

        // BUILD SUB-PANELS
        BuildNewGameSubPanel(panel);
        BuildLoadSaveSubPanel(panel);
        BuildCoopSubPanel(panel);
    }

    // -------------------------------------------------------------------------
    // SUB-PANEL: CHƠI MỚI (NEW GAME)
    // -------------------------------------------------------------------------
    private void BuildNewGameSubPanel(Transform panel)
    {
        newGameSubPanel = new GameObject("SubPanel_NewGame", typeof(RectTransform));
        RectTransform rt = newGameSubPanel.GetComponent<RectTransform>();
        rt.SetParent(panel, false);
        rt.anchorMin = new Vector2(0.1f, 0.08f);
        rt.anchorMax = new Vector2(0.9f, 0.72f);
        rt.sizeDelta = Vector2.zero;

        VerticalLayoutGroup vlg = newGameSubPanel.AddComponent<VerticalLayoutGroup>();
        vlg.spacing = 12f;
        vlg.childControlWidth = true;
        vlg.childControlHeight = true;
        vlg.childForceExpandHeight = false;

        CreateMenuButton(newGameSubPanel.transform, "📜  VỤ ÁN MẪU (CHƠI NGAY)", "Hồ sơ mẫu Nam Định / Đà Lạt đã xác thực logic y pháp", BtnPrimary, () =>
        {
            Close();
            EnsureLoadingScreen();
            GameLoadingScreen.Instance?.Show("ĐANG NẠP HỒ SƠ VỤ ÁN MẪU...");
            StartCoroutine(LoadSampleRoutine());
        });

        CreateMenuButton(newGameSubPanel.transform, "✨  SINH VỤ ÁN MỚI BẰNG AI", "Tùy biến bối cảnh Việt Nam / Nhật Bản / Phòng kín", BtnSecondary, () =>
        {
            EnsureGenerateCaseModal();
            GenerateCaseModal modal = GenerateCaseModal.Instance ?? FindObjectOfType<GenerateCaseModal>(true);
            if (modal != null)
            {
                Close();
                modal.Open();
            }
            else
            {
                Debug.LogError("[TitleMenuModal] Could not find or instantiate GenerateCaseModal!");
            }
        });

        CreateMenuButton(newGameSubPanel.transform, "↩️  QUAY LẠI MENU CHÍNH", "Quay lại danh mục trước", BtnDanger, ShowMainMenuButtons);

        newGameSubPanel.SetActive(false);
    }

    private System.Collections.IEnumerator LoadSampleRoutine()
    {
        yield return new WaitForSeconds(0.6f);

        DetectiveAPIManager api = DetectiveAPIManager.Instance ?? FindObjectOfType<DetectiveAPIManager>();
        if (api == null)
        {
            EnsureAPIManager();
            api = DetectiveAPIManager.Instance;
        }

        api?.GetSampleCase((success, dossier) =>
        {
            GameLoadingScreen.Instance?.Hide();
            if (success && dossier != null)
            {
                StartGameWithCase(dossier);
            }
            else
            {
                Open();
            }
        });
    }

    // -------------------------------------------------------------------------
    // SUB-PANEL: MỞ FILE SAVE (LOAD GAME)
    // -------------------------------------------------------------------------
    private void BuildLoadSaveSubPanel(Transform panel)
    {
        loadSaveSubPanel = new GameObject("SubPanel_LoadSave", typeof(RectTransform));
        RectTransform rt = loadSaveSubPanel.GetComponent<RectTransform>();
        rt.SetParent(panel, false);
        rt.anchorMin = new Vector2(0.08f, 0.08f);
        rt.anchorMax = new Vector2(0.92f, 0.72f);
        rt.sizeDelta = Vector2.zero;

        // Title
        CreateText(loadSaveSubPanel.transform, "DANH SÁCH VỤ ÁN ĐÃ LƯU", 15, TitleGold, FontStyle.Bold, new Vector2(0f, 150f));

        // Scroll view for saves
        GameObject scrollGo = new GameObject("ScrollArea", typeof(RectTransform), typeof(ScrollRect), typeof(Image));
        RectTransform srt = scrollGo.GetComponent<RectTransform>();
        srt.SetParent(loadSaveSubPanel.transform, false);
        srt.anchoredPosition = new Vector2(0f, 15f);
        srt.sizeDelta = new Vector2(460f, 220f);
        scrollGo.GetComponent<Image>().color = new Color(0.06f, 0.06f, 0.08f, 0.9f);

        GameObject contentGo = new GameObject("Content", typeof(RectTransform), typeof(VerticalLayoutGroup), typeof(ContentSizeFitter));
        RectTransform crt = contentGo.GetComponent<RectTransform>();
        crt.SetParent(scrollGo.transform, false);
        crt.anchorMin = new Vector2(0f, 1f);
        crt.anchorMax = new Vector2(1f, 1f);
        crt.pivot = new Vector2(0.5f, 1f);
        crt.sizeDelta = new Vector2(0f, 0f);

        VerticalLayoutGroup vlg = contentGo.GetComponent<VerticalLayoutGroup>();
        vlg.spacing = 6f;
        vlg.childControlWidth = true;
        vlg.childControlHeight = true;
        vlg.childForceExpandHeight = false;

        ContentSizeFitter csf = contentGo.GetComponent<ContentSizeFitter>();
        csf.verticalFit = ContentSizeFitter.FitMode.PreferredSize;

        ScrollRect sr = scrollGo.GetComponent<ScrollRect>();
        sr.content = crt;
        sr.horizontal = false;
        sr.vertical = true;
        saveListContainer = contentGo.transform;

        // Back button
        GameObject backBtnGo = new GameObject("BackBtn", typeof(RectTransform));
        RectTransform brt = backBtnGo.GetComponent<RectTransform>();
        brt.SetParent(loadSaveSubPanel.transform, false);
        brt.anchoredPosition = new Vector2(0f, -145f);
        brt.sizeDelta = new Vector2(460f, 40f);
        CreateMenuButton(backBtnGo.transform, "↩️  QUAY LẠI MENU CHÍNH", "", BtnDanger, ShowMainMenuButtons);

        loadSaveSubPanel.SetActive(false);
    }

    private void PopulateSaveList()
    {
        if (saveListContainer == null) return;

        // Clear previous
        foreach (Transform child in saveListContainer)
        {
            Destroy(child.gameObject);
        }

        string saveDir = Path.Combine(Application.persistentDataPath, "saves");
        if (Directory.Exists(saveDir))
        {
            string[] files = Directory.GetFiles(saveDir, "*.json");
            if (files.Length > 0)
            {
                foreach (string filePath in files)
                {
                    try
                    {
                        string json = File.ReadAllText(filePath);
                        CaseDossier d = JsonUtility.FromJson<CaseDossier>(json);
                        if (d != null)
                        {
                            string caseTitle = string.IsNullOrEmpty(d.title) ? Path.GetFileNameWithoutExtension(filePath) : d.title;
                            CreateSaveItem(saveListContainer, caseTitle, d);
                        }
                    }
                    catch { }
                }
                return;
            }
        }

        // No saves found placeholder
        CreateText(saveListContainer, "Chưa có file lưu nào trong máy.\nHãy bắt đầu 'Chơi mới' và lưu tiến độ!", 13, TextMuted, FontStyle.Italic, Vector2.zero);
    }

    private void CreateSaveItem(Transform parent, string title, CaseDossier dossier)
    {
        GameObject itemGo = new GameObject("SaveItem_" + dossier.case_id, typeof(RectTransform), typeof(Image), typeof(Button));
        itemGo.transform.SetParent(parent, false);

        LayoutElement le = itemGo.AddComponent<LayoutElement>();
        le.minHeight = 44f;
        le.preferredHeight = 44f;

        itemGo.GetComponent<Image>().color = new Color(0.16f, 0.17f, 0.20f);
        Button btn = itemGo.GetComponent<Button>();
        btn.onClick.AddListener(() => StartGameWithCase(dossier));

        GameObject textGo = new GameObject("Text", typeof(RectTransform), typeof(Text));
        RectTransform rt = textGo.GetComponent<RectTransform>();
        rt.SetParent(itemGo.transform, false);
        rt.anchorMin = Vector2.zero;
        rt.anchorMax = Vector2.one;
        rt.offsetMin = new Vector2(12f, 2f);
        rt.offsetMax = new Vector2(-12f, -2f);

        Text txt = textGo.GetComponent<Text>();
        txt.font = font ?? Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
        txt.fontSize = 13;
        txt.color = TextWhite;
        txt.alignment = TextAnchor.MiddleLeft;
        txt.text = $"📁 <b>{title}</b>\n<size=10><color=#999999>Mã vụ án: {dossier.case_id}</color></size>";
        txt.supportRichText = true;
    }

    // -------------------------------------------------------------------------
    // SUB-PANEL: CHƠI CO-OP (LAN)
    // -------------------------------------------------------------------------
    private void BuildCoopSubPanel(Transform panel)
    {
        coopSubPanel = new GameObject("SubPanel_Coop", typeof(RectTransform));
        RectTransform rt = coopSubPanel.GetComponent<RectTransform>();
        rt.SetParent(panel, false);
        rt.anchorMin = new Vector2(0.1f, 0.08f);
        rt.anchorMax = new Vector2(0.9f, 0.72f);
        rt.sizeDelta = Vector2.zero;

        VerticalLayoutGroup vlg = coopSubPanel.AddComponent<VerticalLayoutGroup>();
        vlg.spacing = 12f;
        vlg.childControlWidth = true;
        vlg.childControlHeight = true;
        vlg.childForceExpandHeight = false;

        CreateMenuButton(coopSubPanel.transform, "🏠  TẠO PHÒNG MỚI (LÀM HOST)", "Mở phòng điều tra để đồng đội tham gia (Voice Chat)", BtnPrimary, () =>
        {
            Close();
            FindObjectOfType<LanLobbyModal>()?.Open();
        });

        CreateMenuButton(coopSubPanel.transform, "🔍  VÀO PHÒNG CÓ SẴN (GUEST)", "Quét mạng LAN tự động hoặc nhập mã phòng", BtnSecondary, () =>
        {
            Close();
            FindObjectOfType<LanLobbyModal>()?.Open();
        });

        CreateMenuButton(coopSubPanel.transform, "↩️  QUAY LẠI MENU CHÍNH", "Quay lại danh mục trước", BtnDanger, ShowMainMenuButtons);

        coopSubPanel.SetActive(false);
    }

    private void CreateMenuButton(Transform parent, string title, string subtext, Color bgColor, System.Action onClick)
    {
        GameObject btnGo = new GameObject("Btn_" + title, typeof(RectTransform), typeof(Image), typeof(Button));
        btnGo.transform.SetParent(parent, false);

        LayoutElement le = btnGo.AddComponent<LayoutElement>();
        le.minHeight = 50f;
        le.preferredHeight = 50f;

        btnGo.GetComponent<Image>().color = bgColor;
        Button btn = btnGo.GetComponent<Button>();
        btn.onClick.AddListener(() => onClick?.Invoke());

        GameObject textGo = new GameObject("Text", typeof(RectTransform), typeof(Text));
        RectTransform rt = textGo.GetComponent<RectTransform>();
        rt.SetParent(btnGo.transform, false);
        rt.anchorMin = Vector2.zero;
        rt.anchorMax = Vector2.one;
        rt.offsetMin = new Vector2(16f, 4f);
        rt.offsetMax = new Vector2(-16f, -4f);

        Text txt = textGo.GetComponent<Text>();
        txt.font = font ?? Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
        txt.fontSize = 14;
        txt.fontStyle = FontStyle.Bold;
        txt.color = TextWhite;
        txt.alignment = TextAnchor.MiddleLeft;
        txt.text = string.IsNullOrEmpty(subtext) ? title : $"{title}\n<size=10><color=#a8a8a8>{subtext}</color></size>";
        txt.supportRichText = true;
    }

    private void CreateText(Transform parent, string content, int size, Color color, FontStyle style, Vector2 offset)
    {
        GameObject go = new GameObject("Text", typeof(RectTransform), typeof(Text));
        RectTransform rt = go.GetComponent<RectTransform>();
        rt.SetParent(parent, false);
        rt.anchoredPosition = offset;
        rt.sizeDelta = new Vector2(540f, 32f);

        Text txt = go.GetComponent<Text>();
        txt.font = font ?? Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
        txt.fontSize = size;
        txt.color = color;
        txt.fontStyle = style;
        txt.alignment = TextAnchor.MiddleCenter;
        txt.text = content;
    }
}
