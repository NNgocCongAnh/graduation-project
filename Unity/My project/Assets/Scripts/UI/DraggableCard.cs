using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;
using System;

[RequireComponent(typeof(RectTransform))]
public class DraggableCard : MonoBehaviour, IBeginDragHandler, IDragHandler, IEndDragHandler, IPointerClickHandler
{
    public string CardId { get; private set; }
    public bool IsSuspect { get; private set; }

    private RectTransform rectTransform;
    private Canvas canvas;
    private CanvasGroup canvasGroup;
    private Vector2 dragStartPos;
    private bool isDragging = false;

    public static event Action<string, Vector2> OnCardMoved;
    public static event Action<DraggableCard> OnCardClicked;

    private void Awake()
    {
        rectTransform = GetComponent<RectTransform>();
        canvas = GetComponentInParent<Canvas>();
        canvasGroup = GetComponent<CanvasGroup>();
        if (canvasGroup == null)
        {
            canvasGroup = gameObject.AddComponent<CanvasGroup>();
        }
    }

    public void Initialize(string id, bool isSuspect)
    {
        CardId = id;
        IsSuspect = isSuspect;
    }

    public void OnBeginDrag(PointerEventData eventData)
    {
        if (eventData.button != PointerEventData.InputButton.Left) return;

        isDragging = true;
        dragStartPos = rectTransform.anchoredPosition;
        transform.SetAsLastSibling(); // Bring to front while dragging
        canvasGroup.blocksRaycasts = false;
        canvasGroup.alpha = 0.85f;
    }

    public void OnDrag(PointerEventData eventData)
    {
        if (!isDragging || canvas == null) return;

        rectTransform.anchoredPosition += eventData.delta / canvas.scaleFactor;
    }

    public void OnEndDrag(PointerEventData eventData)
    {
        if (!isDragging) return;

        isDragging = false;
        canvasGroup.blocksRaycasts = true;
        canvasGroup.alpha = 1f;

        // Broadcast move event for multiplayer sync
        OnCardMoved?.Invoke(CardId, rectTransform.anchoredPosition);
    }

    public void OnPointerClick(PointerEventData eventData)
    {
        // Avoid clicking while ending drag
        if (isDragging) return;

        if (eventData.button == PointerEventData.InputButton.Left)
        {
            OnCardClicked?.Invoke(this);
        }
    }

    public void SetPosition(Vector2 newPos)
    {
        if (rectTransform == null) rectTransform = GetComponent<RectTransform>();
        rectTransform.anchoredPosition = newPos;
    }

    public Vector2 GetPosition()
    {
        if (rectTransform == null) rectTransform = GetComponent<RectTransform>();
        return rectTransform.anchoredPosition;
    }
}

