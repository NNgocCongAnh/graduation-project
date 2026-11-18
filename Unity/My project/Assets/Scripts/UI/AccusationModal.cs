using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// Bảng Chỉ Định Thủ Phạm & Đối Soát Lập Luận (Accusation & Deductive Reasoning Modal)
/// Thiết kế tối giản theo yêu cầu:
/// 1. Dropdown chọn 1 trong số các nghi phạm làm hung thủ.
/// 2. Ô nhập văn bản tự do để điền dẫn chứng / lập luận suy luận (tùy chọn).
/// 3. Nút Gửi lệnh bắt giữ:
///    - So khớp hung thủ với ground_truth.culprit_id.
///    - So khớp lập luận với ground_truth.core_contradiction, giờ tử vong, hung khí (nếu người chơi có nhập).
///    - Bật màn hình Phán quyết (Verdict Panel) công bố kết quả và sự thật vụ án.
/// </summary>
public class AccusationModal : MonoBehaviour
{
    private static AccusationModal _instance;
    public static AccusationModal Instance
    {
        get
        {
            if (_instance == null)
            {
#if UNITY_2022_2_OR_NEWER
                _instance = FindAnyObjectByType<AccusationModal>(FindObjectsInactive.Include);
#else
                _instance = FindObjectOfType<AccusationModal>(true);
#endif
            }
            return _instance;
        }
        private set => _instance = value;
    }

    [Header("Main Dialog References")]
    [SerializeField] private GameObject modalRoot;
    [SerializeField] private Dropdown suspectDropdown;
    [SerializeField] private Transform evidenceTogglesContainer;
    [SerializeField] private GameObject evidenceTogglePrefab;
    [SerializeField] private Button submitButton;
    [SerializeField] private Button closeButton;

    [Header("Verdict Result Panel References")]
    [SerializeField] private GameObject verdictPanel;
    [SerializeField] private Text verdictTitleText;
    [SerializeField] private Text verdictFeedbackText;
    [SerializeField] private Text coreContradictionText;
    [SerializeField] private Button closeVerdictButton;

    // State
    private string selectedSuspectId = "";
    private string selectedSuspectName = "";
    private string selectedSuspectOccupation = "";
    private InputField reasoningInputField;
    private Text warningText;
    private Text dropdownLabelText;
    private GameObject dropdownListPopup;
    private bool isDropdownOpen = false;

    public bool IsOpen => (modalRoot != null && modalRoot.activeSelf) || (verdictPanel != null && verdictPanel.activeSelf);

    private void Awake()
    {
        _instance = this;

        if (submitButton != null)
        {
            submitButton.onClick.RemoveAllListeners();
            submitButton.onClick.AddListener(OnSubmitButtonClicked);
        }

        if (closeButton != null)
        {
            closeButton.onClick.RemoveAllListeners();
            closeButton.onClick.AddListener(Close);
        }

        if (closeVerdictButton != null)
        {
            closeVerdictButton.onClick.RemoveAllListeners();
            closeVerdictButton.onClick.AddListener(CloseVerdict);
        }

        if (suspectDropdown != null)
        {
            suspectDropdown.gameObject.SetActive(false);
        }

        if (modalRoot != null) modalRoot.SetActive(false);
        if (verdictPanel != null) verdictPanel.SetActive(false);
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
        Canvas canvas = GetComponentInParent<Canvas>() ?? FindObjectOfType<Canvas>(true);
        if (canvas != null && transform.parent != canvas.transform)
        {
            transform.SetParent(canvas.transform, false);
        }

        if (modalRoot == null) modalRoot = gameObject;
        modalRoot.SetActive(true);
        gameObject.SetActive(true);

        if (verdictPanel != null) verdictPanel.SetActive(false);
        transform.SetAsLastSibling();

        BuildSimplifiedAccusationUI();
    }

    public void Close()
    {
        if (dropdownListPopup != null) dropdownListPopup.SetActive(false);
        isDropdownOpen = false;
        if (modalRoot != null) modalRoot.SetActive(false);
        if (verdictPanel != null) verdictPanel.SetActive(false);
        gameObject.SetActive(false);
    }

