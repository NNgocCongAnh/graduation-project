using UnityEngine;
using UnityEngine.UI;
using System;
using System.Collections.Generic;

public class CorkboardManager : MonoBehaviour
{
    public static CorkboardManager Instance { get; private set; }

    [Header("UI Containers & Prefabs")]
    [SerializeField] private Transform itemContainer;
    [SerializeField] private Transform stringContainer;
    [SerializeField] private GameObject cardPrefab;

    [Header("Red String Settings")]
    public bool showRedStrings = true;
    [SerializeField] private Color redStringColor = new Color(0.85f, 0.18f, 0.15f, 0.85f);

    private List<GameObject> activeUiStrings = new List<GameObject>();
    private Dictionary<string, GameObject> activeCards = new Dictionary<string, GameObject>();
    private Dictionary<string, Texture2D> cardTextures = new Dictionary<string, Texture2D>();

    public Texture2D GetCardTexture(string cardId)
    {
        if (string.IsNullOrEmpty(cardId)) return null;
        cardTextures.TryGetValue(cardId, out Texture2D tex);
        return tex;
    }

    // Manual red string connection state
    private readonly HashSet<string> manualConnections = new HashSet<string>();
    private DraggableCard selectedPinCard = null;
    private GameObject rubberBandPreview = null;
    private GameObject pinGlowIndicator = null;
    private Text toastBannerText = null;
    private float bannerTimer = 0f;

    public bool IsConnectingString => selectedPinCard != null;

    private int suspectCount = 0;
    private int evidenceCount = 0;

    private void Awake()
    {
        if (Instance == null) Instance = this;
        else Destroy(gameObject);
    }

    private void OnEnable()
    {
        DraggableCard.OnCardClicked += HandleCardClicked;
        DraggableCard.OnPhotoClicked += HandlePhotoClicked;
        DraggableCard.OnPinClicked += HandlePinClicked;
        DraggableCard.OnCardMoved += HandleCardMovedForStrings;
        DraggableCard.OnCardDragging += HandleCardMovedForStrings;
    }

    private void OnDisable()
    {
        DraggableCard.OnCardClicked -= HandleCardClicked;
        DraggableCard.OnPhotoClicked -= HandlePhotoClicked;
        DraggableCard.OnPinClicked -= HandlePinClicked;
        DraggableCard.OnCardMoved -= HandleCardMovedForStrings;
        DraggableCard.OnCardDragging -= HandleCardMovedForStrings;
    }

    private void Update()
    {
        // Cancel active manual string drawing if Escape or Right-Click is pressed
        if (selectedPinCard != null)
        {
            if (Input.GetKeyDown(KeyCode.Escape) || Input.GetMouseButtonDown(1))
            {
                CancelPinSelection();
                ShowBanner("Đã hủy chế độ nối dây.");
                return;
            }

            UpdateRubberBandPreview();
        }

        // Auto-fade banner timer
        if (bannerTimer > 0f)
        {
            bannerTimer -= Time.unscaledDeltaTime;
            if (bannerTimer <= 0f && toastBannerText != null)
            {
                toastBannerText.transform.parent.gameObject.SetActive(false);
            }
        }
    }

    private void HandleCardMovedForStrings(string cardId, Vector2 pos)
    {
        if (showRedStrings)
        {
            UpdateRedStrings();
        }
    }

