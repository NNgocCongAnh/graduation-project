using UnityEngine;
using UnityEngine.UI;
using System.Collections.Generic;

public class AccusationModal : MonoBehaviour
{
    public static AccusationModal Instance { get; private set; }

    [Header("Main Dialog References")]
    [SerializeField] private GameObject modalRoot;
    [SerializeField] private Dropdown suspectDropdown;
    [SerializeField] private Transform evidenceTogglesContainer;
    [SerializeField] private GameObject evidenceTogglePrefab;
    [SerializeField] private Button submitButton;
    [SerializeField] private Button closeButton;

    [Header("Verdict Result Panel References")]
    [SerializeField] private GameObject verdictPanel;
    [SerializeField] private Text verdictTitleText;
    [SerializeField] private Text verdictFeedbackText;
    [SerializeField] private Text coreContradictionText;
    [SerializeField] private Button closeVerdictButton;

    private List<string> suspectIds = new List<string>();
    private Dictionary<string, Toggle> evidenceToggleMap = new Dictionary<string, Toggle>();

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

        if (submitButton != null) submitButton.onClick.AddListener(OnSubmitClicked);
        if (closeButton != null) closeButton.onClick.AddListener(Close);
        if (closeVerdictButton != null) closeVerdictButton.onClick.AddListener(CloseVerdict);

        if (modalRoot != null) modalRoot.SetActive(false);
        if (verdictPanel != null) verdictPanel.SetActive(false);
    }

    public void Open()
    {
        if (modalRoot == null) return;
        modalRoot.SetActive(true);
        if (verdictPanel != null) verdictPanel.SetActive(false);
        transform.SetAsLastSibling();

        PopulateOptions();
    }

    public void Close()
    {
        if (modalRoot != null) modalRoot.SetActive(false);
        if (verdictPanel != null) verdictPanel.SetActive(false);
    }

    private void PopulateOptions()
    {
        CaseDossier currentCase = GameController.Instance != null ? GameController.Instance.currentCase : null;
        if (currentCase == null) return;

        // 1. Suspects
        if (suspectDropdown != null)
        {
            suspectDropdown.ClearOptions();
            suspectIds.Clear();
            List<string> options = new List<string>();

            if (currentCase.suspects != null)
            {
                foreach (var s in currentCase.suspects)
                {
                    options.Add($"{s.name} ({s.occupation})");
                    suspectIds.Add(s.id);
                }
            }
            suspectDropdown.AddOptions(options);
        }

        // 2. Evidences
        evidenceToggleMap.Clear();
        if (evidenceTogglesContainer != null)
        {
            foreach (Transform child in evidenceTogglesContainer)
            {
                Destroy(child.gameObject);
            }

            if (currentCase.evidences != null && evidenceTogglePrefab != null)
            {
                foreach (var ev in currentCase.evidences)
                {
                    GameObject toggleObj = Instantiate(evidenceTogglePrefab, evidenceTogglesContainer);
                    toggleObj.SetActive(true);
                    Text label = toggleObj.GetComponentInChildren<Text>();
                    if (label != null) label.text = $"{ev.id}: {ev.title}";

                    Toggle toggle = toggleObj.GetComponent<Toggle>();
                    if (toggle != null)
                    {
                        evidenceToggleMap[ev.id] = toggle;
                    }
                }
            }
        }
    }

    private void OnSubmitClicked()
    {
        if (suspectDropdown == null || suspectIds.Count == 0) return;

        int selectedIndex = suspectDropdown.value;
        if (selectedIndex < 0 || selectedIndex >= suspectIds.Count) return;
        string accusedId = suspectIds[selectedIndex];

        List<string> selectedEvidences = new List<string>();
        foreach (var pair in evidenceToggleMap)
        {
            if (pair.Value != null && pair.Value.isOn)
            {
                selectedEvidences.Add(pair.Key);
            }
        }

        if (submitButton != null) submitButton.interactable = false;

        if (GameController.Instance != null)
        {
            GameController.Instance.SubmitAccusation(accusedId, selectedEvidences);
        }
    }

    public void ShowVerdict(VerifyResponse response)
    {
        if (submitButton != null) submitButton.interactable = true;
        if (verdictPanel == null) return;

        verdictPanel.SetActive(true);

        if (verdictTitleText != null)
        {
            verdictTitleText.text = $"{GetVerdictTitle(response)} — {Mathf.RoundToInt(response.score)}/100";
            verdictTitleText.color = response.is_correct
                ? new Color(0.2f, 0.8f, 0.2f)
                : new Color(0.9f, 0.2f, 0.2f);
        }

        if (verdictFeedbackText != null)
        {
            verdictFeedbackText.text = $"{response.feedback}\n\n{FormatScoreBreakdown(response)}";
        }

        if (coreContradictionText != null)
        {
            coreContradictionText.text = string.IsNullOrEmpty(response.core_contradiction) 
                ? "" 
                : $"<b>Mâu thuẫn mấu chốt:</b>\n{response.core_contradiction}";
        }
    }

    private static string GetVerdictTitle(VerifyResponse response)
    {
        switch (response.verdict)
        {
            case "solved_perfect": return "PHÁ ÁN HOÀN HẢO! (SOLVED)";
            case "solved_flawed": return "PHÁ ÁN THÀNH CÔNG (CÒN SƠ SUẤT)";
            case "insufficient_evidence": return "ĐÚNG HUNG THỦ, THIẾU CHỨNG CỨ";
            case "trapped_by_red_herring": return "SA BẪY MANH MỐI GIẢ!";
            case "spam_detected": return "NỘP CHỨNG CỨ TRÀN LAN!";
            case "wrong_suspect": return "PHÁN ĐOÁN SAI LẦM! (FAILED)";
            default:
                return response.is_correct ? "PHÁ ÁN THÀNH CÔNG! (SOLVED)" : "PHÁN ĐOÁN SAI LẦM! (FAILED)";
        }
    }

    private static string FormatScoreBreakdown(VerifyResponse response)
    {
        string summary =
            $"Chứng cứ then chốt: {response.found_crucial_count}/{response.total_crucial_count}" +
            $" · Manh mối giả: {response.red_herrings_selected_count}" +
            $" · Không liên quan: {response.irrelevant_clues_count}";

        DeductionScoreBreakdown b = response.score_breakdown;
        if (b == null) return summary;

        return summary +
            $"\n<b>Điểm:</b> Hung thủ +{b.base_culprit_score:0}" +
            $" · Chứng cứ +{b.crucial_clues_score:0}" +
            $" · Chính xác +{b.precision_bonus:0}" +
            $" · Phạt -{b.red_herring_penalty:0}" +
            $" = <b>{b.total_score:0}</b>";
    }

    private void CloseVerdict()
    {
        if (verdictPanel != null) verdictPanel.SetActive(false);
    }
}

