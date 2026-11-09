# Evaluation report

Runs: 1, 2
Same offer in every run (consistency): 17/18 (94%)

| Metric | run 1 (all) | run 2 (all) | run 2: dev | run 2: held-out |
|---|---|---|---|---|
| Runs (e-mail × run) | 20 | 20 | 7 | 13 |
| Errors | 1 | 0 | 0 | 0 |
| Request detected correctly | 19/19 (100%) | 20/20 (100%) | 7/7 (100%) | 13/13 (100%) |
| Machine model extracted | 18/18 (100%) | 18/19 (95%) | 7/7 (100%) | 11/12 (92%) |
| Urgency extracted | 18/18 (100%) | 19/19 (100%) | 7/7 (100%) | 12/12 (100%) |
| Language detected | 18/18 (100%) | 19/19 (100%) | 7/7 (100%) | 12/12 (100%) |
| Number of requested items | 18/18 (100%) | 19/19 (100%) | 7/7 (100%) | 12/12 (100%) |
| Expected parts found | 18/21 (86%) | 21/22 (95%) | 9/10 (90%) | 12/12 (100%) |
| Expected parts with correct quantity | 18/21 (86%) | 21/22 (95%) | 9/10 (90%) | 12/12 (100%) |
| Wrong parts offered (total) | 0 | 0 | 0 | 0 |
| Offer exactly right | 16/18 (89%) | 18/19 (95%) | 6/7 (86%) | 12/12 (100%) |
| Asked customer when needed (and only then) | 15/16 (94%) | 16/17 (94%) | 6/6 (100%) | 10/11 (91%) |
| Urgency warning correct | 18/18 (100%) | 19/19 (100%) | 7/7 (100%) | 12/12 (100%) |
| Avg tokens per e-mail | 7,867 | 7,923 | 9,352 | 7,153 |
| Avg LLM calls per e-mail | 5.5 | 5.5 | 6.1 | 5.1 |
| Avg seconds per e-mail | 28.1 | 31.8 | 40.4 | 27.1 |

## Per e-mail

