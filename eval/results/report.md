# Evaluation report

Runs: 1
Same offer in every run (consistency): –

| Metric | dev (e-mails 001–007) | held-out (e-mails 008–020) | all |
|---|---|---|---|
| Runs (e-mail × run) | 7 | 13 | 20 |
| Errors | 0 | 1 | 1 |
| Request detected correctly | 7/7 (100%) | 12/12 (100%) | 19/19 (100%) |
| Machine model extracted | 7/7 (100%) | 11/11 (100%) | 18/18 (100%) |
| Urgency extracted | 7/7 (100%) | 11/11 (100%) | 18/18 (100%) |
| Language detected | 7/7 (100%) | 11/11 (100%) | 18/18 (100%) |
| Number of requested items | 7/7 (100%) | 11/11 (100%) | 18/18 (100%) |
| Expected parts found | 9/10 (90%) | 9/11 (82%) | 18/21 (86%) |
| Expected parts with correct quantity | 9/10 (90%) | 9/11 (82%) | 18/21 (86%) |
| Wrong parts offered (total) | 0 | 0 | 0 |
| Offer exactly right | 6/7 (86%) | 10/11 (91%) | 16/18 (89%) |
| Asked customer when needed (and only then) | 6/6 (100%) | 9/10 (90%) | 15/16 (94%) |
| Urgency warning correct | 7/7 (100%) | 11/11 (100%) | 18/18 (100%) |
| Avg tokens per e-mail | 9,118 | 7,138 | 7,867 |
| Avg LLM calls per e-mail | 6.0 | 5.2 | 5.5 |
| Avg seconds per e-mail | 32.4 | 25.5 | 28.1 |

## Per e-mail

| Run | Id | Split | Offer exact | Asked ok | Wrong parts | Offered | Note |
|---|---|---|---|---|---|---|---|
| 1 | 001 | dev | yes | yes | 0 | HPC-SEA-110×2 | Simple request with exact part number. |
| 1 | 002 | dev | yes | yes | 0 | H2D-BRK-303×1 | No part number, urgent, out of stock. |
| 1 | 003 | dev | yes | yes | 0 | HPC-VLV-202×1 | Wrong part number HPC-VLV-220; correct part found by name, customer must confirm. |
| 1 | 004 | dev | yes | yes | 0 | HPC-FLT-131×4, HPC-FLT-130×4, HPC-LUB-140×2 | Three parts, mixed language. |
| 1 | 005 | dev | yes | yes | 0 | none | Ambiguous: check valve DN6 or DN10. Must not guess. |
| 1 | 006 | dev | NO | – | 0 | HPU-SEA-404×2 | Valve quantity implicit ('das Ventil' = 1). |
| 1 | 007 | dev | yes | yes | 0 | HPC-FLT-131×10, HPC-SNS-150×1 | Part number with spaces; one item out of stock, not urgent. |
| 1 | 008 | test | yes | yes | 0 | HPC-MEC-260×3 | Same part name exists for HPC-300 and HPC-500; out of stock, not urgent. |
| 1 | 009 | test | yes | yes | 0 | HPC-SAF-270×1 | Urgent but in stock: no attention flag. |
| 1 | 010 | test | yes | yes | 0 | H2D-SEA-350×5 | Exact part number, no machine model. |
| 1 | 011 | test | yes | yes | 0 | none | Part not in catalog: must not offer a wrong part. |
| 1 | 012 | test | yes | yes | 0 | H2D-NOZ-701×1 | Wrong part number H2D-NOZ-710; customer must confirm. |
| 1 | 013 | test | yes | yes | 0 | H2D-FLT-340×2, H2D-SNS-330×1 | Two parts, mixed language. |
| 1 | 014 | test | not a request: ok | | | | Event invitation, not a spare-part request. |
| 1 | 015 | test | ERROR | | | BadRequestError: Error code: 400 - Tool call validation fail | Urgent, station down, out of stock. |
| 1 | 016 | test | yes | yes | 0 | HPC-SEA-210×3 | Partial stock: 1 available, 2 to order. |
| 1 | 017 | test | yes | yes | 0 | none | Suction valve exists for HPC-300 and HPC-500; machine model missing, must ask. |
| 1 | 018 | test | NO | NO | 0 | none | Informal, typos, lower case, model written as 'hpc300'. |
| 1 | 019 | test | yes | – | 0 | HPU-PMP-401×1 | Quantity implicit ('an axial piston pump' = 1); out of stock, not urgent. |
| 1 | 020 | test | yes | yes | 0 | HPC-SNS-151×4 | Long e-mail with irrelevant maintenance history. |
