#!/bin/sh
# Build the ACM menu bar app and install it to /Applications/ACM.app.
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
echo "Installed: $DEST"
