using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// "Sổ tay Thám tử - Hướng dẫn Chơi" Dialog:
/// Hiển thị quy trình phá án 4 bước, cách tương tác với các đạo cụ (đèn bàn, dây chỉ đỏ, hồ sơ),
/// và bảng tra cứu phím tắt nhanh.
/// Xây dựng UGUI động tự động tương thích 16:9.
/// </summary>
public class HelpTutorialModal : MonoBehaviour
{
    private static readonly Color PanelColor = new Color(0.08f, 0.08f, 0.09f, 0.98f);
    private static readonly Color StepCardColor = new Color(0.13f, 0.13f, 0.15f, 1f);
    private static readonly Color TextColor = new Color(0.92f, 0.90f, 0.84f);
    private static readonly Color HighlightColor = new Color(0.95f, 0.82f, 0.40f);
    private static readonly Color MutedColor = new Color(0.65f, 0.65f, 0.60f);
    private static readonly Color CloseColor = new Color(0.45f, 0.18f, 0.18f);

    private Font font;
    private RectTransform root;

    public static HelpTutorialModal Instance { get; private set; }
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
        root.gameObject.SetActive(true);
    }

    public void Close()
    {
        if (root != null) root.gameObject.SetActive(false);
    }

    // ------------------------------------------------------------------
    // UI Construction
    // ------------------------------------------------------------------

    private void BuildUI()
    {
        root = NewRect("Help_Modal_Root", transform);
        Stretch(root);
        Image backdrop = root.gameObject.AddComponent<Image>();
        backdrop.color = new Color(0, 0, 0, 0.75f);

        RectTransform panel = NewRect("Panel", root);
        panel.anchorMin = panel.anchorMax = new Vector2(0.5f, 0.5f);
        panel.sizeDelta = new Vector2(760, 580);
        panel.gameObject.AddComponent<Image>().color = PanelColor;

        VerticalLayoutGroup layout = panel.gameObject.AddComponent<VerticalLayoutGroup>();
        layout.padding = new RectOffset(26, 26, 20, 20);
        layout.spacing = 10;
        layout.childControlWidth = true;
        layout.childControlHeight = true;
        layout.childForceExpandWidth = true;
        layout.childForceExpandHeight = false;

        // Title
        CreateLabel(panel, "🕵️ SỔ TAY THÁM TỬ - HƯỚNG DẪN ĐIỀU TRA & PHÁ ÁN", 19, HighlightColor, FontStyle.Bold, 26);
        CreateLabel(panel, "Chào mừng Thám tử! Hãy làm theo quy trình phá án khoa học 4 bước để vạch trần hung thủ thật sự:", 12, TextColor, FontStyle.Normal, 18);

        // --- STEP 1 & 2 ROW ---
        RectTransform row1 = NewRect("Row1", panel);
        row1.gameObject.AddComponent<LayoutElement>().preferredHeight = 115;
        HorizontalLayoutGroup hl1 = row1.gameObject.AddComponent<HorizontalLayoutGroup>();
        hl1.spacing = 10;
        hl1.childControlWidth = true;
        hl1.childControlHeight = true;
        hl1.childForceExpandWidth = true;

        CreateStepCard(row1, "1. KHÁM NGHIỆM PHÁP Y (TOD)", 
            "• Mở cặp hồ sơ Kraft để xem Báo cáo Tử thi.\n• Xem đồ thị nhiệt Henssge để xác định Cửa sổ tử vong (TOD Window) của nạn nhân.");

        CreateStepCard(row1, "2. RÀ SOÁT ALIBI NGHI PHẠM", 
            "• Click vào từng thẻ ảnh Polaroid nghi phạm.\n• Đọc lời khai ngoại phạm (Alibi), so khớp giờ có mặt với Cửa sổ tử vong TOD.");

        // --- STEP 3 & 4 ROW ---
        RectTransform row2 = NewRect("Row2", panel);
        row2.gameObject.AddComponent<LayoutElement>().preferredHeight = 115;
        HorizontalLayoutGroup hl2 = row2.gameObject.AddComponent<HorizontalLayoutGroup>();
        hl2.spacing = 10;
        hl2.childControlWidth = true;
        hl2.childControlHeight = true;
        hl2.childForceExpandWidth = true;

        CreateStepCard(row2, "3. TÌM CHỨNG CỨ BẺ ALIBI", 
            "• Click các thẻ vật chứng hiện trường.\n• Tìm chứng cứ then chốt mâu thuẫn trực tiếp với alibi của kẻ nói dối trong giờ chết.");

        CreateStepCard(row2, "4. NỘP LỆNH BẮT GIỮ", 
            "• Mở Lệnh bắt giữ (bìa da đỏ đô bên dưới).\n• Chọn đúng Hung thủ + Tick ít nhất 1 chứng cứ then chốt bẻ alibi rồi bấm Nộp!");

        // --- SPECIAL PROPS & HOTKEYS ---
        CreateLabel(panel, "💡 TƯƠNG TÁC ĐẠO CỤ & BẢNG PHÍM TẮT NHANH (HOTKEYS)", 13, HighlightColor, FontStyle.Bold, 20);

        RectTransform infoBox = NewRect("InfoBox", panel);
        infoBox.gameObject.AddComponent<LayoutElement>().preferredHeight = 110;
        infoBox.gameObject.AddComponent<Image>().color = StepCardColor;
        VerticalLayoutGroup ibLayout = infoBox.gameObject.AddComponent<VerticalLayoutGroup>();
        ibLayout.padding = new RectOffset(16, 16, 8, 8);
        ibLayout.spacing = 3;
        ibLayout.childControlWidth = true;
        ibLayout.childControlHeight = true;

        CreateLabel(infoBox, "• NỐI CHỈ ĐỎ THỦ CÔNG: Bấm vào Đinh ghim trên thẻ A rồi bấm vào Đinh ghim thẻ B để nối dây. Bấm lại để gỡ.", 12, new Color(1f, 0.45f, 0.45f), FontStyle.Normal, 16);
        CreateLabel(infoBox, "• PHÓNG TO ẢNH: Bấm trực tiếp vào ảnh Polaroid trên bảng (hoặc Chuột phải vào thẻ) để zoom Lightbox.", 12, new Color(0.95f, 0.85f, 0.45f), FontStyle.Normal, 16);
        CreateLabel(infoBox, "• ĐÈN BÀN BANKER: Bấm chuột trực tiếp vào chao đèn ngọc bích để bật/tắt đèn tạo không khí Noir.", 12, TextColor, FontStyle.Normal, 16);
        CreateLabel(infoBox, "• PHÍM TẮT: O = Cài đặt | N = Đổi nhạc Conan | H = Sổ tay | T = Chat | ESC = Menu / Đóng cửa sổ", 12, MutedColor, FontStyle.Normal, 16);

        // --- CLOSE BUTTON ---
        RectTransform btnRow = NewRect("BtnRow", panel);
        btnRow.gameObject.AddComponent<LayoutElement>().preferredHeight = 38;
        HorizontalLayoutGroup brLayout = btnRow.gameObject.AddComponent<HorizontalLayoutGroup>();
        brLayout.childControlWidth = true;
        brLayout.childControlHeight = true;
        brLayout.childForceExpandWidth = true;

        Button closeBtn = CreateButton(btnRow, "ĐÃ HIỂU - BẮT ĐẦU PHÁ ÁN (ESC)", new Color(0.18f, 0.48f, 0.35f), 38);
        closeBtn.onClick.AddListener(Close);
    }

    private void CreateStepCard(Transform parent, string header, string body)
    {
        RectTransform card = NewRect("StepCard", parent);
        card.gameObject.AddComponent<Image>().color = StepCardColor;
        VerticalLayoutGroup cardLayout = card.gameObject.AddComponent<VerticalLayoutGroup>();
        cardLayout.padding = new RectOffset(14, 14, 10, 10);
        cardLayout.spacing = 4;
        cardLayout.childControlWidth = true;
        cardLayout.childControlHeight = true;

        CreateLabel(card, header, 13, new Color(0.55f, 0.88f, 0.65f), FontStyle.Bold, 20);
        CreateLabel(card, body, 11, TextColor, FontStyle.Normal, 65);
    }

    private RectTransform NewRect(string name, Transform parent)
    {
        var go = new GameObject(name, typeof(RectTransform));
        go.layer = gameObject.layer;
        go.transform.SetParent(parent, false);
        return (RectTransform)go.transform;
    }

    private void Stretch(RectTransform rt)
    {
        rt.anchorMin = Vector2.zero;
        rt.anchorMax = Vector2.one;
        rt.offsetMin = Vector2.zero;
        rt.offsetMax = Vector2.zero;
    }

    private Text CreateLabel(Transform parent, string text, int size, Color color, FontStyle style, float height)
    {
        RectTransform rt = NewRect("Label", parent);
        if (height > 0) rt.gameObject.AddComponent<LayoutElement>().preferredHeight = height;
        Text t = rt.gameObject.AddComponent<Text>();
        t.font = font != null ? font : Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
        t.text = text;
        t.fontSize = size;
        t.color = color;
        t.fontStyle = style;
        t.alignment = TextAnchor.MiddleLeft;
        return t;
    }

    private Button CreateButton(Transform parent, string text, Color bg, float height)
    {
        RectTransform rt = NewRect("Btn_" + text, parent);
        if (height > 0) rt.gameObject.AddComponent<LayoutElement>().preferredHeight = height;
        rt.gameObject.AddComponent<Image>().color = bg;
        Button b = rt.gameObject.AddComponent<Button>();

        ColorBlock cb = b.colors;
        cb.normalColor = Color.white;
        cb.highlightedColor = new Color(1.15f, 1.15f, 1.15f, 1f);
        cb.pressedColor = new Color(0.85f, 0.85f, 0.85f, 1f);
        b.colors = cb;

        RectTransform labelRt = NewRect("Text", rt);
        Stretch(labelRt);
        Text t = labelRt.gameObject.AddComponent<Text>();
        t.font = font != null ? font : Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
        t.text = text;
        t.fontSize = 12;
        t.fontStyle = FontStyle.Bold;
        t.color = TextColor;
        t.alignment = TextAnchor.MiddleCenter;
        return b;
    }
}
