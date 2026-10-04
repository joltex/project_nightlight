# Migrating Nightlight to uv

Status: planning (2026-10-03). Nothing in the repo has changed yet.

This doc covers two things:

1. **Plan A (now):** move the project from Pipenv + `setup.py` to uv, **without touching the Pi's OS**. The Pi stays on Raspbian Buster / Python 3.7.
2. **Plan B (later):** reflash the Pi to a current Raspberry Pi OS, then drop the Python 3.7 workarounds.

---

## Findings

### Repo

- `main` uses **Pipenv + `setup.py`**, not Poetry. Poetry only exists on the unmerged `switch_to_poetry` branch, so this migration replaces that branch.
- Python 3.7 is the effective floor today. `implement_sources` has several `TODO >= Python 3.8` comments (`import attr as attrs`, commented-out `Protocol`), and `switch_to_poetry` pins `python = "^3.7"`.
- `matplotlib` is needed by `pattern_generators/perlin.py`. The Poetry branch dropped it by mistake.
- `noise` is a C extension with no PyPI wheels, so it is compiled from source or pulled from piwheels.

### The Pi

| | |
|---|---|
| Model | Raspberry Pi 3 Model B Rev 1.2 |
| OS | Raspbian GNU/Linux 10 (Buster), 32-bit (`armv7l`) |
| glibc | 2.28 |
| Python | 3.7.3 (system only) |
| Disk | 15 GB card, ~3.5 GB free |
| pip config | `/etc/pip.conf` sets `extra-index-url=https://www.piwheels.org/simple` |

- Buster has been EOL since mid-2024 and Python 3.7 since mid-2023. Neither gets security updates.
- The Pi is reachable from the internet via the `external_rasp_pi` port forward. With an unpatched OS, that is the main reason to do Plan B sooner rather than later.
- `~/.ssh/config` has two `Host rasp_pi` blocks. The first sets `HostName rasp_pi`, which overrides the IP in the second, so `ssh rasp_pi` doesn't resolve. `ssh pi@192.168.1.134` works.

### uv compatibility (from uv docs)

- **Platform:** Linux armv7 is Tier 2 ("guaranteed to build"). uv ships an `armv7-unknown-linux-gnueabihf` binary.
- **Python 3.7:** Tier 2 ("expected to work"), with the warning "We do not recommend using these versions."
- uv has **no managed Python 3.7 downloads**. On the Pi, uv uses the system `/usr/bin/python3.7`.
- **uv does not read `pip.conf`.** piwheels has to be configured for uv separately.

### Dependency resolution (dry run on the Mac)

- `uv pip compile --python-version 3.7` resolves all deps, including `adafruit-blinka==5.9.2`. It picks numpy 1.21.6, matplotlib 3.5.3, pillow 9.5.0, attrs 24.2.0 and pytest 7.4.4.
- A universal resolve (`--universal`, `requires-python >= 3.7`) forks per Python version, so **one `uv.lock` can serve both the Pi (3.7) and the Mac (3.14)**.

### On-device test (Pi, 2026-10-03)

1. **uv installs and runs:** `uv 0.12.23 (armv7-unknown-linux-gnueabihf)` installed to `~/.local/bin`. It is the glibc build, so Buster's glibc 2.28 is new enough. (The Mac has uv 0.12.22.)
2. **The first install tried to compile numpy:** uv picked numpy **1.21.6**, the newest version supporting 3.7. piwheels has no Buster/cp37/armv7 wheel for it, so uv fell back to building from source. That was aborted, because it is very slow on a Pi 3 and may run out of its 1 GB of RAM.
3. **With `--only-binary numpy,pillow`, uv picked numpy 1.21.4**, which piwheels *does* have a wheel for. All 16 packages resolved.
4. **The real install worked:** it took about 5 s with a warm cache, with nothing compiled. The smoke test `import numpy, PIL, noise, attr, board` printed `ok 1.21.4 9.5.0`. `import board` succeeding means blinka detected the real hardware.
5. On the Pi, `adafruit-blinka` also pulls in `rpi-gpio`, `rpi-ws281x` and `sysv-ipc`. These don't appear in a Mac-side resolve.

