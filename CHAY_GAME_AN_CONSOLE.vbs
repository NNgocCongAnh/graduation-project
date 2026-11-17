' ===========================================================================
' Trình Khởi Chạy Tự Động 100% Ẩn Console: Unsolved Case Files AI
' Tự động kích hoạt Server Backend FastAPI chạy ngầm và mở Game Unity .exe
' Khi tắt Game, tự động dọn dẹp tiến trình backend!
' ===========================================================================

Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

strCurDir = fso.GetParentFolderName(WScript.ScriptFullName)
strBackendDir = strCurDir & "\detective-backend"
strExePath = strCurDir & "\Build\UnsolvedCaseFiles.exe"

' 1. Khởi động Backend FastAPI hoàn toàn ẩn cửa sổ (WindowStyle = 0)
strCmd = "cmd /c cd /d """ & strBackendDir & """ && python -m uvicorn main:app --host 0.0.0.0 --port 8000"
WshShell.Run strCmd, 0, False

' 2. Đợi 3.5 giây để Server sẵn sàng
WScript.Sleep 3500

' 3. Mở Game Unity Client và đợi người chơi đóng game
If fso.FileExists(strExePath) Then
    WshShell.Run """" & strExePath & """", 1, True
Else
    MsgBox "Chưa tìm thấy file game tại: " & strExePath & vbCrLf & "Vui lòng chạy file DONG_GOI_GAME_EXE.bat trước!", vbCritical, "Unsolved Case Files AI"
End If

' 4. Dọn dẹp tiến trình uvicorn khi game kết thúc
WshShell.Run "cmd /c taskkill /f /im uvicorn.exe 2>nul", 0, False
