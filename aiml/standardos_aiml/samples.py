"""Synthetic sample procurement specifications for the account-less demo workspace.

They are written for this project (not copied from real tenders) and
deliberately contain the kinds of issues the reasoning layer detects. The demo
workspace runs the real pipeline over them, so demo results are genuine engine
output.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SampleDocument:
    id: str
    name: str
    organization: str
    type: str  # PDF | DOCX | TXT
    text: str


SAMPLE_DOCUMENTS: list[SampleDocument] = [
    SampleDocument(
        id="sample-electrical-panel",
        name="Electrical Distribution Panel — Tender 2026/47 (sample)",
        organization="Infrastructure Procurement Cell (sample)",
        type="PDF",
        text="""TECHNICAL SPECIFICATION FOR LT DISTRIBUTION PANELS

1. Scope
1.1 This specification covers design, manufacture, testing and supply of indoor, floor-mounted LT distribution panels for the administrative block.

2. Applicable Standards
2.1 Switchgear assemblies shall conform to IS 8623:1993.
2.2 Miniature circuit breakers shall conform to IS 8828.
2.3 Power cables shall conform to IS 1554 (Part 1):1988.

3. Technical Requirements
3.1 Panels shall be rated for operation at an ambient temperature of 120°C.
3.2 The rated operational voltage of the panel shall be 415 V, 3 phase, 4 wire, 50 Hz.
3.3 Main busbars shall be of electrolytic grade copper rated for 800 A.
3.4 All outgoing circuits shall be provided with coordinated overload and short-circuit protection.
3.5 Protective earth continuity shall be maintained across all removable panels and doors.
3.6 Panels shall be indoor, floor-mounted type of suitable construction.
3.7 Cables shall be 4 core 95 sq mm aluminium conductor, PVC insulated, armoured.

4. Testing
4.1 Tests shall be carried out as per relevant IS.
""",
    ),
    SampleDocument(
        id="sample-water-pump",
        name="Industrial Water Pump Procurement (sample)",
        organization="Public Health Engineering Dept. (sample)",
        type="DOCX",
        text="""SUPPLY OF HORIZONTAL CENTRIFUGAL PUMPSETS

1. General
1.1 Horizontal centrifugal pump for continuous clean-water duty at the raw water pump house.
1.2 The pump shall conform to IS 1520.
1.3 Rated discharge: 60 m3/hr.
1.4 The pump shall be energy efficient.

2. Motor
2.1 The pump shall be driven by a 15 kW squirrel cage induction motor conforming to IS 325.
2.2 The motor shall be suitable for 415 V ± 15 %, 50 Hz supply.
2.3 Motor enclosure: IP55.
2.4 The motor shall have class F insulation and be suitable for S1 duty.

3. Inspection
3.1 The pump shall be tested at the manufacturer's works in the presence of the Engineer.
3.2 Earthing of the motor shall conform to IS 3043:1987.
""",
    ),
    SampleDocument(
        id="sample-water-tank",
        name="Rural Water Supply — RCC Service Reservoir (sample)",
        organization="Rural Water Supply Division (sample)",
        type="TXT",
        text="""CONSTRUCTION OF 200 KL RCC OVERHEAD SERVICE RESERVOIR AND SUPPLY OF TREATED WATER

A. STRUCTURAL WORKS
1. The reservoir is located in a coastal area and the exposure condition shall be considered as severe.
2. All reinforced concrete shall be of grade M20 conforming to IS 456:2000.
3. Nominal cover to reinforcement shall be 25 mm.
4. Cement shall be 43 grade OPC conforming to IS 8112.
5. Reinforcement shall be Fe 500D TMT bars conforming to IS 1786:2008.
6. Water-cement ratio shall not exceed 0.45.
7. Cube tests shall be carried out as per IS 516:1959.

B. TREATED WATER QUALITY
8. Treated water supplied shall conform to IS 10500.
9. pH of treated water shall be between 6.5 and 8.5.
10. Total dissolved solids shall not exceed 2000 mg/l.
11. Turbidity shall not be more than 1 NTU.
12. E. coli shall not be detectable in any 100 ml sample.
""",
    ),
]
