using UnityEngine;
using UnityEngine.UI;

public class AutopsyReportModal : MonoBehaviour
{
    public static AutopsyReportModal Instance { get; private set; }

    [Header("UI Component Bindings")]
    [SerializeField] private GameObject modalRoot;
    [SerializeField] private Text victimNameText;
    [SerializeField] private Text victimMetaText;
    [SerializeField] private Text bodyTempText;
    [SerializeField] private Text ambientTempText;
    [SerializeField] private Text estimatedTodText;
    [SerializeField] private Text livorMortisText;
    [SerializeField] private Text woundText;
    [SerializeField] private Button closeButton;

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

        if (closeButton != null)
        {
            closeButton.onClick.AddListener(Close);
        }

        if (modalRoot != null)
        {
            modalRoot.SetActive(false);
        }
    }

    public void Open()
    {
        CaseDossier currentCase = GameController.Instance != null ? GameController.Instance.currentCase : null;
        if (currentCase == null || currentCase.victim == null)
        {
            Debug.LogWarning("[AutopsyReportModal] No case or victim data available.");
            return;
        }

        VictimData v = currentCase.victim;
        ForensicData f = v.forensic_data ?? new ForensicData();

        if (victimNameText != null) victimNameText.text = $"NẠN NHÂN: {v.name.ToUpper()}";
        if (victimMetaText != null) victimMetaText.text = $"<b>Tuổi:</b> {v.age}  |  <b>Nghề nghiệp:</b> {v.occupation}  |  <b>Hồ sơ vụ án:</b> {currentCase.case_id}";

        if (bodyTempText != null) bodyTempText.text = $"{f.body_temp:F1} °C";
        if (ambientTempText != null) ambientTempText.text = $"{f.ambient_temp:F1} °C";
        if (estimatedTodText != null) estimatedTodText.text = $"[{f.estimated_tod_start} - {f.estimated_tod_end}]";

        if (livorMortisText != null) livorMortisText.text = string.IsNullOrEmpty(f.livor_mortis_state) ? "Hoen tử thi cố định mặt sau" : f.livor_mortis_state;
        if (woundText != null) woundText.text = string.IsNullOrEmpty(f.wound_description) ? "Vết thương hở do vật sắc nhọn gây mất máu cấp" : f.wound_description;

        if (modalRoot != null)
        {
            modalRoot.SetActive(true);
            transform.SetAsLastSibling();
        }
    }

    public void Close()
    {
        if (modalRoot != null)
        {
            modalRoot.SetActive(false);
        }
    }
}

