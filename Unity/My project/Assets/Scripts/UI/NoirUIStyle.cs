using System.Collections;
using UnityEngine;
using UnityEngine.Events;
using UnityEngine.EventSystems;
using UnityEngine.UI;

/// <summary>
/// Bang mau, vien khung va hieu ung phan hoi thong nhat theo phong cach Ho so Trinh tham Co dien (Vintage Noir).
/// Loai bo hoan toan mau xam phang mac dinh va trang thai bam nut cung nhac.
/// </summary>
public static class NoirUIStyle
{
    // --- Surface & Scrim Palette ---
    public static readonly Color BackdropScrim = new Color(0.03f, 0.025f, 0.022f, 0.68f);
    public static readonly Color ModalSurface = new Color(0.095f, 0.086f, 0.078f, 0.98f);
    public static readonly Color CardSurface = new Color(0.140f, 0.128f, 0.116f, 0.98f);
    public static readonly Color FieldSurface = new Color(0.068f, 0.062f, 0.058f, 1.0f);

    // --- Accent & Ink Palette ---
    public static readonly Color BrassGold = new Color(0.92f, 0.76f, 0.38f, 1.0f);
    public static readonly Color BrassBorder = new Color(0.66f, 0.52f, 0.25f, 0.72f);
    public static readonly Color SubtleBorder = new Color(0.32f, 0.28f, 0.24f, 0.70f);

    public static readonly Color EmeraldPrimary = new Color(0.13f, 0.44f, 0.30f, 1.0f);
    public static readonly Color SlateSecondary = new Color(0.20f, 0.21f, 0.24f, 1.0f);
    public static readonly Color SlateBlue = new Color(0.18f, 0.27f, 0.37f, 1.0f);
    public static readonly Color CrimsonDanger = new Color(0.54f, 0.17f, 0.17f, 1.0f);

    public static readonly Color CreamText = new Color(0.94f, 0.91f, 0.85f, 1.0f);
    public static readonly Color MutedText = new Color(0.67f, 0.63f, 0.57f, 1.0f);
    public static readonly Color MintFeedback = new Color(0.45f, 0.88f, 0.56f, 1.0f);
    public static readonly Color CoralAlert = new Color(0.95f, 0.46f, 0.42f, 1.0f);

    // --- Paper Document Palette ---
    public static readonly Color PaperIvory = new Color(0.965f, 0.945f, 0.895f, 1.0f);
    public static readonly Color PaperBorder = new Color(0.22f, 0.19f, 0.16f, 0.95f);

    /// <summary>
    /// Gan khung vien dong mảnh, do bong va thanh nhan tren cung cho hop thoai.
    /// </summary>
    public static void ApplyPanelChrome(GameObject panelGo, Color? borderColor = null, bool addTopBrassRule = true)
    {
        if (panelGo == null) return;

        Outline outline = panelGo.GetComponent<Outline>() ?? panelGo.AddComponent<Outline>();
        outline.effectColor = borderColor ?? BrassBorder;
        outline.effectDistance = new Vector2(1.5f, -1.5f);

        Shadow shadow = panelGo.GetComponent<Shadow>() ?? panelGo.AddComponent<Shadow>();
        shadow.effectColor = new Color(0f, 0f, 0f, 0.65f);
        shadow.effectDistance = new Vector2(0f, -10f);

        if (addTopBrassRule && panelGo.transform.Find("TopBrassRule") == null)
        {
            GameObject bar = new GameObject("TopBrassRule", typeof(RectTransform), typeof(Image));
            RectTransform rt = bar.GetComponent<RectTransform>();
            rt.SetParent(panelGo.transform, false);
            rt.anchorMin = new Vector2(0f, 1f);
            rt.anchorMax = new Vector2(1f, 1f);
            rt.pivot = new Vector2(0.5f, 1f);
            rt.anchoredPosition = Vector2.zero;
            rt.sizeDelta = new Vector2(0f, 3f);

            Image img = bar.GetComponent<Image>();
            img.color = BrassGold;
            img.raycastTarget = false;
        }
    }

    /// <summary>
    /// Gan trang thai hover/press va co nhe scale 0.97 cho nut bam.
    /// </summary>
    public static void AttachButtonFeel(Button btn, float pressScale = 0.97f, bool applyBorder = true)
    {
        if (btn == null) return;

        ColorBlock cb = btn.colors;
        cb.normalColor = Color.white;
        cb.highlightedColor = new Color(1.16f, 1.14f, 1.10f, 1.0f);
        cb.pressedColor = new Color(0.84f, 0.82f, 0.78f, 1.0f);
        cb.selectedColor = new Color(1.10f, 1.08f, 1.04f, 1.0f);
        cb.disabledColor = new Color(0.55f, 0.55f, 0.55f, 0.55f);
        cb.fadeDuration = 0.08f;
        btn.colors = cb;

        if (applyBorder && btn.GetComponent<Outline>() == null)
        {
            Outline o = btn.gameObject.AddComponent<Outline>();
            o.effectColor = new Color(0.85f, 0.72f, 0.40f, 0.25f);
            o.effectDistance = new Vector2(1f, -1f);
        }

        NoirButtonFeedback fb = btn.GetComponent<NoirButtonFeedback>();
        if (fb == null) fb = btn.gameObject.AddComponent<NoirButtonFeedback>();
        fb.Configure(pressScale);
    }

