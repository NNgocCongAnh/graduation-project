using UnityEngine;
using UnityEngine.UI;
using System.Collections.Generic;

public class CorkboardManager : MonoBehaviour
{
    [Header("UI Containers & Prefabs")]
    [SerializeField] private Transform itemContainer;
    [SerializeField] private GameObject cardPrefab;
    [SerializeField] private LineRenderer redStringPrefab;

    private List<LineRenderer> activeStrings = new List<LineRenderer>();
    private Dictionary<string, GameObject> activeCards = new Dictionary<string, GameObject>();

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
        activeCards[id] = card;

        // Set Text component (supports standard Text or TextMeshProUGUI)
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
                    if (success && tex != null && rawImg != null)
                    {
                        rawImg.texture = tex;
                    }
                });
            }
        }
    }

    /// <summary>
    /// Connects two pin cards with a red string LineRenderer.
    /// </summary>
    public void ConnectCards(GameObject from, GameObject to)
    {
        if (redStringPrefab == null || from == null || to == null) return;

        LineRenderer line = Instantiate(redStringPrefab, transform);
        line.positionCount = 2;
        line.SetPosition(0, from.transform.position);
        line.SetPosition(1, to.transform.position);
        activeStrings.Add(line);
    }

    /// <summary>
    /// Clears all cards and strings from the board.
    /// </summary>
    public void ClearBoard()
    {
        foreach (var s in activeStrings)
        {
            if (s != null) Destroy(s.gameObject);
        }
        activeStrings.Clear();
        activeCards.Clear();

        if (itemContainer != null)
        {
            foreach (Transform child in itemContainer)
            {
                Destroy(child.gameObject);
            }
        }
    }
}
