using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// HỒ SƠ CẢNH SÁT & BIÊN BẢN VẬT CHỨNG CHUẨN TÀI LIỆU GIẤY (OFFICIAL PAPER DOSSIER SHEET):
/// Tái hiện 100% mẫu giấy hồ sơ trinh thám hình sự chuyên nghiệp theo tài liệu thực tế:
/// - Đối với Nghi phạm: Mẫu CASE FILE (Major Crimes Division) chuẩn hồ sơ San Fernando (Reference Image 3),
///   khổ giấy ngà A4, bảng nhân khẩu học kẻ ô chi tiết, ảnh Mugshot kèm vạch đo chiều cao, con dấu [IN CUSTODY],
///   lời khai nguyên văn, lịch trình ngoại phạm tự khai, biên bản hỏi cung có thanh che bảo mật ██████.
/// - Đối với Vật chứng: Mẫu PHYSICAL EVIDENCE REPORT của Phòng Kỹ thuật Hình sự (Crime Lab),
///   thước đo tỉ lệ pháp y (Forensic Scale Ruler), kết quả giám định vân tay, xét nghiệm máu/ADN, dấu niêm phong [EVIDENCE SEALED].
/// </summary>
public class EvidenceDetailModal : MonoBehaviour
{
    private static EvidenceDetailModal _instance;
    public static EvidenceDetailModal Instance
    {
        get
        {
            if (_instance == null)
            {
#if UNITY_2022_2_OR_NEWER
                _instance = FindAnyObjectByType<EvidenceDetailModal>(FindObjectsInactive.Include);
#else
                _instance = FindObjectOfType<EvidenceDetailModal>(true);
#endif
            }
            return _instance;
        }
        private set => _instance = value;
    }

    [Header("Legacy Bindings (Disabled in favor of paper sheet)")]
    [SerializeField] private GameObject modalRoot;

    // Paper Sheet Dynamic Hierarchy
    private GameObject paperRootGo;
    private RectTransform paperSheetRt;
    private Font uiFont;

    private Texture2D currentTexture;
    private string currentCaption;

    // Paper Palette Colors
    private static readonly Color OverlayDim = new Color(0.04f, 0.04f, 0.05f, 0.82f);
    private static readonly Color PaperColor = new Color(0.96f, 0.94f, 0.90f, 1f); // Màu giấy ngà cổ điển
    private static readonly Color PaperBorder = new Color(0.18f, 0.17f, 0.16f, 1f); // Đường kẻ mực đen
    private static readonly Color InkBlack = new Color(0.11f, 0.11f, 0.13f, 1f); // Màu mực in máy đánh chữ
    private static readonly Color InkMuted = new Color(0.35f, 0.35f, 0.38f, 1f);
    private static readonly Color InkRed = new Color(0.72f, 0.14f, 0.14f, 1f); // Mực đỏ đóng dấu
    private static readonly Color TableBg = new Color(0.92f, 0.90f, 0.85f, 0.6f);

    public bool IsOpen => paperRootGo != null && paperRootGo.activeSelf;

