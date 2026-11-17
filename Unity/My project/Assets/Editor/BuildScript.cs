using UnityEditor;
using UnityEngine;
using System.IO;

public static class BuildScript
{
    public static void PerformBuild()
    {
        try
        {
            string[] scenes = new string[] { "Assets/Scenes/SampleScene.unity" };
            string buildPath = "D:/Work/Đồ Án Tốt Nghiệp/Build/UnsolvedCaseFiles.exe";

            BuildPlayerOptions buildPlayerOptions = new BuildPlayerOptions();
            buildPlayerOptions.scenes = scenes;
            buildPlayerOptions.locationPathName = buildPath;
            buildPlayerOptions.target = BuildTarget.StandaloneWindows64;
            buildPlayerOptions.options = BuildOptions.None;

            var report = BuildPipeline.BuildPlayer(buildPlayerOptions);
            if (report.summary.result == UnityEditor.Build.Reporting.BuildResult.Succeeded)
            {
                Debug.Log("[BuildScript] Build SUCCESSFUL: " + report.summary.totalSize + " bytes");
                EditorApplication.Exit(0);
            }
            else
            {
                Debug.LogError("[BuildScript] Build FAILED with " + report.summary.totalErrors + " errors!");
                EditorApplication.Exit(1);
            }
        }
        catch (System.Exception e)
        {
            Debug.LogError("[BuildScript] Exception during build: " + e.Message);
            EditorApplication.Exit(1);
        }
    }
}
