# clinix-backend

# Clinix — Product Requirements Document
## The Sovereign Clinical Agent

**Version:** 1.0  
**Date:** June 28, 2026  
**Track:** Social Impact & Inclusion / EdTech  
**Status:** Hackathon MVP

---

## 1. Executive Summary

Clinix is an agentic clinical operating system that empowers Nigerian medical students to deliver high-quality supervised care while giving patients absolute sovereignty over their medical data. Every patient encounter becomes a dual-value event: the student earns verified, cryptographically-signed clinical credits toward their professional portfolio, and the patient receives an encrypted, portable copy of their record in their personal data wallet.

### The Problem We Solve

| Stakeholder | Pain Point |
|-------------|-----------|
| **Medical Students** | Perform millions of supervised consultations with zero feedback loop, no tracked competency, and no portable evidence of clinical growth |
| **Patients** | Lose paper cards, forget histories, and start from zero at every new hospital. Medical records belong to institutions, not people |
| **Healthcare System** | Fragmented care, no continuity between facilities, students graduate with theoretical knowledge but undocumented practical experience |

### Our Solution in One Sentence

> *"Clinix turns every supervised patient encounter into a learning credit for the student and a portable health record for the patient — using AI that actually does things, not just chats."*

---

## 2. Product Vision

### North Star

By 2030, every medical student in Nigeria will graduate with a Clinix-verified clinical portfolio, and every Nigerian patient will own their complete health history in a portable, encrypted data wallet.

### 5-Year Vision
- **Year 1:** Pilot at LAUTECH Teaching Hospital, 500 students, 10,000 patients
- **Year 2:** Expand to 5 Nigerian teaching hospitals (LUTH, UCH, UNTH, ABUTH, OAUTH)
- **Year 3:** National deployment across all 40+ teaching hospitals
- **Year 4:** Integration with MDCN for official credential verification
- **Year 5:** Pan-African expansion (Ghana, Kenya, South Africa)

---

## 3. Target Users

### Primary: Medical Students (500L, Nigeria)
- **Name:** Ademilua Adeola (our persona)
- **Age:** 24
- **Context:** Final year at LAUTECH, rotating through OPD, wards, and emergency
- **Pain:** Documents encounters on paper that gets lost. No record of what he's seen or how accurate his diagnoses were. Graduates with no proof of clinical competence.
- **Goal:** Build a verified portfolio that MDCN and international residency programs will trust

### Secondary: Patients
- **Name:** Fatima Abdullahi
- **Age:** 34, market trader in Ogbomoso
- **Context:** Sees different doctors at different hospitals. Loses her card every time. Can't remember her medication history.
- **Pain:** "Every time I go to the hospital, they ask me the same questions. I don't remember what drugs I took last time."
- **Goal:** Own her health record and take it anywhere

### Tertiary: Supervising Physicians
- **Name:** Dr. Okonkwo
- **Role:** Consultant, Internal Medicine
- **Pain:** Reviews student notes on paper. Can't track student progress systematically.
- **Goal:** Verify student work efficiently, ensure patient safety, maintain oversight

---

## 4. Core Features

### Feature 1: AI-Assisted Encounter Documentation

**What it does:** Guides the student through a structured clinical encounter with real-time AI analysis.

**User Flow:**
1. Student logs into Clinix dashboard
2. Selects patient from today's queue (or searches existing patient)
3. Documents chief complaint, history, and associated symptoms
4. **AI Agent analyzes symptoms** via MCP (Model Context Protocol)
5. AI suggests probable diagnosis, differential, and required investigations
6. Student conducts physical exam, enters vitals
7. Student confirms or modifies AI suggestions
8. Working diagnosis and treatment plan documented
9. **Supervisor reviews and approves** before finalization

**Key Interactions:**
- Auto-save as draft every 30 seconds
- AI analysis triggers after 10 characters in chief complaint (debounced 500ms)
- MCP Action Skills trigger based on symptom patterns
- All AI suggestions require human verification before execution

**Success Metrics:**
- Average encounter documentation time: < 8 minutes
- AI suggestion acceptance rate: > 75%
- Supervisor approval rate: > 90%

---

### Feature 2: MCP Action Skills

**What it does:** AI doesn't just suggest — it *acts*. Via the Model Context Protocol, Clinix triggers automated workflows when specific clinical patterns are detected.

**Active Skills (MVP):**

| Skill | Trigger | Actions |
|-------|---------|---------|
| **Malaria Detection** | Fever + headache + chills pattern | Check RDT stock, verify Coartem availability, schedule Day 3 follow-up |
| **Cardiac Alert** | Chest pain + SOB + age > 40 | Order ECG, draft cardiology referral, check troponin stock |
| **Diabetes Management** | RBS > 200 or known diabetic | Check insulin stock, suggest HbA1c, flag hypoglycemia risk |
| **Prenatal Screening** | Pregnant patient | Track gestational age, flag high-risk markers, schedule next visit |

