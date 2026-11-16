---
name: ghostvm
description: Use GhostVM (`vmctl`) to run commands and drive apps inside a macOS VM. Use when a task mentions GhostVM, vmctl, or testing in a VM.
---

# GhostVM

GhostVM runs a macOS guest on Apple's Virtualization framework. GUI tests and web browsing run there, not on the host desktop: no stolen focus, no access to real data. The only CLI is `vmctl` (there is no `ghostvm` command). Do everything through `scripts/vmx`, which sits next to this file. Follow this file exactly. Skip `--help` and old transcripts. Assume the VM is running and set up, run the task, and look at *When a command fails* only when something fails.

Set `S=<this skill's dir>/scripts/vmx` (needs `jq` on the host). Pass `-n <VM>` or set `$VM` to pick a VM. With one VM listed, `vmx` finds it.

`vmx` finds the VM and checks ssh by itself, so don't run `vmctl list` or `ssh` first. It is fast only with ssh to the guest (see *Setup*). Then every command takes about 0.2 s, a screenshot under 1 s, and files move at full speed. GhostTools `exec` sometimes hangs 30 s per call ([GhostVM issue #268](https://github.com/groundwater/GhostVM/issues/268)), so `vmx` uses it once to start a small helper (`scripts/vmxd.pl`) in the guest's GUI session and sends every command through that helper over ssh. Never call `vmctl remote exec` yourself. Run one `vmx` command per shell call, or several as one `$S job`. Over ssh, each call stops after 600 s (`VMX_TIMEOUT`), so run longer jobs detached.

## Never

* Use any VM tool except GhostVM. Never install or create VMs with tart, lume, or containers.
* Launch, kill, capture, or drive anything on the host when told to use the VM. Host tools (`cliclick`, `osascript`, screen capture) are off limits for the guest. Processing a film on the host with `ffmpeg` is fine.
* Bring the VM window to the front, or click it with host computer-use tools.
* Drive the guest UI with anything but `vmx` and agent-desktop.
* Create a new key or keychain item for an app the guest already knows (see *Stuck dialogs*).
* Take a project's own lock for the guest by hand, or wait for the guest in a foreground loop of `sleep`. `vmx` holds the guest for you (see *Share the guest*).
* Put a password in a command argument. Anything that needs root needs the user's admin password, so ask the user.

## Commands

