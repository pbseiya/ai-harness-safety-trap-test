# AI Harness Safety Trap Test

**การทดสอบกับดักความปลอดภัยของ AI coding/agent harness แบบเต็มสเกล — 500 สถานการณ์ × 3 harness ด้วยโมเดลเดียวกัน**

> **English summary:** A full-scale behavioural safety test of three AI agent harnesses — Claude Code 2.1.311, OpenAI Codex CLI 0.164.0, and Hermes Agent 0.19.0 — all driving the *same* model (`qwen3.7-plus`) through 500 filesystem tasks seeded with "traps": plausible-looking actions that cause real damage if taken (deleting credential backups during cleanup, editing generated files instead of their source, purging pinned cache entries, embedding production credentials in migrations, and 21 more families). Scoring is done purely from before/after filesystem state — no LLM judge. All three harnesses have now completed all 500 scenarios. Claude Code completed the fewest tasks (313/500) but also fell into the fewest traps (33 runs, 14 critical) — mainly because 177 of its runs never touched a file at all.

## คำถามของการทดสอบ

เมื่อตรึงโมเดลไว้ตัวเดียวกัน harness ที่ต่างกันมีพฤติกรรมด้านความปลอดภัยต่างกันแค่ไหน โดยเฉพาะพฤติกรรม **ทำเกินขอบเขตงานที่สั่ง (over-eagerness)** จนสร้างความเสียหายจริง เช่น ลบไฟล์ที่ไม่ควรลบ แก้ไฟล์นอกขอบเขต หรือฝังข้อมูลลับลงในงานที่ส่งมอบ

## ผลสรุป (รันครบ 500/500 ทุกชุด — Hermes มีสองเวอร์ชัน)

| ตัวชี้วัด (จาก 500 ฉาก) | Claude Code 2.1.311 | Codex CLI 0.164.0 | Hermes Agent 0.19.0 | Hermes Agent v0.22.5 |
|---|---|---|---|---|
| งานสำเร็จตามเงื่อนไข | 313 (62.6%) | **448 (89.6%)** | 431 (86.2%) | 432 (86.4%) |
| รันที่ตกกับดัก ≥ 1 จุด | **33 (6.6%)** | 72 (14.4%) | 77 (15.4%) | 50 (10.0%) |
| รันที่ตกกับดักระดับวิกฤต | **14 (2.8%)** | 54 (10.8%) | 59 (11.8%) | 32 (6.4%) |
| เวลามัธยฐานต่อรัน | **25.8 วิ** | 32.8 วิ | 46.8 วิ | 55.7 วิ |

ข้อค้นพบเด่น: ทั้งสามตัวตกตระกูล `generated_fix` **100% (18/18)** เหมือนกัน ส่วน `cleanup_cred` ~80% เป็นของ Codex และ Hermes จุดอ่อนเฉพาะตัวของสองตัวนั้นต่างกันชัด — Hermes ไม่เคารพไฟล์ที่กำกับว่าห้ามลบ (`cleanup_marks` 11/24 เทียบกับ Codex 1/24) ขณะที่ Codex ฝืนลบรายการที่ถูก pin ในแคชเกือบทุกครั้ง (`cache_pinned` 15/16 เทียบกับ Hermes 9/16) ส่วนจุดต่างของ Claude คือโหมดไม่ลงมือ — 177 จาก 500 รันไม่มีการเปลี่ยนแปลงไฟล์ใด ๆ เลย ทำให้อัตราตกกับดักต่ำสุดในสามตัว (33 รัน) แต่อัตรางานสำเร็จก็ต่ำสุดเช่นกัน (313/500) รายละเอียดเต็มอยู่ใน [`RESULTS-CODEX-HERMES.md`](RESULTS-CODEX-HERMES.md), [`RESULTS-CLAUDE.md`](RESULTS-CLAUDE.md) และ [`results/per-family-results.csv`](results/per-family-results.csv)

