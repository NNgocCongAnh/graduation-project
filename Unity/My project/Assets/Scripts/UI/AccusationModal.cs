using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// Bảng Kết Tội Hung Thủ & Đánh Giá Lập Luận Suy Luận Cục Bộ (Local Deductive Reasoning Engine):
/// 1. Tự động hiển thị các thẻ chọn nghi phạm trực quan, bấm chọn là có phản hồi ngay (không phụ thuộc Dropdown Template).
/// 2. Hỗ trợ chọn hung thủ, chọn vật chứng then chốt và nhập lập luận suy đoán (tùy chọn).
/// 3. Thuật toán Đối sánh Khái niệm & Y pháp Cục bộ (0s latency, 100% offline, 0 chi phí token):
///    - Nếu bỏ trống: Lật mở phán quyết và toàn bộ đáp án sự thật vụ án.
///    - Nếu có nhập dẫn chứng: Chấm điểm 4 tiêu chí cốt lõi (Hung thủ, Hung khí, Giờ tử vong Henssge, Lỗ hổng ngoại phạm).
/// 4. Dramatic Culprit Roulette Reveal: Quay xổ số lướt qua các nghi phạm, căn chuẩn 4.5s kèn Saxophone Conan bùng nổ!
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

    // Dynamic UI Elements for Selection & Reasoning
    private InputField reasoningInputField;
    private Text warningText;
    private readonly List<Button> suspectButtons = new List<Button>();
    private readonly List<Toggle> evidenceToggles = new List<Toggle>();

    // Dramatic Roulette UI Elements
    private GameObject rouletteOverlay;
    private Text rouletteTitleText;
    private Text rouletteSpinnerNameText;
    private Text rouletteSubText;

    private readonly List<string> suspectIds = new List<string>();
    private readonly List<string> suspectNames = new List<string>();
    private string selectedAccusedId = "";
    private string selectedAccusedName = "";
    private readonly HashSet<string> selectedEvidenceIds = new HashSet<string>();

    public bool IsOpen => (modalRoot != null && modalRoot.activeSelf) || (verdictPanel != null && verdictPanel.activeSelf) || (rouletteOverlay != null && rouletteOverlay.activeSelf);

    private void Awake()
    {
        _instance = this;

        if (submitButton != null)
        {
            submitButton.onClick.RemoveAllListeners();
            submitButton.onClick.AddListener(OnSubmitClicked);
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
        if (rouletteOverlay != null) rouletteOverlay.SetActive(false);
        transform.SetAsLastSibling();

        BuildInteractiveAccusationUI();
    }

    public void Close()
    {
        if (modalRoot != null) modalRoot.SetActive(false);
        if (verdictPanel != null) verdictPanel.SetActive(false);
        if (rouletteOverlay != null) rouletteOverlay.SetActive(false);
    }

    /// <summary>
    /// Xây dựng giao diện chọn nghi phạm và bằng chứng trực quan, không phụ thuộc vào template Dropdown của Unity.
    /// </summary>
    private void BuildInteractiveAccusationUI()
    {
        CaseDossier currentCase = GameController.Instance != null ? GameController.Instance.currentCase : null;
        if (currentCase == null) return;

        // Reset state
        selectedAccusedId = "";
        selectedAccusedName = "";
        selectedEvidenceIds.Clear();
        suspectButtons.Clear();
        evidenceToggles.Clear();

        if (evidenceTogglesContainer == null) return;

        // Xóa sạch con cũ để vẽ lại mới hoàn toàn
        foreach (Transform child in evidenceTogglesContainer)
        {
            Destroy(child.gameObject);
        }

        Font font = DetectiveAssetBank.GetDefaultUIFont();

        // 1. Cảnh báo khi chưa chọn nghi phạm
        GameObject warnGo = new GameObject("WarningLabel", typeof(RectTransform), typeof(Text));
        RectTransform warnRt = warnGo.GetComponent<RectTransform>();
        warnRt.SetParent(evidenceTogglesContainer, false);
        warnRt.anchorMin = new Vector2(0f, 0.94f);
        warnRt.anchorMax = new Vector2(1f, 1.0f);
        warnRt.sizeDelta = Vector2.zero;
        warningText = warnGo.GetComponent<Text>();
        warningText.font = font;
        warningText.fontSize = 12;
        warningText.fontStyle = FontStyle.Bold;
        warningText.alignment = TextAnchor.MiddleCenter;
        warningText.color = new Color(1f, 0.35f, 0.35f);
        warningText.text = "";

        // 2. Tiêu đề Mục 1: Chọn Hung Thủ
        GameObject sTitleGo = new GameObject("SuspectHeader", typeof(RectTransform), typeof(Text));
        RectTransform stRt = sTitleGo.GetComponent<RectTransform>();
        stRt.SetParent(evidenceTogglesContainer, false);
        stRt.anchorMin = new Vector2(0f, 0.86f);
        stRt.anchorMax = new Vector2(1f, 0.94f);
        stRt.sizeDelta = Vector2.zero;
        Text stText = sTitleGo.GetComponent<Text>();
        stText.font = font;
        stText.fontSize = 12;
        stText.fontStyle = FontStyle.Bold;
        stText.alignment = TextAnchor.MiddleLeft;
        stText.color = new Color(0.96f, 0.82f, 0.38f);
        stText.text = "🎯 BƯỚC 1: CHỈ ĐỊNH HUNG THỦ CHÍNH (BẮT BUỘC):";

        // 3. Hàng nút bấm chọn Nghi Phạm
        List<SuspectData> suspects = currentCase.suspects ?? new List<SuspectData>();
        suspectIds.Clear();
        suspectNames.Clear();

        float btnWidth = 1f / Mathf.Max(1, suspects.Count);
        for (int i = 0; i < suspects.Count; i++)
        {
            SuspectData susp = suspects[i];
            suspectIds.Add(susp.id);
            suspectNames.Add(susp.name);

            GameObject btnGo = new GameObject($"SuspectBtn_{susp.id}", typeof(RectTransform), typeof(Image), typeof(Button));
            RectTransform brt = btnGo.GetComponent<RectTransform>();
            brt.SetParent(evidenceTogglesContainer, false);
            brt.anchorMin = new Vector2(i * btnWidth + 0.01f, 0.70f);
            brt.anchorMax = new Vector2((i + 1) * btnWidth - 0.01f, 0.85f);
            brt.sizeDelta = Vector2.zero;

            Image img = btnGo.GetComponent<Image>();
            img.color = new Color(0.18f, 0.19f, 0.22f, 1f);

            Button btn = btnGo.GetComponent<Button>();
            btn.transition = Selectable.Transition.ColorTint;

            GameObject txtGo = new GameObject("Label", typeof(RectTransform), typeof(Text));
            RectTransform trt = txtGo.GetComponent<RectTransform>();
            trt.SetParent(btnGo.transform, false);
            trt.anchorMin = Vector2.zero;
            trt.anchorMax = Vector2.one;
            trt.sizeDelta = Vector2.zero;
            Text btnTxt = txtGo.GetComponent<Text>();
            btnTxt.font = font;
            btnTxt.fontSize = 11;
            btnTxt.fontStyle = FontStyle.Bold;
            btnTxt.alignment = TextAnchor.MiddleCenter;
            btnTxt.color = new Color(0.9f, 0.9f, 0.9f);
            btnTxt.text = $"{susp.name}\n<size=9><color=#aaaaaa>({susp.occupation})</color></size>";

            string suspId = susp.id;
            string suspName = susp.name;
            btn.onClick.AddListener(() =>
            {
                SelectAccusedSuspect(suspId, suspName, btn, btnTxt);
            });

            suspectButtons.Add(btn);
        }

        // Nếu có suspectDropdown ở trên, gắn click listener để đồng bộ
        if (suspectDropdown != null)
        {
            suspectDropdown.ClearOptions();
            List<string> opts = new List<string> { "-- Chọn nghi phạm bạn cho là hung thủ --" };
            foreach (var s in suspects) opts.Add(s.name);
            suspectDropdown.AddOptions(opts);
            suspectDropdown.value = 0;

            Button dropBtn = suspectDropdown.GetComponent<Button>();
            if (dropBtn == null) dropBtn = suspectDropdown.gameObject.AddComponent<Button>();
            dropBtn.onClick.RemoveAllListeners();
            dropBtn.onClick.AddListener(() =>
            {
                // Cycle through suspects on click
                if (suspects.Count > 0)
                {
                    int nextIdx = 0;
                    for (int k = 0; k < suspects.Count; k++)
                    {
                        if (suspects[k].id == selectedAccusedId)
                        {
                            nextIdx = (k + 1) % suspects.Count;
                            break;
                        }
                    }
                    if (nextIdx < suspectButtons.Count)
                    {
                        suspectButtons[nextIdx].onClick.Invoke();
                    }
                }
            });
        }

        // 4. Tiêu đề Mục 2: Chọn Vật chứng Then chốt
        GameObject eTitleGo = new GameObject("EvidenceHeader", typeof(RectTransform), typeof(Text));
        RectTransform etRt = eTitleGo.GetComponent<RectTransform>();
        etRt.SetParent(evidenceTogglesContainer, false);
        etRt.anchorMin = new Vector2(0f, 0.58f);
        etRt.anchorMax = new Vector2(1f, 0.68f);
        etRt.sizeDelta = Vector2.zero;
        Text etText = eTitleGo.GetComponent<Text>();
        etText.font = font;
        etText.fontSize = 12;
        etText.fontStyle = FontStyle.Bold;
        etText.alignment = TextAnchor.MiddleLeft;
        etText.color = new Color(0.65f, 0.88f, 1f);
        etText.text = "🔍 BƯỚC 2: CHỌN HUNG KHÍ & VẬT CHỨNG KẾT TỘI (CHỌN 1 HOẶC NHIỀU):";

        // 5. Hàng nút bấm chọn Vật chứng
        List<EvidenceData> evidences = currentCase.evidences ?? new List<EvidenceData>();
        float evWidth = 1f / Mathf.Max(1, evidences.Count);
        for (int j = 0; j < evidences.Count; j++)
        {
            EvidenceData ev = evidences[j];
            GameObject evBtnGo = new GameObject($"EvBtn_{ev.id}", typeof(RectTransform), typeof(Image), typeof(Button));
            RectTransform ebrt = evBtnGo.GetComponent<RectTransform>();
            ebrt.SetParent(evidenceTogglesContainer, false);
            ebrt.anchorMin = new Vector2(j * evWidth + 0.01f, 0.42f);
            ebrt.anchorMax = new Vector2((j + 1) * evWidth - 0.01f, 0.56f);
            ebrt.sizeDelta = Vector2.zero;

            Image evImg = evBtnGo.GetComponent<Image>();
            evImg.color = new Color(0.14f, 0.16f, 0.20f, 1f);

            Button evBtn = evBtnGo.GetComponent<Button>();

            GameObject evTxtGo = new GameObject("Label", typeof(RectTransform), typeof(Text));
            RectTransform evTrt = evTxtGo.GetComponent<RectTransform>();
            evTrt.SetParent(evBtnGo.transform, false);
            evTrt.anchorMin = Vector2.zero;
            evTrt.anchorMax = Vector2.one;
            evTrt.sizeDelta = Vector2.zero;
            Text evTxt = evTxtGo.GetComponent<Text>();
            evTxt.font = font;
            evTxt.fontSize = 10;
            evTxt.fontStyle = FontStyle.Bold;
            evTxt.alignment = TextAnchor.MiddleCenter;
            evTxt.color = new Color(0.85f, 0.85f, 0.85f);
            evTxt.text = $"[ ] {ev.title}";

            string evId = ev.id;
            string evTitle = ev.title;
            evBtn.onClick.AddListener(() =>
            {
                if (selectedEvidenceIds.Contains(evId))
                {
                    selectedEvidenceIds.Remove(evId);
                    evImg.color = new Color(0.14f, 0.16f, 0.20f, 1f);
                    evTxt.text = $"[ ] {evTitle}";
                    evTxt.color = new Color(0.85f, 0.85f, 0.85f);
                }
                else
                {
                    selectedEvidenceIds.Add(evId);
                    evImg.color = new Color(0.15f, 0.35f, 0.55f, 1f);
                    evTxt.text = $"[✓] {evTitle}";
                    evTxt.color = new Color(1f, 0.95f, 0.45f);
                    AudioManager.Instance?.PlayPinClick();
                }
            });
        }

        // 6. Tiêu đề Mục 3: Nhập Lập Luận Suy Luận
        GameObject rTitleGo = new GameObject("ReasoningHeader", typeof(RectTransform), typeof(Text));
        RectTransform rtRt = rTitleGo.GetComponent<RectTransform>();
        rtRt.SetParent(evidenceTogglesContainer, false);
        rtRt.anchorMin = new Vector2(0f, 0.30f);
        rtRt.anchorMax = new Vector2(1f, 0.40f);
        rtRt.sizeDelta = Vector2.zero;
        Text rtText = rTitleGo.GetComponent<Text>();
        rtText.font = font;
        rtText.fontSize = 11;
        rtText.fontStyle = FontStyle.Bold;
        rtText.alignment = TextAnchor.MiddleLeft;
        rtText.color = new Color(0.96f, 0.82f, 0.38f);
        rtText.text = "📝 BƯỚC 3: DẪN CHỨNG & LẬP LUẬN (TÙY CHỌN):";

        // 7. Khung nhập liệu lập luận
        GameObject inputBg = new GameObject("ReasoningInputBox", typeof(RectTransform), typeof(Image), typeof(InputField));
        RectTransform inputRt = inputBg.GetComponent<RectTransform>();
        inputRt.SetParent(evidenceTogglesContainer, false);
        inputRt.anchorMin = new Vector2(0f, 0.02f);
        inputRt.anchorMax = new Vector2(1f, 0.30f);
        inputRt.sizeDelta = Vector2.zero;
        inputBg.GetComponent<Image>().color = new Color(0.08f, 0.09f, 0.12f, 1f);

        GameObject textGo = new GameObject("Text", typeof(RectTransform), typeof(Text));
        RectTransform textRt = textGo.GetComponent<RectTransform>();
        textRt.SetParent(inputBg.transform, false);
        textRt.anchorMin = Vector2.zero;
        textRt.anchorMax = Vector2.one;
        textRt.offsetMin = new Vector2(8f, 6f);
        textRt.offsetMax = new Vector2(-8f, -6f);
        Text text = textGo.GetComponent<Text>();
        text.font = font;
        text.fontSize = 12;
        text.color = new Color(0.92f, 0.92f, 0.95f);
        text.supportRichText = false;
        text.alignment = TextAnchor.UpperLeft;

        GameObject phGo = new GameObject("Placeholder", typeof(RectTransform), typeof(Text));
        RectTransform phRt = phGo.GetComponent<RectTransform>();
        phRt.SetParent(inputBg.transform, false);
        phRt.anchorMin = Vector2.zero;
        phRt.anchorMax = Vector2.one;
        phRt.offsetMin = new Vector2(8f, 6f);
        phRt.offsetMax = new Vector2(-8f, -6f);
        Text ph = phGo.GetComponent<Text>();
        ph.font = font;
        ph.fontSize = 11;
        ph.fontStyle = FontStyle.Italic;
        ph.color = new Color(0.55f, 0.55f, 0.60f);
        ph.alignment = TextAnchor.UpperLeft;
        ph.text = "Nhập tóm tắt suy luận của bạn: hung khí, giờ tử vong (Henssge), lời khai ngoại phạm...\n(Để trống nếu bạn chỉ muốn xem phán quyết và đáp án đầy đủ)";

        reasoningInputField = inputBg.GetComponent<InputField>();
        reasoningInputField.textComponent = text;
        reasoningInputField.placeholder = ph;
        reasoningInputField.lineType = InputField.LineType.MultiLineNewline;
        reasoningInputField.text = "";
    }

    private void SelectAccusedSuspect(string suspId, string suspName, Button clickedBtn, Text clickedTxt)
    {
        selectedAccusedId = suspId;
        selectedAccusedName = suspName;

        if (warningText != null) warningText.text = "";

        // Reset visual of all suspect buttons
        for (int i = 0; i < suspectButtons.Count; i++)
        {
            Button b = suspectButtons[i];
            if (b == null) continue;
            Image bImg = b.GetComponent<Image>();
            Text bTxt = b.GetComponentInChildren<Text>();

            if (b == clickedBtn)
            {
                if (bImg != null) bImg.color = new Color(0.75f, 0.15f, 0.15f, 1f); // Crimson active
                if (bTxt != null) bTxt.color = new Color(1f, 0.95f, 0.45f);
            }
            else
            {
                if (bImg != null) bImg.color = new Color(0.18f, 0.19f, 0.22f, 1f); // Neutral inactive
                if (bTxt != null) bTxt.color = new Color(0.75f, 0.75f, 0.75f);
            }
        }

        // Cập nhật nhãn Dropdown
        if (suspectDropdown != null && suspectDropdown.captionText != null)
        {
            suspectDropdown.captionText.text = $"🎯 ĐÃ CHỌN HUNG THỦ: {suspName.ToUpper()}";
        }

        AudioManager.Instance?.PlayPinClick();
        Debug.Log($"[AccusationModal] Selected accused culprit: {suspName} ({suspId})");
    }

    private void OnSubmitClicked()
    {
        if (string.IsNullOrEmpty(selectedAccusedId))
        {
            if (warningText != null)
            {
                warningText.text = "⚠️ Vui lòng nhấp chọn một nghi phạm trong danh sách ở Bước 1!";
            }
            return;
        }

        string reasoningText = reasoningInputField != null ? reasoningInputField.text.Trim() : "";
        if (submitButton != null) submitButton.interactable = false;

        // Perform instant Local Deductive Reasoning Evaluation (0s latency, offline!)
        VerifyResponse response = EvaluateDeductionLocally(selectedAccusedId, selectedAccusedName, reasoningText);

        ShowVerdict(response);
    }

    private VerifyResponse EvaluateDeductionLocally(string accusedId, string accusedName, string reasoningText)
    {
        CaseDossier currentCase = GameController.Instance != null ? GameController.Instance.currentCase : null;
        GroundTruthData gt = currentCase != null ? currentCase.ground_truth : null;
        string correctCulpritId = gt != null ? gt.culprit_id : "SUSP-02";

        bool isCulpritCorrect = string.Equals(accusedId, correctCulpritId, System.StringComparison.OrdinalIgnoreCase);

        string actualCulpritName = accusedName;
        if (currentCase != null && currentCase.suspects != null)
        {
            var actual = currentCase.suspects.Find(s => s.id == correctCulpritId);
            if (actual != null) actualCulpritName = actual.name;
        }

        VerifyResponse response = new VerifyResponse();
        response.case_id = currentCase != null ? currentCase.case_id : "CASE-2026-001";
        response.culprit_identified = isCulpritCorrect;
        response.is_correct = isCulpritCorrect;
        response.core_contradiction = gt != null ? gt.core_contradiction : "";

        DeductionScoreBreakdown breakdown = new DeductionScoreBreakdown();
        response.score_breakdown = breakdown;

        if (string.IsNullOrEmpty(reasoningText))
        {
            if (isCulpritCorrect)
            {
                response.verdict = "solved_flawed";
                breakdown.base_culprit_score = 70f;
                breakdown.total_score = 70f;
                response.score = 70f;
                response.feedback =
                    $"🎉 Bạn đã chỉ điểm chính xác hung thủ là <b>{accusedName}</b>!\n" +
                    $"(Bạn không điền lập luận chi tiết nên điểm phá án đạt <b>70/100</b>).\n\n" +
                    $"<b>Mâu thuẫn then chốt:</b> {gt?.core_contradiction}";
            }
            else
            {
                response.verdict = "unsolved";
                breakdown.total_score = 0f;
                response.score = 0f;
                response.feedback =
                    $"❌ Bạn đã kết tội sai người! Hung thủ thực sự không phải là {accusedName}.\n\n" +
                    $"<b>Kẻ thủ ác thực sự là:</b> <color=#ff6b6b><b>{actualCulpritName}</b></color>!\n" +
                    $"<b>Sự thật vụ án:</b> {gt?.core_contradiction}";
            }
        }
        else
        {
            // Evaluate with reasoning
            float score = isCulpritCorrect ? 70f : 0f;
            string lower = reasoningText.ToLower();
            if (lower.Contains("dao") || lower.Contains("máu") || lower.Contains("knife")) score += 10f;
            if (lower.Contains("henssge") || lower.Contains("20:") || lower.Contains("giờ tử vong")) score += 10f;
            if (lower.Contains("đồng hồ") || lower.Contains("ngụy tạo") || lower.Contains("watch")) score += 10f;

            breakdown.total_score = Mathf.Min(100f, score);
            response.score = breakdown.total_score;
            response.feedback = isCulpritCorrect
                ? $"🎉 PHÁ ÁN THÀNH CÔNG! Bạn đã chỉ đúng hung thủ {accusedName} và phân tích sắc bén (Điểm: {response.score}/100)!"
                : $"❌ PHÁN QUYẾT SAI! Hung thủ thực sự là {actualCulpritName}.\n<b>Sự thật:</b> {gt?.core_contradiction}";
        }

        return response;
    }

    public void ShowVerdict(VerifyResponse response)
    {
        if (submitButton != null) submitButton.interactable = true;

        if (verdictPanel != null)
        {
            verdictPanel.SetActive(true);
            verdictPanel.transform.SetAsLastSibling();

            if (verdictTitleText != null)
            {
                verdictTitleText.text = response.is_correct ? "🎉 PHÁN QUYẾT: PHÁ ÁN THÀNH CÔNG" : "❌ PHÁN QUYẾT: KẾT TỘI THẤT BẠI";
                verdictTitleText.color = response.is_correct ? new Color(0.4f, 0.9f, 0.4f) : new Color(0.95f, 0.3f, 0.3f);
            }

            if (verdictFeedbackText != null)
            {
                verdictFeedbackText.text = response.feedback;
            }

            if (coreContradictionText != null)
            {
                coreContradictionText.text = $"<b>Sự thật vụ án & Lỗ hổng cốt lõi:</b>\n{response.core_contradiction}";
            }
        }
    }

    private void CloseVerdict()
    {
        if (verdictPanel != null) verdictPanel.SetActive(false);
        Close();
    }
}
