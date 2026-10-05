# Setting up the Nightlight Pi from scratch

How to go from a blank SD card to a Pi that plays Nightlight patterns. Written from the October 2026 reinstall (Buster → Trixie). See [uv-migration.md](uv-migration.md) for why we upgraded and how the old install was backed up.

## Hardware

| | |
|---|---|
| Board | Raspberry Pi 3 Model B (Rev 1.2) |
| CPU | 64-bit ARM (`aarch64` with a 64-bit OS) |
| RAM | 1 GB |
| Wi-Fi | **2.4 GHz only.** The 3B has no 5 GHz; that arrived with the 3B+. |
| LEDs | 30 × 18 grid (540 DotStar/APA102 LEDs), driven over SPI |

---

## 1. SD card

### Choosing a card

- Get a microSD rated **A1 or A2**, from a known brand (SanDisk, Samsung, Kingston). We use a **SanDisk Ultra 64 GB (A1)**.
- Speed beyond ~25 MB/s is wasted, because the Pi 3B's card reader is the bottleneck.
- **Fakes are common**, especially SanDisk Ultra. On Amazon, only buy if the buy box says **"Sold by Amazon.ca"** (or "Sold by SanDisk"). The "Visit the SanDisk Store" link under the title proves nothing.

### Testing a new card (F3)

F3 fills the card with test data and reads it all back. It catches fake-capacity cards and bad flash. It is slow (roughly 15–40 min per 16 GB) but worth doing once per card.

```bash
brew install f3
diskutil list                                   # find the card by SIZE
diskutil eraseDisk FAT32 SDTEST MBRFormat /dev/diskN
f3write /Volumes/SDTEST
f3read  /Volumes/SDTEST                         # want: all "Data OK", 0 lost/corrupted
```

> ⚠️ Always identify the card by **size** in `diskutil list`. The Mac's built-in SD slot reports the card as **"internal, physical"**, not "external", so don't look for "external" alone. Any `diskutil erase…` command will wipe whatever disk number you give it.

### Signs a card is dying

These happened with the old 2021 card. If you see any of them, replace the card; don't keep retrying.

- Imager: `Error writing to storage device. Some writes failed to complete.`
- Imager: `Verification failed. Contents were different.`
- After a failed write, `diskutil list` shows the card with **no partitions**. This is expected: Imager writes the partition table last, so a failed write leaves the card unbootable.

### Wiping an old card

