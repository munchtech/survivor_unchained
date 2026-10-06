#!/usr/bin/env bash
# The enemy looks in play (rallies, summons, slams, bolts, orbs), the Dig's marks, and the round-5 fixes.
cd "$(dirname "$0")"
python shot.py dig2 --zone arena --people lamplings --seed 739 --tier 2 --minute 25 --give "oathblade:6,seeking_motes:5,cinderfall:5" --auto --seconds 5 --every 1.5 --count 10
python shot.py kerch2 --zone arena --people kerchiefs --tier 2 --minute 25 --give "oathblade:6,seeking_motes:5,cinderfall:5,arcweb:4" --auto --seconds 5 --every 1.5 --count 10
python shot.py dead2 --zone arena --people dead --tier 3 --minute 25 --give "oathblade:6,hoarfrost:6,seeking_motes:5" --auto --seconds 5 --every 1.5 --count 10
python shot.py pack2 --zone arena --people pack --tier 3 --minute 25 --give "cleaver:6,judgement_disc:6,volley:5" --auto --seconds 5 --every 1.5 --count 10
python sweep.py s7 gale_chakram umbral_bolt moonbrand reaving_arc thunderhead --horde 40 --dist 5 --spread 7 --every 0.05 --count 32 --start 2.0
echo done