| Run | Id | Split | Offer exact | Asked ok | Wrong parts | Offered | Extraction issues | Note |
|---|---|---|---|---|---|---|---|---|
| 1 | 001 | dev | yes | yes | 0 | HPC-SEA-110×2 | – | Simple request with exact part number. |
| 1 | 002 | dev | yes | yes | 0 | H2D-BRK-303×1 | – | No part number, urgent, out of stock. |
| 1 | 003 | dev | yes | yes | 0 | HPC-VLV-202×1 | – | Wrong part number HPC-VLV-220; correct part found by name, customer must confirm. |
| 1 | 004 | dev | yes | yes | 0 | HPC-FLT-131×4, HPC-FLT-130×4, HPC-LUB-140×2 | – | Three parts, mixed language. |
| 1 | 005 | dev | yes | yes | 0 | none | – | Ambiguous: check valve DN6 or DN10. Must not guess. |
| 1 | 006 | dev | NO | – | 0 | HPU-SEA-404×2 | – | Valve quantity implicit ('das Ventil' = 1). |
| 1 | 007 | dev | yes | yes | 0 | HPC-FLT-131×10, HPC-SNS-150×1 | – | Part number with spaces; one item out of stock, not urgent. |
| 1 | 008 | test | yes | yes | 0 | HPC-MEC-260×3 | – | Same part name exists for HPC-300 and HPC-500; out of stock, not urgent. |
| 1 | 009 | test | yes | yes | 0 | HPC-SAF-270×1 | – | Urgent but in stock: no attention flag. |
| 1 | 010 | test | yes | yes | 0 | H2D-SEA-350×5 | – | Exact part number, no machine model. |
| 1 | 011 | test | yes | yes | 0 | none | – | Part not in catalog: must not offer a wrong part. |
| 1 | 012 | test | yes | yes | 0 | H2D-NOZ-701×1 | – | Wrong part number H2D-NOZ-710; customer must confirm. |
| 1 | 013 | test | yes | yes | 0 | H2D-FLT-340×2, H2D-SNS-330×1 | – | Two parts, mixed language. |
| 1 | 014 | test | not a request: ok | | | | | Event invitation, not a spare-part request. |
| 1 | 015 | test | ERROR | | | BadRequestError: Error code: 400 - Tool call validation fail | | Urgent, station down, out of stock. |
| 1 | 016 | test | yes | yes | 0 | HPC-SEA-210×3 | – | Partial stock: 1 available, 2 to order. |
| 1 | 017 | test | yes | yes | 0 | none | – | Suction valve exists for HPC-300 and HPC-500; machine model missing, must ask. |
| 1 | 018 | test | NO | NO | 0 | none | – | Informal, typos, lower case, model written as 'hpc300'. |
| 1 | 019 | test | yes | – | 0 | HPU-PMP-401×1 | – | Quantity implicit ('an axial piston pump' = 1); out of stock, not urgent. |
| 1 | 020 | test | yes | yes | 0 | HPC-SNS-151×4 | – | Long e-mail with irrelevant maintenance history. |
| 2 | 001 | dev | yes | yes | 0 | HPC-SEA-110×2 | – | Simple request with exact part number. |
| 2 | 002 | dev | yes | yes | 0 | H2D-BRK-303×1 | – | No part number, urgent, out of stock. |
| 2 | 003 | dev | yes | yes | 0 | HPC-VLV-202×1 | – | Wrong part number HPC-VLV-220; correct part found by name, customer must confirm. |
| 2 | 004 | dev | yes | yes | 0 | HPC-FLT-131×4, HPC-FLT-130×4, HPC-LUB-140×2 | – | Three parts, mixed language. |
| 2 | 005 | dev | yes | yes | 0 | none | – | Ambiguous: check valve DN6 or DN10. Must not guess. |
| 2 | 006 | dev | NO | – | 0 | HPU-SEA-404×2 | – | Valve quantity implicit ('das Ventil' = 1). |
| 2 | 007 | dev | yes | yes | 0 | HPC-FLT-131×10, HPC-SNS-150×1 | – | Part number with spaces; one item out of stock, not urgent. |
| 2 | 008 | test | yes | yes | 0 | HPC-MEC-260×3 | – | Same part name exists for HPC-300 and HPC-500; out of stock, not urgent. |
| 2 | 009 | test | yes | yes | 0 | HPC-SAF-270×1 | – | Urgent but in stock: no attention flag. |
| 2 | 010 | test | yes | yes | 0 | H2D-SEA-350×5 | – | Exact part number, no machine model. |
| 2 | 011 | test | yes | yes | 0 | none | – | Part not in catalog: must not offer a wrong part. |
| 2 | 012 | test | yes | yes | 0 | H2D-NOZ-701×1 | – | Wrong part number H2D-NOZ-710; customer must confirm. |
| 2 | 013 | test | yes | yes | 0 | H2D-FLT-340×2, H2D-SNS-330×1 | – | Two parts, mixed language. |
| 2 | 014 | test | not a request: ok | | | | | Event invitation, not a spare-part request. |
| 2 | 015 | test | yes | NO | 0 | H2D-SNS-331×1 | machine_model=None | Urgent, station down, out of stock. |
| 2 | 016 | test | yes | yes | 0 | HPC-SEA-210×3 | – | Partial stock: 1 available, 2 to order. |
| 2 | 017 | test | yes | yes | 0 | none | – | Suction valve exists for HPC-300 and HPC-500; machine model missing, must ask. |
| 2 | 018 | test | yes | yes | 0 | HPC-FLT-131×2, HPC-FLT-130×2 | – | Informal, typos, lower case, model written as 'hpc300'. |
| 2 | 019 | test | yes | – | 0 | HPU-PMP-401×1 | – | Quantity implicit ('an axial piston pump' = 1); out of stock, not urgent. |
| 2 | 020 | test | yes | yes | 0 | HPC-SNS-151×4 | – | Long e-mail with irrelevant maintenance history. |
