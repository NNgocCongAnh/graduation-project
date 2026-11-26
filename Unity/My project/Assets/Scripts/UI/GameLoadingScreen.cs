using System.Collections;
using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// Màn hình Chờ Tải Vụ Án (Noir Cinematic Loading Screen):
/// Hiển thị tiến trình sinh vụ án 4 bước, vòng xoay kính lúp động,
/// và tự động phát nhạc Conan trong lúc chờ đợi để tạo cảm giác hồi hộp.
/// </summary>
public class GameLoadingScreen : MonoBehaviour
{
    private static GameLoadingScreen _instance;
    public static GameLoadingScreen Instance
    {
        get
        {
            if (_instance == null)
            {
                _instance = FindObjectOfType<GameLoadingScreen>(true);
            }
            return _instance;
        }
        private set => _instance = value;
    }

    private void Awake()
    {
        if (_instance == null) _instance = this;
        Image selfImg = GetComponent<Image>();
        if (selfImg != null)
        {
            selfImg.enabled = false;
            selfImg.raycastTarget = false;
        }
    }

    private RectTransform root;
    private Text mainStatusText;
    private Text subStatusText;
    private RectTransform spinner;
    private Slider progressBar;
    private Coroutine stepCoroutine;

    private Font font;

    private static readonly Color BgColor = new Color(0.04f, 0.04f, 0.05f, 0.98f);
    private static readonly Color GoldColor = new Color(0.96f, 0.82f, 0.38f);
    private static readonly Color TextWhite = new Color(0.93f, 0.93f, 0.90f);
    private static readonly Color TextMuted = new Color(0.65f, 0.65f, 0.60f);

    public bool IsShowing => root != null && root.gameObject.activeSelf;

    public void Initialize(Font uiFont)
    {
        font = uiFont;
        Instance = this;
    }

    public void Show(string initialTitle = "HỆ THỐNG TRINH THÁM AI ĐANG TẠO VỤ ÁN...")
    {
        if (root == null) BuildUI();
        if (root != null)
        {
            root.SetAsLastSibling();
            root.gameObject.SetActive(true);
        }

        if (mainStatusText != null) mainStatusText.text = initialTitle;
        if (progressBar != null) progressBar.value = 0.05f;

        // Play Conan theme during case generation
        AudioManager.Instance?.SwitchTrack(AudioManager.BgmTrack.ConanMain);

        if (stepCoroutine != null) StopCoroutine(stepCoroutine);
        stepCoroutine = StartCoroutine(SimulatePipelineSteps());
    }

    public void Hide()
    {
        if (stepCoroutine != null)
        {
            StopCoroutine(stepCoroutine);
            stepCoroutine = null;
        }

        if (root != null) root.gameObject.SetActive(false);
        gameObject.SetActive(false);

        // Switch back to gentle investigation BGM
        AudioManager.Instance?.SwitchTrack(AudioManager.BgmTrack.ConanRan);
    }

    private void Update()
    {
        if (IsShowing && spinner != null)
        {
            spinner.Rotate(0f, 0f, -180f * Time.deltaTime);
        }
    }

    private IEnumerator SimulatePipelineSteps()
    {
        string[] steps = new string[]
        {
            "Bước 1/4: Đang kết nối AI Engine & Khởi tạo bối cảnh vụ án...",
            "Bước 2/4: Tính toán nhiệt học tử thi Henssge xác định giờ tử vong...",
            "Bước 3/4: Thiết lập động cơ, hung khí & bằng chứng ngoại phạm (Alibi)...",
            "Bước 4/4: Kiểm định logic toán học & giăng dây chỉ đỏ lên bảng..."
        };

        float[] targets = new float[] { 0.25f, 0.55f, 0.82f, 0.96f };

        for (int i = 0; i < steps.Length; i++)
        {
            if (subStatusText != null) subStatusText.text = steps[i];
            float startVal = progressBar != null ? progressBar.value : 0f;
            float endVal = targets[i];
            float dur = Random.Range(1.8f, 2.5f);
            float elapsed = 0f;

            while (elapsed < dur)
            {
                elapsed += Time.deltaTime;
                if (progressBar != null) progressBar.value = Mathf.Lerp(startVal, endVal, elapsed / dur);
                yield return null;
            }
        }

        if (subStatusText != null) subStatusText.text = "Hoàn tất. Đang mở hồ sơ vụ án lên hiện trường...";
        if (progressBar != null) progressBar.value = 1f;
    }