    /// <summary>
    /// Thêm Thẻ Nạn Nhân (Victim Card) lên bảng trinh thám với ruy-băng đen tang lễ.
    /// Sử dụng ảnh chân dung thật sắc nét (536KB portrait) thay vì ảnh vẽ cartoon.
    /// </summary>
    public void AddVictimCard(VictimData victim)
    {
        if (victim == null || cardPrefab == null || itemContainer == null) return;

        string id = "card_victim";
        string title = $"NẠN NHÂN: {victim.name.ToUpper()}\n(Tử thi #001)";

        GameObject card = Instantiate(cardPrefab, itemContainer);
        card.name = id;
        card.SetActive(true);
        activeCards[id] = card;

        DraggableCard draggable = card.GetComponent<DraggableCard>();
        if (draggable == null) draggable = card.AddComponent<DraggableCard>();
        draggable.Initialize(id, isSuspect: false, isVictim: true);

        // Position victim prominently on the left of suspects
        RectTransform rt = card.GetComponent<RectTransform>();
        if (rt != null)
        {
            rt.anchoredPosition = new Vector2(-540f, 220f);
            rt.localRotation = Quaternion.Euler(0, 0, -2f);
        }

        // Title text
        Text textComp = card.GetComponentInChildren<Text>();
        if (textComp != null)
        {
            textComp.text = title;
            textComp.color = new Color(0.9f, 0.2f, 0.2f);
        }

        // Add black mourning ribbon badge
        GameObject ribbonGo = new GameObject("MourningRibbon", typeof(RectTransform), typeof(Image));
        RectTransform ribbonRt = ribbonGo.GetComponent<RectTransform>();
        ribbonRt.SetParent(card.transform, false);
        ribbonRt.anchorMin = new Vector2(0.55f, 0.85f);
        ribbonRt.anchorMax = new Vector2(0.98f, 0.98f);
        ribbonRt.sizeDelta = Vector2.zero;
        ribbonGo.GetComponent<Image>().color = new Color(0.1f, 0.1f, 0.12f, 0.92f);

        GameObject ribbonTxtGo = new GameObject("RibbonText", typeof(RectTransform), typeof(Text));
        RectTransform rtrt = ribbonTxtGo.GetComponent<RectTransform>();
        rtrt.SetParent(ribbonGo.transform, false);
        rtrt.anchorMin = Vector2.zero;
        rtrt.anchorMax = Vector2.one;
        rtrt.sizeDelta = Vector2.zero;
        Text rtxt = ribbonTxtGo.GetComponent<Text>();
        rtxt.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
        rtxt.fontSize = 10;
        rtxt.fontStyle = FontStyle.Bold;
        rtxt.alignment = TextAnchor.MiddleCenter;
        rtxt.color = new Color(0.95f, 0.85f, 0.85f);
        rtxt.text = "TỬ THI";

        // Nạp ảnh chân dung thật sắc nét (Lord Arthur Blackwood portrait 536KB)
        RawImage rawImg = card.GetComponentInChildren<RawImage>();
        if (rawImg != null)
        {
            Texture2D localTex = DetectiveAssetBank.ResolveTexture("victim_male_1.png", id, victim.name, true);
            if (localTex == null) localTex = DetectiveAssetBank.ResolveTexture("victim_male.png", id, victim.name, true);

            if (localTex != null)
            {
                cardTextures[id] = localTex;
                rawImg.texture = localTex;
                rawImg.color = Color.white;
            }
        }

        draggable.SetupInteractiveElements();
    }

