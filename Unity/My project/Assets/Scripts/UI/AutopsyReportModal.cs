using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// BIÊN BẢN KHÁM NGHIỆM TỬ THI PHÁP Y CHUẨN TÀI LIỆU GIẤY (OFFICIAL CORONER AUTOPSY REPORT SHEET):
/// Tái hiện 100% tài liệu giám định pháp y cổ điển của Văn phòng Giám định Y khoa Hạt Essex (Reference Image 4):
/// - Khổ giấy chứng nhận y khoa ngà cổ điển (Aged Ivory Medical Certificate Paper), viền đen kép thanh lịch.
/// - Tiêu đề Office of the County Medical Examiner / Report of Investigation.
/// - Form điền thông tin nạn nhân, nhân thân, hiện trường, phân loại án mạng Homicide [✓].
/// - Tình trạng sinh lý: Thân nhiệt trực tràng, nhiệt độ môi trường, trạng thái co cứng (Rigor Mortis) và hoen ố (Livor Mortis).
/// - Phân tích nhiệt học giảm thân nhiệt Henssge Nomogram xác lập khung giờ tử vong thực tế.
/// - Bản vẽ sơ đồ giải phẫu học cơ thể người 2 mặt (Anatomical Dual-View Chart: Mặt trước & Mặt sau) kèm chỉ dẫn vị trí tổn thương.
/// - Bảng kết luận nguyên nhân tử vong (Cause of Death) & Chữ ký bác sĩ pháp y trưởng.
/// - TUYỆT ĐỐI KHÔNG mớm trước đáp án về đồng hồ bị ngụy tạo (để người chơi tự phát hiện đối chiếu như Unsolved Case Files).
/// </summary>
public class AutopsyReportModal : MonoBehaviour
{
    private static AutopsyReportModal _instance;
    public static AutopsyReportModal Instance
    {
        get
        {
            if (_instance == null)
            {
#if UNITY_2022_2_OR_NEWER
                _instance = FindAnyObjectByType<AutopsyReportModal>(FindObjectsInactive.Include);
#else
                _instance = FindObjectOfType<AutopsyReportModal>(true);
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

    // Palette Colors for Aged Medical Certificate
    private static readonly Color OverlayDim = new Color(0.04f, 0.04f, 0.05f, 0.82f);
    private static readonly Color PaperIvory = new Color(0.97f, 0.96f, 0.92f, 1f); // Giấy ngà y tế
    private static readonly Color PaperBorder = new Color(0.18f, 0.17f, 0.16f, 1f); // Đường kẻ mực đen
    private static readonly Color InkBlack = new Color(0.10f, 0.10f, 0.12f, 1f); // Mực in đen
    private static readonly Color InkMuted = new Color(0.35f, 0.35f, 0.38f, 1f);
    private static readonly Color InkRed = new Color(0.72f, 0.14f, 0.14f, 1f); // Mực đỏ đóng dấu
    private static readonly Color TableBg = new Color(0.93f, 0.91f, 0.86f, 0.6f);

    public bool IsOpen => paperRootGo != null && paperRootGo.activeSelf;

    private void Awake()
    {
        _instance = this;
        uiFont = DetectiveAssetBank.GetDefaultUIFont();

        Image selfBg = GetComponent<Image>();
        if (selfBg != null)
        {
            selfBg.enabled = false;
            selfBg.raycastTarget = false;
        }

        if (modalRoot != null) modalRoot.SetActive(false);
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

    public void Open()
    {
        EnsurePaperRoot();

        CaseDossier currentCase = GameController.Instance != null ? GameController.Instance.currentCase : null;
        VictimData v = currentCase?.victim;
        if (v == null)
        {
            v = new VictimData
            {
                name = "Arthur Blackwood",
                age = 62,
                gender = "Nam",
                occupation = "Chủ sở hữu trang viên & Doanh nhân",
                residence = "Biệt thự cổ Blackwood, Hạt Sussex",
                forensic_data = new ForensicData
                {
                    ambient_temp = 18.5f,
                    body_temp = 27.5f,
                    livor_mortis_state = "Hoen tử thi tím sẫm cố định ở vùng lưng, mông và mặt sau bắp đùi. Không phai màu khi ấn ngón.",
                    rigor_mortis_state = "Co cứng toàn phần (Full Rigor Mortis) ở cơ hàm, cổ và chi trên.",
                    wound_description = "Vết đâm trực diện khoang liên sườn 4-5 bên trái dài 2.0cm, sâu khoảng 8.5cm, xuyên thủng thất trái.",
                    cause_of_death = "Sốc mất máu cấp tính do tổn thương thấu tim (Penetrating Cardiac Trauma).",
                    manner_of_death = "Vụ án mạng sát hại (Homicide).",
                    estimated_tod_start = "20:30",
                    estimated_tod_end = "20:50",
                    body_weight_kg = 76.0f,
                    cooling_factor = 1.25f,
                    discovery_time = "06:30"
                }
            };
        }

        BuildAutopsyPaperDocument(v);

        paperRootGo.SetActive(true);
        transform.SetAsLastSibling();
        Debug.Log("[AutopsyReportModal] Opened Paper Autopsy Report Sheet.");
    }

    public void Close()
    {
        if (paperRootGo != null)
        {
            paperRootGo.SetActive(false);
        }
        if (modalRoot != null)
        {
            modalRoot.SetActive(false);
        }
        gameObject.SetActive(false);
    }

    private void EnsurePaperRoot()
    {
        if (paperRootGo != null) return;

        Canvas canvas = GetComponentInParent<Canvas>() ?? FindObjectOfType<Canvas>(true);
        if (canvas == null) return;

        // Overlay Dim Fullscreen
        paperRootGo = new GameObject("Autopsy_Report_Overlay", typeof(RectTransform), typeof(Image));
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

        // Tờ giấy biên bản khám nghiệm A4 (Medical Paper Sheet)
        GameObject sheetGo = new GameObject("Autopsy_Paper_Document", typeof(RectTransform), typeof(Image));
        paperSheetRt = sheetGo.GetComponent<RectTransform>();
        paperSheetRt.SetParent(paperRootGo.transform, false);
        paperSheetRt.anchorMin = new Vector2(0.5f, 0.5f);
        paperSheetRt.anchorMax = new Vector2(0.5f, 0.5f);
        paperSheetRt.sizeDelta = new Vector2(860f, 960f);

        Image sImg = sheetGo.GetComponent<Image>();
        sImg.color = PaperIvory;
        sImg.raycastTarget = true;

        Outline outline = sheetGo.AddComponent<Outline>();
        outline.effectColor = PaperBorder;
        outline.effectDistance = new Vector2(2f, -2f);

        // Nút tắt văn bản [X]
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
    /// Xây dựng biên bản khám nghiệm tử thi chuẩn Hạt Essex (Reference Image 4).
    /// </summary>
    private void BuildAutopsyPaperDocument(VictimData v)
    {
        ClearPaperContents();

        ForensicData f = v.forensic_data ?? new ForensicData
        {
            ambient_temp = 18.5f,
            body_temp = 27.5f,
            livor_mortis_state = "Cố định vùng lưng",
            rigor_mortis_state = "Toàn phần",
            wound_description = "Vết thương thấu tim",
            cause_of_death = "Sốc mất máu",
            manner_of_death = "Án mạng (Homicide)",
            estimated_tod_start = "20:30",
            estimated_tod_end = "20:50",
            body_weight_kg = 76f
        };

        GameObject contentGo = new GameObject("Document_Content", typeof(RectTransform));
        RectTransform crt = contentGo.GetComponent<RectTransform>();
        crt.SetParent(paperSheetRt, false);
        crt.anchorMin = Vector2.zero;
        crt.anchorMax = Vector2.one;
        crt.offsetMin = new Vector2(24f, 18f);
        crt.offsetMax = new Vector2(-24f, -18f);

        // =========================================================================
        // 1. HEADER VĂN PHÒNG PHÁP Y (Y hệt Reference Image 4)
        // =========================================================================
        CreateText(crt, new Vector2(0.70f, 0.95f), new Vector2(1f, 0.99f),
            "Case Nº: <b>2026-MED-001</b>", TextAnchor.MiddleRight, 10, InkBlack);

        string headerCenter =
            "<b><size=15>OFFICE OF THE COUNTY MEDICAL EXAMINER</size></b>\n" +
            "<size=10>88 Washington Street, SALEM, MASSACHUSETTS // PHÒNG GIÁM ĐỊNH PHÁP Y QUỐC GIA</size>\n" +
            "<b><size=16>REPORT OF INVESTIGATION BY COUNTY MEDICAL EXAMINER</size></b>";
        CreateText(crt, new Vector2(0f, 0.88f), new Vector2(1f, 0.95f), headerCenter, TextAnchor.MiddleCenter, 11, InkBlack);

        CreateDivider(crt, 0.875f);

        // =========================================================================
        // 2. KHỐI FORM ĐIỀN THÔNG TIN TỬ THI & HÌNH THỨC TỬ VONG
        // =========================================================================
        string victimName = string.IsNullOrEmpty(v.name) ? "ARTHUR BLACKWOOD" : v.name.ToUpper();
        string victimResidence = string.IsNullOrEmpty(v.residence) ? "Biệt thự cổ Blackwood" : v.residence;
        string victimJob = string.IsNullOrEmpty(v.occupation) ? "Chủ sở hữu trang viên & Doanh nhân" : v.occupation;

        string demoForm =
            $"DECEDENT (TỬ THI): <b><size=13>{victimName}</size></b> ................... CHỦNG TỘC: Caucasian ..... GIỚI TÍNH: {v.gender} ..... TUỔI: {v.age}\n" +
            $"ĐỊA CHỈ TÌM THẤY: {victimResidence} ..................................... NGHỀ NGHIỆP: {victimJob}\n" +
            $"HÌNH THỨC TỬ VONG (TYPE OF DEATH):   Violent [X]     Casualty [ ]     Suicide [ ]     Suspicious, unusual [X]     Natural [ ]";
        CreateText(crt, new Vector2(0f, 0.775f), new Vector2(1f, 0.865f), demoForm, TextAnchor.UpperLeft, 10, InkBlack);

        CreateDivider(crt, 0.765f);

        // =========================================================================
        // 3. KHỐI KHÁM NGHIỆM BÊN NGOÀI & THÂN NHIỆT (DESCRIPTION OF BODY)
        // =========================================================================
        string physForm =
            $"<b>TÌNH TRẠNG TRANG PHỤC:</b> Mặc đầy đủ âu phục dạ tiệc trang trọng [X]      Không mặc [ ]      Rách nát [ ]\n" +
            $"• <b>Mắt:</b> Giãn đồng tử        |   <b>Tóc:</b> Bạc hoa râm        |   <b>Râu:</b> Cạo sạch        |   <b>Thể trọng:</b> <b>{f.body_weight_kg:F1} kg</b>\n" +
            $"• <b>THÂN NHIỆT TRỰC TRÀNG:</b> <color=#8c1d1d><b>{f.body_temp:F1} °C</b></color>        |   <b>NHIỆT ĐỘ PHÒNG:</b> <b>{f.ambient_temp:F1} °C</b>        |   <b>GIỜ PHÁT HIỆN:</b> {f.discovery_time}\n" +
            $"• <b>CO CỨNG TỬ THI (RIGOR):</b> Có [X]   Không [ ]   |   <i>{f.rigor_mortis_state}</i>\n" +
            $"• <b>HOEN TỬ THI (LIVOR MORTIS):</b> Cố định [X]   Chưa cố định [ ]   |   <i>{f.livor_mortis_state}</i>";
        CreateText(crt, new Vector2(0f, 0.615f), new Vector2(1f, 0.755f), physForm, TextAnchor.UpperLeft, 10, InkBlack);

        CreateDivider(crt, 0.605f);

        // =========================================================================
        // 4. THÂN BIÊN BẢN CHIA 2 CỘT: VẾT THƯƠNG + NHIỆT HỌC (TRÁI) & SƠ ĐỒ CƠ THỂ (PHẢI)
        // =========================================================================
        float midSecYMin = 0.17f;
        float midSecYMax = 0.595f;

        // Cột Trái (52%): Vết thương & Phân tích Henssge Nomogram
        GameObject leftCol = CreateBox(crt, new Vector2(0f, midSecYMin), new Vector2(0.52f, midSecYMax), TableBg, PaperBorder);

        string leftText =
            $"<b><size=11>DẤU HIỆU THƯƠNG TÍCH & GIẢI PHẪU TỬ THI</size></b>\n" +
            $"<size=9><color=#555555>(MARKS AND WOUNDS INVESTIGATION):</color></size>\n" +
            $"───────────────────────────────────────────────────\n" +
            $"• <b>Vết thương ngực trái (Penetrating Wound):</b>\n" +
            $"  {f.wound_description}\n" +
            $"• <b>Dấu vết tự vệ (Defense Wounds):</b> Không ghi nhận vết cứa hay bầm tím ở lòng bàn tay và cẳng tay.\n\n" +
            $"<b><size=11>ĐỊNH LƯỢNG NHIỆT HỌC PHÁP Y HENSSGE</size></b>\n" +
            $"<size=9><color=#555555>(TWO-EXPONENTIAL COOLING ANALYSIS):</color></size>\n" +
            $"───────────────────────────────────────────────────\n" +
            $"• Phương trình: <i>B(t) = 1.25·e^(-kt) - 0.25·e^(-5kt)</i>\n" +
            $"• Hệ số thích nghi thể trọng C = 1.0 (76kg mặc ấm)\n" +
            $"• <b>KHUNG GIỜ TỬ VONG XÁC LẬP (TOD WINDOW):</b>\n" +
            $"  <size=13><color=#8c1d1d><b>[{f.estimated_tod_start} - {f.estimated_tod_end}]</b></color></size>\n" +
            $"  <size=9><i>(Biên độ sai số y học pháp chứng: ± 25 phút)</i></size>";

        CreateText(leftCol.transform, new Vector2(0.04f, 0.03f), new Vector2(0.96f, 0.97f), leftText, TextAnchor.UpperLeft, 10, InkBlack);

        // Cột Phải (46%): Sơ đồ giải phẫu học cơ thể người 2 mặt (Anatomical Body Diagram)
        GameObject rightCol = CreateBox(crt, new Vector2(0.54f, midSecYMin), new Vector2(1.0f, midSecYMax), Color.white, PaperBorder);

        CreateText(rightCol.transform, new Vector2(0f, 0.91f), new Vector2(1f, 0.98f),
            "<b>SƠ ĐỒ GIẢI PHẪU TỔN THƯƠNG (ANATOMICAL CHART)</b>", TextAnchor.MiddleCenter, 9, InkBlack);

        // Ảnh sơ đồ cơ thể người 2 mặt (Mặt trước Anterior & Mặt sau Posterior)
        Texture2D diagramTex = DetectiveAssetBank.GetNoirTexture("autopsy_body_diagram.png");
        if (diagramTex != null)
        {
            GameObject diagGo = new GameObject("BodyDiagramImg", typeof(RectTransform), typeof(RawImage));
            RectTransform drt = diagGo.GetComponent<RectTransform>();
            drt.SetParent(rightCol.transform, false);
            drt.anchorMin = new Vector2(0.05f, 0.08f);
            drt.anchorMax = new Vector2(0.95f, 0.90f);
            drt.sizeDelta = Vector2.zero;

            RawImage rImg = diagGo.GetComponent<RawImage>();
            rImg.texture = diagramTex;
            rImg.color = Color.white;

            // Điểm chỉ dẫn vết đâm ngực trái màu đỏ trên sơ đồ
            GameObject woundMarker = new GameObject("WoundMarker", typeof(RectTransform), typeof(Text));
            RectTransform wmrt = woundMarker.GetComponent<RectTransform>();
            wmrt.SetParent(diagGo.transform, false);
            wmrt.anchorMin = new Vector2(0.28f, 0.65f); // Vị trí khoang ngực trái mặt trước
            wmrt.anchorMax = new Vector2(0.28f, 0.65f);
            wmrt.sizeDelta = new Vector2(120f, 24f);

            Text wmt = woundMarker.GetComponent<Text>();
            if (uiFont == null) uiFont = DetectiveAssetBank.GetDefaultUIFont();
            wmt.font = uiFont;
            wmt.fontSize = 11;
            wmt.fontStyle = FontStyle.Bold;
            wmt.color = InkRed;
            wmt.text = "🔴 Vết đâm 8.5cm";
            wmt.horizontalOverflow = HorizontalWrapMode.Overflow;
            wmt.verticalOverflow = VerticalWrapMode.Overflow;
        }

        // =========================================================================
        // 5. BẢNG KẾT LUẬN & CHỮ KÝ PHÁP Y (Y hệt Reference Image 4 footer)
        // =========================================================================
        CreateDivider(crt, 0.16f);

        float bottomYMin = 0.02f;
        float bottomYMax = 0.15f;

        // Ô 1: Nguyên nhân tử vong
        GameObject box1 = CreateBox(crt, new Vector2(0f, bottomYMin), new Vector2(0.40f, bottomYMax), TableBg, PaperBorder);
        CreateText(box1.transform, new Vector2(0.04f, 0.05f), new Vector2(0.96f, 0.95f),
            $"<b>PROBABLE CAUSE OF DEATH:</b>\n<color=#8c1d1d><b>{f.cause_of_death}</b></color>",
            TextAnchor.UpperLeft, 10, InkBlack);

        // Ô 2: Hình thức tử vong
        GameObject box2 = CreateBox(crt, new Vector2(0.41f, bottomYMin), new Vector2(0.68f, bottomYMax), TableBg, PaperBorder);
        CreateText(box2.transform, new Vector2(0.04f, 0.05f), new Vector2(0.96f, 0.95f),
            $"<b>MANNER OF DEATH:</b>\n<b>[X] {f.manner_of_death}</b>\n[ ] Accident   [ ] Suicide",
            TextAnchor.UpperLeft, 10, InkBlack);

        // Ô 3: Bác sĩ pháp y chủ trì & Chữ ký
        GameObject box3 = CreateBox(crt, new Vector2(0.69f, bottomYMin), new Vector2(1.0f, bottomYMax), TableBg, PaperBorder);
        CreateText(box3.transform, new Vector2(0.04f, 0.05f), new Vector2(0.96f, 0.95f),
            "<b>CORONER PATHOLOGIST:</b>\nDr. Whitby Lodge, MD\n<i><color=#1a1a24>Whitby Lodge, MD</color></i> (Signature)",
            TextAnchor.UpperLeft, 10, InkBlack);

        // Con dấu đỏ Viện Pháp Y đóng đè lên bảng chữ ký
        CreateStamp(box2.transform, new Vector2(0.50f, 0.50f), "HOMICIDE\nMED-LEGAL", InkRed, -8f);
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
        rt.sizeDelta = new Vector2(130f, 44f);
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
        txt.fontSize = 10;
        txt.fontStyle = FontStyle.Bold;
        txt.alignment = TextAnchor.MiddleCenter;
        txt.color = stampColor;
        txt.text = stampText;
        txt.horizontalOverflow = HorizontalWrapMode.Overflow;
        txt.verticalOverflow = VerticalWrapMode.Overflow;
        txt.raycastTarget = false;
    }
}
