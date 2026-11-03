#!/bin/sh
# ACM 메뉴바 앱을 빌드해서 /Applications/ACM.app 에 설치한다.
set -eu
cd "$(dirname "$0")"

APP=build/ACM.app
rm -rf build
mkdir -p "$APP/Contents/MacOS"
cp Info.plist "$APP/Contents/Info.plist"

swiftc -O -parse-as-library -swift-version 5 \
  -target arm64-apple-macos14.0 \
  -o "$APP/Contents/MacOS/ACM" Sources/*.swift

codesign --force --sign - "$APP"

DEST="/Applications/ACM.app"

osascript -e 'tell application "ACM" to quit' >/dev/null 2>&1 || true
sleep 1
rm -rf "$DEST"
cp -R "$APP" "$DEST"
echo "설치: $DEST"
