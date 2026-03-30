# EC800M Audio Board Board Map

## 1. Scope

This file is the final board-oriented software map for the current PCB.

Naming policy:

- Product / project / target board naming: `EC800MCNLE`
- Low-level pin-reference source: `EC800M-CN` hardware design data
- Local schematic note on `U1`: `EC800M-CN`

This means:

- Development target should be treated as `EC800MCNLE`
- Pin-function lookup can still reference the `EC800M-CN` hardware design document

## 2. Confidence Rules

- `high`: confirmed by local schematic net labels and module pin mapping
- `medium`: strongly inferred from connector wiring and signal naming
- `low`: board-level clue exists but the final module-side binding still needs one more pass

## 3. Core Board Identity

| Item | Value |
| --- | --- |
| Target platform | `EC800MCNLE` |
| Local U1 symbol | `EC800G-CN` |
| Local U1 comment | `EC800M-CN` |
| Board role | audio + LCD + battery + cellular terminal board |
| Main QuecPython project | `xiaozhi_AI_mqtt` |

## 4. Functional Signal Map

| Function | Board net | Module pin | Module signal | Class | Confidence | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Mic positive | `MIC1P` / `MIC_P` | `3` | `MIC_P` | dedicated audio | high | board mic path |
| Mic negative | `MIC1N` / `MIC_N` | `4` | `MIC_N` | dedicated audio | high | board mic path |
| Speaker positive | `SPK_P` | `5` | `SPK_P` | dedicated audio | high | enters power amp |
| Speaker negative | `SPK_N` | `6` | `SPK_N` | dedicated audio | high | enters power amp |
| Power key | `PWRKEY` | `7` | `PWRKEY` | power-control signal | high | not a normal GPIO |
| ADC input | `ADC0` | `9` | `ADC0` | ADC | high | not traced to a board connector yet |
| SIM data | `SIM_DATA` | `11` | `USIM_DATA` | dedicated SIM | high | card interface |
| SIM reset | `SIM_RST` | `12` | `USIM_RST` | dedicated SIM | high | card interface |
| SIM clock | `SIM_CLK` | `13` | `USIM_CLK` | dedicated SIM | high | card interface |
| SIM power | `SIM_VDD` | `14` | `USIM_VDD` | dedicated SIM | high | card interface |
| Net status | status indicator path | `16` | `NET_STATUS` | indication signal | medium | board indication usage |
| Main UART RX | `MAIN_RXD` | `17` | `MAIN_RXD` | UART | high | routed to `J4` side as `RXD2` |
| Main UART TX | `MAIN_TXD` | `18` | `MAIN_TXD` | UART | high | routed to `J4` side as `TXD2` |
| IO supply | `VDD_EXT` | `24` | `VDD_EXT` | power rail | high | reference rail for board logic |
| Module status | status indicator path | `25` | `STATUS` | indication signal | medium | board indication usage |
| Main antenna | `ANT_MAIN` | `27` | `ANT_MAIN` | RF | high | to antenna connector |
| USB D+ | `USB_DP` | `59` | `USB_DP` | USB | high | type-C interface |
| USB D- | `USB_DM` | `60` | `USB_DM` | USB | high | type-C interface |
| USB VBUS | `USB_VBUS` | `61` | `USB_VBUS` | USB | high | type-C interface |
| LCD reset | `LCD_RST` | `49` | `LCD_RST` | dedicated LCM | high | level-shifted to `J6` |
| LCD data out | `LCD_SPI_DOUT` | `50` | `LCD_SPI_DOUT` | dedicated LCM | high | level-shifted to `J6` |
| LCD RS/DC | `LCD_RS` | `51` | `LCD_SPI_RS` | dedicated LCM | high | level-shifted to `J6` |
| LCD chip select | `LCD_SPI_CS` | `52` | `LCD_SPI_CS` | dedicated LCM | high | level-shifted to `J6` |
| LCD clock | `LCD_SPI_CLK` | `53` | `LCD_SPI_CLK` | dedicated LCM | high | level-shifted to `J6` |
| I2C SDA | `I2C_SDA` | `66` | `I2C_SDA` | I2C | high | module capability visible; board-side usage not confirmed |
| I2C SCL | `I2C_SCL` | `67` | `I2C_SCL` | I2C | high | module capability visible; board-side usage not confirmed |
| LCD TE | `LCD_TE` | `78` | `LCD_TE` | dedicated LCM | high | appears on both module and LCD pages |
| SIM detect | `SIM_DET` | `79` | `USIM_DET` | SIM detect | high | card-detect path |
| USB boot | `USB_BOOT` | `82` | `USB_BOOT` | boot/download | high | do not repurpose casually |
| AUX UART RX | `AUX_RXD` | `28` | `AUX_RXD` | UART | high | visible on module, no board connector confirmed |
| AUX UART TX | `AUX_TXD` | `29` | `AUX_TXD` | UART | high | visible on module, no board connector confirmed |
| Debug RX | `DBG_RXD` | `38` | `DBG_RXD` | debug UART | high | not traced to board connector yet |
| Debug TX | `DBG_TXD` | `39` | `DBG_TXD` | debug UART | high | not traced to board connector yet |
| LCD backlight | `BLK` | unknown | unknown | control signal | low | board output confirmed, module-side source not fully closed |