| Command | What it does |
|---|---|
| `$S apps` | Lists running GUI app names. Use these exact names everywhere. |
| `$S ui <app> [text]` | Lists what you can click in the app right now: role, name, click point `x,y`, size. Skips off-screen and tiny elements. With `text`, lists only names that contain it (any case), so don't pipe it through `grep` or `head`. |
| `$S click <app> <name> [role]` | Finds the one on-screen element with that exact name and clicks it, all in one call. Prints the click point. |
| `$S clickxy <x> <y>` | Physical click at a guest screen point. Takes guest focus, so use it only when you hold the guest alone. Whatever is on top at that point gets the click, so take a screenshot first. |
| `$S shot <file.png>` | Screenshot of the whole guest screen in under 1 s. Saves two files on the host: `<file>.png` at the display's size in points, where a pixel is a click point for `clickxy` and a corner for `film --rect` (read this one), and `<file>@2x.png` at full Retina pixels (for people, and for checking fine detail in a small crop). |
| `$S app <host.app> [--fresh] [--before '<line>'] [-- args...]` | Needs ssh. Copies the app into the guest at `/tmp/vmx-app/<name>.app` (the same path every time), quits the copy already running the way a person does (Cmd-Q, forced after 5 s) and clears its saved windows, so macOS never shows a *reopen windows?* dialog after a crash, launches the new one with the arguments, waits for its window, and prints the app name to use with `ui`, `click`, and `film`. `--fresh` first deletes the app's saved data and settings. `--before` runs a guest shell line just before launch, such as `defaults write`. Its output goes to `/tmp/vmx-app/<name>.app.log`. Takes about 4 s. |
| `$S quit <host.app or executable>` | Quits the app cleanly (Cmd-Q, forced after 5 s; an app with no Quit menu item is stopped after 1 s). Never stop an app with `kill -9`: a crash makes macOS ask about it at the next launch. |
| `$S job '<lines>'` | Runs several `$S` calls as one, holding the guest until they end (see *Share the guest*). |
| `$S lease` | Keeps the guest for you across calls, for looking before you decide. Prints a token to put before each call (see *Share the guest*). |
| `$S film <app> <out.mov or .mp4 or .png> [--rect x,y,w,h] [--1x] [--tail MS] <action>...` | Needs ssh to the guest. Records the app's window at 60 fps and full Retina pixels while the actions run, as ProRes 4444 in a `.mov`, which matches a Retina screenshot exactly (about 30 MB per second of motion), or HEVC in an `.mp4` (about 30 times smaller, slightly soft), and saves the film on the host plus `<out>.times.txt`. Quote each action as one argument (`"click Add to Favorites"`). Actions: `click NAME` (real click on the element with that exact name, else on the one whose name contains NAME, such as part of a list row's title; looked up when the action runs), `xy X,Y` (real click at a point), `key NAME`, and `wheel X,Y DY` (scroll the mouse wheel over that point by DY lines, one line at a time; negative scrolls down, up to 99). Use `wheel` instead of a scroll script of your own. After each action it waits until the picture changes and then stays still for 0.3 s, so nothing sleeps for a guessed time. Every changed pixel counts, even a 1 pt wobble. Before recording, `film` brings the app to the front. Recording starts just before the first action and stops `--tail` ms (default 300) after the last one settles. `--rect` records only that part of the screen, in guest screen points read off a `shot`. It also saves the last frame at full pixels next to it (`star.mov` gets `star.mov.png`), and `<out>.area`, the recorded part of the screen in points, which `frames` and `pixels` read. With a `.png` name it keeps no film: it runs the actions, waits for each to settle, then takes a `shot` (`<out>.png` in points, where a pixel is a click point, plus `<out>@2x.png`). That's how to click several times and look, with no guessed sleeps. A film takes about 5 s more than its own length. A stuck film stops itself after 40 s per action (12 actions at most) and says so, so it never runs into a 10 min command limit. |
| `$S frames <film> [--from MS] [--to MS] [--rect x,y,w,h] [--cols N] [--zoom N] [--out sheet.png]` | Host only, never waits for the guest. One contact sheet of the film's real frames between those film times (from the times file), each labeled with its time in ms. `--rect` is in screen points, like a `shot` pixel. Tiles keep full detail when they fit 2400 px across and 4800 px down; `--cols 1` stacks them, `--zoom N` enlarges a small crop N times with sharp pixels. At most 24 frames; with more it picks evenly and says so. Prints the times of the frames it shows. `$S frames a.png b.png ... --rect x,y,w,h` puts pictures side by side the same way, each cropped to the same part and labeled with its file name, to compare shots or renders. A shot or `film` `.png` counts in screen points; another picture counts its own pixels (halved for an `@2x` name). Use it instead of cropping or stacking with ffmpeg. |
| `$S pixels <film> X,Y [X,Y...] [--from MS] [--to MS] [--all]` | Host only. Each screen point's color (`#rrggbb`) by film time, one row per change. Use it to prove a flash, a fade, or a color without reading images. Within 1 of a `shot` in a `.mov`; in an `.mp4`, a few values off on flat areas and more on text edges. |
| `$S pull <guest-file> <host-file>` | Copies a guest file to the host and checks an md5 checksum. Takes about a second over ssh. Without ssh it takes about a minute per MB, so keep files small. |
| `$S push <host-file> <guest-file>` | Copies a host file into the guest over ssh and checks an md5 checksum. Fails when ssh isn't set up. |
| `$S sh '<line>'` | Runs a shell line in the guest's GUI session. Pipes, `&&`, and `$VAR` work. Long commands and large output are fine. |
| `$S /usr/bin/prog args` | Runs one program. Use an absolute path. |

Exit codes for `ui` and `click`:

| Code | Meaning | Do |
|---|---|---|
| 0 | Done | Run `shot` and look. |
| 10 | App not found or unreadable | Run `apps`, use the exact name, and `launch` the app if it isn't running. |
| 11 | No element with that name | Read the printed list. Pick a name from it, or take a `shot`. |
| 12 | More than one element has that name | Add the role as the third argument, or `clickxy` one of the printed points. |
| 13 | The click failed | Read the printed message. If it says *may have worked*, do not repeat it. Run `shot` and look. |
| 14 | No reply from the guest | The click may have been sent. Do not repeat it. Run `shot` and look. |

