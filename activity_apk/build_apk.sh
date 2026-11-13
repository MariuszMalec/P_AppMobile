#!/bin/bash
set -e

cd ~/projects/P_AppMobile/activity_react
npm run build

cd ~/projects/P_AppMobile/activity_apk
bash gradlew assembleDebug --rerun-tasks
cp app/build/outputs/apk/debug/*.apk ~/storage/downloads/Activity-debug.apk
echo "Gotowe: ~/storage/downloads/Activity-debug.apk"