**Technical Implementation:**
- Each skill is an MCP server with defined input schema (symptoms, vitals, patient demographics)
- Skills return structured output: diagnosis confidence, recommended actions, urgency level
- All actions are **drafted**, not executed — student/supervisor must confirm
- Skills log every invocation for audit and accuracy tracking

**Success Metrics:**
- Skill trigger accuracy: > 85%
- Average time saved per encounter: 3 minutes
- Stock check accuracy: 100% (real-time inventory API)

---

### Feature 3: Patient Data Wallet (Chekk Integration)

**What it does:** When an encounter is finalized, Clinix encrypts the clinical summary and pushes it to the patient's sovereign data wallet via Chekk's Data Portability infrastructure.

**User Flow:**
1. Encounter is finalized and supervisor-approved
2. Clinix generates encrypted encounter summary (JSON)
3. Summary is pushed to patient's Chekk wallet via API
4. Patient receives SMS with QR code link
5. Patient scans QR code to view record in their wallet
6. Record is permanently accessible, portable to any hospital

**Data Included in Wallet Push:**
- Encounter date and location
- Chief complaint and history
- Vitals (temperature, BP, pulse, SpO2)
- Working diagnosis
- Investigations ordered
- Treatment plan and medications
- Follow-up instructions
- Student and supervisor names
- Cryptographic signature

**Security:**
- AES-256 encryption at rest
- TLS 1.3 in transit
- Patient holds decryption key (or key escrow with patient-controlled recovery)
- HIPAA-equivalent compliance (NDPR aligned)

**Success Metrics:**
- Wallet creation rate: > 80% of encounters
- Patient access rate (within 24h): > 60%
- Data portability success: > 95%

---

### Feature 4: Verified Clinical Credits & Portfolio

**What it does:** Every encounter earns the student credits in specific competency categories. These build into a cryptographically-signed professional portfolio.

**Credit Categories:**

| Category | Points per Encounter | Verification Method |
|----------|---------------------|---------------------|
| History Taking | 2 | Supervisor review of documentation completeness |
| Physical Examination | 2 | Vitals recorded + exam notes present |
| Differential Diagnosis | 2 | AI confidence > 70% OR supervisor override |
| Treatment Planning | 2 | Medications appropriate for diagnosis |
| Patient Communication | 1 | Patient satisfaction (optional feedback) |

**Portfolio Features:**
- Total encounters, diagnoses, accuracy rate
- Competency radar chart (6 axes)
- Verified procedures list with cryptographic seals
- Exportable PDF for MDCN/residency applications
- Blockchain-anchored signature (optional, for tamper-proofing)

**Success Metrics:**
- Average credits per student per week: 25
- Portfolio export rate: > 30% at graduation
- Supervisor verification time: < 2 minutes per encounter

---

### Feature 5: Supervisor Dashboard

**What it does:** Gives supervising physicians oversight of all student encounters with quick review and approval workflows.

**Features:**
- Queue of encounters pending review
- Side-by-side comparison: student diagnosis vs. AI suggestion vs. supervisor's own assessment
- One-click approve / request changes / reject
- Student performance trends (accuracy over time)
- Flagged encounters (high-risk, unusual patterns)

---

## 5. User Stories

### Student Stories

> **As a** 500L medical student, **I want** to document my patient encounters digitally **so that** I don't lose my notes and can track my clinical growth.

> **As a** student, **I want** AI to suggest diagnoses based on symptoms **so that** I don't miss important differentials.

> **As a** student, **I want** my encounters to earn verified credits **so that** I can prove my competence to MDCN and residency programs.

### Patient Stories

> **As a** patient, **I want** to receive a copy of my medical record after every visit **so that** I can show it to any doctor I see in the future.

> **As a** patient without a smartphone, **I want** to receive my record via SMS **so that** I'm not excluded from digital health.

### Supervisor Stories

> **As a** supervising physician, **I want** to review student encounters before they're finalized **so that** patient safety is maintained.

> **As a** supervisor, **I want** to see my students' accuracy trends **so that** I can identify who needs more support.

---

## 6. Technical Architecture

### High-Level Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND (React 18)                   │
│  Dashboard | Encounters | Portfolio | Wallets | Skills      │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS / JSON
┌────────────────────────▼────────────────────────────────────┐
│                      API GATEWAY (FastAPI)                   │
│  Auth | Patients | Encounters | AI/MCP | Wallets | Portfolio │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
┌────────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐
│  PostgreSQL   │ │  OpenAI    │ │   Chekk    │
│  (Primary DB) │ │  (GPT-4)   │ │  (Wallet)  │
└───────────────┘ └────────────┘ └────────────┘
         │
