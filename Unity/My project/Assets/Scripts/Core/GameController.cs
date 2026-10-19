using UnityEngine;
using System.Collections;
using System.Collections.Generic;

public class GameController : MonoBehaviour
{
    public static GameController Instance { get; private set; }

    [Header("Manager References")]
    [SerializeField] private DetectiveAPIManager apiManager;
    [SerializeField] private CorkboardManager corkboardManager;
    [SerializeField] private GameObject loadingScreen;

    [Header("Current Game State")]
    public string currentCaseId = "CASE-2026-001";
    public CaseDossier currentCase;
    public bool isCaseLoaded = false;

    private void Awake()
    {
        if (Instance == null)
        {
            Instance = this;
            DontDestroyOnLoad(gameObject);
        }
        else
        {
            Destroy(gameObject);
        }
    }

    private void Start()
    {
        if (apiManager == null) apiManager = DetectiveAPIManager.Instance ?? FindObjectOfType<DetectiveAPIManager>();
        if (corkboardManager == null) corkboardManager = FindObjectOfType<CorkboardManager>();

        StartCoroutine(LoadInitialCaseRoutine());
    }

    public IEnumerator LoadInitialCaseRoutine()
    {
        Debug.Log("[GameController] Fetching sample case from backend...");
        if (loadingScreen != null) loadingScreen.SetActive(true);

        bool requestFinished = false;
        bool requestSuccess = false;
        CaseDossier loadedDossier = null;

        apiManager.GetSampleCase((success, data) =>
        {
            requestFinished = true;
            requestSuccess = success;
            loadedDossier = data;
        });

        while (!requestFinished)
        {
            yield return null;
        }

        if (requestSuccess && loadedDossier != null)
        {
            currentCase = loadedDossier;
            currentCaseId = loadedDossier.case_id;
            isCaseLoaded = true;
            Debug.Log($"[GameController] Case '{currentCase.title}' loaded successfully!");

            SetupCorkboard();
        }
        else
        {
            Debug.LogError("[GameController] Failed to load case from backend! Ensure FastAPI is running at http://localhost:8000");
        }

        if (loadingScreen != null) loadingScreen.SetActive(false);
    }

    private void SetupCorkboard()
    {
        if (corkboardManager == null)
        {
            Debug.LogWarning("[GameController] CorkboardManager not found in scene. Setup skipped.");
            return;
        }

        corkboardManager.ClearBoard();

        // 1. Instantiate Suspect Cards
        if (currentCase.suspects != null)
        {
            foreach (var suspect in currentCase.suspects)
            {
                corkboardManager.AddCard(suspect.id, suspect.name, true, suspect.image_url);
            }
        }

        // 2. Instantiate Evidence Cards
        if (currentCase.evidences != null)
        {
            foreach (var evidence in currentCase.evidences)
            {
                corkboardManager.AddCard(evidence.id, evidence.title, false, evidence.image_url);
            }
        }
    }

    /// <summary>
    /// Called when player accuses a suspect with selected key clues.
    /// </summary>
    public void SubmitAccusation(string accusedSuspectId, List<string> selectedEvidenceIds)
    {
        Debug.Log($"[GameController] Submitting deduction: Accused={accusedSuspectId}, Evidences={string.Join(", ", selectedEvidenceIds)}");

        VerifyRequest req = new VerifyRequest
        {
            case_id = currentCaseId,
            selected_suspect_id = accusedSuspectId,
            selected_evidence_ids = selectedEvidenceIds ?? new List<string>()
        };

        apiManager.VerifyDeduction(req, (success, response) =>
        {
            if (success && response != null)
            {
                Debug.Log($"[GameController] Deduction Verdict: is_correct={response.is_correct}");
                Debug.Log($"[GameController] Feedback: {response.feedback}");
                if (response.is_correct)
                {
                    Debug.Log($"[GameController] Solved Contradiction: {response.core_contradiction}");
                }
            }
            else
            {
                Debug.LogError("[GameController] Failed to verify deduction with server.");
            }
        });
    }
}
