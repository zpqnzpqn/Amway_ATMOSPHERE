#!/usr/bin/env python3
"""Amway Atmosphere Token Assistant (New capture tool).

This standalone helper tool allows users to safely capture their Amway Conex
Bearer Access Token for use with the Home Assistant Amway Atmosphere integration.

Usage:
  # Mode 1: Local proxy listener (Recommended for Mobile App)
  python3 tools/get_token.py --proxy [--port 8080]

  # Mode 2: Browser OAuth guide (Manual URL exchange)
  python3 tools/get_token.py --manual
"""

import argparse
import base64
import json
import os
import socket
import sys
import urllib.parse
import urllib.request

# ⚠️ 錯誤端點警告：
# 切勿使用 gluu-prod01-prod.amstack-amwayidv2-prod.amwayglobal.com/oxauth/restv1/authorize，那是綠色內部頁面。
# 正確官方消費者入口為 account2.amwayglobal.com
OFFICIAL_AUTH_PORTAL = "https://account2.amwayglobal.com"
GLUU_TOKEN_ENDPOINT = (
    "https://gluu-prod01-prod.amstack-amwayidv2-prod.amwayglobal.com/oxauth/restv1/token"
)
CLIENT_ID = "7b90a30d-b404-4da7-a72b-449db798387c"
CLIENT_SECRET = (
    "296cf938479e0a0a520bfd2629b3ae3ecfa450c283626e25be4722513a9686df"
)
REDIRECT_URI = "amwayhealthyhome://loginRedirect"
DEFAULT_SCOPES = (
    "openid profile email address phone offline_access "
    "bonus:all:read mdms:uberprofile:read partyID "
    "durables:parties:read durables:products:read durables:registration:create "
    "given_name middle_name family_name abo"
)


def get_local_ip() -> str:
    """Detect local IP address of current machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connect to public DNS to detect primary interface IP
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def print_banner(token: str) -> None:
    """Print the captured token with clear Home Assistant instructions."""
    print("\n" + "=" * 70)
    print("🎉 恭喜！成功捕獲 Amway Conex Access Token！")
    print("=" * 70)
    print("\n請複製以下 Access Token，並貼入 Home Assistant 設定精靈：\n")
    print(token)
    print("\n" + "=" * 70)
    print("⚠️  安全提示：")
    print("1. 請妥善保管您的 Token，切勿公開或上傳至 GitHub。")
    print("2. 若您剛才在手機上設置了 Wi-Fi 代理，請記得將手機 Wi-Fi 代理切換回「關閉」。")
    print("=" * 70 + "\n")


def run_proxy_mode(port: int = 8080) -> None:
    """Run lightweight mitmproxy capture script."""
    local_ip = get_local_ip()
    print("\n" + "=" * 70)
    print("🚀 Amway Atmosphere Token 捕獲助手 (本地代理模式)")
    print("=" * 70)
    print(f"本機 IP 位址:  {local_ip}")
    print(f"代理伺服器連接埠: {port}")
    print("-" * 70)
    print("📱 請按照以下步驟在手機上操作：")
    print(f"1. 確保手機與此電腦連線至相同的 Wi-Fi 網路。")
    print(f"2. 手機開啟 Wi-Fi 設定 > 點選連線 Wi-Fi > 設定代理伺服器 > 選擇「手動」：")
    print(f"   - 伺服器: {local_ip}")
    print(f"   - 連接埠: {port}")
    print("3. 手機瀏覽器開啟 http://mitm.it 下載並信任憑證（若尚未信任）。")
    print("4. 打開「Amway Healthy Home」App，進行登入或切換清淨機開關。")
    print("5. 捕獲到 Token 後，本工具將自動印出並結束！")
    print("=" * 70)
    print("\n⏳ 正在監聽中 (按 Ctrl+C 可隨時取消)...\n")

    # In-memory inline capture addon script
    addon_code = """
import json

class AmwayTokenInterceptor:
    def request(self, flow):
        auth = flow.request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth.split("Bearer ")[1].strip()
            # Conex bearer token typically has ~2000+ length containing durables scopes
            if len(token) > 500:
                print("TOKEN_FOUND:" + token, flush=True)