┌────────▼──────┐
│  Redis        │
│  (Cache /     │
│   Queue)      │
└───────────────┘
```

### Database Schema

**Users Table**
```sql
id: UUID PRIMARY KEY
email: VARCHAR(255) UNIQUE NOT NULL
password_hash: VARCHAR(255) NOT NULL
first_name: VARCHAR(100) NOT NULL
last_name: VARCHAR(100) NOT NULL
role: ENUM('student', 'supervisor', 'admin') DEFAULT 'student'
year_of_study: INT  -- NULL for non-students
hospital: VARCHAR(100)
mdcn_reg_no: VARCHAR(50)  -- For supervisors
is_active: BOOLEAN DEFAULT TRUE
created_at: TIMESTAMP DEFAULT NOW()
updated_at: TIMESTAMP DEFAULT NOW()
```

**Patients Table**
```sql
id: UUID PRIMARY KEY
hospital_id: VARCHAR(50) UNIQUE NOT NULL  -- e.g., "LTH-2024-001"
first_name: VARCHAR(100) NOT NULL
last_name: VARCHAR(100) NOT NULL
date_of_birth: DATE NOT NULL
gender: ENUM('M', 'F') NOT NULL
phone: VARCHAR(20) NOT NULL
address: TEXT
emergency_contact_name: VARCHAR(100)
emergency_contact_phone: VARCHAR(20)
chekk_wallet_id: VARCHAR(100)  -- External reference
insurance_id: VARCHAR(50)
created_at: TIMESTAMP DEFAULT NOW()
updated_at: TIMESTAMP DEFAULT NOW()
```

**Encounters Table**
```sql
id: UUID PRIMARY KEY
student_id: UUID REFERENCES users(id)
patient_id: UUID REFERENCES patients(id)
supervisor_id: UUID REFERENCES users(id)  -- NULL until assigned
status: ENUM('draft', 'in_progress', 'pending_review', 'finalized', 'rejected')

-- Chief Complaint & History
chief_complaint: TEXT NOT NULL
duration: VARCHAR(50)
severity: ENUM('mild', 'moderate', 'severe', 'life_threatening')
associated_symptoms: JSONB DEFAULT '[]'

-- AI Analysis
ai_diagnosis: TEXT
ai_confidence: DECIMAL(3,2)  -- 0.00 to 1.00
ai_differential: JSONB DEFAULT '[]'
ai_actions_triggered: JSONB DEFAULT '[]'

-- Physical Exam
vitals: JSONB DEFAULT '{}'  -- {temp, bp, pulse, spo2}
exam_notes: TEXT

-- Assessment & Plan
working_diagnosis: TEXT
investigations: JSONB DEFAULT '[]'
treatment_plan: TEXT
follow_up: VARCHAR(50)

-- Supervisor Review
supervisor_notes: TEXT
supervisor_verified: BOOLEAN DEFAULT FALSE
verified_at: TIMESTAMP

-- Credits
credits_earned: INT DEFAULT 0
credit_breakdown: JSONB DEFAULT '{}'  -- {history: 2, exam: 2, ...}

-- Metadata
created_at: TIMESTAMP DEFAULT NOW()
updated_at: TIMESTAMP DEFAULT NOW()
finalized_at: TIMESTAMP
```

**WalletRecords Table**
```sql
id: UUID PRIMARY KEY
patient_id: UUID REFERENCES patients(id)
encounter_id: UUID REFERENCES encounters(id)
chekk_record_id: VARCHAR(100)  -- External reference
qr_payload: TEXT NOT NULL
encrypted_summary: TEXT NOT NULL
encryption_iv: VARCHAR(100)  -- Initialization vector
status: ENUM('pending', 'pushed', 'accessed', 'expired')
pushed_at: TIMESTAMP
accessed_at: TIMESTAMP
created_at: TIMESTAMP DEFAULT NOW()
```

**ClinicalCredits Table**
```sql
id: UUID PRIMARY KEY
student_id: UUID REFERENCES users(id)
encounter_id: UUID REFERENCES encounters(id)
category: ENUM('history_taking', 'physical_exam', 'diagnosis', 'treatment', 'communication')
points: INT NOT NULL
verified: BOOLEAN DEFAULT FALSE
supervisor_id: UUID REFERENCES users(id)
signed_hash: VARCHAR(255)  -- Cryptographic signature
created_at: TIMESTAMP DEFAULT NOW()
```

**ActionSkillLogs Table**
```sql
id: UUID PRIMARY KEY
encounter_id: UUID REFERENCES encounters(id)
skill_name: VARCHAR(50) NOT NULL  -- e.g., "malaria_detect"
triggered_at: TIMESTAMP DEFAULT NOW()
input_data: JSONB DEFAULT '{}'
output_data: JSONB DEFAULT '{}'
success: BOOLEAN DEFAULT TRUE
error_message: TEXT
execution_time_ms: INT
```

**Activities Table**
```sql
id: UUID PRIMARY KEY
user_id: UUID REFERENCES users(id)
activity_type: VARCHAR(50) NOT NULL  -- 'encounter_complete', 'wallet_push', 'credit_earned'
description: TEXT NOT NULL
metadata: JSONB DEFAULT '{}'
created_at: TIMESTAMP DEFAULT NOW()
```

---

## 7. API Specification

### Authentication

**POST /api/v1/auth/register**
```json
Request:
{
  "email": "adeola@clinix.ng",
  "password": "securePassword123",
  "first_name": "Ademilua",
  "last_name": "Adeola",
  "role": "student",
  "year_of_study": 5,
  "hospital": "LAUTECH Teaching Hospital"
}

