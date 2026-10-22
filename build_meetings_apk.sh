#!/data/data/com.termux/files/usr/bin/bash
set -e

ROOT=~/projects/P_AppMobile
GRADLE_FILE="$ROOT/Meetings_apk/app/build.gradle"

echo "=== 1/4 Build Reacta ==="
cd "$ROOT/Meetings_react"
npm run build

echo "=== 2/4 Podnoszenie versionCode ==="
n=$(grep -oE 'versionCode [0-9]+' "$GRADLE_FILE" | grep -oE '[0-9]+')
if [ -z "$n" ]; then
  echo "BLAD: nie znaleziono liczbowego versionCode w build.gradle"
  exit 1
fi
new=$((n+1))
sed -i "s/versionCode $n/versionCode $new/" "$GRADLE_FILE"
sed -i "s/versionName '[^']*'/versionName '1.0.$new'/" "$GRADLE_FILE"
echo "versionCode: $n -> $new"

echo "=== 3/4 Build APK ==="
cd "$ROOT/Meetings_apk"
bash gradlew assembleRelease --rerun-tasks

echo "=== 4/4 Kopiowanie do Pobranych ==="
cp app/build/outputs/apk/release/app-release.apk ~/storage/downloads/Meetings.apk
ls -la ~/storage/downloads/Meetings.apk

echo "GOTOWE: otworz Meetings.apk z Pobranych i kliknij Aktualizuj"
