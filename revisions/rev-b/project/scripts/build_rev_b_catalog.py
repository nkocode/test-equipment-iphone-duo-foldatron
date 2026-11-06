"""Build the procurement register and traceable vendor-source inventory."""

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hardware/rev-b"
SOURCES = [
    (
        "S01",
        "80/20",
        "1010 extrusion",
        "https://8020.net/1010.html",
        "",
        "25.4 square; current product lists 6063-T6; I=0.0442 in^4; "
        "weight 0.0424 lb/in.",
        "Reconstructed envelope; slot relief is "
        "illustrative. Original STEP requires PartCommunity sign-in.",
    ),
    (
        "S02",
        "80/20",
        "4119 inside corner bracket",
        "https://8020.net/4119.html",
        "",
        "25.4 legs; 22.225 width; 4.7752 thick; D7.1374 holes at 12.7.",
        "Reconstructed mounting geometry; edge radii omitted.",
    ),
    (
        "S03",
        "80/20",
        "3393 button-head screw / T-nut set",
        "https://8020.net/3393.html",
        "",
        "1/4-20 x 0.500 screw; 10-series slide-in economy T-nut. "
        "Two sets per 4119 bracket.",
        "No original CAD downloaded; "
        "do not manufacture T-nuts from the assembly illustration.",
    ),
    (
        "S04",
        "ROBOTIS",
        "XM430-W350-T/R manufacturer drawing",
        "https://media.distrelec.com/Web/Downloads/_t/ds/Dynamixel_XM-Series_eng_tds.pdf",
        "robotis-xm430-drawing.pdf",
        "28.5 x 46.5 x 34; axis 11.25 below top; "
        "side pattern 12 x 24; horn PCD16. M2 horn max 2 deep; M2.5 "
        "case max 3 deep.",
        "Reconstructed interface model. Manufacturer's legacy STEP "
        "links returned HTML, discarded.",
    ),
    (
        "S05",
        "Dynatect",
        "Polyclutch Slip-Ease catalogue",
        "https://www.dynatect.de/wp-content/uploads/Polyclutch-SlipEaseClutch.pdf",
        "slip-ease.pdf",
        "EAS12: OD19.05, overall31.75, bossOD14.28, bossL4.78. "
        "Published max0.96 N m at50rpm; 4.5W. Exact 6mm bores "
        "require configuration.",
        "Envelope only; insertion depth and low-torque setting not confirmed.",
    ),
    (
        "S06",
        "HIWIN",
        "Linear Guideway G99TJ22-2503, printed pp86/90",
        "https://www.hiwinsupport.com/download/tech_doc/gw/Linear_Guideway-%28J%29.pdf",
        "hiwin-linear.pdf",
        "MGN7C H8 W17 L22.5 Lmax23.1; block pattern12x8, M2x2.5 "
        "deep; rail7x4.8, pitch15, end5, D2.4/D4.2 counterbore2.3. "
        "Torque table says M2x0.25 while dimension table omits "
        "pitch: confirm thread on order.",
        "Reconstructed interface, no bearing-ball or raceway "
        "manufacturing geometry.",
    ),
    (
        "S07",
        "NSK",
        "Bearing and Linear Replacement Guide",
        "https://www.nsk.com/content/dam/nsk/am/en_us/documents/bearings-americas/Bearing-and-Linear-Replacement-Guide.pdf",
        "nsk-bearing-guide.pdf",
        "626 open deep-groove bearing: 6 ID x19 OD x6 width; "
        "shaft shoulder8, housing shoulder17, corner radius max0.3.",
        "Reconstructed ring envelope. Buy genuine 626; do not make a "
        "bearing from STEP.",
    ),
    (
        "S08",
        "Ruland",
        "MCL-6-A one-piece clamp collar",
        "https://www.ruland.com/mcl-6-a.html",
        "",
        "Bore6, OD16, width9; M3x8 screw; 2.5mm hex; seating torque2.1 N m. "
        "Clamp clearance OD20.8.",
        "Reconstructed fit envelope; clamp screw clearance "
        "must be checked on purchased collar.",
    ),
    (
        "S09",
        "ACE",
        "FRT-C2-201 damper operating instructions",
        "https://www.acecontrols.co.uk/media/msimages/pdf/ACE_FRT%28FRN%29-C2_Operating-Mounting_EN_21_22_0019.pdf",
        "ace-frt-c2.pdf",
        "0.020 N m +/-0.006 at20rpm/23C; bodyOD15; D4 shaft "
        "flat3.5; mount centers21; 50,000 reference cycles. No shaft "
        "side/axial load.",
        "Investigated, not fitted: torque/lifetime do not justify "
        "the previous generic damper assumption.",
    ),
    (
        "S10",
        "Raspberry Pi",
        "Pi 5 mechanical drawing",
        "https://datasheets.raspberrypi.com/rpi5/raspberry-pi-5-mechanical-drawing.pdf",
        "raspberry-pi-5-mechanical.pdf",
        "Board85x56; mounting pitch58x49; D2.7 mounting "
        "holes. Vendor explicitly calls dimensions approximate and "
        "not production data.",
        "Use physical board before machining a close-fitting enclosure.",
    ),
    (
        "S11",
        "Raspberry Pi",
        "Pi 5 original STEP archive",
        "https://pip-assets.raspberrypi.com/categories/892-raspberry-pi-5/documents/RP-010083-CA-1-rpi-5%203D%20STEP%20-%20No%20Graphics%20small%20file.zip",
        "raspberry-pi-5-step.zip",
        "Original manufacturer 3D board/component model; "
        "archive includes LICENSE.txt (MIT).",
        "Original vendor STEP; preserve included license.",
    ),
    (
        "S12",
        "JST",
        "EH connector family",
        "https://www.jst-mfg.com/product/pdf/eng/eEH.pdf",
        "jst-eh.pdf",
        "2.5mm pitch EH family. ROBOTIS TTL uses EHR-03 housing, "
        "B3B-EH-A header; 1 GND / 2 VDD / 3 DATA.",
        "Factory Robot Cable-X3P preferred; no generic Dupont substitutes.",
    ),
    (
        "S13",
        "Hammond",
        "1554YA enclosure drawing",
        "https://www.hammfg.com/files/parts/pdf/1554YAGY.pdf",
        "hammond-1554YA.pdf",
        "1554YA2GY polycarbonate variant:299.33x239.46x119.73; "
        "inside height111.75. Optional1554YPL panel250.50x214.52. "
        "Lid torque0.9-1.0 N m.",
        "Reconstructed shell envelope; bosses and seals omitted. "
        "STEP not obtained.",
    ),
    (
        "S14",
        "MEAN WELL",
        "GST60A supply series",
        "https://www.meanwell.com/Upload/PDF/GST60A/GST60A-SPEC.PDF",
        "meanwell-gst60a.pdf",
        "GST60A12-P1J:12V/5A; nominal125x50x31.5 housing; "
        "P1J DC plug5.5OD/2.1ID, center positive.",
        "External factory mains brick; do not put mains terminals "
        "inside bench.",
    ),
    (
        "S15",
        "MEAN WELL",
        "GST25A supply series",
        "https://www.meanwell.com/Upload/PDF/GST25A/GST25A-SPEC.PDF",
        "meanwell-gst25a.pdf",
        "GST25A24-P1J:24V/1.04A; external adapter; "
        "P1J center-positive5.5OD/2.1ID plug. Use the series drawing "
        "for cable exit clearance.",
        "Original datasheet; no 3D body model needed inside cabinet.",
    ),
    (
        "S16",
        "Neutrik",
        "NC3FD-LX panel connector drawing",
        "https://www.neutrik.com/media/8412/download/nc3fd-lx-3.pdf?v=1",
        "NC3FD-LX.pdf",
        "26x31 flange; 19x24 diagonal mounting pitch; "
        "panel clearance >D23.6. Project cutout D24.0 +0.1/0; M3 mounting.",
        "Original PDF and STEP (S17); project-defined 12V pin assignment.",
    ),
    (
        "S17",
        "Neutrik",
        "NC3FD-LX original 3D CAD",
        "https://www.neutrik.com/media/13322/download/3-D%20NC3FD-LX.stp?v=1",
        "NC3FD-LX.stp",
        "Original vendor mechanical part geometry.",
        "Original STEP validated by file signature and OpenCascade import.",
    ),
    (
        "S18",
        "Neutrik",
        "NC4FD-LX panel connector drawing",
        "https://www.neutrik.com/media/8417/download/nc4fd-lx-2.pdf?v=1",
        "NC4FD-LX.pdf",
        "D-series four-pin panel connector; separate keying from "
        "3-pin 12V inlet. Same19x24 mounting pitch and D24.0 project opening.",
        "Original PDF and STEP (S19); project-defined 24V pin assignment.",
    ),
    (
        "S19",
        "Neutrik",
        "NC4FD-LX original 3D CAD",
        "https://www.neutrik.com/media/11865/download/NC4FD-LX.stp?v=2",
        "NC4FD-LX.stp",
        "Original vendor mechanical part geometry.",
        "Original STEP validated by file signature and OpenCascade import.",
    ),
    (
        "S20",
        "Pilz",
        "PNOZ X3 manual 20547-EN-10",
        "https://www.pilz.com/download/open/PNOZ_X3_Operating_Manual_20547-EN-10.pdf",
        "pilz-pnoz-x3.pdf",
        "774310,24VAC/DC variant; 45 wide x121 high x87 deep. "
        "DC supply B1+/B2-. Pages12/13 define dual-channel inputs "
        "and monitored reset.",
        "Original PDF; check current manual supplied with device "
        "before wiring. "
        "Manual permits internal-use copies.",
    ),
    (
        "S21",
        "Schneider Electric",
        "XB5AS8444 emergency-stop datasheet",
        "https://www.farnell.com/datasheets/2548526.pdf",
        "schneider-xb5as8444.pdf",
        "2NC,40mm red mushroom; D22.5 panel opening; "
        "clamp thickness1..6; 40x43x82 overall; terminal torque0.8..1.2 N m.",
        "Original manufacturer datasheet hosted by distributor.",
    ),
    (
        "S22",
        "Schneider Electric",
        "XB5AA61 reset button",
        "https://media.distributordatasolutions.com/schneider_synd/2023q2/documents/772793a73ac5d61af21589d4ebbac215fb79964c.pdf",
        "schneider-xb5aa61.pdf",
        "Blue spring-return1NO,22mm family; "
        "panel cutout D22.5. Two separate buttons used for two safety relays.",
        "Original manufacturer datasheet; do not bridge two "
        "monitored-reset circuits.",
    ),
    (
        "S23",
        "OMRON",
        "D4NS / D4NS-SK catalogue",
        "https://files.omron.eu/downloads/latest/datasheet/en/"
        "d4ns_d4ns-sk_safety-door_switch_datasheet_en.pdf?v=1",
        "omron-d4ns.pdf",
        "D4NS-1BF:2NC,PG13.5; D4DS-K2 key front-insertion setting40..42.5 "
        "from rear seating face; alignment+/-1. Mount22x47 diagonal "
        "M4; key15 pitch. Body0.5..0.7Nm; key2.4..2.8Nm. Pages7/8/10/12.",
        "Original manufacturer PDF downloaded from European server. "
        "B128-B130 project mounts; physical insertion/access tests P3.",
    ),
    (
        "S24",
        "OMRON",
        "D2F switch datasheet",
        "https://omronfs.omron.com/en_US/ecb/products/pdf/en-d2f.pdf",
        "omron-d2f.pdf",
        "D2F-01L-D3 low-load lever,solder terminals; pitch6.5; "
        "OP6.8+/-1.5,OTmin0.55; mounting0.08..0.10Nm. "
        "Solder300C max3sec; leave undisturbed1min.",
        "Original PDF; B125-B127 define endpoint mount/cam. "
        "Actuation and wear still require physical acceptance.",
    ),
    (
        "S25",
        "Phoenix Contact",
        "UT 2,5 terminal block 3044076",
        "https://www.farnell.com/datasheets/3541626.pdf",
        "phoenix-ut25.pdf",
        "5.2 wide x47.7 long; 47.5 high on NS35/7.5; strip9mm; "
        "torque0.5..0.6 N m.",
        "Original manufacturer PDF hosted by distributor; end "
        "plates/stops must be separately ordered.",
    ),
    (
        "S26",
        "ROBOTIS",
        "U2D2 and power hub",
        "https://docs.robotis.com/docs/parts/interface/u2d2_power_hub/",
        "",
        "Power-hub board48x57; 3.5..24V,10A maximum. Included M3x10 supports. "
        "Hub DC jack is2.5ID, unlike selected supply's2.1ID plug: "
        "use screw terminals.",
        "Manufacturer web instructions; mounting pattern must be "
        "measured or vendor drawing obtained.",
    ),
    (
        "S27",
        "Analog Devices",
        "DS18B20 temperature sensor",
        "https://www.analog.com/media/en/technical-documentation/data-sheets/ds18b20.pdf",
        "",
        "3-wire powered1-Wire sensor; select genuine TO-92 part. "
        "A bare sensor datasheet does not define a third-party "
        "waterproof probe housing.",
        "Primary URL identified; download failed. Probe assembly not "
        "dimensionally released.",
    ),
    (
        "S28",
        "Bossard",
        "BN612 ISO4762 socket screw catalogue",
        "https://www.tme.eu/Document/c28d0e41a5209ef4d5f4150eb50af631/BN612-IT.pdf",
        "",
        "Metric cap-head nominal envelopes d/headD/headH:2/3.8/2, "
        "2.5/4.5/2.5,3/5.5/3,4/7/4,5/8.5/5,6/10/6.",
        "Manufacturer catalogue indexed online; download403. "
        "Supplied STEP fasteners "
        "are standard-derived envelopes, not original vendor CAD.",
    ),
]


