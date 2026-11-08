# ATtiny85 Candle Light (8-LED WS2812B Ring)

A standalone candle-flicker light: an ATtiny85 driving an 8-LED WS2812B ring, powered by a 5V USB wall charger, built on protoboard.

## Bill of Materials

| Part | Qty | Notes |
|---|---|---|
| ATtiny85 (DIP-8) | 1 | ATtiny85 or ATtiny85V both run at 5V |
| DIP-8 IC socket | 1 | So the chip can be pulled for reprogramming |
| WS2812B 8-LED ring | 1 | 5V, pins: DIN, 5V, GND (DOUT unused) |
| 0.1µF ceramic capacitor | 1 | Decoupling at the ATtiny |
| 470 to 1000µF electrolytic, 6.3V+ | 1 | Bulk cap at the ring |
| 330 to 470Ω resistor | 1 | Series resistor on the data line |
| USB breakout (USB-A male or USB-C) or cut USB cable | 1 | Only 5V and GND are used |
| 5V USB wall charger, 1A+ | 1 | Not a power bank (they auto-shutoff at low draw) |
| Mini protoboard, about 9x9 holes, 2.54mm pitch | 1 | Isolated pads, roughly 25mm square with a mounting hole |
| Hookup wire (22 AWG for power, 26-30 AWG for data) | | Plus a few bare leg offcuts for bridges |

### Programming hardware (one of)

- **USBasp** (about $3 on AliExpress), plus a 10-pin to 6-pin adapter if needed
- **Arduino Uno** running the ArduinoISP sketch, plus a 10µF capacitor

## Power Budget

- Each WS2812B draws up to about 60mA at full white. 8 LEDs = about 480mA worst case.
- A warm flicker (red-heavy, never full white) with `setBrightness(180)` averages well under 150mA.
- A 1A charger has plenty of headroom.

## ATtiny85 Pinout

```
          +--\/--+
 RESET PB5 |1    8| VCC
       PB3 |2    7| PB2 (SCK)
  DATA PB4 |3    6| PB1 (MISO)
       GND |4    5| PB0 (MOSI)
          +------+
```

Data uses **PB4 (pin 3)** because it is not shared with the ISP programming pins. That means you can reprogram the chip in-circuit without the ring interfering.

## Schematic

```
USB 5V ──┬──────────────┬───────────────┬──────── Ring 5V
         │              │               │
         │           [0.1µF]       [470-1000µF] (+ to 5V)
         │              │               │
USB GND ─┼──────────────┴───────────────┴──────── Ring GND
         │
ATtiny85 pin 8 (VCC) ── 5V
ATtiny85 pin 4 (GND) ── GND
ATtiny85 pin 3 (PB4) ── [330-470Ω] ── Ring DIN
```

## Protoboard Layout (Mini 9x9 Board)

The layout uses an 8x8 area (columns A-H, rows 1-8), so it fits a roughly 9x9 board with a spare row and column. Row 1 stays empty to clear the mounting hole. Count your board's holes first and shift the layout if needed.

View from the **component side**, with the socket notch facing row 1.

```
       A   B   C   D   E   F   G   H
   1   .   .   .   .   .   .   .   .
   2   .   .   .   V===o===o===o===U
                           |
   3   .   .   1   .   c===8   .   .
   4   D   .   2   .   .   7   .   .
       |
   5   r   R===3   .   .   6   .   .
   6   .   .   4===c   .   5   .   .
               |
   7   .   .   o   .   .   .   .   .
               |
   8   .   .   o===G===o===o===o===u
```

### Legend

| Mark | Meaning |
|---|---|
| `1`-`8` | DIP-8 socket pins (C3-C6 = pins 1-4, F6-F3 = pins 5-8) |
| `c` | 0.1µF ceramic cap legs (E3 and D6), placed diagonally inside the socket footprint |
| `R`, `r` | Series resistor, standing vertically (B5 and A5) |
| `V` | Wire to ring 5V |
| `G` | Wire to ring GND |
| `D` | Wire to ring DIN |
| `U` | Wire from USB 5V |
| `u` | Wire from USB GND |
| `===` and `\|` | Solder bridges or bare-wire jumpers on the solder side |
| `o` | Rail pad (just part of a bridge) |

