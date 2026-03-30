#!/usr/bin/env python3
"""
Generate a curated seed dataset of ~500 popular car models for Grille.

This script contains an embedded list of notable/popular automobile models
curated from common automotive knowledge. It serves as:

1. A fallback when the Wikidata API (fetch-cars.py) is unavailable
2. A seed list that can be enriched with fetch-cars.py's API data
3. A quick way to bootstrap the game's car database

Usage:
    python scripts/seed-cars.py               # Generate all ~500 cars
    python scripts/seed-cars.py --limit 100   # Generate top 100 only
    python scripts/seed-cars.py --stats        # Show stats only

Output:
    data/cars-wikidata.json
"""

import argparse
import json
import re
from pathlib import Path

# Curated car data: (make, model, year, country, hp, weight_kg, engine, drivetrain)
# Ordered roughly by cultural significance / popularity / notability
# Sources: common automotive knowledge, Wikipedia
CARS = [
    # === Iconic Sports & Supercars ===
    ("Ford", "Model T", 1908, "USA", 20, 540, "I4", "RWD"),
    ("Ford", "Mustang (1st Gen)", 1964, "USA", 271, 1297, "V8", "RWD"),
    ("Chevrolet", "Corvette (C1)", 1953, "USA", 150, 1295, "I6", "RWD"),
    ("Chevrolet", "Corvette (C2)", 1963, "USA", 360, 1399, "V8", "RWD"),
    ("Chevrolet", "Corvette (C3)", 1968, "USA", 390, 1496, "V8", "RWD"),
    ("Chevrolet", "Corvette (C4)", 1984, "USA", 205, 1441, "V8", "RWD"),
    ("Chevrolet", "Corvette (C5)", 1997, "USA", 345, 1475, "V8", "RWD"),
    ("Chevrolet", "Corvette (C6)", 2005, "USA", 400, 1440, "V8", "RWD"),
    ("Chevrolet", "Corvette (C7)", 2014, "USA", 455, 1496, "V8", "RWD"),
    ("Chevrolet", "Corvette (C8)", 2020, "USA", 495, 1527, "V8", "RWD"),
    ("Chevrolet", "Camaro (1st Gen)", 1967, "USA", 295, 1497, "V8", "RWD"),
    ("Chevrolet", "Camaro SS (3rd Gen)", 1982, "USA", 165, 1474, "V8", "RWD"),
    ("Chevrolet", "Camaro Z28 (4th Gen)", 1993, "USA", 275, 1499, "V8", "RWD"),
    ("Chevrolet", "Camaro ZL1 (5th Gen)", 2012, "USA", 580, 1839, "V8 Supercharged", "RWD"),
    ("Chevrolet", "Impala (3rd Gen)", 1965, "USA", 250, 1684, "V8", "RWD"),
    ("Chevrolet", "Chevelle SS 396", 1966, "USA", 375, 1542, "V8", "RWD"),
    ("Chevrolet", "Bel Air", 1957, "USA", 283, 1549, "V8", "RWD"),
    ("Ford", "GT40", 1964, "USA", 485, 910, "V8", "RWD"),
    ("Ford", "GT (2005)", 2005, "USA", 550, 1583, "V8 Supercharged", "RWD"),
    ("Ford", "GT (2017)", 2017, "USA", 647, 1385, "V6 Twin Turbo", "RWD"),
    ("Ford", "Mustang GT (S197)", 2005, "USA", 300, 1549, "V8", "RWD"),
    ("Ford", "Mustang Shelby GT500 (S197)", 2007, "USA", 500, 1733, "V8 Supercharged", "RWD"),
    ("Ford", "Mustang (S550)", 2015, "USA", 435, 1678, "V8", "RWD"),
    ("Ford", "Thunderbird (1st Gen)", 1955, "USA", 198, 1479, "V8", "RWD"),
    ("Ford", "F-150 Raptor", 2010, "USA", 411, 2608, "V8", "4WD"),
    ("Ford", "Bronco (1st Gen)", 1966, "USA", 105, 1451, "I6", "4WD"),
    ("Ford", "Escort RS Cosworth", 1992, "UK", 227, 1275, "I4 Turbo", "4WD"),
    ("Ford", "Sierra RS Cosworth", 1986, "UK", 204, 1220, "I4 Turbo", "RWD"),
    ("Ford", "Focus RS (Mk2)", 2009, "Germany", 305, 1467, "I5 Turbo", "FWD"),
    ("Ford", "Focus RS (Mk3)", 2016, "Germany", 350, 1572, "I4 Turbo", "AWD"),
    ("Dodge", "Charger R/T", 1968, "USA", 375, 1724, "V8", "RWD"),
    ("Dodge", "Challenger R/T", 1970, "USA", 335, 1644, "V8", "RWD"),
    ("Dodge", "Viper (RT/10)", 1992, "USA", 400, 1527, "V10", "RWD"),
    ("Dodge", "Viper GTS", 1996, "USA", 450, 1564, "V10", "RWD"),
    ("Dodge", "Viper SRT-10 ACR", 2008, "USA", 600, 1538, "V10", "RWD"),
    ("Dodge", "Challenger SRT Hellcat", 2015, "USA", 707, 2013, "V8 Supercharged", "RWD"),
    ("Dodge", "Challenger SRT Demon", 2018, "USA", 840, 1894, "V8 Supercharged", "RWD"),
    ("Plymouth", "Barracuda (3rd Gen)", 1970, "USA", 335, 1593, "V8", "RWD"),
    ("Pontiac", "GTO (1964)", 1964, "USA", 348, 1538, "V8", "RWD"),
    ("Pontiac", "Firebird Trans Am (2nd Gen)", 1970, "USA", 345, 1630, "V8", "RWD"),
    ("Pontiac", "Firebird Trans Am (3rd Gen)", 1982, "USA", 165, 1506, "V8", "RWD"),
    ("Toyota", "Supra (A80)", 1993, "Japan", 320, 1560, "I6 Twin Turbo", "RWD"),
    ("Toyota", "Supra (A70)", 1986, "Japan", 230, 1574, "I6 Turbo", "RWD"),
    ("Toyota", "Supra (A90)", 2019, "Japan", 335, 1541, "I6 Turbo", "RWD"),
    ("Toyota", "2000GT", 1967, "Japan", 150, 1120, "I6", "RWD"),
    ("Toyota", "AE86 Sprinter Trueno", 1983, "Japan", 128, 940, "I4", "RWD"),
    ("Toyota", "MR2 (AW11)", 1984, "Japan", 112, 1060, "I4", "RWD"),
    ("Toyota", "MR2 Turbo (SW20)", 1989, "Japan", 200, 1260, "I4 Turbo", "RWD"),
    ("Toyota", "Celica GT-Four (ST205)", 1994, "Japan", 255, 1390, "I4 Turbo", "AWD"),
    ("Toyota", "Land Cruiser (J40)", 1960, "Japan", 125, 1565, "I6", "4WD"),
    ("Toyota", "Land Cruiser (J80)", 1990, "Japan", 212, 2210, "I6", "4WD"),
    ("Toyota", "Corolla (E110)", 1995, "Japan", 120, 1100, "I4", "FWD"),
    ("Toyota", "Camry (XV20)", 1996, "Japan", 133, 1360, "I4", "FWD"),
    ("Toyota", "Hilux (7th Gen)", 2004, "Japan", 171, 1865, "I4 Turbo Diesel", "4WD"),
    ("Toyota", "GR Yaris", 2020, "Japan", 261, 1280, "I3 Turbo", "AWD"),
    ("Nissan", "Skyline GT-R (R34)", 1999, "Japan", 280, 1560, "I6 Twin Turbo", "AWD"),
    ("Nissan", "Skyline GT-R (R33)", 1995, "Japan", 280, 1540, "I6 Twin Turbo", "AWD"),
    ("Nissan", "Skyline GT-R (R32)", 1989, "Japan", 280, 1430, "I6 Twin Turbo", "AWD"),
    ("Nissan", "GT-R (R35)", 2007, "Japan", 480, 1740, "V6 Twin Turbo", "AWD"),
    ("Nissan", "Silvia (S15)", 1999, "Japan", 250, 1240, "I4 Turbo", "RWD"),
    ("Nissan", "Silvia (S13)", 1988, "Japan", 205, 1190, "I4 Turbo", "RWD"),
    ("Nissan", "240SX (S14)", 1993, "Japan", 155, 1230, "I4", "RWD"),
    ("Nissan", "350Z", 2002, "Japan", 287, 1474, "V6", "RWD"),
    ("Nissan", "370Z", 2009, "Japan", 332, 1496, "V6", "RWD"),
    ("Nissan", "Fairlady Z (S30)", 1969, "Japan", 151, 1041, "I6", "RWD"),
    ("Nissan", "300ZX (Z32)", 1989, "Japan", 300, 1539, "V6 Twin Turbo", "RWD"),
    ("Nissan", "Patrol (Y60)", 1987, "Japan", 145, 2100, "I6", "4WD"),
    ("Honda", "NSX (NA1)", 1990, "Japan", 270, 1370, "V6", "RWD"),
    ("Honda", "NSX (NC1)", 2016, "Japan", 573, 1725, "V6 Twin Turbo Hybrid", "AWD"),
    ("Honda", "S2000 (AP1)", 1999, "Japan", 240, 1260, "I4", "RWD"),
    ("Honda", "Civic Type R (EK9)", 1997, "Japan", 185, 1050, "I4", "FWD"),
    ("Honda", "Civic Type R (FD2)", 2007, "Japan", 225, 1270, "I4", "FWD"),
    ("Honda", "Civic Type R (FK8)", 2017, "Japan", 306, 1380, "I4 Turbo", "FWD"),
    ("Honda", "Integra Type R (DC2)", 1995, "Japan", 200, 1080, "I4", "FWD"),
    ("Honda", "Prelude (5th Gen)", 1996, "Japan", 200, 1310, "I4", "FWD"),
    ("Honda", "Beat", 1991, "Japan", 64, 760, "I3", "RWD"),
    ("Honda", "CR-X (EF8)", 1987, "Japan", 150, 910, "I4", "FWD"),
    ("Mazda", "RX-7 (FD)", 1992, "Japan", 255, 1260, "Rotary Twin Turbo", "RWD"),
    ("Mazda", "RX-7 (FC)", 1985, "Japan", 185, 1250, "Rotary Turbo", "RWD"),
    ("Mazda", "RX-7 (SA/FB)", 1978, "Japan", 100, 1025, "Rotary", "RWD"),
    ("Mazda", "RX-8", 2003, "Japan", 232, 1310, "Rotary", "RWD"),
    ("Mazda", "MX-5 (NA)", 1989, "Japan", 116, 955, "I4", "RWD"),
    ("Mazda", "MX-5 (NB)", 1998, "Japan", 140, 1065, "I4", "RWD"),
    ("Mazda", "MX-5 (NC)", 2005, "Japan", 170, 1098, "I4", "RWD"),
    ("Mazda", "MX-5 (ND)", 2015, "Japan", 155, 1058, "I4", "RWD"),
    ("Mazda", "Cosmo Sport", 1967, "Japan", 110, 940, "Rotary", "RWD"),
    ("Mazda", "3 MPS / Mazdaspeed3", 2007, "Japan", 263, 1385, "I4 Turbo", "FWD"),
    ("Subaru", "Impreza WRX STI (GC8)", 1994, "Japan", 280, 1260, "Flat-4 Turbo", "AWD"),
    ("Subaru", "Impreza WRX STI (GDB)", 2001, "Japan", 280, 1390, "Flat-4 Turbo", "AWD"),
    ("Subaru", "WRX STI (VAB)", 2014, "Japan", 305, 1490, "Flat-4 Turbo", "AWD"),
    ("Subaru", "BRZ", 2012, "Japan", 200, 1230, "Flat-4", "RWD"),
    ("Subaru", "Legacy RS", 1989, "Japan", 220, 1340, "Flat-4 Turbo", "AWD"),
    ("Mitsubishi", "Lancer Evolution VI", 1999, "Japan", 280, 1360, "I4 Turbo", "AWD"),
    ("Mitsubishi", "Lancer Evolution IX", 2005, "Japan", 286, 1410, "I4 Turbo", "AWD"),
    ("Mitsubishi", "Lancer Evolution X", 2007, "Japan", 295, 1560, "I4 Turbo", "AWD"),
    ("Mitsubishi", "3000GT VR-4", 1990, "Japan", 300, 1710, "V6 Twin Turbo", "AWD"),
    ("Mitsubishi", "Eclipse GSX", 1990, "Japan", 195, 1391, "I4 Turbo", "AWD"),
    ("Mitsubishi", "Pajero Evolution", 1997, "Japan", 280, 1920, "V6", "4WD"),
    ("Suzuki", "Cappuccino", 1991, "Japan", 64, 700, "I3 Turbo", "RWD"),
    ("Suzuki", "Swift Sport (ZC31S)", 2005, "Japan", 125, 1060, "I4", "FWD"),
    ("Suzuki", "Jimny (JB74)", 2018, "Japan", 102, 1090, "I4", "4WD"),
    ("Daihatsu", "Copen", 2002, "Japan", 64, 830, "I4 Turbo", "FWD"),
    # === German ===
    ("Porsche", "911 Carrera (993)", 1995, "Germany", 272, 1370, "Flat-6", "RWD"),
    ("Porsche", "911 Carrera (996)", 1998, "Germany", 300, 1320, "Flat-6", "RWD"),
    ("Porsche", "911 Carrera (997)", 2004, "Germany", 325, 1395, "Flat-6", "RWD"),
    ("Porsche", "911 Turbo (930)", 1975, "Germany", 260, 1195, "Flat-6 Turbo", "RWD"),
    ("Porsche", "911 Turbo (964)", 1990, "Germany", 320, 1470, "Flat-6 Turbo", "AWD"),
    ("Porsche", "911 GT3 (996)", 1999, "Germany", 360, 1350, "Flat-6", "RWD"),
    ("Porsche", "911 GT3 RS (997)", 2006, "Germany", 415, 1375, "Flat-6", "RWD"),
    ("Porsche", "911 (991)", 2011, "Germany", 350, 1380, "Flat-6", "RWD"),
    ("Porsche", "911 (992)", 2019, "Germany", 385, 1505, "Flat-6 Twin Turbo", "RWD"),
    ("Porsche", "918 Spyder", 2013, "Germany", 887, 1674, "V8 Hybrid", "AWD"),
    ("Porsche", "Carrera GT", 2004, "Germany", 612, 1380, "V10", "RWD"),
    ("Porsche", "959", 1986, "Germany", 450, 1450, "Flat-6 Twin Turbo", "AWD"),
    ("Porsche", "356", 1948, "Germany", 60, 830, "Flat-4", "RWD"),
    ("Porsche", "550 Spyder", 1953, "Germany", 110, 550, "Flat-4", "RWD"),
    ("Porsche", "944 Turbo", 1985, "Germany", 220, 1280, "I4 Turbo", "RWD"),
    ("Porsche", "968", 1992, "Germany", 240, 1370, "I4", "RWD"),
    ("Porsche", "Boxster (986)", 1996, "Germany", 201, 1250, "Flat-6", "RWD"),
    ("Porsche", "Cayman S (987)", 2005, "Germany", 295, 1340, "Flat-6", "RWD"),
    ("Porsche", "Cayenne Turbo (9PA)", 2002, "Germany", 450, 2355, "V8 Twin Turbo", "AWD"),
    ("Porsche", "Panamera Turbo", 2009, "Germany", 500, 1970, "V8 Twin Turbo", "AWD"),
    ("Porsche", "Taycan Turbo S", 2020, "Germany", 750, 2295, "Electric", "AWD"),
    ("BMW", "M3 (E30)", 1986, "Germany", 200, 1200, "I4", "RWD"),
    ("BMW", "M3 (E36)", 1992, "Germany", 286, 1460, "I6", "RWD"),
    ("BMW", "M3 (E46)", 2000, "Germany", 343, 1495, "I6", "RWD"),
    ("BMW", "M3 (E90)", 2007, "Germany", 414, 1605, "V8", "RWD"),
    ("BMW", "M3 (F80)", 2014, "Germany", 425, 1520, "I6 Twin Turbo", "RWD"),
    ("BMW", "M5 (E28)", 1985, "Germany", 286, 1431, "I6", "RWD"),
    ("BMW", "M5 (E34)", 1988, "Germany", 315, 1670, "I6", "RWD"),
    ("BMW", "M5 (E39)", 1998, "Germany", 394, 1795, "V8", "RWD"),
    ("BMW", "M5 (E60)", 2005, "Germany", 507, 1830, "V10", "RWD"),
    ("BMW", "M5 (F10)", 2011, "Germany", 560, 1870, "V8 Twin Turbo", "RWD"),
    ("BMW", "E30 325i", 1985, "Germany", 171, 1220, "I6", "RWD"),
    ("BMW", "Z3 M Coupe", 1998, "Germany", 321, 1400, "I6", "RWD"),
    ("BMW", "Z4 M (E85)", 2006, "Germany", 343, 1425, "I6", "RWD"),
    ("BMW", "Z8", 2000, "Germany", 394, 1585, "V8", "RWD"),
    ("BMW", "i8", 2014, "Germany", 369, 1485, "I3 Turbo Hybrid", "AWD"),
    ("BMW", "2002 Turbo", 1973, "Germany", 170, 1080, "I4 Turbo", "RWD"),
    ("BMW", "M1", 1978, "Germany", 277, 1300, "I6", "RWD"),
    ("BMW", "1M Coupe", 2011, "Germany", 340, 1495, "I6 Twin Turbo", "RWD"),
    ("BMW", "M2 (F87)", 2016, "Germany", 365, 1495, "I6 Twin Turbo", "RWD"),
    ("Mercedes-Benz", "300SL Gullwing", 1954, "Germany", 215, 1295, "I6", "RWD"),
    ("Mercedes-Benz", "190E 2.5-16 Evo II", 1990, "Germany", 235, 1340, "I4", "RWD"),
    ("Mercedes-Benz", "SL500 (R129)", 1989, "Germany", 326, 1810, "V8", "RWD"),
    ("Mercedes-Benz", "CLK GTR", 1998, "Germany", 612, 1440, "V12", "RWD"),
    ("Mercedes-Benz", "SLS AMG", 2010, "Germany", 563, 1620, "V8", "RWD"),
    ("Mercedes-Benz", "AMG GT R", 2017, "Germany", 577, 1555, "V8 Twin Turbo", "RWD"),
    ("Mercedes-Benz", "C63 AMG (W204)", 2008, "Germany", 451, 1655, "V8", "RWD"),
    ("Mercedes-Benz", "E63 AMG (W212)", 2009, "Germany", 518, 1825, "V8 Twin Turbo", "RWD"),
    ("Mercedes-Benz", "S-Class (W140)", 1991, "Germany", 394, 2070, "V8", "RWD"),
    ("Mercedes-Benz", "G-Wagen (W463)", 1990, "Germany", 241, 2380, "V8", "4WD"),
    ("Mercedes-Benz", "SLR McLaren", 2003, "Germany", 617, 1768, "V8 Supercharged", "RWD"),
    ("Mercedes-Benz", "AMG ONE", 2022, "Germany", 1063, 1695, "V6 Turbo Hybrid", "AWD"),
    ("Mercedes-Benz", "W124 500E", 1991, "Germany", 326, 1690, "V8", "RWD"),
    ("Mercedes-Benz", "CLK 55 AMG", 1999, "Germany", 342, 1590, "V8", "RWD"),
    ("Audi", "Quattro", 1980, "Germany", 200, 1290, "I5 Turbo", "AWD"),
    ("Audi", "RS4 (B5)", 2000, "Germany", 380, 1620, "V6 Twin Turbo", "AWD"),
    ("Audi", "RS6 (C5)", 2002, "Germany", 450, 1840, "V8 Twin Turbo", "AWD"),
    ("Audi", "R8 V10", 2009, "Germany", 525, 1620, "V10", "AWD"),
    ("Audi", "TT (8N)", 1998, "Germany", 225, 1395, "I4 Turbo", "AWD"),
    ("Audi", "S4 (B5)", 1997, "Germany", 265, 1595, "V6 Twin Turbo", "AWD"),
    ("Audi", "Sport Quattro", 1984, "Germany", 306, 1300, "I5 Turbo", "AWD"),
    ("Audi", "RS3 (8V)", 2015, "Germany", 367, 1520, "I5 Turbo", "AWD"),
    ("Audi", "e-tron GT RS", 2021, "Germany", 637, 2347, "Electric", "AWD"),
    ("Volkswagen", "Golf GTI (Mk1)", 1976, "Germany", 110, 810, "I4", "FWD"),
    ("Volkswagen", "Golf GTI (Mk2)", 1984, "Germany", 139, 960, "I4", "FWD"),
    ("Volkswagen", "Golf GTI (Mk5)", 2004, "Germany", 200, 1318, "I4 Turbo", "FWD"),
    ("Volkswagen", "Golf R (Mk7)", 2014, "Germany", 296, 1476, "I4 Turbo", "AWD"),
    ("Volkswagen", "Corrado VR6", 1991, "Germany", 190, 1243, "VR6", "FWD"),
    ("Volkswagen", "Beetle (Classic)", 1938, "Germany", 25, 750, "Flat-4", "RWD"),
    ("Volkswagen", "Scirocco R", 2009, "Germany", 265, 1373, "I4 Turbo", "FWD"),
    ("Volkswagen", "Golf GTI (Mk7)", 2013, "Germany", 220, 1351, "I4 Turbo", "FWD"),
    ("Volkswagen", "Polo GTI (6R)", 2010, "Germany", 180, 1184, "I4 Turbo", "FWD"),
    ("Opel", "Manta A GT/E", 1974, "Germany", 105, 960, "I4", "RWD"),
    ("Opel", "Speedster", 2000, "Germany", 147, 870, "I4", "RWD"),
    # === Italian ===
    ("Ferrari", "Testarossa", 1984, "Italy", 390, 1506, "Flat-12", "RWD"),
    ("Ferrari", "F40", 1987, "Italy", 478, 1100, "V8 Twin Turbo", "RWD"),
    ("Ferrari", "F50", 1995, "Italy", 520, 1230, "V12", "RWD"),
    ("Ferrari", "Enzo", 2002, "Italy", 651, 1365, "V12", "RWD"),
    ("Ferrari", "LaFerrari", 2013, "Italy", 950, 1255, "V12 Hybrid", "RWD"),
    ("Ferrari", "288 GTO", 1984, "Italy", 400, 1160, "V8 Twin Turbo", "RWD"),
    ("Ferrari", "250 GTO", 1962, "Italy", 300, 880, "V12", "RWD"),
    ("Ferrari", "308 GTB", 1975, "Italy", 255, 1090, "V8", "RWD"),
    ("Ferrari", "328 GTS", 1985, "Italy", 270, 1263, "V8", "RWD"),
    ("Ferrari", "348", 1989, "Italy", 300, 1393, "V8", "RWD"),
    ("Ferrari", "355", 1994, "Italy", 380, 1350, "V8", "RWD"),
    ("Ferrari", "360 Modena", 1999, "Italy", 400, 1390, "V8", "RWD"),
    ("Ferrari", "430 Scuderia", 2007, "Italy", 503, 1250, "V8", "RWD"),
    ("Ferrari", "458 Italia", 2009, "Italy", 570, 1380, "V8", "RWD"),
    ("Ferrari", "488 GTB", 2015, "Italy", 661, 1370, "V8 Twin Turbo", "RWD"),
    ("Ferrari", "SF90 Stradale", 2019, "Italy", 986, 1570, "V8 Turbo Hybrid", "AWD"),
    ("Ferrari", "812 Superfast", 2017, "Italy", 789, 1525, "V12", "RWD"),
    ("Ferrari", "F12berlinetta", 2012, "Italy", 730, 1525, "V12", "RWD"),
    ("Ferrari", "599 GTO", 2010, "Italy", 670, 1495, "V12", "RWD"),
    ("Ferrari", "Dino 246 GT", 1969, "Italy", 195, 1080, "V6", "RWD"),
    ("Ferrari", "275 GTB", 1964, "Italy", 280, 1200, "V12", "RWD"),
    ("Lamborghini", "Countach (LP500S)", 1982, "Italy", 375, 1490, "V12", "RWD"),
    ("Lamborghini", "Diablo", 1990, "Italy", 485, 1576, "V12", "RWD"),
    ("Lamborghini", "Murcielago", 2001, "Italy", 572, 1650, "V12", "AWD"),
    ("Lamborghini", "Gallardo", 2003, "Italy", 493, 1430, "V10", "AWD"),
    ("Lamborghini", "Aventador LP700-4", 2011, "Italy", 700, 1575, "V12", "AWD"),
    ("Lamborghini", "Huracan Performante", 2017, "Italy", 631, 1382, "V10", "AWD"),
    ("Lamborghini", "Miura P400", 1966, "Italy", 350, 1125, "V12", "RWD"),
    ("Lamborghini", "Sesto Elemento", 2010, "Italy", 570, 999, "V10", "AWD"),
    ("Lamborghini", "Urus", 2018, "Italy", 641, 2200, "V8 Twin Turbo", "AWD"),
    ("Lamborghini", "Revuelto", 2023, "Italy", 1001, 1772, "V12 Hybrid", "AWD"),
    ("Lamborghini", "Diablo SV", 1995, "Italy", 510, 1530, "V12", "RWD"),
    ("Lamborghini", "Huracan STO", 2021, "Italy", 631, 1339, "V10", "RWD"),
    ("Maserati", "MC12", 2004, "Italy", 630, 1335, "V12", "RWD"),
    ("Maserati", "GranTurismo", 2007, "Italy", 405, 1780, "V8", "RWD"),
    ("Maserati", "Ghibli (Tipo AM115)", 1967, "Italy", 330, 1400, "V8", "RWD"),
    ("Maserati", "3200 GT", 1998, "Italy", 370, 1565, "V8 Twin Turbo", "RWD"),
    ("Alfa Romeo", "Giulia GTA", 1965, "Italy", 170, 790, "I4", "RWD"),
    ("Alfa Romeo", "8C Competizione", 2007, "Italy", 450, 1585, "V8", "RWD"),
    ("Alfa Romeo", "4C", 2013, "Italy", 237, 895, "I4 Turbo", "RWD"),
    ("Alfa Romeo", "33 Stradale", 1967, "Italy", 230, 700, "V8", "RWD"),
    ("Alfa Romeo", "GTV6", 1980, "Italy", 160, 1160, "V6", "RWD"),
    ("Alfa Romeo", "Spider (Series 4)", 1990, "Italy", 120, 1130, "I4", "RWD"),
    ("Alfa Romeo", "Giulia Quadrifoglio", 2016, "Italy", 505, 1524, "V6 Twin Turbo", "RWD"),
    ("Alfa Romeo", "156 GTA", 2002, "Italy", 250, 1410, "V6", "FWD"),
    ("Fiat", "500 Abarth", 2008, "Italy", 135, 1035, "I4 Turbo", "FWD"),
    ("Fiat", "124 Spider Abarth", 1972, "Italy", 128, 960, "I4", "RWD"),
    ("Fiat", "X1/9", 1972, "Italy", 75, 907, "I4", "RWD"),
    ("Lancia", "Delta Integrale HF", 1987, "Italy", 210, 1300, "I4 Turbo", "AWD"),
    ("Lancia", "Stratos HF", 1973, "Italy", 190, 980, "V6", "RWD"),
    ("Lancia", "037", 1982, "Italy", 205, 980, "I4 Supercharged", "RWD"),
    ("De Tomaso", "Pantera", 1971, "Italy", 330, 1416, "V8", "RWD"),
    ("Pagani", "Zonda C12", 1999, "Italy", 550, 1250, "V12", "RWD"),
    ("Pagani", "Huayra", 2012, "Italy", 730, 1350, "V12 Twin Turbo", "RWD"),
    # === British ===
    ("Lotus", "Elise (Series 1)", 1996, "UK", 118, 725, "I4", "RWD"),
    ("Lotus", "Exige S", 2006, "UK", 218, 875, "I4 Supercharged", "RWD"),
    ("Lotus", "Esprit V8", 1996, "UK", 350, 1300, "V8 Twin Turbo", "RWD"),
    ("Lotus", "Esprit Turbo", 1980, "UK", 210, 1195, "I4 Turbo", "RWD"),
    ("Lotus", "Elan (M100)", 1989, "UK", 165, 1020, "I4 Turbo", "FWD"),
    ("Lotus", "Europa", 1966, "UK", 82, 610, "I4", "RWD"),
    ("Lotus", "Seven", 1957, "UK", 40, 420, "I4", "RWD"),
    ("Lotus", "Emira", 2022, "UK", 400, 1405, "V6 Supercharged", "RWD"),
    ("Lotus", "Evija", 2024, "UK", 1972, 1680, "Electric", "AWD"),
    ("Jaguar", "E-Type", 1961, "UK", 265, 1315, "I6", "RWD"),
    ("Jaguar", "XJ220", 1992, "UK", 542, 1470, "V6 Twin Turbo", "RWD"),
    ("Jaguar", "XKR (X100)", 1998, "UK", 370, 1710, "V8 Supercharged", "RWD"),
    ("Jaguar", "F-Type R", 2013, "UK", 550, 1665, "V8 Supercharged", "RWD"),
    ("Jaguar", "XJ13", 1966, "UK", 502, 908, "V12", "RWD"),
    ("Jaguar", "XK120", 1948, "UK", 160, 1315, "I6", "RWD"),
    ("Aston Martin", "DB5", 1963, "UK", 282, 1502, "I6", "RWD"),
    ("Aston Martin", "DB9", 2004, "UK", 450, 1760, "V12", "RWD"),
    ("Aston Martin", "V8 Vantage (2005)", 2005, "UK", 380, 1570, "V8", "RWD"),
    ("Aston Martin", "DBS Superleggera", 2018, "UK", 715, 1693, "V12 Twin Turbo", "RWD"),
    ("Aston Martin", "Vanquish", 2001, "UK", 460, 1835, "V12", "RWD"),
    ("Aston Martin", "Valkyrie", 2021, "UK", 1160, 1030, "V12 Hybrid", "RWD"),
    ("Aston Martin", "One-77", 2009, "UK", 750, 1630, "V12", "RWD"),
    ("Aston Martin", "DB11", 2016, "UK", 600, 1770, "V12 Twin Turbo", "RWD"),
    ("McLaren", "F1", 1992, "UK", 627, 1138, "V12", "RWD"),
    ("McLaren", "P1", 2013, "UK", 903, 1395, "V8 Twin Turbo Hybrid", "RWD"),
    ("McLaren", "720S", 2017, "UK", 710, 1283, "V8 Twin Turbo", "RWD"),
    ("McLaren", "570S", 2015, "UK", 562, 1313, "V8 Twin Turbo", "RWD"),
    ("McLaren", "MP4-12C", 2011, "UK", 592, 1336, "V8 Twin Turbo", "RWD"),
    ("McLaren", "Senna", 2018, "UK", 789, 1198, "V8 Twin Turbo", "RWD"),
    ("McLaren", "Speedtail", 2019, "UK", 1035, 1430, "V8 Hybrid", "RWD"),
    ("McLaren", "Artura", 2022, "UK", 671, 1395, "V6 Twin Turbo Hybrid", "RWD"),
    ("Bentley", "Continental GT", 2003, "UK", 552, 2350, "W12 Twin Turbo", "AWD"),
    ("Bentley", "Continental GT Speed", 2007, "UK", 600, 2320, "W12 Twin Turbo", "AWD"),
    ("Rolls-Royce", "Silver Shadow", 1965, "UK", 189, 2075, "V8", "RWD"),
    ("Rolls-Royce", "Phantom VII", 2003, "UK", 453, 2550, "V12", "RWD"),
    ("Land Rover", "Defender (L316)", 1983, "UK", 122, 1830, "I4 Turbo Diesel", "4WD"),
    ("Land Rover", "Range Rover (L322)", 2002, "UK", 282, 2510, "V8", "4WD"),
    ("Land Rover", "Range Rover Sport SVR", 2015, "UK", 550, 2310, "V8 Supercharged", "AWD"),
    ("Mini", "Cooper S (R53)", 2002, "UK", 163, 1140, "I4 Supercharged", "FWD"),
    ("Mini", "John Cooper Works (R56)", 2008, "UK", 211, 1205, "I4 Turbo", "FWD"),
    ("Mini", "Classic Cooper S", 1963, "UK", 76, 660, "I4", "FWD"),
    ("TVR", "Sagaris", 2004, "UK", 406, 1078, "I6", "RWD"),
    ("TVR", "Tuscan", 1999, "UK", 350, 1100, "I6", "RWD"),
    ("TVR", "Cerbera Speed Six", 1996, "UK", 350, 1130, "I6", "RWD"),
    ("Morgan", "Aero 8", 2001, "UK", 286, 1100, "V8", "RWD"),
    ("Caterham", "Seven 620R", 2013, "UK", 311, 545, "I4 Supercharged", "RWD"),
    ("Ariel", "Atom 500", 2011, "UK", 500, 550, "V8", "RWD"),
    ("Noble", "M600", 2010, "UK", 650, 1198, "V8 Twin Turbo", "RWD"),
    ("Gordon Murray", "T.50", 2022, "UK", 654, 986, "V12", "RWD"),
    # === French ===
    ("Peugeot", "205 GTI", 1984, "France", 130, 875, "I4", "FWD"),
    ("Peugeot", "306 GTi-6", 1996, "France", 167, 1215, "I4", "FWD"),
    ("Peugeot", "106 Rallye", 1994, "France", 103, 825, "I4", "FWD"),
    ("Peugeot", "308 GTi", 2015, "France", 270, 1205, "I4 Turbo", "FWD"),
    ("Renault", "5 Turbo", 1980, "France", 160, 970, "I4 Turbo", "RWD"),
    ("Renault", "Clio V6", 2001, "France", 230, 1335, "V6", "RWD"),
    ("Renault", "Clio Williams", 1993, "France", 150, 1015, "I4", "FWD"),
    ("Renault", "Megane RS (Mk3)", 2009, "France", 250, 1387, "I4 Turbo", "FWD"),
    ("Renault", "Megane RS Trophy-R", 2019, "France", 300, 1306, "I4 Turbo", "FWD"),
    ("Renault", "Alpine A110 (2017)", 2017, "France", 252, 1103, "I4 Turbo", "RWD"),
    ("Renault", "Alpine A110 (Original)", 1962, "France", 80, 710, "I4", "RWD"),
    ("Citroën", "DS", 1955, "France", 75, 1180, "I4", "FWD"),
    ("Citroën", "SM", 1970, "France", 170, 1450, "V6", "FWD"),
    ("Citroën", "2CV", 1948, "France", 9, 560, "Flat-2", "FWD"),
    ("Bugatti", "Veyron 16.4", 2005, "France", 1001, 1888, "W16 Quad Turbo", "AWD"),
    ("Bugatti", "Chiron", 2016, "France", 1479, 1978, "W16 Quad Turbo", "AWD"),
    ("Bugatti", "EB110", 1991, "France", 553, 1566, "V12 Quad Turbo", "AWD"),
    ("Bugatti", "Divo", 2019, "France", 1479, 1986, "W16 Quad Turbo", "AWD"),
    # === Swedish ===
    ("Volvo", "240 Turbo", 1980, "Sweden", 155, 1280, "I4 Turbo", "RWD"),
    ("Volvo", "850 T-5R", 1995, "Sweden", 240, 1430, "I5 Turbo", "FWD"),
    ("Volvo", "C30 Polestar", 2009, "Sweden", 227, 1347, "I5 Turbo", "FWD"),
    ("Volvo", "P1800", 1961, "Sweden", 108, 1140, "I4", "RWD"),
    ("Volvo", "S60 Polestar", 2014, "Sweden", 350, 1695, "I6 Turbo", "AWD"),
    ("Saab", "9-3 Viggen", 1999, "Sweden", 225, 1415, "I4 Turbo", "FWD"),
    ("Saab", "900 Turbo", 1978, "Sweden", 145, 1230, "I4 Turbo", "FWD"),
    ("Koenigsegg", "CCX", 2006, "Sweden", 806, 1180, "V8 Twin Supercharged", "RWD"),
    ("Koenigsegg", "Agera RS", 2015, "Sweden", 1160, 1395, "V8 Twin Turbo", "RWD"),
    ("Koenigsegg", "Jesko", 2019, "Sweden", 1600, 1420, "V8 Twin Turbo", "RWD"),
    ("Koenigsegg", "Regera", 2016, "Sweden", 1500, 1628, "V8 Twin Turbo Hybrid", "RWD"),
    ("Polestar", "1", 2019, "Sweden", 609, 2350, "I4 Turbo Hybrid", "AWD"),
    ("Polestar", "2", 2020, "Sweden", 408, 2113, "Electric", "AWD"),
    # === American (additional) ===
    ("Shelby", "Cobra 427", 1965, "USA", 425, 1063, "V8", "RWD"),
    ("Shelby", "GT350", 1965, "USA", 306, 1247, "V8", "RWD"),
    ("Shelby", "GT500 (S550)", 2020, "USA", 760, 1916, "V8 Supercharged", "RWD"),
    ("Cadillac", "CTS-V (2nd Gen)", 2009, "USA", 556, 1919, "V8 Supercharged", "RWD"),
    ("Cadillac", "CT5-V Blackwing", 2022, "USA", 668, 1885, "V8 Supercharged", "RWD"),
    ("Cadillac", "Escalade (4th Gen)", 2015, "USA", 420, 2630, "V8", "4WD"),
    ("Cadillac", "Eldorado (1959)", 1959, "USA", 345, 2210, "V8", "RWD"),
    ("Lincoln", "Continental (4th Gen)", 1961, "USA", 300, 2290, "V8", "RWD"),
    ("Jeep", "Wrangler (TJ)", 1996, "USA", 181, 1574, "I6", "4WD"),
    ("Jeep", "Grand Cherokee SRT8 (WK2)", 2012, "USA", 470, 2260, "V8", "AWD"),
    ("Jeep", "CJ-7", 1976, "USA", 150, 1447, "I6", "4WD"),
    ("GMC", "Syclone", 1991, "USA", 280, 1602, "V6 Turbo", "AWD"),
    ("Buick", "Grand National GNX", 1987, "USA", 276, 1643, "V6 Turbo", "RWD"),
    ("Chevrolet", "El Camino SS", 1970, "USA", 450, 1716, "V8", "RWD"),
    ("Chevrolet", "Monte Carlo SS", 1987, "USA", 180, 1503, "V8", "RWD"),
    ("Chevrolet", "SSR", 2003, "USA", 300, 2132, "V8", "RWD"),
    ("Chevrolet", "Silverado (3rd Gen)", 2019, "USA", 420, 2140, "V8", "4WD"),
    ("Tesla", "Model S Plaid", 2021, "USA", 1020, 2162, "Electric", "AWD"),
    ("Tesla", "Model 3 Performance", 2018, "USA", 450, 1847, "Electric", "AWD"),
    ("Tesla", "Roadster (1st Gen)", 2008, "USA", 248, 1235, "Electric", "RWD"),
    ("Tesla", "Model X Plaid", 2021, "USA", 1020, 2455, "Electric", "AWD"),
    ("Tesla", "Cybertruck", 2023, "USA", 845, 3104, "Electric", "AWD"),
    ("Rivian", "R1T", 2021, "USA", 835, 3075, "Electric", "AWD"),
    ("Lucid", "Air Sapphire", 2023, "USA", 1234, 2360, "Electric", "AWD"),
    ("Hennessey", "Venom GT", 2012, "USA", 1244, 1244, "V8 Twin Turbo", "RWD"),
    ("SSC", "Tuatara", 2020, "USA", 1750, 1247, "V8 Twin Turbo", "RWD"),
    ("Saleen", "S7 Twin Turbo", 2005, "USA", 750, 1247, "V8 Twin Turbo", "RWD"),
    ("Vector", "W8", 1990, "USA", 625, 1565, "V8 Twin Turbo", "RWD"),
    ("DeLorean", "DMC-12", 1981, "USA", 130, 1233, "V6", "RWD"),
    ("Hummer", "H1 Alpha", 2006, "USA", 300, 3610, "V8 Turbo Diesel", "4WD"),
    ("RAM", "1500 TRX", 2021, "USA", 702, 2870, "V8 Supercharged", "4WD"),
    ("Ford", "Explorer (1st Gen)", 1991, "USA", 155, 1824, "V6", "4WD"),
    ("Ford", "Taurus SHO (1st Gen)", 1989, "USA", 220, 1527, "V6", "FWD"),
    ("Chevrolet", "Cobalt SS Turbo", 2008, "USA", 260, 1311, "I4 Turbo", "FWD"),
    ("Pontiac", "Solstice GXP", 2007, "USA", 260, 1310, "I4 Turbo", "RWD"),
    ("Saturn", "Sky Red Line", 2007, "USA", 260, 1310, "I4 Turbo", "RWD"),
    # === South Korean ===
    ("Hyundai", "Veloster N", 2019, "South Korea", 275, 1391, "I4 Turbo", "FWD"),
    ("Hyundai", "i30 N", 2017, "South Korea", 275, 1429, "I4 Turbo", "FWD"),
    ("Hyundai", "Genesis Coupe 3.8", 2008, "South Korea", 306, 1540, "V6", "RWD"),
    ("Hyundai", "IONIQ 5 N", 2024, "South Korea", 601, 2190, "Electric", "AWD"),
    ("Genesis", "G70 3.3T", 2017, "South Korea", 365, 1715, "V6 Twin Turbo", "RWD"),
    ("Genesis", "GV70 3.5T", 2021, "South Korea", 375, 1955, "V6 Twin Turbo", "AWD"),
    ("Kia", "Stinger GT", 2017, "South Korea", 365, 1780, "V6 Twin Turbo", "RWD"),
    ("Kia", "EV6 GT", 2022, "South Korea", 577, 2090, "Electric", "AWD"),
    # === Australian ===
    ("Holden", "Commodore VL Turbo", 1986, "Australia", 204, 1330, "I6 Turbo", "RWD"),
    ("Holden", "Commodore (VE) SS-V", 2006, "Australia", 362, 1744, "V8", "RWD"),
    ("Holden", "Monaro CV8", 2001, "Australia", 306, 1633, "V8", "RWD"),
    ("Holden", "Torana A9X", 1978, "Australia", 199, 1260, "V8", "RWD"),
    ("Ford", "Falcon GT-HO Phase III", 1971, "Australia", 300, 1524, "V8", "RWD"),
    ("Ford", "Falcon XR6 Turbo (FG)", 2008, "Australia", 310, 1626, "I6 Turbo", "RWD"),
    ("HSV", "GTS (E Series)", 2006, "Australia", 425, 1792, "V8 Supercharged", "RWD"),
    # === Other Countries ===
    ("Tata", "Nano", 2008, "India", 38, 600, "I2", "RWD"),
    ("Mahindra", "Thar", 2010, "India", 105, 1660, "I4 Turbo Diesel", "4WD"),
    ("Proton", "Satria GTi", 1998, "Malaysia", 138, 1080, "I4", "FWD"),
    ("Skoda", "Octavia RS (Mk3)", 2013, "Czech Republic", 220, 1365, "I4 Turbo", "FWD"),
    ("SEAT", "Leon Cupra R", 2009, "Spain", 265, 1375, "I4 Turbo", "FWD"),
    ("Dacia", "Sandero Stepway", 2009, "Romania", 90, 1140, "I4", "FWD"),
    # === Chinese EVs ===
    ("BYD", "Han EV", 2020, "China", 517, 2170, "Electric", "AWD"),
    ("BYD", "Seal", 2022, "China", 523, 2150, "Electric", "AWD"),
    ("NIO", "ET7", 2022, "China", 644, 2379, "Electric", "AWD"),
    ("NIO", "EP9", 2016, "China", 1341, 1735, "Electric", "AWD"),
    ("Xpeng", "P7", 2020, "China", 267, 1900, "Electric", "RWD"),
    ("Xiaomi", "SU7", 2024, "China", 673, 1980, "Electric", "AWD"),
    ("Geely", "Zeekr 001", 2021, "China", 544, 2310, "Electric", "AWD"),
    # === Additional JDM ===
    ("Toyota", "Century (3rd Gen)", 1997, "Japan", 280, 1990, "V12", "RWD"),
    ("Toyota", "Crown Athlete", 2003, "Japan", 280, 1560, "V6 Twin Turbo", "RWD"),
    ("Toyota", "Chaser JZX100", 1996, "Japan", 280, 1480, "I6 Turbo", "RWD"),
    ("Toyota", "Soarer (Z30)", 1991, "Japan", 280, 1660, "V8", "RWD"),
    ("Toyota", "GR86", 2022, "Japan", 228, 1270, "Flat-4", "RWD"),
    ("Toyota", "RAV4 (XA50)", 2019, "Japan", 203, 1600, "I4", "AWD"),
    ("Nissan", "Stagea RS Four (WC34)", 1997, "Japan", 280, 1630, "I6 Turbo", "AWD"),
    ("Nissan", "Pulsar GTI-R", 1990, "Japan", 230, 1220, "I4 Turbo", "AWD"),
    ("Nissan", "Leaf (1st Gen)", 2010, "Japan", 109, 1521, "Electric", "FWD"),
    ("Honda", "Accord Euro R (CL1)", 2000, "Japan", 220, 1340, "I4", "FWD"),
    ("Honda", "City Turbo II", 1983, "Japan", 110, 735, "I4 Turbo", "FWD"),
    ("Honda", "e", 2020, "Japan", 154, 1512, "Electric", "RWD"),
    ("Lexus", "LFA", 2010, "Japan", 553, 1480, "V10", "RWD"),
    ("Lexus", "IS F", 2007, "Japan", 416, 1714, "V8", "RWD"),
    ("Lexus", "LC 500", 2017, "Japan", 471, 1935, "V8", "RWD"),
    ("Lexus", "RC F", 2014, "Japan", 467, 1765, "V8", "RWD"),
    ("Lexus", "LS 400 (UCF10)", 1989, "Japan", 250, 1690, "V8", "RWD"),
    ("Infiniti", "G35 Coupe", 2003, "Japan", 260, 1544, "V6", "RWD"),
    ("Infiniti", "Q50 Red Sport 400", 2016, "Japan", 400, 1718, "V6 Twin Turbo", "RWD"),
    ("Acura", "Integra Type R (DC2)", 1997, "Japan", 195, 1101, "I4", "FWD"),
    ("Acura", "NSX (2016)", 2016, "Japan", 573, 1725, "V6 Twin Turbo Hybrid", "AWD"),
    ("Isuzu", "Vehicross", 1997, "Japan", 215, 1930, "V6", "4WD"),
    ("Datsun", "240Z (S30)", 1969, "Japan", 151, 1041, "I6", "RWD"),
    ("Datsun", "510 SSS", 1967, "Japan", 96, 870, "I4", "RWD"),
    # === Additional German ===
    ("Audi", "RS5 (B8)", 2010, "Germany", 450, 1715, "V8", "AWD"),
    ("Audi", "RS7 (C7)", 2013, "Germany", 560, 1920, "V8 Twin Turbo", "AWD"),
    ("Audi", "TT RS (8S)", 2017, "Germany", 400, 1440, "I5 Turbo", "AWD"),
    ("Volkswagen", "Golf R32 (Mk4)", 2002, "Germany", 240, 1477, "VR6", "AWD"),
    ("Volkswagen", "Type 2 (T1)", 1950, "Germany", 25, 1050, "Flat-4", "RWD"),
    ("Volkswagen", "Karmann Ghia", 1955, "Germany", 36, 820, "Flat-4", "RWD"),
    ("Volkswagen", "Up! GTI", 2018, "Germany", 115, 1070, "I3 Turbo", "FWD"),
    ("Volkswagen", "ID.4 GTX", 2021, "Germany", 295, 2224, "Electric", "AWD"),
    ("Mercedes-Benz", "300 SEL 6.3", 1968, "Germany", 247, 1780, "V8", "RWD"),
    ("Mercedes-Benz", "A45 AMG (W176)", 2013, "Germany", 355, 1480, "I4 Turbo", "AWD"),
    ("Mercedes-Benz", "EQS 580", 2021, "Germany", 516, 2480, "Electric", "AWD"),
    ("BMW", "X5 M (E70)", 2009, "Germany", 555, 2380, "V8 Twin Turbo", "AWD"),
    ("BMW", "M4 GTS (F82)", 2016, "Germany", 493, 1510, "I6 Twin Turbo", "RWD"),
    ("BMW", "i4 M50", 2022, "Germany", 536, 2215, "Electric", "AWD"),
    ("BMW", "M8 Competition", 2019, "Germany", 617, 1885, "V8 Twin Turbo", "AWD"),
    ("BMW", "850CSi (E31)", 1992, "Germany", 380, 1780, "V12", "RWD"),
    ("Porsche", "Macan GTS", 2015, "Germany", 360, 1895, "V6 Twin Turbo", "AWD"),
    ("Porsche", "GT2 RS (991)", 2017, "Germany", 700, 1470, "Flat-6 Twin Turbo", "RWD"),
    ("Porsche", "914", 1969, "Germany", 80, 940, "Flat-4", "RWD"),
    ("Porsche", "928 GTS", 1992, "Germany", 350, 1545, "V8", "RWD"),
    ("Mercedes-AMG", "GT Black Series", 2020, "Germany", 720, 1575, "V8 Twin Turbo", "RWD"),
    ("Wiesmann", "GT MF5", 2009, "Germany", 507, 1350, "V10", "RWD"),
    ("Gumpert", "Apollo", 2005, "Germany", 650, 1100, "V8 Twin Turbo", "RWD"),
    ("Ruf", "CTR Yellow Bird", 1987, "Germany", 469, 1150, "Flat-6 Twin Turbo", "RWD"),
    ("Ruf", "CTR3", 2007, "Germany", 700, 1400, "Flat-6 Twin Turbo", "RWD"),
    ("Alpina", "B10 Biturbo", 1989, "Germany", 360, 1620, "I6 Twin Turbo", "RWD"),
    # === Additional European ===
    ("Renault", "Clio RS 200", 2006, "France", 197, 1204, "I4", "FWD"),
    ("Peugeot", "207 GTi", 2007, "France", 175, 1193, "I4 Turbo", "FWD"),
    ("Peugeot", "405 Mi16", 1988, "France", 160, 1200, "I4", "FWD"),
    ("Citroën", "Saxo VTS", 1996, "France", 120, 935, "I4", "FWD"),
    ("Citroën", "C2 VTS", 2003, "France", 125, 1050, "I4", "FWD"),
    ("Rimac", "Nevera", 2021, "Croatia", 1914, 2150, "Electric", "AWD"),
    ("Rimac", "Concept One", 2013, "Croatia", 1224, 1850, "Electric", "AWD"),
    # === Additional British ===
    ("Vauxhall", "VXR8", 2007, "UK", 425, 1813, "V8", "RWD"),
    ("Vauxhall", "Lotus Carlton", 1990, "UK", 377, 1658, "I6 Twin Turbo", "RWD"),
    ("Ginetta", "G60", 2015, "UK", 310, 1080, "V6 Supercharged", "RWD"),
    ("BAC", "Mono", 2011, "UK", 305, 540, "I4", "RWD"),
    ("Radical", "SR8", 2005, "UK", 440, 680, "V8", "RWD"),
    ("MG", "F", 1995, "UK", 120, 1060, "I4", "RWD"),
    ("MG", "MGB GT", 1965, "UK", 95, 1020, "I4", "RWD"),
    ("Triumph", "TR6", 1968, "UK", 150, 1117, "I6", "RWD"),
    ("Austin-Healey", "3000 Mk III", 1963, "UK", 150, 1178, "I6", "RWD"),
    # === Pickup Trucks & SUVs (popular) ===
    ("Toyota", "Tacoma TRD Pro (3rd Gen)", 2016, "Japan", 278, 1955, "V6", "4WD"),
    ("Toyota", "4Runner (5th Gen)", 2010, "Japan", 270, 2041, "V6", "4WD"),
    ("Ford", "Ranger Raptor", 2018, "Australia", 213, 2361, "I4 Turbo Diesel", "4WD"),
    ("Chevrolet", "Tahoe (4th Gen)", 2015, "USA", 355, 2495, "V8", "4WD"),
    ("Nissan", "Frontier PRO-4X", 2005, "Japan", 261, 1927, "V6", "4WD"),
    ("Jeep", "Gladiator Rubicon", 2020, "USA", 285, 2320, "V6", "4WD"),
    ("Mercedes-Benz", "G63 AMG (W463)", 2012, "Germany", 544, 2550, "V8 Twin Turbo", "4WD"),
    # === Hypercars & Exotics (misc) ===
    ("Zenvo", "TSR-S", 2018, "Denmark", 1177, 1495, "V8 Twin Supercharged", "RWD"),
    ("Spyker", "C8 Aileron", 2008, "Netherlands", 400, 1400, "V8", "RWD"),
    ("Donkervoort", "D8 GTO", 2013, "Netherlands", 380, 700, "I5 Turbo", "RWD"),
    ("W Motors", "Lykan HyperSport", 2013, "Lebanon", 780, 1380, "Flat-6 Twin Turbo", "RWD"),
    ("Hispano-Suiza", "Carmen", 2019, "Spain", 1005, 1690, "Electric", "RWD"),
    ("Czinger", "21C", 2022, "USA", 1233, 1250, "V8 Twin Turbo Hybrid", "RWD"),
    # === Rally & Race Heritage (road cars) ===
    ("Lancia", "Fulvia 1.6 HF", 1969, "Italy", 132, 960, "V4", "FWD"),
    ("Ford", "RS200", 1984, "UK", 250, 1050, "I4 Turbo", "4WD"),
    ("MG", "Metro 6R4", 1985, "UK", 250, 1000, "V6", "4WD"),
    ("Peugeot", "205 T16", 1984, "France", 200, 940, "I4 Turbo", "4WD"),
    ("Toyota", "Celica GT-Four (ST185)", 1990, "Japan", 204, 1350, "I4 Turbo", "AWD"),
    ("Mitsubishi", "Lancer Evolution III", 1995, "Japan", 270, 1260, "I4 Turbo", "AWD"),
    ("Subaru", "Impreza 22B STI", 1998, "Japan", 280, 1270, "Flat-4 Turbo", "AWD"),
    # === Station Wagons / Estates (enthusiast favorites) ===
    ("Audi", "RS2 Avant", 1994, "Germany", 315, 1595, "I5 Turbo", "AWD"),
    ("Audi", "RS4 Avant (B7)", 2006, "Germany", 420, 1710, "V8", "AWD"),
    ("Audi", "RS6 Avant (C6)", 2008, "Germany", 580, 2025, "V10 Twin Turbo", "AWD"),
    ("BMW", "M5 Touring (E34)", 1992, "Germany", 340, 1730, "I6", "RWD"),
    ("BMW", "M5 Touring (E61)", 2007, "Germany", 507, 1890, "V10", "RWD"),
    ("Mercedes-Benz", "E63 AMG Estate (S212)", 2009, "Germany", 518, 1920, "V8 Twin Turbo", "RWD"),
    ("Volvo", "V60 Polestar", 2014, "Sweden", 350, 1695, "I6 Turbo", "AWD"),
    # === Additional Classics ===
    ("Chevrolet", "Corvette Stingray (C2)", 1963, "USA", 360, 1399, "V8", "RWD"),
    ("Ford", "Shelby Mustang GT500 (1967)", 1967, "USA", 355, 1511, "V8", "RWD"),
    ("Porsche", "904 Carrera GTS", 1964, "Germany", 180, 655, "Flat-4", "RWD"),
    ("Jaguar", "XKSS", 1957, "UK", 262, 1020, "I6", "RWD"),
    ("Mercedes-Benz", "SLR 300", 1955, "Germany", 310, 1293, "I6", "RWD"),
    ("Ferrari", "250 GT California", 1957, "Italy", 240, 1050, "V12", "RWD"),
    ("Aston Martin", "DB4 GT Zagato", 1960, "UK", 314, 1225, "I6", "RWD"),
    ("AC", "Cobra 427", 1965, "UK", 425, 1063, "V8", "RWD"),
    ("Chevrolet", "Nova SS", 1966, "USA", 350, 1408, "V8", "RWD"),
    ("Oldsmobile", "442 W-30", 1970, "USA", 370, 1619, "V8", "RWD"),
    ("Plymouth", "Superbird", 1970, "USA", 425, 1688, "V8", "RWD"),
    ("AMC", "Javelin AMX", 1971, "USA", 401, 1497, "V8", "RWD"),
    # === Modern Performance EVs ===
    ("Porsche", "Taycan 4S", 2020, "Germany", 563, 2220, "Electric", "AWD"),
    ("BMW", "iX M60", 2022, "Germany", 610, 2560, "Electric", "AWD"),
    ("Mercedes-Benz", "EQE AMG", 2022, "Germany", 677, 2525, "Electric", "AWD"),
    ("Lotus", "Eletre R", 2023, "UK", 905, 2640, "Electric", "AWD"),
    ("Hyundai", "IONIQ 6", 2023, "South Korea", 320, 1985, "Electric", "AWD"),
    ("Ford", "Mustang Mach-E GT", 2021, "USA", 480, 2218, "Electric", "AWD"),
    ("Chevrolet", "Corvette E-Ray", 2024, "USA", 655, 1736, "V8 Hybrid", "AWD"),
    ("Dodge", "Charger Daytona SRT", 2024, "USA", 670, 2415, "Electric", "AWD"),
    # === Gran Turismo / Touring Cars ===
    ("Aston Martin", "Vantage (2018)", 2018, "UK", 503, 1530, "V8 Twin Turbo", "RWD"),
    ("BMW", "M850i (G15)", 2018, "Germany", 523, 1890, "V8 Twin Turbo", "AWD"),
    ("Lexus", "LC 500h", 2017, "Japan", 354, 2020, "V6 Hybrid", "RWD"),
    ("Maserati", "MC20", 2020, "Italy", 621, 1475, "V6 Twin Turbo", "RWD"),
    ("Ferrari", "Roma", 2020, "Italy", 612, 1472, "V8 Twin Turbo", "RWD"),
    ("Bentley", "Continental GT V8", 2019, "UK", 542, 2165, "V8 Twin Turbo", "AWD"),
    ("Mercedes-AMG", "GT 63 S 4-Door", 2019, "Germany", 630, 2075, "V8 Twin Turbo", "AWD"),
]


