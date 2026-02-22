@echo off
if not "%1"=="am_admin" (powershell start -verb runas '%0' am_admin & exit /b)

:: echo main code here
:: pause

cls

route print -4

netsh interface ip show config

netsh interface ip show interfaces

route.exe print ^|findstr "\<0.0.0.0\>"

set /p VPNIFnum="Set VPN interface number:"
netsh interface ip show config %VPNIFnum%

REM -- Main part delete Inet-to-VPN routes

route delete 0.0.0.0 IF %VPNIFnum%
route delete 8.0.0.0 IF %VPNIFnum%
route delete 11.0.0.0 IF %VPNIFnum%
route delete 12.0.0.0 IF %VPNIFnum%
route delete 16.0.0.0 IF %VPNIFnum%
route delete 32.0.0.0 IF %VPNIFnum%
route delete 64.0.0.0 IF %VPNIFnum%
route delete 80.0.0.0 IF %VPNIFnum%
route delete 88.0.0.0 IF %VPNIFnum%
route delete 92.0.0.0 IF %VPNIFnum%
route delete 94.0.0.0 IF %VPNIFnum%
route delete 95.0.0.0 IF %VPNIFnum%
route delete 127.0.0.0 IF %VPNIFnum%
route delete 127.0.0.1 IF %VPNIFnum%
route delete 192.0.0.0 IF %VPNIFnum%
route delete 192.168.1.0 IF %VPNIFnum%

pause
