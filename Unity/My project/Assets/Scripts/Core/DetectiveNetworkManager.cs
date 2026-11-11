using UnityEngine;
using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Net.WebSockets;
using System.Collections.Concurrent;

[Serializable]
public class CardState
{
    public string card_id;
    public float x;
    public float y;
}

/// <summary>Wire format shared with detective-backend/rooms.py (JsonUtility-friendly).</summary>
[Serializable]
public class NetworkSyncMessage
{
    public string type;
    public string card_id;
    public float x;
    public float y;
    public string sender;
    public string text;
    public string case_id;
    public string you;
    public string[] players;
    public CardState[] cards;
}

public enum RoomConnectionState
{
    Offline,
    Connecting,
    Connected,
    RoomFull
}

public class DetectiveNetworkManager : MonoBehaviour
{
    public static DetectiveNetworkManager Instance { get; private set; }

    public const string MsgCardMoved = "CARD_MOVED";
    public const string MsgCaseLoaded = "CASE_LOADED";
    public const string MsgChat = "CHAT_MESSAGE";
    private const string MsgRoomState = "ROOM_STATE";
    private const string MsgRoomFull = "ROOM_FULL";
    private const string MsgPlayerJoined = "PLAYER_JOINED";
    private const string MsgPlayerLeft = "PLAYER_LEFT";
    private const int ReceiveChunkBytes = 8192;

    /// <summary>Push-to-talk audio from a peer (sender name, PCM16 mono 16 kHz). Main thread.</summary>
    public static event Action<string, byte[]> OnVoiceFrame;

    /// <summary>Fired on the main thread whenever connection state or the player list changes.</summary>
    public static event Action OnRoomChanged;

    public string roomId { get; private set; }
    public string playerName { get; private set; }
    public RoomConnectionState State { get; private set; } = RoomConnectionState.Offline;
    public IReadOnlyList<string> Players => players;
    /// <summary>Case the room is currently investigating (null until someone announces one).</summary>
    public string RoomCaseId { get; private set; }

    public bool IsConnected => State == RoomConnectionState.Connected && clientWs != null && clientWs.State == WebSocketState.Open;

    private readonly List<string> players = new List<string>();
    private readonly ConcurrentQueue<Action> mainThreadActions = new ConcurrentQueue<Action>();
    private ClientWebSocket clientWs;
    private CancellationTokenSource cts;
    private readonly SemaphoreSlim sendLock = new SemaphoreSlim(1, 1);

    private void Awake()
    {
        if (Instance == null)
        {
            Instance = this;
            DontDestroyOnLoad(gameObject);
            // Co-op must keep processing room traffic (and voice) while alt-tabbed.
            Application.runInBackground = true;
            if (GetComponent<VoiceChatController>() == null) gameObject.AddComponent<VoiceChatController>();
        }
        else
        {
            Destroy(gameObject);
        }
    }

    private void Start()
    {
        ConnectWithSavedConfig();
    }

    private void OnEnable()
    {
        DraggableCard.OnCardMoved += HandleLocalCardMoved;
    }

    private void OnDisable()
    {
        DraggableCard.OnCardMoved -= HandleLocalCardMoved;
        Disconnect();
    }

    private void Update()
    {
        while (mainThreadActions.TryDequeue(out Action action))
        {
            action?.Invoke();
        }
    }

    // ------------------------------------------------------------------
    // Connection lifecycle
    // ------------------------------------------------------------------

    public void ConnectWithSavedConfig()
    {
        ConnectToRoom(ServerConfig.RoomId, ServerConfig.PlayerName);
    }

    public async void ConnectToRoom(string room, string requestedName)
    {
        Disconnect();

        roomId = room;
        playerName = requestedName;
        RoomCaseId = null;
        players.Clear();
        SetState(RoomConnectionState.Connecting);

        var localCts = new CancellationTokenSource();
        var localWs = new ClientWebSocket();
        cts = localCts;
        clientWs = localWs;

        string url = $"{ServerConfig.WsRoomsUrl}/{Uri.EscapeDataString(room)}?name={Uri.EscapeDataString(requestedName)}";
        Debug.Log($"[DetectiveNetwork] Connecting to {url}...");

        try
        {
            await localWs.ConnectAsync(new Uri(url), localCts.Token);
            if (localWs != clientWs) return; // superseded by a newer connect
            SetState(RoomConnectionState.Connected);
            _ = ReceiveLoop(localWs, localCts.Token);
        }
        catch (Exception ex)
        {
            if (localWs != clientWs) return;
            Debug.LogWarning($"[DetectiveNetwork] Connection failed: {ex.Message}. Running in local mode.");
            SetState(RoomConnectionState.Offline);
        }
    }

