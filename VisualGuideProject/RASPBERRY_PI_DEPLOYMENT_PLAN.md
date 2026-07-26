# Raspberry Pi Remote Access and Deployment Plan

Date: 2026-07-12

Goal:

- Remotely access the Raspberry Pi from the Windows laptop over Wi-Fi.
- Move `VisualGuideProject` from the laptop to the Pi.
- Run the same visual-guide project on Raspberry Pi hardware for real-world
  testing.
- Start the Pi robot interface automatically through the Pi desktop terminal.
- Wait in standby until the camera is plugged in.
- Run continuously until the camera is unplugged or the user quits.

Current shortcut:

- Remote file transfer can wait.
- For the first Pi test, use a USB drive or Pi desktop file manager through
  TigerVNC.

## 1. How SSH will work

SSH is a remote terminal connection.

In our setup:

- Raspberry Pi = SSH server
- Windows laptop = SSH client
- Both devices should be on the same Wi-Fi network at first
- The laptop connects to the Pi with:

```powershell
ssh <pi_username>@<pi_hostname>.local
```

or, if hostname lookup does not work:

```powershell
ssh <pi_username>@<pi_ip_address>
```

Example:

```powershell
ssh dongx@visualguidepi.local
```

## 2. Recommended first Pi setup

Use Raspberry Pi Imager on the laptop.

Recommended OS for this project:

- Raspberry Pi OS 64-bit with Desktop if we want to see OpenCV camera windows on
  the Pi.
- Raspberry Pi OS Lite if we only want headless terminal testing.

For the first real camera test, Desktop is easier because OpenCV preview windows
are useful.

In Raspberry Pi Imager customisation:

1. Set hostname, for example:

```text
visualguidepi
```

2. Set username and password.
3. Set Wi-Fi SSID and password.
4. Enable SSH.
5. Use password authentication first.

After the Pi boots, test from Windows PowerShell:

```powershell
ssh <pi_username>@visualguidepi.local
```

If that fails, find the Pi IP address from the router or Pi desktop and use:

```powershell
ssh <pi_username>@<pi_ip_address>
```

## 3. Move the project folder to the Pi without SSH

Use this path if remote transfer is not ready yet.

On the Windows laptop, create a clean transfer ZIP from the project folder:

```powershell
cd "C:\Users\dongx\OneDrive\Desktop\VisualGuideProject"
Compress-Archive -Path *.py,*.md,*.sh,requirements*.txt -DestinationPath .\VisualGuideProject_PI_TRANSFER.zip
```

Copy `VisualGuideProject_PI_TRANSFER.zip` to a USB drive.

On the Pi desktop through TigerVNC:

1. Plug in the USB drive.
2. Open the file manager.
3. Copy `VisualGuideProject_PI_TRANSFER.zip` to the Pi home folder.
4. Extract it into:

```text
/home/<pi_username>/VisualGuideProject
```

Or, in the Pi terminal:

```bash
mkdir -p ~/VisualGuideProject
unzip ~/VisualGuideProject_PI_TRANSFER.zip -d ~/VisualGuideProject
```

## 4. Move the project folder to the Pi with SSH/SCP later

First create a folder on the Pi:

```bash
mkdir -p ~/VisualGuideProject
```

From Windows PowerShell, copy the useful project files.

Do not copy laptop-only folders such as:

- `.venv-win/`
- `venv/`
- `__pycache__/`
- `Ultralytics/`
- `MatplotlibCache/`
- `runs/`

Simple first transfer:

```powershell
scp "C:\Users\dongx\OneDrive\Desktop\VisualGuideProject\*.py" <pi_username>@visualguidepi.local:~/VisualGuideProject/
scp "C:\Users\dongx\OneDrive\Desktop\VisualGuideProject\*.md" <pi_username>@visualguidepi.local:~/VisualGuideProject/
scp "C:\Users\dongx\OneDrive\Desktop\VisualGuideProject\*.sh" <pi_username>@visualguidepi.local:~/VisualGuideProject/
scp "C:\Users\dongx\OneDrive\Desktop\VisualGuideProject\requirements*.txt" <pi_username>@visualguidepi.local:~/VisualGuideProject/
```

If hostname does not work, use the Pi IP address:

```powershell
scp "C:\Users\dongx\OneDrive\Desktop\VisualGuideProject\*.py" <pi_username>@<pi_ip_address>:~/VisualGuideProject/
scp "C:\Users\dongx\OneDrive\Desktop\VisualGuideProject\*.md" <pi_username>@<pi_ip_address>:~/VisualGuideProject/
scp "C:\Users\dongx\OneDrive\Desktop\VisualGuideProject\*.sh" <pi_username>@<pi_ip_address>:~/VisualGuideProject/
scp "C:\Users\dongx\OneDrive\Desktop\VisualGuideProject\requirements*.txt" <pi_username>@<pi_ip_address>:~/VisualGuideProject/
```

Note:

- `scp` is simple and good for the first transfer.
- Later, `rsync` is better because it only sends changed files.
- Later, we can create a small deployment script once the Pi username and
  hostname are known.

## 5. Prepare Python on Raspberry Pi

For Raspberry Pi, prefer the system OpenCV package first. It is usually faster
and safer than asking `pip` to install/build OpenCV on the Pi.