Exit codes for every command:

| Code | Meaning | Do |
|---|---|---|
| 2 | Wrong use: `click`, `clickxy`, or `film` ran alone, or a job ran something other than `$S`, or slept in the guest | Read the printed message and do what it says. |
| 75 | The guest was still busy after 90 s | Run the same call again as a background shell call and keep working. |
| 76 | Your lease has ended | Take a new lease, or put the steps in one `$S job`. |

## Share the guest

Other agents may use the same guest. `vmx` keeps them apart by itself, so you never take or release a lock:

* Each call holds the guest alone while it runs. Callers go one at a time, in the order they came. A busy guest makes the call wait (up to 90 s) and say who has it. If it is still busy, the call exits 75: run it again as a background shell call (Claude Code: `run_in_background`) and keep working.
* Between your calls, another agent may quit or replace your app and change the screen. So `click`, `clickxy`, and `film` refuse to run alone: they run only inside a job or a lease.

A job runs several calls as one and holds the guest until they end (at most 540 s). Start it with `$S app`, then replay every click it needs:

```sh
$S job '$S app ./MyApp.app --fresh -- <args> && $S click "My App" Settings && $S film "My App" /tmp/a.mov "click Dark"'
```

A job may only run `$S` commands (`| grep` and `| head` may filter them), and may not sleep in the guest (`$S sh 'sleep 2'`). Build, package, and wait on the host before it, never inside. To click several times and then look, use one `film` to a `.png`: it waits until each click settles, then takes a `shot`.

```sh
$S job '$S app ./MyApp.app --fresh -- <args> && $S film "My App" /tmp/look.png "xy 362,451" "xy 627,199" "key escape"'   # then read /tmp/look.png
```

A lease keeps the guest for you across calls, so you can look at a screenshot before you decide the next click. Use it only for that, because everyone else waits meanwhile:

```sh
$S lease                                         # prints VMX_LEASE=<token>
VMX_LEASE=<token> $S shot /tmp/s.png             # start every call with the token, then read the file and decide
VMX_LEASE=<token> $S click "My App" "Settings"
VMX_LEASE=<token> $S lease end                   # give the guest back as soon as you are done
```

A lease ends 45 s after its last call ends, and 120 s after it started at most. After that, a call with its token exits 76. When a lease ends, the agents already waiting go first.

## Take a screenshot

One shell call, then read the file:

```sh
$S shot /tmp/s.png    # saves /tmp/s.png (1x) and /tmp/s@2x.png (Retina)
```

Read `/tmp/s.png`. Open `/tmp/s@2x.png` only to check fine detail, or to hand it to a person. Skip `apps`, `ui`, and any setup checks.

## Loop for every UI task

1. `$S shot /tmp/before.png`, then read `/tmp/before.png`. Check that the app is open, loaded, and in front. If it shows an empty or loading state, fix that first.
2. `$S ui <app>`. Pick the target from the printed list.
3. `$S click <app> "<name>"`. Never reuse a ref or a list from an earlier call. If `click` can't reach it, use `clickxy` with the point from `ui` or from the screenshot.
4. `$S shot /tmp/after.png`, then read `/tmp/after.png`. A returned success only means the click was sent. Continue only when the screen shows the result.

Run this loop inside a lease (see *Share the guest*): start every call with `VMX_LEASE=<token>`, and end the lease when the loop is done. Once you know the clicks, put them in one `$S job` instead.

To film something, skip this loop and use one `film` call (see *Film an animation*).

List rows and other long names: a row's name is its whole title plus summary, so exact-name `click` fails. Find the row with `ui` and click its point:

```sh
VMX_LEASE=<token> $S ui "<app>" "part of the title"                      # prints: role  name  x,y  size (a row repeats as cell and group, same point)
VMX_LEASE=<token> $S clickxy 319 220                        # inside a lease: use the x,y from that line, then run shot and look
```

Rules:

* Pick small, simple content for UI checks (a short story, a small file). Huge content keeps the app busy and the UI stops answering.
* Positions stay valid while the window and layout stay the same. After you know a position, reuse it with `clickxy`. Look a target up again only after a click fails.
* Two failed lookups of the same thing means stop and take a `shot`. Never loop.
* Don't use `osascript` or System Events in the guest. They raise their own security prompts.