    private void Awake()
    {
        _instance = this;
        uiFont = DetectiveAssetBank.GetDefaultUIFont();

        // Tắt triệt để giao diện đen cũ của scene nếu có
        if (modalRoot != null && modalRoot != gameObject)
        {
            modalRoot.SetActive(false);
        }
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

    /// <summary>
    /// Hiển thị Hồ Sơ Đối Tượng Tình Nghi chuẩn Cảnh sát Hình sự (Chuẩn mẫu CASE FILE - Ảnh 3).
    /// </summary>
    public void ShowSuspect(SuspectData suspect, Texture2D texture)
    {
        if (suspect == null) return;
        currentTexture = texture;
        currentCaption = $"Hồ sơ tạm giữ: {suspect.name}";

        EnsurePaperRoot();
        BuildSuspectPaperDocument(suspect, texture);

        paperRootGo.SetActive(true);
        transform.SetAsLastSibling();
        Debug.Log($"[EvidenceDetailModal] Opened Paper Case File for: {suspect.name}");
    }

    /// <summary>
    /// Hiển thị Báo Cáo Giám Định Vật Chứng & Hung Khí Chuẩn Phòng Kỹ Thuật Hình Sự.
    /// </summary>
    public void ShowEvidence(EvidenceData evidence, Texture2D texture)
    {
        if (evidence == null) return;
        currentTexture = texture;
        currentCaption = $"Vật chứng: {evidence.title}";

        EnsurePaperRoot();
        BuildEvidencePaperDocument(evidence, texture);

        paperRootGo.SetActive(true);
        transform.SetAsLastSibling();
        Debug.Log($"[EvidenceDetailModal] Opened Paper Evidence Report for: {evidence.title}");
    }

    public void Close()
    {
        if (paperRootGo != null)
        {
            paperRootGo.SetActive(false);
        }
        if (modalRoot != null && modalRoot != gameObject)
        {
            modalRoot.SetActive(false);
        }
    }

    private void EnsurePaperRoot()
    {
        if (paperRootGo != null) return;

        Canvas canvas = GetComponentInParent<Canvas>() ?? FindObjectOfType<Canvas>(true);
        if (canvas == null) return;

        // 1. Overlay Dim Fullscreen
        paperRootGo = new GameObject("Police_CaseFile_Overlay", typeof(RectTransform), typeof(Image));
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

        // 2. Tờ giấy hồ sơ A4 ở trung tâm màn hình (Paper Sheet)
        GameObject sheetGo = new GameObject("Paper_Sheet_Document", typeof(RectTransform), typeof(Image));
        paperSheetRt = sheetGo.GetComponent<RectTransform>();
        paperSheetRt.SetParent(paperRootGo.transform, false);
        paperSheetRt.anchorMin = new Vector2(0.5f, 0.5f);
        paperSheetRt.anchorMax = new Vector2(0.5f, 0.5f);
        paperSheetRt.sizeDelta = new Vector2(850f, 960f); // Chuẩn tỉ lệ trang tài liệu cảnh sát A4

        Image sImg = sheetGo.GetComponent<Image>();
        sImg.color = PaperColor;
        sImg.raycastTarget = true; // Chặn click xuyên qua overlay

        // Viền đôi đen cổ điển của văn bản cảnh sát
        Outline outline = sheetGo.AddComponent<Outline>();
        outline.effectColor = PaperBorder;
        outline.effectDistance = new Vector2(2f, -2f);

        // Nút tắt văn bản [X] bằng con dấu kim loại góc trên
        CreateCloseButton(paperSheetRt);
    }

    private void CreateCloseButton(RectTransform parent)
    {
        GameObject closeGo = new GameObject("Btn_Close_Paper", typeof(RectTransform), typeof(Image), typeof(Button));
        RectTransform crt = closeGo.GetComponent<RectTransform>();
        crt.SetParent(parent, false);
        crt.anchorMin = new Vector2(1f, 1f);
        crt.anchorMax = new Vector2(1f, 1f);
        crt.sizeDelta = new Vector2(36f, 36f);
        crt.anchoredPosition = new Vector2(-16f, -16f);

        Image cImg = closeGo.GetComponent<Image>();
        cImg.color = new Color(0.25f, 0.24f, 0.22f, 0.9f);

        Button cBtn = closeGo.GetComponent<Button>();
        cBtn.onClick.AddListener(Close);

        GameObject txtGo = new GameObject("X_Label", typeof(RectTransform), typeof(Text));
        RectTransform trt = txtGo.GetComponent<RectTransform>();
        trt.SetParent(closeGo.transform, false);
        trt.anchorMin = Vector2.zero;
        trt.anchorMax = Vector2.one;
        trt.sizeDelta = Vector2.zero;

        Text txt = txtGo.GetComponent<Text>();
        if (uiFont == null) uiFont = DetectiveAssetBank.GetDefaultUIFont();
        txt.font = uiFont;
        txt.fontSize = 18;
        txt.fontStyle = FontStyle.Bold;
        txt.alignment = TextAnchor.MiddleCenter;
        txt.color = Color.white;
        txt.text = "✕";
        txt.horizontalOverflow = HorizontalWrapMode.Overflow;
        txt.verticalOverflow = VerticalWrapMode.Overflow;
    }

    /// <summary>
    /// Xây dựng trang hồ sơ đối tượng chuẩn Nikki Freeman (Reference Image 3).
    /// </summary>
    private void BuildSuspectPaperDocument(SuspectData suspect, Texture2D texture)
    {
        // Xóa sạch nội dung cũ bên trong Paper Sheet (trừ nút close)
        ClearPaperContents();

        // Container có padding lề giấy chuẩn 24px
        GameObject contentGo = new GameObject("Document_Content", typeof(RectTransform));
        RectTransform crt = contentGo.GetComponent<RectTransform>();
        crt.SetParent(paperSheetRt, false);
        crt.anchorMin = Vector2.zero;
        crt.anchorMax = Vector2.one;
        crt.offsetMin = new Vector2(24f, 20f);
        crt.offsetMax = new Vector2(-24f, -20f);

        // =========================================================================
        // 1. HEADER KHU VỰC CẢNH SÁT & MÃ VỤ ÁN (Y hệt Reference Image 3)
        // =========================================================================
        GameObject headerGo = new GameObject("Header_Row", typeof(RectTransform));
        RectTransform hrt = headerGo.GetComponent<RectTransform>();
        hrt.SetParent(crt, false);
        hrt.anchorMin = new Vector2(0f, 0.90f);
        hrt.anchorMax = new Vector2(1f, 1.0f);
        hrt.sizeDelta = Vector2.zero;

        // Cột trái: Huy hiệu cảnh sát & Tên cục
        CreateText(headerGo.transform, new Vector2(0f, 0f), new Vector2(0.35f, 1f),
            "<b>CITY POLICE DEPARTMENT</b>\n<size=10>MAJOR CRIMES DIVISION // HOMICIDE BUREAU</size>\n<size=9>METROPOLITAN INVESTIGATION ARCHIVES</size>",
            TextAnchor.MiddleLeft, 12, InkBlack);

        // Cột giữa: Chữ lớn CASE FILE
        CreateText(headerGo.transform, new Vector2(0.35f, 0f), new Vector2(0.68f, 1f),
            "<b><size=28>CASE FILE</size></b>\n<size=10><b>HOMICIDE INVESTIGATION DOSSIER</b></size>",
            TextAnchor.MiddleCenter, 12, InkBlack);

        // Cột phải: Khung Mã Vụ Án & Mã Vạch (Barcode Box)
        GameObject barcodeBox = CreateBox(headerGo.transform, new Vector2(0.70f, 0.05f), new Vector2(1.0f, 0.95f), TableBg, PaperBorder);
        CreateText(barcodeBox.transform, new Vector2(0.05f, 0.5f), new Vector2(0.95f, 0.95f),
            $"CASE NO: <b>MCD-{(string.IsNullOrEmpty(suspect.id) ? "26-0529" : suspect.id)}</b>",
            TextAnchor.MiddleCenter, 10, InkBlack);
        CreateText(barcodeBox.transform, new Vector2(0.05f, 0.05f), new Vector2(0.95f, 0.55f),
            "<size=15><b>|| | |||| | ||| || |||| | ||</b></size>",
            TextAnchor.MiddleCenter, 14, InkBlack);

        // Đường kẻ ngang ngăn cách header
        CreateDivider(crt, 0.895f);

        // =========================================================================
        // 2. KHỐI NHÂN KHẨU HỌC & ẢNH BOOKING MUGSHOT (PRIMARY SUBJECT)
        // =========================================================================
        float topSecYMin = 0.58f;
        float topSecYMax = 0.89f;

        // Ảnh Mugshot bên trái
        GameObject photoBox = CreateBox(crt, new Vector2(0f, topSecYMin), new Vector2(0.28f, topSecYMax), Color.black, PaperBorder);
        if (texture != null)
        {
            GameObject rawGo = new GameObject("Mugshot_Photo", typeof(RectTransform), typeof(RawImage), typeof(Button));
            RectTransform prt = rawGo.GetComponent<RectTransform>();
            prt.SetParent(photoBox.transform, false);
            prt.anchorMin = new Vector2(0.04f, 0.12f);
            prt.anchorMax = new Vector2(0.96f, 0.96f);
            prt.sizeDelta = Vector2.zero;

            RawImage rImg = rawGo.GetComponent<RawImage>();
            rImg.texture = texture;
            rImg.color = Color.white;

            Button pBtn = rawGo.GetComponent<Button>();
            pBtn.onClick.AddListener(OnPhotoZoomClicked);
        }

        // Nhãn dưới ảnh
        CreateText(photoBox.transform, new Vector2(0f, 0f), new Vector2(1f, 0.11f),
            "<size=9>BOOKING PHOTO (APPREHENSION)\n<i>[Nhấp để soi kính lúp]</i></size>",
            TextAnchor.MiddleCenter, 9, Color.white);

        // Bảng lý lịch kẻ ô bên phải ảnh (Primary Subject Table)
        GameObject infoBox = CreateBox(crt, new Vector2(0.30f, topSecYMin), new Vector2(1.0f, topSecYMax), TableBg, PaperBorder);

        // Tên đối tượng và mã hiệu
        string suspName = string.IsNullOrEmpty(suspect.name) ? "CHƯA XÁC ĐỊNH" : suspect.name.ToUpper();
        string genderStr = string.IsNullOrEmpty(suspect.gender) ? "Nam" : suspect.gender;
        string relStr = string.IsNullOrEmpty(suspect.relationship_to_victim) ? "Bạn thân lâu năm kiêm bác sĩ riêng" : suspect.relationship_to_victim;
        string resStr = string.IsNullOrEmpty(suspect.residence) ? "Biệt thự Blackwood Manor" : suspect.residence;

        string demoText =
            $"<size=11>PRIMARY SUBJECT:</size>   <b><size=17>{suspName}</size></b>\n" +
            $"<color=#555555>──────────────────────────────────────────────────────────────────────────</color>\n" +
            $"• <b>TUỔI / AGE:</b> {suspect.age}        |   <b>GIỚI TÍNH / SEX:</b> {genderStr}        |   <b>MÃ ĐỐI TƯỢNG:</b> {suspect.id}\n" +
            $"• <b>NGHỀ NGHIỆP:</b> {suspect.occupation}\n" +
            $"• <b>NƠI CƯ TRÚ (ADDRESS):</b> {resStr}\n" +
            $"• <b>MỐI QUAN HỆ VỚI NẠN NHÂN:</b> <color=#8c1d1d><b>{relStr}</b></color>\n" +
            $"• <b>TÌNH TRẠNG PHÁP LÝ:</b> <color=#9c2b2b><b>TẠM GIỮ CHỜ XÉT XỬ (IN CUSTODY / AWAITING TRIAL)</b></color>\n" +
            $"<color=#555555>──────────────────────────────────────────────────────────────────────────</color>\n" +
            $"<b>TỘI DANH TÌNH NGHI & ĐỘNG CƠ (CHARGES / MOTIVE):</b>\n" +
            $"<color=#222222>{suspect.motive}</color>";

        CreateText(infoBox.transform, new Vector2(0.03f, 0.04f), new Vector2(0.97f, 0.96f), demoText, TextAnchor.UpperLeft, 11, InkBlack);

        // Con dấu đỏ IN CUSTODY đóng đè chéo ở góc
        CreateStamp(infoBox.transform, new Vector2(0.68f, 0.58f), "IN CUSTODY\nĐANG TẠM GIỮ", InkRed, -10f);

        // Đường kẻ ngang ngăn cách
        CreateDivider(crt, 0.575f);

        // =========================================================================
        // 3. THÂN HỒ SƠ 2 CỘT: LỜI KHAI NGUYÊN VĂN & BẰNG CHỨNG NGOẠI PHẠM
        // =========================================================================
        float midSecYMin = 0.08f;
        float midSecYMax = 0.565f;

        // Cột Trái (50%): Lời khai & Bằng chứng ngoại phạm
        GameObject leftCol = CreateBox(crt, new Vector2(0f, midSecYMin), new Vector2(0.49f, midSecYMax), TableBg, PaperBorder);

        string statementStr = !string.IsNullOrEmpty(suspect.statement) ? suspect.statement : (!string.IsNullOrEmpty(suspect.alibi_statement) ? suspect.alibi_statement : "Đối tượng từ chối trả lời một số câu hỏi liên quan đến thời điểm án mạng.");
        string timelineStr = !string.IsNullOrEmpty(suspect.timeline_claimed) ? suspect.timeline_claimed : $"{suspect.alibi_start} - {suspect.alibi_end}: {suspect.alibi_statement}";

        string leftText =
            $"<b><size=12>I. LỜI KHAI NGUYÊN VĂN KHI THẨM VẤN</size></b>\n" +
            $"<size=10><color=#555555>(OFFICIAL RECORDED STATEMENT):</color></size>\n\n" +
            $"<color=#1a1a24><i>\"{statementStr}\"</i></color>\n\n" +
            $"<color=#555555>────────────────────────────────────────────</color>\n" +
            $"<b><size=12>II. BẰNG CHỨNG NGOẠI PHẠM & LỊCH TRÌNH</size></b>\n" +
            $"<size=10><color=#555555>(CLAIMED ALIBI & MOVEMENTS):</color></size>\n\n" +
            $"• <b>Khung giờ khai báo:</b> <color=#1c6b2a><b>[{suspect.alibi_start} - {suspect.alibi_end}]</b></color>\n" +
            $"• <b>Lịch trình di chuyển tự khai:</b>\n{timelineStr}";

        CreateText(leftCol.transform, new Vector2(0.04f, 0.04f), new Vector2(0.96f, 0.96f), leftText, TextAnchor.UpperLeft, 11, InkBlack);

        // Cột Phải (50%): Ghi chép của điều tra viên & Dải băng đen bảo mật
        GameObject rightCol = CreateBox(crt, new Vector2(0.51f, midSecYMin), new Vector2(1.0f, midSecYMax), TableBg, PaperBorder);

        string notesStr = !string.IsNullOrEmpty(suspect.interview_notes) ? suspect.interview_notes : "Đối tượng trả lời rành mạch, thái độ bình tĩnh nhưng có biểu hiện bồn chồn khi được hỏi về hiện trường.";

        string rightText =
            $"<b><size=12>III. BIÊN BẢN HỎI CUNG CỦA ĐIỀU TRA VIÊN</size></b>\n" +
            $"<size=10><color=#555555>(INTERVIEW NOTES & OBSERVATIONS):</color></size>\n\n" +
            $"• {notesStr}\n\n" +
            $"<color=#555555>────────────────────────────────────────────</color>\n" +
            $"<b><size=11>GHI CHÚ BẢO MẬT HỒ SƠ CHƯA GIẢI MẬT:</size></b>\n" +
            $"<color=#222222>████████████████████████████████████████████\n" +
            $"████████████████████████████████████████████\n" +
            $"████████████████████████████████████████████</color>\n" +
            $"<size=9><color=#666666><i>[TÀI LIỆU BẢO MẬT MỨC ĐỘ 2 - CHỈ LƯU HÀNH NỘI BỘ PHÒNG ĐIỀU TRA HÌNH SỰ]</i></color></size>";

        CreateText(rightCol.transform, new Vector2(0.04f, 0.04f), new Vector2(0.96f, 0.96f), rightText, TextAnchor.UpperLeft, 11, InkBlack);

        // =========================================================================
        // 4. FOOTER CUỐI TRANG VĂN BẢN (OFFICIAL CLASSIFICATION)
        // =========================================================================
        CreateDivider(crt, 0.075f);

        string footerText =
            "<b>Điều tra viên thụ lý:</b> Det. Marcus Hale #7841   |   " +
            "<b>Cán bộ giám định:</b> Det. L. Ramirez #6527   |   " +
            "<b>Phân loại:</b> <color=#9c2b2b>CONFIDENTIAL // NOT FOR PUBLIC RELEASE</color>";
        CreateText(crt, new Vector2(0f, 0f), new Vector2(1f, 0.065f), footerText, TextAnchor.MiddleCenter, 10, InkMuted);
    }

    /// <summary>
    /// Xây dựng trang báo cáo giám định vật chứng & hung khí chuẩn Crime Lab.
    /// </summary>
    private void BuildEvidencePaperDocument(EvidenceData evidence, Texture2D texture)
    {
        ClearPaperContents();

        GameObject contentGo = new GameObject("Document_Content", typeof(RectTransform));
        RectTransform crt = contentGo.GetComponent<RectTransform>();
        crt.SetParent(paperSheetRt, false);
        crt.anchorMin = Vector2.zero;
        crt.anchorMax = Vector2.one;
        crt.offsetMin = new Vector2(24f, 20f);
        crt.offsetMax = new Vector2(-24f, -20f);

        // Header
        GameObject headerGo = new GameObject("Header_Row", typeof(RectTransform));
        RectTransform hrt = headerGo.GetComponent<RectTransform>();
        hrt.SetParent(crt, false);
        hrt.anchorMin = new Vector2(0f, 0.90f);
        hrt.anchorMax = new Vector2(1f, 1.0f);
        hrt.sizeDelta = Vector2.zero;

        CreateText(headerGo.transform, new Vector2(0f, 0f), new Vector2(0.35f, 1f),
            "<b>POLICE FORENSIC SCIENCE LABORATORY</b>\n<size=10>CRIMINAL INVESTIGATION DIVISION</size>\n<size=9>PHYSICAL EVIDENCE & FORENSICS LAB</size>",
            TextAnchor.MiddleLeft, 12, InkBlack);

        CreateText(headerGo.transform, new Vector2(0.35f, 0f), new Vector2(0.68f, 1f),
            "<b><size=24>EVIDENCE REPORT</size></b>\n<size=10><b>BÁO CÁO GIÁM ĐỊNH TƯ PHÁP VẬT CHỨNG</b></size>",
            TextAnchor.MiddleCenter, 12, InkBlack);

        GameObject barcodeBox = CreateBox(headerGo.transform, new Vector2(0.70f, 0.05f), new Vector2(1.0f, 0.95f), TableBg, PaperBorder);
        CreateText(barcodeBox.transform, new Vector2(0.05f, 0.5f), new Vector2(0.95f, 0.95f),
            $"TAG NO: <b>#{(string.IsNullOrEmpty(evidence.id) ? "EVD-01" : evidence.id)}</b>",
            TextAnchor.MiddleCenter, 10, InkBlack);
        CreateText(barcodeBox.transform, new Vector2(0.05f, 0.05f), new Vector2(0.95f, 0.55f),
            "<size=15><b>|||| | || ||||| | ||| || ||</b></size>",
            TextAnchor.MiddleCenter, 14, InkBlack);

        CreateDivider(crt, 0.895f);

        // Khối ảnh vật chứng kèm thước tỉ lệ pháp y
        float topSecYMin = 0.58f;
        float topSecYMax = 0.89f;

        GameObject photoBox = CreateBox(crt, new Vector2(0f, topSecYMin), new Vector2(0.35f, topSecYMax), Color.black, PaperBorder);
        if (texture != null)
        {
            GameObject rawGo = new GameObject("Evidence_Photo", typeof(RectTransform), typeof(RawImage), typeof(Button));
            RectTransform prt = rawGo.GetComponent<RectTransform>();
            prt.SetParent(photoBox.transform, false);
            prt.anchorMin = new Vector2(0.05f, 0.16f);
            prt.anchorMax = new Vector2(0.95f, 0.95f);
            prt.sizeDelta = Vector2.zero;

            RawImage rImg = rawGo.GetComponent<RawImage>();
            rImg.texture = texture;
            rImg.color = Color.white;

            Button pBtn = rawGo.GetComponent<Button>();
            pBtn.onClick.AddListener(OnPhotoZoomClicked);
        }

        // Thước đo tỉ lệ pháp y
        Texture2D rulerTex = DetectiveAssetBank.GetNoirTexture("forensic_ruler.png");
        if (rulerTex != null)
        {
            GameObject rulerGo = new GameObject("RulerImg", typeof(RectTransform), typeof(RawImage));
            RectTransform rrt = rulerGo.GetComponent<RectTransform>();
            rrt.SetParent(photoBox.transform, false);
            rrt.anchorMin = new Vector2(0.05f, 0.03f);
            rrt.anchorMax = new Vector2(0.95f, 0.14f);
            rrt.sizeDelta = Vector2.zero;

            RawImage ruImg = rulerGo.GetComponent<RawImage>();
            ruImg.texture = rulerTex;
            ruImg.color = Color.white;
        }

        // Bảng thuộc tính vật chứng bên phải
        GameObject infoBox = CreateBox(crt, new Vector2(0.37f, topSecYMin), new Vector2(1.0f, topSecYMax), TableBg, PaperBorder);
        string categoryTag = evidence.is_weapon
            ? "<color=#9c2b2b><b>🔴 HUNG KHÍ GÂY ÁN TIỀM TÀNG (SUSPECTED WEAPON)</b></color>"
            : "<color=#1b4d8c><b>🔵 VẬT CHỨNG HIỆN TRƯỜNG (CRIME SCENE EVIDENCE)</b></color>";

        string demoText =
            $"<size=11>TÊN VẬT MẪU:</size>   <b><size=16>{(string.IsNullOrEmpty(evidence.title) ? "VẬT CHỨNG" : evidence.title.ToUpper())}</size></b>\n" +
            $"<color=#555555>───────────────────────────────────────────────────────────────────</color>\n" +
            $"• <b>PHÂN LOẠI:</b> {categoryTag}\n" +
            $"• <b>ĐỊA ĐIỂM THU GIỮ (LOCATION):</b> <color=#111111>{evidence.location}</color>\n" +
            $"• <b>TÌNH TRẠNG VẬT LÝ & ĐẶC TÍNH:</b>\n" +
            $"  {(!string.IsNullOrEmpty(evidence.physical_condition) ? evidence.physical_condition : evidence.description)}\n" +
            $"<color=#555555>───────────────────────────────────────────────────────────────────</color>\n" +
            $"• <b>TÌNH TRẠNG NIÊM PHONG:</b> <color=#9c2b2b><b>EVIDENCE SEALED // TÒA ÁN NIÊM PHONG</b></color>";

        CreateText(infoBox.transform, new Vector2(0.03f, 0.04f), new Vector2(0.97f, 0.96f), demoText, TextAnchor.UpperLeft, 11, InkBlack);

        CreateStamp(infoBox.transform, new Vector2(0.70f, 0.55f), "EVIDENCE\nSEALED", InkRed, -12f);
        CreateDivider(crt, 0.575f);

        // Khối phân tích khoa học hình sự
        float midSecYMin = 0.08f;
        float midSecYMax = 0.565f;

        GameObject analysisBox = CreateBox(crt, new Vector2(0f, midSecYMin), new Vector2(1.0f, midSecYMax), TableBg, PaperBorder);

        string printStr = !string.IsNullOrEmpty(evidence.fingerprint_analysis) ? evidence.fingerprint_analysis : "Quét Ninhydrin và bột từ: Dấu vân tay mờ hoặc có dấu hiệu bị ma sát vải thô làm biến dạng.";
        string bioStr = !string.IsNullOrEmpty(evidence.blood_dna_analysis) ? evidence.blood_dna_analysis : "Phản ứng Kastle-Meyer xác định mẫu máu. Không phát hiện ADN tạp chất ngoài dự kiến.";

        string analysisText =
            $"<b><size=13>I. KẾT QUẢ GIÁM ĐỊNH DẤU VÂN TAY TIỀM ẨN (LATENT FINGERPRINT ANALYSIS):</size></b>\n" +
            $"• {printStr}\n\n" +
            $"<color=#555555>───────────────────────────────────────────────────────────────────────────────────</color>\n" +
            $"<b><size=13>II. XÉT NGHIỆM HUYẾT HỌC & ADN PHÁP CHỨNG (SEROLOGY & DNA ANALYSIS):</size></b>\n" +
            $"• {bioStr}\n\n" +
            $"<color=#555555>───────────────────────────────────────────────────────────────────────────────────</color>\n" +
            $"<b><size=13>III. ĐỐI CHIẾU HIỆN TRƯỜNG & TƯƠNG THÍCH THƯƠNG TÍCH TỬ THI:</size></b>\n" +
            $"• {evidence.description}";

        CreateText(analysisBox.transform, new Vector2(0.03f, 0.04f), new Vector2(0.97f, 0.96f), analysisText, TextAnchor.UpperLeft, 11, InkBlack);

        CreateDivider(crt, 0.075f);
        string footerText =
            "<b>Giám định viên trưởng:</b> Dr. Angela Miller (Crime Lab)   |   " +
            "<b>Chứng chỉ pháp y:</b> FSL-8921-QC   |   " +
            "<b>Tình trạng:</b> CHAIN OF CUSTODY VERIFIED";
        CreateText(crt, new Vector2(0f, 0f), new Vector2(1f, 0.065f), footerText, TextAnchor.MiddleCenter, 10, InkMuted);
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
        RectTransform rt = divGo.GetComponent<RectTransform>();
        rt.SetParent(parent, false);
        rt.anchorMin = new Vector2(0f, yNorm);
        rt.anchorMax = new Vector2(1f, yNorm);
        rt.sizeDelta = new Vector2(0f, 1.5f);

        Image img = divGo.GetComponent<Image>();
        img.color = PaperBorder;
    }

    private void CreateStamp(Transform parent, Vector2 anchorPos, string stampText, Color stampColor, float angle)
    {
        GameObject stampGo = new GameObject("RubberStamp", typeof(RectTransform), typeof(Image));
        RectTransform rt = stampGo.GetComponent<RectTransform>();
        rt.SetParent(parent, false);
        rt.anchorMin = anchorPos;
        rt.anchorMax = anchorPos;
        rt.sizeDelta = new Vector2(140f, 48f);
        rt.localRotation = Quaternion.Euler(0f, 0f, angle);

        Image img = stampGo.GetComponent<Image>();
        img.color = new Color(stampColor.r, stampColor.g, stampColor.b, 0.15f);

        Outline outline = stampGo.AddComponent<Outline>();
        outline.effectColor = stampColor;
        outline.effectDistance = new Vector2(1.5f, -1.5f);

        GameObject txtGo = new GameObject("StampTxt", typeof(RectTransform), typeof(Text));
        RectTransform trt = txtGo.GetComponent<RectTransform>();
        trt.SetParent(stampGo.transform, false);
        trt.anchorMin = Vector2.zero;
        trt.anchorMax = Vector2.one;
        trt.sizeDelta = Vector2.zero;

        if (uiFont == null) uiFont = DetectiveAssetBank.GetDefaultUIFont();

        Text txt = txtGo.GetComponent<Text>();
        txt.font = uiFont;
        txt.fontSize = 11;
        txt.fontStyle = FontStyle.Bold;
        txt.alignment = TextAnchor.MiddleCenter;
        txt.color = stampColor;
        txt.text = stampText;
        txt.horizontalOverflow = HorizontalWrapMode.Overflow;
        txt.verticalOverflow = VerticalWrapMode.Overflow;
        txt.raycastTarget = false;
    }

    private void OnPhotoZoomClicked()
    {
        if (currentTexture != null && PhotoLightboxModal.Instance != null)
        {
            PhotoLightboxModal.Instance.Show(currentTexture, currentCaption ?? "Chi tiết hình ảnh");
        }
    }
}
