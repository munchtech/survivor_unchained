#!/usr/bin/env bash
# The rest of the evolutions, for grading.
cd "$(dirname "$0")"
python sweep.py v1 seeking_motes:4@mote_cascade seeking_motes:4@starseeker moonbrand:4@moonfall moonbrand:4@lunar_brand cinderfall:4@fallen_star cinderfall:4@living_flame rimeshard:4@deepwinter rimeshard:4@glacier_spear hoarfrost:4@winter_ward hoarfrost:4@absolute_zero arcweb:4@skybreak arcweb:4@tempest_coil thunderhead:4@eye_of_the_storm thunderhead:4@thunderclap umbral_bolt:4@ruin_bolt umbral_bolt:4@soul_siphon --count 12 --every 0.15
python sweep.py v1 grave_tether:4@tether_of_anguish grave_tether:4@deathcoil gravecall:4@barrow_legion gravecall:4@bone_knights dawnpulse:4@circle_of_dawn dawnpulse:4@sunbreak hallowed_ring:4@sanctified_earth blightfield:4@blighted_earth blightfield:4@plaguebloom thornbloom:4@everbloom thornbloom:4@strangleroot verdant_lance:4@verdant_gaze verdant_lance:4@sunlance spirit_herd:4@great_herd spirit_herd:4@wild_hunt --count 12 --every 0.15
echo done
