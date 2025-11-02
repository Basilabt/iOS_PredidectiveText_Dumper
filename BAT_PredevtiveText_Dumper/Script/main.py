#!/usr/bin/env python3
import os
import io
import sys
import fnmatch
import stat
import base64
import binascii
import sqlite3
import plistlib
import paramiko
from getpass import getpass
from datetime import datetime
from art import tprint

tprint("BAT PredictiveText Dumper")
print("by @Basel AbuTaleb\n\n")

host = input("[+] Enter device IP or hostname: ")
port = int(input("[+] Enter SSH port (default 22): ") or 22)
username = input("[+] Enter SSH username: ")
password = getpass("[+] Enter SSH password: ")

REMOTE_BASE = "/private/var/mobile/Library/Keyboard"
DIRS_TO_GET = ["en-dynamic.lm", "ar-dynamic.lm"]
DBS = ["user_model_database.sqlite", "langlikelihood.dat"]

def quote(p):
    return "'" + p.replace("'", "'\"'\"'") + "'"

def ensure_dir(p):
    os.makedirs(p, exist_ok=True)

def s_isdir(sftp, path):
    st = sftp.lstat(path)
    return stat.S_ISDIR(st.st_mode)

def s_list(sftp, path):
    for e in sftp.listdir_attr(path):
        yield e.filename

def s_download_file_sftp_or_stream(ssh, sftp, rpath, lpath):
    try:
        sftp.get(rpath, lpath)
        return True
    except Exception:
        try:
            cmd = f"base64 -w 0 {quote(rpath)}"
            _, out, err = ssh.exec_command(cmd)
            b64 = out.read()
            if not b64:
                return False
            data = base64.b64decode(b64)
            with open(lpath, "wb") as f:
                f.write(data)
            return True
        except Exception:
            return False

def s_download_dir(ssh, sftp, rdir, ldir):
    ensure_dir(ldir)
    for name in s_list(sftp, rdir):
        rpath = f"{rdir.rstrip('/')}/{name}"
        lpath = os.path.join(ldir, name)
        if s_isdir(sftp, rpath):
            s_download_dir(ssh, sftp, rpath, lpath)
        else:
            s_download_file_sftp_or_stream(ssh, sftp, rpath, lpath)

def merge_and_dump_sqlite(db_path):
    try:
        wal = db_path + "-wal" if db_path.endswith(".sqlite") else db_path + "-wal"
        shm = db_path + "-shm" if db_path.endswith(".sqlite") else db_path + "-shm"
        base = os.path.basename(db_path)
        root, ext = os.path.splitext(base)
        out_db = os.path.join(os.path.dirname(db_path), f"{root}_full.db")
        con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        b = sqlite3.connect(out_db)
        con.backup(b)
        b.commit(); b.close(); con.close()
        dump_sql = os.path.join(os.path.dirname(db_path), f"{root}_dump.sql")
        c = sqlite3.connect(out_db)
        with open(dump_sql, "w", encoding="utf-8") as f:
            for line in c.iterdump():
                f.write(f"{line}\n")
        c.close()
    except Exception:
        pass

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port=port, username=username, password=password, timeout=20)
    sftp = ssh.open_sftp()

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.join(os.getcwd(), f"predictive_text_dump_{stamp}")
    ensure_dir(out_dir)

    for d in DIRS_TO_GET:
        rdir = f"{REMOTE_BASE}/{d}"
        try:
            if s_isdir(sftp, rdir):
                s_download_dir(ssh, sftp, rdir, os.path.join(out_dir, d))
        except Exception:
            pass

    for db in DBS:
        rfile = f"{REMOTE_BASE}/{db}"
        lfile = os.path.join(out_dir, db)
        s_download_file_sftp_or_stream(ssh, sftp, rfile, lfile)
        for suf in ("-wal", "-shm"):
            s_download_file_sftp_or_stream(ssh, sftp, rfile + suf, lfile + suf)
        merge_and_dump_sqlite(lfile)

    try: sftp.close()
    except Exception: pass
    try: ssh.close()
    except Exception: pass
except Exception:
    try: sftp.close()
    except Exception: pass
    try: ssh.close()
    except Exception: pass
    sys.exit(1)
