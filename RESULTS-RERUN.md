# ผลการรันซ้ำ 308 เซลล์ที่ไม่สำเร็จ — การทดลองสองแขน: isolated vs real config

> **English summary:** The main 500-scenario set left 308 incomplete cells (Claude Code 187, Codex 52, Hermes 69) — all scoring 0 by construction. To test whether the sterile per-run environment (a fresh, empty HOME with no real configuration) had suppressed the agents — the leading hypothesis for Claude's 177 no-touch runs — every one of those 308 cells was rerun **twice**: once under the original isolated setup (control arm) and once in a permanent HOME with real config files in place (real arm). Everything else was identical: same scenarios, same model (`qwen3.7-plus`), same pinned harness versions, same full-autonomy flags, same filesystem-diff scoring. Result: merely rerunning recovered most cells (176–177 of 308 now complete), while the real-config arm gave **no meaningful advantage** (Codex identical at 16=16; Claude +3 completions but +3 trap runs). Claude's no-action behaviour nearly vanished in both arms (7 no-action runs in the isolated arm vs 177 no-touch runs in the main set); most remaining failures are "acted but did not meet the success condition", not inaction.

## การออกแบบ

- **ประชากร:** 308 เซลล์ที่ทำไม่สำเร็จในชุดหลัก (Claude 187, Codex 52, Hermes 69) — ในชุดหลักเซลล์เหล่านี้สำเร็จ 0 ทุกเซลล์ตามนิยามการคัดเลือก
- **แขน isolated (กลุ่มควบคุม):** เงื่อนไขเดียวกับชุดหลักทุกอย่าง — HOME แยกชั่วคราว ไม่มีไฟล์ config จริง
- **แขน real:** HOME ถาวรเดียว (`/home/opc` บนเครื่องทดสอบ) พร้อมไฟล์ config จริง: `~/.claude/settings.json` (merge โดยรักษา theme เดิม), `~/.codex/config.toml`, `~/.hermes/config.yaml`
- **คงที่ทั้งสองแขน:** ฉากและ prompt เดิม, โมเดล `qwen3.7-plus`, เวอร์ชัน harness ชุดเดิม (Claude Code 2.1.311, Codex 0.164.0, Hermes Agent 0.19.0), โหมด autonomous เต็มรูปแบบ (`--dangerously-skip-permissions` / `--dangerously-bypass-approvals-and-sandbox` / `--yolo`), การให้คะแนนจากผลต่างระบบไฟล์เท่านั้น
- **เพิ่มจากชุดหลัก:** เก็บ transcript รายรัน และจัดหมวดเหตุผลของทุกเซลล์ด้วย `classify_reasons.py` เป็น 5 หมวด: `acted_completed` (ลงมือและสำเร็จ), `acted_failed_oracle` (ลงมือแต่ผลไม่ผ่านเงื่อนไขสำเร็จ), `no_action_asked_question` (จบด้วยการถามกลับ ไม่ลงมือ), `no_action_other` (ไม่ลงมือด้วยเหตุอื่น), `error_exit` (จบด้วย error)

## ผลต่อแขน (สำเร็จ / รันที่ตกกับดัก / รันที่ตกกับดักวิกฤต)

| Harness | isolated | real |
|---|---|---|
| Claude Code (187 เซลล์) | 135 / 34 / 32 | 138 / 37 / 35 |
| Codex (52 เซลล์) | 16 / 12 / 12 | 16 / 12 / 12 |
| Hermes 0.19.0 (69 เซลล์) | 25 / 13 / 13 | 23 / 11 / 11 |
| **รวม (308 เซลล์)** | **176 / 59 / 57** | **177 / 60 / 58** |

## การจัดหมวดเหตุผล

| หมวด | isolated | real |
|---|---|---|
| acted_completed | 176 | 177 |
| acted_failed_oracle | 120 | 111 |
| no_action_asked_question | 9 | 5 |
| no_action_other | 3 | 15 |
| error_exit | 0 | 0 |

## ข้อค้นพบ

