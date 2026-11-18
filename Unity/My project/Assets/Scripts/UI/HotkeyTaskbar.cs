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
    private SettingsModal settingsModal;
    private HelpTutorialModal helpModal;
    private TitleMenuModal titleMenuModal;
    private InGamePauseModal pauseModal;
    private PhotoLightboxModal lightboxModal;
    private GameObject pauseBtnGo;
    private GameObject settingsBtnGo;
    private GameObject briefingBtnGo;

    public static HotkeyTaskbar Instance { get; private set; }

    private void Awake()
    {
        Instance = this;
        if (chatUI == null) chatUI = FindAnyObjectByType<DetectiveChatUI>(FindObjectsInactive.Include);
        if (chatUI != null) chatUI.EnsureRegistered();
        lobby = CreateLobby();
        settingsModal = CreateSettingsModal();
        helpModal = CreateHelpModal();
        titleMenuModal = CreateTitleMenuModal();
        pauseModal = CreatePauseModal();
        lightboxModal = CreateLightboxModal();
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
        if (lobbyChipButton != null)
        {
            lobbyChipButton.onClick.AddListener(ToggleLobby);

            // Clone chip button for Pause & Settings
            try
            {
                // Pause button
                pauseBtnGo = Instantiate(lobbyChipButton.gameObject, lobbyChipButton.transform.parent);
                pauseBtnGo.name = "PauseChipButton";
                pauseBtnGo.transform.SetAsFirstSibling();
                Text pauseText = pauseBtnGo.GetComponentInChildren<Text>();
                if (pauseText != null) pauseText.text = "⏸️ Menu (ESC)";
                Button pauseBtn = pauseBtnGo.GetComponent<Button>();
                if (pauseBtn != null)
                {
                    pauseBtn.onClick.RemoveAllListeners();
                    pauseBtn.onClick.AddListener(TogglePause);
                }

                // Settings button
                settingsBtnGo = Instantiate(lobbyChipButton.gameObject, lobbyChipButton.transform.parent);
                settingsBtnGo.name = "SettingsChipButton";
                Text btnText = settingsBtnGo.GetComponentInChildren<Text>();
                if (btnText != null) btnText.text = "⚙️ Cài đặt (O)";
                Button btn = settingsBtnGo.GetComponent<Button>();
                if (btn != null)
                {
                    btn.onClick.RemoveAllListeners();
                    btn.onClick.AddListener(ToggleSettings);
                }

                // Briefing button (Case Intro & Initial Report)
                briefingBtnGo = Instantiate(lobbyChipButton.gameObject, lobbyChipButton.transform.parent);
                briefingBtnGo.name = "BriefingChipButton";
                Text bText = briefingBtnGo.GetComponentInChildren<Text>();
                if (bText != null) bText.text = "📁 Bàn giao án (B)";
                Button bBtn = briefingBtnGo.GetComponent<Button>();
                if (bBtn != null)
                {
                    bBtn.onClick.RemoveAllListeners();
                    bBtn.onClick.AddListener(ToggleBriefing);
                }
            }
            catch (System.Exception e)
            {
                Debug.LogWarning($"[HotkeyTaskbar] Could not clone taskbar buttons: {e.Message}");
            }
        }

        // Tự động liên kết click vào tập hồ sơ giấy Manila trên bàn
        try
        {
            GameObject manila = GameObject.Find("Manila_Dossier_Folder");
            if (manila != null)
            {
                Button mBtn = manila.GetComponent<Button>();
                if (mBtn == null) mBtn = manila.AddComponent<Button>();
                mBtn.onClick.RemoveAllListeners();
                mBtn.onClick.AddListener(() => CaseBriefingModal.Instance.Open());
            }
        }
        catch (System.Exception ex)
        {
            Debug.LogWarning($"[HotkeyTaskbar] Manila folder click bind warning: {ex.Message}");
        }
        RefreshStatus();

        // Show Main Title Menu at initial launch and hide taskbar visuals
        if (titleMenuModal != null)
        {
            titleMenuModal.Open();
            SetTaskbarVisuals(false);
        }
    }

    /// <summary>
    /// Shows or hides the bottom HUD taskbar visuals (chips, text, background)
    /// while keeping the HotkeyTaskbar GameObject active so the ESC input loop always runs.
    /// </summary>
    public void SetTaskbarVisuals(bool visible)
    {
        if (chatChipButton != null) chatChipButton.gameObject.SetActive(visible);
        if (lobbyChipButton != null) lobbyChipButton.gameObject.SetActive(visible);
        if (pauseBtnGo != null) pauseBtnGo.SetActive(visible);
        if (settingsBtnGo != null) settingsBtnGo.SetActive(visible);
        if (briefingBtnGo != null) briefingBtnGo.SetActive(visible);
        if (statusText != null) statusText.gameObject.SetActive(visible);

        Image bg = GetComponent<Image>();
        if (bg != null) bg.enabled = visible;
    }

    private void Update()
    {
        if (IsTypingInInputField()) return;

#if ENABLE_INPUT_SYSTEM
        Keyboard kb = Keyboard.current;
        if (kb == null) return;
        if (kb.tKey.wasPressedThisFrame) ToggleChat();
        if (kb.bKey.wasPressedThisFrame) ToggleBriefing();
        if (kb.lKey.wasPressedThisFrame) ToggleLobby();
        if (kb.oKey.wasPressedThisFrame) ToggleSettings();
        if (kb.hKey.wasPressedThisFrame || kb.f1Key.wasPressedThisFrame) ToggleHelp();
        if (kb.mKey.wasPressedThisFrame) ToggleTitleMenu();
        if (kb.nKey.wasPressedThisFrame) AudioManager.Instance?.PlayNextTrack();
        if (kb.escapeKey.wasPressedThisFrame) OnEscapePressed();
#else
        if (Input.GetKeyDown(KeyCode.T)) ToggleChat();
        if (Input.GetKeyDown(KeyCode.B)) ToggleBriefing();
        if (Input.GetKeyDown(KeyCode.L)) ToggleLobby();
        if (Input.GetKeyDown(KeyCode.O)) ToggleSettings();
        if (Input.GetKeyDown(KeyCode.H) || Input.GetKeyDown(KeyCode.F1)) ToggleHelp();
        if (Input.GetKeyDown(KeyCode.M)) ToggleTitleMenu();
        if (Input.GetKeyDown(KeyCode.N)) AudioManager.Instance?.PlayNextTrack();
        if (Input.GetKeyDown(KeyCode.Escape)) OnEscapePressed();
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

    private SettingsModal CreateSettingsModal()
    {
        Transform host = transform.parent != null ? transform.parent : transform;
        var go = new GameObject("Settings_Modal", typeof(RectTransform));
        go.layer = gameObject.layer;
        go.transform.SetParent(host, false);
        var rt = (RectTransform)go.transform;
        rt.anchorMin = Vector2.zero;
        rt.anchorMax = Vector2.one;
        rt.offsetMin = Vector2.zero;
        rt.offsetMax = Vector2.zero;

        SettingsModal modal = go.AddComponent<SettingsModal>();
        modal.Initialize(statusText != null ? statusText.font : null);
        return modal;
    }

    private HelpTutorialModal CreateHelpModal()
    {
        Transform host = transform.parent != null ? transform.parent : transform;
        var go = new GameObject("Help_Modal", typeof(RectTransform));
        go.layer = gameObject.layer;
        go.transform.SetParent(host, false);
        var rt = (RectTransform)go.transform;
        rt.anchorMin = Vector2.zero;
        rt.anchorMax = Vector2.one;
        rt.offsetMin = Vector2.zero;
        rt.offsetMax = Vector2.zero;

        HelpTutorialModal modal = go.AddComponent<HelpTutorialModal>();
        modal.Initialize(statusText != null ? statusText.font : null);
        return modal;
    }

    private TitleMenuModal CreateTitleMenuModal()
    {
        Transform host = transform.parent != null ? transform.parent : transform;
        var go = new GameObject("TitleMenu_Modal", typeof(RectTransform));
        go.layer = gameObject.layer;
        go.transform.SetParent(host, false);
        var rt = (RectTransform)go.transform;
        rt.anchorMin = Vector2.zero;
        rt.anchorMax = Vector2.one;
        rt.offsetMin = Vector2.zero;
        rt.offsetMax = Vector2.zero;

        TitleMenuModal modal = go.AddComponent<TitleMenuModal>();
        modal.Initialize(statusText != null ? statusText.font : null);
        return modal;
    }

    private PhotoLightboxModal CreateLightboxModal()
    {
        Transform host = transform.parent != null ? transform.parent : transform;
        var go = new GameObject("PhotoLightbox_Modal", typeof(RectTransform));
        go.layer = gameObject.layer;
        go.transform.SetParent(host, false);
        var rt = (RectTransform)go.transform;
        rt.anchorMin = Vector2.zero;
        rt.anchorMax = Vector2.one;
        rt.offsetMin = Vector2.zero;
        rt.offsetMax = Vector2.zero;

        PhotoLightboxModal modal = go.AddComponent<PhotoLightboxModal>();
        modal.Initialize(statusText != null ? statusText.font : null);
        return modal;
    }

    public void ToggleTitleMenu()
    {
        if (titleMenuModal == null) return;
        titleMenuModal.transform.SetAsLastSibling();
        titleMenuModal.Toggle();
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

    public void ToggleSettings()
    {
        if (settingsModal == null) return;
        settingsModal.transform.SetAsLastSibling();
        settingsModal.Toggle();
    }

    public void ToggleBriefing()
    {
        if (CaseBriefingModal.Instance == null) return;
        if (CaseBriefingModal.Instance.IsOpen)
            CaseBriefingModal.Instance.Close();
        else
            CaseBriefingModal.Instance.Open();
    }

    public void ToggleHelp()
    {
        if (helpModal == null) return;
        helpModal.transform.SetAsLastSibling();
        helpModal.Toggle();
    }

    private InGamePauseModal CreatePauseModal()
    {
        Transform host = transform.parent != null ? transform.parent : transform;
        var go = new GameObject("InGamePause_Modal", typeof(RectTransform));
        go.layer = gameObject.layer;
        go.transform.SetParent(host, false);
        var rt = (RectTransform)go.transform;
        rt.anchorMin = Vector2.zero;
        rt.anchorMax = Vector2.one;
        rt.offsetMin = Vector2.zero;
        rt.offsetMax = Vector2.zero;

        InGamePauseModal modal = go.AddComponent<InGamePauseModal>();
        modal.Initialize(statusText != null ? statusText.font : null);
        return modal;
    }

    public void TogglePause()
    {
        if (pauseModal == null) return;
        pauseModal.transform.SetAsLastSibling();
        pauseModal.Toggle();
    }

    private void OnEscapePressed()
    {
        // 1. If Title Menu is open:
        if (titleMenuModal != null && titleMenuModal.IsOpen)
        {
            if (titleMenuModal.IsInSubPanel)
            {
                titleMenuModal.SendMessage("ShowMainMenuButtons", SendMessageOptions.DontRequireReceiver);
            }
            return;
        }

        // 2. If GenerateCaseModal is open:
        if (GenerateCaseModal.Instance != null && GenerateCaseModal.Instance.IsOpen)
        {
            GenerateCaseModal.Instance.Close();
            return;
        }

        // 3. If any in-game modal or lightbox is open:
        bool anyOpen = (PhotoLightboxModal.Instance != null && PhotoLightboxModal.Instance.IsOpen) ||
                       (CaseBriefingModal.Instance != null && CaseBriefingModal.Instance.IsOpen) ||
                       (AccusationModal.Instance != null && AccusationModal.Instance.IsOpen) ||
                       (AutopsyReportModal.Instance != null && AutopsyReportModal.Instance.IsOpen) ||
                       (EvidenceDetailModal.Instance != null && EvidenceDetailModal.Instance.IsOpen) ||
                       (chatUI != null && chatUI.IsChatPanelOpen) ||
                       (lobby != null && lobby.IsOpen) ||
                       (settingsModal != null && settingsModal.IsOpen) ||
                       (helpModal != null && helpModal.IsOpen) ||
                       (pauseModal != null && pauseModal.IsOpen);

        if (anyOpen)
        {
            CloseAll();
        }
        else
        {
            TogglePause();
        }
    }

    private void CloseAll()
    {
        if (PhotoLightboxModal.Instance != null && PhotoLightboxModal.Instance.IsOpen) PhotoLightboxModal.Instance.Close();
        if (CaseBriefingModal.Instance != null && CaseBriefingModal.Instance.IsOpen) CaseBriefingModal.Instance.Close();
        if (AccusationModal.Instance != null && AccusationModal.Instance.IsOpen) AccusationModal.Instance.Close();
        if (AutopsyReportModal.Instance != null && AutopsyReportModal.Instance.IsOpen) AutopsyReportModal.Instance.Close();
        if (EvidenceDetailModal.Instance != null && EvidenceDetailModal.Instance.IsOpen) EvidenceDetailModal.Instance.Close();
        if (chatUI != null) chatUI.SetChatPanelOpen(false);
        if (lobby != null) lobby.Close();
        if (settingsModal != null) settingsModal.Close();
        if (helpModal != null) helpModal.Close();
        if (pauseModal != null) pauseModal.Close();
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