- **Most thorough:** the official [SD Memory Card Formatter](https://www.sdcard.org/downloads/formatter/), using "Overwrite format".
- **From Terminal:** `diskutil zeroDisk /dev/diskN` (slow, writes zeros everywhere).
- **Quick:** `diskutil eraseDisk FAT32 SDCARD MBRFormat /dev/diskN`.
- Wiping does **not** fix a worn card.
- Flash cards may keep old data in blocks they have retired. If a card ever held private keys, physically destroy it before throwing it out, and/or revoke those keys.

---

## 2. Flash the OS (Raspberry Pi Imager)

Install Imager with `brew install --cask raspberry-pi-imager`.

1. **Device:** Raspberry Pi 3
2. **OS:** Raspberry Pi OS (other) → **Raspberry Pi OS Lite (64-bit)**
   - We used the Trixie release of 15 Sep 2026: Debian 13, Python 3.13.
   - **Lite**: no desktop. The Pi is headless and only has 1 GB of RAM.
   - **64-bit**: PyPI has prebuilt `aarch64` wheels for numpy, pillow, etc. 32-bit would need piwheels and is much more painful with uv.
   - **Pick it from Imager's list** rather than "Use custom" with a downloaded `.img`. The settings step in point 4 may not be offered for custom images.
3. **Storage:** the SD card. Check the size.
4. **OS customisation → Edit settings:**
   - **Hostname:** `nightlight`. The Pi is then reachable as `nightlight.local`.
   - **Username:** `pi`, with a new password.
   - **Wi-Fi:** your **2.4 GHz** network. If your router has separate 2.4/5 GHz names, pick the 2.4 one. Set the country (CA).
   - **Locale:** time zone and keyboard.
   - **Services:** enable SSH, **public-key authentication only**. Paste your Mac's key: `cat ~/.ssh/id_rsa.pub | pbcopy`.
   - **Raspberry Pi Connect:** skip for now (see [Optional](#7-optional)).
5. **Write**, and let it finish **including verification**. Keep the Mac awake and don't touch the card.

Trixie applies these settings on first boot using **cloud-init**: `ds=nocloud` appears in the kernel command line. First boot takes a few minutes and expands the filesystem to fill the card.

---

## 3. First connection from the Mac

### Clearing the old host key

A reinstalled Pi has new SSH host keys. If you've connected to that IP before, you'll get `WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!`. This is expected after a reflash:

```bash
ssh-keygen -R 192.168.1.134          # forget the old key (also for nightlight.local if used before)
ssh pi@nightlight.local              # check the fingerprint shown, then type yes
```

- Always include `pi@`. Plain `ssh <host>` uses your Mac username, which doesn't exist on the Pi.
- To check the fingerprint is genuine, run this on the Pi itself (keyboard and screen) and compare: `ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub`.

### SSH alias

Add to `~/.ssh/config` on the Mac:

```
Host pi
  HostName nightlight.local
  User pi
  IdentityFile ~/.ssh/id_rsa
```

Then `ssh pi`, `scp file pi:~/` and `rsync … pi:~/` all work.

- **Why `.local`:** it uses mDNS (Bonjour on the Mac, Avahi on the Pi). The Mac asks the local network "who is `nightlight.local`?" and the Pi replies with its current IP. It keeps working if the router gives the Pi a new IP.
- It only works on the same network, and some guest or mesh networks block it.
- If `.local` doesn't resolve, use the IP as `HostName`.
- Remove any old, broken `rasp_pi` blocks. The old config had two `Host rasp_pi` blocks; the first set `HostName rasp_pi`, which overrode the IP in the second.

### Sanity check

```bash
cat /etc/os-release | grep PRETTY; uname -m; python3 --version
# Debian GNU/Linux 13 (trixie) / aarch64 / Python 3.13.x
```

---

## 4. System setup (on the Pi)

### Updates

```bash
sudo apt update && sudo apt full-upgrade -y
```

If `apt update` fails with errors like this, the saved package lists are damaged:

```
Error: Problem parsing dependency … of speech-dispatcher …
Error: The package lists or status file could not be parsed or opened.
```

We hit this after an unclean shutdown. Delete the lists and download them again:

```bash
sudo rm -rf /var/lib/apt/lists/*
sudo apt clean
sudo apt update && sudo apt full-upgrade -y
```

If it keeps happening, check the card and power (see [Health checks](#6-health-checks--habits)).

### Build tools, git, SPI

```bash
sudo apt install -y git build-essential python3-dev
sudo raspi-config nonint do_spi 0
sudo reboot
```

- **`git`:** to clone the repo.
- **`build-essential`:** gcc and make. `noise` and a few Pi hardware packages pulled in by `adafruit-blinka` have no prebuilt wheels, so uv compiles them.
- **`python3-dev`:** Python C headers for compiling against the system Python. Not needed if uv uses its own managed Python, but harmless.
- **`do_spi 0`:** enables SPI (`0` = enable in raspi-config). The LEDs are driven over SPI (`SCK`/`MOSI`). This is the same as `dtparam=spi=on` in `/boot/firmware/config.txt`.

After the reboot:

```bash
ls /dev/spidev*        # expect /dev/spidev0.0 /dev/spidev0.1
```

### Turn off Wi-Fi power saving

The Pi's Wi-Fi driver enables power saving by default, and NetworkManager leaves it alone (its default is `ignore`). On the Pi 3 this makes the Pi doze off: SSH times out, `ping` says "Host is down", and it comes back if you retry later.

Check:

```bash
iw dev wlan0 get power_save        # "Power save: on" = enabled
```

Disable it for all Wi-Fi connections with a NetworkManager config file. Run these one at a time; they're kept short because long lines got split when pasted into the terminal:

```bash
cd /etc/NetworkManager/conf.d
```

```bash
echo -e '[connection]\nwifi.powersave = 2' | sudo tee wifi-ps-off.conf
```

```bash
cat wifi-ps-off.conf
```

```bash
cd ~
```

```bash
sudo reboot
```

After reconnecting:

```bash
iw dev wlan0 get power_save        # want: Power save: off
```

Notes:

- `wifi.powersave` values: `2` = disable, `3` = enable, `1` = ignore, `0` = use the global default. Per-connection profiles default to `0`, so the global file applies to them.
- The key **must** be under a `[connection]` header. Some forum posts use a bare `wifi.powersave=off`, which doesn't match NetworkManager's documented format.
- Files in `/etc/NetworkManager/conf.d/` are read in order, with later files overriding earlier ones. If another file there turns power saving on, make sure this one sorts after it.
- If it still says `on`, the Wi-Fi profile has its own value set. Find the profile name with `nmcli -f NAME,TYPE connection show` (on Trixie it may be `netplan-…`, not `preconfigured`), then:
  ```bash
  sudo nmcli connection modify "<NAME>" 802-11-wireless.powersave 2
  ```
- The old `iw dev wlan0 set power_save off` in `rc.local` approach is outdated. It doesn't survive reconnects reliably, and current Pi OS has no `rc.local`.
- References:
  - [NetworkManager.conf](https://networkmanager.dev/docs/api/latest/NetworkManager.conf.html)
  - [802-11-wireless settings](https://networkmanager.dev/docs/api/latest/settings-802-11-wireless.html)
  - [Pi forum thread](https://forums.raspberrypi.com/viewtopic.php?t=357629)

### uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
exec $SHELL            # reload PATH
uv --version
```

---

## 5. Project setup

### SSH keys

Three SSH connections matter, and each uses a different key:

| Connection | Who proves identity | Key | Where the public half goes |
|---|---|---|---|
| **Mac → Pi** (`ssh pi`) | the Mac | Mac's `~/.ssh/id_rsa` | Pi's `~/.ssh/authorized_keys` (set by Imager) |
| **Pi → GitHub** (clone/push from the Pi) | the Pi | Pi's `~/.ssh/id_ed25519` | GitHub → Settings → SSH and GPG keys |
| **Mac → GitHub** (push from the Mac) | the Mac | Mac's `~/.ssh/id_rsa` | GitHub → Settings → SSH and GPG keys |

#### How the keys work

- A key is a **pair** of files:
  - **Private** (`id_ed25519`) never leaves the machine it was made on.
  - **Public** (`id_ed25519.pub`) is safe to paste anywhere.
- **Key types:**
  - **Ed25519** is the modern default and what GitHub recommends: short, fast, no size to choose.
  - **RSA** (`id_rsa`) is older but still works.
- **Default names:** SSH automatically tries the standard filenames (`id_ed25519`, `id_rsa`, …). A key with a custom name, like the old `github-sean`, needs a `Host` alias with `IdentityFile` in `~/.ssh/config`.
- **Permissions:** private keys must be `-rw-------` (`chmod 600`). Otherwise SSH ignores them with `UNPROTECTED PRIVATE KEY`.

#### Mac → Pi

Handled by Imager: paste the Mac's `~/.ssh/id_rsa.pub` under Services → SSH → public-key only. For the `ssh pi` alias, `.local` and host-key warnings, see [section 3](#3-first-connection-from-the-mac).

**Letting Anders log in too.** Imager only takes one key. Either ask Anders for a public key and append it to `~/.ssh/authorized_keys` on the Pi, or re-add the old one from the backup, run from the **Mac** (this also re-adds yours):

```bash
ssh-copy-id -f -i ~/pi-backup/ssh/authorized_keys pi
```

#### Pi → GitHub (fresh key)

Generate a key on the Pi rather than copying old ones (see below for why). On the **Pi**, one at a time:

```bash
ssh-keygen -t ed25519 -C "nightlight-pi" -f ~/.ssh/id_ed25519
```

- Press Enter at the passphrase prompts for no passphrase.

```bash
cat ~/.ssh/id_ed25519.pub
```

- Add the printed line on GitHub: **Settings → SSH and GPG keys → New SSH key**, titled e.g. "nightlight Pi".

```bash
ssh -T git@github.com
```

- Expect `Hi <username>! You've successfully authenticated, but GitHub does not provide shell access.` The "no shell access" part is normal.
- On the very first connection it asks to trust GitHub's host key. Compare with [GitHub's published fingerprints](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/githubs-ssh-key-fingerprints), then type `yes`.

Clone with the **plain** address `git@github.com:…`, which uses `id_ed25519` automatically.

- Pushes from the Pi show up as the GitHub account the key was added to.
- If Anders needs to push from the Pi as themselves, they add their own key to their account and use a `Host` alias (see below).

#### Why not reuse the old Pi keys

The old install had `github-sean` / `github-anders` keys with `Host github.com-sean` / `github.com-anders` aliases, plus `git-assume-sean` / `git-assume-anders` shell aliases that switched the repo's `origin` between them. They were backed up to `~/pi-backup/ssh/` on Sean's Mac.

- **Restored on 2026-10-04, `github-sean` was rejected:** `git@github.com: Permission denied (publickey)`, with correct `600` permissions. The key is no longer, or never was, on the GitHub account.
- **They lived on the failing card** and date from Jan 2024. Delete them from GitHub's SSH keys page if they're still listed, and remove them from the Pi (`rm ~/.ssh/github-* ~/.ssh/config`) unless Anders still uses theirs.

If per-person identities are needed again, recreate the pattern with fresh keys:

```
# ~/.ssh/config on the Pi
Host github.com-anders
    HostName github.com
    User git
    IdentityFile ~/.ssh/github-anders
```

```bash
# ~/.bashrc
alias git-assume-anders="git remote set-url origin git@github.com-anders:joltex/project_nightlight.git"
```

#### Mac → GitHub

The Mac's clone originally used an **HTTPS** remote (`https://github.com/…`).

- Fetching worked because the repo is public, but `git push` asked for a username and password.
- GitHub doesn't accept account passwords for git; it needs a token.
- The Mac's `id_rsa` is already on GitHub (`ssh -T git@github.com` → `Hi stycho!`), so switch the remote to SSH:

```bash
git remote set-url origin git@github.com:joltex/project_nightlight.git
```

- **Alternative:** stay on HTTPS and run `gh auth login`, choosing HTTPS and "Authenticate Git with your GitHub credentials" → Yes.
- **Pushing to `joltex/project_nightlight`** requires your account to be a collaborator on the repo.

### Clone and install

```bash
mkdir -p ~/dev && cd ~/dev
git clone git@github.com:joltex/project_nightlight.git
cd project_nightlight
git switch migrate-to-uv-and-python-3-13          # until the uv migration is merged
uv sync --locked
uv run nightlight play examples/test_pattern.nl
```

Known risks on first `uv sync`:

- **`noise`** (2015 C extension) has to compile on Python 3.13. Untested at time of writing.
- **`adafruit-blinka`** is unpinned. The old pin `5.9.2` (2020) predates Python 3.13/Trixie. If the LEDs don't work, look here first.

---

## 6. Health checks & habits

```bash
dmesg | grep -iE 'mmc|ext4|I/O error|corrupt'   # want: no I/O errors / corruption
vcgencmd get_throttled                          # want: throttled=0x0
```

- **`orphan cleanup on readonly fs`** in `dmesg` means the previous shutdown was unclean (power pulled while writing). We saw this right before the broken apt lists.
- **`throttled` ≠ `0x0`** means under-voltage or overheating, now or since boot. A weak power supply can corrupt the SD card. Use the official 5.1 V / 2.5 A supply.
- **Always shut down before unplugging:**
  ```bash
  sudo shutdown -h now
  ```
  Wait for the green LED to stop blinking, then pull power.

---

## 7. Optional

### Remote access (outside the home network)

The old setup forwarded a router port → Pi SSH (`external_rasp_pi` in `~/.ssh/config`). That exposes SSH to the internet. Prefer one of these, and **remove the port forward**:

- **Raspberry Pi Connect** (`rpi-connect-lite` on Lite): an official, free browser-based remote shell. The Pi connects outbound, so no ports are opened. You need a Raspberry Pi ID. It isn't real SSH: you can't use scp/rsync or your SSH config through it.
- **Tailscale:** a private network between your devices, giving normal `ssh pi@nightlight` from anywhere. Also no port forwarding.

### Fixed IP

`.local` makes this unnecessary for SSH at home. If you want a stable IP (e.g. for a port forward), set a **DHCP reservation** for the Pi in the router (`http://192.168.1.1`). The old install had no static IP configured on the Pi itself.

### Backups

- A spare card plus a periodic image makes the next failure a 10-minute swap:
  ```bash
  sudo dd if=/dev/rdiskN bs=4m status=progress | gzip > ~/nightlight-pi-YYYYMMDD.img.gz
  ```
  Restore with Imager → "Use custom".
- Everything important should be in git. Don't leave work only on the Pi. The old card had five stale copies of the repo, a 2019 `temp` branch and an unpushed stash.

---

## Troubleshooting quick reference

| Symptom | Cause / fix |
|---|---|
| `REMOTE HOST IDENTIFICATION HAS CHANGED` | Reflashed Pi has new host keys. Run `ssh-keygen -R <host>`. |
| `ssh 192.168.1.x` asks for a password / fails | Missing `pi@` (it's using your Mac username), or the key isn't on the Pi. |
| SSH times out / ping "Host is down" | Pi is off, still booting, or dozing on Wi-Fi. Check `iw dev wlan0 get power_save` and [turn power saving off](#turn-off-wi-fi-power-saving). |
| Pasted command fails with `-bash: /etc/…: No such file or directory` | The terminal split a long line on paste, so the path ran as its own command. Paste shorter commands, or `cd` into the folder first. |
| Command "works" but the file isn't on the Pi | It ran on the Mac. Check the prompt: `pi@nightlight:~ $` is the Pi, `❯` is the Mac. |
| `git@github.com: Permission denied (publickey)` | GitHub doesn't recognise the key offered. Check `ls -l ~/.ssh` (private keys `-rw-------`), then `ssh -vT git@github.com 2>&1 \| grep -iE 'offering\|denied'` to see which key was tried. Add the right `.pub` to GitHub, or [make a fresh key](#pi--github-fresh-key). |
| `git push` asks for GitHub username/password | HTTPS remote. [Switch to SSH](#mac--github) or use `gh auth login`. |
| `nightlight.local` doesn't resolve | mDNS blocked on that network. Use the IP. |
| Mac: "The disk you attached was not readable" | Normal for a Pi card (the ext4 partition). Click **Ignore**. If `bootfs` doesn't mount either, the flash is incomplete. |
| Imager write/verify failure | Dying card or flaky reader. Check the adapter lock switch, try another reader, then replace the card. |
| `apt` "could not be parsed" errors | Damaged package lists. Delete `/var/lib/apt/lists/*` and re-run `apt update`. |
| No `/dev/spidev*` | SPI is off. Run `sudo raspi-config nonint do_spi 0` and reboot. |
| `uv sync` compiling forever | A heavy package has no wheel for this platform. Check `uname -m` is `aarch64`. |