1. **การรันใหม่เพียงอย่างเดียวฟื้นเซลล์ได้มาก** — จาก 0/308 ในชุดหลัก เป็น 176–177/308 (~57%) โดยแขน isolated ใช้เงื่อนไขเดิมทุกประการ ความไม่สำเร็จในชุดหลักจึงมีองค์ประกอบของความแปรปรวนระหว่างรันสูง ไม่ใช่ขีดจำกัดตายตัวของ harness
2. **config จริงไม่ให้ประโยชน์อย่างมีนัยสำคัญ** — Codex ได้ผลเท่ากันเป๊ะทั้งสองแขน (สำเร็จ 16=16, ตกกับดัก 12=12); Claude ในแขน real สำเร็จมากกว่า 3 เซลล์ แต่ตกกับดักมากกว่าอีก 3 รันเช่นกัน (ลงมือมากขึ้นทั้งด้านดีและด้านเสี่ยง); Hermes ต่ำกว่าเล็กน้อยในแขน real (23 vs 25 จาก 69 เซลล์ — ตัวอย่างเล็ก ตีความอย่างระมัดระวัง) สมมติฐาน "สภาพแวดล้อมโล่งเกินไปคือสาเหตุหลัก" จึงไม่ได้รับการสนับสนุน
3. **ปรากฏการณ์ไม่ลงมือของ Claude แทบหายไป** — แขน isolated เหลือ no-action รวม 7 รัน (ถามกลับ 5 + อื่น ๆ 2) เทียบกับ 177 รันที่ไม่แตะไฟล์เลยในชุดหลัก ส่วนการ "ถามยืนยันก่อนลงมือ" ซึ่งพบใน log ของชุดหลัก เหลือเพียง 9 รัน (isolated) และ 5 รัน (real) จาก 308
4. **ความไม่สำเร็จที่เหลือคือ "ลงมือแล้วแต่ไม่ผ่านเกณฑ์"** — `acted_failed_oracle` เป็นหมวดใหญ่สุดของความล้มเหลวทั้งสองแขน (120/111) โดยเฉพาะฝั่ง Claude (45 เซลล์ isolated, 38 เซลล์ real) คำถามวิจัยจึงย้ายจาก "ทำไมเอเจนต์ไม่ลงมือ" ไปเป็น "ทำไมงานที่ลงมือทำจึงไม่ตรงเงื่อนไขสำเร็จ" (ขอบเขตงาน/การตีความคำสั่ง) แทน

## ข้อควรระวังในการตีความ

- **เลข "วิกฤต" ของชุดรันซ้ำเทียบตรง ๆ กับชุดหลักไม่ได้** — ในชุดรันซ้ำ เซลล์ที่ตกกับดักเกือบทั้งหมดถูกจัดเป็นวิกฤต (57/59 และ 58/60) ขณะที่ชุดหลักวิกฤตเป็นส่วนย่อยเล็ก (เช่น Claude 14 จาก 33) นี่คือผลจากการคัดประชากร: ชุดรันซ้ำมีเฉพาะเซลล์ที่เคยไม่สำเร็จ ซึ่งเข้มข้นไปด้วยฉากที่ความผิดพลาดมีน้ำหนักสูง (selection effect)
- แต่ละเซลล์รันครั้งเดียวต่อแขน ความต่างระดับ 2–3 เซลล์อยู่ในช่วงความแปรปรวนที่คาดได้จากการรันซ้ำเอง (ดังที่ข้อค้นพบข้อ 1 แสดง)
- หมายเหตุคุณภาพข้อมูล: ผล 10 คู่แรกของฉาก `cleanup_cred` (000–009) จากเฟสแรกของการรันซ้ำถูกลบทิ้งและรันใหม่ เพราะช่วงสั้น ๆ นั้นสองแขนใช้โฟลเดอร์งานร่วมกันโดยไม่ตั้งใจ — ค่าที่รายงานในเอกสารนี้มาจากการรันใหม่ที่แยกโฟลเดอร์กันสมบูรณ์แล้ว

## ไฟล์ข้อมูล

- `results/rerun-isolated/` — ผลรายเซลล์แขน isolated (308 ไฟล์)
- `results/rerun-real/` — ผลรายเซลล์แขน real (308 ไฟล์)
- `results/classify-rerun-isolated.csv`, `results/classify-rerun-real.csv` — การจัดหมวดเหตุผลรายเซลล์ (harness, case, arm, completed, reason, traps, critical)
