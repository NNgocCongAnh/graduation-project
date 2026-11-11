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
        DraggableCard.OnCardMoved += HandleCardMovedForStrings;
    }

    private void OnDisable()
    {
        DraggableCard.OnCardClicked -= HandleCardClicked;
        DraggableCard.OnCardMoved -= HandleCardMovedForStrings;
    }

    private void HandleCardMovedForStrings(string cardId, Vector2 pos)
    {
        if (showRedStrings)
        {
            UpdateRedStrings();
        }
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

        // Asynchronously load portrait / evidence photo
        if (!string.IsNullOrEmpty(imageUrl) && DetectiveAPIManager.Instance != null)
        {
            RawImage rawImg = card.GetComponentInChildren<RawImage>();
            if (rawImg != null)
            {
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

    /// <summary>
    /// Redraws UI red string connections between linked evidence and suspects.
    /// </summary>
    public void UpdateRedStrings()
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

        if (stringContainer == null) return;

        CaseDossier c = GameController.Instance != null ? GameController.Instance.currentCase : null;
        if (c == null || c.evidences == null) return;

        // Clear previous strings
        foreach (var str in activeUiStrings)
        {
            if (str != null) Destroy(str);
        }
        activeUiStrings.Clear();

        if (!showRedStrings) return;

        // Draw line for each linked evidence
        foreach (var ev in c.evidences)
        {
            if (string.IsNullOrEmpty(ev.linked_suspect_id)) continue;

            if (activeCards.TryGetValue(ev.id, out GameObject evCard) &&
                activeCards.TryGetValue(ev.linked_suspect_id, out GameObject susCard))
            {
                if (evCard == null || susCard == null) continue;

                RectTransform evRt = evCard.GetComponent<RectTransform>();
                RectTransform susRt = susCard.GetComponent<RectTransform>();

                // Pin offset is at (0, 116) relative to card center
                Vector2 pinA = evRt.anchoredPosition + new Vector2(0, 116f);
                Vector2 pinB = susRt.anchoredPosition + new Vector2(0, 116f);

                DrawStringLine(pinA, pinB);
            }
        }
    }

    private void DrawStringLine(Vector2 posA, Vector2 posB)
    {
        GameObject lineObj = new GameObject("Red_String_Line", typeof(RectTransform), typeof(Image));
        lineObj.transform.SetParent(stringContainer, false);

        Image img = lineObj.GetComponent<Image>();
        img.color = redStringColor;
        img.raycastTarget = false;

        RectTransform rt = lineObj.GetComponent<RectTransform>();
        rt.pivot = new Vector2(0.5f, 0.5f);

        Vector2 dir = posB - posA;
        float distance = dir.magnitude;
        float angle = Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg;

        rt.sizeDelta = new Vector2(distance, 3.2f);
        rt.anchoredPosition = posA + dir * 0.5f;
        rt.localRotation = Quaternion.Euler(0, 0, angle);

        activeUiStrings.Add(lineObj);
    }

    private void HandleCardClicked(DraggableCard card)
    {
        if (card == null || EvidenceDetailModal.Instance == null) return;

        CaseDossier currentCase = GameController.Instance != null ? GameController.Instance.currentCase : null;
        if (currentCase == null) return;

        cardTextures.TryGetValue(card.CardId, out Texture2D tex);

        if (card.IsSuspect)
        {
            SuspectData suspect = currentCase.suspects?.Find(s => s.id == card.CardId);
            if (suspect != null)
            {
                EvidenceDetailModal.Instance.ShowSuspect(suspect, tex);
            }
        }
        else
        {
            EvidenceData evidence = currentCase.evidences?.Find(e => e.id == card.CardId);
            if (evidence != null)
            {
                EvidenceDetailModal.Instance.ShowEvidence(evidence, tex);
            }
        }
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
        suspectCount = 0;
        evidenceCount = 0;

        foreach (var s in activeUiStrings)
        {
            if (s != null) Destroy(s);
        }
        activeUiStrings.Clear();
        activeCards.Clear();
        cardTextures.Clear();

        if (itemContainer != null)
        {
            foreach (Transform child in itemContainer)
            {
                Destroy(child.gameObject);
            }
        }
    }
}
