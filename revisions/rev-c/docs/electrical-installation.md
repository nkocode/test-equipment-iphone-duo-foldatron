# Rev C electrical installation and connection schedule

Revision C-0.3, 2026-11-13. **Design review, not a released wiring drawing.**
The point-to-point schedule is an implementation proposal. Before energizing,
the builder must close E01-E04 in `release-register.json`, export the actual
Banner configuration report, and complete the empty-fixture tests. No safety
performance level or standards conformity is claimed by this document.

## Power domains

Use separate purchased, isolated supplies for motor power, 24 V controls and
5 V Raspberry Pi power. The proposed motor and control supplies are each
Zaber PS12S-24V30 (24 V, 3 A). The Pi 3B uses Adafruit 1995 (5 V, 2.5 A,
factory micro-USB lead). Keep all mains wiring within factory products.
The cabinet contains only the extra-low-voltage circuits below.

The PS12S output is listed as a two-pin 5 mm terminal connector. Confirm its
removable screw-terminal construction and polarity before ordering the final
harness. Do not cut a molded mains cable or assume a 5.08 mm third-party plug
mates with a 5 mm Zaber plug. This connector verification is E01, not an
instruction to fabricate an adapter. Use the Zaber PTB2 for the stage end.

Motor +24 V passes through fuse F1 and two independently controlled relay
banks before it reaches the stage. There must be no second supply through
the stage's daisy-chain connection. Leave NEXT unused and protected.
Control +24 V passes through F2; it remains on after an E-stop. Vacuum is
pneumatic and stays applied after motor power is removed. Disconnecting all
power is a maintenance operation, not the normal protective-stop sequence.

F1 starts at T1.6 A and F2 at T1 A, 5 x 20 mm time-delay cartridges in
Phoenix 3211861 holders. These are **qualification selections**: verify
actual inrush, conductor protection, supply current limiting and the SC10
DC contact rating before release. Do not increase a fuse to cure a fault.

## Terminal and wire conventions

X1.01-.10 are a bridged control +24 V group; X1.11-.20 are a separately
bridged 0 V group. X2.01-.18 are isolated signal feed-throughs. Use Phoenix
PT 2,5 / 3209510 blocks and FBS 10-5 / 3030213 bridges only in X1. Label
both ends of every wire. Never bridge the two test-pulse circuits together.

Use 18 AWG stranded copper for power and 22 AWG for cabinet signals,
subject to each device's terminal specification. Purchased sensor cables
are 0.25 mm2. Use correctly sized ferrules where required, one conductor
per SC10 terminal, and separate terminal blocks for fanout. Insulate spare
cores individually. Torque and strip length come from the delivered
component's instructions; a generic screw torque is not substituted.

| Wire | From | To | Function |
|---|---|---|---|
| W001 | Motor supply + | F1 input | Unswitched motor power |
| W002 | F1 output | SC10 RO1:13 | First motor disconnect |
| W003 | SC10 RO1:14 | SC10 RO2:43 | Series link |
| W004 | SC10 RO2:44 | Stage power +, PTB2 | Switched motor power |
| W005 | Motor supply - | Stage power - | Motor return |
| W010 | Control supply + | F2 input | Control power |
| W011 | F2 output | X1.01 | +24 V distribution |
| W012 | Control supply - | X1.11 | 0 V distribution |
| W013 | X1.02 / X1.12 | SC10 +24 V / 0 V | Controller supply |
| W014 | X1.03 / X1.13 | Waveshare V+ / GND | Digital I/O supply |
| W015 | X1.04 / X1.14 | M-7018R +Vs / GND | Temperature I/O supply |
| W016 | X1.15 | Waveshare DI COM | Active-high PNP input reference |
| W020 | SC10 IO1 test pulse | X2.01 | Channel A fanout |
| W021 | X2.01 | E-stop NC contact A input | Independent channel A |
| W022 | E-stop NC contact A output | SC10 IN1 via X2.03 | E-stop A return |
| W023 | SC10 IO2 test pulse | X2.02 | Channel B fanout |
| W024 | X2.02 | E-stop NC contact B input | Independent channel B |
| W025 | E-stop NC contact B output | SC10 IN2 via X2.04 | E-stop B return |
| W026 | X2.01 | BNS black (S11) | Guard A source |
| W027 | BNS blue (S12) | SC10 IN3 via X2.05 | Guard A return |
| W028 | X2.02 | BNS white (S21) | Guard B source |
| W029 | BNS brown (S22) | SC10 IN4 via X2.06 | Guard B return |
| W030 | X1.05 | Physical reset NO input | Local reset supply |
| W031 | Physical reset NO output | SC10 IN5 via X2.07 | Monitored manual reset |
| W032 | X1.06 | SC10 RO1:23 | Auxiliary permit supply |
| W033 | SC10 RO1:24 | SC10 RO2:53 | Both relay banks required |
| W034 | SC10 RO2:54 | Waveshare DI1 via X2.08 | Software motion permit |

X2.01 and .02 each need one controller wire plus two outgoing wires. Use
manufacturer-approved twin ferrules within the terminal's rating, or add
separately bridged duplicate terminals; never insert three loose wires in
one connection. The final terminal allocation and cabinet fit are E02.
The BNS wire colors apply to **BNS 260-02Z-L, non-LED**. Do not substitute
an LED G version or assume sensor brown is +24 V: here brown is a contact
return. Confirm delivered marking against the manufacturer's diagram.

## Vacuum and temperature channels

