using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// Tờ Giới Thiệu Vụ Án & Báo Cáo Hiện Trường Sơ Bộ (Case Briefing & Initial Police Report)
/// Chuẩn phong cách hồ sơ giấy của dòng game Unsolved Case Files.
/// </summary>
public class CaseBriefingModal : MonoBehaviour
{
    private static CaseBriefingModal _instance;
    public static CaseBriefingModal Instance
    {
        get
        {
            if (_instance == null)
            {
#if UNITY_2023_1_OR_NEWER
                _instance = FindAnyObjectByType<CaseBriefingModal>(FindObjectsInactive.Include);
#else
                _instance = FindObjectOfType<CaseBriefingModal>(true);
#endif
                if (_instance == null)
                {
                    GameObject go = new GameObject("CaseBriefingModal");
                    _instance = go.AddComponent<CaseBriefingModal>();
                }
            }
            return _instance;
        }
        private set => _instance = value;
    }

    private GameObject paperRootGo;
    private RectTransform paperSheetRt;
    private Font uiFont;

    public bool IsOpen => paperRootGo != null && paperRootGo.activeSelf;

    private static readonly Color PaperColor = new Color(0.96f, 0.94f, 0.89f, 1.0f);
    private static readonly Color PaperBorder = new Color(0.24f, 0.20f, 0.16f, 0.95f);
    private static readonly Color OverlayDim = new Color(0.04f, 0.04f, 0.06f, 0.85f);
    private static readonly Color InkBlack = new Color(0.12f, 0.12f, 0.14f, 1.0f);
    private static readonly Color InkRed = new Color(0.78f, 0.18f, 0.18f, 1.0f);
    private static readonly Color InkBlue = new Color(0.12f, 0.32f, 0.58f, 1.0f);
    private static readonly Color InkMuted = new Color(0.38f, 0.38f, 0.40f, 1.0f);
    private static readonly Color TableBg = new Color(0.91f, 0.88f, 0.82f, 0.85f);

    private void Awake()
    {
        _instance = this;
        Image selfBg = GetComponent<Image>();
        if (selfBg != null)
        {
            selfBg.enabled = false;
            selfBg.raycastTarget = false;
        }
    }

    public void Open()
    {
        gameObject.SetActive(true);
        EnsurePaperRoot();
        BuildBriefingDocument();
        paperRootGo.SetActive(true);
        transform.SetAsLastSibling();
        paperRootGo.transform.SetAsLastSibling();
        NoirUIStyle.AnimateModalOpen(this, paperRootGo, paperSheetRt);
        Debug.Log("[CaseBriefingModal] Opened Case Briefing Dossier Sheet.");
    }

    public void Close()
    {
        if (paperRootGo != null)
        {
            paperRootGo.SetActive(false);
        }
        gameObject.SetActive(false);
    }

    private void EnsurePaperRoot()
    {
        if (paperRootGo != null) return;

        Canvas canvas = GetComponentInParent<Canvas>() ?? FindObjectOfType<Canvas>(true);
        if (canvas == null) return;

        // Overlay Dim
        paperRootGo = new GameObject("CaseBriefing_Overlay", typeof(RectTransform), typeof(Image));
        RectTransform ort = paperRootGo.GetComponent<RectTransform>();
        ort.SetParent(canvas.transform, false);
        ort.anchorMin = Vector2.zero;
        ort.anchorMax = Vector2.one;
        ort.sizeDelta = Vector2.zero;

        Image oImg = paperRootGo.GetComponent<Image>();
        oImg.color = OverlayDim;
        oImg.raycastTarget = true;

        Button overlayBtn = paperRootGo.AddComponent<Button>();
        overlayBtn.transition = Selectable.Transition.None;
        overlayBtn.onClick.AddListener(Close);

        // A4 Paper Sheet
        GameObject sheetGo = new GameObject("Paper_Sheet_Briefing", typeof(RectTransform), typeof(Image));
        paperSheetRt = sheetGo.GetComponent<RectTransform>();
        paperSheetRt.SetParent(paperRootGo.transform, false);
        paperSheetRt.anchorMin = new Vector2(0.5f, 0.5f);
        paperSheetRt.anchorMax = new Vector2(0.5f, 0.5f);
        paperSheetRt.sizeDelta = new Vector2(860f, 960f);

        Image sImg = sheetGo.GetComponent<Image>();
        sImg.color = PaperColor;
        sImg.raycastTarget = true;

        Outline outline = sheetGo.AddComponent<Outline>();
        outline.effectColor = PaperBorder;
        outline.effectDistance = new Vector2(2f, -2f);

        CreateCloseButton(paperSheetRt);
    }

