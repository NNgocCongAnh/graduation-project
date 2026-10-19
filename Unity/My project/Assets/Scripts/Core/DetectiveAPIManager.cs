using UnityEngine;
using UnityEngine.Networking;
using System;
using System.Collections;
using System.Collections.Generic;

public class DetectiveAPIManager : MonoBehaviour
{
    public static DetectiveAPIManager Instance { get; private set; }

    [Header("Server Configuration")]
    [SerializeField] private string baseUrl = "http://localhost:8000";

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
    /// </summary>
    public void GetSampleCase(Action<bool, CaseDossier> callback)
    {
        StartCoroutine(GetRequest("/api/case/sample", (success, json) =>
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
            byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(json);
            req.uploadHandler = new UploadHandlerRaw(bodyRaw);
            req.downloadHandler = new DownloadHandlerBuffer();
            req.SetRequestHeader("Content-Type", "application/json");

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
