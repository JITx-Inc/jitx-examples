"""JS4: the LPDDR4X pin rules against AMD's own board pinouts.

Each fixture is one LPDDR4 interface of an AMD evaluation board, as AMD's
board files (or, for VCK190, AMD's tutorial constraints) place it. Every pin
was looked up in the device's AMD package file and written as its position in
the DDRMC triplet: ``NAME@bnp`` is bank ``b`` of the triplet, nibble ``n``,
pin ``p``. Signal names are canonical: DQ0 to DQ31 across both channels,
DQS and DMI by byte, CA, CK, CKE and CS with their channel.

Sources, all from AMD:

- VMK180 (XCVM1802-VSVA2197): XilinxBoardStore tag 2025.2,
  ``boards/Xilinx/vmk180/production/3.3/part0_pins.xml``.
- VCK190 (XCVC1902-VSVA2197): Vivado-Design-Tutorials tag 2025.2,
  ``Versal/Memory_and_NoC/NoC_DDRMC/Performance_Tuning/finished_design/
  design/lpddr4_mc3_vck190.xdc``.
- VPK120 (XCVP1202-VSVA2785): XilinxBoardStore tag 2025.2,
  ``boards/Xilinx/vpk120/production/1.2/part0_pins.xml``.
- VEK280 (XCVE2802-VSVH1760): XilinxBoardStore tag 2025.2,
  ``boards/Xilinx/vek280/production/1.2/part0_pins.xml``.
- Package files: ``xcvm1802vsva2197pkg.txt``, ``xcvc1902vsva2197pkg.txt``,
  ``xcvp1202vsva2785pkg.txt``, ``xcve2802vsvh1760pkg.txt`` from AMD's Versal
  package pinout downloads.

The board files and tutorial are Apache-2.0. VMK180, VCK190 and VPK120 use
the standard dual channel pinout; VEK280 uses the pin efficient one. Every
board places its interfaces flipped except VEK280's triplets M0 and M1.
"""

from collections.abc import Mapping
from math import factorial

from jitx.test import TestCase

from jitxexamples.jumpstart_kits.js4_fpga_lpddr4x.pinout import (
    OPTIMUM_CH1,
    OPTIMUM_X32,
    OPTIMUM_X32_FLIPPED,
    PIN_EFFICIENT_CH0,
    PIN_EFFICIENT_CH1,
    Pos,
    assignment_count,
    nibble_violations,
)