On the Pi:

```bash
sudo apt update
sudo apt install -y python3-venv python3-opencv python3-numpy unzip alsa-utils
cd ~/VisualGuideProject
python3 -m venv --system-site-packages .venv-pi
source .venv-pi/bin/activate
python -m pip install --upgrade pip
python -c "import cv2, numpy; print('cv2 ok', cv2.__version__)"
```

Audio is currently disabled in `config.py`, so speech packages are not required
for the first Pi camera test.

Then test the basic OpenCV app first:

```bash
python LIVE_CAMERA_TEST.py --seconds 15 --background-seconds 3
```

Note:

- Current laptop config has `YOLO_ENABLED = True`.
- If `ultralytics` is not installed on the Pi, the code should print that YOLO
  could not load and continue with OpenCV detection.
- For the cleanest first Pi test, edit `config.py` on the Pi and set:

```python
YOLO_ENABLED = False
AUDIO_ENABLED = False
```

## 6. Pi production runner

The laptop uses `LIVE_CAMERA_TEST.py` for timed tests.

The Raspberry Pi should use:

```bash
python pi_visual_guide.py
```

or:

```bash
./start_visual_guide_pi.sh
```

Behavior:

- Pi desktop terminal opens.
- Program waits in standby if no camera is plugged in.
- When camera appears, the continuous guide session starts.
- There is no 25-second test timer.
- If the camera is unplugged, the session stops and returns to standby.
- Press `q` in the camera window or `Ctrl+C` in terminal to quit.

Before running scripts directly:

```bash
chmod +x start_visual_guide_pi.sh install_pi_autostart.sh
```

## 7. Pi desktop autostart

After the project works manually, install desktop autostart:

```bash
cd ~/VisualGuideProject
bash install_pi_autostart.sh
```

This creates:

```text
~/.config/autostart/visual-guide-robot.desktop
```

Expected behavior:

- When Raspberry Pi boots into the desktop session, a terminal starts the visual
  guide standby program.
- If the camera is not plugged in yet, the terminal stays in standby.
- Plugging in the camera starts the guide.
- Unplugging the camera returns to standby.

## 8. YOLO on Raspberry Pi

The laptop can run YOLO acceptably with:

```python
YOLO_PROCESS_INTERVAL = 10
YOLO_IMAGE_SIZE = 320
```

But Raspberry Pi 4B will likely be much slower with normal PyTorch YOLO.

Recommended Pi order:

1. First run without YOLO to confirm camera, motion, background, warnings.
2. Then install base YOLO:

```bash
python -m pip install -r requirements-yolo.txt
```

3. Test YOLO with a longer process interval, for example:

```python
YOLO_PROCESS_INTERVAL = 15
```

4. If PyTorch YOLO is too slow, export to NCNN and use the exported model.

## 9. Camera notes

On Raspberry Pi, camera index may differ from Windows.

Useful checks:

```bash
ls /dev/video*
```

For a USB webcam, OpenCV usually starts at camera index `0`.

If the Pi camera module is used instead of USB camera, we may need a different
capture path later.

## 10. First real Pi test checklist

Before testing:

- Pi boots on Wi-Fi.
- Laptop can SSH into Pi.
- Project folder is copied.
- Python environment is created.
- Basic dependencies install.
- Camera is visible from the Pi.

First timed test:

```bash
cd ~/VisualGuideProject
source .venv-pi/bin/activate
python LIVE_CAMERA_TEST.py --seconds 20 --background-seconds 3
```

First production-style test:

```bash
cd ~/VisualGuideProject
source .venv-pi/bin/activate
python pi_visual_guide.py
```

Record:

- FPS
- warning delay
- camera delay
- whether YOLO is enabled or disabled
- whether audio/beep is enabled or disabled
- any difference from laptop behavior

## 11. Current expectation

Laptop test is a development baseline.

Raspberry Pi test is the real performance gate.

If Pi FPS drops too low, the likely optimisations are:

- keep YOLO disabled at first
- run YOLO less often
- lower image size
- export YOLO to NCNN
- simplify display windows during real use
- keep audio as simple beep only

## 12. Audio warning plan on Pi

For the first Pi transfer/test, keep audio disabled:

```python
AUDIO_ENABLED = False
```

After camera FPS is acceptable, test beep mode:

```python
AUDIO_ENABLED = True
AUDIO_OUTPUT_MODE = "beep"
```

For a temporary timed test without permanently changing `config.py`, run:

```bash
python LIVE_CAMERA_TEST.py --seconds 20 --background-seconds 3 --audio
```

Current beep policy:

- beep at most once every `2.0` seconds
- beep when an obstacle is approaching ahead
- beep when a YOLO-recognized moving vehicle warning mentions `car` or
  `bicycle`
- do not beep for ordinary side/static obstacle warnings

Current beep patterns:

- approaching ahead: medium double beep
- stop/approaching ahead: fast triple beep
- car warning: lower double beep
- bicycle warning: higher quick double beep

Linux/Pi audio backend:

- `alsa-utils` provides `aplay`.
- The code generates tiny `.wav` tone files in `audio_cache/`.
- Playback happens in a background thread.

Longer-term robot hardware:

- Prefer a GPIO buzzer over speech for the wearable Pi prototype.