SOURCES.append(
    (
        "S29",
        "MISUMI",
        "Hole fit tolerance reference",
        "https://de.meviy.misumi-ec.com/help/en/technical_info-en-c/"
        "mpb_conditions-en-c/9726/",
        "",
        "H7 for diameters over18 through30mm is +0.021/0. "
        "The D19 bearing seats are therefore19.000..19.021mm.",
        "Manufacturer technical reference; fit callout, not a purchased part.",
    )
)

SOURCES.extend(
    [
        (
            "S30",
            "Phoenix Contact",
            "CLIPFIX 35-5 / 3022276",
            "https://www.phoenixcontact.com/en-us/products/"
            "end-block-clipfix-35-5-3022276?type=pdf",
            "",
            "Width5.2; length48.6; depth37.1 on NS35/7.5.",
            "Manufacturer dimension table; purchased DIN end bracket.",
        ),
        (
            "S31",
            "Phoenix Contact",
            "D-UT 2,5/10 / 3047028",
            "https://www.phoenixcontact.com/en-de/products/"
            "end-cover-d-ut-25-10-3047028?type=pdf",
            "",
            "Width2.2; height47; depth39.8. End cover for UT terminal bank.",
            "Manufacturer dimension table; verify open side on installation.",
        ),
        (
            "S32",
            "Phoenix Contact",
            "NS35/7.5 PERF 2000MM / 0801733",
            "https://www.phoenixcontact.com/en-us/products/"
            "din-rail-ns-35-75-perf-2000mm-0801733",
            "",
            "35mm wide,7.5mm high; stock2000mm; cut two140mm lengths.",
            "Use purchased perforated rail; deburr both cut ends.",
        ),
        (
            "S33",
            "Phoenix Contact",
            "FBS 4-5 / 3030187",
            "https://www.phoenixcontact.com/en-us/products/"
            "jumper-fbs-4-5-3030187",
            "",
            "Four positions,5.2mm pitch,24A; bridge only identified buses.",
            "Manufacturer terminal accessory; not a universal wire jumper.",
        ),
        (
            "S34",
            "Hammond",
            "1427BCGM16 cable gland",
            "https://www.hammfg.com/files/parts/pdf/1427BCGM16.pdf",
            "hammond-gland.pdf",
            "M16x1.5; mounting hole16; cableOD4..8; outerL21; threadL6. "
            "Locknut and EPDM ring included.",
            "Cabinet gland only. NOT a substitute for the PG13.5 "
            "entry on the guard switch; check wall and locknut stack.",
        ),
        (
            "S35",
            "Littelfuse",
            "ATO FHAC inline fuse holder",
            "https://www.littelfuse.com/assetdocs/"
            "littelfuse-fuse-holder-ato-fhac-datasheet.pdf?"
            "assetguid=272e0b1a-a576-4173-8740-c1eb469efd79",
            "",
            "FHAC0001ZXJ:32VDC,20A,16AWG leads with cover. "
            "Holder rating is not the selected fuse current.",
            "Manufacturer datasheet; fuse selection/coordination remains P4.",
        ),
    ]
)


