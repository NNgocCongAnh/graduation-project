using System.Collections;
using System.Collections.Generic;
using System.IO;
using UnityEngine;

/// <summary>
/// Quản lý âm thanh toàn diện (Audio Manager):
/// 1. Tự động chuyển bài (Auto-advance): Không bị lặp mãi 1 bài, tự động sang bài tiếp theo khi kết thúc.
/// 2. Hỗ trợ 3 chế độ phát nhạc: Ngẫu nhiên (Shuffle), Tuần tự (Sequential Playlist), và Lặp lại 1 bài (Single Loop).
/// 3. Hỗ trợ bộ lọc Playlist: Người chơi có thể tích chọn những bài muốn nghe trong Cài Đặt.
/// 4. Phím tắt N hoặc nút bấm để chuyển nhanh bài tiếp theo.
/// 5. Phát kèn Saxophone Conan tức thì khi Kết tội lật mặt hung thủ.
/// </summary>
public class AudioManager : MonoBehaviour
{
    public static AudioManager Instance { get; private set; }

    public enum BgmTrack
    {
        NoirJazz,       // 🎷 Detective Noir Jazz ma mị
        ConanMain,      // ⚡ Detective Conan Main Theme (Bùng nổ phá án)
        ConanRan,       // 🌸 Conan - Ran's Theme (Nhẹ nhàng, êm dịu)
        ConanDream,     // 🌙 Conan - Conan's Dream (Suy tư điều tra)
        ConanShowdown,  // ⚔️ Conan - Showdown (Đối đầu kịch tính)
        Mute            // 🔇 Tắt nhạc
    }

    public enum PlaybackMode
    {
        Shuffle,        // 🔀 Ngẫu nhiên
        Sequential,     // 🔁 Tuần tự danh sách
        SingleLoop      // 🔂 Lặp 1 bài
    }

    [Header("Audio Sources")]
    private AudioSource bgmSource;
    private AudioSource sfxSource;

    private AudioClip noirClip;
    private AudioClip conanMainClip;
    private AudioClip conanRanClip;
    private AudioClip conanDreamClip;
    private AudioClip conanShowdownClip;

    private const string PrefKeyMaster = "audio.volume.master";
    private const string PrefKeyBgm = "audio.volume.bgm";
    private const string PrefKeySfx = "audio.volume.sfx";
    private const string PrefKeyTrack = "audio.track.selected";
    private const string PrefKeyPlayMode = "audio.playback.mode";
    private const string PrefKeyTrackEnabled = "audio.track.enabled.";

    public float MasterVolume { get; private set; } = 0.8f;
    public float BgmVolume { get; private set; } = 0.7f;
    public float SfxVolume { get; private set; } = 0.9f;
    public BgmTrack CurrentTrack { get; private set; } = BgmTrack.ConanRan;
    public PlaybackMode CurrentPlayMode { get; private set; } = PlaybackMode.Shuffle;

    private HashSet<BgmTrack> enabledTracks = new HashSet<BgmTrack>();

    private static readonly BgmTrack[] AllPlayableTracks = new[]
    {
        BgmTrack.NoirJazz,
        BgmTrack.ConanMain,
        BgmTrack.ConanRan,
        BgmTrack.ConanDream,
        BgmTrack.ConanShowdown
    };

    private void Awake()
    {
        if (Instance == null)
        {
            Instance = this;
            DontDestroyOnLoad(gameObject);
            InitializeAudioSources();
            LoadPreferences();
        }
        else
        {
            Destroy(gameObject);
        }
    }

    private void Start()
    {
        StartCoroutine(LoadClipsAndPlay());
    }

    private void Update()
    {
        // Auto-advance when the current track finishes
        if (CurrentTrack != BgmTrack.Mute && bgmSource != null && bgmSource.clip != null && !bgmSource.isPlaying)
        {
            // Only auto advance if clip has reached near the end
            if (bgmSource.time >= bgmSource.clip.length - 0.5f || bgmSource.time == 0f)
            {
                OnTrackFinished();
            }
        }
    }

    private void InitializeAudioSources()
    {
        bgmSource = gameObject.AddComponent<AudioSource>();
        bgmSource.loop = false; // Never infinite loop 1 song!
        bgmSource.playOnAwake = false;

        sfxSource = gameObject.AddComponent<AudioSource>();
        sfxSource.loop = false;
        sfxSource.playOnAwake = false;
    }