The commands used (in a throwaway `/tmp/uv-test`):

```bash
curl -LsSf https://astral.sh/uv/install.sh | env UV_NO_MODIFY_PATH=1 sh
~/.local/bin/uv venv --python /usr/bin/python3.7
~/.local/bin/uv pip install \
  --extra-index-url https://www.piwheels.org/simple \
  --index-strategy unsafe-best-match \
  --only-binary numpy,pillow \
  numpy pillow noise 'adafruit-blinka==5.9.2' attrs
```

**What this test did not cover:** a Mac-generated `uv.lock` installed on the Pi with `uv sync --locked`, a cold-cache install time, and actually playing a pattern.

---

## Plan A: switch to uv, keep the Pi on Buster / Python 3.7

Code must stay **Python 3.7 compatible** while this plan is in effect. That means `import attr as attrs` instead of `import attrs`, `from __future__ import annotations` for `tuple[...]`/`X | Y` hints, and no `typing.Protocol`.

### 1. Add `pyproject.toml`

Replaces `setup.py` and the Pipfile:

```toml
[project]
name = "nightlight"
version = "0.1.0"
requires-python = ">=3.7"
dependencies = [
    "adafruit-blinka==5.9.2",
    "adafruit-circuitpython-lis3dh",
    "attrs",
    "matplotlib",
    "noise",
    "numpy",
    "pillow",
    "youtube-dl",
]

[project.scripts]
nightlight = "nightlight.cli:main"

[dependency-groups]
dev = ["pytest"]

[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"

[tool.uv]
# piwheels only has prebuilt numpy up to 1.21.4 for Buster / cp37 / armv7.
constraint-dependencies = ["numpy<1.21.5; python_version < '3.8'"]
# Never compile these on the Pi; fail loudly instead.
no-build-package = ["numpy", "pillow"]
index-strategy = "unsafe-best-match"

[[tool.uv.index]]
name = "piwheels"
url = "https://www.piwheels.org/simple"
```

Notes:

- piwheels must be in `pyproject.toml`, not only in the Pi's `pip.conf`. The lock is generated on the Mac and needs to record the piwheels wheel URLs.
- The numpy constraint only applies on Python 3.7, so the Mac still gets current numpy.
- `index-strategy = "unsafe-best-match"` lets uv choose between PyPI and piwheels per version. That is acceptable here because piwheels is a trusted mirror, but it is the reason for the "unsafe" name.
- **Unverified:** that `no-build-package` plus a universal lock behaves as expected. Check this first, in step 3.

### 2. Clean up packaging files

- Delete `setup.py`, `Pipfile` and `Pipfile.lock`.
- Add `.python-version` containing `3.7`. This is optional on the Mac, since uv will otherwise use a newer local Python for development.
- Add `.venv/` to `.gitignore`.
- Locally, delete the stale `build/`, `dist/` and `nightlight.egg-info/` folders. They are already gitignored.

### 3. Lock and verify on the Mac

```bash
uv lock
uv sync
uv run nightlight --help
uv run nightlight convert <some video>     # converter path still works
```

- Confirm `uv.lock` includes numpy `<1.21.5` for `python_full_version < '3.8'` and piwheels wheel entries.

### 4. Verify on the Pi

```bash
git fetch && git switch use-uv
~/.local/bin/uv sync --locked
~/.local/bin/uv run nightlight play examples/test_pattern.nl
```

- Install time with a cold cache should be minutes, not tens of minutes. A long numpy build means the constraint or index setup is wrong.
- Optional: add `~/.local/bin` to `PATH` on the Pi (the uv installer was run with `UV_NO_MODIFY_PATH=1`).

### 5. README

Add setup and usage steps: install uv, run `uv sync`, run `uv run nightlight …`, plus Pi-specific notes (piwheels, SPI enabled).