SOURCES.extend(
    [
        (
            "S36",
            "Adafruit",
            "1609 Perma-Proto original EAGLE board",
            "https://raw.githubusercontent.com/adafruit/Adafruit-Perma-Proto-PCB/"
            "master/adafruit%20permaproto%20halfbreadboard.brd",
            "adafruit-permaproto-half.brd",
            "81.28 x50.8; two D3.2 holes73.66 apart; "
            "grid2.54; center gap7.62.",
            "Original EAGLE CAD; copper connectivity checked; CC BY-SA3.0.",
        ),
        (
            "S37",
            "LITEON",
            "LTV-817 optocoupler manufacturer datasheet",
            "https://media.digikey.com/pdf/data%20sheets/lite-on%20pdfs/"
            "ltv-817_827_847%28m%2Cs%2Cs_ta1%29.pdf",
            "liteon-ltv817.pdf",
            "DIP4: lead pitch2.54; rows7.62; body4.6x6.5 nominal.",
            "Manufacturer PDF via distributor; pin1A,2K,3E,4C.",
        ),
        (
            "S38",
            "Vishay",
            "PR01 power metal-film resistor",
            "https://www.vishay.com/docs/28729/pr010203.pdf",
            "vishay-pr01.pdf",
            "PR01:1W at70C; bodyL6.5,D2.5; leadD0.58; select1% tolerance.",
            "Manufacturer dimensional and rating data; no vendor STEP.",
        ),
        (
            "S39",
            "Vishay",
            "1N4148 switching diode",
            "https://www.vishay.com/docs/81857/1n4148.pdf",
            "vishay-1n4148.pdf",
            "Axial glass DO35; cathode band identifies negative terminal.",
            "Manufacturer PDF; upright mounting with insulated formed lead.",
        ),
        (
            "S40",
            "Littelfuse",
            "ATOF287 blade fuse32VDC",
            "https://www.littelfuse.com/assetdocs/"
            "littelfuse_datasheet_287_atof_r2.7.pdf?"
            "assetguid=43dcdce8-8ca2-426f-8998-7e566f048d40",
            "",
            "19.1 wide x18.8 high x5.1; F1=0287002.L2A; F2=0287001.L1A.",
            "Selected prototypes; verify inrush and supply fault behavior P4.",
        ),
    ]
)

