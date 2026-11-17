using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;
using System;

[RequireComponent(typeof(RectTransform))]
public class DraggableCard : MonoBehaviour, IPointerDownHandler, IPointerUpHandler, IBeginDragHandler, IDragHandler, IEndDragHandler
{
    public string CardId { get; private set; }
    public bool IsSuspect { get; private set; }
    public bool IsVictim { get; private set; }

    private RectTransform rectTransform;
    private Canvas canvas;
    private CanvasGroup canvasGroup;

    private Vector2 pointerDownPos;
    private float pointerDownTime;
    private bool isDragMovement = false;
    private bool isDragging = false;

    public static event Action<string, Vector2> OnCardMoved;
    public static event Action<string, Vector2> OnCardDragging;
    public static event Action<DraggableCard> OnCardClicked;
    public static event Action<DraggableCard> OnPhotoClicked;
    public static event Action<DraggableCard> OnPinClicked;

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

    private void Start()
    {
        SetupInteractiveElements();
    }

    /// <summary>
    /// Gắn Button và sự kiện Click trực tiếp lên ảnh Polaroid và đinh ghim,
    /// loại bỏ hoàn toàn nguy cơ bị nuốt sự kiện click chuột.
    /// </summary>
    public void SetupInteractiveElements()
    {
        // 1. Tìm và gắn Button lên ảnh Polaroid
        Transform photoTr = transform.Find("Card_Paper_Body/Photo_Cutout_Mask/Photo_RawImage")
            ?? transform.Find("Card_Paper_Body/Photo_RawImage")
            ?? transform.Find("Photo_RawImage");

        if (photoTr == null)
        {
            RawImage raw = GetComponentInChildren<RawImage>();
            if (raw != null) photoTr = raw.transform;
        }

        if (photoTr != null)
        {
            RawImage raw = photoTr.GetComponent<RawImage>();
            if (raw != null) raw.raycastTarget = true;

            Button photoBtn = photoTr.GetComponent<Button>();
            if (photoBtn == null) photoBtn = photoTr.gameObject.AddComponent<Button>();
            photoBtn.transition = Selectable.Transition.None;
            photoBtn.onClick.RemoveAllListeners();
            photoBtn.onClick.AddListener(TriggerPhotoZoom);
        }

        // 2. Tìm và gắn Button lên đinh ghim Push Pin 3D
        Transform pinTr = transform.Find("Card_Paper_Body/Push_Pin_3D")
            ?? transform.Find("Push_Pin_3D");

        if (pinTr != null)
        {
            Image pinImg = pinTr.GetComponent<Image>();
            if (pinImg != null) pinImg.raycastTarget = true;

            Button pinBtn = pinTr.GetComponent<Button>();
            if (pinBtn == null) pinBtn = pinTr.gameObject.AddComponent<Button>();
            pinBtn.transition = Selectable.Transition.ColorTint;
            ColorBlock cb = pinBtn.colors;
            cb.normalColor = Color.white;
            cb.highlightedColor = new Color(1f, 0.88f, 0.25f, 1f); // Hào quang vàng khi rà chuột
            cb.pressedColor = new Color(0.9f, 0.2f, 0.2f, 1f);
            pinBtn.colors = cb;
            pinBtn.onClick.RemoveAllListeners();
            pinBtn.onClick.AddListener(TriggerPinClick);
        }
    }

    public void Initialize(string id, bool isSuspect, bool isVictim = false)
    {
        CardId = id;
        IsSuspect = isSuspect;
        IsVictim = isVictim;
        SetupInteractiveElements();
    }

    public void TriggerPhotoZoom()
    {
        // Nếu người chơi đang trong chế độ kéo nối dây đỏ, bấm vào thẻ/ảnh sẽ hoàn tất nối dây
        if (CorkboardManager.Instance != null && CorkboardManager.Instance.IsConnectingString)
        {
            CorkboardManager.Instance.HandlePinClicked(this);
            return;
        }

        Debug.Log($"[DraggableCard] TriggerPhotoZoom for card: {CardId}");
        OnPhotoClicked?.Invoke(this);
    }

    public void TriggerPinClick()
    {
        Debug.Log($"[DraggableCard] TriggerPinClick for card: {CardId}");
        OnPinClicked?.Invoke(this);
    }

    public void OnPointerDown(PointerEventData eventData)
    {
        pointerDownPos = eventData.position;
        pointerDownTime = Time.unscaledTime;
        isDragMovement = false;
    }

    public void OnBeginDrag(PointerEventData eventData)
    {
        if (eventData.button != PointerEventData.InputButton.Left) return;

        if (Vector2.Distance(pointerDownPos, eventData.position) > 8f)
        {
            isDragMovement = true;
            isDragging = true;
            transform.SetAsLastSibling();
            canvasGroup.blocksRaycasts = false;
            canvasGroup.alpha = 0.88f;
        }
    }

    public void OnDrag(PointerEventData eventData)
    {
        if (eventData.button != PointerEventData.InputButton.Left) return;

        if (!isDragMovement && Vector2.Distance(pointerDownPos, eventData.position) > 8f)
        {
            isDragMovement = true;
            isDragging = true;
            transform.SetAsLastSibling();
            canvasGroup.blocksRaycasts = false;
            canvasGroup.alpha = 0.88f;
        }

        if (isDragging && canvas != null)
        {
            rectTransform.anchoredPosition += eventData.delta / canvas.scaleFactor;
            OnCardDragging?.Invoke(CardId, rectTransform.anchoredPosition);
        }
    }

    public void OnEndDrag(PointerEventData eventData)
    {
        if (isDragging)
        {
            isDragging = false;
            canvasGroup.blocksRaycasts = true;
            canvasGroup.alpha = 1f;
            OnCardMoved?.Invoke(CardId, rectTransform.anchoredPosition);
        }
    }

    public void OnPointerUp(PointerEventData eventData)
    {
        if (isDragMovement || isDragging)
        {
            isDragging = false;
            isDragMovement = false;
            canvasGroup.blocksRaycasts = true;
            canvasGroup.alpha = 1f;
            return;
        }

        // Chuột phải bất kỳ vị trí nào: Mở ngay Photo Lightbox
        if (eventData.button == PointerEventData.InputButton.Right)
        {
            TriggerPhotoZoom();
            return;
        }

        // Chuột trái vào phần giấy / viền / chữ:
        if (eventData.button == PointerEventData.InputButton.Left)
        {
            if (CorkboardManager.Instance != null && CorkboardManager.Instance.IsConnectingString)
            {
                CorkboardManager.Instance.HandlePinClicked(this);
                return;
            }

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
