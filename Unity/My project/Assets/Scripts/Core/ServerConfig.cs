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

    private const string DefaultHost = "localhost";
    private const string DefaultPlayer = "Thám tử";
    private const string DefaultRoom = "PHONG-1";

    public static event Action OnChanged;

    /// <summary>Host name or IP, optionally with ":port" (e.g. "192.168.1.20" or "192.168.1.20:8000").</summary>
    public static string Host => PlayerPrefs.GetString(KeyHost, DefaultHost);
    public static string PlayerName => PlayerPrefs.GetString(KeyPlayer, DefaultPlayer);
    public static string RoomId => PlayerPrefs.GetString(KeyRoom, DefaultRoom);

    public static string HostWithPort => Host.Contains(":") ? Host : $"{Host}:{DefaultHttpPort}";
    public static string HttpBaseUrl => $"http://{HostWithPort}";
    public static string WsRoomsUrl => $"ws://{HostWithPort}/ws/rooms";

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

    private static string Clean(string value, string fallback)
    {
        string trimmed = (value ?? "").Trim();
        if (trimmed.StartsWith("http://")) trimmed = trimmed.Substring("http://".Length);
        trimmed = trimmed.TrimEnd('/');
        return string.IsNullOrEmpty(trimmed) ? fallback : trimmed;
    }
}