### Connections

- **5V rail (row 2):** bridge D2 to H2. Bridge F2 down to F3 (pin 8).
- **GND rail (row 8):** bridge C8 to H8. Bridge C6 (pin 4) down through C7 to C8.
- **Decoupling:** solder the 0.1µF cap into E3 and D6, then bridge E3 to F3 (pin 8) and D6 to C6 (pin 4). It sits under the socket, so use an open-frame socket and fit the cap **before** the socket.
- **Data:** bridge C5 (pin 3, PB4) to B5. Stand the resistor in B5 and A5. Bridge A5 to A4, where the ring DIN wire lands.
- **Bulk cap:** this board has no room for it. Solder the 470-1000µF cap directly across the ring's 5V and GND pads, laid on its side. Watch the polarity.
- **Unused pins:** leave pins 1, 2, 5, 6, and 7 unconnected. Pin 7 (PB2) floats on purpose to seed `randomSeed()`.

### Build order

1. 0.1µF cap (under the socket)
2. DIP-8 socket
3. Resistor
4. Solder-side bridges
5. Wires: USB in, then ring 5V, GND, DIN

### Notes

- With isolated pads, it's easy to bridge neighboring pads by accident. Pins 4 and 5 and pins 8 and 1 are the risky pairs. Check every adjacent pair with a continuity tester before inserting the chip.
- Keep the ring wires short. If the board mounts behind the ring (an 8-LED ring is typically about 32mm across), 3-5cm leads are plenty.
- Run 5V and GND to the ring with wire heavier than the data line. 22 AWG is fine.
- The socket adds about 4mm of height. If that matters once the firmware is final, solder the chip directly and reprogram it with a DIP-8 test clip.

## Software Setup

### 1. Install ATTinyCore

1. Arduino IDE > Settings > Additional Boards Manager URLs, add:
   `http://drazzy.com/package_drazzy.com_index.json`
2. Boards Manager: install **ATTinyCore** (Spence Konde).
3. Library Manager: install **Adafruit NeoPixel**.

### 2. Connect the programmer

**USBasp:** connect the 6-pin ISP header to the ATtiny85:

| ISP signal | ATtiny85 pin |
|---|---|
| MISO | 6 (PB1) |
| SCK | 7 (PB2) |
| RESET | 1 (PB5) |
| VCC | 8 |
| MOSI | 5 (PB0) |
| GND | 4 |

Some USBasp units with older firmware can't talk to a fresh chip running at 1MHz. If you see `cannot set sck period` or the chip isn't found, set the board's slow-clock jumper (often labeled JP3 or "slow SCK") for the first fuse burn.

**Arduino Uno as ISP:**

1. Upload File > Examples > ArduinoISP to the Uno.
2. Wire Uno pin 13 to ATtiny pin 7, 12 to 6, 11 to 5, and 10 to 1. Then wire 5V to 8 and GND to 4.
3. Put a 10µF capacitor between Uno RESET and GND (+ to RESET). This stops the Uno from resetting itself when the IDE starts uploading.
4. Programmer: **Arduino as ISP**.

### 3. Board settings

- Board: **ATtiny25/45/85 (No bootloader)**
- Chip: **ATtiny85**
- Clock: **8 MHz (internal)**
- Programmer: USBasp or Arduino as ISP

### 4. Burn fuses (required, once per chip)

Run **Tools > Burn Bootloader**. With the "No bootloader" board this only writes the fuses. It switches the chip from its factory 1MHz clock to 8MHz.

**If you skip this step, the LEDs will not work.** At 1MHz the chip is too slow for WS2812B timing.

### 5. Upload

Use **Sketch > Upload Using Programmer** (or plain Upload, which behaves the same with the No bootloader board).