Response: 201 Created
{
  "id": "uuid",
  "email": "adeola@clinix.ng",
  "first_name": "Ademilua",
  "last_name": "Adeola",
  "role": "student",
  "access_token": "eyJ...",
  "refresh_token": "eyJ..."
}
```

**POST /api/v1/auth/login**
```json
Request:
{
  "email": "adeola@clinix.ng",
  "password": "securePassword123"
}

Response: 200 OK
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**POST /api/v1/auth/refresh**
```json
Request:
{
  "refresh_token": "eyJ..."
}

Response: 200 OK
{
  "access_token": "eyJ...",
  "expires_in": 900
}
```

### Patients

**GET /api/v1/patients**
```json
Query: ?search=abdullahi&page=1&limit=20

Response: 200 OK
{
  "data": [
    {
      "id": "uuid",
      "hospital_id": "LTH-2024-001",
      "first_name": "Fatima",
      "last_name": "Abdullahi",
      "age": 34,
      "gender": "F",
      "phone": "+2348012345678",
      "chekk_wallet_id": "chk_wallet_abc123"
    }
  ],
  "pagination": {
    "total": 156,
    "page": 1,
    "limit": 20,
    "total_pages": 8
  }
}
```

**GET /api/v1/patients/:id**
```json
Response: 200 OK
{
  "id": "uuid",
  "hospital_id": "LTH-2024-001",
  "first_name": "Fatima",
  "last_name": "Abdullahi",
  "date_of_birth": "1990-03-15",
  "gender": "F",
  "phone": "+2348012345678",
  "address": "Ogbomoso, Oyo State",
  "emergency_contact": {
    "name": "Aminu Abdullahi",
    "phone": "+2348098765432"
  },
  "encounter_count": 3,
  "last_encounter_date": "2026-06-26",
  "chekk_wallet_status": "active"
}
```

**GET /api/v1/patients/queue**
```json
Response: 200 OK
{
  "data": [
    {
      "id": "uuid",
      "hospital_id": "LTH-2024-001",
      "first_name": "Fatima",
      "last_name": "Abdullahi",
      "age": 34,
      "gender": "F",
      "chief_complaint": "Fever, headache, chills",
      "waiting_time_minutes": 12,
      "priority": "urgent",
      "status": "waiting"
    }
  ],
  "total_waiting": 3,
  "urgent_count": 1
}
```

### Encounters

**POST /api/v1/encounters**
```json
Request:
{
  "patient_id": "uuid",
  "chief_complaint": "Patient presents with fever, headache, and chills for 3 days.",
  "duration": "3 days",
  "severity": "moderate",
  "associated_symptoms": ["fever", "headache", "chills"]
}

Response: 201 Created
{
  "id": "uuid",
  "patient_id": "uuid",
  "student_id": "uuid",
  "status": "draft",
  "chief_complaint": "Patient presents with fever...",
  "created_at": "2026-06-28T10:30:00Z"
}
```

**POST /api/v1/encounters/:id/ai-analyze**
```json
Response: 200 OK
{
  "encounter_id": "uuid",
  "analysis": {
    "primary_diagnosis": "Probable Malaria (Uncomplicated)",
    "confidence": 0.92,
    "differential_diagnoses": [
      {"condition": "Malaria", "probability": 0.92},
      {"condition": "Typhoid fever", "probability": 0.15},
      {"condition": "Viral illness", "probability": 0.08}
    ],
    "recommended_investigations": ["Malaria RDT", "Full Blood Count"],
    "urgency": "routine",
    "mcp_actions": [
      {
        "skill": "malaria_detect",
        "actions": [
          {"type": "inventory_check", "drug": "Artemether-Lumefantrine", "stock": 24, "available": true},
          {"type": "rdt_recommend", "test": "SD Bioline Malaria Ag", "available": true},
          {"type": "schedule_followup", "days": 2}
        ]
      }
    ]
  },
  "processing_time_ms": 1240
}
```

**PATCH /api/v1/encounters/:id**
```json
Request:
{
  "vitals": {
    "temperature": 38.5,
    "blood_pressure": "120/80",
    "pulse": 96,
    "spo2": 98
  },
  "exam_notes": "Patient appears mildly pale. No jaundice. Spleen not palpable.",
  "working_diagnosis": "Uncomplicated Plasmodium falciparum malaria",
  "investigations": ["Malaria RDT", "Full Blood Count"],
  "treatment_plan": "Artemether-Lumefantrine 20/120mg: 4 tablets now, then 4 tablets at 8h, 24h, 36h. Paracetamol 1g PRN for fever.",
  "follow_up": "48 hours"
}

Response: 200 OK
{
  "id": "uuid",
  "status": "in_progress",
  "updated_at": "2026-06-28T10:45:00Z"
}
```