#: (board, triplet, interface) to its pinout.
BOARD_PINOUTS: dict[tuple[str, int, str], str] = {
    ("VMK180", 1, "lpddr4_2"): (
        "CA0_A@203 CA0_B@222 CA1_A@202 CA1_B@235 CA2_A@200 CA2_B@225 CA3_A@205 "
        "CA3_B@224 CA4_A@212 CA4_B@233 CA5_A@213 CA5_B@232 CKE_A@214 CKE_B@234 "
        "CK_C_A@211 CK_C_B@231 CK_T_A@210 CK_T_B@230 CS0_A@204 CS0_B@271 "
        "CS1_A@201 CS1_B@241 DMI0@120 DMI1@240 DMI2@160 DMI3@270 DQ0@133 "
        "DQ1@132 DQ10@244 DQ11@245 DQ12@242 DQ13@254 DQ14@243 DQ15@255 DQ16@172 "
        "DQ17@165 DQ18@173 DQ19@164 DQ2@124 DQ20@174 DQ21@175 DQ22@162 DQ23@163 "
        "DQ24@273 DQ25@272 DQ26@274 DQ27@264 DQ28@263 DQ29@262 DQ3@125 DQ30@265 "
        "DQ31@275 DQ4@134 DQ5@123 DQ6@135 DQ7@122 DQ8@252 DQ9@253 DQS0_C@131 "
        "DQS0_T@130 DQS1_C@251 DQS1_T@250 DQS2_C@171 DQS2_T@170 DQS3_C@261 "
        "DQS3_T@260 RESET_N@282 "
    ),
    ("VMK180", 1, "lpddr4_3"): (
        "CA0_A@063 CA0_B@034 CA1_A@062 CA1_B@035 CA2_A@065 CA2_B@025 CA3_A@064 "
        "CA3_B@033 CA4_A@072 CA4_B@032 CA5_A@073 CA5_B@024 CKE_A@074 CKE_B@021 "
        "CK_C_A@071 CK_C_B@031 CK_T_A@070 CK_T_B@030 CS0_A@060 CS0_B@051 "
        "CS1_A@075 CS1_B@001 DMI0@050 DMI1@110 DMI2@000 DMI3@140 DQ0@042 "
        "DQ1@043 DQ10@103 DQ11@115 DQ12@112 DQ13@113 DQ14@105 DQ15@104 DQ16@014 "
        "DQ17@002 DQ18@004 DQ19@013 DQ2@054 DQ20@012 DQ21@005 DQ22@003 DQ23@015 "
        "DQ24@153 DQ25@152 DQ26@154 DQ27@142 DQ28@143 DQ29@155 DQ3@055 DQ30@144 "
        "DQ31@145 DQ4@052 DQ5@053 DQ6@044 DQ7@045 DQ8@114 DQ9@102 DQS0_C@041 "
        "DQS0_T@040 DQS1_C@101 DQS1_T@100 DQS2_C@011 DQS2_T@010 DQS3_C@151 "
        "DQS3_T@150 RESET_N@283 "
    ),
    ("VMK180", 3, "lpddr4_0"): (
        "CA0_A@203 CA0_B@222 CA1_A@202 CA1_B@235 CA2_A@200 CA2_B@225 CA3_A@205 "
        "CA3_B@224 CA4_A@212 CA4_B@233 CA5_A@213 CA5_B@232 CKE_A@214 CKE_B@234 "
        "CK_C_A@211 CK_C_B@231 CK_T_A@210 CK_T_B@230 CS0_A@204 CS0_B@271 "
        "CS1_A@201 CS1_B@241 DMI0@120 DMI1@240 DMI2@160 DMI3@270 DQ0@125 "
        "DQ1@124 DQ10@245 DQ11@244 DQ12@254 DQ13@243 DQ14@255 DQ15@242 DQ16@175 "
        "DQ17@163 DQ18@162 DQ19@174 DQ2@123 DQ20@172 DQ21@173 DQ22@164 DQ23@165 "
        "DQ24@265 DQ25@264 DQ26@272 DQ27@273 DQ28@262 DQ29@274 DQ3@122 DQ30@263 "
        "DQ31@275 DQ4@134 DQ5@135 DQ6@132 DQ7@133 DQ8@252 DQ9@253 DQS0_C@131 "
        "DQS0_T@130 DQS1_C@251 DQS1_T@250 DQS2_C@171 DQS2_T@170 DQS3_C@261 "
        "DQS3_T@260 RESET_N@282 "
    ),
    ("VMK180", 3, "lpddr4_1"): (
        "CA0_A@063 CA0_B@034 CA1_A@062 CA1_B@035 CA2_A@065 CA2_B@025 CA3_A@064 "
        "CA3_B@033 CA4_A@072 CA4_B@032 CA5_A@073 CA5_B@024 CKE_A@074 CKE_B@021 "
        "CK_C_A@071 CK_C_B@031 CK_T_A@070 CK_T_B@030 CS0_A@060 CS0_B@051 "
        "CS1_A@075 CS1_B@001 DMI0@050 DMI1@110 DMI2@140 DMI3@000 DQ0@054 "
        "DQ1@042 DQ10@114 DQ11@115 DQ12@112 DQ13@113 DQ14@105 DQ15@104 DQ16@143 "
        "DQ17@155 DQ18@142 DQ19@154 DQ2@043 DQ20@153 DQ21@152 DQ22@144 DQ23@145 "
        "DQ24@012 DQ25@004 DQ26@005 DQ27@013 DQ28@002 DQ29@014 DQ3@055 DQ30@015 "
        "DQ31@003 DQ4@053 DQ5@052 DQ6@044 DQ7@045 DQ8@102 DQ9@103 DQS0_C@041 "
        "DQS0_T@040 DQS1_C@101 DQS1_T@100 DQS2_C@151 DQS2_T@150 DQS3_C@011 "
        "DQS3_T@010 RESET_N@283 "
    ),
    ("VCK190", 1, "CH0_LPDDR4_1"): (
        "CA0_A@203 CA0_B@222 CA1_A@202 CA1_B@235 CA2_A@200 CA2_B@225 CA3_A@205 "
        "CA3_B@224 CA4_A@212 CA4_B@233 CA5_A@213 CA5_B@232 CKE_A@214 CKE_B@234 "
        "CK_C_A@211 CK_C_B@231 CK_T_A@210 CK_T_B@230 CS0_A@204 CS0_B@271 "
        "DMI0@120 DMI1@240 DMI2@160 DMI3@270 DQ0@133 DQ1@132 DQ10@244 DQ11@245 "
        "DQ12@242 DQ13@254 DQ14@243 DQ15@255 DQ16@172 DQ17@165 DQ18@173 "
        "DQ19@164 DQ2@124 DQ20@174 DQ21@175 DQ22@162 DQ23@163 DQ24@273 DQ25@272 "
        "DQ26@274 DQ27@264 DQ28@263 DQ29@262 DQ3@125 DQ30@265 DQ31@275 DQ4@134 "
        "DQ5@123 DQ6@135 DQ7@122 DQ8@252 DQ9@253 DQS0_C@131 DQS0_T@130 "
        "DQS1_C@251 DQS1_T@250 DQS2_C@171 DQS2_T@170 DQS3_C@261 DQS3_T@260 "
        "RESET_N@282 "
    ),
    ("VCK190", 1, "CH1_LPDDR4_1"): (
        "CA0_A@063 CA0_B@034 CA1_A@062 CA1_B@035 CA2_A@065 CA2_B@025 CA3_A@064 "
        "CA3_B@033 CA4_A@072 CA4_B@032 CA5_A@073 CA5_B@024 CKE_A@074 CKE_B@021 "
        "CK_C_A@071 CK_C_B@031 CK_T_A@070 CK_T_B@030 CS0_A@060 CS0_B@051 "
        "DMI0@050 DMI1@110 DMI2@000 DMI3@140 DQ0@042 DQ1@043 DQ10@103 DQ11@115 "
        "DQ12@112 DQ13@113 DQ14@105 DQ15@104 DQ16@014 DQ17@002 DQ18@004 "
        "DQ19@013 DQ2@054 DQ20@012 DQ21@005 DQ22@003 DQ23@015 DQ24@153 DQ25@152 "
        "DQ26@154 DQ27@142 DQ28@143 DQ29@155 DQ3@055 DQ30@144 DQ31@145 DQ4@052 "
        "DQ5@053 DQ6@044 DQ7@045 DQ8@114 DQ9@102 DQS0_C@041 DQS0_T@040 "
        "DQS1_C@101 DQS1_T@100 DQS2_C@011 DQS2_T@010 DQS3_C@151 DQS3_T@150 "
        "RESET_N@283 "
    ),
    ("VCK190", 3, "CH0_LPDDR4_3"): (
        "CA0_A@203 CA0_B@222 CA1_A@202 CA1_B@235 CA2_A@200 CA2_B@225 CA3_A@205 "
        "CA3_B@224 CA4_A@212 CA4_B@233 CA5_A@213 CA5_B@232 CKE_A@214 CKE_B@234 "
        "CK_C_A@211 CK_C_B@231 CK_T_A@210 CK_T_B@230 CS0_A@204 CS0_B@271 "
        "DMI0@120 DMI1@240 DMI2@160 DMI3@270 DQ0@125 DQ1@124 DQ10@245 DQ11@244 "
        "DQ12@254 DQ13@243 DQ14@255 DQ15@242 DQ16@175 DQ17@163 DQ18@162 "
        "DQ19@174 DQ2@123 DQ20@172 DQ21@173 DQ22@164 DQ23@165 DQ24@265 DQ25@264 "
        "DQ26@272 DQ27@273 DQ28@262 DQ29@274 DQ3@122 DQ30@263 DQ31@275 DQ4@134 "
        "DQ5@135 DQ6@132 DQ7@133 DQ8@252 DQ9@253 DQS0_C@131 DQS0_T@130 "
        "DQS1_C@251 DQS1_T@250 DQS2_C@171 DQS2_T@170 DQS3_C@261 DQS3_T@260 "
        "RESET_N@282 "
    ),
    ("VCK190", 3, "CH1_LPDDR4_3"): (
        "CA0_A@063 CA0_B@034 CA1_A@062 CA1_B@035 CA2_A@065 CA2_B@025 CA3_A@064 "
        "CA3_B@033 CA4_A@072 CA4_B@032 CA5_A@073 CA5_B@024 CKE_A@074 CKE_B@021 "
        "CK_C_A@071 CK_C_B@031 CK_T_A@070 CK_T_B@030 CS0_A@060 CS0_B@051 "
        "DMI0@050 DMI1@110 DMI2@140 DMI3@000 DQ0@054 DQ1@042 DQ10@114 DQ11@115 "
        "DQ12@112 DQ13@113 DQ14@105 DQ15@104 DQ16@143 DQ17@155 DQ18@142 "
        "DQ19@154 DQ2@043 DQ20@153 DQ21@152 DQ22@144 DQ23@145 DQ24@012 DQ25@004 "
        "DQ26@005 DQ27@013 DQ28@002 DQ29@014 DQ3@055 DQ30@015 DQ31@003 DQ4@053 "
        "DQ5@052 DQ6@044 DQ7@045 DQ8@102 DQ9@103 DQS0_C@041 DQS0_T@040 "
        "DQS1_C@101 DQS1_T@100 DQS2_C@151 DQS2_T@150 DQS3_C@011 DQS3_T@010 "
        "RESET_N@283 "
    ),
    ("VPK120", 0, "lpddr4_0"): (
        "CA0_A@203 CA0_B@222 CA1_A@202 CA1_B@235 CA2_A@200 CA2_B@225 CA3_A@205 "
        "CA3_B@224 CA4_A@212 CA4_B@233 CA5_A@213 CA5_B@232 CKE_A@214 CKE_B@234 "
        "CK_C_A@211 CK_C_B@231 CK_T_A@210 CK_T_B@230 CS0_A@204 CS0_B@271 "
        "CS1_A@201 CS1_B@241 DMI0@120 DMI1@240 DMI2@160 DMI3@270 DQ0@133 "
        "DQ1@132 DQ10@244 DQ11@245 DQ12@242 DQ13@254 DQ14@243 DQ15@255 DQ16@172 "
        "DQ17@165 DQ18@173 DQ19@164 DQ2@124 DQ20@174 DQ21@175 DQ22@162 DQ23@163 "
        "DQ24@273 DQ25@272 DQ26@274 DQ27@264 DQ28@263 DQ29@262 DQ3@125 DQ30@265 "
        "DQ31@275 DQ4@134 DQ5@123 DQ6@135 DQ7@122 DQ8@252 DQ9@253 DQS0_C@131 "
        "DQS0_T@130 DQS1_C@251 DQS1_T@250 DQS2_C@171 DQS2_T@170 DQS3_C@261 "
        "DQS3_T@260 RESET_N@282 "
    ),
    ("VPK120", 0, "lpddr4_1"): (
        "CA0_A@063 CA0_B@034 CA1_A@062 CA1_B@035 CA2_A@065 CA2_B@025 CA3_A@064 "
        "CA3_B@033 CA4_A@072 CA4_B@032 CA5_A@073 CA5_B@024 CKE_A@074 CKE_B@021 "
        "CK_C_A@071 CK_C_B@031 CK_T_A@070 CK_T_B@030 CS0_A@060 CS0_B@051 "
        "CS1_A@075 CS1_B@001 DMI0@050 DMI1@110 DMI2@000 DMI3@140 DQ0@042 "
        "DQ1@043 DQ10@103 DQ11@115 DQ12@112 DQ13@113 DQ14@105 DQ15@104 DQ16@014 "
        "DQ17@002 DQ18@004 DQ19@013 DQ2@054 DQ20@012 DQ21@005 DQ22@003 DQ23@015 "
        "DQ24@153 DQ25@152 DQ26@154 DQ27@142 DQ28@143 DQ29@155 DQ3@055 DQ30@144 "
        "DQ31@145 DQ4@052 DQ5@053 DQ6@044 DQ7@045 DQ8@114 DQ9@102 DQS0_C@041 "
        "DQS0_T@040 DQS1_C@101 DQS1_T@100 DQS2_C@011 DQS2_T@010 DQS3_C@151 "
        "DQS3_T@150 RESET_N@283 "
    ),
    ("VPK120", 1, "lpddr4_2"): (
        "CA0_A@203 CA0_B@222 CA1_A@202 CA1_B@235 CA2_A@200 CA2_B@225 CA3_A@205 "
        "CA3_B@224 CA4_A@212 CA4_B@233 CA5_A@213 CA5_B@232 CKE_A@214 CKE_B@234 "
        "CK_C_A@211 CK_C_B@231 CK_T_A@210 CK_T_B@230 CS0_A@204 CS0_B@271 "
        "CS1_A@201 CS1_B@241 DMI0@120 DMI1@240 DMI2@160 DMI3@270 DQ0@133 "
        "DQ1@132 DQ10@244 DQ11@245 DQ12@242 DQ13@254 DQ14@243 DQ15@255 DQ16@172 "
        "DQ17@165 DQ18@173 DQ19@164 DQ2@124 DQ20@174 DQ21@175 DQ22@162 DQ23@163 "
        "DQ24@273 DQ25@272 DQ26@274 DQ27@264 DQ28@263 DQ29@262 DQ3@125 DQ30@265 "
        "DQ31@275 DQ4@134 DQ5@123 DQ6@135 DQ7@122 DQ8@252 DQ9@253 DQS0_C@131 "
        "DQS0_T@130 DQS1_C@251 DQS1_T@250 DQS2_C@171 DQS2_T@170 DQS3_C@261 "
        "DQS3_T@260 RESET_N@282 "
    ),
    ("VPK120", 1, "lpddr4_3"): (
        "CA0_A@063 CA0_B@034 CA1_A@062 CA1_B@035 CA2_A@065 CA2_B@025 CA3_A@064 "
        "CA3_B@033 CA4_A@072 CA4_B@032 CA5_A@073 CA5_B@024 CKE_A@074 CKE_B@021 "
        "CK_C_A@071 CK_C_B@031 CK_T_A@070 CK_T_B@030 CS0_A@060 CS0_B@051 "
        "CS1_A@075 CS1_B@001 DMI0@050 DMI1@110 DMI2@000 DMI3@140 DQ0@042 "
        "DQ1@043 DQ10@103 DQ11@115 DQ12@112 DQ13@113 DQ14@105 DQ15@104 DQ16@014 "
        "DQ17@002 DQ18@004 DQ19@013 DQ2@054 DQ20@012 DQ21@005 DQ22@003 DQ23@015 "
        "DQ24@153 DQ25@152 DQ26@154 DQ27@142 DQ28@143 DQ29@155 DQ3@055 DQ30@144 "
        "DQ31@145 DQ4@052 DQ5@053 DQ6@044 DQ7@045 DQ8@114 DQ9@102 DQS0_C@041 "
        "DQS0_T@040 DQS1_C@101 DQS1_T@100 DQS2_C@011 DQS2_T@010 DQS3_C@151 "
        "DQS3_T@150 RESET_N@283 "
    ),
    ("VPK120", 2, "lpddr4_4"): (
        "CA0_A@203 CA0_B@222 CA1_A@202 CA1_B@235 CA2_A@200 CA2_B@225 CA3_A@205 "
        "CA3_B@224 CA4_A@212 CA4_B@233 CA5_A@213 CA5_B@232 CKE_A@214 CKE_B@234 "
        "CK_C_A@211 CK_C_B@231 CK_T_A@210 CK_T_B@230 CS0_A@204 CS0_B@271 "
        "CS1_A@201 CS1_B@241 DMI0@120 DMI1@240 DMI2@160 DMI3@270 DQ0@125 "
        "DQ1@124 DQ10@253 DQ11@255 DQ12@254 DQ13@243 DQ14@244 DQ15@242 DQ16@175 "
        "DQ17@163 DQ18@162 DQ19@174 DQ2@123 DQ20@172 DQ21@173 DQ22@164 DQ23@165 "
        "DQ24@275 DQ25@274 DQ26@263 DQ27@262 DQ28@265 DQ29@264 DQ3@122 DQ30@273 "
        "DQ31@272 DQ4@134 DQ5@135 DQ6@132 DQ7@133 DQ8@245 DQ9@252 DQS0_C@131 "
        "DQS0_T@130 DQS1_C@251 DQS1_T@250 DQS2_C@171 DQS2_T@170 DQS3_C@261 "
        "DQS3_T@260 RESET_N@282 "
    ),
    ("VPK120", 2, "lpddr4_5"): (
        "CA0_A@063 CA0_B@034 CA1_A@062 CA1_B@035 CA2_A@065 CA2_B@025 CA3_A@064 "
        "CA3_B@033 CA4_A@072 CA4_B@032 CA5_A@073 CA5_B@024 CKE_A@074 CKE_B@021 "
        "CK_C_A@071 CK_C_B@031 CK_T_A@070 CK_T_B@030 CS0_A@060 CS0_B@051 "
        "CS1_A@075 CS1_B@001 DMI0@050 DMI1@110 DMI2@140 DMI3@000 DQ0@054 "
        "DQ1@052 DQ10@103 DQ11@112 DQ12@115 DQ13@113 DQ14@102 DQ15@114 DQ16@143 "
        "DQ17@155 DQ18@142 DQ19@154 DQ2@042 DQ20@153 DQ21@152 DQ22@144 DQ23@145 "
        "DQ24@012 DQ25@004 DQ26@005 DQ27@013 DQ28@002 DQ29@014 DQ3@053 DQ30@015 "
        "DQ31@003 DQ4@043 DQ5@055 DQ6@044 DQ7@045 DQ8@105 DQ9@104 DQS0_C@041 "
        "DQS0_T@040 DQS1_C@101 DQS1_T@100 DQS2_C@151 DQS2_T@150 DQS3_C@011 "
        "DQS3_T@010 RESET_N@283 "
    ),
    ("VEK280", 0, "lpddr4_0"): (
        "CA0_A@001 CA1_A@084 CA2_A@083 CA3_A@051 CA4_A@061 CA5_A@082 CKE_A@085 "
        "CK_C_A@081 CK_T_A@080 CS0_A@021 DMI0@060 DMI1@050 DMI2@020 DMI3@000 "
        "DQ0@074 DQ1@073 DQ10@055 DQ11@043 DQ12@042 DQ13@054 DQ14@045 DQ15@052 "
        "DQ16@034 DQ17@024 DQ18@032 DQ19@033 DQ2@065 DQ20@035 DQ21@025 DQ22@023 "
        "DQ23@022 DQ24@005 DQ25@004 DQ26@003 DQ27@002 DQ28@013 DQ29@012 DQ3@064 "
        "DQ30@014 DQ31@015 DQ4@062 DQ5@063 DQ6@075 DQ7@072 DQ8@053 DQ9@044 "
        "DQS0_C@071 DQS0_T@070 DQS1_C@041 DQS1_T@040 DQS2_C@031 DQS2_T@030 "
        "DQS3_C@011 DQS3_T@010 RESET_N@283 "
    ),
    ("VEK280", 0, "lpddr4_1"): (
        "CA0_A@185 CA1_A@131 CA2_A@101 CA3_A@183 CA4_A@141 CA5_A@182 CKE_A@184 "
        "CK_C_A@181 CK_T_A@180 CS0_A@171 DMI0@140 DMI1@100 DMI2@170 DMI3@130 "
        "DQ0@145 DQ1@142 DQ10@115 DQ11@104 DQ12@114 DQ13@105 DQ14@113 DQ15@112 "
        "DQ16@162 DQ17@163 DQ18@175 DQ19@174 DQ2@143 DQ20@165 DQ21@164 DQ22@173 "
        "DQ23@172 DQ24@122 DQ25@124 DQ26@125 DQ27@123 DQ28@135 DQ29@134 DQ3@144 "
        "DQ30@133 DQ31@132 DQ4@153 DQ5@152 DQ6@155 DQ7@154 DQ8@102 DQ9@103 "
        "DQS0_C@151 DQS0_T@150 DQS1_C@111 DQS1_T@110 DQS2_C@161 DQS2_T@160 "
        "DQS3_C@121 DQS3_T@120 RESET_N@282 "
    ),
    ("VEK280", 1, "lpddr4_2"): (
        "CA0_A@001 CA1_A@084 CA2_A@083 CA3_A@051 CA4_A@061 CA5_A@082 CKE_A@085 "
        "CK_C_A@081 CK_T_A@080 CS0_A@021 DMI0@060 DMI1@050 DMI2@020 DMI3@000 "
        "DQ0@072 DQ1@075 DQ10@043 DQ11@044 DQ12@052 DQ13@055 DQ14@053 DQ15@054 "
        "DQ16@034 DQ17@024 DQ18@032 DQ19@033 DQ2@073 DQ20@035 DQ21@025 DQ22@023 "
        "DQ23@022 DQ24@014 DQ25@015 DQ26@004 DQ27@005 DQ28@013 DQ29@012 DQ3@074 "
        "DQ30@003 DQ31@002 DQ4@064 DQ5@065 DQ6@063 DQ7@062 DQ8@042 DQ9@045 "
        "DQS0_C@071 DQS0_T@070 DQS1_C@041 DQS1_T@040 DQS2_C@031 DQS2_T@030 "
        "DQS3_C@011 DQS3_T@010 RESET_N@283 "
    ),
    ("VEK280", 1, "lpddr4_3"): (
        "CA0_A@185 CA1_A@131 CA2_A@101 CA3_A@183 CA4_A@141 CA5_A@182 CKE_A@184 "
        "CK_C_A@181 CK_T_A@180 CS0_A@171 DMI0@140 DMI1@100 DMI2@170 DMI3@130 "
        "DQ0@142 DQ1@143 DQ10@115 DQ11@104 DQ12@114 DQ13@105 DQ14@113 DQ15@112 "
        "DQ16@162 DQ17@163 DQ18@175 DQ19@174 DQ2@144 DQ20@165 DQ21@164 DQ22@173 "
        "DQ23@172 DQ24@122 DQ25@124 DQ26@125 DQ27@123 DQ28@135 DQ29@134 DQ3@145 "
        "DQ30@133 DQ31@132 DQ4@152 DQ5@153 DQ6@154 DQ7@155 DQ8@102 DQ9@103 "
        "DQS0_C@151 DQS0_T@150 DQS1_C@111 DQS1_T@110 DQS2_C@161 DQS2_T@160 "
        "DQS3_C@121 DQS3_T@120 RESET_N@282 "
    ),
    ("VEK280", 2, "lpddr4_4"): (
        "CA0_A@271 CA1_A@284 CA2_A@283 CA3_A@221 CA4_A@211 CA5_A@282 CKE_A@285 "
        "CK_C_A@281 CK_T_A@280 CS0_A@251 DMI0@210 DMI1@220 DMI2@250 DMI3@270 "
        "DQ0@212 DQ1@204 DQ10@225 DQ11@233 DQ12@232 DQ13@224 DQ14@235 DQ15@222 "
        "DQ16@244 DQ17@254 DQ18@242 DQ19@243 DQ2@215 DQ20@245 DQ21@255 DQ22@253 "
        "DQ23@252 DQ24@264 DQ25@265 DQ26@274 DQ27@275 DQ28@263 DQ29@262 DQ3@214 "
        "DQ30@273 DQ31@272 DQ4@202 DQ5@203 DQ6@205 DQ7@213 DQ8@223 DQ9@234 "
        "DQS0_C@201 DQS0_T@200 DQS1_C@231 DQS1_T@230 DQS2_C@241 DQS2_T@240 "
        "DQS3_C@261 DQS3_T@260 RESET_N@083 "
    ),
    ("VEK280", 2, "lpddr4_5"): (
        "CA0_A@185 CA1_A@141 CA2_A@171 CA3_A@183 CA4_A@131 CA5_A@182 CKE_A@184 "
        "CK_C_A@181 CK_T_A@180 CS0_A@101 DMI0@130 DMI1@170 DMI2@100 DMI3@140 "
        "DQ0@125 DQ1@124 DQ10@163 DQ11@162 DQ12@175 DQ13@173 DQ14@174 DQ15@172 "
        "DQ16@112 DQ17@113 DQ18@105 DQ19@104 DQ2@123 DQ20@115 DQ21@114 DQ22@103 "
        "DQ23@102 DQ24@152 DQ25@154 DQ26@155 DQ27@153 DQ28@145 DQ29@144 DQ3@133 "
        "DQ30@143 DQ31@142 DQ4@122 DQ5@132 DQ6@134 DQ7@135 DQ8@165 DQ9@164 "
        "DQS0_C@121 DQS0_T@120 DQS1_C@161 DQS1_T@160 DQS2_C@111 DQS2_T@110 "
        "DQS3_C@151 DQS3_T@150 RESET_N@082 "
    ),
}

