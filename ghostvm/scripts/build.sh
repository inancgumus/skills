#!/bin/sh
# Run through vmx (host only, never touches the guest):
#   vmx build <project-dir> <product> <out.app> --id BUNDLE-ID [--name NAME] [--plist FILE] [--then LINE] [--release]
#   vmx build <project-dir> --scheme SCHEME <out.app> [--release]
#   vmx test <project-dir> (--filter NAME | --all) [--scheme SCHEME]
# build: builds the debug configuration (it looks the same on screen as release and builds several times faster) and
# makes a signed .app to hand to `vmx app`. SwiftPM: the product's binary goes to Contents/MacOS, its resource bundles to
# Contents/Resources, --plist (else a minimal Info.plist with --id and --name) to Contents/Info.plist, then --then runs
# (with $APP set to the .app, for project steps such as an icon), then it signs with the same identity every time: the
# first "Apple Development" identity, else ad hoc. Xcode (--scheme): xcodebuild Debug, then the built .app is copied.
# test: --filter runs only the tests for the code you changed; --all runs the whole suite, once, at the end.
# Every build and test on this Mac takes one shared lock, so agents take turns instead of slowing each other down.
# Output: errors only, then one line with the time spent and the time waited for the lock.
cmd="$1"; shift
die() { echo "vmx $cmd: $1" >&2; exit 2; }
dir="${1%/}"; shift 2>/dev/null
[ -d "$dir" ] || die "no project folder \"$dir\""
product=""; scheme=""; out=""; id=""; name=""; plist=""; then_=""; conf=debug; filter=""; all=""
while [ $# -gt 0 ]; do
  case "$1" in
    --scheme) scheme="$2"; shift 2;;
    --id) id="$2"; shift 2;;
    --name) name="$2"; shift 2;;
    --plist) plist="$2"; shift 2;;
    --then) then_="$2"; shift 2;;
    --release) conf=release; shift;;
    --filter) filter="$2"; shift 2;;
    --all) all=1; shift;;
    -*) die "unknown option $1";;
    *) if [ "$cmd" = build ] && [ -z "$scheme" ] && [ -z "$product" ]; then product="$1"; else out="$1"; fi; shift;;
  esac
done
jobs="${VMX_BUILD_JOBS:-$(( $(sysctl -n hw.ncpu) / 2 ))}"; [ "$jobs" -ge 1 ] || jobs=1
lock="${VMX_BUILD_LOCK:-/tmp/vmx-build.lock}"
t0=$(date +%s)
# locked CMD...: runs CMD while holding the shared lock; writes when it got the lock to $tmp.got.
tmp=$(mktemp "${TMPDIR:-/tmp}/vmx-build.XXXXXX") || exit 1
trap 'rm -f "$tmp" "$tmp.got"' EXIT
locked() { /usr/bin/lockf -t 1800 "$lock" /bin/sh -c 'date +%s > "$0.got"; exec "$@"' "$tmp" "$@"; }
# errors CMD...: runs CMD, keeps its output, and on failure prints only the error lines (all of it if none match).
errors() {
  "$@" > "$tmp" 2>&1; rc=$?
  if [ $rc -ne 0 ]; then
    grep -E 'error:|error |fatal|FAILED|failed|Test Case .* failed|✘' "$tmp" | grep -v '^warning' | sort -u | head -40 >&2
    grep -q -E 'error|fail' "$tmp" || tail -40 "$tmp" >&2
  fi
  return $rc
}
waited() { got=$(cat "$tmp.got" 2>/dev/null || echo "$t0"); echo "$(( $(date +%s) - got )) s, after $(( got - t0 )) s waiting for the build lock"; }

