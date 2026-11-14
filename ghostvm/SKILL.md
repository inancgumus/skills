---
name: ghostvm
description: Use GhostVM (`vmctl`) to run commands and drive apps inside a macOS VM. Use when a task mentions GhostVM, vmctl, or testing in a VM.
---

# GhostVM

GhostVM runs a macOS guest on Apple's Virtualization framework. The only CLI is `vmctl` (there is no `ghostvm` command). This file has everything you need, so skip `--help` and old transcripts. Assume the VM is running and set up. Run the task, and diagnose only when a call fails (see *When something fails*).

## Never

* Use any VM tool except GhostVM. Never install or create VMs with tart, lume, or containers.
* Launch, kill, capture, or drive anything on the host when told to use the VM. Host tools (`cliclick`, `osascript`, `ffmpeg`) are off limits for the guest.
* Bring the VM window to the front, or click it with host computer-use tools.
* Drive the guest UI with anything but agent-desktop.
* Create a new key or keychain item for an app the guest already knows (see *Stuck dialogs*).
* Share a guest. One agent per guest at a time. If a lock file or another agent holds it, wait or use another VM.
* Put a password in a command argument. Anything that needs root needs the user's admin password, so ask the user.

## 1. Run commands

`scripts/vmx` sits next to this file (needs `jq`). Set `S=<this skill's dir>/scripts/vmx`. Use it instead of raw `vmctl remote exec`. It retries empty replies, prints the guest's stdout and stderr, and exits with the guest's exit code.

```sh
$S /usr/bin/whoami                       # run a program (absolute path)
$S sh 'cd /tmp && ls | head'             # run a shell line
$S pull /tmp/shot.png ./shot.png         # copy a guest file to the host, any size
$S -n other-vm /usr/bin/uptime           # pick a VM (default: the only one listed, or $VM)
$S sh '(nohup CMD > /tmp/job.log 2>&1 &); echo started'   # long job, then: $S sh 'cat /tmp/job.log'
```

If you must call `vmctl remote --name <VM> exec` directly:

* Use absolute paths. `exec` has no `PATH`, and a bare name returns `status 500`.
* Wrap pipes, `&&`, and `$VAR` in `/bin/sh -c '...'`.
* Don't store the command in a shell variable. `V="vmctl remote ..."; $V ...` fails in zsh.
* Retry `Empty response from server` once. Replies over about 30 KB come back empty, so page them with `cut -c`.
* Long commands get dropped. Run them detached, as above.

Other `vmctl` commands you may need:

* `vmctl remote --name <VM> apps` lists the guest's running apps.
* `vmctl remote --name <VM> clipboard get` and `clipboard set <text>` read and write the guest clipboard.
* `vmctl status <bundle>`, `vmctl stop <bundle>`, and `vmctl resume <bundle> --headless` (from a suspended state) manage the VM. Don't stop it unasked.

`exec` runs as the guest user with no sudo. It is the only path that reaches the GUI session: `screencapture`, accessibility, and `open` work through `exec`, not over `ssh`.

## 2. Move files

| Need | Do |
|---|---|
| Host file into the guest | The folder passed to `vmctl start --shared-folder PATH` appears at `/Volumes/My Shared Files/<name>`, read-only unless started with `--writable`. Copy before use: `$S /usr/bin/ditto "<src>" /tmp/x`. |
| Guest file to the host | `$S pull`. Never write into the share. Write to `/tmp` in the guest first. |
| Screenshot | `$S sh '$HOME/.local/bin/agent-desktop screenshot --screen 0 /tmp/s.png'`, then `pull`. `--app X` fails with `AMBIGUOUS_TARGET` when the app has several windows (Finder has hidden ones). Pass `--window-id` from `list-windows` instead. Use screenshots as evidence, and read the UI tree to decide what to do. |

## 3. Test an app

1. Build on the host. The guest has no Xcode and no Apple Intelligence model.
2. Package the `.app` without launching it on the host, then copy it into the guest.
3. Install to one fixed path with the same bundle ID every time. Run `lsregister -u <path>` when you delete a copy, because stale copies slow launches.
4. Launch it in the guest, then drive it (section 4).

Also:

* The guest is slower and lacks the host's real data. Don't use it for timing or data-dependent bugs.
* Guard guest-only scripts with `[ "$(sysctl -n kern.hv_vmm_present)" = 1 ]`. It prints 1 in the guest and 0 on the host.
* To undo guest changes, `vmctl snapshot <bundle> list`, then `revert <name>`. Don't create snapshots unasked.

## 4. Drive the UI

`agent-desktop` is at `$HOME/.local/bin/agent-desktop` in the guest. Call it through `$S`. Install it from its [GitHub release](https://github.com/vercel-labs/agent-desktop) only if the call says *not found*. If you are unsure of a flag, read its guide instead of guessing:

```sh
$S sh '$HOME/.local/bin/agent-desktop skills get desktop'
```

* Keep tokens low. Run `snapshot --skeleton -i --compact`, then `--root <ref>` for one region, or `find`. A full snapshot of a busy app is a huge blob.
* List rows are often `treeitem` or `unknown` inside a scroll area, not `row`. Read the real roles in a snapshot before `find --role`.
* `STALE_REF` or a ref that no longer works: refs go stale after any UI change. Snapshot again.
* Read properties with `get <ref> --property bounds`. Get the screen size from `list-displays`, not `system_profiler`.
* If `scroll <ref>` returns `ACTION_FAILED`, use `mouse-wheel --x --y --dy=-15 --headed`. `--headed` moves the guest's cursor and takes focus, so use it only after the headless action failed.
* `AMBIGUOUS_TARGET`: more than one window or element matches. Narrow it with `--window-id`, or `find --role --name --exact`, or `--root`.
* `APP_NOT_FOUND` means the app isn't running yet or the name is wrong. Use the name `list-apps` shows (often with spaces, like `Hacker News`, not `HackerNews`). Use `wait`, not `sleep`.
* A busy app can stop answering accessibility queries. Wait a few seconds and query again before you decide it crashed.
* Don't use `osascript` or System Events in the guest. They raise their own security prompts.

## 5. Fix a specific failure

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

The VM name is the bundle's folder name without `.GhostVM`. If `health` fails, see the next item.

### `health` fails: the VM is not running

Run `vmctl start <bundle> --headless`. Without `--headless` it fails with `GhostVMHelper.app not found` unless the GhostVM app manages the VM.

### `health` is ok but every `exec` fails (`status 500` or `Connection reset by peer`)

GhostTools isn't running in the guest. Ask the user to start it. Don't retry in a loop.

### One `exec` fails with `status 500`

You used a bare command name. Use the absolute path (section 1).

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

### A screenshot fails with `AMBIGUOUS_TARGET`

Pass `--window-id` from `list-windows` instead of `--app`, or use `--screen 0`.

### An agent-desktop call fails

* `STALE_REF`: snapshot again.
* `AMBIGUOUS_TARGET`: narrow with `--window-id`, `find --role --name --exact`, or `--root`.
* `APP_NOT_FOUND`: use the name `list-apps` shows, and `wait` for the app.
* `ACTION_FAILED` on `scroll`: use `mouse-wheel --x --y --dy=-15 --headed`.

## Setup (done once by a human, never redo)

The guest user and password, Apple's license, GhostTools (`GhostVM.app/Contents/Resources/GhostTools.dmg`, with *Auto Start*), and the Accessibility, Screen Recording, and Remote Login permissions. If one is missing, ask the user. Don't create a VM or download an image unless asked.