#: System clock pair of each triplet, shared by its interfaces.
SYS_CLK: dict[tuple[str, int], str] = {
    ("VMK180", 1): "SYS_CLK_P@280 SYS_CLK_N@281",
    ("VMK180", 3): "SYS_CLK_P@280 SYS_CLK_N@281",
    ("VCK190", 1): "SYS_CLK_P@280 SYS_CLK_N@281",
    ("VCK190", 3): "SYS_CLK_P@280 SYS_CLK_N@281",
    ("VPK120", 0): "SYS_CLK_P@280 SYS_CLK_N@281",
    ("VPK120", 1): "SYS_CLK_P@280 SYS_CLK_N@281",
    ("VPK120", 2): "SYS_CLK_P@280 SYS_CLK_N@281",
    ("VEK280", 0): "SYS_CLK_P@280 SYS_CLK_N@281",
    ("VEK280", 1): "SYS_CLK_P@280 SYS_CLK_N@281",
    ("VEK280", 2): "SYS_CLK_P@080 SYS_CLK_N@081",
}

#: Channel 0 of the standard pinout, checked pin for pin against the kit's
#: layout (every one is flipped).
OPTIMUM_CH0_IFACES = [
    ("VMK180", 1, "lpddr4_2"),
    ("VMK180", 3, "lpddr4_0"),
    ("VCK190", 1, "CH0_LPDDR4_1"),
    ("VCK190", 3, "CH0_LPDDR4_3"),
    ("VPK120", 0, "lpddr4_0"),
    ("VPK120", 1, "lpddr4_2"),
    ("VPK120", 2, "lpddr4_4"),
]

