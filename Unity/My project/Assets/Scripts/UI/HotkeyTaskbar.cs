using UnityEngine;
using UnityEngine.UI;
using UnityEngine.EventSystems;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

/// <summary>
/// Slim Windows-style taskbar at the bottom of the room: hotkey hints on the left,
/// co-op status on the right. Owns the global hotkeys:
///   T = text chat, L = LAN lobby, Esc = close. (Hold V = voice, see VoiceChatController.)
/// </summary>
public class HotkeyTaskbar : MonoBehaviour
{
    [Header("References")]
    [SerializeField] private Text statusText;
    [SerializeField] private Button chatChipButton;
    [SerializeField] private Button lobbyChipButton;
    [Tooltip("Chat UI lives on a panel that starts inactive; reference it directly.")]
    [SerializeField] private DetectiveChatUI chatUI;

    private LanLobbyModal lobby;

    public static HotkeyTaskbar Instance { get; private set; }

    private void Awake()
    {
        Instance = this;
        if (chatUI == null) chatUI = FindAnyObjectByType<DetectiveChatUI>(FindObjectsInactive.Include);
        if (chatUI != null) chatUI.EnsureRegistered();
        lobby = CreateLobby();
    }

    private void OnEnable()
    {
        DetectiveNetworkManager.OnRoomChanged += RefreshStatus;
        ServerConfig.OnChanged += RefreshStatus;
        VoiceChatController.OnSpeakingChanged += RefreshStatus;
    }

    private void OnDisable()
    {
        DetectiveNetworkManager.OnRoomChanged -= RefreshStatus;
        ServerConfig.OnChanged -= RefreshStatus;
        VoiceChatController.OnSpeakingChanged -= RefreshStatus;
    }

    private void Start()
    {
        if (chatChipButton != null) chatChipButton.onClick.AddListener(ToggleChat);
        if (lobbyChipButton != null) lobbyChipButton.onClick.AddListener(ToggleLobby);
        RefreshStatus();
    }

    private void Update()
    {
        if (IsTypingInInputField()) return;

#if ENABLE_INPUT_SYSTEM
        Keyboard kb = Keyboard.current;
        if (kb == null) return;
        if (kb.tKey.wasPressedThisFrame) ToggleChat();
        if (kb.lKey.wasPressedThisFrame) ToggleLobby();
        if (kb.escapeKey.wasPressedThisFrame) CloseAll();
#else
        if (Input.GetKeyDown(KeyCode.T)) ToggleChat();
        if (Input.GetKeyDown(KeyCode.L)) ToggleLobby();
        if (Input.GetKeyDown(KeyCode.Escape)) CloseAll();
#endif
    }

    /// <summary>True while the player types in any InputField (hotkeys must not fire).</summary>
    public static bool IsTypingInInputField()
    {
        EventSystem es = EventSystem.current;
        if (es == null || es.currentSelectedGameObject == null) return false;
        InputField field = es.currentSelectedGameObject.GetComponent<InputField>();
        return field != null && field.isFocused;
    }

    private LanLobbyModal CreateLobby()
    {
        // Lives beside the taskbar so it can cover the whole 16:9 viewport.
        Transform host = transform.parent != null ? transform.parent : transform;
        var go = new GameObject("Lan_Lobby", typeof(RectTransform));
        go.layer = gameObject.layer;
        go.transform.SetParent(host, false);
        var rt = (RectTransform)go.transform;
        rt.anchorMin = Vector2.zero;
        rt.anchorMax = Vector2.one;
        rt.offsetMin = Vector2.zero;
        rt.offsetMax = Vector2.zero;

        LanLobbyModal modal = go.AddComponent<LanLobbyModal>();
        modal.Initialize(statusText != null ? statusText.font : null);
        return modal;
    }

    private void ToggleChat()
    {
        if (chatUI != null) chatUI.ToggleChatPanel();
    }

    private void ToggleLobby()
    {
        if (lobby == null) return;
        lobby.transform.SetAsLastSibling();
        lobby.Toggle();
    }

    private void CloseAll()
    {
        if (chatUI != null) chatUI.SetChatPanelOpen(false);
        if (lobby != null) lobby.Close();
    }

    private static string DescribeVoice()
    {
        VoiceChatController voice = VoiceChatController.Instance;
        if (voice == null) return "";

        string text = "";
        if (voice.IsTransmitting) text += "<color=#FF6B6B>◉ ĐANG NÓI</color>   ";
        if (voice.RemoteSpeakers.Count > 0) text += $"<color=#E3C76B>♪ {string.Join(", ", voice.RemoteSpeakers)}</color>   ";
        return text;
    }

    private void RefreshStatus()
    {
        if (statusText == null) return;

        DetectiveNetworkManager net = DetectiveNetworkManager.Instance;
        if (net == null)
        {
            statusText.text = "<color=#888888>○ CHƠI ĐƠN</color>";
            return;
        }

        string room = $"PHÒNG {net.roomId}";
        switch (net.State)
        {
            case RoomConnectionState.Connected:
                statusText.text = DescribeVoice() +
                    $"<color=#6BE38A>●</color> CO-OP {net.Players.Count}/{ServerConfig.MaxPlayersPerRoom} · {room} · {net.playerName}";
                break;
            case RoomConnectionState.Connecting:
                statusText.text = $"<color=#E3C76B>●</color> ĐANG KẾT NỐI · {ServerConfig.HostWithPort}";
                break;
            case RoomConnectionState.RoomFull:
                statusText.text = $"<color=#E36B6B>●</color> {room} ĐÃ ĐẦY · nhấn L";
                break;
            default:
                statusText.text = $"<color=#E36B6B>●</color> OFFLINE · nhấn L để vào phòng LAN";
                break;
        }
    }
}
