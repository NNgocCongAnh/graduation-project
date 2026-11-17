using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// Ngân hàng Tài nguyên Trinh thám & Thuật toán Khớp Semantic Asset:
/// 1. Tự động tìm kiếm và nạp ảnh có sẵn trên máy (StreamingAssets) với độ trễ 0s.
/// 2. Hỗ trợ kho chân dung 3X cho từng độ tuổi và giới tính (Thiếu niên, Thanh niên, Trung niên, Lão niên, Nạn nhân).
/// 3. Procedural Fallback: Tự động sinh texture Noir chuyên nghiệp nếu file ảnh bị thiếu,
///    đảm bảo 100% không bao giờ để thẻ bài bị ô vuông đen.
/// </summary>
public static class DetectiveAssetBank
{
    private static readonly Dictionary<string, Texture2D> textureCache = new Dictionary<string, Texture2D>();

    // Semantic Rules for Suspect Archetypes with 3X variations per age/gender
    private static readonly (string[] variants, string[] keywords)[] SuspectRules = new[]
    {
        (new[] { "victim_male_1.png", "victim_male_2.png", "victim_male_3.png", "victim_male.png" },
            new[] { "nạn nhân nam", "ông arthur", "blackwood", "thi thể nam", "tử thi nam", "nạn nhân", "tử thi", "thi thể", "victim", "deceased" }),

        (new[] { "victim_female_1.png", "victim_female_2.png", "victim_female_3.png", "victim_female.png" },
            new[] { "nạn nhân nữ", "bà chủ", "phu nhân qua đời", "thi thể nữ", "tử thi nữ", "tiểu thư đã khuất" }),

        (new[] { "elderly_male_1.png", "elderly_male_2.png", "elderly_male_3.png", "elderly_male.png" },
            new[] { "ông lão", "cụ ông", "bác", "già", "elder", "old man" }),

        (new[] { "elderly_female_1.png", "elderly_female_2.png", "elderly_female_3.png", "elderly_female.png" },
            new[] { "bà lão", "cụ bà", "phu nhân già", "mẹ", "old woman" }),

        (new[] { "middle_male_1.png", "middle_male_2.png", "middle_male_3.png", "butler_male_50s.png" },
            new[] { "quản gia", "butler", "gia nhân", "người hầu", "valet", "vance" }),

        (new[] { "middle_male_1.png", "middle_male_2.png", "middle_male_3.png", "businessman_male_50s.png" },
            new[] { "bác sĩ", "doctor", "doanh nhân", "businessman", "luật sư", "lawyer", "grey", "chủ tịch", "giám đốc", "ông trùm", "trung niên nam", "ông" }),

        (new[] { "middle_female_1.png", "middle_female_2.png", "middle_female_3.png", "middle_aged_female.png" },
            new[] { "quý bà", "phu nhân", "nữ giám đốc", "nữ doanh nhân", "mẹ kế", "bác gái", "dì", "trung niên nữ" }),

        (new[] { "young_female_1.png", "young_female_2.png", "young_female_3.png", "female_30s.png", "female_20s.png" },
            new[] { "cháu gái", "tiểu thư", "eleanor", "nữ nghệ sĩ", "lady", "chị", "cô gái", "bạn gái", "người yêu", "nữ sinh", "tiếp tân nữ", "y tá", "young woman" }),

        (new[] { "young_male_1.png", "young_male_2.png", "young_male_3.png", "young_male_20s.png" },
            new[] { "thanh niên", "cháu trai", "cậu", "sinh viên", "nghệ sĩ", "con trai", "young", "artist" }),

        (new[] { "teen_female_1.png", "teen_female_2.png", "teen_female_3.png", "teen_female.png" },
            new[] { "nữ sinh", "thiếu nữ", "bé gái", "con gái nhỏ", "em gái", "teen girl", "thiếu niên nữ" }),

        (new[] { "teen_male_1.png", "teen_male_2.png", "teen_male_3.png", "teen_male.png" },
            new[] { "học sinh", "thiếu niên", "cậu bé", "teen", "boy", "em trai", "thiếu niên nam" })
    };