#: The other interfaces, checked to the nibble: (layout, flipped).
OTHER_IFACES = {
    ("VMK180", 1, "lpddr4_3"): (OPTIMUM_CH1, True),
    ("VMK180", 3, "lpddr4_1"): (OPTIMUM_CH1, True),
    ("VCK190", 1, "CH1_LPDDR4_1"): (OPTIMUM_CH1, True),
    ("VCK190", 3, "CH1_LPDDR4_3"): (OPTIMUM_CH1, True),
    ("VPK120", 0, "lpddr4_1"): (OPTIMUM_CH1, True),
    ("VPK120", 1, "lpddr4_3"): (OPTIMUM_CH1, True),
    ("VPK120", 2, "lpddr4_5"): (OPTIMUM_CH1, True),
    ("VEK280", 0, "lpddr4_0"): (PIN_EFFICIENT_CH0, False),
    ("VEK280", 0, "lpddr4_1"): (PIN_EFFICIENT_CH1, False),
    ("VEK280", 1, "lpddr4_2"): (PIN_EFFICIENT_CH0, False),
    ("VEK280", 1, "lpddr4_3"): (PIN_EFFICIENT_CH1, False),
    ("VEK280", 2, "lpddr4_4"): (PIN_EFFICIENT_CH0, True),
    ("VEK280", 2, "lpddr4_5"): (PIN_EFFICIENT_CH1, True),
}


