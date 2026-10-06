#!/usr/bin/env bash
# After the director's frozen/burning tint, the numbers and the new atlases: the packed crowd,
# the remade skills, the lamplings' marks on the Dig, the Kerchiefs' lobs, minute 20 Hoarfrost.
cd "$(dirname "$0")"
python sweep.py a9 oathblade hoarfrost seeking_motes judgement_disc cinderfall
python sweep.py s6 arcweb thunderhead verdant_lance reaving_arc gale_chakram moonbrand dawnpulse umbral_bolt thornbloom --horde 40 --dist 5 --spread 7 --every 0.05 --count 32 --start 2.0
python shot.py dig1 --zone arena --people lamplings --seed 739 --tier 2 --minute 25 --give "oathblade:6,seeking_motes:5,cinderfall:5" --auto --seconds 5 --every 2 --count 8
python shot.py kerch1 --zone arena --people kerchiefs --tier 2 --minute 25 --give "oathblade:6,seeking_motes:5,cinderfall:5,arcweb:4" --auto --seconds 5 --every 3 --count 8
python shot.py m20 --zone arena --people dead --tier 2 --minute 20 --give "hoarfrost:6,oathblade:6,seeking_motes:5" --auto --seconds 6 --every 1.5 --count 8
echo done