    public void CloseVerdict()
    {
        if (verdictPanel != null) verdictPanel.SetActive(false);
        Close();
    }

    /// <summary>
    /// Xây dựng giao diện tối giản: 1 Dropdown chọn nghi phạm + 1 Ô nhập văn bản lập luận + Nút gửi
    /// </summary>
    private void BuildSimplifiedAccusationUI()
    {
        CaseDossier currentCase = GameController.Instance != null ? GameController.Instance.currentCase : null;
        if (currentCase == null || evidenceTogglesContainer == null) return;

        // Reset container
        foreach (Transform child in evidenceTogglesContainer)
        {
            Destroy(child.gameObject);
        }

        RectTransform cRt = evidenceTogglesContainer.GetComponent<RectTransform>();
        if (cRt != null)
        {
            cRt.anchorMin = new Vector2(0.05f, 0.17f);
            cRt.anchorMax = new Vector2(0.95f, 0.90f);
            cRt.offsetMin = Vector2.zero;
            cRt.offsetMax = Vector2.zero;
        }

        Font font = DetectiveAssetBank.GetDefaultUIFont();
        List<SuspectData> suspects = currentCase.suspects ?? new List<SuspectData>();

        // Tự động chọn nghi phạm đầu tiên nếu chưa chọn
        if (string.IsNullOrEmpty(selectedSuspectId) && suspects.Count > 0)
        {
            selectedSuspectId = suspects[0].id;
            selectedSuspectName = suspects[0].name;
            selectedSuspectOccupation = suspects[0].occupation;
        }

        // =========================================================================
        // 1. NHÃN CẢNH BÁO (WARNING LABEL TRÊN CÙNG)
        // =========================================================================
        GameObject warnGo = new GameObject("WarningText", typeof(RectTransform), typeof(Text));
        RectTransform wRt = warnGo.GetComponent<RectTransform>();
        wRt.SetParent(evidenceTogglesContainer, false);
        wRt.anchorMin = new Vector2(0f, 0.94f);
        wRt.anchorMax = new Vector2(1f, 1.0f);
        wRt.sizeDelta = Vector2.zero;
        warningText = warnGo.GetComponent<Text>();
        warningText.font = font;
        warningText.fontSize = 11;
        warningText.fontStyle = FontStyle.Bold;
        warningText.alignment = TextAnchor.MiddleCenter;
        warningText.color = new Color(1f, 0.35f, 0.35f);
        warningText.text = "";

        // =========================================================================
        // 2. PHẦN 1: TIÊU ĐỀ & DROPDOWN CHỌN NGHI PHẠM
        // =========================================================================
        GameObject sTitleGo = new GameObject("SuspectSectionTitle", typeof(RectTransform), typeof(Text));
        RectTransform stRt = sTitleGo.GetComponent<RectTransform>();
        stRt.SetParent(evidenceTogglesContainer, false);
        stRt.anchorMin = new Vector2(0f, 0.85f);
        stRt.anchorMax = new Vector2(1f, 0.93f);
        stRt.sizeDelta = Vector2.zero;
        Text stText = sTitleGo.GetComponent<Text>();
        stText.font = font;
        stText.fontSize = 12;
        stText.fontStyle = FontStyle.Bold;
        stText.alignment = TextAnchor.MiddleLeft;
        stText.color = new Color(0.96f, 0.82f, 0.38f);
        stText.text = "🎯 BƯỚC 1: CHỌN HUNG THỦ CẦN BẮT GIỮ (BẮT BUỘC):";

        // Dropdown Selector Button
        GameObject dropBtnGo = new GameObject("DropdownSelectorBtn", typeof(RectTransform), typeof(Image), typeof(Button));
        RectTransform dRt = dropBtnGo.GetComponent<RectTransform>();
        dRt.SetParent(evidenceTogglesContainer, false);
        dRt.anchorMin = new Vector2(0f, 0.70f);
        dRt.anchorMax = new Vector2(1f, 0.83f);
        dRt.sizeDelta = Vector2.zero;

        Image dImg = dropBtnGo.GetComponent<Image>();
        dImg.color = new Color(0.18f, 0.20f, 0.25f, 1f);

        Outline dOutline = dropBtnGo.AddComponent<Outline>();
        dOutline.effectColor = new Color(0.8f, 0.65f, 0.25f, 0.8f);
        dOutline.effectDistance = new Vector2(1.5f, -1.5f);

        Button dropBtn = dropBtnGo.GetComponent<Button>();
        dropBtn.onClick.AddListener(() =>
        {
            isDropdownOpen = !isDropdownOpen;
            if (dropdownListPopup != null)
            {
                dropdownListPopup.SetActive(isDropdownOpen);
                if (isDropdownOpen) dropdownListPopup.transform.SetAsLastSibling();
            }
            AudioManager.Instance?.PlayPinClick();
        });

        // Label bên trong Dropdown Selector
        GameObject dLabelGo = new GameObject("Label", typeof(RectTransform), typeof(Text));
        RectTransform dlRt = dLabelGo.GetComponent<RectTransform>();
        dlRt.SetParent(dropBtnGo.transform, false);
        dlRt.anchorMin = new Vector2(0.03f, 0f);
        dlRt.anchorMax = new Vector2(0.97f, 1f);
        dlRt.sizeDelta = Vector2.zero;

        dropdownLabelText = dLabelGo.GetComponent<Text>();
        dropdownLabelText.font = font;
        dropdownLabelText.fontSize = 12;
        dropdownLabelText.fontStyle = FontStyle.Bold;
        dropdownLabelText.alignment = TextAnchor.MiddleLeft;
        dropdownLabelText.color = Color.white;
        dropdownLabelText.text = $"👤 Hung thủ chỉ định:  [ {selectedSuspectName} ({selectedSuspectOccupation}) ]  ▼";

        // =========================================================================
        // 3. PHẦN 2: TIÊU ĐỀ & KHUNG NHẬP DẪN CHỨNG LẬP LUẬN
        // =========================================================================
        GameObject rTitleGo = new GameObject("ReasoningSectionTitle", typeof(RectTransform), typeof(Text));
        RectTransform rtRt = rTitleGo.GetComponent<RectTransform>();
        rtRt.SetParent(evidenceTogglesContainer, false);
        rtRt.anchorMin = new Vector2(0f, 0.58f);
        rtRt.anchorMax = new Vector2(1f, 0.67f);
        rtRt.sizeDelta = Vector2.zero;
        Text rtText = rTitleGo.GetComponent<Text>();
        rtText.font = font;
        rtText.fontSize = 12;
        rtText.fontStyle = FontStyle.Bold;
        rtText.alignment = TextAnchor.MiddleLeft;
        rtText.color = new Color(0.65f, 0.88f, 1f);
        rtText.text = "✍️ BƯỚC 2: DẪN CHỨNG & LẬP LUẬN SUY LUẬN (TÙY CHỌN):";

        // InputField Container
        GameObject inputFieldGo = new GameObject("ReasoningInputField", typeof(RectTransform), typeof(Image), typeof(InputField));
        RectTransform ifRt = inputFieldGo.GetComponent<RectTransform>();
        ifRt.SetParent(evidenceTogglesContainer, false);
        ifRt.anchorMin = new Vector2(0f, 0.08f);
        ifRt.anchorMax = new Vector2(1f, 0.56f);
        ifRt.sizeDelta = Vector2.zero;

        Image ifImg = inputFieldGo.GetComponent<Image>();
        ifImg.color = new Color(0.10f, 0.11f, 0.14f, 0.98f);

        Outline ifOutline = inputFieldGo.AddComponent<Outline>();
        ifOutline.effectColor = new Color(0.35f, 0.40f, 0.50f, 0.6f);
        ifOutline.effectDistance = new Vector2(1f, -1f);

        reasoningInputField = inputFieldGo.GetComponent<InputField>();
        reasoningInputField.lineType = InputField.LineType.MultiLineNewline;

        // Text Component bên trong InputField
        GameObject textCompGo = new GameObject("Text", typeof(RectTransform), typeof(Text));
        RectTransform tcRt = textCompGo.GetComponent<RectTransform>();
        tcRt.SetParent(inputFieldGo.transform, false);
        tcRt.anchorMin = new Vector2(0.02f, 0.05f);
        tcRt.anchorMax = new Vector2(0.98f, 0.95f);
        tcRt.sizeDelta = Vector2.zero;

        Text textComp = textCompGo.GetComponent<Text>();
        textComp.font = font;
        textComp.fontSize = 11;
        textComp.color = new Color(0.95f, 0.95f, 0.95f);
        textComp.lineSpacing = 1.25f;
        textComp.supportRichText = false;
        reasoningInputField.textComponent = textComp;

        // Placeholder Component
        GameObject phGo = new GameObject("Placeholder", typeof(RectTransform), typeof(Text));
        RectTransform phRt = phGo.GetComponent<RectTransform>();
        phRt.SetParent(inputFieldGo.transform, false);
        phRt.anchorMin = new Vector2(0.02f, 0.05f);
        phRt.anchorMax = new Vector2(0.98f, 0.95f);
        phRt.sizeDelta = Vector2.zero;

        Text phText = phGo.GetComponent<Text>();
        phText.font = font;
        phText.fontSize = 11;
        phText.fontStyle = FontStyle.Italic;
        phText.color = new Color(0.55f, 0.60f, 0.70f, 0.8f);
        phText.lineSpacing = 1.25f;
        phText.text = "Nhập suy luận tóm tắt của bạn: mâu thuẫn ngoại phạm, hung khí thật sự, giờ tử vong (Henssge)...\n\n(💡 Gợi ý: Bạn có thể để trống ô này nếu chỉ muốn đối chiếu nhanh phán quyết của Tòa án!)";
        reasoningInputField.placeholder = phText;

        // =========================================================================
        // 4. HƯỚNG DẪN DƯỚI CÙNG
        // =========================================================================
        GameObject tipGo = new GameObject("TipText", typeof(RectTransform), typeof(Text));
        RectTransform tipRt = tipGo.GetComponent<RectTransform>();
        tipRt.SetParent(evidenceTogglesContainer, false);
        tipRt.anchorMin = new Vector2(0f, 0f);
        tipRt.anchorMax = new Vector2(1f, 0.07f);
        tipRt.sizeDelta = Vector2.zero;
        Text tipText = tipGo.GetComponent<Text>();
        tipText.font = font;
        tipText.fontSize = 10;
        tipText.fontStyle = FontStyle.Normal;
        tipText.alignment = TextAnchor.MiddleLeft;
        tipText.color = new Color(0.65f, 0.70f, 0.78f);
        tipText.text = "⚖️ Tòa án sẽ đối chiếu hung thủ bạn chọn và so khớp lập luận với Chân lý vụ án (Ground Truth).";

        // =========================================================================
        // 5. DROPDOWN LIST POPUP (DANH SÁCH THẢ XUỐNG KHI CLICK DROPDOWN)
        // =========================================================================
        dropdownListPopup = new GameObject("DropdownListPopup", typeof(RectTransform), typeof(Image));
        RectTransform popRt = dropdownListPopup.GetComponent<RectTransform>();
        popRt.SetParent(evidenceTogglesContainer, false);
        popRt.anchorMin = new Vector2(0f, 0.28f);
        popRt.anchorMax = new Vector2(1f, 0.70f);
        popRt.sizeDelta = Vector2.zero;

        Image popImg = dropdownListPopup.GetComponent<Image>();
        popImg.color = new Color(0.12f, 0.13f, 0.16f, 0.98f);

        Outline popOutline = dropdownListPopup.AddComponent<Outline>();
        popOutline.effectColor = new Color(0.9f, 0.75f, 0.3f, 0.9f);
        popOutline.effectDistance = new Vector2(2f, -2f);

        float itemHeight = 1f / Mathf.Max(1, suspects.Count);
        for (int i = 0; i < suspects.Count; i++)
        {
            SuspectData susp = suspects[i];
            GameObject itemBtnGo = new GameObject($"Item_{susp.id}", typeof(RectTransform), typeof(Image), typeof(Button));
            RectTransform itemRt = itemBtnGo.GetComponent<RectTransform>();
            itemRt.SetParent(dropdownListPopup.transform, false);
            itemRt.anchorMin = new Vector2(0.01f, 1f - (i + 1) * itemHeight + 0.02f);
            itemRt.anchorMax = new Vector2(0.99f, 1f - i * itemHeight - 0.02f);
            itemRt.sizeDelta = Vector2.zero;

            Image itemImg = itemBtnGo.GetComponent<Image>();
            bool isCurrent = (susp.id == selectedSuspectId);
            itemImg.color = isCurrent ? new Color(0.65f, 0.20f, 0.20f, 1f) : new Color(0.18f, 0.20f, 0.24f, 1f);

            Button itemBtn = itemBtnGo.GetComponent<Button>();
            string sId = susp.id;
            string sName = susp.name;
            string sOcc = susp.occupation;
            itemBtn.onClick.AddListener(() =>
            {
                selectedSuspectId = sId;
                selectedSuspectName = sName;
                selectedSuspectOccupation = sOcc;

                if (dropdownLabelText != null)
                {
                    dropdownLabelText.text = $"👤 Hung thủ chỉ định:  [ {selectedSuspectName} ({selectedSuspectOccupation}) ]  ▼";
                }

                if (warningText != null) warningText.text = "";
                if (dropdownListPopup != null) dropdownListPopup.SetActive(false);
                isDropdownOpen = false;

                AudioManager.Instance?.PlayPinClick();
                BuildSimplifiedAccusationUI();
            });

            GameObject itemTxtGo = new GameObject("ItemText", typeof(RectTransform), typeof(Text));
            RectTransform itRt = itemTxtGo.GetComponent<RectTransform>();
            itRt.SetParent(itemBtnGo.transform, false);
            itRt.anchorMin = new Vector2(0.03f, 0f);
            itRt.anchorMax = new Vector2(0.97f, 1f);
            itRt.sizeDelta = Vector2.zero;

            Text itemTxt = itemTxtGo.GetComponent<Text>();
            itemTxt.font = font;
            itemTxt.fontSize = 11;
            itemTxt.fontStyle = FontStyle.Bold;
            itemTxt.alignment = TextAnchor.MiddleLeft;
            itemTxt.color = isCurrent ? new Color(1f, 0.95f, 0.4f) : Color.white;
            itemTxt.text = $"{(isCurrent ? "🎯 [ĐÃ CHỌN] " : "   ")}{susp.name}  —  <color=#cccccc>{susp.occupation}</color>  <size=9><color=#88bb88>(Ngoại phạm tự nhận: {susp.alibi_start}-{susp.alibi_end})</color></size>";
        }

        dropdownListPopup.SetActive(false);
        isDropdownOpen = false;
    }