**POST /api/v1/encounters/:id/finalize**
```json
Response: 200 OK
{
  "id": "uuid",
  "status": "pending_review",
  "credits_earned": 8,
  "credit_breakdown": {
    "history_taking": 2,
    "physical_exam": 2,
    "diagnosis": 2,
    "treatment": 2
  },
  "wallet_push_status": "pending",
  "finalized_at": "2026-06-28T10:50:00Z"
}
```

### Wallets

**POST /api/v1/wallets/:patient_id/push**
```json
Request:
{
  "encounter_id": "uuid"
}

Response: 200 OK
{
  "wallet_record_id": "uuid",
  "chekk_status": "pushed",
  "qr_payload": "CLINIX-ENC-uuid-20260628",
  "encrypted_summary": "base64encryptedstring...",
  "pushed_at": "2026-06-28T10:52:00Z",
  "patient_notification": {
    "sms_sent": true,
    "sms_id": "sms_abc123"
  }
}
```

**GET /api/v1/wallets/:patient_id/qr**
```json
Response: 200 OK
{
  "qr_payload": "CLINIX-ENC-uuid-20260628",
  "expires_at": "2026-06-29T10:52:00Z",
  "access_url": "https://wallet.chekk.io/access/CLINIX-ENC-uuid-20260628"
}
```

### Portfolio

**GET /api/v1/portfolio/me**
```json
Response: 200 OK
{
  "student": {
    "id": "uuid",
    "name": "Ademilua Adeola",
    "year_of_study": 5,
    "hospital": "LAUTECH Teaching Hospital"
  },
  "summary": {
    "total_encounters": 47,
    "total_diagnoses": 23,
    "diagnostic_accuracy": 0.94,
    "total_credits": 156,
    "clinical_hours": 128
  },
  "competencies": {
    "history_taking": {"score": 94, "encounters": 47},
    "physical_exam": {"score": 91, "encounters": 42},
    "diagnosis": {"score": 89, "encounters": 38},
    "treatment": {"score": 93, "encounters": 35},
    "communication": {"score": 96, "encounters": 47},
    "procedures": {"score": 85, "encounters": 28}
  },
  "verified_procedures": [
    {
      "category": "history_taking",
      "count": 47,
      "accuracy": 94,
      "verified": true,
      "signature": "sha256:abc123..."
    }
  ],
  "recent_activity": [
    {
      "type": "encounter_complete",
      "description": "Completed encounter with Amina Ibrahim",
      "credits_earned": 8,
      "created_at": "2026-06-28T08:30:00Z"
    }
  ]
}
```

---

## 8. Frontend Specification

### Tech Stack
- **Framework:** React 18 + Vite
- **Styling:** Tailwind CSS
- **State Management:** React Query (server state) + Zustand (client state)
- **Charts:** Chart.js + react-chartjs-2
- **QR Codes:** qrcode.js
- **HTTP Client:** Axios with interceptors
- **Forms:** React Hook Form + Zod validation
- **Routing:** React Router v6

### Component Hierarchy

```
App
├── Layout
│   ├── Sidebar (fixed, 260px)
│   │   ├── Logo
│   │   ├── Navigation
│   │   │   ├── Main Section (Dashboard, Encounters, Patients, Portfolio)
│   │   │   ├── Clinical Section (Skills, Inventory, Referrals)
│   │   │   └── Data Section (Wallets, Analytics)
│   │   └── UserCard
│   └── TopBar
│       ├── PageTitle
│       └── ActionButtons
├── Routes
│   ├── / (Dashboard)
│   │   ├── StatsGrid (4 StatCards)
│   │   ├── ContentGrid
│   │   │   ├── PatientQueue
│   │   │   │   └── PatientItem[]
│   │   │   └── AIPanel
│   │   │       └── AISuggestion[]
│   │   └── ContentGrid2
│   │       ├── ActivityFeed
│   │       │   └── ActivityItem[]
│   │       └── PortfolioPreview
│   │           └── PortfolioChart
│   ├── /encounters/new (NewEncounter)
│   │   ├── PatientSelection
│   │   ├── ChiefComplaintForm
│   │   ├── AIDiagnosisCard
│   │   ├── PhysicalExamForm
│   │   ├── AssessmentPlanForm
│   │   └── ActionButtons
│   ├── /portfolio (Portfolio)
│   ├── /wallets (Wallets)
│   ├── /skills (ActionSkills)
│   └── /patients, /inventory, /referrals, /analytics (Placeholder)
├── Modals
│   ├── WalletPushModal (QR code display)
│   ├── SuccessModal (post-finalization)
│   └── ConfirmModal (generic)
└── ToastContainer
```

### Key Components

**StatCard**
- Props: `icon`, `value`, `label`, `trend`, `trendDirection`, `color`
- Hover: lift effect, shadow increase
- Top border: 3px gradient (primary to primary-light)