def make_slug(make: str, model: str) -> str:
    """Create a URL-safe slug from make and model."""
    text = f"{make}-{model}".lower()
    slug = ""
    for ch in text:
        if ch.isalnum() or ch == '-':
            slug += ch
        elif ch in (' ', '_', '/'):
            slug += '-'
    while '--' in slug:
        slug = slug.replace('--', '-')
    return slug.strip('-')


def generate_wiki_url(make: str, model: str) -> str:
    """Generate a plausible Wikipedia URL for a car model."""
    # Combine make and model, replacing spaces with underscores
    title = f"{make}_{model}"
    # Remove parenthetical generation codes for cleaner URLs
    title = re.sub(r'\s*\([^)]*\)\s*', ' ', title).strip()
    title = title.replace(' ', '_')
    return f"https://en.wikipedia.org/wiki/{title}"


def validate_car(car: dict) -> tuple[bool, list[str]]:
    """
    Validate that a car has all required fields for the guessing game.
    Returns (is_valid, list_of_reasons) — if invalid, reasons describe what's
    missing or wrong.
    """
    reasons: list[str] = []

    if not car.get("make"):
        reasons.append("missing make")
    if not car.get("model"):
        reasons.append("missing model")

    year = car.get("year", 0)
    if not isinstance(year, int) or year < 1800 or year > 2030:
        reasons.append(f"invalid year ({year})")

    if not car.get("country"):
        reasons.append("missing country")

    hp = car.get("horsepower", 0)
    if not isinstance(hp, (int, float)) or hp <= 0:
        reasons.append(f"invalid horsepower ({hp})")

    weight = car.get("weight_kg", 0)
    if not isinstance(weight, (int, float)) or weight <= 0:
        reasons.append(f"invalid weight ({weight})")

    if not car.get("engine"):
        reasons.append("missing engine")

    dt = car.get("drivetrain", "")
    if not dt:
        reasons.append("missing drivetrain")

    return (len(reasons) == 0, reasons)