    private void CreateCloseButton(RectTransform parent)
    {
        NoirUIStyle.CreateCornerCloseButton(parent, uiFont, Close);
    }

    private void ClearPaperContents()
    {
        if (paperSheetRt == null) return;
        foreach (Transform child in paperSheetRt)
        {
            if (child.name != "Btn_Close_Paper")
            {
                Destroy(child.gameObject);
            }
        }
    }

    private void BuildBriefingDocument()
    {
        ClearPaperContents();

        CaseDossier c = GameController.Instance != null ? GameController.Instance.currentCase : null;
        string caseTitle = c != null && !string.IsNullOrEmpty(c.title) ? c.title : "BÍ ẨN ÁN MẠNG TRANG VIÊN BLACKWOOD";
        string caseId = c != null && !string.IsNullOrEmpty(c.case_id) ? c.case_id : "CASE-2026-001";
        string victimName = c?.victim?.name ?? "Arthur Blackwood";
        string victimOcc = c?.victim?.occupation ?? "Chủ trang viên & Doanh nhân";
        string victimRes = c?.victim?.residence ?? "Biệt thự Blackwood Manor";
        string summaryText = c != null && !string.IsNullOrEmpty(c.summary) 
            ? c.summary 
            : "Vào rạng sáng ngày 16/11, cảnh sát hạt nhận được tin báo án mạng tại dinh thự Blackwood. Cửa thư phòng tầng 2 bị khóa chặt từ bên trong. Nạn nhân được phát hiện tử vong tại bàn làm việc với vết thương chí mạng ở ngực trái.";

        GameObject contentGo = new GameObject("Document_Content", typeof(RectTransform));
        RectTransform crt = contentGo.GetComponent<RectTransform>();
        crt.SetParent(paperSheetRt, false);
        crt.anchorMin = Vector2.zero;
        crt.anchorMax = Vector2.one;
        crt.offsetMin = new Vector2(28f, 22f);
        crt.offsetMax = new Vector2(-28f, -22f);

        // 1. Header: Cục cảnh sát & Mã văn bản
        GameObject headerGo = new GameObject("Header_Row", typeof(RectTransform));
        RectTransform hrt = headerGo.GetComponent<RectTransform>();
        hrt.SetParent(crt, false);
        hrt.anchorMin = new Vector2(0f, 0.90f);
        hrt.anchorMax = new Vector2(1f, 1.0f);
        hrt.sizeDelta = Vector2.zero;

        CreateText(headerGo.transform, new Vector2(0f, 0f), new Vector2(0.38f, 1f),
            "<b>METROPOLITAN POLICE DEPARTMENT</b>\n<size=10>CRIMINAL INVESTIGATION DIVISION // COLD CASE UNIT</size>\n<size=9>SPECIAL DIRECTIVE // FOR OFFICIAL USE ONLY</size>",
            TextAnchor.MiddleLeft, 11, InkBlack);

        CreateText(headerGo.transform, new Vector2(0.38f, 0f), new Vector2(0.72f, 1f),
            "<b><size=22>CASE BRIEFING SHEET</size></b>\n<size=11><b>TỜ BÀN GIAO & TỔNG QUAN HỒ SƠ ÁN MẠNG</b></size>",
            TextAnchor.MiddleCenter, 12, InkBlack);

        GameObject boxCode = CreateBox(headerGo.transform, new Vector2(0.74f, 0.05f), new Vector2(1.0f, 0.95f), TableBg, PaperBorder);
        CreateText(boxCode.transform, new Vector2(0.05f, 0.5f), new Vector2(0.95f, 0.95f),
            $"DOSSIER: <b>{caseId}</b>", TextAnchor.MiddleCenter, 10, InkBlack);
        CreateText(boxCode.transform, new Vector2(0.05f, 0.05f), new Vector2(0.95f, 0.55f),
            "<size=14><b>|| | |||| | ||| || |</b></size>", TextAnchor.MiddleCenter, 13, InkBlack);

        CreateDivider(crt, 0.895f);

        // 2. Section I: Bản ghi nhận sự việc ban đầu
        float sec1YMin = 0.65f;
        float sec1YMax = 0.885f;
        GameObject sec1Box = CreateBox(crt, new Vector2(0f, sec1YMin), new Vector2(1.0f, sec1YMax), TableBg, PaperBorder);

        string sec1Text =
            $"<b><size=13>I. TỔNG QUAN VỤ VIỆC & NHÂN THÂN NẠN NHÂN (INCIDENT OVERVIEW):</size></b>\n" +
            $"<color=#555555>───────────────────────────────────────────────────────────────────────────────────────────</color>\n" +
            $"• <b>TÊN VỤ ÁN:</b> <color=#9c2b2b><b>{caseTitle.ToUpper()}</b></color>\n" +
            $"• <b>NẠN NHÂN (DECEDENT):</b> <b>{victimName.ToUpper()}</b>   |   <b>NGHỀ NGHIỆP:</b> {victimOcc}\n" +
            $"• <b>ĐỊA BÀN XẢY RA:</b> {victimRes}\n" +
            $"• <b>THỜI GIAN PHÁT HIỆN THI THỂ:</b> Khoảng 06:30 sáng   |   <b>TÌNH TRẠNG:</b> Tử vong tại chỗ (DOA)\n" +
            $"• <b>ĐIỀU TRA VIÊN PHỤ TRÁCH:</b> Det. Marcus Hale (#7841)   |   <b>CƠ QUAN TIẾP NHẬN:</b> Đội Trọng án";

        CreateText(sec1Box.transform, new Vector2(0.03f, 0.04f), new Vector2(0.97f, 0.96f), sec1Text, TextAnchor.UpperLeft, 11, InkBlack);

        CreateStamp(sec1Box.transform, new Vector2(0.85f, 0.55f), "CONFIDENTIAL\nTỐI MẬT", InkRed, -8f);

        CreateDivider(crt, 0.64f);

        // 3. Section II: Báo cáo hiện trường của sĩ quan đầu tiên tiếp cận
        float sec2YMin = 0.36f;
        float sec2YMax = 0.63f;
        GameObject sec2Box = CreateBox(crt, new Vector2(0f, sec2YMin), new Vector2(1.0f, sec2YMax), TableBg, PaperBorder);

        string sec2Text =
            $"<b><size=13>II. BIÊN BẢN CỦA SĨ QUAN ĐẦU TIÊN TIẾP CẬN HIỆN TRƯỜNG (FIRST RESPONDER LOG):</size></b>\n" +
            $"<color=#555555>───────────────────────────────────────────────────────────────────────────────────────────</color>\n" +
            $"<color=#1a1a24><i>\"{summaryText}\"</i></color>\n\n" +
            $"• <b>Ghi nhận hiện trường:</b> Hiện trường vụ án được phong tỏa nguyên trạng theo biên bản tiếp cận ban đầu; toàn bộ dấu vết vật lý và vật chứng thu giữ được ghim trực tiếp trên bảng.\n" +
            $"• <b>Đối tượng hiện diện:</b> Tất cả các nghi phạm có tên trong hồ sơ đều khai báo lịch trình ngoại phạm (Alibi) riêng biệt trong khoảng thời gian xảy ra án mạng.";

        CreateText(sec2Box.transform, new Vector2(0.03f, 0.04f), new Vector2(0.97f, 0.96f), sec2Text, TextAnchor.UpperLeft, 11, InkBlack);

        CreateDivider(crt, 0.35f);

        // 4. Section III: Hướng dẫn phá án theo 3 Chặng Mục Tiêu (Phong bì niêm phong UCF)
        float sec3YMin = 0.08f;
        float sec3YMax = 0.34f;
        GameObject sec3Box = CreateBox(crt, new Vector2(0f, sec3YMin), new Vector2(1.0f, sec3YMax), TableBg, PaperBorder);

        string sec3Text =
            $"<b><size=13>III. CHỈ THỊ ĐIỀU TRA THEO QUY TRÌNH 3 MỤC TIÊU:</size></b>\n" +
            $"<color=#555555>───────────────────────────────────────────────────────────────────────────────────────────</color>\n" +
            $"Để bảo đảm kết luận khách quan và tránh kết tội oan sai, điều tra viên tiến hành bóc tách vụ án theo <b>3 CHẶNG MỤC TIÊU</b> trước khi mở Lệnh bắt giữ:\n\n" +
            $"<b>[MỤC TIÊU 1]</b> <b>Minh oan cho người vô tội:</b> Dựa vào lời khai và lịch trình ngoại phạm để loại trừ các đối tượng có bằng chứng ngoại phạm vững chắc.\n" +
            $"<b>[MỤC TIÊU 2]</b> <b>Đối chứng Pháp y & Vật chứng:</b> So khớp Báo cáo nhiệt học Henssge với lời khai để phát hiện mâu thuẫn thời gian và xác định hung khí.\n" +
            $"<b>[MỤC TIÊU 3]</b> <b>Nộp lệnh bắt giữ chính thức:</b> Chỉ định đích danh thủ phạm và trình bày lập luận để máy chủ thẩm định kết quả.";

        CreateText(sec3Box.transform, new Vector2(0.03f, 0.04f), new Vector2(0.97f, 0.96f), sec3Text, TextAnchor.UpperLeft, 11, InkBlack);

        CreateDivider(crt, 0.07f);

        // Nút Bắt Đầu / Đóng
        GameObject btnGo = new GameObject("Btn_Dismiss_Briefing", typeof(RectTransform), typeof(Image), typeof(Button));
        RectTransform brt = btnGo.GetComponent<RectTransform>();
        brt.SetParent(crt, false);
        brt.anchorMin = new Vector2(0.35f, 0.005f);
        brt.anchorMax = new Vector2(0.65f, 0.06f);
        brt.sizeDelta = Vector2.zero;

        Image bImg = btnGo.GetComponent<Image>();
        bImg.color = new Color(0.18f, 0.16f, 0.14f, 1f);

        Button btn = btnGo.GetComponent<Button>();
        btn.onClick.AddListener(Close);
        NoirUIStyle.AttachButtonFeel(btn, 0.97f, true);

        GameObject btxtGo = new GameObject("Label", typeof(RectTransform), typeof(Text));
        RectTransform btrt = btxtGo.GetComponent<RectTransform>();
        btrt.SetParent(btnGo.transform, false);
        btrt.anchorMin = Vector2.zero;
        btrt.anchorMax = Vector2.one;
        btrt.sizeDelta = Vector2.zero;

        Text btxt = btxtGo.GetComponent<Text>();
        btxt.font = uiFont ?? DetectiveAssetBank.GetDefaultUIFont();
        btxt.fontSize = 11;
        btxt.fontStyle = FontStyle.Bold;
        btxt.alignment = TextAnchor.MiddleCenter;
        btxt.color = new Color(0.95f, 0.85f, 0.45f);
        btxt.text = "TIẾP NHẬN CHỈ THỊ // BẮT ĐẦU ĐIỀU TRA [X]";
    }