    /// <summary>
    /// Xử lý gửi lệnh bắt giữ: So khớp Hung thủ & Đối soát lập luận với Ground Truth
    /// </summary>
    private void OnSubmitButtonClicked()
    {
        CaseDossier currentCase = GameController.Instance != null ? GameController.Instance.currentCase : null;
        if (currentCase == null) return;

        if (string.IsNullOrEmpty(selectedSuspectId))
        {
            if (warningText != null)
            {
                warningText.text = "⚠️ Vui lòng chọn 1 nghi phạm trong danh sách trước khi gửi lệnh bắt!";
            }
            AudioManager.Instance?.PlayPinClick();
            return;
        }

        SuspectData selectedSuspect = currentCase.suspects.Find(s => s.id == selectedSuspectId);
        bool isCulprit = (selectedSuspect != null && selectedSuspect.is_culprit) ||
                         (selectedSuspectId == currentCase.ground_truth?.culprit_id);

        string reasoning = reasoningInputField != null ? reasoningInputField.text.Trim() : "";
        bool hasReasoning = !string.IsNullOrEmpty(reasoning);

        AudioManager.Instance?.PlayConanClimaxTheme();

        // ---------------------------------------------------------------------
        // 1. TRƯỜNG HỢP BẮT SAI HUNG THỦ
        // ---------------------------------------------------------------------
        if (!isCulprit)
        {
            string innocentReason = selectedSuspect != null && !string.IsNullOrEmpty(selectedSuspect.secret_innocent_fact)
                ? selectedSuspect.secret_innocent_fact
                : "Đối tượng có ngoại phạm độc lập và không có động cơ/phương tiện thực hiện vụ án.";

            ShowVerdict(
                title: "❌ LỆNH BẮT GIỮ BỊ BÁC BỎ // BẮT OAN NGƯỜI VÔ TỘI",
                titleColor: new Color(0.92f, 0.25f, 0.25f),
                feedback: $"Tòa án và Viện Kiểm sát bác bỏ lệnh bắt giữ đối với <b>{selectedSuspectName}</b> ({selectedSuspectOccupation})!\n\n" +
                          $"<b>SỰ THẬT VỀ ĐỐI TƯỢNG VÔ CAN:</b>\n{innocentReason}\n\n" +
                          $"⚠️ <i>Cảnh báo: Bắt sai đối tượng vi phạm quy tắc tố tụng và tạo cơ hội cho kẻ thủ ác tẩu thoát. Hãy đối soát lại Báo cáo pháp y Henssge và các vật chứng hiện trường!</i>",
                contradiction: currentCase.ground_truth != null ? $"Hung thủ thật sự là {currentCase.ground_truth.culprit_id}" : "",
                score: 0
            );
            return;
        }

        // ---------------------------------------------------------------------
        // 2. TRƯỜNG HỢP BẮT ĐÚNG HUNG THỦ
        // ---------------------------------------------------------------------
        string coreContradiction = currentCase.ground_truth?.core_contradiction ?? "";
        string actualCrimeTime = currentCase.ground_truth?.actual_crime_time ?? "";

        if (!hasReasoning)
        {
            // Người chơi BỎ TRỐNG ô lập luận: Công nhận đúng hung thủ, hiển thị kết quả
            ShowVerdict(
                title: "⚖️ PHÁN QUYẾT: CHÍNH XÁC // BẮT GIỮ ĐÚNG HUNG THỦ",
                titleColor: new Color(0.2f, 0.82f, 0.45f),
                feedback: $"Chúc mừng Thám tử! Đối tượng <b>{selectedSuspectName}</b> ({selectedSuspectOccupation}) chính là thủ phạm thực sự của vụ án.\n\n" +
                          $"<b>TÓM TẮT DIỄN BIẾN VỤ ÁN:</b>\n{currentCase.summary}\n\n" +
                          $"<b>MÂU THUẪN THEN CHỐT VẠCH TRẦN HUNG THỦ (GROUND TRUTH):</b>\n{coreContradiction}\n\n" +
                          $"<b>THỜI ĐIỂM GÂY ÁN THẬT:</b> {actualCrimeTime}",
                contradiction: coreContradiction,
                score: 75
            );
        }
        else
        {
            // Người chơi CÓ NHẬP lập luận: Đối chiếu với Ground Truth
            int score = 70;
            List<string> matchedPoints = new List<string>();
            string lowerReasoning = reasoning.ToLowerInvariant();

            // So khớp giờ án mạng & Henssge
            if (!string.IsNullOrEmpty(actualCrimeTime) && (lowerReasoning.Contains(actualCrimeTime) || lowerReasoning.Contains("henssge") || lowerReasoning.Contains("nhiệt") || lowerReasoning.Contains("tử vong") || lowerReasoning.Contains("pháp y")))
            {
                score += 10;
                matchedPoints.Add("✓ Xác định chuẩn xác thời gian tử vong theo nhiệt học Henssge (+10đ)");
            }

            // So khớp mâu thuẫn ngoại phạm (từ core_contradiction)
            string[] flawKeywords = new string[] { "ngoại phạm", "sổ", "đồng hồ", "cháy", "vé", "tàu", "hầm", "bếp", "ấm", "thuốc", "vết thương", "mâu thuẫn", "giả", "vỡ", "dừng", "alibi", "lời khai" };
            int flawHits = 0;
            foreach (var kw in flawKeywords)
            {
                if (lowerReasoning.Contains(kw) && coreContradiction.ToLowerInvariant().Contains(kw))
                {
                    flawHits++;
                }
            }
            if (flawHits >= 1)
            {
                score += 15;
                matchedPoints.Add("✓ Bóc trần thành công mâu thuẫn ngoại phạm của đối tượng (+15đ)");
            }

            // So khớp hung khí & thương tích
            if (lowerReasoning.Contains("dao") || lowerReasoning.Contains("đâm") || lowerReasoning.Contains("vũ khí") || lowerReasoning.Contains("hung khí") || lowerReasoning.Contains("thuốc") || lowerReasoning.Contains("độc"))
            {
                score += 5;
                matchedPoints.Add("✓ Chỉ điểm đúng hung khí và cơ chế sát hại (+5đ)");
            }

            score = Mathf.Clamp(score, 70, 100);
            string pointsFeedback = matchedPoints.Count > 0 ? string.Join("\n", matchedPoints) : "• Lập luận phù hợp với hồ sơ vụ án.";

            ShowVerdict(
                title: score >= 90 ? "🏆 PHÁN QUYẾT TOÀN THẮNG // LẬP LUẬN XUẤT SẮC" : "⚖️ PHÁN QUYẾT: CHÍNH XÁC // LẬP LUẬN HỢP LỆ",
                titleColor: score >= 90 ? new Color(1f, 0.85f, 0.25f) : new Color(0.2f, 0.82f, 0.45f),
                feedback: $"Xuất sắc! Lập luận suy luận của bạn đã thuyết phục hoàn toàn Hội đồng xét xử.\n\n" +
                          $"<b>LẬP LUẬN CỦA BẠN:</b>\n\"{reasoning}\"\n\n" +
                          $"<b>ĐỐI CHIẾU DẪN CHỨNG:</b>\n{pointsFeedback}\n\n" +
                          $"<b>MÂU THUẪN THEN CHỐT VẠCH TRẦN HUNG THỦ (GROUND TRUTH):</b>\n{coreContradiction}\n\n" +
                          $"<b>THỜI ĐIỂM GÂY ÁN THẬT:</b> {actualCrimeTime}",
                contradiction: coreContradiction,
                score: score
            );
        }

        // Đồng bộ lên API Backend nếu có kết nối
        if (DetectiveAPIManager.Instance != null && currentCase != null)
        {
            var req = new VerifyRequest
            {
                case_id = currentCase.case_id,
                selected_suspect_id = selectedSuspectId,
                selected_evidence_ids = new List<string>()
            };
            DetectiveAPIManager.Instance.VerifyDeduction(req, (ok, res) => { });
        }
    }

