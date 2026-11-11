using UnityEngine;

/// <summary>
/// Plays one remote player's voice. Frames arrive on the main thread and are pulled by
/// Unity's audio thread through a streaming AudioClip, with a small jitter buffer:
/// playback starts after <see cref="PrebufferSeconds"/> of audio and goes silent (and
/// re-buffers) on underrun; latency is capped by dropping the oldest audio.
/// </summary>
[RequireComponent(typeof(AudioSource))]
public class VoicePlayback : MonoBehaviour
{
    private const float PrebufferSeconds = 0.08f;
    private const float MaxBufferSeconds = 0.5f;

    private readonly object gate = new object();
    private float[] ring;
    private int head;
    private int count;
    private bool buffering = true;
    private int prebufferSamples;

    public string PlayerName { get; private set; }
    public float LastFrameTime { get; private set; } = -10f;

    public void Init(string playerName)
    {
        PlayerName = playerName;
        int rate = PcmCodec.SampleRate;
        ring = new float[Mathf.CeilToInt(rate * MaxBufferSeconds)];
        prebufferSamples = Mathf.CeilToInt(rate * PrebufferSeconds);

        AudioSource source = GetComponent<AudioSource>();
        source.spatialBlend = 0f;
        source.loop = true;
        source.playOnAwake = false;
        source.clip = AudioClip.Create($"voice_{playerName}", rate, 1, rate, true, OnAudioRead);
        source.Play();
    }

    public void Enqueue(byte[] pcm16)
    {
        float[] samples = PcmCodec.Pcm16ToFloat(pcm16);
        lock (gate)
        {
            foreach (float s in samples)
            {
                if (count == ring.Length)
                {
                    head = (head + 1) % ring.Length; // full: drop oldest to cap latency
                    count--;
                }
                ring[(head + count) % ring.Length] = s;
                count++;
            }
        }
        LastFrameTime = Time.unscaledTime;
    }

    // Audio thread.
    private void OnAudioRead(float[] data)
    {
        lock (gate)
        {
            if (buffering && count >= prebufferSamples) buffering = false;

            for (int i = 0; i < data.Length; i++)
            {
                if (buffering || count == 0)
                {
                    data[i] = 0f;
                    if (count == 0) buffering = true;
                    continue;
                }
                data[i] = ring[head];
                head = (head + 1) % ring.Length;
                count--;
            }
        }
    }
}