    private GameObject CreateBox(Transform parent, Vector2 anchorMin, Vector2 anchorMax, Color bgColor, Color borderColor)
    {
        GameObject boxGo = new GameObject("Box", typeof(RectTransform), typeof(Image));
        RectTransform rt = boxGo.GetComponent<RectTransform>();
        rt.SetParent(parent, false);
        rt.anchorMin = anchorMin;
        rt.anchorMax = anchorMax;
        rt.sizeDelta = Vector2.zero;

        Image img = boxGo.GetComponent<Image>();
        img.color = bgColor;

        Outline outline = boxGo.AddComponent<Outline>();
        outline.effectColor = borderColor;
        outline.effectDistance = new Vector2(1f, -1f);

        return boxGo;
    }

    private Text CreateText(Transform parent, Vector2 anchorMin, Vector2 anchorMax, string content, TextAnchor align, int fontSize, Color color)
    {
        GameObject txtGo = new GameObject("TextLabel", typeof(RectTransform), typeof(Text));
        RectTransform rt = txtGo.GetComponent<RectTransform>();
        rt.SetParent(parent, false);
        rt.anchorMin = anchorMin;
        rt.anchorMax = anchorMax;
        rt.sizeDelta = Vector2.zero;

        if (uiFont == null) uiFont = DetectiveAssetBank.GetDefaultUIFont();

        Text txt = txtGo.GetComponent<Text>();
        txt.font = uiFont;
        txt.fontSize = fontSize;
        txt.alignment = align;
        txt.color = color;
        txt.text = content;
        txt.supportRichText = true;
        txt.horizontalOverflow = HorizontalWrapMode.Wrap;
        txt.verticalOverflow = VerticalWrapMode.Overflow;
        txt.raycastTarget = false;

        return txt;
    }

