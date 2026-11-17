using System.Collections;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.EventSystems;

/// <summary>
/// Điều khiển Đạo cụ Gạt tàn & Điếu thuốc đang cháy (Ashtray & Smoldering Cigarette):
/// Tự động nạp sprite trong mọi môi trường (Editor và Standalone Build),
/// tạo gạt tàn pha lê bóng mờ, tàn thuốc đỏ rực lập lòe và làn khói bốc lên ma mị.
/// </summary>
public class AshtrayPropController : MonoBehaviour, IPointerClickHandler
{
    private Image ashtrayImage;
    private Image emberGlowImage;
    private RectTransform emberTransform;

    private class SmokeParticle
    {
        public RectTransform rect;
        public Image img;
        public float life;
        public float maxLife;
        public Vector2 velocity;
        public float swayPhase;
        public float initialScale;
    }

    private List<SmokeParticle> activeParticles = new List<SmokeParticle>();
    private Transform smokeContainer;
    private float nextSpawnTime;

    private static Sprite cachedSprite;

    private void Start()
    {
        BuildAshtrayHierarchy();
    }

    private void BuildAshtrayHierarchy()
    {
        Canvas canvas = GetComponentInParent<Canvas>();
        if (canvas == null) return;

        // Attach to Layer_2_DetectiveDesk if available
        Transform desk = GameObject.Find("Layer_2_DetectiveDesk")?.transform;
        if (desk != null && transform.parent != desk)
        {
            transform.SetParent(desk, false);
        }

        RectTransform rt = GetComponent<RectTransform>();
        if (rt == null) rt = gameObject.AddComponent<RectTransform>();

        // Place on desk neatly between folders (~0.71) and bankers lamp (~0.86)
        rt.anchorMin = new Vector2(0.74f, 0.14f);
        rt.anchorMax = new Vector2(0.85f, 0.58f);
        rt.anchoredPosition = Vector2.zero;
        rt.sizeDelta = Vector2.zero;
        rt.pivot = new Vector2(0.5f, 0.5f);

        // Ashtray sprite image
        ashtrayImage = gameObject.GetComponent<Image>();
        if (ashtrayImage == null) ashtrayImage = gameObject.AddComponent<Image>();
        ashtrayImage.preserveAspect = true;

        if (cachedSprite == null)
        {
            cachedSprite = LoadAshtraySprite();
        }

        if (cachedSprite != null)
        {
            ashtrayImage.sprite = cachedSprite;
            ashtrayImage.color = Color.white;
        }
        else
        {
            // Fallback: procedural dark crystal glass texture (NEVER WHITE!)
            Texture2D procTex = CreateProceduralAshtrayTexture();
            cachedSprite = Sprite.Create(procTex, new Rect(0, 0, procTex.width, procTex.height), new Vector2(0.5f, 0.5f));
            ashtrayImage.sprite = cachedSprite;
            ashtrayImage.color = Color.white;
        }

        // Ember Glow child
        GameObject emberGo = new GameObject("Cigarette_Ember_Glow", typeof(RectTransform), typeof(Image));
        emberTransform = emberGo.GetComponent<RectTransform>();
        emberTransform.SetParent(transform, false);
        emberTransform.anchorMin = new Vector2(0.44f, 0.54f);
        emberTransform.anchorMax = new Vector2(0.46f, 0.58f);
        emberTransform.sizeDelta = new Vector2(16f, 16f);

        emberGlowImage = emberGo.GetComponent<Image>();
        emberGlowImage.color = new Color(1f, 0.45f, 0.1f, 0.85f);

        // Container for smoke particles
        GameObject smokeGo = new GameObject("Smoke_Container", typeof(RectTransform));
        smokeContainer = smokeGo.transform;
        smokeContainer.SetParent(transform, false);
    }

