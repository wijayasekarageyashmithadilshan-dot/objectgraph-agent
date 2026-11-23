# Experiment 2 (RealBench) summary

Usable tasks: 9; tasks with any condition above 0: 6.

| Task | G2 pass (k) | G4 pass (k) | GC pass (k) | G6 pass (k) | G7 pass (k) |
|---|---|---|---|---|---|
| draeician_crules | 0.80 (1) | 0.80 (2) | 0.80 (6) | 0.80 (6) | 0.80 (2) |
| salvozappa_gattino | 0.00 (1) | 0.00 (3) | 0.00 (6) | 0.00 (6) | 0.00 (3) |
| FreddyRodgers_emojichef | 0.12 (1) | 0.13 (3) | 0.00 (9) | 0.12 (4) | 0.37 (3) |
| aliyun_alibabacloud-dms-mcp-server | 0.00 (1) | 0.00 (2) | 0.00 (17) | 0.00 (10) | 0.00 (2) |
| antoine311200_torchcolor | 0.00 (1) | 0.00 (4) | 0.00 (19) | 0.00 (7) | 0.00 (4) |
| pab1it0_adx-mcp-server | 0.07 (1) | 0.01 (2) | 0.00 (4) | 0.00 (4) | 0.00 (2) |
| rileydakota_crx-analyzer | 0.32 (1) | 0.48 (3) | 0.00 (22) | 0.22 (4) | 0.48 (3) |
| Camera | 0.13 (1) | 0.13 (4) | 0.00 (5) | 0.00 (5) | 0.04 (4) |
| Reconnaissance | 0.12 (1) | 0.12 (2) | 0.21 (6) | 0.21 (6) | 0.17 (2) |

H1 primary (G7 > G4): {'n_tasks': 9, 'n_nonzero': 4, 'wins': 2, 'losses': 2, 'ties': 5, 'mean_diff': 0.0212, 'p': 0.4375, 'verdict': 'not supported'}

G7_vs_GC: {'n_tasks': 9, 'n_nonzero': 4, 'wins': 3, 'losses': 1, 'ties': 5, 'mean_diff': 0.0946, 'p': 0.375, 'p_holm': 0.75}
G7_vs_G6: {'n_tasks': 9, 'n_nonzero': 4, 'wins': 3, 'losses': 1, 'ties': 5, 'mean_diff': 0.0576, 'p': 0.375, 'p_holm': 0.75}

H2 cost: {'median_ratio_G7_over_G4': 0.7274, 'verdict': 'supported'}

Unusable tasks: level1/AasaiAlangaram__PySecOC (RealBench ships no tests for this project); level1/tcsenpai__sigmon (RealBench ships no tests for this project); level1/tsensei_Semantic-Markdown-Parser (reference code passes no test here: ma_index'
---------------- generated xml fil); level2/phihung_fh_utils (reference code passes no test here: ===
ERROR examples/demo.py
ERROR examples/de); level3/symeval (reference code passes no test here: ---- generated xml file: /tmp/tmpq9vzb152/ju); level4/integral-business-intelligence_chroma-auditor (reference code passes no test here: adb'
---------------- generated xml file: /t); level4/Crypt-Guard_CryptGuard (reference code passes no test here: yptguard/tests/test_password_utils.py
ERROR ); level4/simons-freedom_X-monitor (reference code passes no test here: junit.xml ----------------
=================)