def parse(text: str) -> dict[str, Pos]:
    out: dict[str, Pos] = {}
    for item in text.split():
        name, pos = item.split("@")
        out[name] = Pos.parse(pos)
    return out


def board_pinout(key: tuple[str, int, str]) -> dict[str, Pos]:
    board, triplet, _ = key
    return parse(BOARD_PINOUTS[key]) | parse(SYS_CLK[(board, triplet)])


def mirrored(pinout: Mapping[str, Pos]) -> dict[str, Pos]:
    return {k: v.mirrored() for k, v in pinout.items()}


def swapped(pinout: Mapping[str, Pos], pairs: list[tuple[str, str]]) -> dict[str, Pos]:
    out = dict(pinout)
    for a, b in pairs:
        out[a], out[b] = pinout[b], pinout[a]
    return out


def byte_names(byte: int) -> list[str]:
    return [
        f"DQS{byte}_T",
        f"DQS{byte}_C",
        f"DMI{byte}",
        *(f"DQ{8 * byte + i}" for i in range(8)),
    ]


class TestBoardsAreMembers(TestCase):
    """Each board interface is in the set the rules allow."""

    def test_every_fixture_is_classified(self) -> None:
        self.assertEqual(
            set(BOARD_PINOUTS), set(OPTIMUM_CH0_IFACES) | set(OTHER_IFACES)
        )
        self.assertEqual(
            {board for board, _, _ in BOARD_PINOUTS},
            {"VMK180", "VCK190", "VPK120", "VEK280"},
        )

    def test_standard_channel0_matches_the_kit_layout_pin_for_pin(self) -> None:
        for key in OPTIMUM_CH0_IFACES:
            with self.subTest(key=key):
                pinout = board_pinout(key)
                self.assertEqual(OPTIMUM_X32_FLIPPED.violations(pinout), [])
                self.assertEqual(OPTIMUM_X32.violations(mirrored(pinout)), [])

    def test_every_fixed_signal_is_on_some_board(self) -> None:
        """Signal names only: each fixed signal of the layout appears on some
        standard channel 0 board interface. Positions are checked by
        ``test_standard_channel0_matches_the_kit_layout_pin_for_pin``."""
        seen: set[str] = set()
        for key in OPTIMUM_CH0_IFACES:
            seen |= set(board_pinout(key))
        self.assertLessEqual(set(OPTIMUM_X32_FLIPPED.fixed), seen)

    def test_other_interfaces_match_their_documented_layout(self) -> None:
        for key, (layout, flipped) in OTHER_IFACES.items():
            with self.subTest(key=key):
                target = layout.mirrored() if flipped else layout
                self.assertEqual(nibble_violations(board_pinout(key), target), [])

    def test_vek280_flipped_triplet_mirrors_an_unflipped_one(self) -> None:
        """VEK280's flipped M2 interfaces, mirrored, put every non-DQ pin at
        the pin index where the unflipped M0 interfaces do (rule 15): lpddr4_5
        against lpddr4_1, and lpddr4_4 against lpddr4_0. This is the evidence
        that flipping keeps the pin within its nibble."""
        for flipped, unflipped in (("lpddr4_5", "lpddr4_1"), ("lpddr4_4", "lpddr4_0")):
            m0 = board_pinout(("VEK280", 0, unflipped))
            m2 = mirrored(board_pinout(("VEK280", 2, flipped)))
            for name in m0:
                if not name.startswith("DQ") or name.startswith("DQS"):
                    with self.subTest(pair=(flipped, unflipped), name=name):
                        self.assertEqual(m2[name], m0[name])