    /// <summary>
    /// Spawns a suspect or evidence card on the corkboard and asynchronously loads its photograph.
    /// </summary>
    public void AddCard(string id, string title, bool isSuspect, string imageUrl = null)
    {
        if (cardPrefab == null || itemContainer == null)
        {
            Debug.LogWarning($"[CorkboardManager] Cannot spawn card '{id}': Prefab or Container is not assigned.");
            return;
        }

        GameObject card = Instantiate(cardPrefab, itemContainer);
        card.name = id;
        card.SetActive(true);
        activeCards[id] = card;

        // Ensure DraggableCard is attached
        DraggableCard draggable = card.GetComponent<DraggableCard>();
        if (draggable == null) draggable = card.AddComponent<DraggableCard>();
        draggable.Initialize(id, isSuspect);

        // Position card organically across corkboard
        RectTransform rt = card.GetComponent<RectTransform>();
        if (rt != null)
        {
            float posX = 0;
            float posY = 0;

            if (isSuspect)
            {
                // Top row for suspects
                posX = -500f + (suspectCount * 250f);
                posY = 220f + UnityEngine.Random.Range(-15f, 15f);
                suspectCount++;
            }
            else
            {
                // Bottom area for evidences
                int col = evidenceCount % 4;
                int row = evidenceCount / 4;
                posX = -430f + (col * 250f);
                posY = -60f - (row * 240f) + UnityEngine.Random.Range(-15f, 15f);
                evidenceCount++;
            }

            rt.anchoredPosition = new Vector2(posX, posY);
            rt.localRotation = Quaternion.Euler(0, 0, UnityEngine.Random.Range(-3.5f, 3.5f));
        }

        // Set Text component (supports standard Text)
        Text textComp = card.GetComponentInChildren<Text>();
        if (textComp != null)
        {
            textComp.text = title;
        }

        // Load portrait / evidence photo via DetectiveAssetBank + Remote Fallback
        RawImage rawImg = card.GetComponentInChildren<RawImage>();
        if (rawImg != null)
        {
            // 1. Instant local resolution or smart semantic matching from asset bank (0s latency!)
            Texture2D localTex = DetectiveAssetBank.ResolveTexture(imageUrl, id, title, isSuspect);
            if (localTex != null)
            {
                cardTextures[id] = localTex;
                rawImg.texture = localTex;
                rawImg.color = Color.white;
            }
            else if (!string.IsNullOrEmpty(imageUrl) && imageUrl.StartsWith("http") && DetectiveAPIManager.Instance != null)
            {
                // 2. If it's an external remote HTTP URL, download asynchronously in background
                DetectiveAPIManager.Instance.DownloadTexture(imageUrl, (success, tex) =>
                {
                    if (success && tex != null)
                    {
                        cardTextures[id] = tex;
                        if (rawImg != null)
                        {
                            rawImg.texture = tex;
                            rawImg.color = Color.white;
                        }
                    }
                });
            }
        }

        // Tự động khởi tạo dây chỉ đỏ từ dữ liệu vụ án ban đầu
        CaseDossier currentCase = GameController.Instance != null ? GameController.Instance.currentCase : null;
        if (currentCase != null && currentCase.evidences != null)
        {
            var ev = currentCase.evidences.Find(e => e.id == id);
            if (ev != null && !string.IsNullOrEmpty(ev.linked_suspect_id))
            {
                string key = GetConnectionKey(ev.id, ev.linked_suspect_id);
                manualConnections.Add(key);
            }
        }

        draggable.SetupInteractiveElements();

        if (showRedStrings)
        {
            UpdateRedStrings();
        }
    }

    /// <summary>
    /// Trả về tọa độ chính xác của đầu đinh ghim Push Pin trên thẻ bài trong hệ tọa độ của stringContainer.
    /// Khắc phục 100% lỗi dây chỉ bị lơ lửng do scale/xoay của thẻ bài.
    /// </summary>
    public Vector2 GetPinPositionInStringContainer(GameObject card)
    {
        EnsureStringContainer();
        if (card == null || stringContainer == null) return Vector2.zero;

        Transform pin = card.transform.Find("Card_Paper_Body/Push_Pin_3D")
            ?? card.transform.Find("Push_Pin_3D");

        if (pin == null)
        {
            Image[] imgs = card.GetComponentsInChildren<Image>();
            foreach (var im in imgs)
            {
                if (im.gameObject.name.Contains("Pin"))
                {
                    pin = im.transform;
                    break;
                }
            }
        }

        if (pin != null)
        {
            // Chuyển trực tiếp từ World Position sang Local Position của stringContainer
            return stringContainer.InverseTransformPoint(pin.position);
        }

        // Dự phòng: Lấy đỉnh trên của thẻ
        return stringContainer.InverseTransformPoint(card.transform.position + new Vector3(0, 45f, 0));
    }

    /// <summary>
    /// Xử lý sự kiện click vào Đinh ghim: Kích hoạt chế độ nối/gỡ dây chỉ đỏ thủ công.
    /// </summary>
    public void HandlePinClicked(DraggableCard card)
    {
        if (card == null) return;

        EnsureStringContainer();

        if (selectedPinCard == null)
        {
            // 1. Chọn ghim xuất phát
            selectedPinCard = card;
            ShowPinGlow(card);
            CreateRubberBandPreview(card);
            AudioManager.Instance?.PlayPinClick();

            Text cardTxt = card.GetComponentInChildren<Text>();
            string cardName = cardTxt != null ? cardTxt.text.Split('\n')[0] : card.CardId;
            ShowBanner($"🔴 Đang kéo chỉ đỏ từ [{cardName}]... Bấm vào thẻ thứ 2 để NỐI/GỠ DÂY | ESC: Hủy", 10f);
        }
        else if (selectedPinCard == card)
        {
            // 2. Bấm lại vào chính nó -> Hủy chọn
            CancelPinSelection();
            ShowBanner("Đã hủy chế độ nối dây.");
        }
        else
        {
            // 3. Bấm vào ghim thứ hai -> Tạo mới hoặc Gỡ bỏ dây chỉ đỏ giữa 2 thẻ!
            string key = GetConnectionKey(selectedPinCard.CardId, card.CardId);
            if (manualConnections.Contains(key))
            {
                manualConnections.Remove(key); // Tháo dây đỏ
                ShowBanner("✂️ ĐÃ THÁO SỢI CHỈ ĐỎ!");
            }
            else
            {
                manualConnections.Add(key); // Nối dây đỏ
                ShowBanner("✅ ĐÃ NỐI CHỈ ĐỎ SUY LUẬN GIỮA 2 THẺ!");
            }

            CancelPinSelection();
            UpdateRedStrings();
            AudioManager.Instance?.PlayPinClick();
        }
    }