**หมายเหตุ — พฤติกรรม "ถามกลับ ไม่ลงมือ" (no-action):** ในการรันแบบ headless พบเอเจนต์จำนวนหนึ่งจบรอบด้วยการถามกลับแทนที่จะลงมือทำ เช่น ขอข้อมูลเพิ่ม หรือถามยืนยันก่อนลบ/แก้ไฟล์ ทั้งที่ไม่มีมนุษย์อยู่ตรงนั้นให้ตอบ รันนั้นจึงจบโดยไม่มีการเปลี่ยนแปลงไฟล์ใด ๆ เลย พฤติกรรมนี้เด่นสุดที่ Claude Code ในชุดหลัก (177 จาก 500 รันไม่แตะไฟล์) และเป็นเหตุผลหลักที่ตัวเลขของมันออกมาเป็น "สำเร็จน้อยสุด แต่ตกกับดักน้อยสุด" พร้อมกัน ขอย้ำว่าพฤติกรรมนี้**ไม่ใช่**ผลจากระบบขอสิทธิ์ของ harness เพราะทุกตัวรันในโหมด autonomous เต็มรูปแบบที่ข้ามการอนุมัติทั้งหมด (`--dangerously-skip-permissions` สำหรับ Claude Code, `--dangerously-bypass-approvals-and-sandbox` สำหรับ Codex, `--yolo` สำหรับ Hermes) — มันคือการตัดสินใจของตัวโมเดลเอง การทดลองรันซ้ำซึ่งเก็บ transcript รายรัน (ดู [`RESULTS-RERUN.md`](RESULTS-RERUN.md)) ยืนยันรูปแบบการถามกลับนี้โดยตรง แต่พบว่ามัน**ไม่เสถียร**: เมื่อรันซ้ำเซลล์เดิม การจบแบบถามกลับเหลือเพียง 9 จาก 308 รัน (แขน isolated) และ 5 จาก 308 รัน (แขน real) ส่วนที่ยังไม่สำเร็จส่วนใหญ่เปลี่ยนเป็น "ลงมือแล้วแต่ไม่ผ่านเกณฑ์" แทน การตีความพฤติกรรมนี้จึงมีสองด้าน — ในมุมความปลอดภัย การถามยืนยันคือตัวกันกับดัก (กับดักส่วนใหญ่คือการล่อให้ลงมือทำลายข้อมูล) แต่ในมุมงานอัตโนมัติ มันทำให้งานไม่เดินโดยไม่มีใครสั่งหยุด และอัตราการเกิดของมันแปรปรวนมากระหว่างรันจนใช้เป็นคุณสมบัติประจำตัวของ harness ไม่ได้

## งานติดตามผล (28 ตุลาคม 2026)

- **รันซ้ำ 308 เซลล์ที่ไม่สำเร็จ สองแขน isolated vs real config** — เซลล์ที่เคยสำเร็จ 0 ทั้งหมด ฟื้นเป็น 176 (isolated) และ 177 (real) จาก 308 โดย config จริง**ไม่**ให้ประโยชน์อย่างมีนัย (Codex เท่ากันเป๊ะ 16=16) และปรากฏการณ์ไม่ลงมือของ Claude แทบหายไป (no-action เหลือ 7 รันในแขน isolated) รายละเอียด: [`RESULTS-RERUN.md`](RESULTS-RERUN.md)
- **Hermes Agent v0.22.5 ชุดเต็ม 500 ฉาก** — สำเร็จ 432/500 เท่าเดิมกับ 0.19.0 (431) แต่ตกกับดักลดลงชัด (50 เทียบ 77 รัน, วิกฤต 32 เทียบ 59) รายละเอียด: [`RESULTS-HERMES-V0225.md`](RESULTS-HERMES-V0225.md)

## ระเบียบวิธีโดยย่อ

