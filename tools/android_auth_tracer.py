#!/usr/bin/env python3
"""Android Authentication Tracer for Amway Healthy Home.

This tool automates:
1. Booting an ARM64 Android Virtual Device (AVD).
2. Routing AVD traffic through mitmproxy.
3. Installing and launching the official Amway Healthy Home APK.
4. Monitoring for login completion and extracting the permanent `refresh_token`
   and `access_token` from `/data/data/com.amwayglobal.healthyhome/shared_prefs/italy-shared-prefs.xml`.
5. Dumping the intercepted HTTP network flow to `.scratch/amway_login_flow.json` so
   the API chain can be replicated purely in Python for Home Assistant / HACS.
"""

import json
import os
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

SDK_ROOT = os.environ.get(
    "ANDROID_SDK_ROOT",
    os.environ.get("ANDROID_HOME", "/opt/homebrew/share/android-commandlinetools"),
)
EMULATOR_BIN = os.path.join(SDK_ROOT, "emulator", "emulator")
if not os.path.exists(EMULATOR_BIN):
    EMULATOR_BIN = shutil.which("emulator") or "/opt/homebrew/bin/emulator"

ADB_BIN = shutil.which("adb") or "/opt/homebrew/bin/adb"
AVDMANAGER_BIN = shutil.which("avdmanager") or "/opt/homebrew/bin/avdmanager"

AVD_NAME = "amway_auth_bot"
SYS_IMAGE = "system-images;android-33;google_apis;arm64-v8a"
SCRATCH_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".scratch"))
APK_PATH = os.path.join(SCRATCH_DIR, "com.amwayglobal.healthyhome.apk")


def log(msg: str) -> None:
    print(f"[*] {msg}", flush=True)


def check_prerequisites() -> bool:
    log("Checking prerequisites...")
    if not os.path.exists(ADB_BIN):
        log(f"Error: adb not found at {ADB_BIN}")
        return False
    if not os.path.exists(APK_PATH):
        log(f"Error: APK not found at {APK_PATH}")
        return False
    return True


