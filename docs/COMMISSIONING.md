# Commissioning record

Record ID: __________ Date: __________ Operator/reviewer: __________

Station serial/revision: __________ Servo serial/firmware: __________

Phone serial/iOS: __________ Fixture shoe revision: __________

This checklist is a physical test record. Software simulation results do not fill these boxes.

| Check | Required evidence | Result / initials |
| --- | --- | --- |
| Actual phone envelope | Half widths, height, thickness, camera/button/port map | |
| Hinge migration | Radial/normal position at five angles; >=2 mm spare travel | |
| Cradle retention | 10 N tangential dummy test, no phone/screen damage | |
| Axis alignment | Bearing and clutch alignment measured | |
| Unpowered clearance | Entire swept volume clear; no hinge shaft intrusion | |
| Clutch | Bidirectional breakaway torque, repeatability, lock mark | |
| Baseline hinge load | Force/radius/direction/angle and empty-fixture load | |
| Hard stops | Measured endpoints within specimen free range | |
| Endpoint switches | Independent output-side operation and disagreement fault | |
| 12 V polarity/fuse | Meter reading and fuse identification | |
| 24 V relay wiring | Vendor circuit revision and terminal inspection | |
| GPIO isolation | Permit high/low voltage; no 24 V on Pi side | |
| E-stop | Motor power removed independently of Pi; manual reset required | |
| Guard | Each contact/channel tested; no restart on closing alone | |
| Stop distance/time | Worst motion and gravity settling; reach-in prevented | |
| USB disconnected | Watchdog stops; no automatic resumption | |
| Pi process/power loss | Motion response and restart behavior | |
| Motor power cycle | Torque stays off until explicit valid command | |
| Probe mapping | Case/ambient serials, CRC failure, disconnected-probe fault | |
| Probe thermal contact | Case attachment retained through complete arc | |
| Dummy jam/slip | Fault, no false increment, clutch setting retained | |
| 100 dummy cycles | Independent count agreement and no wear/movement | |
| 1,000 dummy cycles | Temperatures and drive/fixture duty validated | |
| Phone single/10/100 cycles | Functional inspection results at each stage | |
| Network access | Unique key, private/TLS or tunnel, one worker only | |
| Disk/restart | Records durable, interrupted runs never resume | |

Calibrated closed tick/angle: __________ Open tick/angle: __________

Maximum speed/current: __________ Clutch torque: __________

Case/ambient/motor temperature thresholds: __________

Acceptance disposition and remaining restrictions: __________

Release for supervised phone trials: __________

Separate release for any unattended testing: __________