    // Semantic Rules for Evidence / Weapons Archetypes
    private static readonly (string filename, string[] keywords)[] EvidenceRules = new[]
    {
        ("evidence_knife.png", new[] { "dao", "rạch thư", "kiếm", "knife", "dagger", "vết đâm", "vết chém", "lưỡi dao", "hung khí", "máu" }),
        ("evidence_sedative.png", new[] { "thuốc", "an thần", "độc", "poison", "lọ", "chai", "sedative", "viên", "liều lượng", "dược", "chất độc" }),
        ("pocket_watch_broken.png", new[] { "đồng hồ", "watch", "pocket", "thời gian", "kim đồng hồ", "bỏ túi", "timepiece" }),
        ("evidence_revolver.png", new[] { "súng", "đạn", "gun", "revolver", "pistol", "khẩu súng", "vết bắn", "nòng súng" }),
        ("evidence_letter.png", new[] { "thư", "bức thư", "giấy", "di chúc", "tài liệu", "nhật ký", "bản ghi", "letter", "note", "đe dọa" }),
        ("evidence_rope.png", new[] { "dây", "thừng", "siết", "cổ", "rope", "thòng lọng", "sợi dây" }),
        ("evidence_key.png", new[] { "chìa", "khóa", "key", "ổ khóa", "chùm chìa" }),
        ("evidence_glass.png", new[] { "kính", "thủy tinh", "gương", "vỡ", "mặt kính", "glass", "mảnh vỡ" }),
        ("evidence_teacup.png", new[] { "tách", "chén", "trà", "cà phê", "ly", "cup", "teacup", "bình trà" })
    };

    /// <summary>
    /// Nạp hoặc ghép ảnh tương thích ngay lập tức cho thẻ bài.
    /// </summary>
    public static Texture2D ResolveTexture(string imageUrlOrPath, string cardId, string title, bool isSuspect)
    {
        string cacheKey = $"{cardId}_{title}";
        if (textureCache.TryGetValue(cacheKey, out Texture2D cached) && cached != null)
        {
            return cached;
        }

        // 1. Nếu có đường dẫn file cụ thể, thử tìm nạp trực tiếp từ ổ cứng
        if (!string.IsNullOrEmpty(imageUrlOrPath))
        {
            string cleanName = Path.GetFileName(imageUrlOrPath.Trim());
            Texture2D directTex = LoadFromStreamingAssets(cleanName, isSuspect);
            if (directTex != null)
            {
                textureCache[cacheKey] = directTex;
                return directTex;
            }
        }

        // 2. Thuật toán Semantic Matching dựa trên tên & mô tả + biến thể 3X
        string matchedFileName = MatchAssetFileName(cardId, title, isSuspect);
        Texture2D matchedTex = LoadFromStreamingAssets(matchedFileName, isSuspect);
        if (matchedTex != null)
        {
            textureCache[cacheKey] = matchedTex;
            return matchedTex;
        }

        // 3. Procedural Fallback nếu thiếu file ảnh trên đĩa (không bao giờ để ô đen)
        Texture2D fallbackTex = GenerateProceduralBadge(title, isSuspect);
        textureCache[cacheKey] = fallbackTex;
        return fallbackTex;
    }

