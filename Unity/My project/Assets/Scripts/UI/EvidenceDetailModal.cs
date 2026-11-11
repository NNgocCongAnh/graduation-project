using UnityEngine;
using UnityEngine.UI;

public class EvidenceDetailModal : MonoBehaviour
{
    public static EvidenceDetailModal Instance { get; private set; }

    [Header("UI Component Bindings")]
    [SerializeField] private GameObject modalRoot;
    [SerializeField] private Text titleText;
    [SerializeField] private Text categoryBadgeText;
    [SerializeField] private Image badgeBackground;
    [SerializeField] private RawImage photoImage;
    [SerializeField] private Text detailsText;
    [SerializeField] private Button closeButton;

    private void Awake()
    {
        if (Instance == null)
        {
            Instance = this;
        }
        else
        {
            Destroy(gameObject);
            return;
        }

        if (closeButton != null)
        {
            closeButton.onClick.AddListener(Close);
        }

        if (modalRoot != null)
        {
            modalRoot.SetActive(false);
        }
    }

    public void ShowSuspect(SuspectData suspect, Texture2D texture)
    {
        if (modalRoot == null) return;
        modalRoot.SetActive(true);
        transform.SetAsLastSibling();

        if (titleText != null) titleText.text = suspect.name;
        if (categoryBadgeText != null) categoryBadgeText.text = "NGHI PHẠM / SUSPECT";
        if (badgeBackground != null) badgeBackground.color = new Color(0.7f, 0.15f, 0.15f);

        if (photoImage != null)
        {
            photoImage.texture = texture;
            photoImage.color = texture != null ? Color.white : new Color(0.3f, 0.3f, 0.3f);
        }

        if (detailsText != null)
        {
            detailsText.text = 
                $"<b>Mã định danh:</b> {suspect.id}\n" +
                $"<b>Tuổi:</b> {suspect.age} | <b>Nghề nghiệp:</b> {suspect.occupation}\n\n" +
                $"<b>Động cơ khả nghi:</b>\n{suspect.motive}\n\n" +
                $"<b>Chứng cứ ngoại phạm (Alibi):</b>\n{suspect.alibi_statement}\n" +
                $"<i>Thời gian khai báo: {suspect.alibi_start} - {suspect.alibi_end}</i>";
        }
    }

    public void ShowEvidence(EvidenceData evidence, Texture2D texture)
    {
        if (modalRoot == null) return;
        modalRoot.SetActive(true);
        transform.SetAsLastSibling();

        if (titleText != null) titleText.text = evidence.title;
        if (categoryBadgeText != null) categoryBadgeText.text = "CHỨNG CỨ / EVIDENCE";
        if (badgeBackground != null) badgeBackground.color = new Color(0.2f, 0.45f, 0.7f);

        if (photoImage != null)
        {
            photoImage.texture = texture;
            photoImage.color = texture != null ? Color.white : new Color(0.3f, 0.3f, 0.3f);
        }

        if (detailsText != null)
        {
            detailsText.text = 
                $"<b>Mã chứng cứ:</b> {evidence.id}\n" +
                $"<b>Địa điểm thu thập:</b> {evidence.location}\n\n" +
                $"<b>Mô tả vật chứng:</b>\n{evidence.description}\n\n" +
                $"<b>Liên hệ nghi phạm:</b> {(string.IsNullOrEmpty(evidence.linked_suspect_id) ? "Chưa rõ" : evidence.linked_suspect_id)}";
        }
    }

    public void Close()
    {
        if (modalRoot != null)
        {
            modalRoot.SetActive(false);
        }
    }
}