    private string GetConnectionKey(string a, string b)
    {
        return string.CompareOrdinal(a, b) < 0 ? $"{a}|{b}" : $"{b}|{a}";
    }

    private void ShowPinGlow(DraggableCard card)
    {
        if (pinGlowIndicator != null) Destroy(pinGlowIndicator);

        Transform pin = card.transform.Find("Card_Paper_Body/Push_Pin_3D") ?? card.transform.Find("Push_Pin_3D");
        Transform parent = pin != null ? pin : card.transform;

        pinGlowIndicator = new GameObject("Pin_Glow_Indicator", typeof(RectTransform), typeof(Image));
        pinGlowIndicator.transform.SetParent(parent, false);

        RectTransform glowRt = pinGlowIndicator.GetComponent<RectTransform>();
        glowRt.anchoredPosition = Vector2.zero;
        glowRt.sizeDelta = new Vector2(36f, 36f);

        Image glowImg = pinGlowIndicator.GetComponent<Image>();
        glowImg.color = new Color(1f, 0.85f, 0.2f, 0.85f); // Vòng hào quang vàng cam rực rỡ
        glowImg.raycastTarget = false;
    }

    private void CreateRubberBandPreview(DraggableCard card)
    {
        if (rubberBandPreview != null) Destroy(rubberBandPreview);
        EnsureStringContainer();
        if (stringContainer == null) return;

        rubberBandPreview = new GameObject("RubberBand_Preview", typeof(RectTransform), typeof(Image));
        rubberBandPreview.transform.SetParent(stringContainer, false);

        Image img = rubberBandPreview.GetComponent<Image>();
        img.color = new Color(0.95f, 0.25f, 0.2f, 0.75f);
        img.raycastTarget = false;

        RectTransform rt = rubberBandPreview.GetComponent<RectTransform>();
        rt.pivot = new Vector2(0.5f, 0.5f);
        UpdateRubberBandPreview();
    }

    private void UpdateRubberBandPreview()
    {
        if (selectedPinCard == null || rubberBandPreview == null || stringContainer == null) return;

        Vector2 startPos = GetPinPositionInStringContainer(selectedPinCard.gameObject);

        RectTransform containerRt = stringContainer as RectTransform;
        RectTransformUtility.ScreenPointToLocalPointInRectangle(
            containerRt,
            Input.mousePosition,
            null, // null cho ScreenSpaceOverlay
            out Vector2 mouseLocalPos);

        RectTransform lineRt = rubberBandPreview.GetComponent<RectTransform>();
        Vector2 dir = mouseLocalPos - startPos;
        float dist = dir.magnitude;
        float angle = Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg;

        lineRt.sizeDelta = new Vector2(dist, 2.8f);
        lineRt.anchoredPosition = startPos + dir * 0.5f;
        lineRt.localRotation = Quaternion.Euler(0, 0, angle);
    }

    public void CancelPinSelection()
    {
        selectedPinCard = null;
        if (pinGlowIndicator != null)
        {
            Destroy(pinGlowIndicator);
            pinGlowIndicator = null;
        }
        if (rubberBandPreview != null)
        {
            Destroy(rubberBandPreview);
            rubberBandPreview = null;
        }
    }