    private Sprite LoadAshtraySprite()
    {
        string[] candidates = new string[]
        {
            Path.Combine(Application.streamingAssetsPath, "NoirUI", "ashtray_cigarette.png"),
            Path.Combine(Application.dataPath, "StreamingAssets", "NoirUI", "ashtray_cigarette.png"),
            Path.Combine(Application.dataPath, "Textures", "NoirUI", "ashtray_cigarette.png"),
            Path.Combine(Application.dataPath, "..", "Assets", "Textures", "NoirUI", "ashtray_cigarette.png")
        };

        foreach (string path in candidates)
        {
            if (File.Exists(path))
            {
                byte[] bytes = File.ReadAllBytes(path);
                Texture2D tex = new Texture2D(2, 2, TextureFormat.RGBA32, false);
                if (tex.LoadImage(bytes))
                {
                    return Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), new Vector2(0.5f, 0.5f));
                }
            }
        }
        return null;
    }

    private Texture2D CreateProceduralAshtrayTexture()
    {
        int w = 256, h = 256;
        Texture2D tex = new Texture2D(w, h, TextureFormat.RGBA32, false);
        Color[] cols = new Color[w * h];
        Vector2 center = new Vector2(w * 0.5f, h * 0.5f);
        float radius = w * 0.42f;

        for (int y = 0; y < h; y++)
        {
            for (int x = 0; x < w; x++)
            {
                float dist = Vector2.Distance(new Vector2(x, y), center);
                if (dist > radius)
                {
                    cols[y * w + x] = Color.clear;
                }
                else if (dist > radius - 16f)
                {
                    // Crystal glass rim
                    cols[y * w + x] = new Color(0.24f, 0.22f, 0.20f, 0.85f);
                }
                else
                {
                    // Dark ash bed
                    cols[y * w + x] = new Color(0.10f, 0.09f, 0.08f, 0.95f);
                }
            }
        }
        tex.SetPixels(cols);
        tex.Apply();
        return tex;
    }

    private void Update()
    {
        // 1. Pulsing Ember Glow
        if (emberGlowImage != null)
        {
            float pulse = 0.75f + 0.25f * Mathf.Sin(Time.time * 2.8f) + 0.1f * Mathf.PerlinNoise(Time.time * 3f, 0f);
            emberGlowImage.color = new Color(1f, 0.40f + 0.15f * pulse, 0.1f, pulse * 0.9f);
        }

        // 2. Spawn gentle smoke particles periodically
        if (Time.time >= nextSpawnTime)
        {
            SpawnSmokeParticle(isPuff: false);
            nextSpawnTime = Time.time + Random.Range(0.22f, 0.38f);
        }

        // 3. Update existing smoke particles
        for (int i = activeParticles.Count - 1; i >= 0; i--)
        {
            var p = activeParticles[i];
            p.life += Time.deltaTime;
            if (p.life >= p.maxLife)
            {
                Destroy(p.rect.gameObject);
                activeParticles.RemoveAt(i);
                continue;
            }

            float progress = p.life / p.maxLife;
            float sway = Mathf.Sin(Time.time * 2.5f + p.swayPhase) * 18f * Time.deltaTime;
            p.rect.anchoredPosition += new Vector2(sway + p.velocity.x * Time.deltaTime, p.velocity.y * Time.deltaTime);

            float currentScale = p.initialScale * Mathf.Lerp(1f, 2.8f, progress);
            p.rect.localScale = new Vector3(currentScale, currentScale, 1f);

            float alpha = progress < 0.25f ? (progress / 0.25f) * 0.45f : (1f - progress) * 0.45f;
            p.img.color = new Color(0.85f, 0.85f, 0.88f, alpha);
        }
    }

    private void SpawnSmokeParticle(bool isPuff)
    {
        if (smokeContainer == null || emberTransform == null) return;

        GameObject go = new GameObject("SmokeWisp", typeof(RectTransform), typeof(Image));
        RectTransform rt = go.GetComponent<RectTransform>();
        rt.SetParent(smokeContainer, false);
        rt.anchoredPosition = emberTransform.anchoredPosition + new Vector2(Random.Range(-3f, 3f), Random.Range(-2f, 2f));

        Image img = go.GetComponent<Image>();
        img.color = new Color(0.85f, 0.85f, 0.88f, 0.05f);

        float maxLife = isPuff ? Random.Range(1.8f, 2.5f) : Random.Range(2.4f, 3.6f);
        float speedY = isPuff ? Random.Range(35f, 55f) : Random.Range(22f, 34f);
        float speedX = Random.Range(-6f, 6f);

        SmokeParticle p = new SmokeParticle
        {
            rect = rt,
            img = img,
            life = 0f,
            maxLife = maxLife,
            velocity = new Vector2(speedX, speedY),
            swayPhase = Random.Range(0f, Mathf.PI * 2),
            initialScale = isPuff ? Random.Range(0.8f, 1.3f) : Random.Range(0.4f, 0.8f)
        };
        rt.sizeDelta = new Vector2(18f, 18f);
        activeParticles.Add(p);
    }

    public void OnPointerClick(PointerEventData eventData)
    {
        for (int i = 0; i < 4; i++)
        {
            SpawnSmokeParticle(isPuff: true);
        }
    }
}
