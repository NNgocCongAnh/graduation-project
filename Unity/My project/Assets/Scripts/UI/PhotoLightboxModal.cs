using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// Cửa sổ Phóng to Ảnh (Photo Lightbox Zoom Modal):
/// Cho phép người chơi click vào ảnh nghi phạm, vật chứng hoặc nạn nhân để phóng to chi tiết
/// trên nền ảnh Polaroid sắc nét, có nút đóng và hỗ trợ phím ESC.
/// </summary>
public class PhotoLightboxModal : MonoBehaviour
{
    private static PhotoLightboxModal _instance;
    public static PhotoLightboxModal Instance
    {
        get
        {
            if (_instance == null)
            {
                _instance = FindObjectOfType<PhotoLightboxModal>(true);
            }
            return _instance;
        }
        private set { _instance = value; }
    }

    private RectTransform root;
    private RawImage photoImage;
    private Text captionText;
    private Font font;

    private static readonly Color BgOverlay = new Color(0.02f, 0.02f, 0.03f, 0.94f);
    private static readonly Color PolaroidPaper = new Color(0.96f, 0.94f, 0.90f, 1f);
    private static readonly Color TextDark = new Color(0.12f, 0.12f, 0.14f, 1f);

    public bool IsOpen => root != null && root.gameObject.activeSelf;

    public void Initialize(Font uiFont)
    {
        font = uiFont;
        Instance = this;
    }

    private void Awake()
    {
        if (_instance == null) _instance = this;
    }

    public void Show(Texture2D texture, string caption)
    {
        if (root == null) BuildUI();
        if (root == null) return;

        // Bring to front
        transform.SetAsLastSibling();
        root.SetAsLastSibling();
        root.gameObject.SetActive(true);
        gameObject.SetActive(true);

        if (photoImage != null)
        {
            photoImage.texture = texture;
            photoImage.color = texture != null ? Color.white : new Color(0.2f, 0.2f, 0.2f);
        }

        if (captionText != null)
        {
            captionText.text = caption ?? "";
        }

        Debug.Log($"[PhotoLightboxModal] Lightbox ZOOM opened for '{caption}' (Texture: {(texture != null ? texture.name : "null")})");
    }

    public void Close()
    {
        if (root != null) root.gameObject.SetActive(false);
        gameObject.SetActive(false);
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

    private void BuildUI()
    {
        Canvas canvas = GetComponentInParent<Canvas>() ?? FindObjectOfType<Canvas>(true);
        if (canvas == null) return;

        // Fullscreen Backdrop
        GameObject rootGo = new GameObject("PhotoLightboxModal_Root", typeof(RectTransform), typeof(Image), typeof(Button));
        root = rootGo.GetComponent<RectTransform>();
        root.SetParent(canvas.transform, false);
        root.anchorMin = Vector2.zero;
        root.anchorMax = Vector2.one;
        root.sizeDelta = Vector2.zero;
        rootGo.GetComponent<Image>().color = BgOverlay;

        // Click on background closes the lightbox
        Button bgBtn = rootGo.GetComponent<Button>();
        bgBtn.transition = Selectable.Transition.None;
        bgBtn.onClick.AddListener(Close);

        // Center Polaroid Frame (480 x 560)
        GameObject frameGo = new GameObject("PolaroidFrame", typeof(RectTransform), typeof(Image));
        RectTransform frame = frameGo.GetComponent<RectTransform>();
        frame.SetParent(root, false);
        frame.anchorMin = new Vector2(0.5f, 0.5f);
        frame.anchorMax = new Vector2(0.5f, 0.5f);
        frame.pivot = new Vector2(0.5f, 0.5f);
        frame.sizeDelta = new Vector2(480f, 560f);
        frameGo.GetComponent<Image>().color = PolaroidPaper;

        // Red Pushpin at top center
        GameObject pinGo = new GameObject("Pin", typeof(RectTransform), typeof(Text));
        RectTransform pinRt = pinGo.GetComponent<RectTransform>();
        pinRt.SetParent(frame, false);
        pinRt.anchoredPosition = new Vector2(0f, 268f);
        pinRt.sizeDelta = new Vector2(36f, 36f);
        Text pinTxt = pinGo.GetComponent<Text>();
        pinTxt.font = font ?? DetectiveAssetBank.GetDefaultUIFont();
        pinTxt.fontSize = 24;
        pinTxt.alignment = TextAnchor.MiddleCenter;
        pinTxt.color = new Color(0.85f, 0.15f, 0.15f);
        pinTxt.text = "📌";

        // Photo RawImage Slot (430 x 430)
        GameObject photoGo = new GameObject("Photo", typeof(RectTransform), typeof(RawImage));
        RectTransform photoRt = photoGo.GetComponent<RectTransform>();
        photoRt.SetParent(frame, false);
        photoRt.anchoredPosition = new Vector2(0f, 30f);
        photoRt.sizeDelta = new Vector2(430f, 430f);
        photoImage = photoGo.GetComponent<RawImage>();
        photoImage.color = Color.white;

        // Caption Text at bottom of Polaroid
        GameObject captionGo = new GameObject("Caption", typeof(RectTransform), typeof(Text));
        RectTransform captionRt = captionGo.GetComponent<RectTransform>();
        captionRt.SetParent(frame, false);
        captionRt.anchoredPosition = new Vector2(0f, -225f);
        captionRt.sizeDelta = new Vector2(440f, 40f);
        captionText = captionGo.GetComponent<Text>();
        captionText.font = font ?? DetectiveAssetBank.GetDefaultUIFont();
        captionText.fontSize = 16;
        captionText.fontStyle = FontStyle.Bold;
        captionText.alignment = TextAnchor.MiddleCenter;
        captionText.color = TextDark;

        // Close Button (Top right X)
        GameObject closeGo = new GameObject("CloseBtn", typeof(RectTransform), typeof(Image), typeof(Button));
        RectTransform closeRt = closeGo.GetComponent<RectTransform>();
        closeRt.SetParent(frame, false);
        closeRt.anchoredPosition = new Vector2(215f, 255f);
        closeRt.sizeDelta = new Vector2(36f, 36f);
        closeGo.GetComponent<Image>().color = new Color(0.2f, 0.2f, 0.22f, 0.9f);
        Button closeBtn = closeGo.GetComponent<Button>();
        closeBtn.onClick.AddListener(Close);

        GameObject closeTxtGo = new GameObject("X", typeof(RectTransform), typeof(Text));
        RectTransform ctRt = closeTxtGo.GetComponent<RectTransform>();
        ctRt.SetParent(closeGo.transform, false);
        ctRt.anchorMin = Vector2.zero;
        ctRt.anchorMax = Vector2.one;
        ctRt.sizeDelta = Vector2.zero;
        Text closeTxt = closeTxtGo.GetComponent<Text>();
        closeTxt.font = font ?? DetectiveAssetBank.GetDefaultUIFont();
        closeTxt.fontSize = 20;
        closeTxt.fontStyle = FontStyle.Bold;
        closeTxt.alignment = TextAnchor.MiddleCenter;
        closeTxt.color = Color.white;
        closeTxt.text = "✕";

        root.gameObject.SetActive(false);
    }
}