## Firmware

The firmware uses integer math only. Floats pull in a few KB of math library code, and the ATtiny85 only has 8KB of flash.

```cpp
#include <Adafruit_NeoPixel.h>

#define DATA_PIN   4      // PB4, physical pin 3
#define NUM_LEDS   8
#define FRAME_MS   30     // ~33 fps

Adafruit_NeoPixel ring(NUM_LEDS, DATA_PIN, NEO_GRB + NEO_KHZ800);

uint8_t level[NUM_LEDS];
uint8_t target[NUM_LEDS];

void setup() {
  ring.begin();
  ring.setBrightness(180);         // cap overall brightness and current
  randomSeed(analogRead(A1));      // A1 = PB2, left floating for noise
  for (uint8_t i = 0; i < NUM_LEDS; i++) {
    level[i] = 200;
    target[i] = 200;
  }
}

void loop() {
  // Occasional "draft": all LEDs dip together
  bool gust = random(100) < 2;

  for (uint8_t i = 0; i < NUM_LEDS; i++) {
    if (gust) {
      target[i] = (uint8_t)random(60, 120);
    } else if (random(4) == 0) {
      target[i] = (uint8_t)random(140, 256);
    }

    // Ease toward target
    int16_t d = (int16_t)target[i] - level[i];
    level[i] += d / 4;

    uint16_t l = level[i];
    uint8_t r = l;
    uint8_t g = (l * 100) >> 8;    // ~39% of red: warm orange
    uint8_t b = (l * 12) >> 8;     // ~5% of red: slight warmth
    ring.setPixelColor(i, r, g, b);
  }

  ring.show();
  delay(FRAME_MS);
}
```

### Tuning

| Want | Change |
|---|---|
| Calmer flame | Raise the `random(140, 256)` lower bound, or use `random(6) == 0` |
| More nervous flame | Lower `FRAME_MS`, or use `d / 2` for faster easing |
| More frequent drafts | Raise `< 2` in the gust check |
| Warmer / redder | Lower the green multiplier (e.g. `80`) |
| Yellower | Raise the green multiplier (e.g. `130`) |
| Dimmer overall | Lower `setBrightness` |

### Porting your existing ESP32 flicker code

- Replace float math with 0 to 255 integers and bit shifts.
- Replace `esp_random()` and similar calls with `random()`.
- Drop WiFi, `Serial`, and any `millis()`-based scheduling you don't need.
- Prototype and tune on the ESP32-C3 first. The ATtiny has no serial monitor, so debugging there is slow.
- Check the flash size after compiling. The IDE reports usage, and the limit is 8192 bytes.

## Diffusion

Bare WS2812Bs read as 8 distinct dots. For a convincing flame:

- Mount the ring under frosted glass, a paper or vellum shade, or a 3D-printed cover in white/natural PLA.
- Leave 2 to 4cm between the LEDs and the diffuser so the dots blend.
- A tall narrow cover (like a candle jar) works better than a flat cover.

## Testing Order

1. With no power, use a continuity tester: 5V rail to GND rail must be open, and no socket pin may be shorted to its neighbor.
2. Power the bare protoboard from USB with no chip and no ring. Check for 5V at socket pin 8 relative to pin 4.
3. Program the ATtiny on a breadboard first, including the fuse burn.
4. Insert the chip and connect the ring. It should flicker within a second of power-up.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| LEDs dark or random colors | Fuses not burned (still 1MHz), or wrong data pin in code |
| First LED wrong, rest fine | Missing series resistor, or long or noisy data wire |
| Flicker looks too slow and smooth | Clock set to 1MHz at compile time but chip at 8MHz (or the reverse). Recheck the board settings and burn fuses again |
| Programmer can't find chip | Wiring, missing 10µF cap (Arduino ISP), or the USBasp slow-clock jumper |
| Resets or glitches at bright moments | Missing bulk cap, or a weak USB charger or cable |
| Sketch too big | Floats or `String` in the code; switch to integers |
