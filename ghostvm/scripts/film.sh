#!/bin/sh
# Run through: vmx film <app> <out.mov|out.mp4|out.png> [--rect x,y,w,h] [--1x] [--tail MS] <action>...
# Records the app's window at 60 fps (2x pixels; ProRes in .mov, HEVC in .mp4) while the actions run, then copies the
# one file to the host. Also writes <out>.area: the recorded area in screen points (x,y,w,h), for vmx frames and pixels.
# With out.png it keeps no film: it runs the actions, waits for each to settle, then takes a vmx shot (out.png in
# points, where a pixel is a click point, plus out@2x.png).
# Actions:  click NAME real click on the element with that exact name, else the one whose name contains it (looked up when it runs)
#           xy X,Y     real click at a guest screen point (a `shot` pixel)
#           key NAME   press a key in the app (return, escape, cmd+z ...)
#           wheel X,Y DY  scroll the mouse wheel at a point by DY lines, one line at a time (negative scrolls down)
# After every action the film waits until the picture changes and then stays still for 0.3 s (every changed pixel
# counts, even a 1 pt wobble), so nothing sleeps for a guessed time. It warns when an action changed nothing for
# 2 s. Recording starts 0.3 s before the first action and stops --tail ms (default 300) after the last one settles.
# Writes <out>.times.txt: per action, when it ran, when the picture first changed, and when it last changed, in ms
# film time (pts). The film has frames only where pixels changed, so judge timing by frame timestamps, not counts.
# The recorder is built on the host and copied into the guest once. The film runs detached in the guest.
vm="$1"; app="$2"; out="$3"; shift 3
opts=""; tail=300
while :; do
  case "$1" in
    --rect) case "$2" in [0-9]*,[0-9]*,[0-9]*,[0-9]*) ;; *) echo "film: --rect needs x,y,w,h in whole guest points" >&2; exit 2;; esac
            case "$2" in *[!0-9,]*) echo "film: --rect needs x,y,w,h in whole guest points" >&2; exit 2;; esac
            opts="$opts --rect $2"; shift 2;;
    --1x) opts="$opts --1x"; shift;;
    --hevc) shift;;            # old flags: .mp4 is HEVC, .mov is ProRes
    --mbps) shift 2;;
    --tail) case "$2" in ""|*[!0-9]*) echo "film: --tail needs whole milliseconds" >&2; exit 2;; esac; tail="$2"; shift 2;;
    *) break;;
  esac
done
[ -n "$app" ] && [ -n "$out" ] && [ $# -gt 0 ] || { echo "usage: vmx film <app> <out.mov> [--rect x,y,w,h] [--1x] [--tail MS] <click NAME | xy X,Y | key NAME | wheel X,Y DY>..." >&2; exit 2; }
# Time budget: each action gets 40 s (lookup, click, up to 30 s of settling). The film fails at the budget instead of
# running into an agent's 10 min command limit.
budget=$(( 20 + $# * 40 + tail / 1000 ))
[ $budget -le 540 ] || { echo "film: too many actions ($#). Split them into films of 12 or fewer." >&2; exit 2; }
case "$out" in *.mov|*.mp4|*.png) ;; *) echo "film: the output must end in .mov, .mp4, or .png" >&2; exit 2;; esac
here=$(cd "$(dirname "$0")" && pwd)
vmx="$here/vmx"
# The host binary name holds a hash of the source and the build target. Built for macOS 14, so older guests run it too.
target=arm64-apple-macos14
hash=$( (cat "$here/film.swift"; echo "$target") | /sbin/md5 -q | cut -c1-12)
G=/tmp/.vmx-film
ext=${out##*.}; look=""
# The guest never uses its own video encoder (it can hang until the guest restarts). For a film the recorder keeps
# LZ4-packed raw frames and the host encodes them. For a .png it keeps nothing and only watches for changes.
# The guest recorder always lives at one path: the guest's Screen Recording approval names that path, so a new build
# copied over it keeps the approval. $GB.version says which build is there.
GB=$G/film-694607049b7e
# A .png keeps no film: a small HEVC film runs in the guest only to see when each action settles.
if [ "$ext" = png ]; then look=1; opts="$opts --codec none"; else opts="$opts --codec raw"; fi

# 1. The recorder: build it on the host once, copy it into the guest once.
bin="${TMPDIR:-/tmp}/vmx-film-$hash"
if [ ! -x "$bin" ]; then
  echo "film: building the recorder (once)" >&2
  swiftc -O -target $target "$here/film.swift" -o "$bin.tmp" >/dev/null 2>&1 && mv "$bin.tmp" "$bin" \
    || { echo "film: building the recorder failed. It needs the Xcode command line tools on the host." >&2; exit 3; }
fi
have=$("$vmx" -n "$vm" sh "/bin/cat $GB.version 2>/dev/null; true") || exit $?
if [ "$have" != "$hash" ]; then
  "$vmx" -n "$vm" sh "/bin/mkdir -p $G" >/dev/null || exit $?
  "$vmx" -n "$vm" push "$bin" "$GB.new" >/dev/null || exit $?
  "$vmx" -n "$vm" sh "/bin/chmod +x $GB.new && /bin/mv -f $GB.new $GB && echo $hash > $GB.version" >/dev/null || exit $?
fi

# 2. The steps, as shell lines for the guest.
q() { printf "'%s'" "$(printf '%s' "$1" | sed "s/'/'\\\\''/g")"; }
steps=""
for a in "$@"; do
  case "$a" in
    "click "*) steps="$steps
p=\$(findpt $(q "$app") $(q "${a#click }")); case \$p in [0-9]*,[0-9]*) act $(q "$a") \$A --headed mouse-click --xy \$p; printf 'film: \"%s\" is at %s. While the window stays the same, use xy %s instead: finding a name takes 1 to 5 s.\\n' $(q "${a#click }") \$p \$p;; *) miss $(q "$a") \"\$p\";; esac";;
    "xy "*) p=${a#xy }; case "$p" in *[!0-9,]*|'') echo "film: bad point \"$p\" (use xy X,Y)" >&2; exit 2;; esac
            steps="$steps
act \"xy $p\" \$A --headed mouse-click --xy $p";;
    "key "*) steps="$steps