case "$cmd" in
build)
  [ -n "$out" ] && case "$out" in *.app) ;; *) false;; esac || die "usage: vmx build <project-dir> <product> <out.app> --id BUNDLE-ID [--name NAME] [--plist FILE] [--then LINE] [--release]   or   vmx build <project-dir> --scheme SCHEME <out.app> [--release]"
  case "$out" in /*) ;; *) out="$PWD/$out";; esac
  if [ -n "$scheme" ]; then
    C=Debug; [ $conf = release ] && C=Release
    dd="$dir/.build/xcode"
    errors locked /bin/sh -c 'cd "$1" && xcodebuild -scheme "$2" -configuration "$3" -derivedDataPath "$4" -jobs "$5" -quiet build' _ "$dir" "$scheme" "$C" "$dd" "$jobs" || { echo "vmx build: the build failed" >&2; exit 1; }
    src=$(/bin/ls -d "$dd/Build/Products/$C"/*.app 2>/dev/null | head -1)
    [ -n "$src" ] || die "xcodebuild made no .app in $dd/Build/Products/$C"
    rm -rf "$out" && ditto "$src" "$out" || exit 1
  else
    [ -f "$dir/Package.swift" ] || die "$dir has no Package.swift (for an Xcode project, pass --scheme)"
    [ -n "$product" ] && [ -n "$id" ] || die "SwiftPM needs the product name and --id BUNDLE-ID"
    exe=$(basename "$out" .app | tr -d ' ')
    errors locked /bin/sh -c 'cd "$1" && swift build -c "$2" --product "$3" -j "$4" --quiet' _ "$dir" "$conf" "$product" "$jobs" || { echo "vmx build: the build failed" >&2; exit 1; }
    bins=$(cd "$dir" && swift build -c "$conf" --show-bin-path) || exit 1
    rm -rf "$out" && mkdir -p "$out/Contents/MacOS" "$out/Contents/Resources" || exit 1
    cp "$bins/$product" "$out/Contents/MacOS/$exe" || die "no binary $bins/$product (is $product an executable product?)"
    for b in "$bins"/*.bundle; do [ -d "$b" ] && ditto "$b" "$out/Contents/Resources/$(basename "$b")"; done
    if [ -n "$plist" ]; then cp "$plist" "$out/Contents/Info.plist" || exit 1
      /usr/libexec/PlistBuddy -c "Set :CFBundleExecutable $exe" "$out/Contents/Info.plist" 2>/dev/null || /usr/libexec/PlistBuddy -c "Add :CFBundleExecutable string $exe" "$out/Contents/Info.plist"
      /usr/libexec/PlistBuddy -c "Set :CFBundleIdentifier $id" "$out/Contents/Info.plist" 2>/dev/null || /usr/libexec/PlistBuddy -c "Add :CFBundleIdentifier string $id" "$out/Contents/Info.plist"
    else
      cat > "$out/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleExecutable</key><string>$exe</string>
<key>CFBundleIdentifier</key><string>$id</string>
<key>CFBundleName</key><string>${name:-$exe}</string>
<key>CFBundleDisplayName</key><string>${name:-$exe}</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>CFBundleShortVersionString</key><string>1.0</string>
<key>CFBundleVersion</key><string>1</string>
<key>LSMinimumSystemVersion</key><string>14.0</string>
<key>NSHighResolutionCapable</key><true/>
<key>NSPrincipalClass</key><string>NSApplication</string>
</dict></plist>
EOF
    fi
    if [ -n "$then_" ]; then (cd "$dir" && APP="$out" /bin/sh -c "$then_") || { echo "vmx build: the --then line failed" >&2; exit 1; }; fi
    sign=$(security find-identity -p codesigning -v 2>/dev/null | sed -n 's/.*"\(Apple Development[^"]*\)".*/\1/p' | head -1)
    codesign --force --sign "${sign:--}" --identifier "$id" "$out" 2>"$tmp" || { cat "$tmp" >&2; echo "vmx build: signing failed" >&2; exit 1; }
  fi
  echo "built $out ($conf) in $(waited). Next: \$S job '\$S app $out ... && \$S film ...'";;
test)
  [ -n "$filter" ] || [ -n "$all" ] || die "pass --filter NAME to run the tests for the code you changed, or --all to run the whole suite once, at the end"
  [ -n "$filter" ] && [ -n "$all" ] && die "pass --filter or --all, not both"
  if [ -n "$scheme" ]; then
    set -- xcodebuild -scheme "$scheme" -derivedDataPath "$dir/.build/xcode" -jobs "$jobs" -quiet test; [ -n "$filter" ] && set -- "$@" -only-testing:"$filter"
  else
    [ -f "$dir/Package.swift" ] || die "$dir has no Package.swift (for an Xcode project, pass --scheme)"
    set -- swift test -j "$jobs"; [ -n "$filter" ] && set -- "$@" --filter "$filter"
  fi
  if errors locked /bin/sh -c 'cd "$0" && exec "$@"' "$dir" "$@"; then
    n=$(grep -E -o 'Executed [0-9]+ tests?|[0-9]+ tests? (passed|in [0-9]+ suites? passed)' "$tmp" | tail -1)
    [ -n "$filter" ] && ! grep -q -E 'Executed [1-9]|[1-9][0-9]* tests?' "$tmp" && { echo "vmx test: no test matched --filter $filter" >&2; exit 1; }
    echo "tests passed${n:+ ($n)} in $(waited)"
  else
    echo "vmx test: tests failed (lines above) after $(waited)" >&2; exit 1
  fi;;
*) die "unknown command";;
esac