    private void CreateDivider(Transform parent, float yNorm)
    {
        GameObject divGo = new GameObject("DividerLine", typeof(RectTransform), typeof(Image));
        RectTransform drt = divGo.GetComponent<RectTransform>();
        drt.SetParent(parent, false);
        drt.anchorMin = new Vector2(0f, yNorm);
        drt.anchorMax = new Vector2(1f, yNorm);
        drt.sizeDelta = new Vector2(0f, 1.5f);

        Image dImg = divGo.GetComponent<Image>();
        dImg.color = new Color(0.25f, 0.22f, 0.18f, 0.4f);
        dImg.raycastTarget = false;
    }

    private void CreateStamp(Transform parent, Vector2 posNorm, string text, Color color, float rotationDeg)
    {
        GameObject stampGo = new GameObject("Stamp_Badge", typeof(RectTransform), typeof(Image));
        RectTransform rt = stampGo.GetComponent<RectTransform>();
        rt.SetParent(parent, false);
        rt.anchorMin = posNorm;
        rt.anchorMax = posNorm;
        rt.pivot = new Vector2(0.5f, 0.5f);
        rt.sizeDelta = new Vector2(130f, 50f);
        rt.localRotation = Quaternion.Euler(0, 0, rotationDeg);

        Image img = stampGo.GetComponent<Image>();
        img.color = new Color(color.r, color.g, color.b, 0.08f);

        Outline outline = stampGo.AddComponent<Outline>();
        outline.effectColor = new Color(color.r, color.g, color.b, 0.85f);
        outline.effectDistance = new Vector2(2f, -2f);

        GameObject textGo = new GameObject("StampText", typeof(RectTransform), typeof(Text));
        RectTransform trt = textGo.GetComponent<RectTransform>();
        trt.SetParent(stampGo.transform, false);
        trt.anchorMin = Vector2.zero;
        trt.anchorMax = Vector2.one;
        trt.sizeDelta = Vector2.zero;

        Text t = textGo.GetComponent<Text>();
        t.font = uiFont ?? DetectiveAssetBank.GetDefaultUIFont();
        t.fontSize = 11;
        t.fontStyle = FontStyle.Bold;
        t.alignment = TextAnchor.MiddleCenter;
        t.color = new Color(color.r, color.g, color.b, 0.9f);
        t.text = text;
        t.lineSpacing = 0.9f;
        t.raycastTarget = false;
    }
}
