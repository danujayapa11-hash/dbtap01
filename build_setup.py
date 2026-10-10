"""Generates buildozer.spec and the Android files (Java receiver, XML), and
patches the manifest template, so the repo only needs .py/.toml/.txt/.yml."""
import pathlib
import subprocess
import tomllib

root = pathlib.Path(".")
cfg = tomllib.loads((root / "pyproject.toml").read_text())["app"]
reqs = [l.strip() for l in (root / "requirements.txt").read_text().splitlines()
        if l.strip() and not l.startswith("#")]
pkg = f'{cfg["domain"]}.{cfg["name"]}'

# --- Java receiver + device admin policy ---
java_dir = root / "java" / pkg.replace(".", "/")
java_dir.mkdir(parents=True, exist_ok=True)
(java_dir / "AdminReceiver.java").write_text(
    f"package {pkg};\n\n"
    "import android.app.admin.DeviceAdminReceiver;\n\n"
    "public class AdminReceiver extends DeviceAdminReceiver {\n}\n")

(root / "res").mkdir(exist_ok=True)
(root / "res" / "device_admin.xml").write_text(
    '<?xml version="1.0" encoding="utf-8"?>\n'
    "<device-admin>\n    <uses-policies>\n        <force-lock />\n"
    "    </uses-policies>\n</device-admin>\n")

# --- Clone python-for-android and insert the receiver into the manifest ---
P4A_TAG = "v2024.01.21"
p4a = root / "python-for-android"
if not p4a.exists():
    subprocess.run(["git", "clone", "--depth", "1", "--branch", P4A_TAG,
                    "https://github.com/kivy/python-for-android.git", str(p4a)],
                   check=True)

receiver = f"""
        <receiver android:name="{pkg}.AdminReceiver"
            android:permission="android.permission.BIND_DEVICE_ADMIN"
            android:exported="true">
            <meta-data android:name="android.app.device_admin"
                android:resource="@xml/device_admin" />
            <intent-filter>
                <action android:name="android.app.action.DEVICE_ADMIN_ENABLED" />
            </intent-filter>
        </receiver>
"""
patched = []
for tmpl in p4a.rglob("AndroidManifest.tmpl.xml"):
    text = tmpl.read_text()
    if "</application>" in text and "AdminReceiver" not in text:
        tmpl.write_text(text.replace("</application>", receiver + "    </application>", 1))
        patched.append(str(tmpl))
assert patched, "Could not find AndroidManifest.tmpl.xml to patch"
print("Patched manifest templates:", *patched, sep="\n  ")

# --- buildozer.spec ---
spec = f"""[app]
title = {cfg["title"]}
package.name = {cfg["name"]}
package.domain = {cfg["domain"]}
source.dir = .
source.include_exts = py,png,jpg,kv
source.exclude_dirs = .github,bin,.buildozer,java,res,python-for-android
version = {cfg["version"]}
requirements = {",".join(reqs)}
orientation = portrait

p4a.source_dir = python-for-android
android.ndk = 25b
android.permissions = WAKE_LOCK
android.api = 33
android.minapi = 24
android.archs = arm64-v8a
android.accept_sdk_license = True

android.add_src = java
android.add_resources = res/device_admin.xml:xml/device_admin.xml

[buildozer]
log_level = 2
warn_on_root = 1
"""
(root / "buildozer.spec").write_text(spec)
print("Generated buildozer.spec for", pkg)