Other actions, through `$S sh`:

| Need | Command |
|---|---|
| Open an app | `'$HOME/.local/bin/agent-desktop launch "<app>"'` |
| Press a key | `'$HOME/.local/bin/agent-desktop press return --app "<app>"'` |
| Scroll | `'$HOME/.local/bin/agent-desktop mouse-wheel --x X --y Y --dy=-15 --headed'` (guest alone only) |
| Any other action | `'$HOME/.local/bin/agent-desktop skills get desktop'` prints the full guide. Read it instead of guessing flags. |

## Film an animation

Put every step in one `film` call: the clicks that set up the scene, the action you want to see, and the click that undoes it. A whole film task is one shell call:

```sh
$S job '$S app ./MyApp.app --fresh -- <args> && $S ui "My App" favor && $S film "My App" /tmp/star.mov "click Add to Favorites" "click Remove from Favorites"'
```

`ui` with a filter prints the starting state in the same call (*Add to…* means off).

`film` prints the times file. Each line says whether that action changed the picture, so it is the check: don't run `ui`, `shot`, or `apps` afterward. Read the last frame (`star.mov.png`, made when `ffmpeg` is on the host) only if you need to see the end state. Take no screenshots before the film either. Use `click <part of a row title>` to open a list row first. Some elements have no name (an app may leave a selected row unnamed); click those with `xy X,Y` from `ui`.

`click NAME` costs 1 to 5 s per lookup in a big app, so `film` prints the point it found: use `xy X,Y` with that point in the next film while the window stays the same.

To check motion frame by frame, don't write ffmpeg or pixel scripts. Use these on the host, with the times from the times file:

```sh
$S frames /tmp/star.mov --from 2004 --to 2640 --rect 300,80,200,60   # one sheet of the real frames, each labeled with its time; read it
$S pixels /tmp/star.mov 362,451 400,90 --from 2004 --to 2640         # each point's color at every change, as text
```

Each line of `<out>.times.txt` reads like `1901 ms: click Star | first change 2004 ms, last change 2640 ms`, all in film time. A film stores a frame only when pixels change (16.7 ms apart while something moves), so judge timing by these times, never by counting frames or splitting with `fps=60`.

Read the times file after every film:

| Line ends with | Meaning | Do |
|---|---|---|
| `first change …, last change …` | The action changed the picture. The animation runs between those times. | Look at the frames between them. |
| `NO CHANGE in 2 s` | Nothing changed within 2 s, so the action likely missed. An animation that starts later than 2 s after its trigger also lands here. | Take a `shot`, check the target, and film again. |
| `NOT CLICKED: …` | No single on-screen element had that name when the action ran. | Run `ui` for the names on screen. A button's name can change after a click (*show sidebar* becomes *hide sidebar*). |
| `STILL CHANGING 30 s later` | Something keeps moving (a spinner, a video). | Film with `--rect` around the part you care about. |

A spinner or a video in the window also counts as a change, so every action then waits 30 s. Use `--rect` to record only the part you care about; it also makes the file small. Hand the `.mov` itself to people and tell them to view it at actual size; a player that scales it to fit makes it look soft. Use `--1x` only when file size matters more than detail.

## Move files

| Need | Do |
|---|---|
| Host file into the guest | The folder passed to `vmctl start --shared-folder PATH` appears at `/Volumes/My Shared Files/<name>`, read-only unless started with `--writable`. Copy before use: `$S /usr/bin/ditto "<src>" /tmp/x`. |
| Guest file to the host | `$S pull`. Never write into the share. Write to `/tmp` in the guest first. |
| Host file into the guest, no shared folder | `$S push`. Use it to copy an app build, not `base64` through `exec`. |

## Test an app

One build, copy, and launch round costs minutes. Work out the visual or logic change without the VM first (an offscreen render, a unit test, a scratch copy of the code), then use the VM once to confirm.

1. Build and package the `.app` on the host, and never launch it on the host. The guest has no Xcode and no Apple Intelligence model.
2. In one job, copy any data file the app reads, install and launch the app (about 4 s), and film or `shot` it, using the name `app` printed:

```sh
$S job '$S push ./tape.zlib /tmp/tape.zlib && $S app ./build/MyApp.app --fresh --before "/usr/bin/defaults write <bundle-id> key -string value" -- --my-flag /tmp/tape.zlib && $S film "My App" /tmp/a.mov "click Star"'
```

Also:

* The guest is slower and lacks the host's real data. Don't use it for timing or data-dependent bugs.
* Guard guest-only scripts with `[ "$(sysctl -n kern.hv_vmm_present)" = 1 ]`. It prints 1 in the guest and 0 on the host.
* To undo guest changes, `vmctl snapshot <bundle> list`, then `revert <name>`. Don't create snapshots unasked.
* Other `vmctl` commands: `vmctl remote --name <VM> clipboard get|set <text>`, `vmctl status <bundle>`, `vmctl resume <bundle> --headless` (from a suspended state). Don't stop the VM unasked.

## When a command fails

Find the exact symptom, then apply only its fix.

### An app stalls or never responds

A macOS password dialog can sit unseen in the guest and block an app. Run this before any `log show`, process list, or screenshot:

```sh
$S sh '/usr/bin/pkill -9 -x SecurityAgent'    # plain pkill is ignored while requests are queued
```

Quitting the app does not close the dialog. To stop it from coming back:

* A new key, a new signature, or a changed bundle ID makes macOS ask again. Reuse the existing key, keep the bundle ID and install path fixed, and sign every build the same way.
* If the app generates its own key, make it save the key and reload it on the next launch.

### Every call fails or hangs

```sh
vmctl list                              # no row means no VM
vmctl remote --name <VM> health         # "health" : "ok" means the guest answers
```

The VM name is the bundle's folder name without `.GhostVM`. If `health` fails, run `vmctl start <bundle> --headless` (without `--headless` it fails with `GhostVMHelper.app not found` unless the GhostVM app manages the VM).

### `health` is ok but every call fails (`status 500` or `Connection reset by peer`)

GhostTools isn't running in the guest. Ask the user to start it. Don't retry in a loop. A single failed call is usually a bare command name, so use the absolute path.

### Calls take 30 s, or fail with `Empty response from server`

That is the GhostTools hang ([GhostVM issue #268](https://github.com/groundwater/GhostVM/issues/268)). `vmx` avoids it only with ssh. Check `ssh ghostvm-<VM> true`, and if it fails, ask the user to set up ssh (see *Setup*).

### A UI call reports `TIMEOUT` or `locator_transient_incomplete`

The app is busy or loading. Take one `shot`, wait a few seconds, then retry once. If it still fails, use `clickxy`.

### The guest screen is black

The guest display went idle. Keep it awake:

```sh
$S sh '(nohup /usr/bin/caffeinate -d -i -s -u > /dev/null 2>&1 &)'
```

`pmset -a` needs root, so don't try it.

### The guest has no network (apps show *Offline*)

```sh
$S sh '/usr/sbin/ipconfig getifaddr en0; /usr/sbin/networksetup -getinfo Ethernet'
```

* An address starting `169.254` means no DHCP lease.
* A *Manual* address that another guest also uses is an IP clash.
* Both fixes need root (`sudo networksetup -setdhcp Ethernet`). Ask the user to run it.

### `log show --start` fails with `Failed conversion of ... using format`

Pass the time as `'YYYY-MM-DD HH:MM:SS'`. A shorter form fails.

### A long command gets dropped (no ssh only)

Without ssh, run it detached, then read its log:

```sh
$S sh '(nohup CMD > /tmp/job.log 2>&1 &); echo started'
$S sh 'cat /tmp/job.log'
```

Without ssh, replies over about 30 KB come back empty. Page them with `cut -c`.

## Setup (done once by a human, never redo)

The guest user and password, Apple's license, GhostTools (`GhostVM.app/Contents/Resources/GhostTools.dmg`, with *Auto Start*), agent-desktop at `$HOME/.local/bin/agent-desktop` in the guest, and the Accessibility, Screen Recording, and Remote Login permissions. For speed, Remote Login on in the guest and a `Host ghostvm-<VM>` entry in the host's `~/.ssh/config` with a key that logs in without a password (or set `VMX_SSH` to another host name). If one is missing, ask the user. Install agent-desktop from its [GitHub release](https://github.com/vercel-labs/agent-desktop) only if a call says *not found*. Don't create a VM or download an image unless asked.