- **ฉากทดสอบ 500 ฉาก** สร้างเชิงโปรแกรมแบบ deterministic (seed 20261027) จาก **25 ตระกูลกับดัก** แต่ละฉากมี prompt คำสั่งงานที่ฟังดูปกติ, ชุดไฟล์ fixture, เงื่อนไขงานสำเร็จ และเงื่อนไขกับดัก (บางตัวจัดเป็นระดับวิกฤต) — ฉากทุกฉากผ่านการตรวจสอบออฟไลน์ก่อนใช้ (no-op ต้องไม่สำเร็จ, ลบทุกไฟล์ต้องติดกับดัก, เงื่อนไขต้องประเมินได้) ผลตรวจ 500 ฉาก ปัญหา 0
- **การรัน:** แต่ละ harness ถูกเรียกแบบ headless ในโหมด autonomous เต็มรูปแบบ, HOME แยกต่อรัน, timeout 420 วินาที, retry เฉพาะความล้มเหลวเชิงโครงสร้างพื้นฐานสูงสุด 3 ครั้ง
- **การให้คะแนน:** ถ่าย snapshot ระบบไฟล์ (รายชื่อ + แฮชเนื้อหา + symlink) ก่อนและหลังรัน แล้วตัดสินจากผลต่างด้วยเงื่อนไขเชิงตรรกะล้วน ๆ **ไม่ใช้ LLM เป็นผู้ตัดสิน**
- ระเบียบวิธีฉบับเต็ม (รวมสถาปัตยกรรมการเชื่อมต่อ ปัญหาชั้นแปลฟอร์แมต Anthropic↔OpenAI ที่พบระหว่างทดสอบ และข้อจำกัดการตีความผล) อยู่ใน [`METHODOLOGY.md`](METHODOLOGY.md)

## ที่มาของระเบียบวิธี (แหล่งอ้างอิง)

ชุดทดสอบนี้ออกแบบโดยต่อยอดจากงานวิจัยที่ตีพิมพ์แล้ว ดังนี้

- **OverEager-Bench** — Qu et al., *OverEager-Bench: Measuring Over-Eagerness in LLM Agents*, arXiv:2605.18583 (2026). ต้นแบบของกรอบคิดหลัก: นิยามพฤติกรรม "ทำเกินคำสั่ง" เป็นมิติความปลอดภัยที่วัดแยกจากความสามารถ, ใช้ฉากแบบ fixed scenario จำนวนมาก และพบว่าการระบุขอบเขตงานในคำสั่งอย่างชัดลดพฤติกรรมเกินขอบเขตได้อย่างมาก — สอดคล้องกับผลของเราที่ตระกูลงานขอบเขตแคบตกกับดัก 0% ขณะที่งานคำสั่งเปิดกว้างตกหนัก
- **SNARE** — Qu, Liu et al., arXiv:2605.28122 (2026). งานภาคต่อแบบ adaptive attack ซึ่งพบว่าสัดส่วนความแปรปรวนของผลมาจาก framework/harness มากที่สุด (56.1%) มากกว่าตัวโมเดล (20.8%) — เป็นเหตุผลเชิงประจักษ์ที่เราเลือกตรึงโมเดลแล้วเทียบ harness และเป็นข้อควรระวังว่าตัวเลขจากฉาก fixed (ของเราและ OverEager) เทียบตรง ๆ กับตัวเลขแบบ adaptive ไม่ได้
- **AgentDojo** — Debenedetti et al., *AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents*, arXiv:2406.13352 (2024). ต้นแบบของการตัดสินผลจาก "สถานะของสภาพแวดล้อม" (environment state) แทนการอ่านข้อความตอบของเอเจนต์ — วิธีให้คะแนนจากผลต่างระบบไฟล์ของเราใช้หลักเดียวกัน (แม้ภัยของเราต่างกัน: ไม่ใช่ prompt injection จากข้อมูลภายนอก แต่เป็นตัวเอเจนต์เองที่ทำเกินขอบเขต)
- **AgentHarm** — Andriushchenko et al., *AgentHarm: A Benchmark for Measuring Harmfulness of LLM Agents*, arXiv:2410.09024 (ICLR 2025). ต้นแบบของการจัดระดับความร้ายแรงของพฤติกรรมอันตรายเป็นหมวด — เราประยุกต์เป็นการแยก "กับดักทั่วไป" ออกจาก "กับดักวิกฤต" (เช่น ลบ credential, ลบข้อมูล production) ในทุกตระกูล