**PatientItem**
- Props: `patient`, `selected`, `onClick`
- Avatar: gradient circle with initials
- Status badge: color-coded (urgent=red, waiting=amber, completed=green)
- Selected state: teal background border

**AIPanel**
- Dark gradient background (#0f766e to #134e4a)
- Pulsing MCP badge
- Suggestion cards: hover translateX(4px)
- Radial glow decoration (pseudo-element)

**Timeline**
- Vertical line with dots
- Dot states: pending (gray), active (primary), completed (green with check)
- Sticky positioning on scroll

**Modal System**
- Overlay: backdrop-filter blur, fade in
- Content: scale(0.9) → scale(1) animation
- Close on backdrop click or X button
- Focus trap for accessibility

---

## 9. Design System

### Colors

| Token | Hex | Usage |
|-------|-----|-------|
| `--primary` | `#0d9488` | Buttons, links, active states |
| `--primary-light` | `#14b8a6` | Gradients, highlights |
| `--primary-dark` | `#0f766e` | Hover states |
| `--accent` | `#f43f5e` | Badges, urgent indicators |
| `--success` | `#10b981` | Completed, verified states |
| `--warning` | `#f59e0b` | Waiting, pending states |
| `--danger` | `#ef4444` | Errors, urgent |
| `--bg` | `#f8fafc` | Page background |
| `--card` | `#ffffff` | Card backgrounds |
| `--text` | `#0f172a` | Primary text |
| `--text-light` | `#64748b` | Secondary text |
| `--border` | `#e2e8f0` | Borders, dividers |

### Typography

| Element | Font | Size | Weight | Line Height |
|---------|------|------|--------|-------------|
| Page Title | Inter | 28px | 700 | 1.2 |
| Card Title | Inter | 16px | 700 | 1.4 |
| Body | Inter | 14px | 400 | 1.5 |
| Small | Inter | 12px | 500 | 1.4 |
| Label | Inter | 13px | 600 | 1.4 |
| Stat Value | Inter | 32px | 700 | 1.1 |

### Spacing

- Base unit: 4px
- Card padding: 24px (6 units)
- Card gap: 20px (5 units)
- Section margin: 28px (7 units)
- Border radius: 16px (cards), 10px (buttons/inputs), 20px (badges), 50% (avatars)

### Shadows

| Token | Value | Usage |
|-------|-------|-------|
| `--shadow` | `0 1px 3px rgba(0,0,0,0.1)` | Default card |
| `--shadow-lg` | `0 10px 15px -3px rgba(0,0,0,0.1)` | Hover state, modals |

### Animations

| Animation | Duration | Easing | Usage |
|-----------|----------|--------|-------|
| Fade In | 0.5s | ease-out | Page transitions |
| Slide Up | 0.4s | ease-out | Modal content |
| Pulse | 2s | ease-in-out | MCP badge |
| Hover Lift | 0.3s | ease | Card hover |

---

## 10. Security Requirements

### Authentication
- JWT access tokens (15-minute expiry)
- Refresh tokens (7-day expiry, stored httpOnly cookie)
- Role-based access control (student, supervisor, admin)
- Password hashing: bcrypt with salt rounds 12

### Data Protection
- All patient data encrypted at rest (AES-256)
- TLS 1.3 for all API communications
- PHI (Protected Health Information) never logged
- Audit trail for all data access

### API Security
- Rate limiting: 100 req/min per IP, 1000 req/min per user
- Input validation: Zod schemas (frontend) + Pydantic (backend)
- SQL injection prevention: parameterized queries only
- CORS: whitelist production domain only

### Wallet Security
- Patient data encrypted with patient-controlled key
- Key escrow with multi-factor recovery
- QR codes expire after 24 hours
- Access logging for audit

---

## 11. Performance Requirements

| Metric | Target | Measurement |
|--------|--------|-------------|
| Page Load Time | < 2s | Lighthouse |
| Time to Interactive | < 3s | Lighthouse |
| API Response Time (p95) | < 500ms | Server logs |
| AI Analysis Time | < 3s | User timing |
| QR Generation | < 1s | User timing |
| Concurrent Users | 500 | Load test |

---

## 12. Success Metrics (KPIs)

### Student Engagement
- Daily Active Students: > 80% of enrolled
- Encounters per Student per Week: > 10
- AI Suggestion Acceptance Rate: > 75%
- Portfolio Export Rate at Graduation: > 30%

### Patient Outcomes
- Wallet Creation Rate: > 80% of encounters
- Patient Record Access (within 24h): > 60%
- Data Portability Success: > 95%
- Patient Satisfaction Score: > 4.2/5

### System Performance
- Supervisor Review Time: < 2 minutes per encounter
- System Uptime: > 99.5%
- AI Diagnostic Accuracy: > 85% (validated against supervisor diagnosis)
- Credit Verification Rate: > 90%

### Business Metrics
- Hospitals Deployed: 1 (pilot) → 5 (Y1) → 40+ (Y3)
- Students Onboarded: 500 (pilot) → 5,000 (Y1) → 40,000 (Y3)
- Patients with Wallets: 10,000 (pilot) → 100,000 (Y1) → 1M (Y3)

---

## 13. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| AI misdiagnosis | Medium | High | Human-in-the-loop; supervisor verification mandatory; confidence thresholds |
| Data breach | Low | Critical | Encryption at rest + in transit; audit logs; minimal data collection |
| Regulatory rejection (MDCN) | Medium | High | Engage MDCN early; frame as documentation tool, not diagnostic replacement |
| Patient adoption (no smartphone) | Medium | Medium | SMS fallback; USSD option; paper QR codes |
| Hospital IT resistance | Medium | Medium | Pilot with enthusiastic department; demonstrate time savings for supervisors |
| Chekk API unavailability | Low | Medium | Build abstraction layer; mock for demo; local fallback storage |
| Student resistance to documentation | Medium | Medium | Gamification (credits, streaks, leaderboards); integrate into grading |

---

## 14. Competitive Analysis

| Competitor | Strength | Weakness | Our Advantage |
|------------|----------|----------|---------------|
| **OpenMRS** | Open source, widely used | No student tracking; no patient wallets; dated UI | AI assistance + portfolio + data sovereignty |
| **Reliance HMO** | Insurance integration; telemedicine | No student education focus; no data portability | Built for education + patient ownership |
| **Babylon Health** | Strong AI diagnostics | Not available in Nigeria; no student portfolio | Nigerian context; supervisor oversight; credits |
| **Ada Health** | Consumer symptom checker | No clinical workflow; no documentation | Integrated into clinical encounter flow |
| **Paper records** | Zero cost; no training | Lost, illegible, non-portable | Digital, permanent, portable, AI-enhanced |

---

## 15. Go-to-Market Strategy

### Phase 1: Pilot (Months 1-3)
- **Target:** LAUTECH Teaching Hospital, Internal Medicine Department
- **Users:** 50 final-year students, 5 supervisors
- **Goal:** Validate encounter flow, AI accuracy, supervisor adoption
- **Metrics:** 500 encounters, 80% AI acceptance, 90% supervisor approval

### Phase 2: Department Expansion (Months 4-6)
- **Target:** All departments at LAUTECH (Surgery, Pediatrics, O&G, Emergency)
- **Users:** 200 students, 20 supervisors
- **Goal:** Prove cross-specialty viability
- **Metrics:** 5,000 encounters, 5 new MCP skills

### Phase 3: Multi-Hospital (Months 7-12)
- **Target:** 5 teaching hospitals (LUTH, UCH, UNTH, ABUTH, OAUTH)
- **Users:** 2,000 students, 100 supervisors
- **Goal:** Demonstrate scale and standardization
- **Metrics:** 50,000 encounters, MDCN partnership discussion

### Phase 4: National (Year 2)
- **Target:** All 40+ Nigerian teaching hospitals
- **Users:** 40,000 students
- **Goal:** Become standard for medical education documentation
- **Metrics:** 1M encounters, 500,000 patient wallets

---

## 16. Team Roles

| Role | Responsibility | Tech Stack |
|------|---------------|------------|
| **Backend Lead** | API design, database, AI integration, MCP skills | FastAPI, PostgreSQL, SQLModel, OpenAI API |
| **Frontend Lead** | UI/UX implementation, component library, state management | React, Tailwind, Chart.js, React Query |
| **DevOps/Full-Stack** | Deployment, CI/CD, infrastructure, security | Docker, AWS/GCP, Nginx, SSL |
| **Product/Design** | User research, wireframes, pitch deck, demo script | Figma, Google Slides |
| **Medical Advisor** | Clinical validation, supervisor onboarding, regulatory guidance | Clinical knowledge, MDCN relationships |

---

## 17. Hackathon Demo Script (3 Minutes)

### 0:00-0:15 — Hook
> "Every year, 40,000 Nigerian medical students perform millions of supervised consultations. Every single one of those encounters dies on paper. The student learns nothing about their accuracy. The patient leaves with nothing. Clinix changes both."

### 0:15-0:45 — The Problem (Dashboard)
Show dashboard. Point to stats:
> "This is Ademilua — a 500L student at LAUTECH. He's seen 47 patients, but he has no idea if his diagnoses were right. His notes are on paper that gets lost. His patients lose their cards and start from zero at every hospital."

### 0:45-1:30 — The Solution (New Encounter)
Click "New Encounter". Select Fatima Abdullahi.
> "Fatima comes in with fever and headache. Instead of paper, Ademilua opens Clinix. He documents her symptoms — and the AI doesn't just chat. It analyzes."

Type symptoms. AI analysis appears:
> "The AI detects a malaria pattern with 92% confidence. But here's the key — it doesn't stop at diagnosis. Via MCP Action Skills, it checks if Coartem is in stock. It recommends an RDT. It schedules her Day 3 follow-up. All drafted, not executed. Ademilua verifies everything."

### 1:30-2:00 — Physical Exam & Finalize
Fill vitals. Add diagnosis and treatment.
> "Ademilua conducts his exam, confirms the AI suggestions, and finalizes the encounter. His supervisor reviews and approves. And now — the patient gets her record."

### 2:00-2:30 — Data Wallet Push
Click "Finalize". QR code modal appears.
> "This QR code goes to Fatima's phone. She scans it, and her entire encounter — diagnosis, vitals, treatment, follow-up — is encrypted and pushed to her Chekk Data Wallet. She owns it. Forever. Portable to any hospital in Nigeria."

Click "Send to Patient". Success modal:
> "And for Ademilua? He just earned 8 Verified Clinical Credits. Cryptographically signed. Added to his portfolio. Ready for MDCN or any international residency program."

### 2:30-3:00 — Portfolio & Close
Show portfolio view.
> "Every encounter builds this portfolio. 47 encounters. 94% diagnostic accuracy. 156 credits. All verified. All signed. This is what Clinix does — it makes every supervised consultation count. For the student. And for the patient."

> "We're piloting at LAUTECH next month. We need mentorship and deployment partnership to scale to every teaching hospital in Nigeria. Thank you."

---

## 18. Appendix

### A. Glossary

| Term | Definition |
|------|------------|
| **MCP** | Model Context Protocol — standard for connecting AI assistants to external data and tools |
| **Action Skill** | Automated workflow triggered by AI based on clinical patterns |
| **Data Wallet** | Patient-owned, encrypted health record storage (via Chekk) |
| **Clinical Credit** | Verified competency point earned per encounter category |
| **Verified Portfolio** | Cryptographically-signed record of student clinical competence |
| **PHI** | Protected Health Information — any health data that can identify a patient |
| **MDCN** | Medical and Dental Council of Nigeria — regulatory body |

### B. External Integrations

| Service | Purpose | API Docs | Status |
|---------|---------|----------|--------|
| **Chekk** | Patient data wallets | https://docs.chekk.io | Mock for MVP |
| **OpenAI GPT-4** | Clinical AI analysis | https://platform.openai.com | Mock for MVP |
| **Twilio** | SMS notifications to patients | https://www.twilio.com/docs | Mock for MVP |
| **Hospital HIS** | Patient admission data | Internal (varies by hospital) | Future |
| **Lab Information System** | Test results | Internal (varies by hospital) | Future |

### C. Mock Data

**Demo Student:**
```json
{
  "id": "uuid",
  "email": "adeola@clinix.ng",
  "first_name": "Ademilua",
  "last_name": "Adeola",
  "role": "student",
  "year_of_study": 5,
  "hospital": "LAUTECH Teaching Hospital"
}
```

**Demo Patients (Queue):**
```json
[
  {
    "id": "uuid-1",
    "hospital_id": "LTH-2024-001",
    "first_name": "Fatima",
    "last_name": "Abdullahi",
    "age": 34,
    "gender": "F",
    "chief_complaint": "Fever, headache, chills",
    "waiting_time_minutes": 12,
    "priority": "urgent"
  },
  {
    "id": "uuid-2",
    "hospital_id": "LTH-2024-002",
    "first_name": "James",
    "last_name": "Okafor",
    "age": 52,
    "gender": "M",
    "chief_complaint": "Chest pain, shortness of breath",
    "waiting_time_minutes": 8,
    "priority": "waiting"
  },
  {
    "id": "uuid-3",
    "hospital_id": "LTH-2024-003",
    "first_name": "Chioma",
    "last_name": "Adeleke",
    "age": 28,
    "gender": "F",
    "chief_complaint": "Prenatal checkup, 28 weeks",
    "waiting_time_minutes": 5,
    "priority": "waiting"
  }
]
```

### D. Development Milestones

| Milestone | Deadline | Deliverable |
|-----------|----------|-------------|
| Database schema + models | Day 1, 6PM | Migrations, seed data |
| Auth system | Day 1, 10PM | Register, login, JWT, protected routes |
| Patient CRUD + queue | Day 2, 10AM | Patient list, search, queue endpoint |
| Encounter workflow | Day 2, 6PM | Create, update, AI analyze, finalize |
| AI mock service | Day 2, 8PM | Symptom analysis, MCP skills |
| Wallet push + QR | Day 3, 10AM | Encryption, QR generation, mock Chekk |
| Portfolio + credits | Day 3, 2PM | Credit calculation, charts, export |
| Frontend integration | Day 3, 6PM | All views connected to API |
| Polish + demo prep | Day 3, 10PM | Animations, toast, modal, demo script |
| Final rehearsal | Day 4, 8AM | Full run-through, bug fixes |

---

**Document Owner:** Ademilua Adeola  
**Last Updated:** June 28, 2026  
**Next Review:** Post-hackathon retrospective