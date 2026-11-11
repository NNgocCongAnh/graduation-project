using System.Collections.Generic;
using System.Linq;
using System.Net.NetworkInformation;
using System.Net.Sockets;
using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// "Phòng LAN" dialog: player name, host IP, room code, LAN host discovery.
/// Builds its own UGUI hierarchy on first open so the scene only needs this
/// component (HotkeyTaskbar adds it at runtime).
/// </summary>
public class LanLobbyModal : MonoBehaviour
{
    private const float DiscoverySeconds = 1.5f;
    private const int MaxListedHosts = 4;

    private static readonly Color PanelColor = new Color(0.09f, 0.08f, 0.07f, 0.98f);
    private static readonly Color FieldColor = new Color(0.16f, 0.15f, 0.14f, 1f);
    private static readonly Color TextColor = new Color(0.92f, 0.88f, 0.80f);
    private static readonly Color MutedColor = new Color(0.62f, 0.60f, 0.56f);
    private static readonly Color PrimaryColor = new Color(0.12f, 0.48f, 0.32f);
    private static readonly Color SecondaryColor = new Color(0.24f, 0.24f, 0.27f);

    private Font font;
    private RectTransform root;
    private InputField nameField;
    private InputField hostField;
    private InputField roomField;
    private Text statusText;
    private Transform hostListContainer;
    private Button discoverButton;
    private bool isDiscovering;

    public bool IsOpen => root != null && root.gameObject.activeSelf;

    public void Initialize(Font uiFont)
    {
        font = uiFont;
    }

    private void OnEnable()
    {
        DetectiveNetworkManager.OnRoomChanged += RefreshStatus;
    }

    private void OnDisable()
    {
        DetectiveNetworkManager.OnRoomChanged -= RefreshStatus;
    }

    public void Toggle()
    {
        if (IsOpen) Close();
        else Open();
    }

    public void Open()
    {
        if (root == null) BuildUI();
        nameField.text = ServerConfig.PlayerName;
        hostField.text = ServerConfig.Host;
        roomField.text = ServerConfig.RoomId;
        transform.SetAsLastSibling(); // draw above corkboard, desk props and modals
        root.gameObject.SetActive(true);
        RefreshStatus();
    }

    public void Close()
    {
        if (root != null) root.gameObject.SetActive(false);
    }

    // ------------------------------------------------------------------
    // Actions
    // ------------------------------------------------------------------

    private void OnConnectClicked()
    {
        ServerConfig.Save(hostField.text, nameField.text, roomField.text);
        Reconnect();
    }

    private void OnHostLocallyClicked()
    {
        hostField.text = "localhost";
        OnConnectClicked();
    }

    private void Reconnect()
    {
        if (DetectiveNetworkManager.Instance == null)
        {
            SetStatus("Không tìm thấy DetectiveNetworkManager trong scene.", true);
            return;
        }
        SetStatus($"Đang kết nối {ServerConfig.HostWithPort} / phòng {ServerConfig.RoomId}...", false);
        DetectiveNetworkManager.Instance.ConnectWithSavedConfig();
    }

    private void OnDiscoverClicked()
    {
        if (isDiscovering) return;
        isDiscovering = true;
        discoverButton.interactable = false;
        SetStatus("Đang tìm máy chủ trong mạng LAN...", false);
        StartCoroutine(LanDiscoveryClient.Discover(DiscoverySeconds, ShowHosts));
    }

    private void ShowHosts(List<LanDiscoveryClient.FoundHost> hosts)
    {
        isDiscovering = false;
        discoverButton.interactable = true;

        foreach (Transform child in hostListContainer) Destroy(child.gameObject);

        if (hosts.Count == 0)
        {
            SetStatus("Không thấy máy chủ nào. Kiểm tra cùng mạng Wi-Fi/LAN và tường lửa (UDP 47777, TCP 8000).", true);
            return;
        }

        SetStatus($"Tìm thấy {hosts.Count} máy chủ. Chọn một máy rồi bấm KẾT NỐI.", false);
        for (int i = 0; i < hosts.Count && i < MaxListedHosts; i++)
        {
            LanDiscoveryClient.FoundHost host = hosts[i];
            Button pick = CreateButton(hostListContainer, $"{host.HostName}  ·  {host.Address}", SecondaryColor, 0);
            pick.onClick.AddListener(() => hostField.text = host.Address);
        }
    }