    private void BuildUI()
    {
        Canvas canvas = GetComponentInParent<Canvas>() ?? FindObjectOfType<Canvas>(true);
        if (canvas == null)
        {
            Debug.LogError("[GameLoadingScreen] Canvas not found in scene!");
            return;
        }

        if (transform.parent != canvas.transform)
        {
            transform.SetParent(canvas.transform, false);
        }

        GameObject rootGo = new GameObject("LoadingScreen_Root", typeof(RectTransform), typeof(Image));
        root = rootGo.GetComponent<RectTransform>();
        root.SetParent(canvas.transform, false);
        root.anchorMin = Vector2.zero;
        root.anchorMax = Vector2.one;
        root.sizeDelta = Vector2.zero;
        rootGo.GetComponent<Image>().color = BgColor;

        // Center container
        GameObject centerGo = new GameObject("CenterContent", typeof(RectTransform));
        RectTransform crt = centerGo.GetComponent<RectTransform>();
        crt.SetParent(root, false);
        crt.anchorMin = new Vector2(0.5f, 0.5f);
        crt.anchorMax = new Vector2(0.5f, 0.5f);
        crt.pivot = new Vector2(0.5f, 0.5f);
        crt.sizeDelta = new Vector2(560f, 320f);

        // Spinner (Geometric rotating brass emblem - no emoji dependency)
        GameObject spinGo = new GameObject("Spinner", typeof(RectTransform), typeof(Image));
        spinner = spinGo.GetComponent<RectTransform>();
        spinner.SetParent(centerGo.transform, false);
        spinner.anchoredPosition = new Vector2(0f, 88f);
        spinner.sizeDelta = new Vector2(46f, 46f);
        spinner.localRotation = Quaternion.Euler(0f, 0f, 45f);
        spinGo.GetComponent<Image>().color = new Color(GoldColor.r, GoldColor.g, GoldColor.b, 0.16f);
        Outline spinOutline = spinGo.AddComponent<Outline>();
        spinOutline.effectColor = GoldColor;
        spinOutline.effectDistance = new Vector2(2f, -2f);

        GameObject innerDiamond = new GameObject("InnerPip", typeof(RectTransform), typeof(Image));
        RectTransform idrt = innerDiamond.GetComponent<RectTransform>();
        idrt.SetParent(spinner, false);
        idrt.anchorMin = new Vector2(0.5f, 0.5f);
        idrt.anchorMax = new Vector2(0.5f, 0.5f);
        idrt.sizeDelta = new Vector2(18f, 18f);
        innerDiamond.GetComponent<Image>().color = GoldColor;

        // Main status title
        GameObject mainTxtGo = new GameObject("MainTitle", typeof(RectTransform), typeof(Text));
        RectTransform mrt = mainTxtGo.GetComponent<RectTransform>();
        mrt.SetParent(centerGo.transform, false);
        mrt.anchoredPosition = new Vector2(0f, 25f);
        mrt.sizeDelta = new Vector2(540f, 32f);
        mainStatusText = mainTxtGo.GetComponent<Text>();
        mainStatusText.font = font ?? DetectiveAssetBank.GetDefaultUIFont();
        mainStatusText.fontSize = 18;
        mainStatusText.fontStyle = FontStyle.Bold;
        mainStatusText.alignment = TextAnchor.MiddleCenter;
        mainStatusText.color = GoldColor;
        mainStatusText.text = "HỆ THỐNG TRINH THÁM AI ĐANG TẠO VỤ ÁN...";

        // Sub status text (pipeline steps)
        GameObject subTxtGo = new GameObject("SubStatus", typeof(RectTransform), typeof(Text));
        RectTransform srt = subTxtGo.GetComponent<RectTransform>();
        srt.SetParent(centerGo.transform, false);
        srt.anchoredPosition = new Vector2(0f, -15f);
        srt.sizeDelta = new Vector2(540f, 28f);
        subStatusText = subTxtGo.GetComponent<Text>();
        subStatusText.font = font ?? DetectiveAssetBank.GetDefaultUIFont();
        subStatusText.fontSize = 13;
        subStatusText.alignment = TextAnchor.MiddleCenter;
        subStatusText.color = TextWhite;
        subStatusText.text = "Đang kết nối AI Engine...";

        // Progress bar
        GameObject sliderGo = new GameObject("ProgressBar", typeof(RectTransform), typeof(Slider));
        RectTransform prt = sliderGo.GetComponent<RectTransform>();
        prt.SetParent(centerGo.transform, false);
        prt.anchoredPosition = new Vector2(0f, -65f);
        prt.sizeDelta = new Vector2(480f, 16f);

        progressBar = sliderGo.GetComponent<Slider>();
        progressBar.minValue = 0f;
        progressBar.maxValue = 1f;

        GameObject bgGo = new GameObject("Background", typeof(RectTransform), typeof(Image));
        RectTransform bgrt = bgGo.GetComponent<RectTransform>();
        bgrt.SetParent(sliderGo.transform, false);
        bgrt.anchorMin = Vector2.zero;
        bgrt.anchorMax = Vector2.one;
        bgrt.sizeDelta = Vector2.zero;
        bgGo.GetComponent<Image>().color = new Color(0.12f, 0.12f, 0.14f);

        GameObject fillArea = new GameObject("Fill Area", typeof(RectTransform));
        RectTransform fart = fillArea.GetComponent<RectTransform>();
        fart.SetParent(sliderGo.transform, false);
        fart.anchorMin = Vector2.zero;
        fart.anchorMax = Vector2.one;
        fart.sizeDelta = Vector2.zero;

        GameObject fill = new GameObject("Fill", typeof(RectTransform), typeof(Image));
        RectTransform frt = fill.GetComponent<RectTransform>();
        frt.SetParent(fillArea.transform, false);
        frt.sizeDelta = Vector2.zero;
        fill.GetComponent<Image>().color = new Color(0.18f, 0.55f, 0.35f);
        progressBar.fillRect = frt;

        // Bottom hint
        GameObject hintGo = new GameObject("Hint", typeof(RectTransform), typeof(Text));
        RectTransform hrt = hintGo.GetComponent<RectTransform>();
        hrt.SetParent(centerGo.transform, false);
        hrt.anchoredPosition = new Vector2(0f, -110f);
        hrt.sizeDelta = new Vector2(500f, 24f);
        Text hintTxt = hintGo.GetComponent<Text>();
        hintTxt.font = font ?? DetectiveAssetBank.GetDefaultUIFont();
        hintTxt.fontSize = 11;
        hintTxt.fontStyle = FontStyle.Italic;
        hintTxt.alignment = TextAnchor.MiddleCenter;
        hintTxt.color = TextMuted;
        hintTxt.text = "Mẹo: Bằng chứng ngoại phạm của hung thủ luôn có lỗ hổng thời gian so với đồ thị Henssge.";
    }
}
