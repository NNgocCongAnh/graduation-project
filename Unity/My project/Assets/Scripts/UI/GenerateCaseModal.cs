using UnityEngine;
using UnityEngine.UI;
using System.Collections;

public class GenerateCaseModal : MonoBehaviour
{
    public static GenerateCaseModal Instance { get; private set; }

    [Header("UI Component Bindings")]
    [SerializeField] private GameObject modalRoot;
    [SerializeField] private InputField themeInputField;
    [SerializeField] private Button generateButton;
    [SerializeField] private Button closeButton;
    [SerializeField] private Button preset1Button;
    [SerializeField] private Button preset2Button;
    [SerializeField] private Button preset3Button;

    [Header("Loading State UI")]
    [SerializeField] private GameObject loadingPanel;
    [SerializeField] private Text loadingStatusText;

    private void Awake()
    {
        if (Instance == null)
        {
            Instance = this;
        }
        else
        {
            Destroy(gameObject);
            return;
        }

        if (generateButton != null) generateButton.onClick.AddListener(OnGenerateClicked);
        if (closeButton != null) closeButton.onClick.AddListener(Close);

        if (preset1Button != null) preset1Button.onClick.AddListener(() => SetPreset("Bí ẩn Biệt thự cổ Blackwood"));
        if (preset2Button != null) preset2Button.onClick.AddListener(() => SetPreset("Bí mật phòng thí nghiệm Trí tuệ Nhân tạo"));
        if (preset3Button != null) preset3Button.onClick.AddListener(() => SetPreset("Án mạng trên Chuyến tàu Đêm Hà Nội - Sài Gòn"));

        if (modalRoot != null) modalRoot.SetActive(false);
        if (loadingPanel != null) loadingPanel.SetActive(false);
    }

    public void Open()
    {
        if (modalRoot != null)
        {
            modalRoot.SetActive(true);
            transform.SetAsLastSibling();
        }

        if (loadingPanel != null) loadingPanel.SetActive(false);
        if (generateButton != null) generateButton.interactable = true;
    }

    public void Close()
    {
        if (modalRoot != null) modalRoot.SetActive(false);
        if (loadingPanel != null) loadingPanel.SetActive(false);
    }

    private void SetPreset(string presetText)
    {
        if (themeInputField != null)
        {
            themeInputField.text = presetText;
        }
    }

    private void OnGenerateClicked()
    {
        string theme = themeInputField != null ? themeInputField.text.Trim() : "";
        if (string.IsNullOrEmpty(theme))
        {
            theme = "Án mạng bí ẩn tại Biệt thự cổ";
        }

        GenerateCaseRequest req = new GenerateCaseRequest
        {
            theme = theme,
            country = "Việt Nam",
            era = "Hiện đại",
            mystery_type = "Án mạng bí ẩn"
        };

        string json = JsonUtility.ToJson(req);

        if (loadingPanel != null) loadingPanel.SetActive(true);
        if (generateButton != null) generateButton.interactable = false;

        StartCoroutine(SimulatePipelineSteps());

        if (DetectiveAPIManager.Instance != null)
        {
            DetectiveAPIManager.Instance.GenerateCase(json, (success, dossier) =>
            {
                if (success && dossier != null)
                {
                    Debug.Log($"[GenerateCaseModal] Case generated successfully: {dossier.title}");
                    if (GameController.Instance != null)
                    {
                        GameController.Instance.LoadCaseFromData(dossier);
                    }
                    Close();
                }
                else
                {
                    if (loadingStatusText != null)
                    {
                        loadingStatusText.text = "<color=#E53E3E>Lỗi sinh vụ án từ Backend! Vui lòng kiểm tra lại kết nối.</color>";
                    }
                    if (generateButton != null) generateButton.interactable = true;
                }
            });
        }
    }

    private IEnumerator SimulatePipelineSteps()
    {
        string[] steps = new string[]
        {
            "Khởi động Multi-Agent Pipeline... [Tác tử 1/4: OutlineAgent tạo bối cảnh & nạn nhân]",
            "Đang tạo nhân vật... [Tác tử 2/4: CharacterAgent sinh nghi phạm & alibi]",
            "Đang thu thập hiện trường... [Tác tử 3/4: ClueAgent & Tính toán giải tích nhiệt Henssge]",
            "Kiểm định hình thức... [Tác tử 4/4: DeductionAgent & Bipartite Graph Solvability Check]"
        };

        for (int i = 0; i < steps.Length; i++)
        {
            if (loadingStatusText != null)
            {
                loadingStatusText.text = steps[i];
            }
            yield return new WaitForSeconds(3.0f);
        }
    }
}