    /// <summary>
    /// Hiển thị bảng phán quyết từ VerifyResponse (gọi từ GameController hoặc mạng)
    /// </summary>
    public void ShowVerdict(VerifyResponse response)
    {
        if (response == null) return;
        Color color = response.is_correct ? new Color(0.2f, 0.82f, 0.45f) : new Color(0.92f, 0.25f, 0.25f);
        string title = response.is_correct ? "⚖️ PHÁN QUYẾT: CHÍNH XÁC // BẮT GIỮ ĐÚNG HUNG THỦ" : "❌ LỆNH BẮT GIỮ BỊ BÁC BỎ // BẮT OAN";
        ShowVerdict(title, color, response.feedback, response.core_contradiction, Mathf.RoundToInt(response.score));
    }

    /// <summary>
    /// Hiển thị bảng phán quyết kết quả
    /// </summary>
    public void ShowVerdict(string title, Color titleColor, string feedback, string contradiction, int score)
    {
        if (modalRoot != null) modalRoot.SetActive(false);

        if (verdictPanel != null)
        {
            verdictPanel.SetActive(true);
            transform.SetAsLastSibling();

            if (verdictTitleText != null)
            {
                verdictTitleText.text = title;
                verdictTitleText.color = titleColor;
            }

            if (verdictFeedbackText != null)
            {
                verdictFeedbackText.text = $"<b>ĐIỂM ĐÁNH GIÁ: {score}/100</b>\n\n{feedback}";
            }

            if (coreContradictionText != null)
            {
                coreContradictionText.text = contradiction;
            }
        }
    }
}
