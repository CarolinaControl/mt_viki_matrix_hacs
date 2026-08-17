# MT-VIKI HDMI Matrix — Home Assistant integration

Control an MT-VIKI HDMI matrix switcher (4x4 / 8x8 / 16x16, e.g. the
MT-HD44L / MT-HD88L / MT-HD1616L family) from Home Assistant over its
TCP/IP control port.

Built from the manufacturer's control-protocol documentation: TCP port
**8080**, plain-text commands terminated with `.` (identical syntax to
the unit's RS232 port at 115200-8-N-1).

## What you get

- One `media_player` entity per **output**, with a `source` dropdown
  listing every **input** — pick a source in the HA UI/dashboard/voice
  assistant the same way you'd pick an app on a TV.
- Turning an output "off" blanks that output (`0X[out].`); turning it
  back on restores the last-selected input.
- A `switch.buzzer` entity to mute/unmute the confirmation beep.

## Not (yet) implemented

The protocol table in the manual doesn't expose a query/status command
over TCP (status polling is only documented via the front-panel LCD),
so entity state is **optimistic** — it reflects the last command HA
sent, not a live read-back from the matrix. If someone changes a route
from the physical panel or remote, Home Assistant won't see it until
you change it from HA again. Scene save/recall (`Save[Y].`/`Recall[Y].`)
and the "all-to-one" broadcast command aren't wired to entities yet —
they're trivial to add as `button` entities using the same `hub.py`
helper if you want them; shout if you'd like that added.

## Installation (HACS custom repository)

1. In HA: HACS → the "⋮" menu (top right) → **Custom repositories**.
2. Add this repo's URL, category **Integration**.
3. Install "MT-VIKI HDMI Matrix", then restart Home Assistant.
4. Settings → Devices & Services → **Add Integration** → search
   "MT-VIKI HDMI Matrix".
5. Enter the matrix's IP address (check the front-panel LCD — default
   is `192.168.1.200`), port `8080`, and pick your matrix size (or
   "custom" for an asymmetric input/output count).

## Manual install (no HACS)

Copy `custom_components/mt_viki_matrix/` into your Home Assistant
`config/custom_components/` folder, restart HA, then follow steps 4–5
above.

## Repo layout

```
hacs.json
custom_components/mt_viki_matrix/
  __init__.py        # sets up the TCP hub, forwards to platforms
  hub.py              # persistent async TCP client, sends "cmd." and reads the reply
  config_flow.py      # UI setup: host/port/size
  const.py             # command templates from the protocol doc
  media_player.py     # one entity per output
  switch.py            # buzzer on/off
  manifest.json
  strings.json / translations/en.json
```

## Protocol reference (for anyone extending this)

| Command | Meaning |
|---|---|
| `[in]X[out].` | Switch `in` → `out`, e.g. `3X5.` |
| `[in]X[out1]&[out2]&....` | Switch `in` to several outputs, e.g. `3X5&6&7&8.` |
| `[in]All.` | Switch `in` to every output |
| `0X[out].` | Blank a single output |
| `All1.` | Reset all outputs to 1:1 with matching input |
| `Save[1-9].` | Save current routing to scene `1-9` |
| `Recall[1-9].` | Recall scene `1-9` |
| `BeepON.` / `BeepOFF.` | Confirmation beep on/off |

Commands are case-insensitive; the trailing `.` is mandatory. Input
range depends on matrix size (e.g. 1–8 on an 8x8 unit).

## Troubleshooting

- **Config flow says "cannot connect":** confirm the matrix and HA are
  on the same network/VLAN, and that port 8080 isn't blocked by a
  firewall. You can sanity-check from a terminal first:
  `printf '3X5.' | nc <matrix-ip> 8080`
- **Switch does nothing:** some firmware doesn't send a reply for
  every command — that's expected and handled (the integration treats
  a read timeout as "no reply", not an error). Watch the matrix's own
  LCD/beep to confirm the switch happened.
