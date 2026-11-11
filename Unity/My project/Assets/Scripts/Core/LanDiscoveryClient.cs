using System;
using System.Collections;
using System.Collections.Generic;
using System.Net;
using System.Net.Sockets;
using System.Text;
using UnityEngine;

/// <summary>
/// Finds detective backends on the local network via UDP broadcast
/// (pairs with detective-backend/lan_discovery.py).
/// </summary>
public static class LanDiscoveryClient
{
    public const int DiscoveryPort = 47777;
    private static readonly byte[] Request = Encoding.ASCII.GetBytes("DETECTIVE_DISCOVER_V1");
    private const string ServiceName = "detective-game";

    [Serializable]
    private class DiscoveryReply
    {
        public string service;
        public string host_name;
        public int http_port;
    }

    public struct FoundHost
    {
        public string Address;   // "ip:port", ready for ServerConfig
        public string HostName;
    }

    /// <summary>Broadcasts once and collects replies for <paramref name="listenSeconds"/>.</summary>
    public static IEnumerator Discover(float listenSeconds, Action<List<FoundHost>> onDone)
    {
        var found = new Dictionary<string, FoundHost>();
        UdpClient udp = null;
        try
        {
            udp = new UdpClient(0) { EnableBroadcast = true };
            udp.Send(Request, Request.Length, new IPEndPoint(IPAddress.Broadcast, DiscoveryPort));
        }
        catch (Exception ex)
        {
            Debug.LogWarning($"[LanDiscovery] Broadcast failed: {ex.Message}");
            udp?.Close();
            onDone?.Invoke(new List<FoundHost>());
            yield break;
        }

        float deadline = Time.unscaledTime + listenSeconds;
        while (Time.unscaledTime < deadline)
        {
            while (udp.Available > 0)
            {
                TryReadReply(udp, found);
            }
            yield return null;
        }

        udp.Close();
        onDone?.Invoke(new List<FoundHost>(found.Values));
    }

    private static void TryReadReply(UdpClient udp, Dictionary<string, FoundHost> found)
    {
        try
        {
            IPEndPoint remote = new IPEndPoint(IPAddress.Any, 0);
            byte[] data = udp.Receive(ref remote);
            DiscoveryReply reply = JsonUtility.FromJson<DiscoveryReply>(Encoding.UTF8.GetString(data));
            if (reply == null || reply.service != ServiceName) return;

            string address = $"{remote.Address}:{reply.http_port}";
            found[address] = new FoundHost { Address = address, HostName = reply.host_name };
        }
        catch (Exception ex)
        {
            Debug.LogWarning($"[LanDiscovery] Bad reply ignored: {ex.Message}");
        }
    }
}