    /// <summary>
    /// Hiển thị thanh thông báo trạng thái phá án / nối dây đỏ trên đỉnh bảng ghim.
    /// </summary>
    public void ShowBanner(string message, float duration = 2.5f)
    {
        EnsureToastBanner();
        if (toastBannerText == null) return;

        toastBannerText.text = message;
        toastBannerText.transform.parent.gameObject.SetActive(true);
        toastBannerText.transform.parent.SetAsLastSibling();
        bannerTimer = duration;
    }

    private void EnsureToastBanner()
    {
        if (toastBannerText != null) return;

        Canvas canvas = GetComponentInParent<Canvas>() ?? FindObjectOfType<Canvas>(true);
        if (canvas == null) return;

        GameObject bannerBg = new GameObject("Corkboard_ToastBanner", typeof(RectTransform), typeof(Image));
        bannerBg.transform.SetParent(canvas.transform, false);

        RectTransform bgRt = bannerBg.GetComponent<RectTransform>();
        bgRt.anchorMin = new Vector2(0.5f, 0.93f);
        bgRt.anchorMax = new Vector2(0.5f, 0.93f);
        bgRt.pivot = new Vector2(0.5f, 0.5f);
        bgRt.sizeDelta = new Vector2(560f, 36f);

        Image bgImg = bannerBg.GetComponent<Image>();
        bgImg.color = new Color(0.12f, 0.12f, 0.14f, 0.92f);

        GameObject txtGo = new GameObject("Text", typeof(RectTransform), typeof(Text));
        txtGo.transform.SetParent(bannerBg.transform, false);

        RectTransform txtRt = txtGo.GetComponent<RectTransform>();
        txtRt.anchorMin = Vector2.zero;
        txtRt.anchorMax = Vector2.one;
        txtRt.sizeDelta = Vector2.zero;

        toastBannerText = txtGo.GetComponent<Text>();
        toastBannerText.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
        toastBannerText.fontSize = 13;
        toastBannerText.fontStyle = FontStyle.Bold;
        toastBannerText.alignment = TextAnchor.MiddleCenter;
        toastBannerText.color = new Color(0.96f, 0.85f, 0.45f);

        bannerBg.SetActive(false);
    }

    /// <summary>
    /// Xử lý sự kiện click vào ảnh Polaroid trên bảng:
    /// Mở ngay Hồ Sơ Trinh Thám chuyên sâu tương ứng (Hồ sơ nghi phạm / Báo cáo vật chứng / Khám nghiệm tử thi).
    /// Người chơi có thể nhấp vào ảnh bên trong hồ sơ để soi kính lúp (Photo Lightbox Zoom).
    /// </summary>
    private void HandlePhotoClicked(DraggableCard card)
    {
        if (card == null) return;
        HandleCardClicked(card);
    }

    /// <summary>
    /// Xử lý sự kiện click vào phần giấy / nhãn của thẻ.
    /// </summary>
    private void HandleCardClicked(DraggableCard card)
    {
        if (card == null) return;

        Debug.Log($"[CorkboardManager] Clicked on card: {card.CardId} (IsSuspect={card.IsSuspect}, IsVictim={card.IsVictim})");

        // 1. Thẻ nạn nhân -> Mở Biên bản khám nghiệm tử thi (Autopsy Report)
        if (card.IsVictim || card.CardId == "card_victim")
        {
            AutopsyReportModal autopsyModal = AutopsyReportModal.Instance;
            if (autopsyModal != null)
            {
                autopsyModal.Open();
            }
            else
            {
                Debug.LogError("[CorkboardManager] AutopsyReportModal.Instance is NULL!");
            }
            return;
        }

        // 2. Thẻ nghi phạm hoặc vật chứng -> Mở Hồ Sơ Cảnh Sát (EvidenceDetailModal)
        EvidenceDetailModal detailModal = EvidenceDetailModal.Instance;
        if (detailModal == null)
        {
            Debug.LogError("[CorkboardManager] EvidenceDetailModal.Instance is NULL!");
            return;
        }

        CaseDossier currentCase = GameController.Instance != null ? GameController.Instance.currentCase : null;
        cardTextures.TryGetValue(card.CardId, out Texture2D tex);

        if (card.IsSuspect)
        {
            SuspectData suspect = currentCase?.suspects?.Find(s => s.id == card.CardId);
            if (suspect == null)
            {
                // Dự phòng nếu không tìm thấy ID trong case data
                Text t = card.GetComponentInChildren<Text>();
                string name = t != null ? t.text.Split('\n')[0] : card.CardId;
                suspect = new SuspectData
                {
                    id = card.CardId,
                    name = name,
                    occupation = "Nghi phạm được điều tra",
                    motive = "Có mặt tại hiện trường trước và sau thời điểm vụ án xảy ra."
                };
            }
            detailModal.ShowSuspect(suspect, tex);
        }
        else
        {
            EvidenceData evidence = currentCase?.evidences?.Find(e => e.id == card.CardId);
            if (evidence == null)
            {
                // Dự phòng nếu không tìm thấy ID trong case data
                Text t = card.GetComponentInChildren<Text>();
                string title = t != null ? t.text.Split('\n')[0] : card.CardId;
                evidence = new EvidenceData
                {
                    id = card.CardId,
                    title = title,
                    location = "Hiện trường vụ án",
                    description = "Vật chứng liên quan được thu thập phục vụ điều tra."
                };
            }
            detailModal.ShowEvidence(evidence, tex);
        }
    }