def build_cars(limit: int | None = None) -> list[dict]:
    """Convert the embedded car data into Car-interface-compatible dicts."""
    cars = []
    skipped: list[tuple[str, str, list[str]]] = []
    for idx, (make, model, year, country, hp, weight, engine, dt) in enumerate(CARS, 1):
        slug = make_slug(make, model)
        car = {
            "id": idx,
            "make": make,
            "model": model,
            "year": year,
            "country": country,
            "horsepower": hp,
            "weight_kg": weight,
            "engine": engine,
            "drivetrain": dt,
            "image": f"/cars/{slug}.webp",
            "fact": "",
            "wiki": generate_wiki_url(make, model),
        }

        valid, reasons = validate_car(car)
        if not valid:
            skipped.append((make, model, reasons))
            continue

        cars.append(car)

    if skipped:
        print(f"\n  Skipped {len(skipped)} cars with incomplete data:")
        for s_make, s_model, s_reasons in skipped:
            print(f"    - {s_make} {s_model}: {', '.join(s_reasons)}")

    if limit:
        cars = cars[:limit]

    # Reassign IDs sequentially after filtering
    for idx, car in enumerate(cars, 1):
        car["id"] = idx

    return cars


def print_stats(cars: list[dict]) -> None:
    """Print summary statistics about the car list."""
    print(f"\nTotal cars: {len(cars)}")

    # Country distribution
    countries: dict[str, int] = {}
    for c in cars:
        countries[c["country"]] = countries.get(c["country"], 0) + 1
    print(f"\nCountry distribution:")
    for country, count in sorted(countries.items(), key=lambda x: -x[1]):
        print(f"  {country}: {count}")

    # Make distribution (top 20)
    makes: dict[str, int] = {}
    for c in cars:
        makes[c["make"]] = makes.get(c["make"], 0) + 1
    print(f"\nTop manufacturers:")
    for make, count in sorted(makes.items(), key=lambda x: -x[1])[:20]:
        print(f"  {make}: {count}")

    # Decade distribution
    decades: dict[str, int] = {}
    for c in cars:
        decade = f"{(c['year'] // 10) * 10}s"
        decades[decade] = decades.get(decade, 0) + 1
    print(f"\nDecade distribution:")
    for decade, count in sorted(decades.items()):
        print(f"  {decade}: {count}")

    # Drivetrain distribution
    dts: dict[str, int] = {}
    for c in cars:
        dts[c["drivetrain"]] = dts.get(c["drivetrain"], 0) + 1
    print(f"\nDrivetrain distribution:")
    for dt, count in sorted(dts.items(), key=lambda x: -x[1]):
        print(f"  {dt}: {count}")

    # Engine type distribution (simplified)
    print(f"\nEngine highlights:")
    evs = sum(1 for c in cars if c["engine"] == "Electric")
    hybrids = sum(1 for c in cars if "Hybrid" in c["engine"])
    turbos = sum(1 for c in cars if "Turbo" in c["engine"])
    supers = sum(1 for c in cars if "Supercharged" in c["engine"])
    v12s = sum(1 for c in cars if c["engine"].startswith("V12"))
    rotary = sum(1 for c in cars if "Rotary" in c["engine"])
    print(f"  Electric: {evs}")
    print(f"  Hybrid: {hybrids}")
    print(f"  Turbocharged: {turbos}")
    print(f"  Supercharged: {supers}")
    print(f"  V12: {v12s}")
    print(f"  Rotary: {rotary}")

    # Year range
    years = [c["year"] for c in cars]
    print(f"\nYear range: {min(years)} - {max(years)}")

    # HP range
    hps = [c["horsepower"] for c in cars if c["horsepower"]]
    print(f"HP range: {min(hps)} - {max(hps)}")

    # Weight range
    weights = [c["weight_kg"] for c in cars if c["weight_kg"]]
    print(f"Weight range: {min(weights)} - {max(weights)} kg")


def main():
    parser = argparse.ArgumentParser(
        description="Generate a curated car dataset for Grille"
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Limit output to top N cars (default: all)"
    )
    parser.add_argument(
        "--stats", action="store_true",
        help="Show statistics only, don't write file"
    )
    args = parser.parse_args()

    cars = build_cars(args.limit)
    print_stats(cars)

    if args.stats:
        return

    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    output_file = repo_root / "data" / "cars-wikidata.json"

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(cars, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(cars)} cars to {output_file}")
    print(
        "\nNext steps:\n"
        "  1. Run scripts/fetch-cars.py to enrich with Wikidata "
        "(images, verified specs, sitelink counts)\n"
        "  2. Review and curate the list\n"
        "  3. Download images from Wikimedia Commons\n"
        "  4. Write fun facts for each car\n"
    )


if __name__ == "__main__":
    main()