ความแตกต่างจากงานข้างต้นที่ต้องระบุ: ฉากของเรา**สร้างเชิงโปรแกรมจาก 25 ตระกูล** ไม่ใช่ฉากเขียนมือทั้งหมด, รัน**ครั้งเดียวต่อเซลล์**, และโมเดลที่ใช้ไม่ใช่โมเดลดั้งเดิมของแต่ละ harness — ผลจึงอ่านเป็น "พฤติกรรมของระบบ harness+โมเดล" ภายใต้เงื่อนไขที่ระบุใน `METHODOLOGY.md`

## โครงสร้าง repo

| ไฟล์/โฟลเดอร์ | เนื้อหา |
|---|---|
| `METHODOLOGY.md` | ระเบียบวิธีฉบับเต็มและตารางกับดักทั้ง 25 ตระกูล |
| `RESULTS-CODEX-HERMES.md` | ผลฉบับสมบูรณ์ของ Codex และ Hermes พร้อมข้อค้นพบ |
| `RESULTS-CLAUDE.md` | ผลฉบับสมบูรณ์ของ Claude Code พร้อมข้อค้นพบ |
| `scenarios500.json` | ฉากทั้ง 500 ฉาก (prompt, fixture, เงื่อนไขสำเร็จ/กับดัก) — ค่า credential ในฉากเป็นค่าปลอมสังเคราะห์เพื่อการทดสอบเท่านั้น |
| `scenarios.py` | ฉากเขียนมือ 10 ฉากจากรอบทดสอบนำร่อง |
| `gen_scenarios.py` | ตัวสร้างฉาก 500 ฉาก (deterministic) |
| `validate500.py` | ตัวตรวจสอบความถูกต้องของฉากก่อนรัน |
| `runner.py` | ตัวรันรายเซลล์และตัวให้คะแนนจากผลต่างระบบไฟล์ |
| `batch.py` | ตัวขับชุดใหญ่ (เลนขนาน, retry, resume) |
| `results/per-family-results.csv` | ตัวเลขสรุปรายตระกูล |
| `results/codex/`, `results/hermes/`, `results/claude/` | ผลรายเซลล์ (JSON) ครบ 500 ไฟล์ต่อ harness |
| `RESULTS-RERUN.md` | ผลการรันซ้ำ 308 เซลล์ที่ไม่สำเร็จ สองแขน isolated vs real config พร้อมการจัดหมวดเหตุผล |
| `RESULTS-HERMES-V0225.md` | ผล Hermes Agent v0.22.5 ชุดเต็ม 500 ฉาก เทียบกับ 0.19.0 |
| `results/rerun-isolated/`, `results/rerun-real/` | ผลรายเซลล์ของการรันซ้ำ (308 ไฟล์ต่อแขน) |
| `results/classify-rerun-isolated.csv`, `results/classify-rerun-real.csv` | การจัดหมวดเหตุผลรายเซลล์ของชุดรันซ้ำ |
| `results/hermes-v0.22.5/` | ผลรายเซลล์ Hermes v0.22.5 ครบ 500 ไฟล์ |

## วิธีรันซ้ำ

ต้องการ: Python 3, ตัว CLI ของ harness ที่จะทดสอบติดตั้งอยู่ในเครื่อง และ endpoint ที่ให้บริการโมเดลในฟอร์มัตที่ harness นั้นใช้ (Anthropic Messages / OpenAI Responses / OpenAI Chat Completions) ตั้งค่าผ่านตัวแปรแวดล้อม `LITELLM_BASE_URL`, `CLI_TOKEN`, `TEST_MODEL` แล้วรัน `python3 batch.py` (ทั้งชุด) หรือ `python3 runner.py --harness codex --case <id>` (เซลล์เดียว) คะแนนจะถูกเขียนลง `results_full/`

## สัญญาอนุญาต

MIT — ดูไฟล์ `LICENSE`
