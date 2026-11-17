using System;
using UnityEngine;

/// <summary>
/// Single source of truth for where the backend lives (REST + WebSocket) and who
/// the local player is. Persisted in PlayerPrefs so a LAN guest only types the
/// host IP once.
/// </summary>
public static class ServerConfig
{
    public const int DefaultHttpPort = 8000;
    public const int MaxPlayersPerRoom = 3;

    private const string KeyHost = "detective.server.host";
    private const string KeyPlayer = "detective.player.name";
    private const string KeyRoom = "detective.room.id";
    private const string KeyModel = "detective.llm.model";
    private const string KeyApiBase = "detective.llm.apibase";
    private const string KeyApiKey = "detective.llm.apikey";

    private const string DefaultHost = "localhost";
    private const string DefaultPlayer = "Thám tử";
    private const string DefaultRoom = "PHONG-1";
    public const string DefaultModel = "gh/gpt-4o-mini";
    public const string DefaultApiBase = "http://localhost:20128/v1";
    public const string DefaultApiKey = "sk-9router-local";

    public static event Action OnChanged;

    private static string rawHost => PlayerPrefs.GetString(KeyHost, DefaultHost);

    public static string Host => Clean(rawHost, DefaultHost);
    public static string PlayerName => PlayerPrefs.GetString(KeyPlayer, DefaultPlayer);
    public static string RoomId => PlayerPrefs.GetString(KeyRoom, DefaultRoom);
    public static string SelectedModel => PlayerPrefs.GetString(KeyModel, DefaultModel);
    public static string ApiBase => PlayerPrefs.GetString(KeyApiBase, DefaultApiBase);
    public static string ApiKey => PlayerPrefs.GetString(KeyApiKey, DefaultApiKey);

    public static string HostWithPort => Host.Contains(":") ? Host : (IsCloudUrl ? Host : $"{Host}:{DefaultHttpPort}");

    public static bool IsCloudUrl =>
        rawHost.StartsWith("https://", StringComparison.OrdinalIgnoreCase) ||
        Host.Contains(".onrender.com") ||
        Host.Contains(".hf.space") ||
        Host.Contains(".railway.app") ||
        Host.Contains(".app") ||
        Host.Contains(".com") ||
        Host.Contains(".io");

    public static string HttpBaseUrl
    {
        get
        {
            if (rawHost.StartsWith("http://", StringComparison.OrdinalIgnoreCase) ||
                rawHost.StartsWith("https://", StringComparison.OrdinalIgnoreCase))
            {
                return rawHost.TrimEnd('/');
            }
            if (IsCloudUrl)
            {
                return $"https://{Host}";
            }
            string hostWithPort = Host.Contains(":") ? Host : $"{Host}:{DefaultHttpPort}";
            return $"http://{hostWithPort}";
        }
    }

    public static string WsRoomsUrl
    {
        get
        {
            if (IsCloudUrl || rawHost.StartsWith("https://", StringComparison.OrdinalIgnoreCase))
            {
                string cleanDomain = Host.Contains(":") ? Host.Split(':')[0] : Host;
                return $"wss://{cleanDomain}/ws/rooms";
            }
            string hostWithPort = Host.Contains(":") ? Host : $"{Host}:{DefaultHttpPort}";
            return $"ws://{hostWithPort}/ws/rooms";
        }
    }

    public static bool IsLocalHost =>
        Host.StartsWith("localhost", StringComparison.OrdinalIgnoreCase) || Host.StartsWith("127.0.0.1");

    public static void Save(string host, string playerName, string roomId)
    {
        PlayerPrefs.SetString(KeyHost, Clean(host, DefaultHost));
        PlayerPrefs.SetString(KeyPlayer, Clean(playerName, DefaultPlayer));
        PlayerPrefs.SetString(KeyRoom, Clean(roomId, DefaultRoom).ToUpperInvariant());
        PlayerPrefs.Save();
        OnChanged?.Invoke();
    }

    public static void SaveModelConfig(string model, string apiBase = null, string apiKey = null)
    {
        if (!string.IsNullOrEmpty(model)) PlayerPrefs.SetString(KeyModel, model.Trim());
        if (!string.IsNullOrEmpty(apiBase)) PlayerPrefs.SetString(KeyApiBase, apiBase.Trim());
        if (!string.IsNullOrEmpty(apiKey)) PlayerPrefs.SetString(KeyApiKey, apiKey.Trim());
        PlayerPrefs.Save();
        OnChanged?.Invoke();
    }

    private static string Clean(string value, string fallback)
    {
        string trimmed = (value ?? "").Trim();
        if (trimmed.StartsWith("https://", StringComparison.OrdinalIgnoreCase)) trimmed = trimmed.Substring("https://".Length);
        else if (trimmed.StartsWith("http://", StringComparison.OrdinalIgnoreCase)) trimmed = trimmed.Substring("http://".Length);
        trimmed = trimmed.TrimEnd('/');
        return string.IsNullOrEmpty(trimmed) ? fallback : trimmed;
    }
}
