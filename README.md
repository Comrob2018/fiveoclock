# It’s 5 O’Clock Somewhere — PyQt6

A tiny desktop app that lists the **countries where it’s currently 5 PM** (“It’s 5 O’Clock in: …”).

* 🏝️ **Look & feel:** palm‑tree header, clean list (no boxes), and your beach‑to‑sea gradient.
* ⏱️ **Auto‑refresh:** aligns to the **top of every hour**.
* 🔔 **Bottom toast:** a subtle, fading **“Last updated …”** notification (local time + UTC).
* 🌐 **Time logic:** walks all IANA time zones and maps them to countries via `pytz`.


---

## Table of Contents

* [Features](#features)
* [Screenshot](#screenshot)
* [Requirements](#requirements)
* [Installation](#installation)
* [Usage](#usage)
* [How it works](#how-it-works)
* [Customization](#customization)

  * [Gradient / Background](#gradient--background)
  * [Header (palms & title)](#header-palms--title)
  * [List text color](#list-text-color)
  * [Toast timing](#toast-timing)
* [Packaging](#packaging)

  * [Windows `.exe`](#windows-exe)
  * [macOS `.app`](#macos-app)
* [Repository layout](#repository-layout)
* [Troubleshooting](#troubleshooting)
* [Limitations & Notes](#limitations--notes)
* [Contributing](#contributing)
* [License](#license)

---

## Features

* Shows **country names only**, in UPPERCASE, under the heading **“It’s 5 O’Clock in:”**
* **Palm‑tree** icons on both sides of the header for a fun, vacation vibe 🌴
* **Hourly** refresh (top‑of‑hour) + on‑demand refresh from the **Actions → Refresh Now** menu
* **Toast** bubble at the bottom that fades away after each refresh
* Simple, readable list (no list item boxes)

## Screenshot


<img width="632" height="316" alt="image" src="https://github.com/user-attachments/assets/67b1bba4-26cf-4632-876f-7593ac91351e" />


## Requirements

* **Python** 3.9+
* **PyQt6**
* **pytz**

Install:

```bash
pip install PyQt6 pytz
```

## Installation

1. Clone (or download) the repo.
2. Ensure dependencies are installed (see above).

## Usage

Run the script:

```bash
python five_oclock_somewhere.py
```

The list will populate immediately and then auto‑refresh **exactly on the hour**.

## How it works

* We iterate every zone from `pytz.all_timezones` and convert the current time from UTC using `datetime.now(timezone.utc)`.
* If a zone’s **local hour == 17** (i.e., 5 PM), we collect the **owning country code(s)** from `pytz.country_timezones`.
* We map those codes to display names via `pytz.country_names`, de‑duplicate, **uppercase**, and sort.
* The list is rendered in a `QListWidget` with minimal styling.

## Customization

Most tweaks live in two places:

* **`apply_style()`** — background gradient/colors and text color.
* **`countries_at_five_now()`** — selection logic (currently, any minute during the 17:00 hour).

### Gradient / Background

The app uses your requested **vertical gradient** (bottom → top):

```
#E9D59C → #738B13 → #256940 → #64B8B1 → #22BED9
```

These stops are set in `apply_style()`:

```css
QWidget#root {
  background: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0,
                               stop:0    #E9D59C,
                               stop:0.25 #738B13,
                               stop:0.50 #256940,
                               stop:0.75 #64B8B1,
                               stop:1    #22BED9);
}
```

> Prefer a solid color instead? Replace `background:` with `background-color: #64B8B1;` (already supported in the stylesheet).

### Header (palms & title)

The line is centered and includes palms on both sides. Edit the label HTML in the constructor:

```python
self.header_label = QLabel(
    "<div style='font-size:30px; font-weight:800; letter-spacing:1px;'>"
    "🌴&nbsp;&nbsp;It\'s 5 O\'Clock in:&nbsp;&nbsp;🌴"  # <- swap emojis or text here
    "</div>"
)
```

### List text color

The country names are plain list items. Their color is forced via CSS to avoid theme/OS overrides:

```css
QListWidget { color: #0f1b26; }
QListWidget::item { color: #0f1b26; }
QListWidget::item:selected { background: rgba(0,0,0,0.08); color: #0f1b26; }
```

Prefer a specific color? Change the hex values above, or set per item in code:

```python
from PyQt6.QtGui import QColor
item.setForeground(QColor("#0f1b26"))
```

### Toast timing

The bottom toast uses a small fade animation. Adjust its timing in `ToastLabel.show_message(...)`:

```python
self.toast.show_message(msg, duration_ms=3500, fade_ms=600)
```

## Packaging

You can bundle the app with **PyInstaller**. From the project root:

### Windows `.exe`

```bash
pyinstaller --noconfirm --clean \
  --name "FiveOClockSomewhere" \
  --windowed --onefile \
  five_oclock_somewhere.py
```

The EXE will be in `dist/`.

### macOS `.app`

> Build the mac app **on macOS** for best results.

```bash
pyinstaller --noconfirm --clean \
  --name "FiveOClockSomewhere" \
  --windowed \
  five_oclock_somewhere.py
```

The `.app` bundle will be in `dist/`.

## Repository layout

```
.
├─ five_oclock_somewhere.py   # main script (PyQt6)
├─ README.md                  # this file
├─ requirements.txt           # optional: pin versions (PyQt6, pytz)
└─ docs/
   └─ screenshot.png          # optional: add your screenshot
```

Suggested `.gitignore` entries:

```
# Python
__pycache__/
*.py[cod]

# PyInstaller
build/
dist/
*.spec

# OS
.DS_Store
Thumbs.db
```

## Troubleshooting

* **White country names on some themes** → we explicitly set list colors in the stylesheet (see above). If you still see white, confirm your platform/Qt theme isn’t overriding palette roles.
* **App doesn’t update exactly on the hour** → check your system clock sync (NTP). The app schedules a one‑shot timer to the next hour boundary.
* **Some tiny regions or territories missing** → we only include zones that map back to an ISO country via `pytz.country_timezones`.

## Limitations & Notes

* “5 o’clock” means **any minute** during the 17:00 hour (5:00–5:59). If you want *exactly* 5:00, we can add a toggle to require `minute == 0`.
* Timezone data and country mappings are provided by **pytz**; unusual/alias zones may behave differently.
* The app currently focuses on **5 PM**. (A 5 AM toggle can be re‑added easily.)