addons = [AmwayTokenInterceptor()]
"""
    import subprocess
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tf:
        tf.write(addon_code)
        addon_path = tf.name

    cmd = [
        sys.executable,
        "-m",
        "mitmproxy.tools.main",
        "-s",
        addon_path,
        "-p",
        str(port),
        "--set",
        "block_global=false",
    ]

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        for line in proc.stdout:
            if "TOKEN_FOUND:" in line:
                token = line.split("TOKEN_FOUND:")[1].strip()
                proc.terminate()
                print_banner(token)
                break
    except FileNotFoundError:
        print("\n❌ 未偵測到 mitmproxy 模組。請先執行安裝：")
        print("   pip install mitmproxy\n")
    except KeyboardInterrupt:
        print("\n使用者已取消監聽。")
    finally:
        if os.path.exists(addon_path):
            os.remove(addon_path)


def run_manual_mode() -> None:
    """Run manual authorization guide via official Amway portal."""
    auth_params = {
        "clientapp": "healthyhomeTW",
        "redirect": REDIRECT_URI,
        "cancelRedirect": "amwayhealthyhome://cancelLogin",
    }
    url = f"{OFFICIAL_AUTH_PORTAL}/zh-tw/?{urllib.parse.urlencode(auth_params)}"

    print("\n" + "=" * 70)
    print("🌐 Amway Atmosphere Token 捕獲助手 (瀏覽器手動模式)")
    print("=" * 70)
    print("1. 請在瀏覽器中開啟以下官方授權網址：\n")
    print(url)
    print("\n2. 完成登入後，瀏覽器將嘗試跳轉至 `amwayhealthyhome://loginRedirect?code=...`。")
    print("3. 請複製該網址列中的完整跳轉網址（或 code 參數值）。")
    print("=" * 70)

    try:
        user_input = input("\n請在此貼上完整跳轉網址或 code： ").strip()
        if not user_input:
            print("❌ 輸入為空，已取消。")
            return

        code = user_input
        if "code=" in user_input:
            parsed = urllib.parse.urlparse(user_input)
            qs = urllib.parse.parse_qs(parsed.query)
            if "code" in qs and qs["code"]:
                code = qs["code"][0]
            else:
                code = user_input.split("code=")[1].split("&")[0]

        print(f"\n正在向認證伺服器換取 Token...")
        data = urllib.parse.urlencode(
            {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT_URI,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "scope": DEFAULT_SCOPES,
            }
        ).encode("utf-8")

        req = urllib.request.Request(
            GLUU_TOKEN_ENDPOINT,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(req) as resp:
            tokens = json.loads(resp.read().decode())
            token = tokens.get("access_token")
            if token:
                print_banner(token)
            else:
                print("❌ 換證回傳未包含 access_token：", tokens)
    except Exception as err:
        print(f"\n❌ 換證失敗: {err}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Amway Atmosphere Token Assistant"
    )
    parser.add_argument(
        "--proxy", action="store_true", help="啟動本地代理捕獲模式（推薦）"
    )
    parser.add_argument(
        "--manual", action="store_true", help="使用瀏覽器手動授權跳轉模式"
    )
    parser.add_argument(
        "--port", type=int, default=8080, help="代理伺服器連接埠 (預設 8080)"
    )

    args = parser.parse_args()
    if args.proxy:
        run_proxy_mode(args.port)
    elif args.manual:
        run_manual_mode()
    else:
        # Default menu
        print("\n請選擇 Token 獲取方式：")
        print("  1. 📱 本地代理模式 (推薦手機 App 使用)")
        print("  2. 🌐 瀏覽器手動模式")
        print("  q. 離開")
        choice = input("請輸入選項 (1/2/q): ").strip().lower()
        if choice == "1":
            run_proxy_mode(args.port)
        elif choice == "2":
            run_manual_mode()
        else:
            print("已離開。")


if __name__ == "__main__":
    main()
