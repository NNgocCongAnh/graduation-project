using UnityEngine;

#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

public class DetectiveRoomParallax : MonoBehaviour
{
    [Header("Parallax Layers (Far to Near)")]
    [SerializeField] private RectTransform wallLayer;
    [SerializeField] private RectTransform corkboardLayer;
    [SerializeField] private RectTransform deskLayer;
    [SerializeField] private RectTransform lightConeLayer;

    [Header("Parallax Multipliers")]
    [SerializeField] private float wallFactor = 6f;
    [SerializeField] private float corkboardFactor = 15f;
    [SerializeField] private float deskFactor = 32f;
    [SerializeField] private float lightFactor = 20f;
    [SerializeField] private float smoothSpeed = 6f;

    private Vector2 wallOrigin;
    private Vector2 corkboardOrigin;
    private Vector2 deskOrigin;
    private Vector2 lightOrigin;

    private void Start()
    {
        if (wallLayer != null) wallOrigin = wallLayer.anchoredPosition;
        if (corkboardLayer != null) corkboardOrigin = corkboardLayer.anchoredPosition;
        if (deskLayer != null) deskOrigin = deskLayer.anchoredPosition;
        if (lightConeLayer != null) lightOrigin = lightConeLayer.anchoredPosition;
    }

    private void Update()
    {
        // Calculate normalized mouse offset from screen center (-0.5 to 0.5)
        Vector2 mousePos = Vector2.zero;
#if ENABLE_INPUT_SYSTEM
        if (Mouse.current != null)
        {
            mousePos = Mouse.current.position.ReadValue();
        }
#else
        mousePos = Input.mousePosition;
#endif
        float normX = (mousePos.x / Screen.width) - 0.5f;
        float normY = (mousePos.y / Screen.height) - 0.5f;
        Vector2 offset = new Vector2(normX, normY);

        // Smoothly interpolate layers for depth parallax
        if (wallLayer != null)
        {
            Vector2 target = wallOrigin + (offset * wallFactor);
            wallLayer.anchoredPosition = Vector2.Lerp(wallLayer.anchoredPosition, target, Time.deltaTime * smoothSpeed);
        }

        if (corkboardLayer != null)
        {
            Vector2 target = corkboardOrigin + (offset * corkboardFactor);
            corkboardLayer.anchoredPosition = Vector2.Lerp(corkboardLayer.anchoredPosition, target, Time.deltaTime * smoothSpeed);
        }

        if (deskLayer != null)
        {
            Vector2 target = deskOrigin + (offset * deskFactor);
            deskLayer.anchoredPosition = Vector2.Lerp(deskLayer.anchoredPosition, target, Time.deltaTime * smoothSpeed);
        }

        if (lightConeLayer != null)
        {
            Vector2 target = lightOrigin + (offset * lightFactor);
            lightConeLayer.anchoredPosition = Vector2.Lerp(lightConeLayer.anchoredPosition, target, Time.deltaTime * smoothSpeed);
        }
    }
}