    /// <summary>Detach the current socket synchronously, then close it in the background.</summary>
    public void Disconnect()
    {
        ClientWebSocket oldWs = clientWs;
        CancellationTokenSource oldCts = cts;
        clientWs = null;
        cts = null;

        if (State != RoomConnectionState.RoomFull) SetState(RoomConnectionState.Offline);
        players.Clear();

        oldCts?.Cancel();
        if (oldWs != null) _ = CloseQuietly(oldWs, oldCts);
    }

    private static async Task CloseQuietly(ClientWebSocket ws, CancellationTokenSource tokenSource)
    {
        try
        {
            if (ws.State == WebSocketState.Open)
            {
                await ws.CloseAsync(WebSocketCloseStatus.NormalClosure, "Closing", CancellationToken.None);
            }
        }
        catch (Exception) { /* socket already gone - nothing to clean up */ }
        finally
        {
            ws.Dispose();
            tokenSource?.Dispose();
        }
    }

    // ------------------------------------------------------------------
    // Outgoing
    // ------------------------------------------------------------------

    private void HandleLocalCardMoved(string cardId, Vector2 pos)
    {
        SendJson(new NetworkSyncMessage { type = MsgCardMoved, card_id = cardId, x = pos.x, y = pos.y });
    }

    public void SendChatMessage(string messageText)
    {
        SendJson(new NetworkSyncMessage { type = MsgChat, text = messageText });
    }

    /// <summary>Tell the room that everyone should switch to this case.</summary>
    public void AnnounceCaseLoaded(string caseId)
    {
        if (!IsConnected || string.IsNullOrEmpty(caseId) || caseId == RoomCaseId) return;
        RoomCaseId = caseId;
        SendJson(new NetworkSyncMessage { type = MsgCaseLoaded, case_id = caseId });
    }

    private void SendJson(NetworkSyncMessage msg)
    {
        Send(Encoding.UTF8.GetBytes(JsonUtility.ToJson(msg)), WebSocketMessageType.Text);
    }

    /// <summary>Send one push-to-talk frame (raw PCM16 mono 16 kHz).</summary>
    public void SendVoiceFrame(byte[] pcm16)
    {
        if (pcm16 != null && pcm16.Length > 0) Send(pcm16, WebSocketMessageType.Binary);
    }

    private async void Send(byte[] bytes, WebSocketMessageType kind)
    {
        ClientWebSocket ws = clientWs;
        CancellationTokenSource tokenSource = cts;
        if (!IsConnected || ws == null || tokenSource == null) return;

        // ClientWebSocket allows only one outstanding send at a time.
        await sendLock.WaitAsync();
        try
        {
            await ws.SendAsync(new ArraySegment<byte>(bytes), kind, true, tokenSource.Token);
        }
        catch (Exception ex)
        {
            Debug.LogWarning($"[DetectiveNetwork] Send error: {ex.Message}");
        }
        finally
        {
            sendLock.Release();
        }
    }

    // ------------------------------------------------------------------
    // Incoming
    // ------------------------------------------------------------------

    private async Task ReceiveLoop(ClientWebSocket ws, CancellationToken token)
    {
        byte[] buffer = new byte[ReceiveChunkBytes];
        using (var message = new MemoryStream())
        {
            while (!token.IsCancellationRequested && ws.State == WebSocketState.Open)
            {
                try
                {
                    WebSocketReceiveResult result = await ws.ReceiveAsync(new ArraySegment<byte>(buffer), token);
                    if (result.MessageType == WebSocketMessageType.Close) break;

                    message.Write(buffer, 0, result.Count);
                    if (!result.EndOfMessage) continue; // large frames (ROOM_STATE) arrive in pieces

                    if (result.MessageType == WebSocketMessageType.Binary)
                    {
                        HandleVoiceFrame(message.ToArray());
                        message.SetLength(0);
                        continue;
                    }

                    string json = Encoding.UTF8.GetString(message.GetBuffer(), 0, (int)message.Length);
                    message.SetLength(0);

                    NetworkSyncMessage msg = JsonUtility.FromJson<NetworkSyncMessage>(json);
                    if (msg != null) mainThreadActions.Enqueue(() => ProcessIncomingMessage(msg));
                }
                catch (Exception ex)
                {
                    if (!token.IsCancellationRequested)
                    {
                        Debug.LogWarning($"[DetectiveNetwork] Receive error: {ex.Message}");
                    }
                    break;
                }
            }
        }

        mainThreadActions.Enqueue(() =>
        {
            if (ws != clientWs) return; // an intentional reconnect already replaced this socket
            if (State != RoomConnectionState.RoomFull) Debug.LogWarning("[DetectiveNetwork] Disconnected from room.");
            clientWs = null;
            players.Clear();
            if (State != RoomConnectionState.RoomFull) SetState(RoomConnectionState.Offline);
        });
    }