## 5. Connector Map

### 5.1 J6 LCD connector

| J6 pin | Signal | Confidence | Notes |
| --- | --- | --- | --- |
| 1 | `GND` | high | ground |
| 2 | `VCC_3V3` | high | LCD supply |
| 3 | `LCD_SPI_CLK_3V3` | high | from module `LCD_SPI_CLK` through level shift |
| 4 | `LCD_SPI_DOUT_3V3` | high | from module `LCD_SPI_DOUT` through level shift |
| 5 | `LCD_RST_3V3` | high | from module `LCD_RST` through level shift |
| 6 | `LCD_RS_3V3` | high | from module `LCD_SPI_RS` through level shift |
| 7 | `BLK` | medium | backlight/control line |
| 8 | `LCD_SPI_CS_3V3` | high | from module `LCD_SPI_CS` through level shift |

### 5.2 J4 UART connector

| J4 pin | Signal | Confidence | Notes |
| --- | --- | --- | --- |
| 1 | `RXD2` | medium | external RX input side, tied to module main UART RX path |
| 2 | `TXD2` | medium | external TX output side, tied to module main UART TX path |
| 3 | `GND` | high | ground |

Interpretation:

- `J4` should be treated as the primary exposed UART header for bring-up and debug
- software side should still think in terms of module `MAIN_RXD` / `MAIN_TXD`

### 5.3 J3 speaker connector

| J3 pin group | Signal | Confidence | Notes |
| --- | --- | --- | --- |
| speaker output | amplified speaker pair | medium | board clearly routes `SPK_P/SPK_N` into amp `U5` then out to `J3` |

### 5.4 J2 battery connector

| J2 pin group | Signal | Confidence | Notes |
| --- | --- | --- | --- |
| battery pair | `VBAT` / `GND` | high | single-cell battery input |

### 5.5 CARD1 SIM connector

| Card pin | Signal | Confidence |
| --- | --- | --- |
| C1 | `SIM_VDD` | high |
| C2 | `SIM_RST` | high |
| C3 | `SIM_CLK` | high |
| C5 | `GND` | high |
| C7 | `SIM_DATA` | high |
| CD | `SIM_DET` | high |

### 5.6 J1 antenna connector

| Connector | Signal | Confidence | Notes |
| --- | --- | --- | --- |
| J1 center | `ANT_MAIN` | high | RF main antenna |
| J1 shell/side | `GND` | high | RF ground |

## 6. Software-Use Classification

### 6.1 Do not treat these as ordinary GPIO first

- `PWRKEY`
- `USB_DP`, `USB_DM`, `USB_VBUS`
- `USIM_*`
- `MIC_P`, `MIC_N`
- `SPK_P`, `SPK_N`
- `MAIN_RXD`, `MAIN_TXD`
- `LCD_RST`, `LCD_SPI_DOUT`, `LCD_SPI_RS`, `LCD_SPI_CS`, `LCD_SPI_CLK`, `LCD_TE`
- `USB_BOOT`

These should be developed as:

- power-control
- USB
- SIM/network
- audio
- UART
- LCD/LCM
- boot/download

### 6.2 Signals worth deeper GPIO-style follow-up

- `BLK`
- `STATUS`
- `NET_STATUS`

Reason:

- they are board-control or indication signals
- they may still be software-visible
- but they should be verified once more before being frozen into production code

## 7. Bring-Up Priority

Recommended bring-up order:

1. `J4` UART
2. SIM detection and cellular registration
3. audio record / playback path
4. LCD power and control line verification
5. LCD panel init
6. backlight control (`BLK`) confirmation

## 8. Practical Outcome

This board is now sufficiently mapped for:

- UART-based bring-up
- SIM/network bring-up
- audio path validation
- LCD interface bring-up

The only board-control item that still deserves one more pass before hard-coding is:

- `BLK`