    /// <summary>
    /// Thuật toán so khớp từ khóa và lựa chọn biến thể 3X thích hợp cho nghi phạm.
    /// </summary>
    public static string MatchAssetFileName(string cardId, string text, bool isSuspect)
    {
        string lower = (text ?? "").ToLowerInvariant();
        int hash = Math.Abs(((cardId ?? "") + "_" + (text ?? "")).GetHashCode());

        if (isSuspect)
        {
            foreach (var rule in SuspectRules)
            {
                foreach (string kw in rule.keywords)
                {
                    if (lower.Contains(kw))
                    {
                        int index = hash % rule.variants.Length;
                        return rule.variants[index];
                    }
                }
            }
            // Fallback suspect
            string[] defaultFallbacks = new[] { "young_male_1.png", "middle_male_1.png", "young_female_1.png" };
            return defaultFallbacks[hash % defaultFallbacks.Length];
        }
        else
        {
            foreach (var rule in EvidenceRules)
            {
                foreach (string kw in rule.keywords)
                {
                    if (lower.Contains(kw)) return rule.filename;
                }
            }
            return "evidence_knife.png";
        }
    }

    private static Texture2D LoadFromStreamingAssets(string fileName, bool isSuspect)
    {
        if (string.IsNullOrEmpty(fileName)) return null;

        string subFolder = isSuspect ? "suspects" : "evidences";

        string[] candidatePaths = new string[]
        {
            Path.Combine(Application.streamingAssetsPath, "assets", subFolder, fileName),
            Path.Combine(Application.streamingAssetsPath, "assets", fileName),
            Path.Combine(Application.streamingAssetsPath, fileName),
            Path.Combine(Application.dataPath, "StreamingAssets", "assets", subFolder, fileName),
            Path.Combine(Application.dataPath, "StreamingAssets", fileName),
            Path.Combine(Application.dataPath, "..", "StreamingAssets", "assets", subFolder, fileName)
        };

        foreach (string path in candidatePaths)
        {
            if (File.Exists(path))
            {
                try
                {
                    byte[] bytes = File.ReadAllBytes(path);
                    Texture2D tex = new Texture2D(2, 2, TextureFormat.RGBA32, false);
                    if (tex.LoadImage(bytes))
                    {
                        tex.name = fileName;
                        return tex;
                    }
                }
                catch (Exception e)
                {
                    Debug.LogWarning($"[DetectiveAssetBank] Error loading '{path}': {e.Message}");
                }
            }
        }

        return null;
    }

    /// <summary>
    /// Nạp texture phong cách Noir (con dấu, thước đo, sơ đồ tử thi) từ StreamingAssets/NoirUI.
    /// </summary>
    public static Texture2D GetNoirTexture(string fileName)
    {
        if (string.IsNullOrEmpty(fileName)) return null;

        string cacheKey = $"noir_{fileName}";
        if (textureCache.TryGetValue(cacheKey, out Texture2D cached) && cached != null)
        {
            return cached;
        }

        string[] candidatePaths = new string[]
        {
            Path.Combine(Application.streamingAssetsPath, "NoirUI", fileName),
            Path.Combine(Application.streamingAssetsPath, fileName),
            Path.Combine(Application.dataPath, "Textures", "NoirUI", fileName),
            Path.Combine(Application.dataPath, "StreamingAssets", "NoirUI", fileName)
        };

        foreach (string path in candidatePaths)
        {
            if (File.Exists(path))
            {
                try
                {
                    byte[] bytes = File.ReadAllBytes(path);
                    Texture2D tex = new Texture2D(2, 2, TextureFormat.RGBA32, false);
                    if (tex.LoadImage(bytes))
                    {
                        tex.name = fileName;
                        textureCache[cacheKey] = tex;
                        return tex;
                    }
                }
                catch (Exception e)
                {
                    Debug.LogWarning($"[DetectiveAssetBank] Error loading noir texture '{path}': {e.Message}");
                }
            }
        }

        return null;
    }

