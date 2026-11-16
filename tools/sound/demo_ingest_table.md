# Den sound ingest (tools/sound/demo_ingest.py)

Source: `survivorsunchained_inputs/sounds_demo/` (ElevenLabs, made by the owner, 15-16 Nov 2026, no attribution needed).
Format: 16-bit PCM, 44100 Hz; mono for takes the bank places in the world, stereo for loops, music, the Pack-Mother's calls.
Level: each family takes the mean LUFS of its nearest banked neighbour (column `neighbour`); music = the title bed +2 LU;
`limited` = the take would have passed -1 dBFS, so its gain was capped there.

| family_take | source file | s | kind | ch | raw LUFS | out LUFS | target | peak dBFS | limited | neighbour |
|---|---|---|---|---|---|---|---|---|---|---|
| den_ambience_0 | Ambience Loop.wav | 20.30 | loop | 2 | -53.9 | -35.3 | -33.0 | -1.0 | yes | bed_deepshaw_night |
| den_pits_0 | Green pits loop.wav | 8.54 | loop | 2 | -38.2 | -25.6 | -25.6 | -7.8 |  | bed_fire |
| den_pack_far_0 | pack at a distance.wav | 24.98 | shot | 2 | -25.8 | -33.0 | -33.0 | -8.2 |  | bed_deepshaw_night |
| music_den_explore_0 | Music den exploration track.wav | 100.49 | music | 2 | -19.8 | -31.0 | -31.0 | -11.1 |  | bed_title |
| music_den_boss_0 | Music den boss fight.wav | 51.83 | music | 2 | -16.7 | -31.0 | -31.0 | -14.8 |  | bed_title |
| music_den_falls_0 | Music boss falls.wav | 6.00 | sting | 2 | -18.8 | -33.0 | -33.0 | -17.6 |  | bed_title |
| voice_wolf_notice_0 | wolf notice1.wav | 1.79 | shot | 1 | -14.6 | -19.9 | -19.9 | -5.4 |  | kill_hide |
| voice_wolf_notice_1 | wolf notice2.wav | 0.88 | shot | 1 | -15.7 | -19.9 | -19.9 | -5.4 |  | kill_hide |
| voice_wolf_lunge_0 | wolf lunge1.wav | 0.88 | shot | 1 | -15.7 | -19.9 | -19.9 | -5.4 |  | kill_hide |
| voice_wolf_lunge_1 | wolf lunge2.wav | 0.56 | shot | 1 | -20.6 | -19.9 | -19.9 | -2.1 |  | kill_hide |
| voice_wolf_hurt_0 | wolf hurtyelp 1.wav | 0.35 | shot | 1 | -13.8 | -22.7 | -22.7 | -9.8 |  | hurt_her |
| voice_wolf_death_0 | wolf death1.wav | 0.61 | shot | 1 | -27.0 | -19.9 | -19.9 | -10.0 |  | kill_hide |
| voice_wolfb_notice_0 | blight wolf notice1.wav | 2.00 | shot | 1 | -14.2 | -19.9 | -19.9 | -5.7 |  | kill_hide |
| voice_wolfb_notice_1 | blight wolf notice2.wav | 2.90 | shot | 1 | -22.3 | -19.9 | -19.9 | -5.7 |  | kill_hide |
| voice_wolfb_notice_2 | Blight wolf notice3.wav | 2.00 | shot | 1 | -14.2 | -19.9 | -19.9 | -5.7 |  | kill_hide |
| voice_wolfb_bite_0 | blight wolf bite 1.wav | 1.83 | shot | 1 | -18.3 | -19.9 | -19.9 | -3.5 |  | kill_hide |
| voice_wolfb_bite_1 | Blight wolf bite2.wav | 1.48 | shot | 1 | -14.4 | -19.9 | -19.9 | -5.5 |  | kill_hide |
| voice_wolfb_lunge_0 | blight wolf lunge1.wav | 1.81 | shot | 1 | -18.4 | -19.9 | -19.9 | -2.3 |  | kill_hide |
| voice_wolfb_lunge_1 | blight wolf lunge2.wav | 1.19 | shot | 1 | -16.5 | -19.9 | -19.9 | -4.9 |  | kill_hide |
| voice_wolfb_hurt_0 | blight wolf hurtyelp1.wav | 0.58 | shot | 1 | -12.9 | -22.7 | -22.7 | -12.0 |  | hurt_her |
| voice_wolfb_death_0 | blight wolf death1.wav | 0.61 | shot | 1 | -14.5 | -19.9 | -19.9 | -6.4 |  | kill_hide |
| voice_boar_notice_0 | Thicket tusker snort1.wav | 1.94 | shot | 1 | -26.7 | -19.9 | -19.9 | -1.9 |  | kill_hide |
| voice_boar_bite_0 | thicket tusker grunt1.wav | 2.00 | shot | 1 | -36.8 | -20.0 | -19.9 | -1.0 | yes | kill_hide |
| voice_boar_lunge_0 | Thicket tusker charge.wav | 4.00 | shot | 1 | -15.0 | -19.9 | -19.9 | -5.9 |  | kill_hide |
| voice_boar_death_0 | Thicket tusker death.wav | 3.47 | shot | 1 | -15.1 | -19.9 | -19.9 | -6.1 |  | kill_hide |
| voice_yearling_notice_0 | Pack-Mother's Yearling notice1.wav | 1.14 | shot | 1 | -20.0 | -19.9 | -19.9 | -2.6 |  | kill_hide |
| voice_yearling_bite_0 | Pack-Mother's Yearling bite1.wav | 1.01 | shot | 1 | -17.3 | -19.9 | -19.9 | -3.6 |  | kill_hide |
| voice_yearling_bite_1 | Pack-Mother's Yearling bite2.wav | 0.97 | shot | 1 | -15.7 | -19.9 | -19.9 | -5.3 |  | kill_hide |
| voice_yearling_lunge_0 | Pack-Mother's Yearling lunge1.wav | 1.69 | shot | 1 | -10.4 | -19.9 | -19.9 | -9.4 |  | kill_hide |
| voice_yearling_lunge_1 | Pack-Mother's Yearling lunge2.wav | 1.65 | shot | 1 | -18.6 | -19.9 | -19.9 | -2.5 |  | kill_hide |
| voice_yearling_hurt_0 | Pack-Mother's yearling hurtyelp1.wav | 0.61 | shot | 1 | -13.1 | -22.7 | -22.7 | -10.1 |  | hurt_her |
| voice_yearling_death_0 | Pack-Mother's yearling death1.wav | 1.76 | shot | 1 | -21.7 | -19.9 | -19.9 | -3.9 |  | kill_hide |
| voice_packmother_arrival_0 | Pack Mother arrival howl.wav | 8.00 | shot | 2 | -13.8 | -16.0 | -16.0 | -3.2 |  | boss_arrive |
| voice_packmother_drive_0 | The Pack mother the drive.wav | 4.96 | shot | 2 | -18.2 | -18.7 | -16.0 | -1.0 | yes | boss_arrive |
| voice_packmother_hamstring_0 | The Pack mother hamstring.wav | 1.52 | shot | 2 | -14.8 | -16.0 | -16.0 | -2.2 |  | boss_arrive |
| voice_packmother_moonhowl_0 | The Pack mother moon-howl.wav | 5.50 | shot | 2 | -15.7 | -16.0 | -16.0 | -1.4 |  | boss_arrive |
| voice_packmother_phase_0 | The Pack mother phase change.wav | 6.00 | shot | 2 | -11.7 | -16.0 | -16.0 | -5.2 |  | boss_arrive |
| voice_packmother_call_0 | The Pack mother the call that brings wolves.wav | 4.73 | shot | 2 | -14.7 | -16.0 | -16.0 | -5.0 |  | boss_arrive |
| voice_packmother_death_0 | The Pack mother death.wav | 4.72 | shot | 2 | -13.9 | -14.0 | -13.3 | -1.0 | yes | boss_down |
| her_grunt_0 | her swing grunt1.wav | 0.28 | shot | 1 | -20.0 | -22.7 | -22.7 | -4.0 |  | hurt_her |
| her_grunt_1 | her swing grunt2.wav | 0.34 | shot | 1 | -16.7 | -22.7 | -22.7 | -7.0 |  | hurt_her |
| her_grunt_2 | her swing grunt3.wav | 0.27 | shot | 1 | -24.8 | -22.7 | -22.7 | -5.9 |  | hurt_her |
| her_grunt_3 | her swing grunt4.wav | 0.28 | shot | 1 | -23.4 | -22.7 | -22.7 | -6.8 |  | hurt_her |
| her_leap_0 | her leap1.wav | 0.59 | shot | 1 | -13.4 | -22.7 | -22.7 | -10.4 |  | hurt_her |
| her_leap_1 | her leap2.wav | 1.24 | shot | 1 | -15.1 | -22.7 | -22.7 | -8.4 |  | hurt_her |
| her_leap_2 | her leap3.wav | 1.19 | shot | 1 | -14.1 | -22.7 | -22.7 | -11.3 |  | hurt_her |
| her_leap_3 | her leap4.wav | 1.24 | shot | 1 | -12.6 | -22.7 | -22.7 | -11.5 |  | hurt_her |
| her_land_0 | her landing1.wav | 0.87 | shot | 1 | -16.0 | -20.3 | -20.3 | -4.7 |  | hard_landing |
| her_land_1 | her landing2.wav | 0.60 | shot | 1 | -15.7 | -20.3 | -20.3 | -5.7 |  | hard_landing |
| her_land_2 | her landing3.wav | 0.66 | shot | 1 | -14.9 | -20.3 | -20.3 | -5.4 |  | hard_landing |
| her_dodge_0 | her dodge1.wav | 0.47 | shot | 1 | -21.3 | -22.7 | -22.7 | -8.3 |  | hurt_her |
| her_dodge_1 | her dodge2.wav | 0.35 | shot | 1 | -20.0 | -22.7 | -22.7 | -9.1 |  | hurt_her |
| her_perfect_0 | her perfect.wav | 2.31 | shot | 1 | -17.2 | -22.7 | -22.7 | -9.3 |  | hurt_her |
| her_stance_0 | Stance1.wav | 1.25 | shot | 1 | -19.8 | -22.7 | -22.7 | -4.6 |  | hurt_her |
| her_stance_1 | Stance2.wav | 1.44 | shot | 1 | -14.3 | -22.7 | -22.7 | -9.9 |  | hurt_her |
| her_heartbeat_0 | low-health-heartbeat#0.wav | 0.95 | shot | 1 | -24.1 | -22.7 | -22.7 | -1.5 |  | hurt_her |
| her_heartbeat_1 | low-health-heartbeat#1.wav | 0.95 | shot | 1 | -23.8 | -22.7 | -22.7 | -1.5 |  | hurt_her |
| her_heartbeat_2 | low-health-heartbeat#2.wav | 0.95 | shot | 1 | -23.8 | -22.8 | -22.7 | -1.0 | yes | hurt_her |
| her_heartbeat_3 | low-health-heartbeat#3.wav | 0.95 | shot | 1 | -23.6 | -22.7 | -22.7 | -1.3 |  | hurt_her |