    /// <summary>
    /// Gan vien chi mảnh cho o nhap lieu.
    /// </summary>
    public static void StyleInputChrome(GameObject fieldGo)
    {
        if (fieldGo == null) return;
        Outline outline = fieldGo.GetComponent<Outline>() ?? fieldGo.AddComponent<Outline>();
        outline.effectColor = SubtleBorder;
        outline.effectDistance = new Vector2(1f, -1f);
    }

    /// <summary>
    /// Nut dong chuan [X] o goc phai tren cung cho cac ho so giay va cua so.
    /// </summary>
    public static Button CreateCornerCloseButton(RectTransform parent, Font font, UnityAction onClose)
    {
        GameObject closeGo = new GameObject("Btn_Close_Paper", typeof(RectTransform), typeof(Image), typeof(Button));
        RectTransform crt = closeGo.GetComponent<RectTransform>();
        crt.SetParent(parent, false);
        crt.anchorMin = new Vector2(1f, 1f);
        crt.anchorMax = new Vector2(1f, 1f);
        crt.pivot = new Vector2(1f, 1f);
        crt.sizeDelta = new Vector2(34f, 34f);
        crt.anchoredPosition = new Vector2(-12f, -12f);

        Image cImg = closeGo.GetComponent<Image>();
        cImg.color = new Color(0.18f, 0.16f, 0.14f, 0.94f);

        Button cBtn = closeGo.GetComponent<Button>();
        cBtn.onClick.AddListener(onClose);
        AttachButtonFeel(cBtn, 0.94f, true);

        GameObject txtGo = new GameObject("X_Label", typeof(RectTransform), typeof(Text));
        RectTransform trt = txtGo.GetComponent<RectTransform>();
        trt.SetParent(closeGo.transform, false);
        trt.anchorMin = Vector2.zero;
        trt.anchorMax = Vector2.one;
        trt.sizeDelta = Vector2.zero;

        Text txt = txtGo.GetComponent<Text>();
        txt.font = font ?? DetectiveAssetBank.GetDefaultUIFont();
        txt.fontSize = 16;
        txt.fontStyle = FontStyle.Bold;
        txt.alignment = TextAnchor.MiddleCenter;
        txt.color = CreamText;
        txt.text = "X";
        txt.raycastTarget = false;

        return cBtn;
    }

    /// <summary>
    /// Hieu ung mo cua so muot (160ms ease-out tren unscaledTime) tranh cam giac giat cuc.
    /// </summary>
    public static Coroutine AnimateModalOpen(MonoBehaviour host, GameObject rootGo, Transform panelTransform = null, float duration = 0.16f)
    {
        if (host == null || rootGo == null || !host.gameObject.activeInHierarchy) return null;
        return host.StartCoroutine(AnimateOpenRoutine(rootGo, panelTransform, duration));
    }

    private static IEnumerator AnimateOpenRoutine(GameObject rootGo, Transform panelTransform, float duration)
    {
        CanvasGroup cg = rootGo.GetComponent<CanvasGroup>();
        if (cg == null) cg = rootGo.AddComponent<CanvasGroup>();

        cg.alpha = 0f;
        Vector3 startScale = new Vector3(0.965f, 0.965f, 1f);
        if (panelTransform != null) panelTransform.localScale = startScale;

        float elapsed = 0f;
        while (elapsed < duration)
        {
            elapsed += Time.unscaledDeltaTime;
            float t = Mathf.Clamp01(elapsed / duration);
            float easeOut = 1f - Mathf.Pow(1f - t, 3f);
            cg.alpha = easeOut;
            if (panelTransform != null)
            {
                panelTransform.localScale = Vector3.LerpUnclamped(startScale, Vector3.one, easeOut);
            }
            yield return null;
        }

        cg.alpha = 1f;
        if (panelTransform != null) panelTransform.localScale = Vector3.one;
    }
}

/// <summary>
/// Component phan hoi ti le co gian nhe khi hover/press bang unscaledTime (hoat dong ca khi pause).
/// </summary>
public class NoirButtonFeedback : MonoBehaviour, IPointerEnterHandler, IPointerExitHandler, IPointerDownHandler, IPointerUpHandler
{
    private float pressScale = 0.97f;
    private bool isHovered = false;
    private bool isPressed = false;
    private Vector3 targetScale = Vector3.one;

    public void Configure(float scaleOnPress)
    {
        pressScale = Mathf.Clamp(scaleOnPress, 0.90f, 1.0f);
    }

    private void OnDisable()
    {
        isHovered = false;
        isPressed = false;
        transform.localScale = Vector3.one;
    }

    public void OnPointerEnter(PointerEventData eventData)
    {
        isHovered = true;
        UpdateTarget();
    }

    public void OnPointerExit(PointerEventData eventData)
    {
        isHovered = false;
        isPressed = false;
        UpdateTarget();
    }

    public void OnPointerDown(PointerEventData eventData)
    {
        if (eventData.button != PointerEventData.InputButton.Left) return;
        isPressed = true;
        UpdateTarget();
    }

    public void OnPointerUp(PointerEventData eventData)
    {
        isPressed = false;
        UpdateTarget();
    }

    private void UpdateTarget()
    {
        float s = isPressed ? pressScale : (isHovered ? 1.015f : 1.0f);
        targetScale = new Vector3(s, s, 1f);
    }

    private void Update()
    {
        if ((transform.localScale - targetScale).sqrMagnitude > 0.00001f)
        {
            transform.localScale = Vector3.Lerp(transform.localScale, targetScale, Time.unscaledDeltaTime * 22f);
        }
        else if (transform.localScale != targetScale)
        {
            transform.localScale = targetScale;
        }
    }
}