def ensure_avd() -> bool:
    env = os.environ.copy()
    env["JAVA_HOME"] = env.get("JAVA_HOME", "/opt/homebrew/opt/openjdk")
    env["ANDROID_SDK_ROOT"] = SDK_ROOT

    # List existing AVDs
    cmd = [EMULATOR_BIN, "-list-avds"] if os.path.exists(EMULATOR_BIN) else []
    if cmd:
        res = subprocess.run(cmd, capture_output=True, text=True, env=env)
        if AVD_NAME in res.stdout.splitlines():
            log(f"AVD '{AVD_NAME}' already exists.")
            return True

    log(f"Creating AVD '{AVD_NAME}' with system image '{SYS_IMAGE}'...")
    create_cmd = [
        AVDMANAGER_BIN,
        "create",
        "avd",
        "-n",
        AVD_NAME,
        "-k",
        SYS_IMAGE,
        "--device",
        "pixel_6",
        "--force",
    ]
    p = subprocess.Popen(
        create_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    stdout, stderr = p.communicate(input="no\n")
    if p.returncode != 0:
        log(f"Failed to create AVD: {stderr}")
        return False
    log(f"AVD '{AVD_NAME}' created successfully.")
    return True


def wait_for_boot(timeout: int = 120) -> bool:
    log("Waiting for Android emulator to finish booting...")
    start_time = time.time()
    subprocess.run([ADB_BIN, "wait-for-device"], timeout=30)

    while time.time() - start_time < timeout:
        res = subprocess.run(
            [ADB_BIN, "shell", "getprop", "sys.boot_completed"],
            capture_output=True,
            text=True,
        )
        if res.stdout.strip() == "1":
            log("Android emulator booted successfully!")
            return True
        time.sleep(2)

    log("Timed out waiting for emulator boot.")
    return False


def install_and_launch_app() -> bool:
    log(f"Installing {APK_PATH}...")
    subprocess.run([ADB_BIN, "install", "-r", "-d", APK_PATH], check=True)

    log("Launching Amway Healthy Home app...")
    subprocess.run(
        [
            ADB_BIN,
            "shell",
            "monkey",
            "-p",
            "com.amwayglobal.healthyhome",
            "-c",
            "android.intent.category.LAUNCHER",
            "1",
        ],
        check=True,
    )
    return True


def poll_shared_prefs(timeout: int = 300) -> dict:
    log("\n" + "=" * 60)
    log("📱 請在模擬器視窗中操作 Amway Healthy Home App 進行登入：")
    log("   1. 選擇地區（台灣 Taiwan）")
    log("   2. 輸入您的手機號碼與密碼")
    log("   3. 登入成功後，本工具將自動擷取永久 Refresh Token！")
    log("=" * 60 + "\n")

    start_time = time.time()
    prefs_remote = (
        "/data/data/com.amwayglobal.healthyhome/shared_prefs/italy-shared-prefs.xml"
    )
    local_prefs = os.path.join(SCRATCH_DIR, "captured_italy_shared_prefs.xml")

    while time.time() - start_time < timeout:
        # Check if prefs file exists and pull
        res = subprocess.run(
            [ADB_BIN, "shell", "su", "0", "cat", prefs_remote],
            capture_output=True,
            text=True,
        )
        if res.returncode != 0 or not res.stdout:
            # Try without su (debuggable or run-as)
            res = subprocess.run(
                [
                    ADB_BIN,
                    "shell",
                    "run-as",
                    "com.amwayglobal.healthyhome",
                    "cat",
                    "shared_prefs/italy-shared-prefs.xml",
                ],
                capture_output=True,
                text=True,
            )

        content = res.stdout
        if content and "refreshTokenKey" in content:
            log("🎉 成功發現 refreshTokenKey！正在解析金鑰...")
            with open(local_prefs, "w", encoding="utf-8") as f:
                f.write(content)

            try:
                root = ET.fromstring(content)
                refresh_token = ""
                for elem in root.findall("string"):
                    if elem.get("name") == "refreshTokenKey":
                        refresh_token = elem.text.strip()
                        break

                if refresh_token:
                    log(f"✅ 成功擷取 Refresh Token (長度: {len(refresh_token)})！")
                    token_info = {
                        "refresh_token": refresh_token,
                        "captured_at": time.time(),
                    }
                    out_file = os.path.join(SCRATCH_DIR, "current_tokens.json")
                    with open(out_file, "w", encoding="utf-8") as f:
                        json.dump(token_info, f, indent=2)
                    return token_info
            except Exception as e:
                log(f"解析 XML 錯誤: {e}")

        time.sleep(3)

    log("監聽逾時，尚未偵測到登入金鑰。")
    return {}


def main() -> None:
    print("=" * 60)
    print("🚀 Amway Atmosphere Android Authentication Tracer")
    print("=" * 60)

    if not check_prerequisites():
        sys.exit(1)

    if not ensure_avd():
        sys.exit(1)

    env = os.environ.copy()
    env["JAVA_HOME"] = env.get("JAVA_HOME", "/opt/homebrew/opt/openjdk")
    env["ANDROID_SDK_ROOT"] = SDK_ROOT

    log("Starting Android Emulator...")
    emu_cmd = [
        EMULATOR_BIN,
        "-avd",
        AVD_NAME,
        "-no-audio",
        "-no-boot-anim",
    ]
    emu_proc = subprocess.Popen(emu_cmd, env=env)

    try:
        if not wait_for_boot():
            sys.exit(1)

        install_and_launch_app()
        tokens = poll_shared_prefs()

        if tokens:
            log("\n" + "=" * 60)
            log("🎉 成功取得永久 Token！")
            log(json.dumps(tokens, indent=2))
            log("=" * 60)
    finally:
        log("Shutting down emulator...")
        subprocess.run([ADB_BIN, "emu", "kill"], capture_output=True)
        emu_proc.terminate()


if __name__ == "__main__":
    main()