SOURCES.extend(
    [
        (
            "S41",
            "LAPP",
            "SKINTOP STR reduced PG13.5 plastic gland",
            "https://products.lappgroup.com/online-catalogue/cable-glands/"
            "skintop-cable-glands-plastic-pg/standard/skintop-str.html?format=pdf",
            "lapp-skintop-str.pdf",
            "53015130:4..9mm cable; SW24; L41; threadL9mm.",
            "Manufacturer catalogue; matches D4NS9mm maximum thread length.",
        ),
        (
            "S42",
            "LAPP",
            "OLFLEX CLASSIC110 4X0.5",
            "https://www.lapp.ch/de/item/olflex-classic-110-4x05%3B1119754",
            "",
            "1119754:4x0.5mm2; nominalOD5.7; 300/500V; bend5xOD.",
            "Manufacturer product data; stationary guard-switch cable.",
        ),
    ]
)


def source_register():
    records = []
    for sid, maker, title, url, filename, dimensions, model in SOURCES:
        record = dict(
            id=sid,
            manufacturer=maker,
            title=title,
            url=url,
            filename=filename,
            dimensions=dimensions,
            model_status=model,
            accessed="2026-11-05",
        )
        path = OUT / "vendor" / filename if filename else None
        if path and path.is_file():
            content = path.read_bytes()
            signature = (
                content.startswith(b"%PDF-")
                if filename.endswith(".pdf")
                else content.startswith(b"PK")
                if filename.endswith(".zip")
                else content.lstrip().startswith(b"<?xml")
                if filename.endswith(".brd")
                else content.lstrip().startswith(b"ISO-10303-21;")
            )
            if not signature:
                raise ValueError(f"Invalid vendor asset: {filename}")
            record.update(
                file_status="Downloaded; signature verified",
                sha256=hashlib.sha256(content).hexdigest(),
                bytes=len(content),
                license_scope=(
                    "MIT; retain archive LICENSE.txt"
                    if sid == "S11"
                    else "CC BY-SA3.0; Limor Fried/Ladyada, Adafruit"
                    if sid == "S36"
                    else "Vendor copyright; internal reference, "
                    "not covered by project MIT license"
                ),
            )
        else:
            record["file_status"] = "Reference URL only; no local source file"
        check_path = OUT / "vendor-cad-checks.json"
        if check_path.is_file():
            for result in json.loads(check_path.read_text()):
                if result["file"] == filename:
                    record["cad_kernel_valid"] = result["ocp_valid"]
                    if not result["ocp_valid"]:
                        record["model_status"] += (
                            " WARNING: original imports but fails overall "
                            "kernel validity; retained unchanged as reference."
                        )
        records.append(record)
    return records