    private void LoadPreferences()
    {
        MasterVolume = PlayerPrefs.GetFloat(PrefKeyMaster, 0.8f);
        BgmVolume = PlayerPrefs.GetFloat(PrefKeyBgm, 0.7f);
        SfxVolume = PlayerPrefs.GetFloat(PrefKeySfx, 0.9f);
        CurrentTrack = (BgmTrack)PlayerPrefs.GetInt(PrefKeyTrack, (int)BgmTrack.ConanRan);
        CurrentPlayMode = (PlaybackMode)PlayerPrefs.GetInt(PrefKeyPlayMode, (int)PlaybackMode.Shuffle);

        // Load active playlist tracks
        enabledTracks.Clear();
        foreach (var track in AllPlayableTracks)
        {
            int en = PlayerPrefs.GetInt(PrefKeyTrackEnabled + track.ToString(), 1);
            if (en == 1) enabledTracks.Add(track);
        }
        if (enabledTracks.Count == 0)
        {
            // Fallback: at least enable all
            foreach (var track in AllPlayableTracks) enabledTracks.Add(track);
        }

        ApplyVolumes();
    }

    public void SetMasterVolume(float val)
    {
        MasterVolume = Mathf.Clamp01(val);
        PlayerPrefs.SetFloat(PrefKeyMaster, MasterVolume);
        ApplyVolumes();
    }

    public void SetBgmVolume(float val)
    {
        BgmVolume = Mathf.Clamp01(val);
        PlayerPrefs.SetFloat(PrefKeyBgm, BgmVolume);
        ApplyVolumes();
    }

    public void SetSfxVolume(float val)
    {
        SfxVolume = Mathf.Clamp01(val);
        PlayerPrefs.SetFloat(PrefKeySfx, SfxVolume);
        ApplyVolumes();
    }

    public void SetPlaybackMode(PlaybackMode mode)
    {
        CurrentPlayMode = mode;
        PlayerPrefs.SetInt(PrefKeyPlayMode, (int)mode);
        PlayerPrefs.Save();
    }

    public bool IsTrackEnabled(BgmTrack track)
    {
        return enabledTracks.Contains(track);
    }

    public void SetTrackEnabled(BgmTrack track, bool enabled)
    {
        if (enabled)
        {
            enabledTracks.Add(track);
            PlayerPrefs.SetInt(PrefKeyTrackEnabled + track.ToString(), 1);
        }
        else
        {
            enabledTracks.Remove(track);
            PlayerPrefs.SetInt(PrefKeyTrackEnabled + track.ToString(), 0);
        }
        PlayerPrefs.Save();

        // If current track is no longer enabled, advance
        if (!enabled && CurrentTrack == track)
        {
            PlayNextTrack();
        }
    }

    public void SwitchTrack(BgmTrack track)
    {
        CurrentTrack = track;
        PlayerPrefs.SetInt(PrefKeyTrack, (int)track);
        PlayerPrefs.Save();
        PlaySelectedTrack();
    }

    public void PlayNextTrack()
    {
        if (CurrentTrack == BgmTrack.Mute) return;

        List<BgmTrack> list = GetEnabledList();
        if (list.Count == 0) return;

        if (CurrentPlayMode == PlaybackMode.Shuffle && list.Count > 1)
        {
            BgmTrack next;
            do
            {
                next = list[Random.Range(0, list.Count)];
            } while (next == CurrentTrack && list.Count > 1);
            SwitchTrack(next);
        }
        else
        {
            int idx = list.IndexOf(CurrentTrack);
            int nextIdx = (idx + 1) % list.Count;
            SwitchTrack(list[nextIdx]);
        }
    }

    private void OnTrackFinished()
    {
        if (CurrentPlayMode == PlaybackMode.SingleLoop)
        {
            if (bgmSource != null)
            {
                bgmSource.time = 0f;
                bgmSource.Play();
            }
        }
        else
        {
            PlayNextTrack();
        }
    }

    private List<BgmTrack> GetEnabledList()
    {
        List<BgmTrack> list = new List<BgmTrack>();
        foreach (var t in AllPlayableTracks)
        {
            if (enabledTracks.Contains(t)) list.Add(t);
        }
        if (list.Count == 0) list.AddRange(AllPlayableTracks);
        return list;
    }

    private void ApplyVolumes()
    {
        if (bgmSource != null) bgmSource.volume = MasterVolume * BgmVolume;
        if (sfxSource != null) sfxSource.volume = MasterVolume * SfxVolume;
    }

    private IEnumerator LoadClipsAndPlay()
    {
        yield return StartCoroutine(LoadLocalClip("BGM_Detective_Noir.mp3", clip => noirClip = clip));
        yield return StartCoroutine(LoadLocalClip("BGM_Detective_Conan.mp3", clip => conanMainClip = clip));
        yield return StartCoroutine(LoadLocalClip("BGM_Conan_Ran_Theme.mp3", clip => conanRanClip = clip));
        yield return StartCoroutine(LoadLocalClip("BGM_Conan_Dream.mp3", clip => conanDreamClip = clip));
        yield return StartCoroutine(LoadLocalClip("BGM_Conan_Showdown.mp3", clip => conanShowdownClip = clip));

        PlaySelectedTrack();
    }

