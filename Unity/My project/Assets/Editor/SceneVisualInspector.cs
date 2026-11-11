using UnityEngine;
using UnityEditor;
using System.IO;

public class SceneVisualInspector : Editor
{
    [MenuItem("Detective Game/Capture Room Visual Snapshot")]
    public static void CaptureSnapshot()
    {
        Debug.Log("[SceneVisualInspector] Capturing High-Res Snapshot of Detective Room...");

        int width = 1920;
        int height = 1080;

        string snapshotsDir = Path.Combine(Application.dataPath, "Snapshots");
        if (!Directory.Exists(snapshotsDir))
        {
            Directory.CreateDirectory(snapshotsDir);
        }
        string outputPath = Path.Combine(snapshotsDir, "room_snapshot.png");

        if (Application.isPlaying)
        {
            ScreenCapture.CaptureScreenshot(outputPath);
            Debug.Log($"[SceneVisualInspector] Play-mode screenshot captured to: {outputPath}");
            AssetDatabase.Refresh();
            return;
        }

        // In Editor mode, render active Camera or Canvas
        Camera cam = Camera.main;
        if (cam == null) cam = GameObject.FindObjectOfType<Camera>();

        Canvas canvas = GameObject.FindObjectOfType<Canvas>();
        RenderMode prevMode = RenderMode.ScreenSpaceOverlay;
        Camera prevCam = null;

        if (canvas != null && cam != null)
        {
            prevMode = canvas.renderMode;
            prevCam = canvas.worldCamera;

            // Temporarily switch to ScreenSpaceCamera so camera can capture UI
            canvas.renderMode = RenderMode.ScreenSpaceCamera;
            canvas.worldCamera = cam;
            canvas.planeDistance = 10;
        }

        if (cam != null)
        {
            RenderTexture rt = new RenderTexture(width, height, 24);
            RenderTexture prevRt = cam.targetTexture;

            cam.targetTexture = rt;
            cam.Render();

            RenderTexture.active = rt;
            Texture2D tex = new Texture2D(width, height, TextureFormat.RGB24, false);
            tex.ReadPixels(new Rect(0, 0, width, height), 0, 0);
            tex.Apply();

            cam.targetTexture = prevRt;
            RenderTexture.active = null;
            DestroyImmediate(rt);

            byte[] pngData = tex.EncodeToPNG();
            DestroyImmediate(tex);
            File.WriteAllBytes(outputPath, pngData);
        }

        // Restore canvas settings
        if (canvas != null)
        {
            canvas.renderMode = prevMode;
            canvas.worldCamera = prevCam;
        }

        AssetDatabase.Refresh();
        Debug.Log($"[SceneVisualInspector] Scene Snapshot saved successfully to: {outputPath}");
    }
}

