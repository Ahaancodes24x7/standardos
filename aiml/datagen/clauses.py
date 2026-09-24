"""Clause bank for the realworld_v2 dataset.

Every template is a requirement a real Indian public tender would contain,
phrased the way CPWD / state PWD / PHED / DISCOM specifications phrase it. Each
template has at least two paraphrases: variant 0 is used only by the *dev*
split and variant 1 (and later) only by the *test* split, so test documents are
worded differently from anything seen in development.

Values are written as ``{{number|unit}}`` and rendered by ``compose.py`` with a
per-document unit spelling ("415 V", "415V", "415 Volts" …).

Gold labels (category, attributes in canonical units, governing standard) are
attached to the template; defects are *plants* that replace or remove a
template and carry the gold finding a qualified reviewer should report.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


def a(parameter: str, value: float) -> dict[str, Any]:
    return {"parameter": parameter, "value": value}


def at(parameter: str, text: Optional[str] = None) -> dict[str, Any]:
    return {"parameter": parameter, "text": text} if text is not None else {"parameter": parameter}


@dataclass
class T:
    key: str
    cat: str
    variants: list[str]
    attrs: list[dict[str, Any]] = field(default_factory=list)
    std: Optional[str] = None  # governing standard (mapping gold); None for generic clauses
    clauses: tuple[str, ...] = ()  # governing clause ids (retrieval gold)
    query: bool = False  # usable as an isolated retrieval query (no citation in the text)
    section: str = "spec"  # site | spec | gtp | tests | docs


@dataclass
class Plant:
    key: str
    group: str  # conflict | gap | dependency | outdated | certification
    replaces: Optional[str]  # template key replaced (or removed when variants is empty)
    gold: dict[str, Any]
    variants: list[str] = field(default_factory=list)
    cat: str = ""
    attrs: list[dict[str, Any]] = field(default_factory=list)
    std: Optional[str] = None
    companions: dict[str, list[str]] = field(default_factory=dict)  # other templates reworded with this plant


@dataclass
class Domain:
    id: str
    title: str
    heading: str
    templates: list[T]
    plants: list[Plant]
    boq: list[str]
    makes: str
    gtp_title: Optional[str] = None


GENERIC = [
    T("docs.drawings", "documentation", [
        "The contractor shall submit detailed shop drawings for approval within {{21|days}} of award of work.",
        "Shop drawings and schematic diagrams shall be got approved from the Engineer-in-charge before manufacture.",
    ], section="docs"),
    T("docs.manuals", "documentation", [
        "Three sets of operation and maintenance manuals shall be handed over on completion.",
        "O&M manuals, as-built drawings and catalogues shall be furnished in triplicate at the time of handing over.",
    ], section="docs"),
    T("docs.warranty", "general", [
        "The complete installation shall be guaranteed against defective design, material and workmanship for a period of 12 months from the date of handing over.",
        "The supplier shall replace free of cost any part found defective within the defect liability period of 24 months.",
    ], section="docs"),
    T("docs.inspection", "testing", [
        "The equipment shall be inspected by the Engineer-in-charge at the manufacturer's works before dispatch.",
        "Pre-dispatch inspection shall be offered to the Department's authorised representative with 15 days notice.",
    ], section="tests"),
    T("docs.training", "general", [
        "The contractor shall train the Department's operating staff in operation and routine maintenance.",
        "Training of two operators for one week shall be imparted by the supplier after commissioning.",
    ], section="docs"),
]

VAGUE = [
    Plant("vague.suitable_size", "gap", None, {"group": "gap", "why": "'of suitable size' is not measurable"}, [
        "Distribution boards and enclosures shall be of suitable size.",
        "All enclosures shall be of adequate size to accommodate the equipment.",
    ], cat="general"),
    Plant("vague.reputed", "gap", None, {"group": "gap", "why": "'reputed make / robust' is not measurable"}, [
        "All equipment shall be of reputed make and robust construction.",
        "Only standard make items of best quality shall be used.",
    ], cat="general"),
]

# ---------------------------------------------------------------------------
# LV switchgear assembly
# ---------------------------------------------------------------------------

LT_PANEL = Domain(
    "lt_panel", "LT switchboard", "MAIN LT PANEL",
    templates=[
        T("panel.ambient", "environmental", [
            "The equipment shall be designed for a maximum ambient temperature of {{40|degC}}.",
            "All equipment shall be suitable for operation at an ambient air temperature not exceeding {{40|degC}}.",
        ], [a("ambient_temperature", 40)], "is-iec-61439-1-2020", ("is-iec-61439-1-2020#service-conditions",), True, "site"),
        T("panel.humidity", "environmental", [
            "Relative humidity at site may reach {{95|pct}}.",
            "The equipment shall be suitable for relative humidity up to {{95|pct}}.",
        ], [a("relative_humidity", 95)], "is-iec-61439-1-2020", ("is-iec-61439-1-2020#humidity-altitude",), False, "site"),
        T("panel.altitude", "environmental", [
            "The installation is at an altitude of less than {{1000|m}} above mean sea level.",
            "Site altitude does not exceed {{1000|m}} above MSL.",
        ], [a("altitude", 1000000)], "is-iec-61439-1-2020", ("is-iec-61439-1-2020#humidity-altitude",), True, "site"),
        T("panel.std", "general", [
            "The LT panel shall conform to IS/IEC 61439-1:2020 and IS/IEC 61439-2:2020.",
            "Switchboards shall be designed, manufactured and tested in accordance with IS/IEC 61439-1:2020 and IS/IEC 61439-2:2020.",
        ], std="is-iec-61439-2-2020"),
        T("panel.construction", "material", [
            "The panel shall be cubicle type, floor mounted, fabricated from CRCA sheet steel of {{2|mm}} thickness.",
            "Panels shall be free standing, totally enclosed, made of {{2|mm}} thick CRCA sheet with powder coated finish.",
        ]),
        T("panel.voltage", "electrical", [
            "The rated operational voltage shall be {{415|V}}, 3 phase, 4 wire, {{50|Hz}}.",
            "The panel shall be suitable for {{415|V}} ± {{10|pct}}, {{50|Hz}}, 3 phase 4 wire system.",
        ], [a("rated_voltage", 415), a("frequency", 50)], "is-iec-61439-1-2020", ("is-iec-61439-1-2020#ratings",), True),
        T("panel.busbar", "electrical", [
            "Main busbars shall be of electrolytic grade aluminium rated for {{1600|A}} continuous current.",
            "The horizontal busbar shall be high conductivity aluminium alloy of {{1600|A}} rating.",
        ], [a("rated_current", 1600)], "is-iec-61439-1-2020", ("is-iec-61439-1-2020#ratings",), True),
        T("panel.sc", "electrical", [
            "The busbars and panel shall withstand a short circuit current of {{50|kA}} for 1 second.",
            "Short time withstand rating of the switchboard shall be {{50|kA}} for 1 s.",
        ], [a("short_circuit_rating", 50000)], "is-iec-61439-1-2020", ("is-iec-61439-1-2020#short-circuit",), True),
        T("panel.ip", "environmental", [
            "The degree of protection of the panel enclosure shall be IP54.",
            "Enclosure protection class for the switchboard shall be IP 54.",
        ], [at("ip_rating", "IP54")], "is-iec-61439-1-2020", ("is-iec-61439-1-2020#ip",), True),
        T("panel.form", "electrical", [
            "The switchboard shall have Form 3b internal separation.",
            "Internal separation of functional units shall be Form 4.",
        ], std="is-iec-61439-2-2020", clauses=("is-iec-61439-2-2020#forms",), query=True),
        T("panel.acb", "electrical", [
            "Incomers shall be {{1600|A}}, 4 pole, electrically operated air circuit breakers conforming to IS/IEC 60947-2:2003.",
            "Incoming breaker shall be {{1600|A}} four pole draw-out ACB as per IS/IEC 60947-2:2003 with microprocessor release.",
        ], [a("rated_current", 1600)], "is-iec-60947-2-2003"),
        T("panel.mccb", "electrical", [
            "Outgoing feeders shall be MCCBs with ultimate breaking capacity of {{36|kA}}.",
            "All outgoing MCCBs shall have a rated service breaking capacity of not less than {{36|kA}}.",
        ], [a("short_circuit_rating", 36000)], "is-iec-60947-2-2003", ("is-iec-60947-2-2003#ratings",), True),
        T("panel.metering", "electrical", [
            "Multifunction meters of accuracy class 0.5 shall be provided on each incomer.",
            "Each incomer shall be provided with a digital multifunction meter with RS-485 port.",
        ]),
        T("panel.gtp.voltage", "electrical", ["Rated voltage: {{415|V}}", "Rated operational voltage: {{415|V}}"], [a("rated_voltage", 415)], "is-iec-61439-1-2020", section="gtp"),
        T("panel.gtp.current", "electrical", ["Rated current of main busbar: {{1600|A}}", "Busbar current rating: {{1600|A}}"], [a("rated_current", 1600)], "is-iec-61439-1-2020", section="gtp"),
        T("panel.gtp.sc", "electrical", ["Short time current rating: {{50|kA}} for 1 s", "Rated short-time withstand current: {{50|kA}} for 1 sec"], [a("short_circuit_rating", 50000)], "is-iec-61439-1-2020", section="gtp"),
        T("panel.gtp.ip", "environmental", ["Degree of protection: IP54", "Enclosure protection: IP54"], [at("ip_rating", "IP54")], "is-iec-61439-1-2020", section="gtp"),
        T("panel.routine", "testing", [
            "Routine verification of each assembly shall be carried out in accordance with IS/IEC 61439-1.",
            "Each switchboard shall be subjected to routine verification tests as per IS/IEC 61439-1 at the works.",
        ], std="is-iec-61439-1-2020", section="tests"),
        T("panel.typetest", "certification", [
            "Type test certificates of the offered panel design from a NABL accredited laboratory shall be submitted.",
            "The bidder shall furnish type test reports of the switchboard and breakers from an NABL accredited laboratory.",
        ], [at("conformity_evidence")], section="tests"),
    ],
    plants=[
        Plant("panel.ambient.hot", "conflict", "panel.ambient", {"group": "conflict", "standardId": "is-iec-61439-1-2020", "parameter": "ambient_temperature", "why": "above the 40 °C normal service limit"}, [
            "The equipment shall be designed for a maximum ambient temperature of {{50|degC}}.",
            "All equipment shall be suitable for operation at an ambient air temperature of {{50|degC}}.",
        ], "environmental", [a("ambient_temperature", 50)], "is-iec-61439-1-2020"),
        Plant("panel.altitude.high", "conflict", "panel.altitude", {"group": "conflict", "standardId": "is-iec-61439-1-2020", "parameter": "altitude", "why": "above 2000 m normal service altitude"}, [
            "The installation is at an altitude of {{2600|m}} above mean sea level.",
            "Site altitude is {{2600|m}} above MSL.",
        ], "environmental", [a("altitude", 2600000)], "is-iec-61439-1-2020"),
        Plant("panel.std.old", "outdated", "panel.std", {"group": "outdated", "standardId": "is-iec-61439-1-2020", "why": "IS 8623 is superseded by the IS/IEC 61439 series"}, [
            "The LT panel shall conform to IS 8623 (Part 1):1993.",
            "Switchboards shall be designed, manufactured and tested in accordance with IS 8623 (Part 1):1993.",
        ], "general"),
        Plant("panel.std.part2only", "dependency", "panel.std", {"group": "dependency", "standardId": "is-iec-61439-1-2020", "why": "Part 2 is read with Part 1, which is not cited"}, [
            "The LT panel shall conform to IS/IEC 61439-2:2020.",
            "Switchboards shall be designed, manufactured and tested in accordance with IS/IEC 61439-2:2020.",
        ], "general", companions={"panel.routine": [
            "Routine verification of each assembly shall be carried out in accordance with IS/IEC 61439-2.",
            "Each switchboard shall be subjected to routine verification tests as per IS/IEC 61439-2 at the works.",
        ]}),
        Plant("panel.ip.omit", "gap", "panel.ip", {"group": "gap", "parameter": "ip_rating", "why": "degree of protection not stated"}),
        Plant("panel.sc.vague", "gap", "panel.sc", {"group": "gap", "parameter": "short_circuit_rating", "why": "fault level stated without a value"}, [
            "The busbars shall be suitable for the fault level of the system.",
            "The switchboard shall withstand the short circuit level at site.",
        ], "electrical"),
        Plant("panel.cert.omit", "certification", "panel.typetest", {"group": "certification", "why": "no conformity evidence for the circuit breakers"}),
    ],
    boq=["Main LT panel as per specification | Set | 1", "Sub-distribution board, 12 way TPN | No. | 8"],
    makes="LT panel builder: as per approved list; ACB/MCCB: L&T / Siemens / Schneider / ABB",
    gtp_title="GUARANTEED TECHNICAL PARTICULARS — LT PANEL",
)

# ---------------------------------------------------------------------------
# Internal wiring, final distribution, earthing
# ---------------------------------------------------------------------------

WIRING = Domain(
    "wiring", "Internal electrification", "INTERNAL WIRING AND EARTHING",
    templates=[
        T("wiring.code", "general", [
            "Wiring shall be carried out as per IS 732:2019.",
            "The internal wiring installation shall comply with IS 732:2019.",
        ], std="is-732-2019"),
        T("wiring.system", "safety", [
            "The supply system shall be TN-S earthing arrangement.",
            "Earthing arrangement of the installation shall be TN-S system.",
        ], [at("earthing_system", "TN-S")], "is-3043-2018", ("is-3043-2018#systems",)),
        T("wiring.conduit", "installation", [
            "Wiring shall be concealed in rigid PVC conduits of {{1.5|mm}} wall thickness.",
            "All wiring shall be drawn through heavy gauge PVC conduits recessed in walls.",
        ]),
        T("wiring.wires", "electrical", [
            "Wires shall be FR PVC insulated, single core, stranded copper conductor of 450/750 V grade conforming to IS 694:2010.",
            "Building wires shall be 450/750 V grade PVC insulated multistrand copper conductor as per IS 694:2010.",
        ], [a("rated_voltage", 750), at("conductor_material", "copper"), at("insulation_material", "PVC")], "is-694-2010"),
        T("wiring.sizes", "dimensional", [
            "Lighting circuits shall be wired with {{1.5|mm2}} and power circuits with {{4|mm2}} copper conductors.",
            "Minimum conductor size shall be {{1.5|mm2}} for lighting points and {{4|mm2}} for power points.",
        ], [a("conductor_size", 1.5), a("conductor_size", 4)], "is-694-2010", ("is-694-2010#conductors",), True),
        T("wiring.wiretest", "testing", [
            "Wires shall be tested in accordance with IS 10810.",
            "Samples of wires shall be tested as per IS 10810 at the manufacturer's works.",
        ], std="is-10810", section="tests"),
        T("wiring.mcb", "electrical", [
            "Miniature circuit breakers shall conform to IS/IEC 60898-1 and shall have a breaking capacity of {{10|kA}}.",
            "MCBs shall be C-curve, as per IS/IEC 60898-1, with rated short circuit capacity of {{10|kA}}.",
        ], [a("short_circuit_rating", 10000)], "is-iec-60898-1-2002"),
        T("wiring.mcbrating", "electrical", [
            "MCB ratings shall range from {{6|A}} to {{32|A}} as shown in the single line diagram.",
            "Final circuit MCBs shall be rated between {{6|A}} and {{32|A}}.",
        ], [a("rated_current", 6)], "is-iec-60898-1-2002", ("is-iec-60898-1-2002#ratings",), True),
        T("wiring.rccb", "safety", [
            "RCCBs with rated residual operating current of 30 mA shall be provided for all socket outlet circuits and shall conform to IS 12640 (Part 1).",
            "Socket outlet circuits shall be protected by 30 mA RCCBs conforming to IS 12640 (Part 1).",
        ], std="is-12640-1-2016"),
        T("wiring.earthcode", "safety", [
            "Earthing shall be carried out in accordance with IS 3043:2018.",
            "The earthing system shall be designed and installed as per IS 3043:2018.",
        ], std="is-3043-2018"),
        T("wiring.electrodes", "safety", [
            "Two numbers of pipe earth electrodes shall be provided for the main distribution board.",
            "Main distribution board shall be earthed through two separate pipe earth electrodes.",
        ], std="is-3043-2018", clauses=("is-3043-2018#electrodes",), query=True),
        T("wiring.earthres", "safety", [
            "The earth resistance shall not exceed {{1|ohm}}.",
            "Combined resistance of the earthing system shall be less than {{1|ohm}}.",
        ], [a("earth_resistance", 1)], "is-3043-2018", ("is-3043-2018#electrodes", "is-3043-2018#measurement"), True),
        T("wiring.completiontest", "testing", [
            "On completion, insulation resistance and earth continuity tests shall be carried out in accordance with IS 732.",
            "Tests shall be carried out on completion of the installation as per IS 732 and results recorded.",
        ], std="is-732-2019", section="tests"),
        T("wiring.isi", "certification", [
            "Wires, MCBs and RCCBs shall be ISI marked.",
            "All wires, MCBs and RCCBs shall bear the BIS Standard Mark.",
        ], [at("conformity_evidence")], section="tests"),
    ],
    plants=[
        Plant("wiring.code.old", "outdated", "wiring.code", {"group": "outdated", "standardId": "is-732-2019", "why": "IS 732:1989 revised as IS 732:2019"}, [
            "Wiring shall be carried out as per IS 732:1989.",
            "The internal wiring installation shall comply with IS 732:1989.",
        ], "general"),
        Plant("wiring.system.omit", "gap", "wiring.system", {"group": "gap", "parameter": "earthing_system", "why": "earthing arrangement not stated"}),
        Plant("wiring.wires.1100", "conflict", "wiring.wires", {"group": "conflict", "standardId": "is-694-2010", "parameter": "rated_voltage", "why": "IS 694 covers cables up to 450/750 V"}, [
            "Wires shall be FR PVC insulated, single core, stranded copper conductor of 1100 V grade conforming to IS 694:2010.",
            "Building wires shall be 1100 V grade PVC insulated multistrand copper conductor as per IS 694:2010.",
        ], "electrical", [a("rated_voltage", 1100), at("conductor_material", "copper"), at("insulation_material", "PVC")], "is-694-2010"),
        Plant("wiring.wiretest.omit", "dependency", "wiring.wiretest", {"group": "dependency", "standardId": "is-10810", "why": "cable test method not named"}),
        Plant("wiring.mcb.old", "outdated", "wiring.mcb", {"group": "outdated", "standardId": "is-iec-60898-1-2002", "why": "IS 8828 superseded by IS/IEC 60898-1"}, [
            "Miniature circuit breakers shall conform to IS 8828 and shall have a breaking capacity of {{10|kA}}.",
            "MCBs shall be C-curve, as per IS 8828, with rated short circuit capacity of {{10|kA}}.",
        ], "electrical", [a("short_circuit_rating", 10000)], "is-iec-60898-1-2002"),
        Plant("wiring.earthcode.old", "outdated", "wiring.earthcode", {"group": "outdated", "standardId": "is-3043-2018", "why": "IS 3043:1987 revised as IS 3043:2018"}, [
            "Earthing shall be carried out in accordance with IS 3043:1987.",
            "The earthing system shall be designed and installed as per IS 3043:1987.",
        ], "safety"),
        Plant("wiring.completiontest.vague", "gap", "wiring.completiontest", {"group": "gap", "parameter": "test_method", "why": "completion testing without a method"}, [
            "The installation shall be tested on completion.",
            "The complete wiring shall be tested before handing over.",
        ], "testing"),
        Plant("wiring.isi.omit", "certification", "wiring.isi", {"group": "certification", "why": "no conformity evidence for wires and MCBs"}),
    ],
    boq=["Point wiring for light point with 1.5 sq mm FR PVC wire | Point | 240", "4 way SPN distribution board | No. | 16"],
    makes="Wires: Polycab / Havells / Finolex; MCB/RCCB: Legrand / Schneider / Havells",
)

# ---------------------------------------------------------------------------
# Power cables
# ---------------------------------------------------------------------------

CABLES = Domain(
    "cables", "LT power cables", "LT POWER AND CONTROL CABLES",
    templates=[
        T("cable.xlpe", "electrical", [
            "Power cables shall be 1.1 kV grade, aluminium conductor, XLPE insulated, armoured and PVC sheathed, conforming to IS 7098 (Part 1):1988.",
            "LT power cables shall be XLPE insulated 1.1 kV grade armoured cables with aluminium conductors as per IS 7098 (Part 1):1988.",
        ], [a("rated_voltage", 1100), at("conductor_material", "aluminium"), at("insulation_material", "XLPE")], "is-7098-1-1988"),
        T("cable.size", "dimensional", [
            "The main feeder cable shall be 3.5 core {{300|mm2}}.",
            "Size of the incoming feeder cable shall be 3.5 core x {{300|mm2}}.",
        ], [a("conductor_size", 300)], "is-7098-1-1988", ("is-7098-1-1988#conductors",), True),
        T("cable.temp", "electrical", [
            "The cables shall be suitable for a maximum continuous conductor temperature of {{90|degC}}.",
            "Continuous conductor operating temperature of XLPE cables shall be {{90|degC}}.",
        ], [a("conductor_temperature", 90)], "is-7098-1-1988", ("is-7098-1-1988#voltage",), True),
        T("cable.control", "electrical", [
            "Control cables shall be PVC insulated, copper conductor of {{2.5|mm2}}, 1.1 kV grade, conforming to IS 1554 (Part 1).",
            "Copper control cables of {{2.5|mm2}} shall be PVC insulated heavy duty type as per IS 1554 (Part 1).",
        ], [a("conductor_size", 2.5), at("conductor_material", "copper"), at("insulation_material", "PVC")], "is-1554-1-1988"),
        T("cable.conductor", "material", [
            "Conductors shall be stranded, class 2, conforming to IS 8130.",
            "Cable conductors shall meet the resistance requirements of IS 8130 for class 2 conductors.",
        ], std="is-8130-2013"),
        T("cable.test", "testing", [
            "Cables shall be tested in accordance with IS 10810.",
            "Acceptance tests on cables shall be carried out as per IS 10810 in presence of the Engineer.",
        ], std="is-10810", section="tests"),
        T("cable.laying", "installation", [
            "Cables shall be laid in RCC trenches or on perforated cable trays as shown in the drawings.",
            "Cables shall be laid directly in ground at a depth of {{750|mm}} with brick protection.",
        ]),
        T("cable.glands", "installation", [
            "Cable ends shall be terminated using double compression glands and crimped lugs.",
            "Terminations shall be made with brass double compression glands and tinned copper lugs.",
        ]),
        T("cable.drums", "documentation", [
            "Each drum shall be marked with the manufacturer's name, size, voltage grade and year of manufacture.",
            "Cable drums shall carry marking of size, type, length and manufacturer's name.",
        ]),
        T("cable.certs", "certification", [
            "Routine test certificates of cables shall be furnished with each consignment.",
            "Manufacturer's test certificates shall accompany every cable drum supplied.",
        ], [at("conformity_evidence")], section="tests"),
    ],
    plants=[
        Plant("cable.xlpe.11kv", "conflict", "cable.xlpe", {"group": "conflict", "standardId": "is-7098-1-1988", "parameter": "rated_voltage", "why": "IS 7098 (Part 1) covers up to 1.1 kV"}, [
            "Power cables shall be 11 kV grade, aluminium conductor, XLPE insulated, armoured and PVC sheathed, conforming to IS 7098 (Part 1):1988.",
            "HT power cables shall be XLPE insulated 11 kV grade armoured cables with aluminium conductors as per IS 7098 (Part 1):1988.",
        ], "electrical", [a("rated_voltage", 11000), at("conductor_material", "aluminium"), at("insulation_material", "XLPE")], "is-7098-1-1988"),
        Plant("cable.test.omit", "dependency", "cable.test", {"group": "dependency", "standardId": "is-10810", "why": "cable test method not named"}),
        Plant("cable.certs.omit", "certification", "cable.certs", {"group": "certification", "why": "no conformity evidence for cables"}),
        Plant("cable.size.omit", "gap", "cable.size", {"group": "gap", "parameter": "conductor_size", "why": "conductor size not stated"}),
    ],
    boq=["3.5C x 300 sq mm XLPE armoured cable | m | 350", "Cable tray 300 mm wide | m | 120"],
    makes="Cables: Polycab / KEI / Havells / RR Kabel",
)

# ---------------------------------------------------------------------------
# Induction motors
# ---------------------------------------------------------------------------

MOTORS = Domain(
    "motors", "Induction motors", "DRIVE MOTORS",
    templates=[
        T("motor.std", "general", [
            "Motors shall be squirrel cage induction motors conforming to IS 325:1996.",
            "The drive motor shall be a three phase TEFC squirrel cage induction motor as per IS 325:1996.",
        ], std="is-325-1996"),
        T("motor.power", "performance", [
            "The rated output of the motor shall be {{37|kW}}.",
            "Motor rating shall be {{37|kW}} continuous.",
        ], [a("rated_power", 37000)], "is-325-1996", ("is-325-1996#rating-plate",), True),
        T("motor.supply", "electrical", [
            "Motors shall be suitable for {{415|V}} ± {{10|pct}}, {{50|Hz}} ± {{5|pct}}, 3 phase supply.",
            "Motors shall operate satisfactorily on a supply of {{415|V}} ± {{10|pct}} and {{50|Hz}} ± {{5|pct}}.",
        ], [a("rated_voltage", 415), a("voltage_variation", 10), a("frequency", 50), a("frequency_variation", 5)], "is-325-1996", ("is-325-1996#variation",), True),
        T("motor.ie", "performance", [
            "Motors shall be of efficiency class IE3 as per IS 12615:2018.",
            "The motor shall be premium efficiency IE3 conforming to IS 12615:2018.",
        ], [at("efficiency_class", "IE3")], "is-12615-2018"),
        T("motor.ip", "environmental", [
            "Degree of protection of the motor enclosure shall be IP55.",
            "Motor enclosure shall be totally enclosed fan cooled with IP 55 protection.",
        ], [at("ip_rating", "IP55")], "is-325-1996", ("is-325-1996#enclosure",), True),
        T("motor.insulation", "electrical", [
            "Motors shall have class F insulation with temperature rise limited to class B and shall be suitable for S1 duty.",
            "Insulation shall be class F and the motor shall be rated for S1 continuous duty.",
        ], [at("insulation_class", "Class F"), at("duty_type", "S1")], "is-325-1996"),
        T("motor.speed", "performance", [
            "Synchronous speed of the motor shall be {{1500|rpm}}.",
            "Motor speed shall be {{1500|rpm}} (4 pole).",
        ], [a("speed", 1500)], "is-325-1996", ("is-325-1996#rating-plate",)),
        T("motor.test", "testing", [
            "Routine tests on motors shall be carried out as per IS 4029.",
            "Each motor shall be subjected to routine tests in accordance with IS 4029.",
        ], std="is-4029-2010", section="tests"),
        T("motor.cert", "certification", [
            "Motors shall bear the ISI mark.",
            "Motors shall be BIS certified and test certificates shall be furnished.",
        ], [at("conformity_evidence")], section="tests"),
    ],
    plants=[
        Plant("motor.supply.15", "conflict", "motor.supply", {"group": "conflict", "standardId": "is-325-1996", "parameter": "voltage_variation", "why": "±15 % exceeds the ±10 % variation of IS 325"}, [
            "Motors shall be suitable for {{415|V}} ± {{15|pct}}, {{50|Hz}} ± {{5|pct}}, 3 phase supply.",
            "Motors shall operate satisfactorily on a supply of {{415|V}} ± {{15|pct}} and {{50|Hz}} ± {{5|pct}}.",
        ], "electrical", [a("rated_voltage", 415), a("voltage_variation", 15), a("frequency", 50), a("frequency_variation", 5)], "is-325-1996"),
        Plant("motor.ie.vague", "gap", "motor.ie", {"group": "gap", "parameter": "efficiency_class", "why": "efficiency class not measurable"}, [
            "Motors shall be energy efficient.",
            "The motor shall be of high efficiency design.",
        ], "performance"),
        Plant("motor.ip.omit", "gap", "motor.ip", {"group": "gap", "parameter": "ip_rating", "why": "degree of protection not stated"}),
        Plant("motor.test.omit", "dependency", "motor.test", {"group": "dependency", "standardId": "is-4029-2010", "why": "motor test method not named"}),
        Plant("motor.cert.omit", "certification", "motor.cert", {"group": "certification", "why": "no conformity evidence for motors"}),
    ],
    boq=["Squirrel cage induction motor 37 kW, 1500 rpm | No. | 3"],
    makes="Motors: ABB / Siemens / Crompton Greaves / Kirloskar",
)

# ---------------------------------------------------------------------------
# Horizontal centrifugal pumps
# ---------------------------------------------------------------------------

PUMPS = Domain(
    "pumps", "Centrifugal pumps", "HORIZONTAL CENTRIFUGAL PUMPS",
    templates=[
        T("pump.std", "general", [
            "Pumps shall conform to IS 1520:1980.",
            "Horizontal centrifugal pumps for clear cold water shall comply with IS 1520:1980.",
        ], std="is-1520-1980"),
        T("pump.duty", "performance", [
            "Each pump shall deliver {{250|m3h}} against a total head of {{45|m}}.",
            "Duty point of each pump shall be {{250|m3h}} discharge at {{45|m}} total dynamic head.",
        ], [a("flow_rate", 250), a("pump_head", 45000)], "is-1520-1980", ("is-1520-1980#performance",), True),
        T("pump.eff", "performance", [
            "The pump efficiency at the duty point shall not be less than {{78|pct}}.",
            "Guaranteed pump efficiency at the rated duty shall be minimum {{78|pct}}.",
        ], [a("efficiency", 78)], "is-1520-1980", ("is-1520-1980#performance",), True),
        T("pump.materials", "material", [
            "Casing shall be of cast iron and impeller shall be of bronze.",
            "Pump casing shall be CI and impeller of leaded tin bronze.",
        ], std="is-1520-1980", clauses=("is-1520-1980#materials",), query=True),
        T("pump.noise", "environmental", [
            "Noise level at {{1|m}} from the pumpset shall not exceed {{85|dBA}}.",
            "Sound pressure level shall be limited to {{85|dBA}} at {{1|m}} distance.",
        ], [a("noise_level", 85)]),
        T("pump.test", "testing", [
            "Pumps shall be tested at the works in accordance with IS 9137.",
            "Performance tests on each pump shall be conducted as per IS 9137 in the presence of the Engineer.",
        ], std="is-9137-1978", section="tests"),
        T("pump.isi", "certification", [
            "Pumps shall bear the ISI mark.",
            "Pumps shall carry the BIS Standard Mark.",
        ], [at("conformity_evidence")], section="tests"),
        T("pump.gtp.flow", "performance", ["Discharge: {{250|m3h}}", "Rated discharge: {{250|m3h}}"], [a("flow_rate", 250)], "is-1520-1980", section="gtp"),
        T("pump.gtp.head", "performance", ["Total head: {{45|m}}", "Total dynamic head: {{45|m}}"], [a("pump_head", 45000)], "is-1520-1980", section="gtp"),
    ],
    plants=[
        Plant("pump.duty.nohead", "gap", "pump.duty", {"group": "gap", "parameter": "pump_head", "why": "duty head not stated"}, [
            "Each pump shall deliver {{250|m3h}}.",
            "Rated discharge of each pump shall be {{250|m3h}}.",
        ], "performance", [a("flow_rate", 250)], "is-1520-1980"),
        Plant("pump.eff.omit", "gap", "pump.eff", {"group": "gap", "parameter": "efficiency", "why": "efficiency not stated"}),
        Plant("pump.test.omit", "dependency", "pump.test", {"group": "dependency", "standardId": "is-9137-1978", "why": "pump acceptance test not named"}),
        Plant("pump.isi.omit", "certification", "pump.isi", {"group": "certification", "why": "no conformity evidence for pumps"}),
    ],
    boq=["Horizontal centrifugal pumpset 250 m3/hr at 45 m | Set | 3"],
    makes="Pumps: Kirloskar Brothers / KSB / Mather & Platt",
    gtp_title="PUMP DATA SHEET",
)

# ---------------------------------------------------------------------------
# Submersible pumpsets
# ---------------------------------------------------------------------------

SUBMERSIBLE = Domain(
    "submersible", "Submersible pumpsets", "BOREWELL SUBMERSIBLE PUMPSETS",
    templates=[
        T("sub.std", "general", [
            "Borewell submersible pumpsets shall conform to IS 8034:2018.",
            "Submersible pumpsets shall be manufactured to IS 8034:2018.",
        ], std="is-8034-2018"),
        T("sub.duty", "performance", [
            "Each pumpset shall deliver {{18|m3h}} against a total head of {{90|m}}.",
            "Duty point of each pumpset shall be {{18|m3h}} at {{90|m}} total head.",
        ], [a("flow_rate", 18), a("pump_head", 90000)], "is-8034-2018", ("is-8034-2018#performance",), True),
        T("sub.eff", "performance", [
            "The overall efficiency of the pumpset shall be not less than {{52|pct}}.",
            "Overall pumpset efficiency at duty point shall be minimum {{52|pct}}.",
        ], [a("efficiency", 52)], "is-8034-2018", ("is-8034-2018#performance",), True),
        T("sub.motor", "general", [
            "Motors shall be water filled, wet type, conforming to IS 9283:2013.",
            "The submersible motor shall be of rewindable wet type as per IS 9283:2013.",
        ], std="is-9283-2013"),
        T("sub.cable", "electrical", [
            "Submersible flat cables shall be 3 core, {{6|mm2}}, copper conductor, PVC insulated, conforming to IS 694:2010 and tested as per IS 10810.",
            "Flat submersible cables of 3 core {{6|mm2}} copper, PVC insulated, shall comply with IS 694:2010 and be tested to IS 10810.",
        ], [a("conductor_size", 6), at("conductor_material", "copper"), at("insulation_material", "PVC")], "is-694-2010"),
        T("sub.starter", "electrical", [
            "Each pumpset shall be provided with an automatic starter with single phasing preventer and dry run protection.",
            "The starter panel shall include dry run protection, overload relay and single phasing preventer.",
        ]),
        T("sub.bis", "certification", [
            "Pumpsets shall bear the BIS Standard Mark.",
            "Submersible pumpsets shall be ISI marked.",
        ], [at("conformity_evidence")], section="tests"),
    ],
    plants=[
        Plant("sub.eff.omit", "gap", "sub.eff", {"group": "gap", "parameter": "efficiency", "why": "overall efficiency not stated"}),
        Plant("sub.bis.omit", "certification", "sub.bis", {"group": "certification", "why": "no conformity evidence for pumpsets"}),
    ],
    boq=["Submersible pumpset 18 m3/hr at 90 m head | Set | 12"],
    makes="Submersible pumps: CRI / Kirloskar / Texmo",
)

# ---------------------------------------------------------------------------
# Distribution transformers
# ---------------------------------------------------------------------------

TRANSFORMERS = Domain(
    "transformers", "Distribution transformers", "DISTRIBUTION TRANSFORMERS",
    templates=[
        T("tx.std", "general", [
            "The transformers shall conform to IS 1180 (Part 1):2014.",
            "Distribution transformers shall be designed and manufactured to IS 1180 (Part 1):2014.",
        ], std="is-1180-1-2014"),
        T("tx.rating", "electrical", [
            "Rating: {{630|kVA}}, 11/0.433 kV, Dyn11 vector group.",
            "Transformer rating shall be {{630|kVA}}, 11 kV / 433 V, Dyn11.",
        ], [a("apparent_power", 630000)], "is-1180-1-2014", ("is-1180-1-2014#ratings",), True),
        T("tx.eel", "performance", [
            "The transformers shall meet energy efficiency level 2 as specified in IS 1180 (Part 1).",
            "Losses shall correspond to energy efficiency level 2 of IS 1180 (Part 1).",
        ], [at("efficiency_class", "Level 2")], "is-1180-1-2014"),
        T("tx.cooling", "general", [
            "Type: outdoor, oil immersed, ONAN cooled, copper wound.",
            "Transformers shall be outdoor type, mineral oil filled, naturally cooled, with copper windings.",
        ]),
        T("tx.temprise", "environmental", [
            "Temperature rise of top oil shall not exceed {{35|degC}} over an ambient of {{50|degC}}.",
            "Winding temperature rise shall be limited to {{40|degC}} over a maximum ambient of {{50|degC}}.",
        ], [a("ambient_temperature", 50)]),
        T("tx.tank", "material", [
            "The tank shall be of welded mild steel and painted with epoxy based paint.",
            "Transformer tank shall be fabricated from mild steel plates and epoxy painted.",
        ]),
        T("tx.routine", "testing", [
            "All routine tests shall be carried out on each transformer as per IS 2026 (Part 1):2011.",
            "Each transformer shall be subjected to routine tests in accordance with IS 2026 (Part 1):2011.",
        ], std="is-2026-1-2011", section="tests"),
        T("tx.typetest", "certification", [
            "Type test reports of the offered design from a NABL accredited laboratory shall be submitted with the bid.",
            "The bidder shall submit type test certificates from an NABL accredited laboratory for the offered rating.",
        ], [at("conformity_evidence")], section="tests"),
    ],
    plants=[
        Plant("tx.rating.big", "conflict", "tx.rating", {"group": "conflict", "standardId": "is-1180-1-2014", "parameter": "apparent_power", "why": "above the 2500 kVA scope of IS 1180 (Part 1)"}, [
            "Rating: {{3150|kVA}}, 33/0.433 kV, Dyn11 vector group.",
            "Transformer rating shall be {{3150|kVA}}, 33 kV / 433 V, Dyn11.",
        ], "electrical", [a("apparent_power", 3150000)], "is-1180-1-2014"),
        Plant("tx.eel.omit", "gap", "tx.eel", {"group": "gap", "parameter": "efficiency_class", "why": "energy efficiency level not stated"}),
        Plant("tx.routine.old", "outdated", "tx.routine", {"group": "outdated", "standardId": "is-2026-1-2011", "why": "1977 edition cited"}, [
            "All routine tests shall be carried out on each transformer as per IS 2026 (Part 1):1977.",
            "Each transformer shall be subjected to routine tests in accordance with IS 2026 (Part 1):1977.",
        ], "testing"),
        Plant("tx.routine.omit", "dependency", "tx.routine", {"group": "dependency", "standardId": "is-2026-1-2011", "why": "transformer test standard not named"}, [
            "All routine tests shall be carried out on each transformer before dispatch.",
            "Each transformer shall be routine tested at the works.",
        ], "testing"),
        Plant("tx.typetest.omit", "certification", "tx.typetest", {"group": "certification", "why": "no conformity evidence for transformers"}),
    ],
    boq=["630 kVA 11/0.433 kV distribution transformer | No. | 4"],
    makes="Transformers: as per approved vendor list of the utility",
    gtp_title="GUARANTEED TECHNICAL PARTICULARS — TRANSFORMER",
)

# ---------------------------------------------------------------------------
# Reinforced concrete
# ---------------------------------------------------------------------------

RCC = Domain(
    "rcc", "Reinforced concrete works", "CONCRETE AND REINFORCEMENT",
    templates=[
        T("rcc.exposure", "environmental", [
            "The structure shall be designed for the exposure condition severe as defined in IS 456:2000.",
            "Exposure condition shall be considered as severe for all members.",
        ], [at("exposure_condition", "severe")], "is-456-2000", ("is-456-2000#exposure",), False, "site"),
        T("rcc.std", "general", [
            "All plain and reinforced concrete work shall conform to IS 456:2000.",
            "Design and construction of RCC shall be in accordance with IS 456:2000.",
        ], std="is-456-2000"),
        T("rcc.grade", "material", [
            "All RCC work shall be of grade M30.",
            "Grade of concrete for all structural members shall be M 30.",
        ], [a("concrete_grade", 30)], "is-456-2000", ("is-456-2000#min-grade",), True),
        T("rcc.cover", "dimensional", [
            "Nominal cover to reinforcement shall be {{45|mm}}.",
            "Clear cover to main reinforcement shall be {{45|mm}} for all members.",
        ], [a("nominal_cover", 45)], "is-456-2000", ("is-456-2000#cover",), True),
        T("rcc.wc", "material", [
            "The free water-cement ratio shall not exceed 0.45.",
            "Maximum free water cement ratio shall be 0.45.",
        ], [a("water_cement_ratio", 0.45)], "is-456-2000", ("is-456-2000#wc-ratio",), True),
        T("rcc.cc", "material", [
            "Minimum cement content shall be {{320|kgm3}}.",
            "Cement content shall not be less than {{320|kgm3}} of concrete.",
        ], [a("cement_content", 320)], "is-456-2000", ("is-456-2000#cement-content",), True),
        T("rcc.cement", "material", [
            "Cement shall be ordinary Portland cement 43 grade conforming to IS 269:2015.",
            "OPC 43 grade cement as per IS 269:2015 shall be used.",
        ], [at("cement_type", "OPC 43 grade")], "is-269-2015"),
        T("rcc.agg", "material", [
            "Coarse and fine aggregates shall conform to IS 383:2016.",
            "Aggregates shall comply with the requirements of IS 383:2016.",
        ], std="is-383-2016"),
        T("rcc.steel", "material", [
            "Reinforcement shall be Fe 500D TMT bars conforming to IS 1786:2008.",
            "High strength deformed bars of grade Fe 500D as per IS 1786:2008 shall be used.",
        ], [at("steel_grade", "Fe 500D")], "is-1786-2008"),
        T("rcc.mix", "material", [
            "Concrete shall be design mix proportioned as per IS 10262:2019.",
            "Mix design shall be carried out in accordance with IS 10262:2019.",
        ], std="is-10262-2019"),
        T("rcc.cubes", "testing", [
            "Compressive strength tests shall be carried out as per IS 516 (Part 1/Sec 1):2021.",
            "Cube tests for compressive strength shall be done in accordance with IS 516 (Part 1/Sec 1):2021.",
        ], std="is-516-1-1-2021", section="tests"),
        T("rcc.curing", "installation", [
            "Curing shall be continued for a minimum period of 10 days.",
            "Concrete shall be kept continuously moist for at least 10 days.",
        ]),
        T("rcc.vibration", "installation", [
            "Concrete shall be compacted with mechanical needle vibrators.",
            "Compaction shall be done by immersion vibrators.",
        ]),
        T("rcc.mtc", "certification", [
            "Manufacturer's test certificates shall be furnished for each lot of cement and reinforcement steel.",
            "Mill test certificates for steel and test certificates for cement shall be submitted for every consignment.",
        ], [at("conformity_evidence")], section="tests"),
    ],
    plants=[
        Plant("rcc.grade.low", "conflict", "rcc.grade", {"group": "conflict", "standardId": "is-456-2000", "parameter": "concrete_grade", "why": "M20 below M30 minimum for severe exposure"}, [
            "All RCC work shall be of grade M20.",
            "Grade of concrete for all structural members shall be M 20.",
        ], "material", [a("concrete_grade", 20)], "is-456-2000"),
        Plant("rcc.cover.low", "conflict", "rcc.cover", {"group": "conflict", "standardId": "is-456-2000", "parameter": "nominal_cover", "why": "cover below 45 mm for severe exposure"}, [
            "Nominal cover to reinforcement shall be {{30|mm}}.",
            "Clear cover to main reinforcement shall be {{30|mm}} for all members.",
        ], "dimensional", [a("nominal_cover", 30)], "is-456-2000"),
        Plant("rcc.wc.high", "conflict", "rcc.wc", {"group": "conflict", "standardId": "is-456-2000", "parameter": "water_cement_ratio", "why": "w/c above 0.45 for severe exposure"}, [
            "The free water-cement ratio shall not exceed 0.55.",
            "Maximum free water cement ratio shall be 0.55.",
        ], "material", [a("water_cement_ratio", 0.55)], "is-456-2000"),
        Plant("rcc.cement.old", "outdated", "rcc.cement", {"group": "outdated", "standardId": "is-269-2015", "why": "IS 8112 superseded by IS 269:2015"}, [
            "Cement shall be ordinary Portland cement 43 grade conforming to IS 8112.",
            "OPC 43 grade cement as per IS 8112 shall be used.",
        ], "material", [at("cement_type", "OPC 43 grade")]),
        Plant("rcc.agg.omit", "dependency", "rcc.agg", {"group": "dependency", "standardId": "is-383-2016", "why": "aggregate standard not addressed"}),
        Plant("rcc.steel.old", "outdated", "rcc.steel", {"group": "outdated", "standardId": "is-1786-2008", "why": "1985 edition cited"}, [
            "Reinforcement shall be Fe 500D TMT bars conforming to IS 1786:1985.",
            "High strength deformed bars of grade Fe 500D as per IS 1786:1985 shall be used.",
        ], "material", [at("steel_grade", "Fe 500D")]),
        Plant("rcc.cubes.old", "outdated", "rcc.cubes", {"group": "outdated", "standardId": "is-516-1-1-2021", "why": "IS 516:1959 superseded"}, [
            "Compressive strength tests shall be carried out as per IS 516:1959.",
            "Cube tests for compressive strength shall be done in accordance with IS 516:1959.",
        ], "testing"),
        Plant("rcc.cubes.omit", "dependency", "rcc.cubes", {"group": "dependency", "standardId": "is-516-1-1-2021", "why": "strength test method not named"}, [
            "Cube tests for compressive strength shall be carried out at 7 and 28 days.",
            "Concrete cubes shall be tested for compressive strength at 28 days.",
        ], "testing"),
        Plant("rcc.mtc.omit", "certification", "rcc.mtc", {"group": "certification", "why": "no conformity evidence for steel and cement"}),
    ],
    boq=["RCC M30 in superstructure | cum | 420", "TMT reinforcement Fe 500D | MT | 58"],
    makes="Cement: UltraTech / ACC / Ambuja; Steel: SAIL / TATA / JSW",
    gtp_title="MIX DESIGN PARAMETERS",
)

# ---------------------------------------------------------------------------
# Drinking water quality
# ---------------------------------------------------------------------------

WATER = Domain(
    "water", "Drinking water quality", "TREATED WATER QUALITY",
    templates=[
        T("water.std", "quality", [
            "Treated water supplied shall conform to IS 10500:2012.",
            "The quality of water supplied shall meet IS 10500:2012.",
        ], std="is-10500-2012"),
        T("water.ph", "quality", [
            "pH of treated water shall be between 6.5 and 8.5.",
            "pH value: 6.5 to 8.5",
        ], [a("ph", 6.5)], "is-10500-2012", ("is-10500-2012#ph",), True),
        T("water.tds", "quality", [
            "Total dissolved solids shall not exceed {{500|mgl}}.",
            "TDS of supplied water shall be within {{500|mgl}}.",
        ], [a("tds", 500)], "is-10500-2012", ("is-10500-2012#tds",), True),
        T("water.turbidity", "quality", [
            "Turbidity shall not be more than {{1|NTU}}.",
            "Turbidity of treated water shall be limited to {{1|NTU}}.",
        ], [a("turbidity", 1)], "is-10500-2012", ("is-10500-2012#turbidity",), True),
        T("water.fluoride", "quality", [
            "Fluoride shall not exceed {{1.0|mgl}}.",
            "Fluoride content shall be within {{1.0|mgl}}.",
        ], [a("fluoride", 1.0)], "is-10500-2012", ("is-10500-2012#fluoride",), True),
        T("water.nitrate", "quality", [
            "Nitrate shall not exceed {{45|mgl}}.",
            "Nitrate as NO3 shall be less than {{45|mgl}}.",
        ], [a("nitrate", 45)], "is-10500-2012", ("is-10500-2012#nitrate",), True),
        T("water.arsenic", "quality", [
            "Arsenic shall not exceed {{0.01|mgl}}.",
            "Arsenic content in supplied water shall be less than {{0.01|mgl}}.",
        ], [a("arsenic", 0.01)], "is-10500-2012", ("is-10500-2012#arsenic",), True),
        T("water.hardness", "quality", [
            "Total hardness as CaCO3 shall not exceed {{200|mgl}}.",
            "Total hardness shall be within {{200|mgl}} as CaCO3.",
        ], [a("total_hardness", 200)], "is-10500-2012", ("is-10500-2012#hardness",), True),
        T("water.ecoli", "quality", [
            "E. coli shall not be detectable in any 100 ml sample.",
            "Total coliforms shall be absent in any 100 ml sample.",
        ], [at("bacteriological_quality")], "is-10500-2012", ("is-10500-2012#bacteriological",), True),
        T("water.tests", "testing", [
            "Water samples shall be tested in a NABL accredited laboratory as per IS 3025 and IS 1622.",
            "Physico-chemical tests shall follow IS 3025 and bacteriological examination shall follow IS 1622.",
        ], std="is-3025", section="tests"),
        T("water.reports", "documentation", [
            "Test reports shall be submitted to the Engineer-in-charge for each source.",
            "Monthly water quality reports shall be furnished to the Department.",
        ], section="docs"),
    ],
    plants=[
        Plant("water.tds.high", "conflict", "water.tds", {"group": "conflict", "standardId": "is-10500-2012", "parameter": "tds", "why": "2000 mg/l above 500 mg/l acceptable limit"}, [
            "Total dissolved solids shall not exceed {{2000|mgl}}.",
            "TDS of supplied water shall be within {{2000|mgl}}.",
        ], "quality", [a("tds", 2000)], "is-10500-2012"),
        Plant("water.fluoride.high", "conflict", "water.fluoride", {"group": "conflict", "standardId": "is-10500-2012", "parameter": "fluoride", "why": "1.5 mg/l above 1.0 mg/l acceptable limit"}, [
            "Fluoride shall not exceed {{1.5|mgl}}.",
            "Fluoride content shall be within {{1.5|mgl}}.",
        ], "quality", [a("fluoride", 1.5)], "is-10500-2012"),
        Plant("water.arsenic.high", "conflict", "water.arsenic", {"group": "conflict", "standardId": "is-10500-2012", "parameter": "arsenic", "why": "0.05 mg/l above 0.01 mg/l"}, [
            "Arsenic shall not exceed {{0.05|mgl}}.",
            "Arsenic content in supplied water shall be less than {{0.05|mgl}}.",
        ], "quality", [a("arsenic", 0.05)], "is-10500-2012"),
        Plant("water.turbidity.high", "conflict", "water.turbidity", {"group": "conflict", "standardId": "is-10500-2012", "parameter": "turbidity", "why": "5 NTU above 1 NTU"}, [
            "Turbidity shall not be more than {{5|NTU}}.",
            "Turbidity of treated water shall be limited to {{5|NTU}}.",
        ], "quality", [a("turbidity", 5)], "is-10500-2012"),
        Plant("water.tests.no1622", "dependency", "water.tests", {"group": "dependency", "standardId": "is-1622-1981", "why": "bacteriological test method not named"}, [
            "Water samples shall be tested in a NABL accredited laboratory as per IS 3025.",
            "Physico-chemical tests on water samples shall follow IS 3025.",
        ], "testing", std="is-3025"),
    ],
    boq=["Water quality testing (complete set of parameters) | Sample | 48"],
    makes="Testing laboratory: NABL accredited",
)

# ---------------------------------------------------------------------------
# Structural steel
# ---------------------------------------------------------------------------

STEEL = Domain(
    "steel", "Structural steel", "STRUCTURAL STEEL WORK",
    templates=[
        T("steel.std", "material", [
            "Structural steel sections and plates shall be of grade E250 conforming to IS 2062:2011.",
            "Rolled steel sections shall be E250 grade as per IS 2062:2011.",
        ], std="is-2062-2011"),
        T("steel.paint", "material", [
            "All steel work shall receive one coat of zinc chromate primer and two coats of enamel paint.",
            "Steel surfaces shall be painted with red oxide primer and two finishing coats.",
        ]),
        T("steel.fab", "installation", [
            "Fabrication and erection shall be carried out as per the approved drawings.",
            "Welding shall be done by qualified welders using approved electrodes.",
        ]),
        T("steel.mtc", "certification", [
            "Mill test certificates shall be submitted for all structural steel.",
            "Structural steel shall be accompanied by mill test certificates from the producer.",
        ], [at("conformity_evidence")], section="tests"),
    ],
    plants=[
        Plant("steel.mtc.omit", "certification", "steel.mtc", {"group": "certification", "why": "no conformity evidence for structural steel"}),
    ],
    boq=["Structural steel work in trusses and purlins | MT | 22"],
    makes="Steel: SAIL / TATA / JSW",
)

DOMAINS: dict[str, Domain] = {d.id: d for d in [LT_PANEL, WIRING, CABLES, MOTORS, PUMPS, SUBMERSIBLE, TRANSFORMERS, RCC, WATER, STEEL]}

# Realistic tender packages (a tender bundles related trades).
PACKAGES: list[tuple[str, list[str], str]] = [
    ("Supply, installation, testing and commissioning of LT electrical distribution system", ["lt_panel", "cables"], "CENTRAL PUBLIC WORKS DEPARTMENT"),
    ("Internal electrification including wiring, distribution boards and earthing", ["wiring"], "PUBLIC WORKS DEPARTMENT"),
    ("Design, supply and commissioning of raw water pumping machinery", ["pumps", "motors", "cables"], "JAL NIGAM"),
    ("Supply and installation of borewell submersible pumpsets and water quality testing", ["submersible", "water"], "PUBLIC HEALTH ENGINEERING DEPARTMENT"),
    ("Procurement of distribution transformers and LT cables", ["transformers", "cables"], "VIDYUT VITRAN NIGAM LIMITED"),
    ("Construction of RCC elevated service reservoir", ["rcc"], "WATER SUPPLY AND DRAINAGE BOARD"),
    ("Construction of pump house with structural steel roof and electrical works", ["rcc", "steel", "wiring"], "MUNICIPAL CORPORATION"),
    ("Electrical works for sewage treatment plant including motors and panels", ["lt_panel", "motors", "cables"], "URBAN DEVELOPMENT AUTHORITY"),
    ("Rural piped water supply scheme — pumping and treated water supply", ["pumps", "motors", "water"], "RURAL WATER SUPPLY DEPARTMENT"),
    ("Hostel block construction — civil and internal electrical works", ["rcc", "wiring"], "PUBLIC WORKS DEPARTMENT"),
]
