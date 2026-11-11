using UnityEngine;
using UnityEngine.UI;
using UnityEngine.EventSystems;
using System.Collections;

public class BankersLampController : MonoBehaviour, IPointerClickHandler
{
    [Header("Lamp References")]
    [SerializeField] private RectTransform chainTransform;
    [SerializeField] private Image lampShadeImage;
    [SerializeField] private GameObject softLightObject;

    [Header("Lamp States")]
    public bool isLightOn = true;

    [Header("Pull Feel")]
    [Tooltip("Pull distance as a fraction of the chain height. Keep below the hidden chain length behind the shade (~0.27) so no gap appears.")]
    [SerializeField, Range(0.05f, 0.27f)] private float pullFraction = 0.2f;

    private Vector2 originalChainPos;
    private Coroutine currentPullRoutine;

    // Image.color multiplies the whole sprite (shade, brass stem, base),
    // so "on" stays neutral and "off" only dims - never hue-shift it.
    private readonly Color lampColorOn = Color.white;
    private readonly Color lampColorOff = new Color(0.55f, 0.55f, 0.6f, 1f);

    private void Start()
    {
        if (chainTransform != null)
        {
            originalChainPos = chainTransform.anchoredPosition;
        }

        ApplyLightVisuals();
    }

    public void OnPointerClick(PointerEventData eventData)
    {
        if (eventData.button != PointerEventData.InputButton.Left) return;

        if (currentPullRoutine != null) StopCoroutine(currentPullRoutine);
        currentPullRoutine = StartCoroutine(PullChainRoutine());
    }

    private IEnumerator PullChainRoutine()
    {
        if (chainTransform == null) yield break;

        // 1. Pull chain downward smoothly
        float pullDuration = 0.09f;
        float pullDistance = chainTransform.rect.height * pullFraction;
        Vector2 targetPos = originalChainPos - new Vector2(0, pullDistance);

        float elapsed = 0f;
        while (elapsed < pullDuration)
        {
            elapsed += Time.deltaTime;
            chainTransform.anchoredPosition = Vector2.Lerp(originalChainPos, targetPos, elapsed / pullDuration);
            yield return null;
        }

        // 2. Toggle State at bottom of pull
        isLightOn = !isLightOn;

        // 3. Vintage bulb flicker effect on turn-on
        yield return StartCoroutine(FlickerRoutine());

        // 4. Spring chain back up with subtle bounce
        float returnDuration = 0.20f;
        elapsed = 0f;
        while (elapsed < returnDuration)
        {
            elapsed += Time.deltaTime;
            float t = elapsed / returnDuration;
            // Elastic spring bounce
            float bounce = 1f - Mathf.Exp(-7f * t) * Mathf.Cos(14f * t);
            chainTransform.anchoredPosition = Vector2.Lerp(targetPos, originalChainPos, bounce);
            yield return null;
        }

        chainTransform.anchoredPosition = originalChainPos;
        currentPullRoutine = null;
    }

    private IEnumerator FlickerRoutine()
    {
        if (isLightOn)
        {
            // Vintage spark flicker before full ignition
            SetVisualState(false);
            yield return new WaitForSeconds(0.035f);
            SetVisualState(true);
            yield return new WaitForSeconds(0.025f);
            SetVisualState(false);
            yield return new WaitForSeconds(0.035f);
            SetVisualState(true);
        }
        else
        {
            SetVisualState(false);
        }
    }

    private void SetVisualState(bool state)
    {
        if (softLightObject != null)
        {
            softLightObject.SetActive(state);
        }

        if (lampShadeImage != null)
        {
            lampShadeImage.color = state ? lampColorOn : lampColorOff;
        }
    }

    private void ApplyLightVisuals()
    {
        SetVisualState(isLightOn);
    }
}

