### 2026-02-17 - Expand eval cases to 20 realistic user inputs

**Changes:**
- `data/eval_cases.json` - Grew from 2 to 20 eval cases covering 18 additional job roles

**Rationale:**
The goal is to stress-test the baseline skill selector with realistic, messy user inputs rather than hand-crafted passing cases. Each case simulates a real user filling in their resume skills without knowledge of the system's internals. Key variation patterns:

- **Role variety**: Frontend, Full-Stack, Back-End, DevOps, ML Engineer, Data Analyst, Cloud Architect, Cyber Security, iOS, Android, QA, Embedded, Data Engineer, SRE, Blockchain, Game Dev, AI Research, Junior Dev — covering most role families plus several (QA, Game Dev, Blockchain, Embedded) that fall through to "general"
- **Synonym/formatting noise**: `ReactJS`, `VueJS`, `Node JS`, `NodeJS`, `Tailwind CSS`, `React.js`, `Pytorch`, `Scikit-Learn`, `sklearn`, `React-Native`, `Amazon Web Services`, `Microsoft Azure`, `Google Cloud`, `Amazon Cloud`, `Google Cloud Platform`, `Apache Spark`
- **Cross-role contamination**: Every case includes a handful of skills irrelevant to the role (e.g. `React` for a backend engineer, `Machine Learning` for a QA engineer, `Docker` for an iOS developer)
- **Untracked tools**: `Figma`, `JIRA`, `Tableau`, `Power BI`, `Looker`, `Excel`, `Xcode`, `CocoaPods`, `TestFlight`, `Airflow`, `Snowflake`, `dbt`, `PagerDuty`, `Solidity`, `Unity`, `HuggingFace`, `CUDA`, `MATLAB`, `VBA`, `Blender` — tools real users list that our profiles don't know about
- **Filler/soft skills in concepts**: `Communication`, `Teamwork`, `Problem Solving`, `Version Control`, `Research Methodology` — padding users copy from generic resume templates
- **Case/casing variation in job_role**: `devops engineer`, `android developer`, `game developer`, `site reliability engineer` (all lowercase), `Back-End Engineer` (hyphen), `QA / Test Engineer` (slash)

**Tests:**
No automated tests added — these are evaluation-only data fixtures consumed by `scripts/eval.py`.

**Impact:**
Provides a diverse, realistic test bed for measuring Precision@N and category hit-rate of the baseline scorer across a wide range of role families, synonym forms, and noise patterns.

*2026-02-17 (amendment)* — Expanded each case with additional irrelevant skills to simulate a user dumping their full skill inventory. Every case now includes 5–10 skills that are clearly off-domain for the role (e.g. Unity/Unreal Engine for a Data Engineer, TensorFlow for a QA Engineer, FreeRTOS/STM32 for a Frontend Engineer, Excel/Tableau for a DevOps engineer, Assembly/MATLAB across most roles). This reflects the real usage pattern: a user feeds all their skills regardless of relevance, and the service must rank and filter for the target job role.
