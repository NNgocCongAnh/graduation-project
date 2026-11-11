using System;

/// <summary>
/// Conversions for the voice wire format: mono PCM16 little-endian at <see cref="SampleRate"/>.
/// Pure functions (no Unity API) so they can be unit-tested and called from the audio thread.
/// </summary>
public static class PcmCodec
{
    public const int SampleRate = 16000;

    public static byte[] FloatToPcm16(float[] samples, int count)
    {
        byte[] bytes = new byte[count * 2];
        for (int i = 0; i < count; i++)
        {
            float clamped = Math.Max(-1f, Math.Min(1f, samples[i]));
            short value = (short)Math.Round(clamped * short.MaxValue);
            bytes[i * 2] = (byte)(value & 0xFF);
            bytes[i * 2 + 1] = (byte)((value >> 8) & 0xFF);
        }
        return bytes;
    }

    public static float[] Pcm16ToFloat(byte[] bytes)
    {
        int count = bytes.Length / 2;
        float[] samples = new float[count];
        for (int i = 0; i < count; i++)
        {
            short value = (short)(bytes[i * 2] | (bytes[i * 2 + 1] << 8));
            samples[i] = value / (float)short.MaxValue;
        }
        return samples;
    }

    /// <summary>Linear resampling; good enough for speech on a LAN.</summary>
    public static float[] Resample(float[] input, int inputCount, int fromRate, int toRate)
    {
        if (fromRate == toRate)
        {
            float[] copy = new float[inputCount];
            Array.Copy(input, copy, inputCount);
            return copy;
        }

        int outputCount = (int)((long)inputCount * toRate / fromRate);
        float[] output = new float[outputCount];
        double step = (double)fromRate / toRate;
        for (int i = 0; i < outputCount; i++)
        {
            double pos = i * step;
            int index = (int)pos;
            double frac = pos - index;
            float a = input[Math.Min(index, inputCount - 1)];
            float b = input[Math.Min(index + 1, inputCount - 1)];
            output[i] = (float)(a + (b - a) * frac);
        }
        return output;
    }

    /// <summary>Root-mean-square level of a block, 0..1 (for speaking indicators / gating).</summary>
    public static float Rms(float[] samples, int count)
    {
        if (count <= 0) return 0f;
        double sum = 0;
        for (int i = 0; i < count; i++) sum += samples[i] * samples[i];
        return (float)Math.Sqrt(sum / count);
    }
}