## Loops: the seam, by measurement

Cut: where the tail best continues the head (normalised cross-correlation `corr`, 1 = identical); the head is cross-faded in over the tail for `xfade`
seconds so the sample after the last is the original signal's own next one. `step/median`: the jump across the seam over the signal's median
sample step (information), and `step/p99`: over the signal's 99th-percentile step (gate: at most 1, the seam is no bigger a jump than the signal makes by itself every few milliseconds). `rms 50 ms` and `rms 3 s`: the level just before the end and just after the start
(both within 1.5 dB = no swell or beat lost at the join). `spec`: mean band-by-band difference of the 200 ms either side (gate under 6 dB).

| family | length s | cut at s | corr | xfade s | step/median | step/p99 | rms 50 ms before / after | rms 3 s before / after | spec dB |
|---|---|---|---|---|---|---|---|---|---|
| den_ambience | 20.30 | 20.30 | 0.11 | 1.5 | 0.51 | 0.04 | -55.9 / -55.4 | -55.6 / -54.3 | 3.5 |
| den_pits | 8.54 | 8.54 | 0.58 | 1.5 | 0.17 | 0.03 | -35.3 / -37.1 | -36.3 / -35.4 | 5.1 |
| music_den_explore | 100.49 | 100.49 | 0.16 | 6.0 | 8.91 | 0.71 | -16.4 / -12.7 | -18.3 / -18.5 | 3.1 |
| music_den_boss | 51.83 | 51.83 | 0.11 | 6.0 | 4.20 | 0.54 | -15.6 / -13.4 | -14.8 / -15.9 | 2.8 |

Seam gate: all loops pass.