    /// <summary>
    /// Toggles red string visibility on the corkboard.
    /// </summary>
    public void ToggleRedStrings()
    {
        showRedStrings = !showRedStrings;
        foreach (var str in activeUiStrings)
        {
            if (str != null) str.SetActive(showRedStrings);
        }

        if (showRedStrings)
        {
            UpdateRedStrings();
        }
    }

    private void EnsureStringContainer()
    {
        if (stringContainer == null && itemContainer != null)
        {
            stringContainer = itemContainer.parent.Find("String_Container");
            if (stringContainer == null)
            {
                GameObject sObj = new GameObject("String_Container", typeof(RectTransform));
                sObj.transform.SetParent(itemContainer.parent, false);
                sObj.transform.SetSiblingIndex(itemContainer.GetSiblingIndex()); // Behind cards
                RectTransform sRt = sObj.GetComponent<RectTransform>();
                sRt.anchorMin = Vector2.zero;
                sRt.anchorMax = Vector2.one;
                sRt.offsetMin = Vector2.zero;
                sRt.offsetMax = Vector2.zero;
                stringContainer = sObj.transform;
            }
        }
    }

    /// <summary>
    /// Vẽ lại toàn bộ dây chỉ đỏ nối chính xác giữa các đinh ghim.
    /// Sử dụng InverseTransformPoint để sợi dây luôn dính chặt vào tâm đinh ghim, không bị trôi hay lơ lửng.
    /// </summary>
    public void UpdateRedStrings()
    {
        EnsureStringContainer();
        if (stringContainer == null) return;

        // Bắt buộc Canvas tính toán xong toàn bộ tọa độ RectTransform trước khi lấy vị trí đinh ghim
        Canvas.ForceUpdateCanvases();

        // Clear previous strings
        foreach (var str in activeUiStrings)
        {
            if (str != null) Destroy(str);
        }
        activeUiStrings.Clear();

        if (!showRedStrings) return;

        // Vẽ toàn bộ các mối nối thủ công & mối nối theo hồ sơ
        foreach (string connKey in manualConnections)
        {
            string[] parts = connKey.Split('|');
            if (parts.Length != 2) continue;

            string idA = parts[0];
            string idB = parts[1];

            if (activeCards.TryGetValue(idA, out GameObject cardA) &&
                activeCards.TryGetValue(idB, out GameObject cardB))
            {
                if (cardA == null || cardB == null) continue;

                Vector2 pinA = GetPinPositionInStringContainer(cardA);
                Vector2 pinB = GetPinPositionInStringContainer(cardB);

                DrawCurvedPhysicsString(pinA, pinB);
            }
        }
    }

