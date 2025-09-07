#Persistent
global AutoRetry := false   ; start disabled
SetTimer, CheckRetry, 2000
return

; Toggle with Ctrl+Alt+R
^!r::
    AutoRetry := !AutoRetry
    if (AutoRetry) {
        TrayTip, Auto Retry, Enabled, 1
    } else {
        TrayTip, Auto Retry, Disabled, 1
    }
return

CheckRetry:
    if (!AutoRetry)
        return

    ; Debug mode: draw a box where Retry was found
    ImageSearch, Px, Py, 0, 0, 1920, 1032, *50 %A_ScriptDir%\retry.png
    if (ErrorLevel = 0) {
        Click, %Px%, %Py%
        Tooltip, Clicked Retry at %Px%x%Py%
        Sleep, 2000
        Tooltip
    } else {
        Tooltip, Not found
        Sleep, 500
        Tooltip
    }
return
