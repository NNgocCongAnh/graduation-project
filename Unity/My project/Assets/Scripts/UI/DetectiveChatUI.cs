using UnityEngine;
using UnityEngine.UI;
using System.Collections.Generic;

public class DetectiveChatUI : MonoBehaviour
{
    public static DetectiveChatUI Instance { get; private set; }

    [Header("UI References")]
    [SerializeField] private GameObject chatPanel;

    public bool IsChatPanelOpen => chatPanel != null && chatPanel.activeSelf;
    [SerializeField] private Text chatLogText;
    [SerializeField] private InputField chatInputField;
    [SerializeField] private Button sendButton;
    [SerializeField] private Button toggleButton;
    [SerializeField] private Text roomStatusText;

    private List<string> messageHistory = new List<string>();
    private const int MaxMessages = 12;

    private void Awake()
    {
        EnsureRegistered();
    }

    /// <summary>
    /// The chat panel starts inactive, so Awake() does not run until it is first opened.
    /// An always-active owner (HotkeyTaskbar) calls this at startup so network messages
    /// and hotkeys can reach the chat before the panel has ever been shown.
    /// </summary>
    public void EnsureRegistered()
    {
        if (Instance == null) Instance = this;
    }

    private void Start()
    {
        if (sendButton != null)
        {
            sendButton.onClick.AddListener(OnSendClicked);
        }

        if (toggleButton != null)
        {
            toggleButton.onClick.AddListener(ToggleChatPanel);
        }

        if (chatInputField != null)
        {
            chatInputField.onEndEdit.AddListener((val) =>
            {
#if ENABLE_INPUT_SYSTEM
                if (UnityEngine.InputSystem.Keyboard.current != null && UnityEngine.InputSystem.Keyboard.current.enterKey.wasPressedThisFrame)
                {
                    OnSendClicked();
                }
#endif
            });
        }

        UpdateRoomStatus();
        AddMessage("SYSTEM", "Radio Link established. Ready for transmission.");
    }

    public void ToggleChatPanel()
    {
        if (chatPanel != null)
        {
            SetChatPanelOpen(!chatPanel.activeSelf);
        }
    }

    public void SetChatPanelOpen(bool open)
    {
        if (chatPanel == null) return;
        chatPanel.SetActive(open);

        if (open && chatInputField != null)
        {
            chatInputField.ActivateInputField();
        }
    }

    public void OnSendClicked()
    {
        if (chatInputField == null) return;
        string text = chatInputField.text.Trim();
        if (string.IsNullOrEmpty(text)) return;

        if (DetectiveNetworkManager.Instance != null)
        {
            DetectiveNetworkManager.Instance.SendChatMessage(text);
        }

        string me = DetectiveNetworkManager.Instance != null && !string.IsNullOrEmpty(DetectiveNetworkManager.Instance.playerName)
            ? DetectiveNetworkManager.Instance.playerName
            : "Tôi";
        AddMessage(me, text);
        chatInputField.text = "";
        chatInputField.ActivateInputField();
    }

    public void AddMessage(string sender, string message)
    {
        string formatted = $"<color=#D4AF37>[{sender}]</color>: {message}";
        messageHistory.Add(formatted);
        if (messageHistory.Count > MaxMessages)
        {
            messageHistory.RemoveAt(0);
        }

        if (chatLogText != null)
        {
            chatLogText.text = string.Join("\n", messageHistory);
        }
    }

    public void UpdateRoomStatus()
    {
        if (roomStatusText != null && DetectiveNetworkManager.Instance != null)
        {
            roomStatusText.text = $"POLICE RADIO // ROOM: {DetectiveNetworkManager.Instance.roomId}";
        }
    }
}