def procurement():
    items = []

    def item(pid, qty, pn, detail, source, status="SELECTED"):
        items.append(
            dict(
                id=pid,
                quantity=qty,
                part_number=pn,
                description=detail,
                source=source,
                status=status,
            )
        )

    item("V01", 4, "80/20 1010", "Cut660.4 mm; front/rear rails", "S01")
    item(
        "V02",
        8,
        "80/20 1010",
        "Cut508.0 mm; four side rails/four posts",
        "S01",
    )
    item(
        "V03", 2, "80/20 1010", "Cut609.6 mm; base support crossmembers", "S01"
    )
    item(
        "V04",
        28,
        "80/20 4119",
        "Inside corner bracket; see FR-001 schedule",
        "S02",
    )
    item(
        "V05",
        90,
        "80/20 3393",
        "56 structure +28 guard panels +4 base +2 interlock mount. "
        "Each set is screw and T-nut; no metric substitution.",
        "S03",
    )
    item(
        "V06",
        32,
        "Washer to drawing F-W14",
        "18 OD x6.6 ID x1 mm stainless; 28 panels +4 base recesses",
        "SHOP SPEC",
    )
    item(
        "V08",
        1,
        "ROBOTIS XM430-W350-T",
        "TTL version; use included horn; "
        "verify horn/case screw lengths against S04",
        "S04",
    )
    item(
        "V09",
        2,
        "NSK 626",
        "Open bearing6x19x6; protected clean interior",
        "S07",
    )
    item(
        "V10",
        4,
        "Ruland MCL-6-A",
        "6 mm bore one-piece clamp collar; supplied screw",
        "S08",
    )
    item(
        "V11",
        2,
        "HIWIN MGN7C + MGNR7,100 mm",
        "One block per100mm rail; "
        "7 mounting holes,5mm end distance,zero/light preload. "
        "Confirm order code, "
        "block thread pitch and seal length before purchase.",
        "S06",
        "RFQ",
    )
    item(
        "V12",
        1,
        "Dynatect EAS12,6mm/6mm",
        "Configured shaft-to-shaft, adjustable; "
        "request0.20 N m bidirectional setpoint. Designation is RFQ wording, "
        "not a confirmed order code.",
        "S05",
        "HOLD P2",
    )
    item(
        "V20",
        1,
        "Hammond 1554YA2GY",
        "Polycarbonate box/lid/gasket/six screws; "
        "independent benchtop cabinet",
        "S13",
    )
    item(
        "V21",
        1,
        "Hammond 1554YPL",
        "Factory internal steel panel; "
        "mounting screw set1591MM100 as required by purchased enclosure",
        "S13",
    )
    item(
        "V22",
        1,
        "MEAN WELL GST60A12-P1J",
        "External12V5A supply; region-matched "
        "factory AC lead; DC inlet adapter still requires rated "
        "cable assembly",
        "S14",
    )
    item(
        "V23",
        1,
        "MEAN WELL GST25A24-P1J",
        "External24V1.04A control supply; region-matched factory AC lead",
        "S15",
    )
    item(
        "V24",
        1,
        "Neutrik NC3FD-LX",
        "12V DC panel inlet; mating NC3MXX. "
        "Project pin1=0V,2=+12V,3 unused. Label DC ONLY.",
        "S16/S17",
    )
    item(
        "V25",
        1,
        "Neutrik NC4FD-LX",
        "24V DC panel inlet; mating NC4MXX. "
        "Project pin1=0V,4=+24V,2/3 unused. Label DC ONLY.",
        "S18/S19",
    )
    item(
        "V26",
        2,
        "Pilz PNOZ X3 774310",
        "K1 emergency stop; K2 guard. "
        "Separate relays avoid series input fault masking; wiring "
        "review required.",
        "S20",
        "HOLD P4",
    )
    item(
        "V27",
        1,
        "Schneider XB5AS8444",
        "2NC twist-release emergency stop; "
        "add yellow background and anti-rotation hardware per manufacturer",
        "S21",
    )
    item(
        "V28",
        2,
        "Schneider XB5AA61",
        "Separate blue reset buttons, one per "
        "safety relay; label E-STOP RESET and GUARD RESET",
        "S22",
    )
    item(
        "V29",
        1,
        "OMRON D4NS-1BF + D4DS-K2",
        "Guard switch/key. "
        "PG13.5 plastic gland required. Mounts B128-B130; "
        "physical insertion/access acceptance required",
        "S23",
        "HOLD P3",
    )
    item(
        "V30",
        20,
        "Phoenix UT 2,5 /3044076",
        "Terminal blocks; E-004 defines X1:1..20 and bus bridges. "
        "Wire sizing/routing and physical release remain P4",
        "S25",
        "HOLD P4",
    )
    item(
        "V31",
        2,
        "OMRON D2F-01L-D3",
        "Endpoint low-load switch with solder terminals; "
        "B125-B127 mount/cam; verify actual overtravel and signal timing",
        "S24",
        "HOLD P3",
    )
    item(
        "V32",
        1,
        "Raspberry Pi 5,4GB",
        "Outside sealed control enclosure, with "
        "official active cooler and Pi5 case; use physical-board fit check",
        "S10/S11",
    )
    item(
        "V33",
        1,
        "ROBOTIS U2D2",
        "USB to TTL interface; mount on hub with supplied rivet",
        "S26",
    )
    item(
        "V34",
        1,
        "ROBOTIS U2D2 Power Hub Board Set",
        "48x57; supplied M3 supports "
        "and100mm TTL lead. Power from screw terminals, not2.5mm DC jack.",
        "S26",
    )
    item(
        "V35",
        1,
        "ROBOTIS Robot Cable-X3P,240mm",
        "Confirm available factory length "
        "and route; no spliced TTL cable through moving pinch points",
        "S12/S26",
        "RFQ",
    )
    item(
        "V36",
        2,
        "Analog Devices DS18B20+,TO-92",
        "Powered3-wire sensors; "
        "case probe attachment and insulated housing to be defined",
        "S27",
        "HOLD P4",
    )
    item(
        "V37",
        1,
        "Raspberry Pi27W USB-C supply",
        "External official supply, "
        "regional plug. Independent Pi power maintains fault logging.",
        "S10",
        "SELECTED / verify accessories",
    )
    for pid, qty, pn, detail, source in [
        (
            "V38",
            4,
            "Phoenix 3022276 / CLIPFIX35-5",
            "Two end brackets per DIN rail; width5.2mm",
            "S30",
        ),
        (
            "V39",
            1,
            "Phoenix 3047028 / D-UT2,5/10",
            "End cover at open side of the20-terminal bank",
            "S31",
        ),
        (
            "V40",
            1,
            "Phoenix 0801733 / NS35/7.5 PERF2000MM",
            "Cut2x140mm;280mm used before saw waste",
            "S32",
        ),
        (
            "V41",
            2,
            "Phoenix 3030187 / FBS4-5",
            "Bridge X1:5..8(+24V) and9..12(0V24) only",
            "S33",
        ),
        (
            "V42",
            2,
            "Littelfuse FHAC0001ZXJ",
            "Covered32VDC20A inline holder; F1/F2=V52/V53; P4 coordination",
            "S35",
        ),
    ]:
        item(pid, qty, pn, detail, source, "SELECTED / P4 fit review")
    fasteners = [
        (
            "F01",
            22,
            "M2 x6",
            "14 rail +8 carriage screws; block pitch confirmation required",
            "0.15 initial",
        ),
        (
            "F02",
            8,
            "M2 x12",
            "Four travel stops;4mm engagement after8mm POM",
            "0.10 initial",
        ),
        (
            "F03",
            8,
            "M2.5 x8",
            "Two motor cheeks;2mm case engagement",
            "0.20 initial",
        ),
        (
            "F04",
            4,
            "M2 x8",
            "Motor flange6mm +0.2 shim washer;1.8mm horn engagement",
            "0.10 initial",
        ),
        (
            "F05",
            8,
            "M3 x8",
            "Bearing retaining plates;6mm thread engagement",
            "0.5 initial",
        ),
        ("F06", 8, "M3 x12", "Yoke arms6mm to hub flange6mm", "0.5 initial"),
        (
            "F07",
            8,
            "M4 x10",
            "Four crossbar end joints +four guide carrier joints",
            "1.0 initial",
        ),
        (
            "F08",
            8,
            "M4 x16",
            "Four counterweight screws +four motor cheek/foot screws",
            "1.5 initial",
        ),
        (
            "F09",
            4,
            "M4 x20",
            "Counterweight adjustment plates; washer/nyloc nut stack",
            "1.5 initial",
        ),
        (
            "F10",
            8,
            "M4 x12",
            "Four fixed tray screws(6mm engagement) +four endpoint "
            "upright feet with1mm washers(5mm engagement)",
            "1.0 initial",
        ),
        (
            "F11",
            8,
            "M5 x12",
            "Tower to angle;6mm engagement in8mm tower",
            "2.0 initial",
        ),
        (
            "F12",
            4,
            "M5 x14",
            "Angle6mm to sole10mm;8mm engagement",
            "2.0 initial",
        ),
        (
            "F13",
            10,
            "M5 x16",
            "Four tray posts +two stop posts +four motor-foot slots",
            "2.0 initial",
        ),
        (
            "F14",
            4,
            "M6 x16",
            "Tower soles;recessed2mm and1mm washer =>7mm engagement",
            "3.0 initial",
        ),
        (
            "F15",
            2,
            "M6 x25",
            "Angular stop screws;M6 jam nuts;minimum10mm engagement",
            "lock after setup",
        ),
    ]
    for pid, qty, size, use, torque in fasteners:
        item(
            pid,
            qty,
            "ISO4762 " + size,
            use
            + "; project torque "
            + torque
            + " N m (not a vendor rating). Clean dry fasteners; do not apply "
            "generic steel torque to aluminum threads.",
            "S28",
            "SPECIFIED / vendor SKU pending",
        )
    item(
        "F16",
        6,
        "ISO4026 M3x4 flat-point set screw",
        "Two per output hub +two cam; "
        "shaft flats required; proof test0.75 N m",
        "SHOP SPEC",
    )
    item(
        "F17",
        4,
        "M4 prevailing-torque locknut",
        "B120 to B106 joints; "
        "replace after repeated adjustment if retention declines",
        "SHOP SPEC",
    )
    item(
        "F18", 2, "M6 thin jam nut", "Angular-stop screw locking", "SHOP SPEC"
    )
    item(
        "F19",
        16,
        "M4 washer,1mm",
        "Four weight screws +eight adjustment faces +four endpoint feet",
        "SHOP SPEC",
    )
    item(
        "F20",
        8,
        "M5 washer,1mm",
        "Four motor slots +four endpoint sole mounts",
        "SHOP SPEC",
    )
    item("F21", 4, "M6 washer,1mm", "Recessed tower sole bolts", "SHOP SPEC")
    item(
        "F22",
        4,
        "D2.2 ID x5 OD x0.2 shim washer",
        "Horn screws; inspect thickness",
        "SHOP SPEC",
    )
    for pid, qty, pn, detail in [
        ("F23", 4, "ISO4762 M2x16", "Endpoint switch through-bolts"),
        (
            "F24",
            4,
            "ISO7089 M2 plain washer",
            "Endpoint switch screw-head seats; nominal0.3mm",
        ),
        ("F25", 4, "ISO4032 M2 hex nut", "Endpoint switch rear nuts"),
        (
            "F26",
            4,
            "DIN127 M2 spring washer",
            "Between switch upright and nut; compressed stack checked",
        ),
        (
            "F27",
            2,
            "ISO4026 M3x4 flat-point set screw",
            "Acetal endpoint cam; initial0.10Nm; NOT the load-bearing cam",
        ),
        (
            "F28",
            4,
            "ISO4762 M5x20",
            "Endpoint sole12mm +washer1mm;7mm thread engagement in base",
        ),
        (
            "F29",
            2,
            "ISO4762 M4x12",
            "D4DS-K2 key; washer/sleeve stack; torque2.4..2.8Nm",
        ),
        (
            "F30",
            2,
            "ISO4762 M4x50 blank",
            "D4NS body: cut to actual stack +nut +two full threads; "
            "record final length. Body clamp0.5..0.7Nm",
        ),
        (
            "F31",
            6,
            "ISO7089 M4 washer,1mm",
            "Two key heads +four switch body through-bolt faces",
        ),
        ("F32", 2, "ISO4032 M4 hex nut", "Guard-switch body rear nuts"),
        ("F33", 2, "DIN127 M4 spring washer", "Guard-switch body nut seats"),
    ]:
        item(pid, qty, pn, detail, "S24 / SHOP SPEC")
    item(
        "C01",
        "200x200mm",
        "Silicone sheet1mm,30-40 Shore A",
        "Contact pads and "
        "stop-cap pads; compatibility with phone coating to be checked",
        "SHOP SPEC",
        "HOLD P1",
    )
    item(
        "C02",
        "100x100mm",
        "Silicone sheet2mm,30-40 Shore A",
        "Travel-stop pads; 4 pieces6x8; measure actual float after bonding",
        "SHOP SPEC",
    )
    item(
        "C03",
        "4 pieces",
        "Neoprene pad25x50x3",
        "Under bottom frame, "
        "near four corners; compression/rocking checked on bench",
        "SHOP SPEC",
    )

    for pid, qty, pn, description, source in [
        ("V43", 1, "Adafruit1609", "Controller base PCB; E-005..008", "S36"),
        ("V44", 1, "LITEON LTV-817-C DIP4", "U1; CTR rankC", "S37"),
        ("V45", 1, "Vishay1N4148", "D1 reverse-LED protection", "S39"),
        ("V46", 1, "Vishay PR01 2kohm 1% 1W", "R1 permit input", "S38"),
        ("V47", 1, "Vishay PR01 10kohm 1% 1W", "R2 pulldown", "S38"),
        ("V48", 1, "Vishay PR01 1kohm 1% 1W", "R3 GPIO series", "S38"),
        ("V49", 2, "Vishay PR01 1.8kohm 1% 1W", "R4,R6", "S38"),
        ("V50", 2, "Vishay PR01 2.7kohm 1% 1W", "R5,R7", "S38"),
        ("V51", 1, "Vishay PR01 4.7kohm 1% 1W", "R8 1Wire", "S38"),
        ("V52", 1, "Littelfuse0287002.L", "F1 2A32VDC; holderV42", "S40"),
        ("V53", 1, "Littelfuse0287001.L", "F2 1A32VDC; holderV42", "S40"),
        ("V54", 1, "LAPP53015130", "Guard PG13.5 plastic gland", "S41"),
        ("V55", "1.8m", "LAPP1119754", "Guard4x0.5 cable; trim", "S42"),
        ("V56", 1, "Hammond1427BCGM16", "Guard cabinet entry only", "S34"),
    ]:
        item(pid, qty, pn, description, source, "SELECTED / P4 acceptance")
    item(
        "E-HOLD",
        "1 lot",
        "Electrical completion schedule",
        "Fuse coordination acceptance; "
        "wire/ferrules/glands; "
        "board mounting/cover; DC adapter cables; cable anchors; Pi "
        "breakout. "
        "These are not procurement-ready generic kits: release P4 first.",
        "UNRESOLVED",
        "HOLD P4",
    )
    item(
        "DUT-HOLD",
        "1 set",
        "Phone inserts and dummy",
        "Shop measures actual "
        "phone before machining inserts, as authorized by owner. No "
        "invented Apple dimensions.",
        "SHOP MEASUREMENT",
        "HOLD P1",
    )
    for p in json.loads((OUT / "custom-parts.json").read_text()):
        item(
            p["id"],
            p["quantity"],
            "Custom drawing " + p["id"],
            p["title"] + "; " + p["material"] + "; individual STEP supplied",
            "DRAWING BOOK",
            "DEVELOPMENT REVIEW",
        )
    return items


def main():
    sources = source_register()
    items = procurement()
    (OUT / "source-register.json").write_text(
        json.dumps(sources, indent=2) + "\n"
    )
    (OUT / "bom.json").write_text(
        json.dumps(
            {
                "revision": "B-development",
                "date": "2026-11-05",
                "release": "NOT released for full procurement or fabrication",
                "cost_basis": "No current vendor quotations; the Rev A "
                "$2510 estimate "
                "does not apply to this revised structure/fixture",
                "items": items,
            },
            indent=2,
        )
        + "\n"
    )
    with (OUT / "bom.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=list(items[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(items)
    print(f"Indexed {len(sources)} sources and {len(items)} BOM rows")


if __name__ == "__main__":
    main()
