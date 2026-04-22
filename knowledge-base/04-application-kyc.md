# 04 — Application & e-KYC

The scheme does not accept individual online applications through the public portal. Registration happens **offline through government-run camps**, then operators upload the form on the admin portal.

## Where to apply

Any one of the following collection points:

- **Gram Panchayat office** (rural)
- **Ward office** (urban)
- **Designated camp site** (shivirs) — these are set up on announced dates in each area
- **Aanganwadi centre** — secondary collection point in some blocks

## Documents required at the camp

| Document | Purpose |
|---|---|
| Samagra Family ID (समग्र परिवार आईडी) | Primary identifier in the MP welfare stack |
| Samagra Member ID (समग्र सदस्य आईडी) | Hers specifically |
| Aadhaar card | Identity + linking |
| Bank passbook / account details | Must be her own, DBT-enabled |
| Mobile number | For OTP and SMS alerts — must be her own |
| Passport-size photograph | For the form |

Ration card, voter ID, and income certificate are commonly requested as supporting documents but are not universally mandatory — Samagra + Aadhaar + bank is the load-bearing trio.

## Mandatory: Samagra e-KYC

**Without a completed Samagra e-KYC, the application will not be processed and no money will be transferred.** This is the #1 reason for "my form was submitted but I haven't got the money" complaints.

### Online e-KYC (self-service)

1. Go to `samagra.gov.in`
2. Under *Update Samagra Profile*, click *Do e-KYC*
3. Enter Samagra Member ID + captcha
4. Receive 6-digit OTP on registered mobile
5. Enter OTP to verify
6. System pulls Aadhaar details and completes linkage

### Offline e-KYC (biometric)

Visit any of:
- Ration shop (public distribution outlet)
- MP Online kiosk
- Common Service Centre (CSC)

Carry: Aadhaar card, PAN card (if available), bank passbook. Operator captures biometric (fingerprint) and completes e-KYC.

## Bank account linking — two checks often confused

A common support request is "I have Aadhaar but still no money." Clarify both:

1. **Aadhaar seeded with bank account** — the bank has noted the Aadhaar number against the account.
2. **Aadhaar-mapped to bank account in NPCI / enabled for DBT** — a separate step where the bank marks the Aadhaar-account pair as the one to receive DBT credits. If there are multiple accounts under one Aadhaar, only the most recently DBT-mapped one receives the money.

Both must be done. Beneficiaries can verify DBT mapping by sending a missed call to the NPCI / UIDAI helpline or checking on the Aadhaar bank seeding portal.

## Application status check

- Portal: `cmladlibahna.mp.gov.in` → "Application Status" → enter Samagra ID or application number
- Status possibilities: *Pending / Under Verification / Approved / Rejected with reason / Active — payment successful*

## Rejection: what to do

If the application is rejected, the portal shows the reason code. The most common reasons:
1. Age out of range
2. Samagra e-KYC incomplete
3. Income/asset disqualification flagged during field verification
4. Duplicate application for the same Samagra ID
5. Bank account not DBT-mapped

Rejection can be appealed via the Gram Panchayat / Ward office. There is no online appeal form.