    /// <summary>Server frame layout: [1 byte name length][name UTF-8][PCM16 bytes].</summary>
    private void HandleVoiceFrame(byte[] frame)
    {
        if (frame.Length < 2) return;
        int nameLength = frame[0];
        int pcmOffset = 1 + nameLength;
        int pcmLength = frame.Length - pcmOffset;
        if (pcmLength <= 0 || pcmLength % 2 != 0) return;

        string sender = Encoding.UTF8.GetString(frame, 1, nameLength);
        byte[] pcm = new byte[pcmLength];
        Buffer.BlockCopy(frame, pcmOffset, pcm, 0, pcmLength);
        mainThreadActions.Enqueue(() => OnVoiceFrame?.Invoke(sender, pcm));
    }

    private void ProcessIncomingMessage(NetworkSyncMessage msg)
    {
        switch (msg.type)
        {
            case MsgRoomState:
                playerName = string.IsNullOrEmpty(msg.you) ? playerName : msg.you;
                SetPlayers(msg.players);
                RoomCaseId = string.IsNullOrEmpty(msg.case_id) ? null : msg.case_id;
                ApplyRoomState(msg);
                ChatSystem($"Đã vào phòng {roomId} với tên '{playerName}' ({players.Count}/{ServerConfig.MaxPlayersPerRoom}).");
                break;

            case MsgRoomFull:
                SetState(RoomConnectionState.RoomFull);
                ChatSystem($"Phòng {roomId} đã đủ {ServerConfig.MaxPlayersPerRoom} người.");
                break;

            case MsgPlayerJoined:
                SetPlayers(msg.players);
                ChatSystem($"{msg.sender} đã vào phòng.");
                break;

            case MsgPlayerLeft:
                SetPlayers(msg.players);
                ChatSystem($"{msg.sender} đã rời phòng.");
                break;

            case MsgCaseLoaded:
                RoomCaseId = msg.case_id;
                ChatSystem($"{msg.sender} đã mở vụ án {msg.case_id}.");
                GameController.Instance?.LoadCaseFromRoom(msg.case_id, null);
                break;

            case MsgCardMoved:
                CorkboardManager.Instance?.MoveCard(msg.card_id, new Vector2(msg.x, msg.y));
                break;

            case MsgChat:
                DetectiveChatUI.Instance?.AddMessage(msg.sender, msg.text);
                break;

            default:
                // Other types (e.g. voice signalling) are handled by their own components.
                OnRawMessage?.Invoke(msg);
                break;
        }
    }

    /// <summary>Messages this manager does not handle itself.</summary>
    public static event Action<NetworkSyncMessage> OnRawMessage;

    private void ApplyRoomState(NetworkSyncMessage state)
    {
        GameController game = GameController.Instance;
        if (game == null) return;

        if (RoomCaseId == null)
        {
            // Empty room: we host the investigation - publish whatever we already have open.
            if (game.isCaseLoaded) AnnounceCaseLoaded(game.currentCaseId);
            return;
        }

        game.LoadCaseFromRoom(RoomCaseId, () => ApplyCards(state.cards));
    }

    private static void ApplyCards(CardState[] cards)
    {
        if (cards == null || CorkboardManager.Instance == null) return;
        foreach (CardState card in cards)
        {
            CorkboardManager.Instance.MoveCard(card.card_id, new Vector2(card.x, card.y));
        }
    }

    private void SetPlayers(string[] names)
    {
        players.Clear();
        if (names != null) players.AddRange(names);
        OnRoomChanged?.Invoke();
    }

    private void SetState(RoomConnectionState newState)
    {
        State = newState;
        OnRoomChanged?.Invoke();
    }

    private static void ChatSystem(string text)
    {
        DetectiveChatUI.Instance?.AddMessage("HỆ THỐNG", text);
    }
}
