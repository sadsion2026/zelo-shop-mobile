import os
import sys
import json
import base64
import datetime
import urllib.request
import urllib.error

TOKEN = os.environ.get("RELEASE_PAT") or os.environ.get("GITHUB_TOKEN")
if not TOKEN:
    print("Neither RELEASE_PAT nor GITHUB_TOKEN found in environment, skipping publish.")
    sys.exit(0)

TARGET_REPO = os.environ.get("GITHUB_REPOSITORY", "sadsion2026/zelo-shop-mobile")
IPA_PATH = sys.argv[1] if len(sys.argv) > 1 else "ios/output/ZeloShop.ipa"

if not os.path.exists(IPA_PATH):
    print(f"Error: IPA file not found at {IPA_PATH}")
    sys.exit(1)

file_size = os.path.getsize(IPA_PATH)

# Release timestamp: set 5 minutes in past relative to current UTC so AltStore accepts it immediately
utc_now = datetime.datetime.now(datetime.timezone.utc)
release_timestamp_iso = (utc_now - datetime.timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")

# Extract version from app.json
version = "1.0.0"
if os.path.exists("app.json"):
    try:
        with open("app.json", "r", encoding="utf-8") as f:
            app_data = json.load(f)
            version = app_data.get("expo", {}).get("version", "1.0.0")
    except Exception as e:
        print(f"Warning reading app.json: {e}")

tag_name = f"v{version}"
print(f"Publishing release for {TARGET_REPO}, Version: {version}, Tag: {tag_name}, Size: {file_size} bytes")

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "User-Agent": "Antigravity-CI-Publisher"
}

release_id = None
upload_url = None
try:
    req = urllib.request.Request(f"https://api.github.com/repos/{TARGET_REPO}/releases/tags/{tag_name}", headers=headers)
    with urllib.request.urlopen(req) as resp:
        rel_data = json.loads(resp.read().decode())
        release_id = rel_data["id"]
        upload_url = rel_data["upload_url"].split("{")[0]
        print(f"Found existing release ID: {release_id}")
except urllib.error.HTTPError as e:
    if e.code == 404:
        print(f"Release {tag_name} does not exist yet. Creating...")
    else:
        raise

release_notes = f"""### Zelo Shop v{version} (AltStore / iOS Release)

- 🚀 **تشغيل فوري وتلقائي**: التطبيق مدمج بالكامل ويعمل بدون سيرفر أو اتصال بالكمبيوتر.
- 🟣 **شعار جديد عالي الدقة**: أيقونة الصاعقة البنفسجية 1024x1024.
- 🎮 **المتجر والأقسام**: قسم الألعاب (PlayStation, Xbox Game Pass, Steam) وقسم الاشتراكات والبرامج.
- 📦 **تفاصيل المنتج ثلاثية الأبعاد**: عرض مجسم Xbox ثلاثي الأبعاد واختيار مدد الاشتراك.
- 💳 **طرق الدفع**: دعم الدفع المباشر عبر زين كاش، كي كارد، فيزا، ماستركارد، ومحفظة المتجر.
- 🔐 **Digital Vault**: شاشة تأكيد الطلب مع مؤثرات الاحتفال واستلام الكود داخل الخزنة الرقمية."""

if not release_id:
    create_payload = json.dumps({
        "tag_name": tag_name,
        "name": f"Zelo Shop v{version} (Release Edition)",
        "body": release_notes,
        "draft": False,
        "prerelease": False
    }).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.github.com/repos/{TARGET_REPO}/releases",
        data=create_payload,
        method="POST",
        headers={**headers, "Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        rel_data = json.loads(resp.read().decode())
        release_id = rel_data["id"]
        upload_url = rel_data["upload_url"].split("{")[0]
        print(f"Created new release ID: {release_id}")

# Check and remove old asset with same name if it exists
try:
    assets_req = urllib.request.Request(f"https://api.github.com/repos/{TARGET_REPO}/releases/{release_id}/assets", headers=headers)
    with urllib.request.urlopen(assets_req) as resp:
        assets = json.loads(resp.read().decode())
        for asset in assets:
            if asset["name"] == "ZeloShop.ipa":
                print(f"Deleting existing ZeloShop.ipa asset (ID: {asset['id']})...")
                del_req = urllib.request.Request(f"https://api.github.com/repos/{TARGET_REPO}/releases/assets/{asset['id']}", headers=headers, method="DELETE")
                urllib.request.urlopen(del_req)
                print("Deleted old asset.")
except Exception as e:
    print(f"Note while checking existing assets: {e}")

print(f"Uploading {IPA_PATH} ({file_size / (1024*1024):.2f} MB)...")
with open(IPA_PATH, "rb") as f:
    ipa_data = f.read()

up_headers = {
    **headers,
    "Content-Type": "application/octet-stream"
}
up_req = urllib.request.Request(f"{upload_url}?name=ZeloShop.ipa", data=ipa_data, method="POST", headers=up_headers)
with urllib.request.urlopen(up_req) as resp:
    print(f"IPA successfully uploaded to release! Status: {resp.status}")

download_url = f"https://github.com/{TARGET_REPO}/releases/download/{tag_name}/ZeloShop.ipa"

# Update altstore_source.json in repository
source_url = f"https://api.github.com/repos/{TARGET_REPO}/contents/altstore_source.json"
req = urllib.request.Request(source_url, headers=headers)
try:
    with urllib.request.urlopen(req) as resp:
        src_file_data = json.loads(resp.read().decode())
        src_sha = src_file_data["sha"]
        src_json = json.loads(base64.b64decode(src_file_data["content"]).decode("utf-8"))
except Exception as e:
    print(f"Could not fetch existing altstore_source.json ({e}), using template.")
    src_sha = None
    with open("altstore_source.json", "r", encoding="utf-8") as f:
        src_json = json.load(f)

app = src_json["apps"][0]
release_desc = f"v{version}: تطبيق Zelo Shop الرسمي المستقل للألعاب والاشتراكات والدفع الإلكتروني."
app["version"] = version
app["versionDate"] = release_timestamp_iso
app["downloadURL"] = download_url
app["size"] = file_size

version_entry = {
    "version": version,
    "date": release_timestamp_iso,
    "downloadURL": download_url,
    "size": file_size,
    "localizedDescription": release_desc
}

if "versions" not in app:
    app["versions"] = []
app["versions"] = [v for v in app["versions"] if v.get("version") != version]
app["versions"].insert(0, version_entry)

new_content_b64 = base64.b64encode(json.dumps(src_json, ensure_ascii=False, indent=2).encode("utf-8")).decode("ascii")
put_payload = {
    "message": f"release: update altstore_source.json for v{version} [skip ci]",
    "content": new_content_b64,
    "branch": "main"
}
if src_sha:
    put_payload["sha"] = src_sha

put_req = urllib.request.Request(source_url, data=json.dumps(put_payload).encode("utf-8"), method="PUT", headers={**headers, "Content-Type": "application/json"})
with urllib.request.urlopen(put_req) as resp:
    print(f"altstore_source.json successfully updated on {TARGET_REPO}! Status: {resp.status}")

print("All AltStore release steps completed successfully!")
