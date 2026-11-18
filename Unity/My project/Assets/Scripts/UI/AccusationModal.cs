using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// Bảng Điều Tra 3 Chặng Mục Tiêu & Lệnh Bắt Giữ (Three Objectives & Accusation System)
/// Thiết kế chuẩn theo phong cách bóc tách phong bì niêm phong của Unsolved Case Files:
/// - Chặng 1: Minh oan cho người vô tội (Exonerate an innocent suspect)
/// - Chặng 2: Bẻ gãy hiện trường giả & Tìm hung khí (Shatter staged alibi & weapon)
/// - Chặng 3: Lệnh bắt giữ chính thức (Official Arrest Warrant & Final Conviction)
/// - Bonus Envelope: Tái hiện toàn cảnh vụ án (Full Narrative Epilogue Solution)
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

    public enum ObjectiveStage
    {
        Stage1_Exonerate = 0,
        Stage2_ShatterAlibi = 1,
        Stage3_ArrestWarrant = 2
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

    [Header("Dramatic Roulette Overlay")]
    [SerializeField] private GameObject rouletteOverlay;
    [SerializeField] private Text rouletteTitleText;
    [SerializeField] private Text rouletteSpinnerNameText;
    [SerializeField] private Text rouletteSubText;

    // State 3 Phong Bì Mục Tiêu
    private ObjectiveStage activeStage = ObjectiveStage.Stage1_Exonerate;
    private bool stage1Done = false;
    private bool stage2Done = false;
    private string stage1ExoneratedName = "";

    // Selection State cho Chặng 1
    private string selectedExonerateSuspectId = "";
    private string selectedExonerateSuspectName = "";
    private string selectedExonerateEvidenceId = "";

    // Selection State cho Chặng 3 (Lệnh bắt giữ)
    private string selectedAccusedId = "";
    private string selectedAccusedName = "";
    private readonly HashSet<string> selectedEvidenceIds = new HashSet<string>();

    private InputField reasoningInputField;
    private Text warningText;
    private readonly List<Button> suspectButtons = new List<Button>();
    private readonly List<Button> evidenceButtons = new List<Button>();

    public bool IsOpen => (modalRoot != null && modalRoot.activeSelf) || (verdictPanel != null && verdictPanel.activeSelf) || (rouletteOverlay != null && rouletteOverlay.activeSelf);

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

        CleanAndPrepareContainer();

        if (modalRoot != null) modalRoot.SetActive(false);
        if (verdictPanel != null) verdictPanel.SetActive(false);
    }

    private void CleanAndPrepareContainer()
    {
        if (suspectDropdown != null)
        {
            suspectDropdown.gameObject.SetActive(false);
        }

        if (evidenceTogglesContainer != null)
        {
            VerticalLayoutGroup vlg = evidenceTogglesContainer.GetComponent<VerticalLayoutGroup>();
            if (vlg != null)
            {
                vlg.enabled = false;
                Destroy(vlg);
            }

            RectTransform cRt = evidenceTogglesContainer.GetComponent<RectTransform>();
            if (cRt != null)
            {
                // Give full middle space from below header to action buttons
                cRt.anchorMin = new Vector2(0.04f, 0.19f);
                cRt.anchorMax = new Vector2(0.96f, 0.89f);
                cRt.offsetMin = Vector2.zero;
                cRt.offsetMax = Vector2.zero;
            }
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

        CleanAndPrepareContainer();

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
        gameObject.SetActive(false);
    }

    /// <summary>
    /// Xây dựng giao diện 3 Chặng Mục Tiêu chuẩn Unsolved Case Files.
    /// </summary>
    private void BuildInteractiveAccusationUI()
    {
        CleanAndPrepareContainer();

        CaseDossier currentCase = GameController.Instance != null ? GameController.Instance.currentCase : null;
        if (currentCase == null) return;

        if (evidenceTogglesContainer == null) return;

        // Xóa sạch container con cũ
        foreach (Transform child in evidenceTogglesContainer)
        {
            Destroy(child.gameObject);
        }

        suspectButtons.Clear();
        evidenceButtons.Clear();

        Font font = DetectiveAssetBank.GetDefaultUIFont();

        // =========================================================================
        // 1. THANH TABS 3 PHONG BÌ MỤC TIÊU TRÊN CÙNG
        // =========================================================================
        GameObject tabsRow = new GameObject("ObjectiveTabsRow", typeof(RectTransform));
        RectTransform tabsRt = tabsRow.GetComponent<RectTransform>();
        tabsRt.SetParent(evidenceTogglesContainer, false);
        tabsRt.anchorMin = new Vector2(0f, 0.91f);
        tabsRt.anchorMax = new Vector2(1f, 1.0f);
        tabsRt.sizeDelta = Vector2.zero;

        CreateTabButton(tabsRow.transform, new Vector2(0f, 0f), new Vector2(0.29f, 1f),
            stage1Done ? "✉️ MỤC TIÊU 1 [✓]" : "✉️ MỤC TIÊU 1\n<size=9>Minh oan</size>",
            activeStage == ObjectiveStage.Stage1_Exonerate,
            stage1Done ? new Color(0.2f, 0.55f, 0.25f, 1f) : new Color(0.7f, 0.2f, 0.2f, 1f),
            () => { activeStage = ObjectiveStage.Stage1_Exonerate; BuildInteractiveAccusationUI(); });

        CreateTabButton(tabsRow.transform, new Vector2(0.31f, 0f), new Vector2(0.60f, 1f),
            stage2Done ? "✉️ MỤC TIÊU 2 [✓]" : (stage1Done ? "✉️ MỤC TIÊU 2\n<size=9>Bẻ Alibi</size>" : "🔒 MỤC TIÊU 2\n<size=9>Niêm phong</size>"),
            activeStage == ObjectiveStage.Stage2_ShatterAlibi,
            stage2Done ? new Color(0.65f, 0.55f, 0.15f, 1f) : new Color(0.7f, 0.2f, 0.2f, 1f),
            () =>
            {
                activeStage = ObjectiveStage.Stage2_ShatterAlibi;
                BuildInteractiveAccusationUI();
            });

        CreateTabButton(tabsRow.transform, new Vector2(0.62f, 0f), new Vector2(0.91f, 1f),
            "⚖️ MỤC TIÊU 3\n<size=9>Lệnh bắt giữ</size>",
            activeStage == ObjectiveStage.Stage3_ArrestWarrant,
            new Color(0.75f, 0.18f, 0.18f, 1f),
            () => { activeStage = ObjectiveStage.Stage3_ArrestWarrant; BuildInteractiveAccusationUI(); });

        // Nút tắt mở khóa nhanh (Bắt khẩn cấp)
        CreateTabButton(tabsRow.transform, new Vector2(0.92f, 0f), new Vector2(1.0f, 1f),
            "⚡\n<size=8>Tắt</size>",
            false,
            new Color(0.25f, 0.26f, 0.30f, 1f),
            () => { activeStage = ObjectiveStage.Stage3_ArrestWarrant; BuildInteractiveAccusationUI(); });

        // =========================================================================
        // 2. VÙNG THÔNG BÁO / FEEDBACK TRẠNG THÁI
        // =========================================================================
        GameObject warnGo = new GameObject("WarningLabel", typeof(RectTransform), typeof(Text));
        RectTransform warnRt = warnGo.GetComponent<RectTransform>();
        warnRt.SetParent(evidenceTogglesContainer, false);
        warnRt.anchorMin = new Vector2(0f, 0.85f);
        warnRt.anchorMax = new Vector2(1f, 0.90f);
        warnRt.sizeDelta = Vector2.zero;
        warningText = warnGo.GetComponent<Text>();
        warningText.font = font;
        warningText.fontSize = 11;
        warningText.fontStyle = FontStyle.Bold;
        warningText.alignment = TextAnchor.MiddleCenter;
        warningText.color = new Color(1f, 0.4f, 0.4f);
        warningText.text = "";

        // =========================================================================
        // 3. NỘI DUNG THEO TỪNG CHẶNG MỤC TIÊU
        // =========================================================================
        if (activeStage == ObjectiveStage.Stage1_Exonerate)
        {
            BuildStage1Content(currentCase, font);
        }
        else if (activeStage == ObjectiveStage.Stage2_ShatterAlibi)
        {
            BuildStage2Content(currentCase, font);
        }
        else
        {
            BuildStage3Content(currentCase, font);
        }

        UpdateSubmitButtonVisual();
    }

    private void CreateTabButton(Transform parent, Vector2 min, Vector2 max, string title, bool isActive, Color activeColor, UnityEngine.Events.UnityAction action)
    {
        GameObject tabGo = new GameObject("TabBtn", typeof(RectTransform), typeof(Image), typeof(Button));
        RectTransform rt = tabGo.GetComponent<RectTransform>();
        rt.SetParent(parent, false);
        rt.anchorMin = min;
        rt.anchorMax = max;
        rt.sizeDelta = Vector2.zero;

        Image img = tabGo.GetComponent<Image>();
        img.color = isActive ? activeColor : new Color(0.14f, 0.15f, 0.18f, 0.95f);

        Outline outline = tabGo.AddComponent<Outline>();
        outline.effectColor = isActive ? new Color(1f, 0.85f, 0.35f, 0.9f) : new Color(0.3f, 0.3f, 0.35f, 0.6f);
        outline.effectDistance = new Vector2(1f, -1f);

        Button btn = tabGo.GetComponent<Button>();
        btn.onClick.AddListener(action);

        GameObject txtGo = new GameObject("Text", typeof(RectTransform), typeof(Text));
        RectTransform trt = txtGo.GetComponent<RectTransform>();
        trt.SetParent(tabGo.transform, false);
        trt.anchorMin = Vector2.zero;
        trt.anchorMax = Vector2.one;
        trt.sizeDelta = Vector2.zero;

        Text txt = txtGo.GetComponent<Text>();
        txt.font = DetectiveAssetBank.GetDefaultUIFont();
        txt.fontSize = 10;
        txt.fontStyle = FontStyle.Bold;
        txt.alignment = TextAnchor.MiddleCenter;
        txt.color = isActive ? Color.white : new Color(0.75f, 0.75f, 0.80f);
        txt.text = title;
        txt.raycastTarget = false;
    }

    // =========================================================================
    // NỘI DUNG CHẶNG 1: MINH OAN CHO NGƯỜI VÔ TỘI
    // =========================================================================
    private void BuildStage1Content(CaseDossier currentCase, Font font)
    {
        // Banner hướng dẫn
        GameObject bannerGo = new GameObject("Stage1Banner", typeof(RectTransform), typeof(Text));
        RectTransform brt = bannerGo.GetComponent<RectTransform>();
        brt.SetParent(evidenceTogglesContainer, false);
        brt.anchorMin = new Vector2(0f, 0.74f);
        brt.anchorMax = new Vector2(1f, 0.84f);
        brt.sizeDelta = Vector2.zero;
        Text bText = bannerGo.GetComponent<Text>();
        bText.font = font;
        bText.fontSize = 11;
        bText.fontStyle = FontStyle.Bold;
        bText.alignment = TextAnchor.MiddleLeft;
        bText.color = new Color(0.96f, 0.82f, 0.38f);
        bText.text = "✉️ PHONG BÌ MỤC TIÊU 1: MINH OAN CHO ĐỐI TƯỢNG VÔ TỘI (EXONERATION)\n" +
                     "<size=10><color=#cccccc>Để thu hẹp diện điều tra, hãy chỉ định 1 nghi phạm bạn tin là vô can và 1 bằng chứng ngoại phạm xác đáng:</color></size>";

        // Hàng nút chọn Nghi phạm cần minh oan
        List<SuspectData> suspects = currentCase.suspects ?? new List<SuspectData>();
        float suspWidth = 1f / Mathf.Max(1, suspects.Count);
        for (int i = 0; i < suspects.Count; i++)
        {
            SuspectData susp = suspects[i];
            GameObject sBtnGo = new GameObject($"ExonerateSuspect_{susp.id}", typeof(RectTransform), typeof(Image), typeof(Button));
            RectTransform srt = sBtnGo.GetComponent<RectTransform>();
            srt.SetParent(evidenceTogglesContainer, false);
            srt.anchorMin = new Vector2(i * suspWidth + 0.01f, 0.53f);
            srt.anchorMax = new Vector2((i + 1) * suspWidth - 0.01f, 0.72f);
            srt.sizeDelta = Vector2.zero;

            Image sImg = sBtnGo.GetComponent<Image>();
            bool isSelected = (selectedExonerateSuspectId == susp.id);
            sImg.color = isSelected ? new Color(0.2f, 0.55f, 0.3f, 1f) : new Color(0.16f, 0.18f, 0.22f, 1f);

            Button sBtn = sBtnGo.GetComponent<Button>();
            string sId = susp.id;
            string sName = susp.name;
            sBtn.onClick.AddListener(() =>
            {
                selectedExonerateSuspectId = sId;
                selectedExonerateSuspectName = sName;
                AudioManager.Instance?.PlayPinClick();
                BuildInteractiveAccusationUI();
            });

            GameObject txtGo = new GameObject("Label", typeof(RectTransform), typeof(Text));
            RectTransform trt = txtGo.GetComponent<RectTransform>();
            trt.SetParent(sBtnGo.transform, false);
            trt.anchorMin = Vector2.zero;
            trt.anchorMax = Vector2.one;
            trt.sizeDelta = Vector2.zero;

            Text stxt = txtGo.GetComponent<Text>();
            stxt.font = font;
            stxt.fontSize = 11;
            stxt.fontStyle = FontStyle.Bold;
            stxt.alignment = TextAnchor.MiddleCenter;
            stxt.color = isSelected ? new Color(1f, 0.95f, 0.45f) : new Color(0.9f, 0.9f, 0.9f);
            stxt.text = $"{(isSelected ? "[✓] " : "")}{susp.name}\n<size=9><color=#aaaaaa>({susp.occupation})</color></size>\n<size=8><color=#88bb88>Alibi: {susp.alibi_start}-{susp.alibi_end}</color></size>";
        }

        // Tiêu đề chọn vật chứng alibi
        GameObject eTitleGo = new GameObject("EvTitle", typeof(RectTransform), typeof(Text));
        RectTransform etRt = eTitleGo.GetComponent<RectTransform>();
        etRt.SetParent(evidenceTogglesContainer, false);
        etRt.anchorMin = new Vector2(0f, 0.42f);
        etRt.anchorMax = new Vector2(1f, 0.50f);
        etRt.sizeDelta = Vector2.zero;
        Text etText = eTitleGo.GetComponent<Text>();
        etText.font = font;
        etText.fontSize = 11;
        etText.fontStyle = FontStyle.Bold;
        etText.alignment = TextAnchor.MiddleLeft;
        etText.color = new Color(0.65f, 0.88f, 1f);
        etText.text = "🔍 CHỌN VẬT CHỨNG / TÀI LIỆU CHỨNG MINH NGOẠI PHẠM:";

        // Danh sách vật chứng
        List<EvidenceData> evidences = currentCase.evidences ?? new List<EvidenceData>();
        float evWidth = 1f / Mathf.Max(1, evidences.Count);
        for (int j = 0; j < evidences.Count; j++)
        {
            EvidenceData ev = evidences[j];
            GameObject evBtnGo = new GameObject($"EvExBtn_{ev.id}", typeof(RectTransform), typeof(Image), typeof(Button));
            RectTransform evRt = evBtnGo.GetComponent<RectTransform>();
            evRt.SetParent(evidenceTogglesContainer, false);
            evRt.anchorMin = new Vector2(j * evWidth + 0.01f, 0.22f);
            evRt.anchorMax = new Vector2((j + 1) * evWidth - 0.01f, 0.40f);
            evRt.sizeDelta = Vector2.zero;

            Image evImg = evBtnGo.GetComponent<Image>();
            bool isEvSel = (selectedExonerateEvidenceId == ev.id);
            evImg.color = isEvSel ? new Color(0.18f, 0.45f, 0.65f, 1f) : new Color(0.14f, 0.16f, 0.20f, 1f);

            Button evBtn = evBtnGo.GetComponent<Button>();
            string evId = ev.id;
            evBtn.onClick.AddListener(() =>
            {
                selectedExonerateEvidenceId = evId;
                AudioManager.Instance?.PlayPinClick();
                BuildInteractiveAccusationUI();
            });

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
            evTxt.color = isEvSel ? new Color(1f, 0.95f, 0.45f) : new Color(0.85f, 0.85f, 0.85f);
            evTxt.text = $"{(isEvSel ? "[✓] " : "[ ] ")}{ev.title}";
        }

        // Hướng dẫn chân trang
        GameObject tipGo = new GameObject("Stage1Tip", typeof(RectTransform), typeof(Text));
        RectTransform tipRt = tipGo.GetComponent<RectTransform>();
        tipRt.SetParent(evidenceTogglesContainer, false);
        tipRt.anchorMin = new Vector2(0f, 0.02f);
        tipRt.anchorMax = new Vector2(1f, 0.18f);
        tipRt.sizeDelta = Vector2.zero;
        Text tipText = tipGo.GetComponent<Text>();
        tipText.font = font;
        tipText.fontSize = 10;
        tipText.fontStyle = FontStyle.Italic;
        tipText.alignment = TextAnchor.MiddleCenter;
        tipText.color = new Color(0.7f, 0.7f, 0.75f);
        tipText.text = "💡 Gợi ý điều tra: Đọc kỹ khung giờ tử vong thực tế từ Báo cáo giám định tử thi nhiệt học Henssge\n" +
                       "và đối chiếu với biên bản lấy lời khai của các nghi phạm để loại trừ người có bằng chứng ngoại phạm chắc chắn.";
    }

    // =========================================================================
    // NỘI DUNG CHẶNG 2: BẺ GÃY HIỆN TRƯỜNG GIẢ & HUNG KHÍ
    // =========================================================================
    private void BuildStage2Content(CaseDossier currentCase, Font font)
    {
        // Banner hướng dẫn
        GameObject bannerGo = new GameObject("Stage2Banner", typeof(RectTransform), typeof(Text));
        RectTransform brt = bannerGo.GetComponent<RectTransform>();
        brt.SetParent(evidenceTogglesContainer, false);
        brt.anchorMin = new Vector2(0f, 0.74f);
        brt.anchorMax = new Vector2(1f, 0.84f);
        brt.sizeDelta = Vector2.zero;
        Text bText = bannerGo.GetComponent<Text>();
        bText.font = font;
        bText.fontSize = 11;
        bText.fontStyle = FontStyle.Bold;
        bText.alignment = TextAnchor.MiddleLeft;
        bText.color = new Color(0.96f, 0.82f, 0.38f);
        bText.text = "✉️ PHONG BÌ MỤC TIÊU 2: BẺ GÃY HIỆN TRƯỜNG GIẢ & TÌM HUNG KHÍ\n" +
                     "<size=10><color=#cccccc>Đối chiếu Báo cáo nhiệt học Henssge, hãy chọn ít nhất 1 manh mối then chốt vạch trần mốc tử vong giả hoặc hung khí thật sự:</color></size>";

        if (stage1Done && !string.IsNullOrEmpty(stage1ExoneratedName))
        {
            GameObject exBadgeGo = new GameObject("ExonerateBadge", typeof(RectTransform), typeof(Text));
            RectTransform exRt = exBadgeGo.GetComponent<RectTransform>();
            exRt.SetParent(evidenceTogglesContainer, false);
            exRt.anchorMin = new Vector2(0f, 0.67f);
            exRt.anchorMax = new Vector2(1f, 0.73f);
            exRt.sizeDelta = Vector2.zero;
            Text exText = exBadgeGo.GetComponent<Text>();
            exText.font = font;
            exText.fontSize = 11;
            exText.fontStyle = FontStyle.Bold;
            exText.alignment = TextAnchor.MiddleLeft;
            exText.color = new Color(0.4f, 0.9f, 0.4f);
            exText.text = $"[✓ ĐÃ MINH OAN CHẶNG 1]: Đối tượng {stage1ExoneratedName} đã được loại trừ khỏi diện tình nghi.";
        }

        // Danh sách vật chứng để chọn bẻ alibi
        List<EvidenceData> evidences = currentCase.evidences ?? new List<EvidenceData>();
        float evWidth = 1f / Mathf.Max(1, evidences.Count);
        for (int j = 0; j < evidences.Count; j++)
        {
            EvidenceData ev = evidences[j];
            GameObject evBtnGo = new GameObject($"EvShatterBtn_{ev.id}", typeof(RectTransform), typeof(Image), typeof(Button));
            RectTransform evRt = evBtnGo.GetComponent<RectTransform>();
            evRt.SetParent(evidenceTogglesContainer, false);
            evRt.anchorMin = new Vector2(j * evWidth + 0.01f, 0.40f);
            evRt.anchorMax = new Vector2((j + 1) * evWidth - 0.01f, 0.62f);
            evRt.sizeDelta = Vector2.zero;

            Image evImg = evBtnGo.GetComponent<Image>();
            bool isSelected = selectedEvidenceIds.Contains(ev.id);
            evImg.color = isSelected ? new Color(0.65f, 0.45f, 0.15f, 1f) : new Color(0.14f, 0.16f, 0.20f, 1f);

            Button evBtn = evBtnGo.GetComponent<Button>();
            string evId = ev.id;
            string evTitle = ev.title;
            evBtn.onClick.AddListener(() =>
            {
                if (selectedEvidenceIds.Contains(evId))
                {
                    selectedEvidenceIds.Remove(evId);
                }
                else
                {
                    selectedEvidenceIds.Add(evId);
                    AudioManager.Instance?.PlayPinClick();
                }
                BuildInteractiveAccusationUI();
            });

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
            evTxt.color = isSelected ? new Color(1f, 0.95f, 0.45f) : new Color(0.85f, 0.85f, 0.85f);
            evTxt.text = $"{(isSelected ? "[✓] " : "[ ] ")}{ev.title}\n<size=8><color=#aaaaaa>({ev.location})</color></size>";
        }

        // Gợi ý
        GameObject tipGo = new GameObject("Stage2Tip", typeof(RectTransform), typeof(Text));
        RectTransform tipRt = tipGo.GetComponent<RectTransform>();
        tipRt.SetParent(evidenceTogglesContainer, false);
        tipRt.anchorMin = new Vector2(0f, 0.05f);
        tipRt.anchorMax = new Vector2(1f, 0.35f);
        tipRt.sizeDelta = Vector2.zero;
        Text tipText = tipGo.GetComponent<Text>();
        tipText.font = font;
        tipText.fontSize = 10;
        tipText.fontStyle = FontStyle.Normal;
        tipText.alignment = TextAnchor.MiddleLeft;
        tipText.color = new Color(0.85f, 0.85f, 0.90f);
        tipText.text = "<b>HƯỚNG DẪN ĐỐI SOÁT VẬT CHỨNG:</b>\n" +
                       "• Kiểm tra tình trạng dây cót / mặt kính của đồng hồ hiện trường so với kết quả nhiệt học Henssge.\n" +
                       "• Kiểm tra tình trạng bếp lò than và các vật dụng đun nước của nghi phạm khai ở bếp.\n" +
                       "• Kiểm tra đặc tính hung khí giấu kín tương thích với vết thương thấu tim nạn nhân.";
    }

    // =========================================================================
    // NỘI DUNG CHẶNG 3: LỆNH BẮT GIỮ HUNG THỦ CHÍNH THỨC
    // =========================================================================
    private void BuildStage3Content(CaseDossier currentCase, Font font)
    {
        // 1. Tiêu đề Mục 1: Chọn Hung Thủ
        GameObject sTitleGo = new GameObject("SuspectHeader", typeof(RectTransform), typeof(Text));
        RectTransform stRt = sTitleGo.GetComponent<RectTransform>();
        stRt.SetParent(evidenceTogglesContainer, false);
        stRt.anchorMin = new Vector2(0f, 0.77f);
        stRt.anchorMax = new Vector2(1f, 0.84f);
        stRt.sizeDelta = Vector2.zero;
        Text stText = sTitleGo.GetComponent<Text>();
        stText.font = font;
        stText.fontSize = 11;
        stText.fontStyle = FontStyle.Bold;
        stText.alignment = TextAnchor.MiddleLeft;
        stText.color = new Color(0.96f, 0.82f, 0.38f);
        stText.text = "🎯 BƯỚC 1: CHỈ ĐỊNH HUNG THỦ CHÍNH (BẮT BUỘC):";

        // 2. Hàng nút bấm chọn Nghi Phạm
        List<SuspectData> suspects = currentCase.suspects ?? new List<SuspectData>();
        float btnWidth = 1f / Mathf.Max(1, suspects.Count);
        for (int i = 0; i < suspects.Count; i++)
        {
            SuspectData susp = suspects[i];
            GameObject btnGo = new GameObject($"SuspectBtn_{susp.id}", typeof(RectTransform), typeof(Image), typeof(Button));
            RectTransform brt = btnGo.GetComponent<RectTransform>();
            brt.SetParent(evidenceTogglesContainer, false);
            brt.anchorMin = new Vector2(i * btnWidth + 0.01f, 0.59f);
            brt.anchorMax = new Vector2((i + 1) * btnWidth - 0.01f, 0.75f);
            brt.sizeDelta = Vector2.zero;

            Image img = btnGo.GetComponent<Image>();
            bool isSel = (selectedAccusedId == susp.id);
            img.color = isSel ? new Color(0.75f, 0.15f, 0.15f, 1f) : new Color(0.18f, 0.19f, 0.22f, 1f);

            Button btn = btnGo.GetComponent<Button>();
            string suspId = susp.id;
            string suspName = susp.name;
            btn.onClick.AddListener(() =>
            {
                selectedAccusedId = suspId;
                selectedAccusedName = suspName;
                AudioManager.Instance?.PlayPinClick();
                BuildInteractiveAccusationUI();
            });

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
            btnTxt.color = isSel ? new Color(1f, 0.95f, 0.45f) : new Color(0.9f, 0.9f, 0.9f);
            btnTxt.text = $"{(isSel ? "🎯 " : "")}{susp.name}\n<size=9><color=#aaaaaa>({susp.occupation})</color></size>";

            suspectButtons.Add(btn);
        }

        // 3. Tiêu đề Mục 2: Chọn Vật chứng Then chốt
        GameObject eTitleGo = new GameObject("EvidenceHeader", typeof(RectTransform), typeof(Text));
        RectTransform etRt = eTitleGo.GetComponent<RectTransform>();
        etRt.SetParent(evidenceTogglesContainer, false);
        etRt.anchorMin = new Vector2(0f, 0.49f);
        etRt.anchorMax = new Vector2(1f, 0.57f);
        etRt.sizeDelta = Vector2.zero;
        Text etText = eTitleGo.GetComponent<Text>();
        etText.font = font;
        etText.fontSize = 11;
        etText.fontStyle = FontStyle.Bold;
        etText.alignment = TextAnchor.MiddleLeft;
        etText.color = new Color(0.65f, 0.88f, 1f);
        etText.text = "🔍 BƯỚC 2: CHỌN HUNG KHÍ & VẬT CHỨNG KẾT TỘI:";

        // 4. Hàng nút bấm chọn Vật chứng
        List<EvidenceData> evidences = currentCase.evidences ?? new List<EvidenceData>();
        float evWidth = 1f / Mathf.Max(1, evidences.Count);
        for (int j = 0; j < evidences.Count; j++)
        {
            EvidenceData ev = evidences[j];
            GameObject evBtnGo = new GameObject($"EvBtn_{ev.id}", typeof(RectTransform), typeof(Image), typeof(Button));
            RectTransform ebrt = evBtnGo.GetComponent<RectTransform>();
            ebrt.SetParent(evidenceTogglesContainer, false);
            ebrt.anchorMin = new Vector2(j * evWidth + 0.01f, 0.32f);
            ebrt.anchorMax = new Vector2((j + 1) * evWidth - 0.01f, 0.48f);
            ebrt.sizeDelta = Vector2.zero;

            Image evImg = evBtnGo.GetComponent<Image>();
            bool isEvSel = selectedEvidenceIds.Contains(ev.id);
            evImg.color = isEvSel ? new Color(0.15f, 0.35f, 0.55f, 1f) : new Color(0.14f, 0.16f, 0.20f, 1f);

            Button evBtn = evBtnGo.GetComponent<Button>();
            string evId = ev.id;
            evBtn.onClick.AddListener(() =>
            {
                if (selectedEvidenceIds.Contains(evId))
                {
                    selectedEvidenceIds.Remove(evId);
                }
                else
                {
                    selectedEvidenceIds.Add(evId);
                    AudioManager.Instance?.PlayPinClick();
                }
                BuildInteractiveAccusationUI();
            });

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
            evTxt.color = isEvSel ? new Color(1f, 0.95f, 0.45f) : new Color(0.85f, 0.85f, 0.85f);
            evTxt.text = $"{(isEvSel ? "[✓] " : "[ ] ")}{ev.title}";
        }

        // 5. Tiêu đề Mục 3: Nhập Lập Luận Suy Luận
        GameObject rTitleGo = new GameObject("ReasoningHeader", typeof(RectTransform), typeof(Text));
        RectTransform rtRt = rTitleGo.GetComponent<RectTransform>();
        rtRt.SetParent(evidenceTogglesContainer, false);
        rtRt.anchorMin = new Vector2(0f, 0.22f);
        rtRt.anchorMax = new Vector2(1f, 0.30f);
        rtRt.sizeDelta = Vector2.zero;
        Text rtText = rTitleGo.GetComponent<Text>();
        rtText.font = font;
        rtText.fontSize = 11;
        rtText.fontStyle = FontStyle.Bold;
        rtText.alignment = TextAnchor.MiddleLeft;
        rtText.color = new Color(0.96f, 0.82f, 0.38f);
        rtText.text = "📝 BƯỚC 3: DẪN CHỨNG & LẬP LUẬN (TÙY CHỌN):";

        // 6. Khung nhập liệu lập luận
        GameObject inputBg = new GameObject("ReasoningInputBox", typeof(RectTransform), typeof(Image), typeof(InputField));
        RectTransform inputRt = inputBg.GetComponent<RectTransform>();
        inputRt.SetParent(evidenceTogglesContainer, false);
        inputRt.anchorMin = new Vector2(0f, 0.02f);
        inputRt.anchorMax = new Vector2(1f, 0.21f);
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
        text.fontSize = 11;
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
        ph.fontSize = 10;
        ph.fontStyle = FontStyle.Italic;
        ph.color = new Color(0.55f, 0.55f, 0.60f);
        ph.alignment = TextAnchor.UpperLeft;
        ph.text = "Nhập suy luận tóm tắt của bạn: hung khí, giờ tử vong (Henssge), mâu thuẫn lời khai...\n(Để trống nếu chỉ muốn xem phán quyết của Tòa án)";

        reasoningInputField = inputBg.GetComponent<InputField>();
        reasoningInputField.textComponent = text;
        reasoningInputField.placeholder = ph;
        reasoningInputField.lineType = InputField.LineType.MultiLineNewline;
        reasoningInputField.text = "";
    }

    private void UpdateSubmitButtonVisual()
    {
        if (submitButton == null) return;
        Text btnText = submitButton.GetComponentInChildren<Text>();
        if (btnText == null) return;

        if (activeStage == ObjectiveStage.Stage1_Exonerate)
        {
            btnText.text = "✉️ XÁC NHẬN MINH OAN // MỞ KHÓA MỤC TIÊU 2";
        }
        else if (activeStage == ObjectiveStage.Stage2_ShatterAlibi)
        {
            btnText.text = "✉️ XÁC NHẬN BẺ ALIBI // MỞ KHÓA MỤC TIÊU 3";
        }
        else
        {
            btnText.text = "⚖️ GỬI LỆNH BẮT GIỮ // TRÌNH TÒA PHÊ CHUẨN";
        }
    }

    private void OnSubmitButtonClicked()
    {
        if (activeStage == ObjectiveStage.Stage1_Exonerate)
        {
            SubmitStage1();
        }
        else if (activeStage == ObjectiveStage.Stage2_ShatterAlibi)
        {
            SubmitStage2();
        }
        else
        {
            SubmitStage3Final();
        }
    }

    // =========================================================================
    // XỬ LÝ NỘP MỤC TIÊU 1 (MINH OAN)
    // =========================================================================
    private void SubmitStage1()
    {
        if (string.IsNullOrEmpty(selectedExonerateSuspectId))
        {
            if (warningText != null)
            {
                warningText.text = "⚠️ Vui lòng nhấp chọn 1 nghi phạm để minh oan!";
                warningText.color = new Color(1f, 0.4f, 0.4f);
            }
            return;
        }

        CaseDossier currentCase = GameController.Instance != null ? GameController.Instance.currentCase : null;
        GroundTruthData gt = currentCase != null ? currentCase.ground_truth : null;
        string correctCulpritId = gt != null ? gt.culprit_id : "SUSP-01";

        bool isCulprit = string.Equals(selectedExonerateSuspectId, correctCulpritId, StringComparison.OrdinalIgnoreCase);

        if (isCulprit)
        {
            if (warningText != null)
            {
                warningText.text = $"❌ BÁC BỎ YÊU CẦU MINH OAN! Đối tượng {selectedExonerateSuspectName} có nhiều biểu hiện nghi vấn trực tiếp tại hiện trường. Không thể loại trừ khỏi diện tình nghi!";
                warningText.color = new Color(1f, 0.35f, 0.35f);
            }
        }
        else
        {
            stage1Done = true;
            stage1ExoneratedName = selectedExonerateSuspectName;
            activeStage = ObjectiveStage.Stage2_ShatterAlibi;
            AudioManager.Instance?.PlayPinClick();
            BuildInteractiveAccusationUI();
            if (warningText != null)
            {
                warningText.text = $"🎉 CHÍNH XÁC! {selectedExonerateSuspectName} đã được chứng minh vô tội. 🔓 ĐÃ MỞ KHÓA MỤC TIÊU 2!";
                warningText.color = new Color(0.4f, 0.95f, 0.4f);
            }
        }
    }

    // =========================================================================
    // XỬ LÝ NỘP MỤC TIÊU 2 (BẺ GÃY ALIBI)
    // =========================================================================
    private void SubmitStage2()
    {
        if (selectedEvidenceIds.Count == 0)
        {
            if (warningText != null)
            {
                warningText.text = "⚠️ Vui lòng chọn ít nhất 1 manh mối then chốt để bẻ gãy mốc thời gian giả!";
                warningText.color = new Color(1f, 0.4f, 0.4f);
            }
            return;
        }

        CaseDossier currentCase = GameController.Instance != null ? GameController.Instance.currentCase : null;
        bool hasCrucial = false;
        if (currentCase != null && currentCase.evidences != null)
        {
            foreach (string evId in selectedEvidenceIds)
            {
                var ev = currentCase.evidences.Find(e => e.id == evId);
                if (ev != null && ev.is_crucial)
                {
                    hasCrucial = true;
                    break;
                }
            }
        }

        if (hasCrucial)
        {
            stage2Done = true;
            activeStage = ObjectiveStage.Stage3_ArrestWarrant;
            AudioManager.Instance?.PlayPinClick();
            BuildInteractiveAccusationUI();
            if (warningText != null)
            {
                warningText.text = "🎉 XUẤT SẮC! Bạn đã vạch trần mốc tử vong ngụy tạo! 🔓 ĐÃ MỞ KHÓA MỤC TIÊU 3: LỆNH BẮT GIỮ!";
                warningText.color = new Color(0.4f, 0.95f, 0.4f);
            }
        }
        else
        {
            if (warningText != null)
            {
                warningText.text = "❌ CHƯA ĐỦ CĂN CỨ VẬT LÝ! Manh mối bạn chọn là hiện trường phụ hoặc bẫy nghi binh. Hãy đối chiếu kỹ lại Báo cáo nhiệt học Henssge!";
                warningText.color = new Color(1f, 0.35f, 0.35f);
            }
        }
    }

    // =========================================================================
    // XỬ LÝ NỘP MỤC TIÊU 3: LỆNH BẮT GIỮ CHÍNH THỨC
    // =========================================================================
    private void SubmitStage3Final()
    {
        if (string.IsNullOrEmpty(selectedAccusedId))
        {
            if (warningText != null)
            {
                warningText.text = "⚠️ Vui lòng nhấp chọn một nghi phạm bạn cho là hung thủ ở Bước 1!";
                warningText.color = new Color(1f, 0.4f, 0.4f);
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
        string correctCulpritId = gt != null ? gt.culprit_id : "SUSP-01";

        bool isCulpritCorrect = string.Equals(accusedId, correctCulpritId, System.StringComparison.OrdinalIgnoreCase);

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
                breakdown.base_culprit_score = 75f;
                breakdown.total_score = 80f;
                response.score = 80f;
                response.feedback =
                    $"🎉 PHÁ ÁN THÀNH CÔNG! Bạn đã chỉ định chính xác kẻ thủ ác là <b>{accusedName}</b>!\n" +
                    $"(Hoàn tất 3 chặng phá án theo đúng chuẩn Unsolved Case Files. Điểm số: <b>80/100</b>).";
            }
            else
            {
                response.verdict = "unsolved";
                breakdown.total_score = 0f;
                response.score = 0f;
                response.feedback =
                    $"❌ LỆNH BẮT GIỮ BỊ TÒA ÁN BÁC BỎ!\n\n" +
                    $"Căn cứ buộc tội đối với <b>{accusedName}</b> chưa đủ sức thuyết phục hoặc đã bắt nhầm người vô tội. " +
                    $"Hồ sơ đã được hoàn trả về bàn trinh thám để tiếp tục đối chiếu lời khai và vật chứng hiện trường!";
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
                ? $"🎉 PHÁ ÁN XUẤT SẮC! Bạn đã chỉ đúng hung thủ {accusedName} và lập luận sắc bén (Điểm: {response.score}/100)!"
                : $"❌ PHÁN QUYẾT SAI! Lệnh bắt giữ đối với {accusedName} bị bác bỏ do thiếu căn cứ xác đáng. Hãy quay lại bàn trinh thám và kiểm tra kỹ lại mâu thuẫn giữa lời khai ngoại phạm và các báo cáo pháp y!";
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

            // Bonus Envelope Solution (Toàn văn giải mã vụ án)
            if (coreContradictionText != null)
            {
                if (response.is_correct && !string.IsNullOrEmpty(response.core_contradiction))
                {
                    CaseDossier currentCase = GameController.Instance != null ? GameController.Instance.currentCase : null;
                    string fullNarrative = currentCase?.reasoning_chain?.final_conclusion ?? "";

                    string bonusStory = $"<b>Sự thật vụ án & Lỗ hổng cốt lõi:</b>\n{response.core_contradiction}";
                    if (!string.IsNullOrEmpty(fullNarrative))
                    {
                        bonusStory += $"\n\n<b>📖 TÁI HIỆN TOÀN CẢNH VỤ ÁN (BONUS SOLUTION DOSSIER):</b>\n{fullNarrative}";
                    }

                    coreContradictionText.gameObject.SetActive(true);
                    coreContradictionText.text = bonusStory;
                }
                else
                {
                    coreContradictionText.gameObject.SetActive(false);
                }
            }
        }
    }

    private void CloseVerdict()
    {
        if (verdictPanel != null) verdictPanel.SetActive(false);
        Close();
    }
}