    private IEnumerator LoadLocalClip(string fileName, System.Action<AudioClip> onLoaded)
    {
        string[] searchPaths = new string[]
        {
            Path.Combine(Application.streamingAssetsPath, "Audio", fileName),
            Path.Combine(Application.dataPath, "Audio", fileName),
            Path.Combine(Application.dataPath, "..", "Audio", fileName),
            Path.Combine(Application.dataPath, "..", "Assets", "Audio", fileName)
        };

        string foundPath = null;
        foreach (var p in searchPaths)
        {
            if (File.Exists(p))
            {
                foundPath = p;
                break;
            }
        }

        if (!string.IsNullOrEmpty(foundPath))
        {
            string url = "file://" + foundPath.Replace("\\", "/");
            using (UnityEngine.Networking.UnityWebRequest www = UnityEngine.Networking.UnityWebRequestMultimedia.GetAudioClip(url, AudioType.MPEG))
            {
                yield return www.SendWebRequest();
                if (www.result == UnityEngine.Networking.UnityWebRequest.Result.Success)
                {
                    AudioClip clip = UnityEngine.Networking.DownloadHandlerAudioClip.GetContent(www);
                    clip.name = fileName;
                    onLoaded?.Invoke(clip);
                }
            }
        }
    }

    public void PlaySelectedTrack()
    {
        if (bgmSource == null) return;

        AudioClip targetClip = null;
        switch (CurrentTrack)
        {
            case BgmTrack.NoirJazz:
                targetClip = noirClip;
                break;
            case BgmTrack.ConanMain:
                targetClip = conanMainClip;
                break;
            case BgmTrack.ConanRan:
                targetClip = conanRanClip ?? conanMainClip;
                break;
            case BgmTrack.ConanDream:
                targetClip = conanDreamClip ?? conanMainClip;
                break;
            case BgmTrack.ConanShowdown:
                targetClip = conanShowdownClip ?? conanMainClip;
                break;
            case BgmTrack.Mute:
                bgmSource.Stop();
                return;
        }

        if (targetClip != null)
        {
            if (bgmSource.clip != targetClip || !bgmSource.isPlaying)
            {
                bgmSource.clip = targetClip;
                bgmSource.time = 0f;
                bgmSource.Play();
            }
        }
        ApplyVolumes();
    }

    /// <summary>
    /// Phát âm thanh ghim / click nhẹ nhàng khi tương tác bảng
    /// </summary>
    public void PlayPinClick()
    {
        if (sfxSource == null) return;
        // Tạo âm thanh pop ngắn
        int sampleRate = 44100;
        int samplesCount = (int)(sampleRate * 0.04f);
        float[] samples = new float[samplesCount];
        for (int i = 0; i < samplesCount; i++)
        {
            float t = (float)i / samplesCount;
            samples[i] = Mathf.Sin(2f * Mathf.PI * 650f * ((float)i / sampleRate)) * (1f - t);
        }
        AudioClip clip = AudioClip.Create("PinClick", samplesCount, 1, sampleRate, false);
        clip.SetData(samples, 0);
        sfxSource.PlayOneShot(clip, SfxVolume * MasterVolume * 0.7f);
    }

    /// <summary>
    /// Phát bản Conan Main Theme ngay lập tức để phục vụ hiệu ứng Lật Mặt Hung Thủ
    /// </summary>
    public void PlayConanClimaxTheme()
    {
        if (bgmSource != null && conanMainClip != null)
        {
            bgmSource.clip = conanMainClip;
            bgmSource.time = 0f;
            bgmSource.Play();
            ApplyVolumes();
        }
    }

    public string GetTrackDisplayName(BgmTrack track)
    {
        switch (track)
        {
            case BgmTrack.NoirJazz: return "🎷 Detective Noir Jazz (Ma mị)";
            case BgmTrack.ConanMain: return "⚡ Conan Main Theme (Phá án)";
            case BgmTrack.ConanRan: return "🌸 Ran's Theme (Nhẹ nhàng)";
            case BgmTrack.ConanDream: return "🌙 Conan's Dream (Suy tư)";
            case BgmTrack.ConanShowdown: return "⚔️ Showdown (Đối đầu)";
            case BgmTrack.Mute: return "🔇 Tắt nhạc";
            default: return track.ToString();
        }
    }
}
