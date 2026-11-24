# Experiment 2 (RealBench) summary

Usable tasks: 8; tasks with any condition above 0: 4.

| Task | G2 pass (k) | G4 pass (k) | GC pass (k) | G6 pass (k) | G7 pass (k) |
|---|---|---|---|---|---|
| draeician_crules | 0.80 (1) | 0.87 (2) | 0.60 (6) | 0.60 (6) | 0.60 (2) |
| salvozappa_gattino | 0.69 (1) | 0.69 (3) | 0.69 (6) | 0.69 (6) | 0.69 (3) |
| FreddyRodgers_emojichef | 0.00 (1) | 0.16 (3) | 0.00 (9) | 0.15 (4) | 0.00 (3) |
| aliyun_alibabacloud-dms-mcp-server | 0.00 (1) | 0.00 (2) | 0.00 (17) | 0.00 (10) | 0.00 (2) |
| antoine311200_torchcolor | 0.00 (1) | 0.00 (4) | 0.00 (19) | 0.00 (7) | 0.00 (4) |
| pab1it0_adx-mcp-server | 0.00 (1) | 0.00 (2) | 0.00 (4) | 0.00 (4) | 0.00 (2) |
| rileydakota_crx-analyzer | 0.00 (1) | 0.00 (3) | 0.00 (22) | 0.00 (4) | 0.00 (3) |
| Reconnaissance | 0.00 (1) | 0.00 (2) | 0.20 (6) | 0.20 (6) | 0.00 (2) |

H1 primary (G7 > G4): {'n_tasks': 8, 'n_nonzero': 2, 'wins': 0, 'losses': 2, 'ties': 6, 'mean_diff': -0.0533, 'p': 1.0, 'verdict': 'not supported'}

G7_vs_G2: {'n_tasks': 8, 'n_nonzero': 1, 'wins': 0, 'losses': 1, 'ties': 7, 'mean_diff': -0.025, 'p': 1.0, 'p_holm': 1.0}
G7_vs_GC: {'n_tasks': 8, 'n_nonzero': 1, 'wins': 0, 'losses': 1, 'ties': 7, 'mean_diff': -0.025, 'p': 1.0, 'p_holm': 1.0}
G7_vs_G6: {'n_tasks': 8, 'n_nonzero': 2, 'wins': 0, 'losses': 2, 'ties': 6, 'mean_diff': -0.0433, 'p': 0.5, 'p_holm': 1.0}

H2 cost: {'median_ratio_G7_over_G4': 0.5915, 'verdict': 'supported'}

Unusable tasks: level1/AasaiAlangaram__PySecOC (RealBench ships no tests for this project); level1/tcsenpai__sigmon (RealBench ships no tests for this project); level1/tsensei_Semantic-Markdown-Parser (reference code passes no test here: ma_index'
---------------- generated xml fil); level2/phihung_fh_utils (reference code passes no test here: ===
ERROR examples/demo.py
ERROR examples/de); level3/symeval (reference code passes no test here: ---- generated xml file: /tmp/tmpq9vzb152/ju); level4/integral-business-intelligence_chroma-auditor (reference code passes no test here: adb'
---------------- generated xml file: /t); level4/Crypt-Guard_CryptGuard (reference code passes no test here: yptguard/tests/test_password_utils.py
ERROR ); level4/simons-freedom_X-monitor (reference code passes no test here: junit.xml ----------------
=================)
