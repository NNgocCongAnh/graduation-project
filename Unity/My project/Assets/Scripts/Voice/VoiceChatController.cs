using System;
using System.Collections.Generic;
using UnityEngine;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

/// <summary>
/// Push-to-talk LAN voice: hold V to capture the default microphone, stream 40 ms PCM16
/// frames through DetectiveNetworkManager, and play peers' frames back (one
/// VoicePlayback per speaker). No third-party packages; see detective-backend/rooms.py
/// for the relay. Headphones recommended: there is no echo cancellation.
/// </summary>
public class VoiceChatController : MonoBehaviour
{
    public static VoiceChatController Instance { get; private set; }

    /// <summary>Main thread: local transmit state or the set of remote speakers changed.</summary>
    public static event Action OnSpeakingChanged;

    private const int MicClipSeconds = 1;
    private const float FrameSeconds = 0.04f;
    private const float SpeakingHoldSeconds = 0.3f;

    public bool HasMicrophone => Microphone.devices.Length > 0;
    public bool IsTransmitting { get; private set; }
    public IReadOnlyCollection<string> RemoteSpeakers => remoteSpeakers;

    private readonly Dictionary<string, VoicePlayback> playbacks = new Dictionary<string, VoicePlayback>();
    private readonly HashSet<string> remoteSpeakers = new HashSet<string>();
    private readonly List<string> scratchNames = new List<string>();

    private string micDevice;
    private AudioClip micClip;
    private int micRate;
    private int lastMicPosition;
    private float[] micBuffer;

    private void Awake()
    {
        Instance = this;
    }

    private void OnEnable()
    {
        DetectiveNetworkManager.OnVoiceFrame += HandleVoiceFrame;
    }

    private void OnDisable()
    {
        DetectiveNetworkManager.OnVoiceFrame -= HandleVoiceFrame;
        StopMicrophone();
    }

    private void Update()
    {
        bool wantsToTalk = IsPushToTalkHeld();
        if (wantsToTalk != IsTransmitting) SetTransmitting(wantsToTalk);
        if (IsTransmitting) PumpMicrophone();
        RefreshRemoteSpeakers();
    }

    // ------------------------------------------------------------------
    // Capture
    // ------------------------------------------------------------------

    private bool IsPushToTalkHeld()
    {
        DetectiveNetworkManager net = DetectiveNetworkManager.Instance;
        if (net == null || !net.IsConnected || HotkeyTaskbar.IsTypingInInputField()) return false;
#if ENABLE_INPUT_SYSTEM
        return Keyboard.current != null && Keyboard.current.vKey.isPressed;
#else
        return Input.GetKey(KeyCode.V);
#endif
    }

    private void SetTransmitting(bool transmit)
    {
        if (transmit && !EnsureMicrophone())
        {
            transmit = false;
        }
        if (transmit)
        {
            // Skip whatever the looping clip captured while we were not talking.
            lastMicPosition = Microphone.GetPosition(micDevice);
        }
        IsTransmitting = transmit;
        OnSpeakingChanged?.Invoke();
    }

    private bool EnsureMicrophone()
    {
        if (micClip != null) return true;
        if (!HasMicrophone)
        {
            DetectiveChatUI.Instance?.AddMessage("HỆ THỐNG", "Không tìm thấy micro. Bạn vẫn nghe được người khác.");
            return false;
        }

        micDevice = null; // null = the Windows default recording device
        Microphone.GetDeviceCaps(micDevice, out int minRate, out int maxRate);
        bool anyRate = minRate == 0 && maxRate == 0;
        micRate = anyRate ? PcmCodec.SampleRate : Mathf.Clamp(PcmCodec.SampleRate, minRate, maxRate);

        micClip = Microphone.Start(micDevice, true, MicClipSeconds, micRate);
        micBuffer = new float[Mathf.CeilToInt(micRate * FrameSeconds)];
        Debug.Log($"[Voice] Default microphone started at {micRate} Hz.");
        return micClip != null;
    }

    private void StopMicrophone()
    {
        if (micClip == null) return;
        Microphone.End(micDevice);
        micClip = null;
    }

    private void PumpMicrophone()
    {
        int position = Microphone.GetPosition(micDevice);
        int clipSamples = micClip.samples;
        int available = (position - lastMicPosition + clipSamples) % clipSamples;
        int frameSamples = micBuffer.Length;

        while (available >= frameSamples)
        {
            micClip.GetData(micBuffer, lastMicPosition); // wraps around the looping clip
            lastMicPosition = (lastMicPosition + frameSamples) % clipSamples;
            available -= frameSamples;

            float[] samples = PcmCodec.Resample(micBuffer, frameSamples, micRate, PcmCodec.SampleRate);
            DetectiveNetworkManager.Instance.SendVoiceFrame(PcmCodec.FloatToPcm16(samples, samples.Length));
        }
    }

    // ------------------------------------------------------------------
    // Playback
    // ------------------------------------------------------------------

    private void HandleVoiceFrame(string sender, byte[] pcm16)
    {
        if (!playbacks.TryGetValue(sender, out VoicePlayback playback) || playback == null)
        {
            var go = new GameObject($"Voice_{sender}", typeof(AudioSource), typeof(VoicePlayback));
            go.transform.SetParent(transform, false);
            playback = go.GetComponent<VoicePlayback>();
            playback.Init(sender);
            playbacks[sender] = playback;
        }
        playback.Enqueue(pcm16);
    }

    private void RefreshRemoteSpeakers()
    {
        scratchNames.Clear();
        float now = Time.unscaledTime;
        foreach (var pair in playbacks)
        {
            if (pair.Value != null && now - pair.Value.LastFrameTime < SpeakingHoldSeconds) scratchNames.Add(pair.Key);
        }

        if (scratchNames.Count == remoteSpeakers.Count && remoteSpeakers.SetEquals(scratchNames)) return;
        remoteSpeakers.Clear();
        remoteSpeakers.UnionWith(scratchNames);
        OnSpeakingChanged?.Invoke();
    }
}
