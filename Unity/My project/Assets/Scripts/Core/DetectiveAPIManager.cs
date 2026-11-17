using UnityEngine;
using UnityEngine.Networking;
using System;
using System.Collections;
using System.Collections.Generic;

public class DetectiveAPIManager : MonoBehaviour
{
    public static DetectiveAPIManager Instance { get; private set; }

    // Host is configurable at runtime (LAN lobby); see ServerConfig.
    private static string baseUrl => ServerConfig.HttpBaseUrl;

    void Awake()
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

    /// <summary>
    /// Fetch verified sample case dossier for offline testing and quick start.
    /// Prioritizes local bundled sample case in StreamingAssets for instant offline playability.
    /// </summary>
    public void GetSampleCase(Action<bool, CaseDossier> callback)
    {
        // 1. Instant check of local bundled sample case in StreamingAssets
        CaseDossier localDossier = LoadLocalSampleCase();
        if (localDossier != null)
        {
            Debug.Log("[APIManager] Loaded offline bundled sample case successfully!");
            callback?.Invoke(true, localDossier);
            return;
        }

        // 2. Fallback to HTTP request with timeout
        StartCoroutine(GetRequest("/api/case/sample", (success, json) =>
        {
            if (success)
            {
                try
                {
                    CaseDossier dossier = JsonUtility.FromJson<CaseDossier>(json);
                    callback?.Invoke(true, dossier);
                    return;
                }
                catch (Exception e)
                {
                    Debug.LogError($"[APIManager] JSON Parse Error: {e.Message}");
                }
            }
            callback?.Invoke(false, null);
        }));
    }

    public static CaseDossier LoadLocalSampleCase()
    {
        string[] paths = new string[]
        {
            System.IO.Path.Combine(Application.streamingAssetsPath, "sample_case.json"),
            System.IO.Path.Combine(Application.dataPath, "StreamingAssets", "sample_case.json"),
            System.IO.Path.Combine(Application.dataPath, "..", "StreamingAssets", "sample_case.json")
        };
        foreach (string p in paths)
        {
            if (System.IO.File.Exists(p))
            {
                try
                {
                    string json = System.IO.File.ReadAllText(p);
                    return JsonUtility.FromJson<CaseDossier>(json);
                }
                catch { }
            }
        }
        return null;
    }

    /// <summary>
    /// Fetch a specific case by ID (used when joining a co-op room that already has a case).
    /// </summary>
    public void GetCaseById(string caseId, Action<bool, CaseDossier> callback)
    {
        StartCoroutine(GetRequest($"/api/case/{UnityWebRequest.EscapeURL(caseId)}", (success, json) =>
        {
            CaseDossier dossier = success ? ParseOrNull(json) : null;
            callback?.Invoke(dossier != null, dossier);
        }));
    }

    private static CaseDossier ParseOrNull(string json)
    {
        try
        {
            return string.IsNullOrEmpty(json) ? null : JsonUtility.FromJson<CaseDossier>(json);
        }
        catch (Exception e)
        {
            Debug.LogError($"[APIManager] JSON Parse Error: {e.Message}");
            return null;
        }
    }

    /// <summary>
    /// Generate a brand new case dossier via 4-step LLM Pipeline and Validator.
    /// </summary>
    public void GenerateCase(string requestJson, Action<bool, CaseDossier> callback)
    {
        StartCoroutine(PostRequest("/api/case/generate", requestJson, (success, json) =>
        {
            if (success)
            {
                try
                {
                    CaseDossier dossier = JsonUtility.FromJson<CaseDossier>(json);
                    callback?.Invoke(true, dossier);
                }
                catch (Exception e)
                {
                    Debug.LogError($"[APIManager] JSON Parse Error: {e.Message}");
                    callback?.Invoke(false, null);
                }
            }
            else
            {
                callback?.Invoke(false, null);
            }
        }));
    }