### 6. Branch housekeeping

- `switch_to_poetry`: close it once this lands. Check with joltex first, since it's their branch.
- `dependabot/pip/pytest-9.0.3`: close it. Dependabot supports `uv.lock`.
- `implement_sources`: rebase onto this so its tests run via `uv run pytest`.
- `20240126`: already squash-merged as PR #2, so it can be deleted.

---

## Plan B (future): reflash the Pi, drop Python 3.7

### Why

- It gets security updates again, which matters because the Pi is internet-reachable.
- Modern Python (3.11+) works on the Pi. That unblocks `import attrs`, `typing.Protocol`, built-in generics, and current numpy/matplotlib.
- It removes the numpy pin and most of the piwheels workarounds.

### Upgrade path (per raspberrypi.com docs)

- **In-place major upgrades are not recommended.** From the Raspberry Pi docs: "we strongly recommend that you use a clean install to upgrade the OS version." From Buster, an in-place upgrade would also take two hops (Buster → Bullseye → Bookworm/Trixie).
- "Installing a new OS overwrites everything on the SD card." Back up first.

### Choice of OS

- **Raspberry Pi OS Lite (64-bit)**, the current release (Trixie). Confirm that Pi 3B appears for it in Imager, or fall back to Bookworm (Python 3.11).
- **Lite:** the Pi is headless and only runs the CLI, and the Pi 3B has only 1 GB of RAM.
- **64-bit:** PyPI ships `aarch64` wheels for numpy and pillow, so uv works without piwheels. `noise` will still compile, so install `build-essential python3-dev`.
- From Bookworm onward, `pip install` outside a venv is blocked (`externally-managed-environment`). That doesn't affect uv, which always uses `.venv`.

### Backup (single SD card)

1. **Copy the files you need while the Pi is running:**
   ```bash
   rsync -avh --progress pi@192.168.1.134:/home/pi/ ~/pi-backup/home/
   ```
   Also copy any customised `/etc/wpa_supplicant/`, `/etc/systemd/system/`, `crontab -l` and `/boot/config.txt` (SPI settings). Check what is using the ~11 GB first, with a `du` survey.
2. **Take a full image of the card** (restorable safety net). Shut the Pi down and put the card in the Mac:
   ```bash
   diskutil list                      # find the ~16 GB external, physical disk; double-check N
   diskutil unmountDisk /dev/diskN
   sudo dd if=/dev/rdiskN bs=4m status=progress | gzip > ~/pi-buster-backup.img.gz
   ```
   - To restore, use Raspberry Pi Imager → "Use custom".

### Flash and set up

1. In Raspberry Pi Imager, choose **Raspberry Pi OS (other) → Lite (64-bit)**. In the settings, preset:
   - hostname, e.g. `nightlight`, reachable as `nightlight.local`
   - user `pi`
   - Wi-Fi
   - SSH with `~/.ssh/id_rsa.pub`
2. On first boot:
   - run `sudo apt update && sudo apt full-upgrade`
   - run `sudo apt install git build-essential python3-dev`
   - enable SPI in `raspi-config`
3. Install uv, clone the repo, run `uv sync --locked`, and play a pattern.
4. On the Mac:
   - remove the old host key with `ssh-keygen -R 192.168.1.134`
   - fix the duplicate `rasp_pi` block in `~/.ssh/config`
   - check that the router port forward still points at the right IP

### Code changes after Plan B

- `requires-python = ">=3.11"` (or whatever the new OS ships), and update `.python-version`.
- Remove the numpy constraint, and probably piwheels, `no-build-package` and `index-strategy` too, if 64-bit.
- Resolve the `TODO >= Python 3.8` items: `import attrs`, enable the `Source` protocol.
- Re-run `uv lock --upgrade`.

---

## Related, out of scope

- `youtube-dl` is largely unmaintained. Consider switching to `yt-dlp`.
- `_calculate_brightness` in `base.py` divides by `max_brightness`, so lower settings are brighter and values can exceed 1.0.
