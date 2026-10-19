using UnityEngine;
using UnityEngine.Networking;
using System.Collections;
using System.Collections.Generic;
using System;

public class DetectiveAPIManager : MonoBehaviour
{
    public static DetectiveAPIManager Instance { get; private set; }

    [SerializeField] private string baseUrl = "http://localhost:8000";
    
    void Awake()
    {
        if (Instance == null) Instance = this;
        else Destroy(gameObject);
    }

    public delegate void CaseRequestCallback(bool success, CaseData data);

    public void GenerateCase(string requestPayload, CaseRequestCallback callback)
    {
        StartCoroutine(PostRequest("/api/case/generate", requestPayload, (success, json) => {
            if (success)
            {
                CaseData data = JsonUtility.FromJson<CaseData>(json);
                callback?.Invoke(true, data);
            }
            else callback?.Invoke(false, null);
        }));
    }

    public delegate void VerifyCallback(bool isCorrect, string feedback);

    public void VerifyDeduction(string deductionJson, VerifyCallback callback)
    {
        StartCoroutine(PostRequest("/api/case/verify", deductionJson, (success, json) => {
            if (success)
            {
                // Assuming the backend returns a simple JSON with { "correct": bool, "feedback": string }
                // In a real scenario, we'd use a wrapper class.
                callback?.Invoke(true, json); 
            }
            else callback?.Invoke(false, "Connection Error");
        }));
    }

    private IEnumerator PostRequest(string endpoint, string json, Action<bool, string> callback)
    {
        using (UnityWebRequest request = new UnityWebRequest(baseUrl + endpoint, "POST"))
        {
            byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(json);
            request.uploadHandler = new UploadHandlerRaw(bodyRaw);
            request.downloadHandler = new DownloadHandlerUTF8();
            request.SetRequestHeader("Content-Type", "application/json");

            yield return request.SendWebRequest();

            if (request.result != UnityWebRequest.Result.Success)
            {
                Debug.LogError($"API Error: {request.error}");
                callback(false, null);
            }
            else
            {
                callback(true, request.downloadHandler.text);
            }
        }
    }
}