    /// <summary>
    /// Update backend AI model and credentials at runtime.
    /// </summary>
    public void UpdateBackendSettings(string model, string apiBase, string apiKey, Action<bool, string> callback)
    {
        UpdateSettingsRequest payload = new UpdateSettingsRequest
        {
            model = model,
            api_base = apiBase,
            api_key = apiKey
        };
        string json = JsonUtility.ToJson(payload);
        StartCoroutine(PostRequest("/api/settings", json, (success, resJson) =>
        {
            callback?.Invoke(success, resJson);
        }));
    }

    /// <summary>
    /// Verify player deduction (accused suspect and selected clues).
    /// </summary>
    public void VerifyDeduction(VerifyRequest requestPayload, Action<bool, VerifyResponse> callback)
    {
        string json = JsonUtility.ToJson(requestPayload);
        StartCoroutine(PostRequest("/api/case/verify", json, (success, responseJson) =>
        {
            if (success)
            {
                try
                {
                    VerifyResponse res = JsonUtility.FromJson<VerifyResponse>(responseJson);
                    callback?.Invoke(true, res);
                }
                catch (Exception e)
                {
                    Debug.LogError($"[APIManager] Verify JSON Parse Error: {e.Message}");
                    callback?.Invoke(false, null);
                }
            }
            else
            {
                callback?.Invoke(false, null);
            }
        }));
    }

    /// <summary>
    /// Download an image texture from local FastAPI static server or remote URL.
    /// </summary>
    public void DownloadTexture(string relativeOrFullUrl, Action<bool, Texture2D> callback)
    {
        if (string.IsNullOrEmpty(relativeOrFullUrl))
        {
            callback?.Invoke(false, null);
            return;
        }

        string fullUrl = relativeOrFullUrl.StartsWith("http") ? relativeOrFullUrl : baseUrl + relativeOrFullUrl;
        StartCoroutine(DownloadTextureRoutine(fullUrl, callback));
    }

    private IEnumerator DownloadTextureRoutine(string url, Action<bool, Texture2D> callback)
    {
        using (UnityWebRequest uwr = UnityWebRequestTexture.GetTexture(url))
        {
            yield return uwr.SendWebRequest();

            if (uwr.result != UnityWebRequest.Result.Success)
            {
                Debug.LogWarning($"[APIManager] Failed to download texture from {url}: {uwr.error}");
                callback?.Invoke(false, null);
            }
            else
            {
                Texture2D texture = DownloadHandlerTexture.GetContent(uwr);
                callback?.Invoke(true, texture);
            }
        }
    }

    private IEnumerator GetRequest(string endpoint, Action<bool, string> callback)
    {
        using (UnityWebRequest req = UnityWebRequest.Get(baseUrl + endpoint))
        {
            req.timeout = 5; // 5-second timeout ensures we never freeze the game loop

            // Attach HMAC-SHA256 Client Integrity signature
            ClientSecurity.SignRequest(req, endpoint, "");

            yield return req.SendWebRequest();

            if (req.result != UnityWebRequest.Result.Success)
            {
                Debug.LogError($"[APIManager] GET Error ({endpoint}): {req.error}");
                callback(false, null);
            }
            else
            {
                callback(true, req.downloadHandler.text);
            }
        }
    }

    private IEnumerator PostRequest(string endpoint, string json, Action<bool, string> callback)
    {
        using (UnityWebRequest req = new UnityWebRequest(baseUrl + endpoint, "POST"))
        {
            req.timeout = 60; // 60-second timeout for LLM generation
            byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(json);
            req.uploadHandler = new UploadHandlerRaw(bodyRaw);
            req.downloadHandler = new DownloadHandlerBuffer();
            req.SetRequestHeader("Content-Type", "application/json");

            // Attach HMAC-SHA256 Client Integrity signature
            ClientSecurity.SignRequest(req, endpoint, json);

            yield return req.SendWebRequest();

            if (req.result != UnityWebRequest.Result.Success)
            {
                Debug.LogError($"[APIManager] POST Error ({endpoint}): {req.error}");
                callback(false, null);
            }
            else
            {
                callback(true, req.downloadHandler.text);
            }
        }
    }
}