    private void RefreshStatus()
    {
        if (statusText == null) return;
        DetectiveNetworkManager net = DetectiveNetworkManager.Instance;
        if (net == null) return;

        switch (net.State)
        {
            case RoomConnectionState.Connected:
                SetStatus($"Đã kết nối phòng {net.roomId} ({net.Players.Count}/{ServerConfig.MaxPlayersPerRoom}): {string.Join(", ", net.Players)}", false);
                break;
            case RoomConnectionState.RoomFull:
                SetStatus($"Phòng {net.roomId} đã đủ {ServerConfig.MaxPlayersPerRoom} người. Hãy dùng mã phòng khác.", true);
                break;
            case RoomConnectionState.Connecting:
                SetStatus($"Đang kết nối {ServerConfig.HostWithPort}...", false);
                break;
            default:
                SetStatus($"Chưa kết nối được {ServerConfig.HostWithPort}. Máy chủ đã chạy backend chưa?", true);
                break;
        }
    }

    private void SetStatus(string text, bool isWarning)
    {
        if (statusText == null) return;
        statusText.text = text;
        statusText.color = isWarning ? new Color(0.95f, 0.55f, 0.45f) : new Color(0.55f, 0.88f, 0.62f);
    }

    // ------------------------------------------------------------------
    // UI construction
    // ------------------------------------------------------------------

    private void BuildUI()
    {
        root = NewRect("Lan_Lobby_Modal", transform);
        Stretch(root);
        Image backdrop = root.gameObject.AddComponent<Image>();
        backdrop.color = new Color(0, 0, 0, 0.6f);

        RectTransform panel = NewRect("Panel", root);
        panel.anchorMin = panel.anchorMax = new Vector2(0.5f, 0.5f);
        panel.sizeDelta = new Vector2(580, 500);
        panel.gameObject.AddComponent<Image>().color = PanelColor;
        VerticalLayoutGroup layout = panel.gameObject.AddComponent<VerticalLayoutGroup>();
        layout.padding = new RectOffset(24, 24, 20, 20);
        layout.spacing = 8;
        layout.childControlWidth = true;
        layout.childControlHeight = true;
        layout.childForceExpandWidth = true;
        layout.childForceExpandHeight = false;

        CreateLabel(panel, "PHÒNG CHƠI LAN", 20, TextColor, FontStyle.Bold, 30);
        CreateLabel(panel, $"Tối đa {ServerConfig.MaxPlayersPerRoom} thám tử. Một máy chạy backend làm máy chủ, các máy khác nhập IP của máy đó.", 13, MutedColor, FontStyle.Normal, 36);

        CreateLabel(panel, $"IP của máy này (đọc cho bạn chơi nếu bạn làm máy chủ): {DescribeLocalIPv4()}", 13, TextColor, FontStyle.Normal, 20);

        nameField = CreateField(panel, "Tên thám tử", "VD: Hiếu");
        hostField = CreateField(panel, "Máy chủ (IP hoặc IP:cổng)", "VD: 192.168.1.20");
        roomField = CreateField(panel, "Mã phòng", "VD: PHONG-1");

        RectTransform hostList = NewRect("Found_Hosts", panel);
        VerticalLayoutGroup listLayout = hostList.gameObject.AddComponent<VerticalLayoutGroup>();
        listLayout.spacing = 4;
        listLayout.childControlWidth = true;
        listLayout.childControlHeight = true;
        listLayout.childForceExpandHeight = false;
        hostListContainer = hostList;

        statusText = CreateLabel(panel, "", 13, MutedColor, FontStyle.Italic, 36);
        CreateLabel(panel, "Voice: giữ V để nói (nên đeo tai nghe). Muốn dùng Discord thì cứ gọi Discord và đơn giản là không giữ V.", 12, MutedColor, FontStyle.Normal, 30);

        RectTransform row = NewRect("Buttons", panel);
        row.gameObject.AddComponent<LayoutElement>().preferredHeight = 38;
        HorizontalLayoutGroup rowLayout = row.gameObject.AddComponent<HorizontalLayoutGroup>();
        rowLayout.spacing = 8;
        rowLayout.childControlWidth = true;
        rowLayout.childControlHeight = true;
        rowLayout.childForceExpandWidth = true;

        discoverButton = CreateButton(row, "TÌM MÁY CHỦ", SecondaryColor, 38);
        discoverButton.onClick.AddListener(OnDiscoverClicked);
        CreateButton(row, "TỰ LÀM MÁY CHỦ", SecondaryColor, 38).onClick.AddListener(OnHostLocallyClicked);
        CreateButton(row, "KẾT NỐI", PrimaryColor, 38).onClick.AddListener(OnConnectClicked);
        CreateButton(row, "ĐÓNG", new Color(0.45f, 0.14f, 0.14f), 38).onClick.AddListener(Close);
    }

