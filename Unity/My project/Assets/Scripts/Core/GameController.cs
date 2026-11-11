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

        DetectiveNetworkManager net = DetectiveNetworkManager.Instance;
        bool roomHasOtherCase = net != null && !string.IsNullOrEmpty(net.RoomCaseId) && net.RoomCaseId != loadedDossier?.case_id;

        if (roomHasOtherCase)
        {
            Debug.Log($"[GameController] Co-op room is on '{net.RoomCaseId}', skipping sample case.");
        }
        else if (requestSuccess && loadedDossier != null)
        {
            Debug.Log($"[GameController] Case '{loadedDossier.title}' loaded successfully!");
            ApplyCase(loadedDossier, announceToRoom: true);
        }
        else
        {
            Debug.LogError("[GameController] Failed to load case from backend! Ensure FastAPI is running at http://localhost:8000");
        }

        if (loadingScreen != null) loadingScreen.SetActive(false);
    }

    /// <summary>Local player opened/generated a case: show it and switch the co-op room to it.</summary>
    public void LoadCaseFromData(CaseDossier dossier)
    {
        ApplyCase(dossier, announceToRoom: true);
    }

    /// <summary>
    /// The co-op room switched case (or we just joined): fetch it unless it is already open.
    /// </summary>
    public void LoadCaseFromRoom(string caseId, System.Action onLoaded)
    {
        if (string.IsNullOrEmpty(caseId)) return;
        if (isCaseLoaded && currentCaseId == caseId)
        {
            onLoaded?.Invoke();
            return;
        }

        apiManager.GetCaseById(caseId, (success, dossier) =>
        {
            if (!success)
            {
                Debug.LogError($"[GameController] Could not fetch room case '{caseId}' from {ServerConfig.HttpBaseUrl}");
                return;
            }
            ApplyCase(dossier, announceToRoom: false);
            onLoaded?.Invoke();
        });
    }

    private void ApplyCase(CaseDossier dossier, bool announceToRoom)
    {
        if (dossier == null) return;
        currentCase = dossier;
        currentCaseId = dossier.case_id;
        isCaseLoaded = true;
        Debug.Log($"[GameController] Loaded new case: '{dossier.title}' ({dossier.case_id})");

        SetupCorkboard();

        // Dynamically update HUD Case Title
        GameObject titleObj = GameObject.Find("Case_Title_Text");
        if (titleObj != null)
        {
            UnityEngine.UI.Text t = titleObj.GetComponent<UnityEngine.UI.Text>();
            if (t != null)
            {
                t.text = $"PHÒNG ĐIỀU TRA // {dossier.case_id}: {dossier.title.ToUpper()}";
            }
        }

        if (announceToRoom && DetectiveNetworkManager.Instance != null)
        {
            DetectiveNetworkManager.Instance.AnnounceCaseLoaded(dossier.case_id);
        }
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

        // 3. Connect related cards with detective red strings
        corkboardManager.UpdateRedStrings();
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

                if (AccusationModal.Instance != null)
                {
                    AccusationModal.Instance.ShowVerdict(response);
                }
            }
            else
            {
                Debug.LogError("[GameController] Failed to verify deduction with server.");
            }
        });
    }
}