class TestRulesRejectAndAllow(TestCase):
    """The checker is not vacuous: it rejects broken pinouts and allows the
    documented swaps. Mutations of VMK180 lpddr4_2, mirrored."""

    def setUp(self) -> None:
        self.base = mirrored(board_pinout(("VMK180", 1, "lpddr4_2")))
        self.assertEqual(OPTIMUM_X32.violations(self.base), [])

    def test_bit_swap_within_a_byte_is_allowed(self) -> None:
        p = swapped(self.base, [("DQ0", "DQ7"), ("DQ1", "DQ4")])
        self.assertEqual(OPTIMUM_X32.violations(p), [])

    def test_byte_swap_within_a_channel_is_allowed(self) -> None:
        a = swapped(self.base, list(zip(byte_names(0), byte_names(1), strict=True)))
        b = swapped(self.base, list(zip(byte_names(2), byte_names(3), strict=True)))
        self.assertEqual(OPTIMUM_X32.violations(a), [])
        self.assertEqual(OPTIMUM_X32.violations(b), [])

    def test_byte_swap_across_channels_is_rejected(self) -> None:
        p = swapped(self.base, list(zip(byte_names(0), byte_names(2), strict=True)))
        self.assertNotEqual(OPTIMUM_X32.violations(p), [])

    def test_dq_moved_to_another_byte_is_rejected(self) -> None:
        p = swapped(self.base, [("DQ0", "DQ8")])
        self.assertNotEqual(OPTIMUM_X32.violations(p), [])

    def test_dqs_or_dmi_traded_with_a_dq_is_rejected(self) -> None:
        for a, b in (("DQS0_T", "DQ0"), ("DMI0", "DQ5")):
            with self.subTest(pair=(a, b)):
                p = swapped(self.base, [(a, b)])
                self.assertNotEqual(OPTIMUM_X32.violations(p), [])

    def test_address_swap_is_rejected(self) -> None:
        p = swapped(self.base, [("CA0_A", "CA1_A")])
        self.assertNotEqual(OPTIMUM_X32.violations(p), [])

    def test_flipped_pinout_is_not_the_non_flipped_layout(self) -> None:
        flipped = board_pinout(("VMK180", 1, "lpddr4_2"))
        self.assertNotEqual(OPTIMUM_X32.violations(flipped), [])
        self.assertNotEqual(OPTIMUM_X32_FLIPPED.violations(self.base), [])


class TestKitLayout(TestCase):
    def test_assignment_count(self) -> None:
        self.assertEqual(assignment_count(), 4 * factorial(8) ** 4)

    def test_kit_layout_uses_the_last_two_banks(self) -> None:
        banks = {p.bank for p in OPTIMUM_X32_FLIPPED.fixed.values()}
        for slot in OPTIMUM_X32_FLIPPED.slots:
            banks |= {p.bank for p in (slot.dqs_t, slot.dqs_c, slot.dmi, *slot.dq)}
        self.assertEqual(banks, {1, 2})
