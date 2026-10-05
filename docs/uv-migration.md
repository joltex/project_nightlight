# Migrating Nightlight to uv

Status: **in progress (2026-10-04)**. The Pi has been reflashed to Raspberry Pi OS Lite 64-bit (Trixie, Python 3.13), and `pyproject.toml` + `uv.lock` are on the `use-uv` branch. Still to do: verify on the Pi, README, branch housekeeping (see [Remaining work](#remaining-work)).

## Summary

We moved the project from **Pipenv + `setup.py`** to **uv**. We first planned to keep the Pi on its old OS (Raspbian Buster, Python 3.7, 32-bit) and work around it with piwheels. That worked in a throwaway test but made the uv setup fragile (see [Approach not taken](#approach-not-taken-keep-the-pi-on-buster--python-37)). Instead, we **reflashed the Pi** to a current 64-bit OS. That lets one ordinary `uv.lock` from PyPI serve both the Mac and the Pi.

- Pi setup steps: see [pi-setup.md](pi-setup.md).

---

## Final configuration

### `pyproject.toml`

```toml
[project]
name = "nightlight"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = [
  "adafruit-blinka",
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

[tool.setuptools.packages.find]
include = ["nightlight*"]
```

### Other files

- **`.python-version`:** `3.13`, matching the Pi's system Python (3.13.5). uv uses Homebrew's 3.13 on the Mac, or downloads one.
- **`.gitignore`:** `.venv/` added.
- **Removed:** `setup.py`, `Pipfile`, `Pipfile.lock`.

### Notes on the choices

- **`requires-python = ">=3.13"`:** matches Trixie. This removes the old 3.7 floor, so `import attrs`, `typing.Protocol`, `tuple[...]`/`X | Y` hints etc. are all fine now.
- **`adafruit-blinka` unpinned:** it was pinned to `5.9.2` (2020), which predates Python 3.13 and Trixie. It locked to **9.2.0**. The code only uses `board`, `busio` and `digitalio`, which current blinka still provides. **This is the most likely thing to break on the Pi.**
- **No piwheels / no `[tool.uv]` section:** on 64-bit (`aarch64`), PyPI has wheels for numpy, pillow, matplotlib etc.
- **Packages that still compile from source on the Pi:** `noise`, plus a few small Pi-hardware packages pulled in by blinka. They need `build-essential python3-dev`.
- **`[tool.setuptools.packages.find]`:** required. Without it, setuptools' automatic discovery sees `gifs/` and `vids/` as packages (see Problems hit below). This matches what `find_packages()` in the old `setup.py` found.
- **Dropped from `setup.py`:** `url='https://github.com/joltex/project_nightlight'`. Optionally restore it as `[project.urls] Repository = "…"`.

### Locked versions (main packages)

| Package | Old (Buster / py3.7) | New (py3.13) |
|---|---|---|
| numpy | 1.21.4 (piwheels) | 2.5.3 |
| pillow | 9.5.0 | 12.3.0 |
| matplotlib | 3.5.3 | 3.11.2 |
| adafruit-blinka | 5.9.2 | 9.2.0 |
| noise | 1.2.2 | 1.2.2 (sdist, compiled) |
| youtube-dl | 2021.12.17 | 2021.12.17 |

Checked on the Mac in the new `.venv`: `Image.ADAPTIVE`, `Image.fromarray(..., mode='RGB')`, `plt.get_cmap` and `noise.snoise4` all still work. `uv run nightlight --help` prints the expected "No valid board detected" warning on the Mac.

---

## Problems hit during the migration

| Error | Cause | Fix |
|---|---|---|
| `matplotlib==3.11.2 @ registry+https://www.piwheels.org/simple can't be installed … doesn't have a source distribution or wheel for the current platform` | `[[tool.uv.index]]` entries take priority over PyPI. Even with `unsafe-best-match`, **uv takes each version from the first index that has it, and doesn't merge files across indexes.** piwheels lists nearly every PyPI version but only has ARM wheels, so the lock pointed the Mac at Pi-only files. | Remove piwheels entirely (not needed on 64-bit). If piwheels is ever needed again, make it `explicit = true` and scope packages to it via `[tool.uv.sources]` with a `platform_machine` marker. |
| `Failed to inspect Python interpreter … /usr/local/bin/python … does not support -I flag. Please use Python 3.6 or newer.` | Typo `requires-python = ">=3.15"`. No 3.15 was installed, so uv walked every Python on PATH and errored on an old python.org **Python 2.7** in `/usr/local/bin`. | Fix to `>=3.13` and add `.python-version`. (The 2.7 install is harmless otherwise, but could be removed: `/Library/Frameworks/Python.framework/Versions/2.7`.) |
| `Using CPython 3.14.7` when we wanted 3.13 | No `.python-version`, so uv picked the newest Python. | Add `.python-version` with `3.13`. |
| `Multiple top-level packages discovered in a flat-layout: ['gifs', 'vids', 'nightlight']` | `pyproject.toml` with no package list uses setuptools' automatic discovery, which treats every top-level folder as a candidate. | `[tool.setuptools.packages.find] include = ["nightlight*"]`. |

Also: `uv init` wasn't used. It ignores `setup.py`/Pipfile, sets `requires-python` from the local Python (3.14) and adds files we don't want. Hand-writing `pyproject.toml` was quicker. Use `uv add`/`uv remove` for future dependency changes.

---

## Remaining work

### 1. Verify on the Pi

```bash
cd ~/dev
git clone -b use-uv git@github.com-sean:joltex/project_nightlight.git
cd project_nightlight
uv sync --locked
uv run nightlight play examples/test_pattern.nl
```

Watch for:

- `noise` failing to compile on 3.13.
- blinka 9.x failing to drive the LEDs.

Record the result here and in `pi-setup.md`.

### 2. README

Add setup and usage instructions: install uv, run `uv sync`, run `uv run nightlight …`, and link `docs/pi-setup.md`.

### 3. Branch housekeeping

- `switch_to_poetry`: superseded. Close it once this lands; check with joltex first.
- `dependabot/pip/pytest-9.0.3`: close it. Dependabot supports `uv.lock`.
- `implement_sources`: rebase onto this. Its `TODO >= Python 3.8` items (`import attrs`, the `Source` protocol) can now be resolved, and its tests run via `uv run pytest`.
- `20240126`: already squash-merged as PR #2, so it can be deleted.
- `nightlight-board-and-attrs` (local): the `NightlightBoard` attrs draft. Rebase onto this. On 3.13 its `import attrs` / `tuple[...]` are fine, but it still has the bugs noted when it was written (self-import instead of `import board`, unannotated pin fields, `data_pin` tuple, `_leds`/`_default_frame_rate` leftovers), and it predates the multiprocessing changes in `base.py`.

---

## What happened to the Pi

### Before

| | |
|---|---|
| Model | Raspberry Pi 3 Model B Rev 1.2 (2.4 GHz Wi-Fi only) |
| OS | Raspbian 10 (Buster), 32-bit (`armv7l`), EOL since mid-2024 |
| Python | 3.7.3 (EOL since mid-2023) |
| Card | 15 GB, ~2021 |

The Pi is also reachable from the internet via a router port forward (`external_rasp_pi`). An unpatched OS on an exposed port was a big reason to upgrade.

### Backup

We surveyed the Pi before wiping (2026-10-03):

- **Repo copies:** five copies of the repo on the Pi, all pushed or stale. The only things that weren't on GitHub were a 2019 `temp` branch and a 2019 stash on `nikolas_edits`, both obsolete. These were skipped.
- **Nothing to recreate:** no services, cron jobs or static IP. The only non-default setting was `dtparam=spi=on`.
- **What was kept:** only `~/.ssh` (GitHub keys for the `github.com-sean`/`github.com-anders` host aliases, plus `authorized_keys` with Sean's and Anders's logins). It was copied to `~/pi-backup/` on Sean's Mac. **It contains private keys; keep it private.**
- No full SD image was taken.

### Reflash

- **In-place upgrade not used:** Raspberry Pi's docs recommend a clean install over an in-place major upgrade.
- **OS:** Raspberry Pi OS Lite 64-bit (Trixie, 15 Sep 2026; Python 3.13.5).
- **Old card:** failed twice in Imager (`Error writing to storage device`, then `Verification failed. Contents were different`). It was replaced with a SanDisk Ultra 64 GB (A1).
- **First boot:** a damaged apt package list after an unclean shutdown. It was fixed by deleting `/var/lib/apt/lists/*`.

Full setup steps and troubleshooting: [pi-setup.md](pi-setup.md).

---

## Approach not taken: keep the Pi on Buster / Python 3.7

Kept for reference in case a Pi ever has to stay on an old 32-bit OS.

### What we found

- **uv on armv7:** supported as Tier 2 ("guaranteed to build"). Installed fine on Buster as `uv 0.12.23 (armv7-unknown-linux-gnueabihf)`; glibc 2.28 is new enough.
- **uv on Python 3.7:** Tier 2 ("expected to work", but "We do not recommend using these versions"). There are no uv-managed 3.7 downloads; uv uses the system `/usr/bin/python3.7`.
- **uv doesn't read `pip.conf`**, so the Pi's piwheels config (`/etc/pip.conf`) is ignored.
- **One lock for both machines:** a universal resolve with `requires-python >= 3.7` forks per Python version, so one lock could in principle serve both the Pi and the Mac.
- **Compiling numpy:** for py3.7, uv picks **numpy 1.21.6**. piwheels has no Buster/cp37/armv7 wheel for it, so uv started compiling numpy on the Pi 3 (very slow, and may run out of RAM).
- **Workaround that worked in a throwaway env:** with `--only-binary numpy,pillow`, uv picked **numpy 1.21.4**, which piwheels has. The install took ~5 s, and `import numpy, PIL, noise, attr, board` worked:
  ```bash
  uv pip install --extra-index-url https://www.piwheels.org/simple \
    --index-strategy unsafe-best-match --only-binary numpy,pillow \
    numpy pillow noise 'adafruit-blinka==5.9.2' attrs
  ```

### Why we dropped it

- Putting piwheels in `pyproject.toml` sent **every** package to piwheels, which broke the Mac (see the first row of Problems hit above).
- Making it work would have needed one of:
  - per-package `[tool.uv.sources]` with platform markers, which only apply to direct dependencies, so Pi-only transitive dependencies like `rpi-gpio` and `kiwisolver` would need adding by hand;
  - or giving up `uv sync --locked` on the Pi and installing from `uv export` output instead.
- It also kept the code stuck on Python 3.7, and the OS was already out of security support.

---

## Related, out of scope

- `youtube-dl` is largely unmaintained. Consider switching to `yt-dlp`.
- `_calculate_brightness` in `base.py` divides by `max_brightness`, so lower settings are brighter and values can exceed 1.0.
- **Python 3.14 breaks `nightlight play` on Linux.** Fix this before moving the Pi past 3.13.
  - **What changes:** Python 3.14 switches the default `multiprocessing` start method on Linux from `fork` to `forkserver`.
  - **Why it breaks:** `player.py:64` starts `Process(target=board.play_patterns, ...)`, passing a bound method of an already-constructed `Nightlight`. Under `forkserver` (and `spawn`, the macOS default), the target and its `board` (`DotStar` LEDs, SPI handles, `Queue`) must be pickled into the child, which will likely fail. It works today only because the Pi runs 3.13, which still forks.
  - **Fix options:**
    - Call `multiprocessing.set_start_method("fork")` at startup (quick, Linux-only).
    - Or, better: construct the `Nightlight` inside the child process and pass only plain data (patterns, settings, the `Queue`) to `Process`.
  - **Related:** `Nightlight.__init__` has `queue: Queue = Queue()` as a default argument. That is evaluated once at import time and shared by every instance, so it should default to `None` and create the queue inside `__init__`.