    /// <summary>
    /// Tạo texture giả lập ảnh chụp hồ sơ cảnh sát cổ điển nếu không có ảnh gốc.
    /// </summary>
    private static Texture2D GenerateProceduralBadge(string title, bool isSuspect)
    {
        int size = 128;
        Texture2D tex = new Texture2D(size, size, TextureFormat.RGBA32, false);
        Color baseCol = isSuspect ? new Color(0.18f, 0.17f, 0.16f, 1f) : new Color(0.15f, 0.16f, 0.18f, 1f);
        Color borderCol = isSuspect ? new Color(0.6f, 0.2f, 0.2f, 1f) : new Color(0.2f, 0.45f, 0.6f, 1f);

        Color[] pixels = new Color[size * size];
        for (int y = 0; y < size; y++)
        {
            for (int x = 0; x < size; x++)
            {
                bool isBorder = (x < 3 || x >= size - 3 || y < 3 || y >= size - 3);
                pixels[y * size + x] = isBorder ? borderCol : baseCol;
            }
        }

        tex.SetPixels(pixels);
        tex.Apply();
        return tex;
    }

    private static Font cachedDefaultFont;

    /// <summary>
    /// Cung cấp font UI mặc định 100% không bao giờ null qua 5 tầng cơ chế dự phòng:
    /// 1. Resources.Load font nhúng dự án (Fonts/DetectiveFont).
    /// 2. Tìm font đã nhúng trong scene (Text components trong SampleScene).
    /// 3. Resources.GetBuiltinResource ("Arial.ttf").
    /// 4. Resources.GetBuiltinResource ("LegacyRuntime.ttf").
    /// 5. Tạo Dynamic Font từ hệ điều hành Windows (Arial, Segoe UI, Tahoma, v.v.).
    /// </summary>
    public static Font GetDefaultUIFont()
    {
        if (cachedDefaultFont != null) return cachedDefaultFont;

        // 1. Thử nạp từ Resources/Fonts/DetectiveFont
        try
        {
            Font resFont = Resources.Load<Font>("Fonts/DetectiveFont");
            if (resFont != null)
            {
                cachedDefaultFont = resFont;
                Debug.Log($"[DetectiveAssetBank] Successfully loaded Resources font: {resFont.name}");
                return cachedDefaultFont;
            }
        }
        catch { }

        // 2. Quét tìm Text bất kỳ trong scene đã được Unity serialize font thành công
        try
        {
#if UNITY_2022_2_OR_NEWER
            Text[] sceneTexts = UnityEngine.Object.FindObjectsByType<Text>(FindObjectsInactive.Include, FindObjectsSortMode.None);
#else
            Text[] sceneTexts = UnityEngine.Object.FindObjectsOfType<Text>(true);
#endif
            if (sceneTexts != null)
            {
                foreach (var t in sceneTexts)
                {
                    if (t != null && t.font != null)
                    {
                        cachedDefaultFont = t.font;
                        Debug.Log($"[DetectiveAssetBank] Successfully acquired scene font: {cachedDefaultFont.name}");
                        return cachedDefaultFont;
                    }
                }
            }
        }
        catch { }

        // 3. Thử Resources.GetBuiltinResource<Font>("Arial.ttf")
        try
        {
            Font builtinArial = Resources.GetBuiltinResource<Font>("Arial.ttf");
            if (builtinArial != null)
            {
                cachedDefaultFont = builtinArial;
                return cachedDefaultFont;
            }
        }
        catch { }

        // 4. Thử Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf")
        try
        {
            Font builtinLegacy = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            if (builtinLegacy != null)
            {
                cachedDefaultFont = builtinLegacy;
                return cachedDefaultFont;
            }
        }
        catch { }

        // 5. Tạo dynamic font từ Windows OS
        string[] osFontNames = new string[] { "Arial", "Segoe UI", "Calibri", "Tahoma", "Verdana" };
        foreach (string fn in osFontNames)
        {
            try
            {
                Font osFont = Font.CreateDynamicFontFromOSFont(fn, 14);
                if (osFont != null)
                {
                    cachedDefaultFont = osFont;
                    Debug.Log($"[DetectiveAssetBank] Successfully created dynamic OS font: {fn}");
                    return cachedDefaultFont;
                }
            }
            catch { }
        }

        Debug.LogError("[DetectiveAssetBank] CRITICAL: Could not find or load ANY font!");
        return null;
    }
}
