"""Generates buildozer.spec and the Android files (Java receiver, XML)
so the repo only needs .py, .toml, .txt and .yml files."""
import pathlib
import tomllib

root = pathlib.Path(".")
cfg = tomllib.loads((root / "pyproject.toml").read_text())["app"]
reqs = [l.strip() for l in (root / "requirements.txt").read_text().splitlines()
        if l.strip() and not l.startswith("#")]
pkg = f'{cfg["domain"]}.{cfg["name"]}'

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

(root / "manifest_extra.xml").write_text(
    f'<receiver android:name="{pkg}.AdminReceiver"\n'
    '    android:permission="android.permission.BIND_DEVICE_ADMIN"\n'
    '    android:exported="true">\n'
    '    <meta-data android:name="android.app.device_admin"\n'
    '        android:resource="@xml/device_admin" />\n'
    "    <intent-filter>\n"
    '        <action android:name="android.app.action.DEVICE_ADMIN_ENABLED" />\n'
    "    </intent-filter>\n</receiver>\n")

spec = f"""[app]
title = {cfg["title"]}
package.name = {cfg["name"]}
package.domain = {cfg["domain"]}
source.dir = .
source.include_exts = py,png,jpg,kv
source.exclude_dirs = .github,bin,.buildozer,java,res
version = {cfg["version"]}
requirements = {",".join(reqs)}
orientation = portrait

p4a.branch = v2024.01.21
android.ndk = 25b
android.permissions = WAKE_LOCK
android.api = 33
android.minapi = 24
android.archs = arm64-v8a
android.accept_sdk_license = True

android.add_src = java
android.add_resources = res/device_admin.xml:xml/device_admin.xml
android.extra_manifest_application_arguments = manifest_extra.xml

[buildozer]
log_level = 2
warn_on_root = 1
"""
(root / "buildozer.spec").write_text(spec)
print("Generated buildozer.spec for", pkg)