| Cup | Location | SDE5 factory cable | Module terminal | Software bit |
|---|---|---|---|---:|
| V1 | Fixed, lower | Brown pin 1 = +24; blue pin 3 = 0; black pin 4 = signal | DI2 | 1 |
| V2 | Fixed, upper | Same three-pin assignment | DI3 | 2 |
| V3 | Moving, lower | Same three-pin assignment | DI4 | 3 |
| V4 | Moving, upper | Same three-pin assignment | DI5 | 4 |
| Permit | Both SC10 relay banks | W034 | DI1 | 0 |

DI6-DI8 remain unused; all DO terminals remain unwired. The API cannot vent
a cup or reset the safety controller. Each SDE5 is PNP normally open and
must indicate vacuum above the qualified retention threshold. Disconnect
one cable at a time and confirm a latched software fault. These sensors
are process permissives, not safety-rated gripping controls.

Use Omega SA1-K probes: CH0 on an approved exterior phone surface clear of
cups, hinge and display; CH1 in ambient air away from warm electronics.
Connect each thermocouple directly to its numbered M-7018R channel with
correct Type K polarity. Do not extend with ordinary copper wire. Leave
other channels disabled. Temperature is surface temperature, not an
internal battery measurement. Record the attachment method and inspect it
at every pause because a detached but connected probe can look plausible.

## Communications

Pi USB port 1 -> Zaber **X-USBDC**, RS232, stage PREV/data connection;
never use a TTL serial lead. Pi USB port 2 -> ICP DAS tM-7561 isolated
USB/RS485 converter -> Waveshare -> M-7018R in a daisy chain. Match DATA+
and DATA- by their function, not by ambiguous A/B lettering. Use a twisted
pair plus reference conductor; connect the isolated bus reference as the
converter manual requires. Terminate only the two physical bus ends after
checking for installed termination; do not add a resistor at every node.
The final converter terminal labels, termination and cable selection are
E03. Keep both adapters' stable `/dev/serial/by-id/` names in commissioning.

Waveshare address 1; M-7018R address 2; both 9600 baud, 8N1. Zaber address
1 on its separate port, 115200 baud, 8N1. Configure manually with vendor
utilities before starting the service. See `../software/protocols.md` for
the read-only register map, checksums and expected device identities.

## Banner SC10 configuration worksheet

In the manufacturer's configuration tool, select SC10-2roe. Create separate
dual-channel E-stop and guard inputs using the terminals in W020-W029,
with distinct cross-short test pulses. Add a monitored manual reset input
on IN5. Require both safety inputs healthy before reset can enable either
relay bank. Both RO1 and RO2 implement the same conjunction and latch;
use zero programmed OFF delay. Do not enable automatic restart.

The proposed pin assignment is **not an imported, validated configuration**.
Confirm that this exact device/firmware supports the shared test-pulse
fanout, selected input blocks and terminal allocation. Export the generated
wiring diagram and configuration checksum. If the tool assigns other
terminals, revise this schedule before wiring; do not quietly diverge.
This is release gate E04. The auxiliary series contact path reports relay
state; it is not a separate safety feedback loop or a certified E-stop API.

Qualification must cover each input opening independently, cross-shorts,
reset held/stuck, guard reopening, power loss/recovery, stage restart and
actual stop time. Resetting the physical circuit restores availability;
it must never restart a run. The Python service separately clears its
latched fault only after a fresh stationary acquisition and requires a new
explicit run command. Loss of Pi software is tested independently of the
hardwired guard and E-stop circuits.

## Primary references

- [Banner SC10-2roe](https://www.bannerengineering.com/us/en/products/part.806222.html)
- [Schmersal BNS 260-02Z-L](https://products.schmersal.com/en_IO/bns-260-02z-l-101184385)
- [Waveshare input wiring](https://www.waveshare.com/wiki/Modbus_RTU_IO_8CH)
- [Zaber supply](https://www.zaber.com/products/accessories/PS12S-24V30)
- [Zaber X-RSW-E manual](https://www.zaber.com/manuals/X-RSW-E)
- [Phoenix feed-through terminal](https://www.phoenixcontact.com/us/products/3209510)
- [Phoenix fuse holder](https://www.phoenixcontact.com/us/products/3211861)
- [Adafruit Pi supply](https://www.adafruit.com/product/1995)

Downloaded vendor references and SHA-256 values are in
`../hardware/sources.json`. Unavailable downloads are not represented as
locally verified datasheets.

## Converter drawing verification, 2026-11-13

The manufacturer's two-page tM-7561 datasheet is now pinned as
`ICP-tM7561.pdf`. It gives a 52 x 27 x 87 mm DIN-rail envelope, USB Type B,
USB-powered operation and the included CA-USB18 1.8 m cable. The seven
terminal positions, top to bottom, are DATA+, DATA-, four unused positions,
and ISO.GND. The unit has an OFF/ON termination-resistor switch.

Use the converter at one physical bus end and M-7018R at the other, with
Waveshare between them. The converter's termination switch is ON; do not
add another external termination at that same end. Resolve the far-end
termination and confirm both end resistances with power removed. Keep
ISO.GND on the isolated bus side; never connect it to USB ground to defeat
the converter isolation. Final reference/shield and resistor installation
remain E03 until incorporated in the wiring drawing.

Belden 9842 is the selected cable family for the next wiring iteration:
two twisted pairs, 24 AWG, 120 ohm nominal impedance and 8.64 mm nominal
jacket diameter. Route and gland sizing must use that diameter, not bare
conductor size. Exact cut length and termination components remain open.

Sources: [ICP DAS drawing](https://www.icpdas.com/web/product/download/industrial_communication/uart/converter/document/data_sheet/tM-7561_en.pdf),
[Belden cable data](https://catalog.belden.com/techdata/EN/9842_techdata.pdf).