act $(q "$a") \$A press $(q "${a#key }") --app $(q "$app")";;
    "wheel "*) w=${a#wheel }; p=${w%% *}; dy=${w#* }
            case "$p" in *[!0-9,]*|''|*,*,*) p=bad;; *,*) ;; *) p=bad;; esac
            case "$dy" in -[1-9]|-[1-9][0-9]|[1-9]|[1-9][0-9]) ;; *) p=bad;; esac
            [ "$p" = bad ] && { echo "film: bad wheel action \"$a\" (use wheel X,Y DY: DY lines from -99 to 99, negative scrolls down)" >&2; exit 2; }
            one=1; n=$dy; case "$dy" in -*) one=-1; n=${dy#-};; esac
            steps="$steps
act $(q "$a") /bin/sh -c 'i=0; while [ \$i -lt $n ]; do \$0 mouse-wheel --x ${p%,*} --y ${p#*,} --dy=$one --headed || exit 1; i=\$((i+1)); done' \$A";;
    *) echo "film: unknown action \"$a\" (use: click NAME | xy X,Y | key NAME | wheel X,Y DY). There is no wait: every action waits for the picture to settle." >&2; exit 2;;
  esac
done

script="A=\$HOME/.local/bin/agent-desktop; G=$G
ms() { /usr/bin/perl -MTime::HiRes=time -e 'printf \"%d\", time*1000'; }
T=\$G/tick
/bin/cat > \$G/settle.pl <<'PERL'
$(cat "$here/settle.pl")
PERL
# findpt APP NAME: the click point of the element with that exact name, else of the elements whose name contains it;
# only when they all share one point. Otherwise says why there is none.
findpt() (
$LIST
printf '%s' \"\$ELS\" | /usr/bin/jq -r --arg n \"\$2\" '(\$n | ascii_downcase) as \$n | [.[] | select((.name | ascii_downcase) == \$n)] as \$e | (if (\$e | length) > 0 then \$e else [.[] | select(.name | ascii_downcase | contains(\$n))] end) | (map(\"\\(.x),\\(.y)\") | unique) as \$p | if (\$p | length) == 1 then \$p[0] else \"\\(\$p | length) on-screen places match that name\" end'
)
fail() { echo \"\$1\"; /bin/cat \$G/log; /usr/bin/pkill -9 -f $GB; echo failed > \$G/status; exit 1; }
/bin/rm -f \$G/stop \$G/log \$G/status \$G/out.frames \$G/times \$T
\$A focus-window --app $(q "$app") > /dev/null 2>&1; /bin/sleep 0.3   # bring the app to the front, so the film and the clicks hit it
($GB \$G/out.frames $budget --app $(q "$app") $opts --stop \$G/stop --tick \$T > \$G/log 2>&1 &)
S0=\$(ms); while ! /usr/bin/grep -q '^recording' \$G/log 2>/dev/null; do
  /usr/bin/grep -q '^film:' \$G/log 2>/dev/null && fail 'film: the recorder failed:'
  [ \$(( \$(ms) - S0 )) -gt 10000 ] && fail 'film: the recorder did not start in 10 s:'
  /bin/sleep 0.05; done
T0=\$(/usr/bin/awk '/^recording/{print \$2}' \$G/log)
act() { n=\$1; shift; e=\$(/usr/bin/perl -MTime::HiRes=time -e 'printf \"%.3f\", time'); s=\$(( \$(ms) - T0 )); /bin/rm -f \$G/done; (\"\$@\" > /dev/null 2>&1; /usr/bin/touch \$G/done) & R=\$(/usr/bin/perl \$G/settle.pl \$T \$e \$T0 \$G/done); wait; echo \"\$s ms: \$n | \$R\" >> \$G/times; case \$R in NO*|*STILL*) echo \"film: warning: \$n: \$R\";; esac; }
miss() { echo \"\$(( \$(ms) - T0 )) ms: \$1 | NOT CLICKED: \$2\" >> \$G/times; echo \"film: warning: \$1: not clicked: \$2. Run vmx ui for the names on screen.\"; }
/bin/sleep 0.3
$steps
/bin/sleep $(awk "BEGIN{print $tail/1000}")
/usr/bin/touch \$G/stop
i=0; while ! /usr/bin/grep -q '^saved' \$G/log 2>/dev/null; do
  i=\$((i+1)); [ \$i -gt 300 ] && fail 'film: the recorder did not finish in 15 s:'
  /bin/sleep 0.05; done
echo ok > \$G/status"

# 3. Run it detached in the guest, poll until it ends, then copy the film out.
b64=$(printf '%s' "$script" | base64 | tr -d '\n')
"$vmx" -n "$vm" sh "printf %s '$b64' | /usr/bin/base64 -d > $G/run.sh && /bin/rm -f $G/status && (/usr/bin/nohup /bin/sh $G/run.sh > $G/run.log 2>&1 &); echo started" >/dev/null || exit $?
waited=0
while :; do
  st=$("$vmx" -n "$vm" sh "/bin/cat $G/status 2>/dev/null; true") || exit $?
  [ -n "$st" ] && break
  waited=$((waited + 1))
  if [ $waited -gt $(( (budget + 15) * 2 )) ]; then
    "$vmx" -n "$vm" sh "/usr/bin/pkill -f $G/run.sh; /usr/bin/pkill -9 -f $GB; /bin/cat $G/run.log $G/log 2>/dev/null; true" >&2
    echo "film: no result after $((budget + 15)) s, so it stopped the film in the guest. Take a shot and look." >&2; exit 6
  fi
  sleep 0.5
done
"$vmx" -n "$vm" sh "/bin/cat $G/run.log; true"
[ "$st" = ok ] || exit 1
info=$("$vmx" -n "$vm" sh "/usr/bin/awk '/^recording/{print \$4; exit}' $G/log; /bin/cat $G/times 2>/dev/null; true")
printf '%s\n' "$info" | sed 1d > "$out.times.txt"
area=$(printf '%s\n' "$info" | sed -n 1p)
if [ -n "$look" ]; then
  # out.png: the screen once everything settled, as a normal shot.
  "$vmx" -n "$vm" shot "$out" || exit $?
  echo "What each action did (also in $out.times.txt):"; cat "$out.times.txt"; exit 0
fi
tmp=$(mktemp -d "${TMPDIR:-/tmp}/vmx-film.XXXXXX") || exit 1
"$vmx" -n "$vm" pull "$G/out.frames" "$tmp/frames" >/dev/null || { rm -rf "$tmp"; exit 1; }
"$bin" --encode "$tmp/frames" "$out" >/dev/null || { rm -rf "$tmp"; echo "film: could not encode the frames on the host" >&2; exit 1; }
rm -rf "$tmp"
# The last frame at full pixels, so the result can be checked without a separate screenshot. Seeking straight to the
# last frame's time takes under a second; decoding the last 3 s took about 5.
lastframe() {
  command -v ffmpeg >/dev/null || return 1
  rm -f "$2"
  lp=$(ffprobe -v error -select_streams v:0 -show_entries packet=pts_time -of csv=p=0 "$1" 2>/dev/null | sort -n | tail -1)
  [ -n "$lp" ] && ffmpeg -v error -y -ss "$lp" -i "$1" -frames:v 1 "$2" 2>/dev/null
  [ -s "$2" ] || ffmpeg -v error -y -sseof -3 -i "$1" -fps_mode passthrough -update 1 "$2" || return 1
  sips -s dpiWidth 144 -s dpiHeight 144 "$2" >/dev/null
}
printf '%s\n' "$area" > "$out.area"
if lastframe "$out" "$out.png"; then last=" Last frame: $out.png."; else last=" No last frame: ffmpeg is not on the host."; fi
frames=$(ffprobe -v error -select_streams v:0 -count_packets -show_entries stream=nb_read_packets,width,height -of csv=p=0 "$out" 2>/dev/null)
echo "film: $out ($frames: width,height,frames), area $area in screen points.$last What each action did (also in $out.times.txt):"
cat "$out.times.txt"
