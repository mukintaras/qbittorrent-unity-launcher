What is this?
=============
This is small script for integrating qBittorrent with Unity Launcher.

Instructions
=============

1. Download `qbittorrent-unity-launcher.py` and module `qbittorrentrpc` anywhere, leave both in the same directory.

2. Make `qbittorrent-unity-launcher.py` executable.
    
    `chmod +x /path/to/qbittorrent-unity-launcher.py`

3. Copy `/usr/share/applications/qBittorrent.desktop` to `~/.local/share/applications`
      
    `cp /usr/share/applications/qBittorrent.desktop ~/.local/share/applications/qBittorrent.desktop`

4. Edit newly copied file

    `gedit ~/.local/share/applications/qBittorrent.desktop`
    
5. Find Exec option and prepend `/path/to/qbittorrent-unity-launcher.py` to command
    
    `Exec=/path/to/qbittorrent-unity-launcher/qbittorrent-unity-launcher.py qbittorrent %U`

6. Make copied .desktop file executable.
    
    `chmod +x ~/.local/share/applications/qBittorrent.desktop`

7. You are done! Now you can use the new .desktop file to open qBittorent or drag to the the Unity Dash.

