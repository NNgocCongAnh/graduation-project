using System;
using System.Security.Cryptography;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

/// <summary>
/// Client Integrity and Cryptographic Request Signing for Unsolved Case Files.
/// Protects the Cloud API backend against unauthorized curl, Postman, and scraping.
/// Uses HMAC-SHA256 with dynamic nonces, UTC timestamp window, and XOR-obfuscated secrets.
/// </summary>
public static class ClientSecurity
{
    private const string CLIENT_ID = "UnsolvedCaseFiles-v1";

    // Multi-byte XOR mask for binary obfuscation
    private static readonly byte[] MASK = new byte[] { 0x5A, 0x3F, 0x8C, 0x1E, 0x77, 0xA2, 0x4D, 0x69 };

    // Obfuscated secret key bytes (resists static memory/binary inspection)
    private static readonly byte[] OBFUSCATED_SECRET = new byte[] {
        0x0a, 0x57, 0xe9, 0x70, 0x1e, 0xc9, 0x2c, 0x08,
        0x05, 0x6a, 0xcf, 0x58, 0x28, 0xe3, 0x04, 0x36,
        0x09, 0x5a, 0xef, 0x6c, 0x12, 0xd6, 0x06, 0x0c,
        0x23, 0x60, 0xbe, 0x2e, 0x45, 0x94, 0x12, 0x3a,
        0x3f, 0x5c, 0xf9, 0x6c, 0x12, 0xea, 0x20, 0x08,
        0x39, 0x74, 0xe9, 0x67, 0x28, 0xda, 0x74, 0x48
    };

    /// <summary>
    /// Reconstruct shared secret in memory dynamically.
    /// </summary>
    private static string GetSecret()
    {
        byte[] deobfuscated = new byte[OBFUSCATED_SECRET.Length];
        for (int i = 0; i < OBFUSCATED_SECRET.Length; i++)
        {
            deobfuscated[i] = (byte)(OBFUSCATED_SECRET[i] ^ MASK[i % MASK.Length]);
        }
        return Encoding.UTF8.GetString(deobfuscated);
    }

    /// <summary>
    /// Sign an outgoing UnityWebRequest with HMAC-SHA256 and anti-replay headers.
    /// </summary>
    public static void SignRequest(UnityWebRequest request, string path, string body = "")
    {
        string method = request.method.ToUpperInvariant();
        string timestamp = DateTimeOffset.UtcNow.ToUnixTimeSeconds().ToString();
        string nonce = Guid.NewGuid().ToString("N");

        // Compute SHA-256 hash of body (empty string produces standard empty sha256)
        byte[] bodyBytes = string.IsNullOrEmpty(body) ? new byte[0] : Encoding.UTF8.GetBytes(body);
        string bodyHash = ComputeSha256Hex(bodyBytes);

        // Canonical request path (exclude query strings to match request.url.path)
        string normalizedPath = path.Contains("?") ? path.Split('?')[0] : path;

        // Canonical request representation
        string canonical = $"{method}\n{normalizedPath}\n{timestamp}\n{nonce}\n{bodyHash}";

        // Compute HMAC-SHA256 signature
        string signature = ComputeHmacSha256(GetSecret(), canonical);

        // Attach security headers
        request.SetRequestHeader("X-Game-Client", CLIENT_ID);
        request.SetRequestHeader("X-Game-Timestamp", timestamp);
        request.SetRequestHeader("X-Game-Nonce", nonce);
        request.SetRequestHeader("X-Game-Signature", signature);
    }

    private static string ComputeSha256Hex(byte[] data)
    {
        using (SHA256 sha = SHA256.Create())
        {
            byte[] hash = sha.ComputeHash(data);
            return ToLowerHex(hash);
        }
    }

    private static string ComputeHmacSha256(string secret, string message)
    {
        byte[] keyBytes = Encoding.UTF8.GetBytes(secret);
        byte[] msgBytes = Encoding.UTF8.GetBytes(message);

        using (HMACSHA256 hmac = new HMACSHA256(keyBytes))
        {
            byte[] hash = hmac.ComputeHash(msgBytes);
            return ToLowerHex(hash);
        }
    }

    private static string ToLowerHex(byte[] bytes)
    {
        StringBuilder sb = new StringBuilder(bytes.Length * 2);
        for (int i = 0; i < bytes.Length; i++)
        {
            sb.Append(bytes[i].ToString("x2"));
        }
        return sb.ToString();
    }
}
