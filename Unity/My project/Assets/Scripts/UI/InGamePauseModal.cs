using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// Menu Tạm dừng khi Đang chơi Game (In-Game Pause Menu):
/// Mở bằng phím ESC hoặc nút trên thanh công cụ trong lúc điều tra.
/// Gồm: Tiếp tục, Lưu tiến độ, Cài đặt, và Về màn hình chính (kèm hộp thoại xác nhận lưu).
/// </summary>
public class InGamePauseModal : MonoBehaviour
{
    private static readonly Color OverlayColor = NoirUIStyle.BackdropScrim;
    private static readonly Color CardColor = NoirUIStyle.ModalSurface;
    private static readonly Color TitleGold = NoirUIStyle.BrassGold;
    private static readonly Color TextWhite = NoirUIStyle.CreamText;
    private static readonly Color TextMuted = NoirUIStyle.MutedText;

    private static readonly Color BtnPrimary = NoirUIStyle.EmeraldPrimary;
    private static readonly Color BtnSecondary = NoirUIStyle.SlateSecondary;
    private static readonly Color BtnDanger = NoirUIStyle.CrimsonDanger;

    private Font font;
    private RectTransform root;
    private GameObject confirmDialog;
    private Text toastText;

    public static InGamePauseModal Instance { get; private set; }
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
        transform.SetAsLastSibling();
        if (confirmDialog != null) confirmDialog.SetActive(false);
        if (toastText != null) toastText.text = "";
        gameObject.SetActive(true);
        root.gameObject.SetActive(true);
        NoirUIStyle.AnimateModalOpen(this, root.gameObject, root.Find("CenterPanel"));
    }

    public void Close()
    {
        if (root != null) root.gameObject.SetActive(false);
        gameObject.SetActive(false);
    }

    private void BuildUI()
    {
        Canvas canvas = GetComponentInParent<Canvas>() ?? FindObjectOfType<Canvas>(true);
        if (canvas == null) return;
        if (transform.parent != canvas.transform)
        {
            transform.SetParent(canvas.transform, false);
        }

        // Fullscreen Overlay
        GameObject rootGo = new GameObject("InGamePauseModal_Root", typeof(RectTransform), typeof(Image));
        root = rootGo.GetComponent<RectTransform>();
        root.SetParent(canvas.transform, false);
        root.anchorMin = Vector2.zero;
        root.anchorMax = Vector2.one;
        root.sizeDelta = Vector2.zero;
        rootGo.GetComponent<Image>().color = OverlayColor;

        // Center Panel
        GameObject panelGo = new GameObject("CenterPanel", typeof(RectTransform), typeof(Image));
        RectTransform panel = panelGo.GetComponent<RectTransform>();
        panel.SetParent(root, false);
        panel.anchorMin = new Vector2(0.5f, 0.5f);
        panel.anchorMax = new Vector2(0.5f, 0.5f);
        panel.pivot = new Vector2(0.5f, 0.5f);
        panel.sizeDelta = new Vector2(460f, 480f);
        panelGo.GetComponent<Image>().color = CardColor;
        NoirUIStyle.ApplyPanelChrome(panelGo, NoirUIStyle.BrassBorder, true);
        NoirUIStyle.CreateCornerCloseButton(panel, font, Close);

        // Title
        CreateText(panel, "TẠM DỪNG ĐIỀU TRA", 22, TitleGold, FontStyle.Bold, new Vector2(0f, 185f), new Vector2(400f, 32f));
        CreateText(panel, "Hồ sơ vụ án đang được giữ nguyên trên bảng", 12, TextMuted, FontStyle.Normal, new Vector2(0f, 155f), new Vector2(400f, 24f));

        // Toast feedback
        GameObject toastGo = new GameObject("ToastText", typeof(RectTransform), typeof(Text));
        RectTransform toastRt = toastGo.GetComponent<RectTransform>();
        toastRt.SetParent(panel, false);
        toastRt.anchoredPosition = new Vector2(0f, 128f);
        toastRt.sizeDelta = new Vector2(400f, 24f);
        toastText = toastGo.GetComponent<Text>();
        toastText.font = font ?? DetectiveAssetBank.GetDefaultUIFont();
        toastText.fontSize = 13;
        toastText.alignment = TextAnchor.MiddleCenter;
        toastText.color = NoirUIStyle.MintFeedback;
        toastText.text = "";

        // Buttons Group
        GameObject btnGroup = new GameObject("ButtonGroup", typeof(RectTransform), typeof(VerticalLayoutGroup));
        RectTransform btnRect = btnGroup.GetComponent<RectTransform>();
        btnRect.SetParent(panel, false);
        btnRect.anchorMin = new Vector2(0.1f, 0.08f);
        btnRect.anchorMax = new Vector2(0.9f, 0.68f);
        btnRect.sizeDelta = Vector2.zero;

        VerticalLayoutGroup vlg = btnGroup.GetComponent<VerticalLayoutGroup>();
        vlg.spacing = 10f;
        vlg.childControlWidth = true;
        vlg.childControlHeight = true;
        vlg.childForceExpandHeight = false;

        // 1. Resume
        CreateButton(btnGroup.transform, "TIẾP TỤC ĐIỀU TRA", BtnPrimary, Close);

        // 2. Save Game
        CreateButton(btnGroup.transform, "LƯU TIẾN ĐỘ VỤ ÁN", BtnSecondary, HandleSaveGame);

        // 3. Settings (Opens 5-tab SettingsModal, hides this Pause menu)
        CreateButton(btnGroup.transform, "CÀI ĐẶT HỆ THỐNG", BtnSecondary, () =>
        {
            Close();
            FindObjectOfType<SettingsModal>()?.Open();
        });

        // 4. Return to Main Menu
        CreateButton(btnGroup.transform, "VỀ MÀN HÌNH CHÍNH", BtnDanger, () =>
        {
            if (confirmDialog != null) confirmDialog.SetActive(true);
        });

        // Build Confirmation Sub-dialog ("Lưu & Thoát hay Chỉ Thoát?")
        BuildConfirmDialog(panel);
    }

    private void BuildConfirmDialog(Transform parent)
    {
        confirmDialog = new GameObject("ConfirmExitDialog", typeof(RectTransform), typeof(Image));
        RectTransform crt = confirmDialog.GetComponent<RectTransform>();
        crt.SetParent(parent, false);
        crt.anchorMin = Vector2.zero;
        crt.anchorMax = Vector2.one;
        crt.sizeDelta = Vector2.zero;
        confirmDialog.GetComponent<Image>().color = new Color(0.06f, 0.055f, 0.05f, 0.98f);

        CreateText(confirmDialog.transform, "XÁC NHẬN RỜI PHÒNG ĐIỀU TRA", 18, TitleGold, FontStyle.Bold, new Vector2(0f, 130f), new Vector2(400f, 30f));
        CreateText(confirmDialog.transform, "Bạn có muốn lưu lại tiến độ hiện tại\ntrước khi trở về màn hình chính không?", 13, TextWhite, FontStyle.Normal, new Vector2(0f, 70f), new Vector2(380f, 50f));

        GameObject group = new GameObject("ConfirmBtnGroup", typeof(RectTransform), typeof(VerticalLayoutGroup));
        RectTransform grt = group.GetComponent<RectTransform>();
        grt.SetParent(confirmDialog.transform, false);
        grt.anchorMin = new Vector2(0.12f, 0.1f);
        grt.anchorMax = new Vector2(0.88f, 0.52f);
        grt.sizeDelta = Vector2.zero;

        VerticalLayoutGroup vlg = group.GetComponent<VerticalLayoutGroup>();
        vlg.spacing = 10f;
        vlg.childControlWidth = true;
        vlg.childControlHeight = true;
        vlg.childForceExpandHeight = false;

        // [Lưu & Thoát]
        CreateButton(group.transform, "LƯU VÀ THOÁT VỀ MENU", BtnPrimary, () =>
        {
            HandleSaveGame();
            ExitToMainMenu();
        });

        // [Chỉ Thoát]
        CreateButton(group.transform, "CHỈ THOÁT (KHÔNG LƯU)", BtnDanger, ExitToMainMenu);

        // [Hủy]
        CreateButton(group.transform, "HỦY (TIẾP TỤC PHÁ ÁN)", BtnSecondary, () =>
        {
            if (confirmDialog != null) confirmDialog.SetActive(false);
        });

        confirmDialog.SetActive(false);
    }

    private void HandleSaveGame()
    {
        CaseDossier current = FindObjectOfType<GameController>()?.currentCase;
        if (current != null)
        {
            // Persist to local JSON file in persistentDataPath/saves/
            string saveDir = System.IO.Path.Combine(Application.persistentDataPath, "saves");
            System.IO.Directory.CreateDirectory(saveDir);
            string savePath = System.IO.Path.Combine(saveDir, $"{current.case_id}.json");
            string json = JsonUtility.ToJson(current, true);
            System.IO.File.WriteAllText(savePath, json);

            if (toastText != null)
            {
                toastText.text = $"Đã lưu hồ sơ '{current.title}' thành công.";
            }
        }
        else
        {
            if (toastText != null) toastText.text = "Không có vụ án nào đang mở để lưu.";
        }
    }

    private void ExitToMainMenu()
    {
        Close();

        // 1. Clear Corkboard cards and strings
        FindObjectOfType<CorkboardManager>()?.ClearBoard();

        // 2. Hide In-game taskbar visuals
        HotkeyTaskbar.Instance?.SetTaskbarVisuals(false);

        // 3. Switch BGM to noir / title theme
        AudioManager.Instance?.SwitchTrack(AudioManager.BgmTrack.NoirJazz);

        // 4. Open Main Menu Title Screen
        FindObjectOfType<TitleMenuModal>()?.Open();
    }

    private void CreateButton(Transform parent, string label, Color bgColor, System.Action onClick)
    {
        GameObject btnGo = new GameObject("Btn_" + label, typeof(RectTransform), typeof(Image), typeof(Button));
        btnGo.transform.SetParent(parent, false);

        LayoutElement le = btnGo.AddComponent<LayoutElement>();
        le.minHeight = 44f;
        le.preferredHeight = 44f;

        btnGo.GetComponent<Image>().color = bgColor;
        Button btn = btnGo.GetComponent<Button>();
        btn.onClick.AddListener(() => onClick?.Invoke());
        NoirUIStyle.AttachButtonFeel(btn, 0.97f, true);

        GameObject textGo = new GameObject("Text", typeof(RectTransform), typeof(Text));
        RectTransform rt = textGo.GetComponent<RectTransform>();
        rt.SetParent(btnGo.transform, false);
        rt.anchorMin = Vector2.zero;
        rt.anchorMax = Vector2.one;
        rt.sizeDelta = Vector2.zero;

        Text txt = textGo.GetComponent<Text>();
        txt.font = font ?? DetectiveAssetBank.GetDefaultUIFont();
        txt.fontSize = 14;
        txt.fontStyle = FontStyle.Bold;
        txt.color = TextWhite;
        txt.alignment = TextAnchor.MiddleCenter;
        txt.text = label;
    }

    private void CreateText(Transform parent, string text, int size, Color color, FontStyle style, Vector2 pos, Vector2 sizeDelta)
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
        txt.alignment = TextAnchor.MiddleCenter;
        txt.text = text;
    }
}
