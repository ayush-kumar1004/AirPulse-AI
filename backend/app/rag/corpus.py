"""
AirPulse AI - Regulatory Knowledge Base
Official statutory provisions and frameworks for Air Quality Management in Delhi-NCR:
1. Graded Response Action Plan (GRAP) for Delhi-NCR (CAQM Direction No. 75 / Revised GRAP Framework).
2. Commission for Air Quality Management in NCR & Adjoining Areas (CAQM) Directions.
3. The Air (Prevention and Control of Pollution) Act, 1981 (Act No. 14 of 1981).
"""

from typing import List, Dict, Any

REGULATORY_DOCUMENTS: List[Dict[str, Any]] = [
    # =========================================================================
    # GRAP STAGE I: "POOR" AIR QUALITY (AQI 201 - 300)
    # =========================================================================
    {
        "doc_id": "GRAP-STAGE-I-01",
        "title": "GRAP Stage I: Mechanized Sweeping and Road Dust Mitigation",
        "category": "GRAP_STAGE_1",
        "section": "Stage I - Action 1 & 2",
        "legal_citation": "CAQM Direction No. 75, Schedule I (AQI 201-300)",
        "metadata_json": {
            "aqi_range": "201-300",
            "category": "Poor",
            "target_sectors": ["Roads", "Municipal", "Transportation"],
            "lead_agency": "MCD / NDMC / PWD / NHAI"
        },
        "content": (
            "GRAP Stage I ('Poor' Air Quality, AQI 201-300) - Action Points 1 & 2:\n"
            "1. Mechanized/vacuum sweeping and water sprinkling on identified municipal roads and traffic corridors "
            "with periodic intervals to arrest re-suspension of road dust.\n"
            "2. Ensure proper disposal of dust collected in designated landfills/dumpsites without open dumping.\n"
            "3. Heavy deployment of water sprinklers and mist-guns at construction corridors and high traffic density intersections."
        )
    },
    {
        "doc_id": "GRAP-STAGE-I-02",
        "title": "GRAP Stage I: C&D Dust Control and Anti-Smog Gun Mandates",
        "category": "GRAP_STAGE_1",
        "section": "Stage I - Action 3 & 4",
        "legal_citation": "CAQM Direction No. 75, Schedule I r/w Direction No. 71",
        "metadata_json": {
            "aqi_range": "201-300",
            "category": "Poor",
            "target_sectors": ["Construction", "Real Estate"],
            "lead_agency": "DPCC / Local Municipal Bodies"
        },
        "content": (
            "GRAP Stage I ('Poor' Air Quality, AQI 201-300) - Construction & Demolition Dust Directives:\n"
            "1. Enforce strict adherence to environmental dust mitigation guidelines at all Construction & Demolition (C&D) sites.\n"
            "2. Mandatory deployment of anti-smog guns at all projects with plot area exceeding 500 sq meters registered on the DPCC dust portal.\n"
            "3. Ensure continuous water sprinkling on loose soil, unpaved haul tracks, and demolition rubble.\n"
            "4. Total ban on uncovered transportation of C&D waste and loose construction materials (sand, aggregate, cement). "
            "Vehicles violating covering norms shall be impounded immediately."
        )
    },
    {
        "doc_id": "GRAP-STAGE-I-03",
        "title": "GRAP Stage I: Vehicular Emissions, Overaged Vehicles & Open Burning",
        "category": "GRAP_STAGE_1",
        "section": "Stage I - Action 5, 6 & 7",
        "legal_citation": "CAQM Direction No. 75, Schedule I r/w Section 19(5) Air Act, 1981",
        "metadata_json": {
            "aqi_range": "201-300",
            "category": "Poor",
            "target_sectors": ["Vehicular", "Waste Management"],
            "lead_agency": "Delhi Traffic Police / Transport Dept / Municipal Corporation"
        },
        "content": (
            "GRAP Stage I ('Poor' Air Quality, AQI 201-300) - Vehicular & Biomass Burning Mandates:\n"
            "1. Strict enforcement of Pollution Under Control (PUC) certification for all plying motor vehicles.\n"
            "2. Intensive impounding of end-of-life overaged vehicles (diesel vehicles > 10 years, petrol vehicles > 15 years) "
            "as per Hon'ble Supreme Court and NGT orders.\n"
            "3. Zero tolerance for open burning of municipal solid waste (MSW), leaves, biomass, agricultural residues, and plastic. "
            "Levy heavy environmental compensation penalties on defaulters.\n"
            "4. Synchronize traffic movements and deploy traffic police at critical congestion bottlenecks to eliminate idling."
        )
    },

    # =========================================================================
    # GRAP STAGE II: "VERY POOR" AIR QUALITY (AQI 301 - 400)
    # =========================================================================
    {
        "doc_id": "GRAP-STAGE-II-01",
        "title": "GRAP Stage II: Diesel Generator Restrictions and Clean Power Augmentation",
        "category": "GRAP_STAGE_2",
        "section": "Stage II - Action 2 & 5",
        "legal_citation": "CAQM Direction No. 75, Schedule II r/w Direction No. 73",
        "metadata_json": {
            "aqi_range": "301-400",
            "category": "Very Poor",
            "target_sectors": ["Power", "Commercial", "Industrial", "Residential"],
            "lead_agency": "State DISCOMs / DPCC / District Magistrates"
        },
        "content": (
            "GRAP Stage II ('Very Poor' Air Quality, AQI 301-400) - Diesel Generator (DG) Regulations:\n"
            "1. Prohibit the operation of Diesel Generator (DG) sets of all capacities across commercial, residential, "
            "and industrial establishments in NCR, except for essential and emergency services.\n"
            "2. Permitted exceptions: Healthcare facilities/hospitals, medical equipment, elevators, railway stations, "
            "metro rail corporations, airports, interstate bus terminals, sewage treatment plants, and water supply pumping stations.\n"
            "3. DG sets converted to dual-fuel (PNG + Diesel) or equipped with approved Emission Control Devices (RECD) "
            "may operate strictly under authorized industrial rosters.\n"
            "4. Electricity distribution companies (DISCOMs) must guarantee uninterrupted continuous power supply to minimize DG demand."
        )
    },
    {
        "doc_id": "GRAP-STAGE-II-02",
        "title": "GRAP Stage II: Mechanical Sweeping, Dust Suppressants & Hotspot Mitigation",
        "category": "GRAP_STAGE_2",
        "section": "Stage II - Action 1 & 4",
        "legal_citation": "CAQM Direction No. 75, Schedule II (AQI 301-400)",
        "metadata_json": {
            "aqi_range": "301-400",
            "category": "Very Poor",
            "target_sectors": ["Municipal", "Hotspots"],
            "lead_agency": "MCD / PWD / DPCC Hotspot Monitoring Squads"
        },
        "content": (
            "GRAP Stage II ('Very Poor' Air Quality, AQI 301-400) - Intensified Dust & Hotspot Mitigation:\n"
            "1. Daily mechanical/vacuum-based sweeping and continuous water sprinkling along with chemical dust suppressants "
            "on arterial roads and identified heavy traffic corridors prior to morning (07:00-09:00) and evening peak hours.\n"
            "2. Mobilize dedicated municipal flying squads for 24x7 inspection of 13 critical Delhi pollution hotspots "
            "(Anand Vihar, Jahangirpuri, Rohini, Wazirpur, Bawana, Mundka, Narela, Okhla, Punjabi Bagh, R.K. Puram, Vivek Vihar, Mayapuri, Dwarka).\n"
            "3. Enforce strict shutdown and heavy spot fines on unpaved C&D activities contributing to localized particulate plumes."
        )
    },
    {
        "doc_id": "GRAP-STAGE-II-03",
        "title": "GRAP Stage II: Public Transport Augmentation & Differential Parking Tariffs",
        "category": "GRAP_STAGE_2",
        "section": "Stage II - Action 3 & 6",
        "legal_citation": "CAQM Direction No. 75, Schedule II r/w Transport Policy",
        "metadata_json": {
            "aqi_range": "301-400",
            "category": "Very Poor",
            "target_sectors": ["Public Transit", "Parking Management"],
            "lead_agency": "DTC / DIMTS / DMRC / Municipal Corporations"
        },
        "content": (
            "GRAP Stage II ('Very Poor' Air Quality, AQI 301-400) - Traffic Management & Modal Shift:\n"
            "1. Augment public transport services: DMRC to induce additional metro train trips (minimum 40 extra daily trips) "
            "and DTC/DIMTS to deploy surplus CNG and Electric buses on heavy commuter routes.\n"
            "2. Impose differential parking charges (3x to 4x hike in surface parking rates) across all municipal commercial parking zones "
            "to actively discourage private motorized vehicular commuting.\n"
            "3. Intensify roadside emissions monitoring teams and issue immediate challans against visible smoking exhausts."
        )
    },

    # =========================================================================
    # GRAP STAGE III: "SEVERE" AIR QUALITY (AQI 401 - 450)
    # =========================================================================
    {
        "doc_id": "GRAP-STAGE-III-01",
        "title": "GRAP Stage III: Total Blanket Ban on Construction & Demolition (C&D) Activities",
        "category": "GRAP_STAGE_3",
        "section": "Stage III - Action 2 & 3",
        "legal_citation": "CAQM Direction No. 75, Schedule III (AQI 401-450)",
        "metadata_json": {
            "aqi_range": "401-450",
            "category": "Severe",
            "target_sectors": ["Construction", "Infrastructure", "Demolition"],
            "lead_agency": "DPCC / PWD / Police / Municipal Enforcement"
        },
        "content": (
            "GRAP Stage III ('Severe' Air Quality, AQI 401-450) - Blanket Construction Ban:\n"
            "1. Impose a complete and strict blanket ban on all Construction and Demolition (C&D) activities across the entire NCT of Delhi and NCR.\n"
            "2. Prohibited activities include: excavation, earthwork, boring, drilling, structural concrete casting, masonry, "
            "demolition, road surfacing, welding, gas cutting, tiling, painting, and movement of heavy earth-moving equipment.\n"
            "3. Specific permitted exemptions ONLY: Railway services/stations, Metro Rail corporations, Airports, Interstate Bus Terminals (ISBT), "
            "National security / defense related projects, and Hospitals / healthcare public facilities.\n"
            "4. Immediate closure and power severance for all stone crushing units, brick kilns, and mining/quarrying operations throughout NCR."
        )
    },
    {
        "doc_id": "GRAP-STAGE-III-02",
        "title": "GRAP Stage III: Vehicular Restrictions on BS-III Petrol and BS-IV Diesel LMVs",
        "category": "GRAP_STAGE_3",
        "section": "Stage III - Action 4 & 5",
        "legal_citation": "CAQM Direction No. 75, Schedule III r/w Section 115 Motor Vehicles Act",
        "metadata_json": {
            "aqi_range": "401-450",
            "category": "Severe",
            "target_sectors": ["Vehicular", "Private Transport"],
            "lead_agency": "Delhi Traffic Police / Transport Dept NCT Delhi"
        },
        "content": (
            "GRAP Stage III ('Severe' Air Quality, AQI 401-450) - Mandatory Vehicle Ban:\n"
            "1. Strictly prohibit the plying of BS-III Petrol and BS-IV Diesel 4-wheeler Light Motor Vehicles (LMVs) "
            "in the NCT of Delhi and the districts of Gurugram, Faridabad, Ghaziabad, and Gautam Buddha Nagar.\n"
            "2. Exemptions: Vehicles deployed for police, emergency healthcare/ambulances, and critical municipal enforcement duties.\n"
            "3. Penalty: Any BS-III Petrol or BS-IV Diesel vehicle found plying in violation of this directive shall be prosecuted "
            "under Section 194(1) of the Motor Vehicles Act, 1988 with an immediate compound fine of ₹20,000 and vehicle impounding."
        )
    },
    {
        "doc_id": "GRAP-STAGE-III-03",
        "title": "GRAP Stage III: School Discontinuation & Industrial Enforcement",
        "category": "GRAP_STAGE_3",
        "section": "Stage III - Action 6 & 7",
        "legal_citation": "CAQM Direction No. 75, Schedule III r/w Directorate of Education Order",
        "metadata_json": {
            "aqi_range": "401-450",
            "category": "Severe",
            "target_sectors": ["Education", "Industrial"],
            "lead_agency": "Directorate of Education / DPCC Industrial Cell"
        },
        "content": (
            "GRAP Stage III ('Severe' Air Quality, AQI 401-450) - Public Health & Industrial Restrictions:\n"
            "1. State Governments in NCR and GNCTD shall discontinue physical classes for children up to Class V "
            "and switch entirely to online / remote learning mode.\n"
            "2. Industrial units in NCR not operating on approved fuels (PNG / Biomass / Electricity) must immediately shut down operations. "
            "DPCC and DISCOMs shall disconnect industrial electricity supply for non-conforming industrial clusters.\n"
            "3. Intensive daily vacuum sweeping and continuous mist-sprinkling on all major thoroughfares and secondary transit loops."
        )
    },

    # =========================================================================
    # GRAP STAGE IV: "SEVERE+" AIR QUALITY (AQI > 450)
    # =========================================================================
    {
        "doc_id": "GRAP-STAGE-IV-01",
        "title": "GRAP Stage IV: Interstate Truck Entry Ban into Delhi",
        "category": "GRAP_STAGE_4",
        "section": "Stage IV - Action 1 & 2",
        "legal_citation": "CAQM Direction No. 75, Schedule IV (AQI > 450)",
        "metadata_json": {
            "aqi_range": ">450",
            "category": "Severe+",
            "target_sectors": ["Freight", "Border Checkpoints", "Heavy Commercial"],
            "lead_agency": "Delhi Police / Transport Dept / MCD Toll Operators"
        },
        "content": (
            "GRAP Stage IV ('Severe+' Air Quality, AQI > 450) - Emergency Commercial Truck Entry Ban:\n"
            "1. Stop entry of all non-Delhi registered commercial trucks into the NCT of Delhi.\n"
            "2. Permitted exemptions ONLY: Trucks powered by LNG/CNG/Electric drivetrains, and trucks carrying essential emergency commodities "
            "(fruits, vegetables, milk, dairy, medical supplies, petroleum products).\n"
            "3. Prohibit entry of all non-Delhi registered Light Commercial Vehicles (LCVs) carrying non-essential goods, "
            "except electric, CNG, or BS-VI diesel vehicles.\n"
            "4. Immediate physical diversion of non-destined transit trucks via Eastern and Western Peripheral Expressways."
        )
    },
    {
        "doc_id": "GRAP-STAGE-IV-02",
        "title": "GRAP Stage IV: Ban on Delhi-Registered Diesel MGVs/HGVs & Outstation Diesel LMVs",
        "category": "GRAP_STAGE_4",
        "section": "Stage IV - Action 3 & 4",
        "legal_citation": "CAQM Direction No. 75, Schedule IV (AQI > 450)",
        "metadata_json": {
            "aqi_range": ">450",
            "category": "Severe+",
            "target_sectors": ["Commercial Fleets", "Diesel Transport"],
            "lead_agency": "Delhi Traffic Police / Transport Enforcement"
        },
        "content": (
            "GRAP Stage IV ('Severe+' Air Quality, AQI > 450) - Diesel Fleet Prohibition:\n"
            "1. Impose a complete ban on the plying of Delhi-registered diesel Medium Goods Vehicles (MGVs) "
            "and Heavy Goods Vehicles (HGVs) in Delhi, except those transporting essential emergency supplies.\n"
            "2. Prohibit plying of 4-wheeler diesel LMVs registered outside Delhi (BS-IV and below) entering the NCT of Delhi, "
            "except for emergency and essential government services.\n"
            "3. Violators will face immediate vehicle seizure and statutory prosecution under Section 31A of the Air Act, 1981."
        )
    },
    {
        "doc_id": "GRAP-STAGE-IV-03",
        "title": "GRAP Stage IV: Public Work Ban, School Closures & 50% Work-From-Home",
        "category": "GRAP_STAGE_4",
        "section": "Stage IV - Action 5, 6, 7 & 8",
        "legal_citation": "CAQM Direction No. 75, Schedule IV r/w GNCTD Emergency Order",
        "metadata_json": {
            "aqi_range": ">450",
            "category": "Severe+",
            "target_sectors": ["Public Works", "Offices", "Higher Education"],
            "lead_agency": "General Administration Dept / Education Dept / DPCC"
        },
        "content": (
            "GRAP Stage IV ('Severe+' Air Quality, AQI > 450) - Emergency Social & Civil Mandates:\n"
            "1. Ban on all construction and demolition work for linear public projects (highways, roads, flyovers, overbridges, "
            "power transmission lines, pipelines), with zero exemptions.\n"
            "2. Discontinue in-person physical classes for Classes VI to IX and Class XI in all schools across NCT Delhi and NCR; "
            "conduct academic instruction exclusively online.\n"
            "3. Mandate 50% operational capacity in GNCTD, municipal, and central government offices with remaining 50% working from home (WFH).\n"
            "4. Strongly advise private corporate offices to operate with at least 50% staff on WFH rosters.\n"
            "5. State Governments may decide to introduce emergency road rationing schemes (Odd-Even) for private vehicular transit."
        )
    },

    # =========================================================================
    # CAQM STATUTORY DIRECTIONS
    # =========================================================================
    {
        "doc_id": "CAQM-DIR-71",
        "title": "CAQM Direction No. 71: C&D Portal Registration, Sensor Telemetry & Anti-Smog Guns",
        "category": "CAQM_DIRECTION",
        "section": "Direction No. 71",
        "legal_citation": "CAQM Direction No. 71 under Section 12 of the CAQM Act, 2021",
        "metadata_json": {
            "target_sectors": ["Construction", "IoT Monitoring"],
            "threshold": ">=500 sq meters",
            "lead_agency": "DPCC / State Pollution Control Boards"
        },
        "content": (
            "CAQM Direction No. 71 - Mandatory Environmental Safeguards for Construction & Demolition Sites:\n"
            "1. All project proponents of C&D activities on plot areas of 500 sq meters and above must register on the State Web Portal.\n"
            "2. Mandatory installation of low-cost PM2.5 and PM10 air quality sensor telemetry and PTZ high-definition CCTV cameras "
            "with uninterrupted live data streaming to the Central and State Pollution Control Board dashboards.\n"
            "3. Mandatory deployment of mobile and stationary Anti-Smog Guns: minimum 1 anti-smog gun for area up to 5,000 sq.m; "
            "2 guns for 5,000 to 10,000 sq.m; 3 guns for 10,000 to 15,000 sq.m; and 4 guns for 15,000 to 20,000 sq.m.\n"
            "4. Non-compliance results in immediate Stop Work Order and statutory Environmental Damage Compensation (EDC)."
        )
    },
    {
        "doc_id": "CAQM-DIR-73",
        "title": "CAQM Direction No. 73: Standard Fuel Policy for NCR Industrial Sectors",
        "category": "CAQM_DIRECTION",
        "section": "Direction No. 73",
        "legal_citation": "CAQM Direction No. 73 under Section 12 of the CAQM Act, 2021",
        "metadata_json": {
            "target_sectors": ["Industrial", "Boilers", "Manufacturing"],
            "lead_agency": "DPCC / Haryana SPCB / UPPCB"
        },
        "content": (
            "CAQM Direction No. 73 - Approved Clean Fuel Mandate for NCR Industries:\n"
            "1. Approved standard fuels across NCR: Piped Natural Gas (PNG), Liquefied Petroleum Gas (LPG), Biogas, Electricity, "
            "and approved Biomass pellets / briquettes.\n"
            "2. Total and absolute prohibition on heavily polluting fuels: Coal (including low-sulfur coal), Furnace Oil, Pet-Coke, "
            "and Tire Pyrolysis Oil in all industrial applications, furnaces, kilns, and boilers.\n"
            "3. Any industrial establishment found storing, combusting, or operating on non-approved fuels shall face immediate "
            "closure directives, sealing of premises, and criminal complaint under Section 14 of the CAQM Act, 2021."
        )
    },
    {
        "doc_id": "CAQM-DIR-75",
        "title": "CAQM Direction No. 75: Statutory Notification of Revised GRAP Schedule",
        "category": "CAQM_DIRECTION",
        "section": "Direction No. 75",
        "legal_citation": "CAQM Direction No. 75 under Section 12 of the CAQM Act, 2021",
        "metadata_json": {
            "target_sectors": ["All Sectors", "Inter-Agency"],
            "lead_agency": "CAQM Sub-Committee on GRAP"
        },
        "content": (
            "CAQM Direction No. 75 - Comprehensive Revised Graded Response Action Plan (GRAP) for NCR:\n"
            "1. GRAP measures are statutory, non-discretionary, and legally binding across Delhi, Haryana, Uttar Pradesh, and Rajasthan NCR districts.\n"
            "2. GRAP activates based on IMD / IITM dynamic air quality forecasts up to 3 days in advance, allowing preventive pre-emptive imposition.\n"
            "3. Stage I (AQI 201-300), Stage II (AQI 301-400), Stage III (AQI 401-450), Stage IV (AQI > 450).\n"
            "4. Sub-Committee on GRAP convenes emergency daily reviews during Stage III and IV episodes to review meteorological trajectories."
        )
    },

    # =========================================================================
    # THE AIR (PREVENTION AND CONTROL OF POLLUTION) ACT, 1981
    # =========================================================================
    {
        "doc_id": "AIR-ACT-SEC-19",
        "title": "Air Act, 1981: Section 19 - Declaration of Air Pollution Control Areas",
        "category": "AIR_ACT_1981",
        "section": "Section 19(1) & 19(5)",
        "legal_citation": "Section 19, The Air (Prevention and Control of Pollution) Act, 1981",
        "metadata_json": {
            "act": "Air Act 1981",
            "section": "19",
            "jurisdiction": "State Government / DPCC"
        },
        "content": (
            "The Air (Prevention and Control of Pollution) Act, 1981 - Section 19:\n"
            "1. Section 19(1): The State Government may, after consultation with the State Board, by notification in the Official Gazette, "
            "declare in such manner as may be prescribed, any area or areas within the State as air pollution control area or areas.\n"
            "2. Section 19(5): If the State Government, after consultation with the State Board, is of opinion that the burning of any material "
            "(not being fuel) in any air pollution control area or part thereof may cause or is likely to cause air pollution, it may, "
            "by notification, prohibit the burning of such material in such area or part thereof.\n"
            "3. The entirety of the National Capital Territory of Delhi is notified as an Air Pollution Control Area."
        )
    },
    {
        "doc_id": "AIR-ACT-SEC-21",
        "title": "Air Act, 1981: Section 21 - Restrictions on Use of Industrial Plants (Consent to Operate)",
        "category": "AIR_ACT_1981",
        "section": "Section 21",
        "legal_citation": "Section 21, The Air (Prevention and Control of Pollution) Act, 1981",
        "metadata_json": {
            "act": "Air Act 1981",
            "section": "21",
            "jurisdiction": "Industrial Facilities / DPCC"
        },
        "content": (
            "The Air (Prevention and Control of Pollution) Act, 1981 - Section 21:\n"
            "1. No person shall, without the previous consent of the State Board (DPCC), establish or operate any industrial plant "
            "in an air pollution control area.\n"
            "2. Every person operating any industrial plant in an air pollution control area must obtain Consent to Establish (CTE) "
            "and Consent to Operate (CTO) specifying prescribed chimney height, particulate control equipment, and emission ceilings.\n"
            "3. Operating without valid CTO or in breach of emission conditions constitutes a cognizable offense."
        )
    },
    {
        "doc_id": "AIR-ACT-SEC-31A",
        "title": "Air Act, 1981: Section 31A - Statutory Power to Give Directions",
        "category": "AIR_ACT_1981",
        "section": "Section 31A",
        "legal_citation": "Section 31A, The Air (Prevention and Control of Pollution) Act, 1981",
        "metadata_json": {
            "act": "Air Act 1981",
            "section": "31A",
            "jurisdiction": "Enforcement Powers / State Board"
        },
        "content": (
            "The Air (Prevention and Control of Pollution) Act, 1981 - Section 31A (Power to Give Directions):\n"
            "Notwithstanding anything contained in any other law, but subject to the provisions of this Act, and to any directions that the Central Government "
            "may give in this behalf, the State Board (DPCC) may, in the exercise of its powers and performance of its functions under this Act, "
            "issue any directions in writing to any person, officer or authority, and such person, officer or authority shall be bound to comply with such directions.\n"
            "Explanation: For the avoidance of doubts, it is hereby declared that the power to issue directions under this section includes the power to direct:\n"
            "(a) the closure, prohibition or regulation of any industry, operation or process; or\n"
            "(b) the stoppage or regulation of supply of electricity, water or any other service."
        )
    },
    {
        "doc_id": "AIR-ACT-SEC-37",
        "title": "Air Act, 1981: Section 37 - Penalties for Failure to Comply with Section 31A Directions",
        "category": "AIR_ACT_1981",
        "section": "Section 37",
        "legal_citation": "Section 37, The Air (Prevention and Control of Pollution) Act, 1981",
        "metadata_json": {
            "act": "Air Act 1981",
            "section": "37",
            "jurisdiction": "Criminal Penalties / Prosecutions"
        },
        "content": (
            "The Air (Prevention and Control of Pollution) Act, 1981 - Section 37 (Penalties):\n"
            "1. Whoever fails to comply with the provisions of section 21 or section 22 or directions issued under section 31A shall, "
            "in respect of each such failure, be punishable with imprisonment for a term which shall not be less than one year and six months "
            "but which may extend to six years and with fine, and in case the failure continues, with an additional fine which may extend to "
            "five thousand rupees for every day during which such failure continues after the conviction for the first such failure.\n"
            "2. If the failure continues beyond a period of one year after the date of conviction, the offender shall be punishable with "
            "imprisonment for a term which shall not be less than two years but which may extend to seven years and with fine."
        )
    },
    {
        "doc_id": "AIR-ACT-SEC-38-39",
        "title": "Air Act, 1981: Section 38 & 39 - Penalties for Obstruction and Corporate Liability",
        "category": "AIR_ACT_1981",
        "section": "Section 38 & 39",
        "legal_citation": "Section 38 & 39, The Air (Prevention and Control of Pollution) Act, 1981",
        "metadata_json": {
            "act": "Air Act 1981",
            "section": "38, 39",
            "jurisdiction": "Corporate Enforcement"
        },
        "content": (
            "The Air (Prevention and Control of Pollution) Act, 1981 - Section 38 & 39:\n"
            "1. Section 38: Penalties for acts like obstructing any person acting under the direction of the Board, damaging notices or monitoring equipment, "
            "or giving false information — punishable with imprisonment up to three months or with fine up to ten thousand rupees, or both.\n"
            "2. Section 39: General penalty for contravention of any provision of the Act — punishable with imprisonment up to three months or fine up to ₹10,000, "
            "with progressive daily fines up to ₹5,000.\n"
            "3. Section 40: Offenses by Companies — every person who, at the time the offense was committed, was in charge of, and was responsible to the company "
            "for the conduct of business of the company, shall be deemed to be guilty of the offense and proceeded against."
        )
    }
]

