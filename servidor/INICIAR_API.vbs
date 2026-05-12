' Inicia la API en background sin ventana CMD
Option Explicit
Dim WshShell, fso, appDir, pythonExe, scriptPath
Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
appDir = fso.GetParentFolderName(WScript.ScriptFullName)
pythonExe = "C:\LOGIEZE\python\pythonw.exe"
scriptPath = appDir & "\api.py"
WshShell.Run Chr(34) & pythonExe & Chr(34) & " " & Chr(34) & scriptPath & Chr(34), 0, False
