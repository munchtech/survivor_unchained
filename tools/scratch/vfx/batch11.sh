#!/usr/bin/env bash
# The new lead's first shoot: batch10 again (enemy looks, the Dig), the main session's three
# findings in a packed crowd (numbers, Hoarfrost's white, motes' and disc's bloom over her),
# and the rise (Cold, Then Not; Not Yet).
cd "$(dirname "$0")"
python shot.py dig3 --zone arena --people lamplings --seed 739 --tier 2 --minute 25 --give "oathblade:6,seeking_motes:5,cinderfall:5" --auto --seconds 5 --every 1.5 --count 10
python shot.py kerch3 --zone arena --people kerchiefs --tier 2 --minute 25 --give "oathblade:6,seeking_motes:5,cinderfall:5,arcweb:4" --auto --seconds 5 --every 1.5 --count 10
python shot.py dead3 --zone arena --people dead --tier 3 --minute 25 --give "oathblade:6,hoarfrost:6,seeking_motes:5" --auto --seconds 5 --every 1.5 --count 10
python shot.py pack3 --zone arena --people pack --tier 3 --minute 25 --give "cleaver:6,judgement_disc:6,volley:5" --auto --seconds 5 --every 1.5 --count 10
python sweep.py s8 gale_chakram umbral_bolt moonbrand reaving_arc thunderhead --horde 40 --dist 5 --spread 7 --every 0.05 --count 32 --start 2.0
python sweep.py r1 oathblade hoarfrost seeking_motes judgement_disc cinderfall
echo done
