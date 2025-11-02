#!/usr/bin/env python3
import os
import io
import sys
import time
import fnmatch
import plistlib
import paramiko
from getpass import getpass
from art import tprint
from tabulate import tabulate
from datetime import datetime

# ----------------------------------------------------
tprint("BAT PredictiveText Dumper")
print("by @Basel AbuTaleb\n\n")

# ----------------------------------------------------
host = input("[+] Enter device IP or hostname: ")
port = int(input("[+] Enter SSH port (default 22): ") or 22)
username = input("[+] Enter SSH username: ")
password = getpass("[+] Enter SSH password: ")

REMOTE_KEYBOARD_DIR = "/var/mobile/Library/Keyboard"

CANDIDATE_PATTERNS = [
    "UserDictionary.sqlite*",
    "*-dynamic-text.dat",
    "dynamic-*.dat",
    "*dynamic*.dat",
    "*.lexicon",
    "*Lexicon*.plist",
    "*.lm",
    "*.dat"
]

# ----------------------------------------------------
def human_size(n):
    for unit in ["B","KB","MB","GB","TB"]:
        if n < 1024.0:
            return f"{n:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} PB"

def match_any(name, patterns):
    return any(fnmatch.fnmatch(name, p) for p in patterns)

def safe_join(dirpath, name):
    if dirpath.endswith("/"):
        return dirpath + name
    return dirpath + "/" + name

# ----------------------------------------------------
try:
    print("[*] Connecting via SSH...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port=port, username=username, password=password)

    sftp = ssh.open_sftp()

    try:
        sftp.chdir(REMOTE_KEYBOARD_DIR)
    except IOError:
        raise RuntimeError(f"Remote path not found: {REMOTE_KEYBOARD_DIR}")

    print(f"[*] Scanning {REMOTE_KEYBOARD_DIR} ...")
    entries = sftp.listdir_attr(".")
    files = [e for e in entries if not str(e).startswith("d")]

    candidates = []
    for e in entries:
        name = getattr(e, "filename", None) or str(e)
        if name in [".",".."]:
            continue
        if match_any(name, CANDIDATE_PATTERNS):
            size = getattr(e, "st_size", 0)
            mtime = getattr(e, "st_mtime", 0)
            candidates.append({
                "name": name,
                "size": size,
                "mtime": mtime
            })

    if not candidates:
        print("[!] No predictive-text / keyboard candidate files found by pattern.")
        sftp.close()
        ssh.close()
        sys.exit(0)

    table_data = []
    for idx, c in enumerate(sorted(candidates, key=lambda x: x["mtime"], reverse=True), 1):
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(c["mtime"])) if c["mtime"] else "-"
        table_data.append([idx, c["name"], human_size(c["size"]), ts])
    print("\n--- Predictive Text / Keyboard Files ---")
    print(tabulate(table_data, headers=["#", "Filename", "Size", "Modified (device time)"], tablefmt="grid", stralign="left"))

    choice = input("\n[?] Download (A)ll or select by numbers (e.g., 1,3,5): ").strip()
    if choice.lower().startswith("a"):
        to_download = sorted(candidates, key=lambda x: x["mtime"], reverse=True)
    else:
        indexes = []
        if choice:
            for part in choice.split(","):
                part = part.strip()
                if part.isdigit():
                    indexes.append(int(part))
        picked = []
        sorted_list = sorted(candidates, key=lambda x: x["mtime"], reverse=True)
        for i in indexes:
            if 1 <= i <= len(sorted_list):
                picked.append(sorted_list[i-1])
        if not picked:
            print("[!] No valid selection. Exiting.")
            sftp.close()
            ssh.close()
            sys.exit(0)
        to_download = picked

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.join(os.getcwd(), f"predictive_text_dump_{stamp}")
    os.makedirs(out_dir, exist_ok=True)
    print(f"[*] Saving files to: {out_dir}")

    for c in to_download:
        remote_path = safe_join(REMOTE_KEYBOARD_DIR, c["name"])
        local_path = os.path.join(out_dir, c["name"])
        try:
            print(f"[+] Downloading: {c['name']}")
            sftp.get(remote_path, local_path)
        except Exception as ex:
            print(f"[!] Failed to download {c['name']}: {ex}")

    plist_rows = []
    for c in to_download:
        if c["name"].lower().endswith(".plist"):
            local_path = os.path.join(out_dir, c["name"])
            try:
                with open(local_path, "rb") as f:
                    data = plistlib.load(io.BytesIO(f.read()))
                if isinstance(data, dict):
                    for k, v in data.items():
                        plist_rows.append([c["name"], str(k), str(v)])
            except Exception:
                pass

    if plist_rows:
        print("\n--- Preview of downloaded *.plist contents (top-level keys) ---")
        print(tabulate(plist_rows, headers=["Plist", "Key", "Value"], tablefmt="grid", stralign="left"))

    sftp.close()
    ssh.close()
    print("\n[*] Done.")

except Exception as e:
    print(f"Error: {e}")