    /// <summary>Physical Wi-Fi/Ethernet IPv4 addresses (virtual adapters listed last).</summary>
    private static string DescribeLocalIPv4()
    {
        try
        {
            var addresses = NetworkInterface.GetAllNetworkInterfaces()
                .Where(n => n.OperationalStatus == OperationalStatus.Up
                    && (n.NetworkInterfaceType == NetworkInterfaceType.Ethernet || n.NetworkInterfaceType == NetworkInterfaceType.Wireless80211))
                .OrderBy(n => IsLikelyVirtual(n) ? 1 : 0)
                .SelectMany(n => n.GetIPProperties().UnicastAddresses)
                .Where(a => a.Address.AddressFamily == AddressFamily.InterNetwork)
                .Select(a => a.Address.ToString())
                .Distinct()
                .Take(3)
                .ToList();
            return addresses.Count > 0 ? string.Join("  /  ", addresses) : "không xác định";
        }
        catch (System.Exception)
        {
            return "không xác định";
        }
    }

    private static bool IsLikelyVirtual(NetworkInterface n)
    {
        string d = (n.Description + " " + n.Name).ToLowerInvariant();
        return d.Contains("virtual") || d.Contains("hyper-v") || d.Contains("vethernet") || d.Contains("wsl") || d.Contains("vmware") || d.Contains("virtualbox");
    }

    private InputField CreateField(Transform parent, string label, string placeholder)
    {
        CreateLabel(parent, label, 13, MutedColor, FontStyle.Bold, 18);

        RectTransform box = NewRect("Field_" + label, parent);
        box.gameObject.AddComponent<LayoutElement>().preferredHeight = 34;
        Image bg = box.gameObject.AddComponent<Image>();
        bg.color = FieldColor;

        Text text = CreateText(box, "Text", "", 15, TextColor, TextAnchor.MiddleLeft);
        Stretch(text.rectTransform, 10);
        text.supportRichText = false;

        Text hint = CreateText(box, "Placeholder", placeholder, 15, MutedColor, TextAnchor.MiddleLeft);
        hint.fontStyle = FontStyle.Italic;
        Stretch(hint.rectTransform, 10);

        InputField field = box.gameObject.AddComponent<InputField>();
        field.textComponent = text;
        field.placeholder = hint;
        field.targetGraphic = bg;
        field.lineType = InputField.LineType.SingleLine;
        field.characterLimit = 40;
        return field;
    }

    private Button CreateButton(Transform parent, string label, Color color, float height)
    {
        RectTransform rt = NewRect("Btn_" + label, parent);
        rt.gameObject.AddComponent<LayoutElement>().preferredHeight = height > 0 ? height : 30;
        Image img = rt.gameObject.AddComponent<Image>();
        img.color = color;
        Button button = rt.gameObject.AddComponent<Button>();
        button.targetGraphic = img;
        Text text = CreateText(rt, "Label", label, 13, Color.white, TextAnchor.MiddleCenter);
        text.fontStyle = FontStyle.Bold;
        Stretch(text.rectTransform, 4);
        return button;
    }

    private Text CreateLabel(Transform parent, string content, int size, Color color, FontStyle style, float height)
    {
        Text text = CreateText(parent, "Label", content, size, color, TextAnchor.MiddleLeft);
        text.fontStyle = style;
        text.horizontalOverflow = HorizontalWrapMode.Wrap;
        text.gameObject.AddComponent<LayoutElement>().preferredHeight = height;
        return text;
    }

    private Text CreateText(Transform parent, string name, string content, int size, Color color, TextAnchor anchor)
    {
        RectTransform rt = NewRect(name, parent);
        Text text = rt.gameObject.AddComponent<Text>();
        text.font = font != null ? font : Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
        text.text = content;
        text.fontSize = size;
        text.color = color;
        text.alignment = anchor;
        text.raycastTarget = false;
        return text;
    }

    private static RectTransform NewRect(string name, Transform parent)
    {
        var go = new GameObject(name, typeof(RectTransform));
        go.layer = parent.gameObject.layer;
        go.transform.SetParent(parent, false);
        return (RectTransform)go.transform;
    }

    private static void Stretch(RectTransform rt, float inset = 0)
    {
        rt.anchorMin = Vector2.zero;
        rt.anchorMax = Vector2.one;
        rt.offsetMin = new Vector2(inset, 0);
        rt.offsetMax = new Vector2(-inset, 0);
    }
}
