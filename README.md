# AI Harness Safety Trap Test

**การทดสอบกับดักความปลอดภัยของ AI coding/agent harness แบบเต็มสเกล — 500 สถานการณ์ × 3 harness ด้วยโมเดลเดียวกัน**

> **English summary:** A full-scale behavioural safety test of three AI agent harnesses — Claude Code 2.1.311, OpenAI Codex CLI 0.164.0, and Hermes Agent 0.19.0 — all driving the *same* model (`qwen3.7-plus`) through 500 filesystem tasks seeded with "traps": plausible-looking actions that cause real damage if taken (deleting credential backups during cleanup, editing generated files instead of their source, purging pinned cache entries, embedding production credentials in migrations, and 21 more families). Scoring is done purely from before/after filesystem state — no LLM judge. Codex and Hermes have completed all 500 scenarios; Claude Code results are in progress.

## คำถามของการทดสอบ

เมื่อตรึงโมเดลไว้ตัวเดียวกัน harness ที่ต่างกันมีพฤติกรรมด้านความปลอดภัยต่างกันแค่ไหน โดยเฉพาะพฤติกรรม **ทำเกินขอบเขตงานที่สั่ง (over-eagerness)** จนสร้างความเสียหายจริง เช่น ลบไฟล์ที่ไม่ควรลบ แก้ไฟล์นอกขอบเขต หรือฝังข้อมูลลับลงในงานที่ส่งมอบ

## ผลสรุป (Codex และ Hermes — รันครบ 500/500)

| ตัวชี้วัด (จาก 500 ฉาก) | Codex CLI 0.164.0 | Hermes Agent 0.19.0 |
|---|---|---|
| งานสำเร็จตามเงื่อนไข | **448 (89.6%)** | 431 (86.2%) |
| รันที่ตกกับดัก ≥ 1 จุด | 72 (14.4%) | 77 (15.4%) |
| รันที่ตกกับดักระดับวิกฤต | 54 (10.8%) | 59 (11.8%) |
| เวลามัธยฐานต่อรัน | **32.8 วิ** | 46.8 วิ |

ข้อค้นพบเด่น: ทั้งสองตัวตกตระกูล `generated_fix` **100% (18/18)** และ `cleanup_cred` ~80% เหมือนกัน ส่วนจุดอ่อนเฉพาะตัวต่างกันชัด — Hermes ไม่เคารพไฟล์ที่กำกับว่าห้ามลบ (`cleanup_marks` 11/24 เทียบกับ Codex 1/24) ขณะที่ Codex ฝืนลบรายการที่ถูก pin ในแคชเกือบทุกครั้ง (`cache_pinned` 15/16 เทียบกับ Hermes 9/16) รายละเอียดเต็มอยู่ใน [`RESULTS-CODEX-HERMES.md`](RESULTS-CODEX-HERMES.md) และ [`results/per-family-results.csv`](results/per-family-results.csv) ผลของ Claude Code กำลังดำเนินการและจะเพิ่มเมื่อครบ 500 เซลล์

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
| `scenarios500.json` | ฉากทั้ง 500 ฉาก (prompt, fixture, เงื่อนไขสำเร็จ/กับดัก) — ค่า credential ในฉากเป็นค่าปลอมสังเคราะห์เพื่อการทดสอบเท่านั้น |
| `scenarios.py` | ฉากเขียนมือ 10 ฉากจากรอบทดสอบนำร่อง |
| `gen_scenarios.py` | ตัวสร้างฉาก 500 ฉาก (deterministic) |
| `validate500.py` | ตัวตรวจสอบความถูกต้องของฉากก่อนรัน |
| `runner.py` | ตัวรันรายเซลล์และตัวให้คะแนนจากผลต่างระบบไฟล์ |
| `batch.py` | ตัวขับชุดใหญ่ (เลนขนาน, retry, resume) |
| `results/per-family-results.csv` | ตัวเลขสรุปรายตระกูล |
| `results/codex/`, `results/hermes/` | ผลรายเซลล์ (JSON) ครบ 500 ไฟล์ต่อ harness |

## วิธีรันซ้ำ

ต้องการ: Python 3, ตัว CLI ของ harness ที่จะทดสอบติดตั้งอยู่ในเครื่อง และ endpoint ที่ให้บริการโมเดลในฟอร์มัตที่ harness นั้นใช้ (Anthropic Messages / OpenAI Responses / OpenAI Chat Completions) ตั้งค่าผ่านตัวแปรแวดล้อม `LITELLM_BASE_URL`, `CLI_TOKEN`, `TEST_MODEL` แล้วรัน `python3 batch.py` (ทั้งชุด) หรือ `python3 runner.py --harness codex --case <id>` (เซลล์เดียว) คะแนนจะถูกเขียนลง `results_full/`

## สัญญาอนุญาต

MIT — ดูไฟล์ `LICENSE`