    /// <summary>
    /// Vẽ dây chỉ đỏ vật lý có độ võng trọng lực (Catenary Sag) và bóng đổ 3D tự nhiên.
    /// </summary>
    private void DrawCurvedPhysicsString(Vector2 posA, Vector2 posB)
    {
        float dist = Vector2.Distance(posA, posB);
        if (dist < 10f) return;

        // Độ võng trọng lực động: Khoảng cách càng xa dây càng chùng và trĩu xuống
        float sag = Mathf.Clamp(dist * 0.11f, 15f, 52f);
        Vector2 mid = (posA + posB) * 0.5f;
        Vector2 ctrl = new Vector2(mid.x, mid.y - sag);

        const int segments = 14;
        Vector2[] points = new Vector2[segments + 1];
        for (int i = 0; i <= segments; i++)
        {
            float t = (float)i / segments;
            float u = 1f - t;
            // Quadratic Bezier interpolation giả lập dây treo chịu trọng lực
            points[i] = u * u * posA + 2f * u * t * ctrl + t * t * posB;
        }

        // 1. Vẽ bóng đổ 3D của dây chỉ lên mặt bảng ghim
        Vector2 shadowOffset = new Vector2(2f, -5f);
        Color shadowColor = new Color(0.04f, 0.04f, 0.05f, 0.38f);
        for (int i = 0; i < segments; i++)
        {
            CreateStringSegment(points[i] + shadowOffset, points[i + 1] + shadowOffset, shadowColor, 3.2f, true);
        }

        // 2. Vẽ các đoạn chỉ đỏ xoắn tự nhiên (Crimson Investigator Twine)
        Color twineRed = new Color(0.88f, 0.15f, 0.14f, 0.95f);
        for (int i = 0; i < segments; i++)
        {
            CreateStringSegment(points[i], points[i + 1], twineRed, 2.6f, false);
        }

        // 3. Nút thắt quấn quanh đinh ghim ở hai đầu
        CreatePinKnot(posA);
        CreatePinKnot(posB);
    }

    private void CreateStringSegment(Vector2 pA, Vector2 pB, Color col, float thickness, bool isShadow)
    {
        GameObject segGo = new GameObject(isShadow ? "String_Shadow" : "String_Segment", typeof(RectTransform), typeof(Image));
        segGo.transform.SetParent(stringContainer, false);

        Image img = segGo.GetComponent<Image>();
        img.color = col;
        img.raycastTarget = false;

        RectTransform rt = segGo.GetComponent<RectTransform>();
        rt.pivot = new Vector2(0.5f, 0.5f);

        Vector2 dir = pB - pA;
        float len = dir.magnitude;
        float angle = Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg;

        rt.sizeDelta = new Vector2(len + 0.8f, thickness);
        rt.anchoredPosition = pA + dir * 0.5f;
        rt.localRotation = Quaternion.Euler(0, 0, angle);

        activeUiStrings.Add(segGo);
    }

    private void CreatePinKnot(Vector2 pinPos)
    {
        GameObject knotGo = new GameObject("String_PinKnot", typeof(RectTransform), typeof(Image));
        knotGo.transform.SetParent(stringContainer, false);

        Image img = knotGo.GetComponent<Image>();
        img.color = new Color(0.65f, 0.10f, 0.10f, 0.95f);
        img.raycastTarget = false;

        RectTransform rt = knotGo.GetComponent<RectTransform>();
        rt.pivot = new Vector2(0.5f, 0.5f);
        rt.sizeDelta = new Vector2(7f, 7f);
        rt.anchoredPosition = pinPos;

        activeUiStrings.Add(knotGo);
    }

    /// <summary>
    /// Update card position (called by multiplayer sync).
    /// </summary>
    public void MoveCard(string cardId, Vector2 newPos)
    {
        if (activeCards.TryGetValue(cardId, out GameObject cardObj) && cardObj != null)
        {
            DraggableCard draggable = cardObj.GetComponent<DraggableCard>();
            if (draggable != null)
            {
                draggable.SetPosition(newPos);
            }

            if (showRedStrings)
            {
                UpdateRedStrings();
            }
        }
    }

    /// <summary>
    /// Clears all cards and strings from the board.
    /// </summary>
    public void ClearBoard()
    {
        CancelPinSelection();
        suspectCount = 0;
        evidenceCount = 0;

        foreach (var s in activeUiStrings)
        {
            if (s != null) Destroy(s);
        }
        activeUiStrings.Clear();
        activeCards.Clear();
        cardTextures.Clear();
        manualConnections.Clear();

        if (itemContainer != null)
        {
            foreach (Transform child in itemContainer)
            {
                Destroy(child.gameObject);
            }
        }
    }
}
