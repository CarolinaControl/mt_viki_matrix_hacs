# MT-VIKI HDMI Matrix — Home Assistant integration

Control an MT-VIKI L-series HDMI matrix switcher (4x4 / 8x8 / 16x16 —
MT-HD44L / MT-HD88L / MT-HD1616L) from Home Assistant.

## The actual protocol

The printed manual documents a plain-text RS232/TCP command set, but the
L-series units actually control switching through a small HTTP CGI
endpoint used by their built-in web GUI:

```
POST http://<matrix-ip>/cgi-bin/matrixs.cgi
Authorization: Basic YWRtaW46YWRtaW4=      (fixed admin:admin, baked into firmware)
Content-Type: application/x-www-form-urlencoded

matrixdata={"COMMAND": "SW <input> <output> "}
```

This was confirmed by cross-checking a working community integration for
the MT-HD88L (credit: [Timman70 / timcloud](https://github.com/Timman70/MT-VIKI-MT-HD88L-Matrix-Switch)).
Raw TCP text commands on port 8080 (as documented in the manual) do not
appear to do anything on these units -- the port is open, but nothing is
listening for that protocol on it.

## What you get

- One `media_player` entity per **output**, with a `source` dropdown
  listing every **input**.

## Not (yet) implemented / known limitations

- **No status polling.** There's no known query/read-back endpoint, so
  entity state is optimistic -- it reflects the last command HA sent, not
  a live read from the matrix. Switching from the matrix's own remote or
  web GUI won't be reflected in HA until you change it from HA again.
- **No "off"/blank command.** The manual's `0X[out].` blanking command is
  for the RS232/TCP protocol, which doesn't appear to be active on these
  units. If you find the equivalent HTTP command (browser dev tools ->
  Network tab while clicking "blank" in the matrix's own web GUI, if it
  has one, will show it), it's a one-line addition to `hub.py`.
- **No scene save/recall or buzzer control** -- same reason: unconfirmed
  HTTP equivalents. Easy to add once you capture the right `COMMAND`
  string from the web GUI's own network traffic.

## Installation (HACS custom repository)

1. In HA: HACS -> the ":" menu (top right) -> **Custom repositories**.
2. Add this repo's URL, category **Integration**.
3. Install "MT-VIKI HDMI Matrix", then restart Home Assistant.
4. Settings -> Devices & Services -> **Add Integration** -> search
   "MT-VIKI HDMI Matrix".
5. Enter the matrix's IP address and pick your matrix size (or "custom"
   for an asymmetric input/output count). No port or credentials needed
   -- both are fixed by the firmware.

## Manual install (no HACS)

Copy `custom_components/mt_viki_matrix/` into your Home Assistant
`config/custom_components/` folder, restart HA, then follow steps 4-5
above.

## Repo layout

```
hacs.json
custom_components/mt_viki_matrix/
  __init__.py        # sets up the hub, forwards to the media_player platform
  hub.py              # HTTP client for /cgi-bin/matrixs.cgi
  config_flow.py      # UI setup: host + matrix size
  const.py
  media_player.py     # one entity per output
  manifest.json
  strings.json / translations/en.json
```

## If this still doesn't switch anything

1. Open `http://<matrix-ip>/` in a browser -- does its own web GUI load?
   If not, we have the wrong IP, or this unit's firmware genuinely
   doesn't expose a web GUI (in which case this integration's approach
   won't work and we're back to figuring out the real protocol from
   scratch -- packet-capturing the vendor's Windows control software with
   Wireshark is the most reliable way to reverse-engineer it).
2. If the web GUI loads, open browser dev tools (F12) -> Network tab,
   click a source button in the GUI itself, and see exactly what request
   fires. If it's not `/cgi-bin/matrixs.cgi`, or the body looks
   different, send me what you see and I'll adjust `hub.py` to match.
3. Enable debug logging in HA and try selecting a source again:
   ```yaml
   logger:
     logs:
       custom_components.mt_viki_matrix: debug
   ```
   Check Settings -> System -> Logs for the exact request sent and the
   matrix's HTTP response -- that tells us if it's rejecting the command
   (bad auth/format) versus not receiving it at all.
