"""
1. 가상(synthetic) EMR 생성.

주의: 아래 데이터는 전부 random 모듈로 만들어낸 가상 환자 기록이며,
실제 환자 정보는 전혀 포함되어 있지 않다 (교육/과제 목적의 synthetic data).
"""

import random

import pandas as pd

import config

DIAGNOSES = [
    "Heart Failure with Reduced Ejection Fraction (HFrEF)",
    "Heart Failure with Preserved Ejection Fraction (HFpEF)",
    "Congestive Heart Failure (CHF)",
    "Acute Decompensated Heart Failure",
]

CHIEF_COMPLAINTS = [
    "Shortness of breath",
    "Leg swelling",
    "Generalized fatigue",
    "Chest discomfort",
    "Weight gain over a week",
    "Difficulty breathing when lying down",
]

PAST_HISTORY_POOL = [
    "Hypertension",
    "Diabetes Mellitus",
    "Coronary Artery Disease",
    "Atrial Fibrillation",
    "Prior Myocardial Infarction",
    "Chronic Kidney Disease",
    "Hyperlipidemia",
]

MEDICATION_POOL = [
    "Furosemide",
    "Lisinopril",
    "Carvedilol",
    "Spironolactone",
    "Digoxin",
    "Metoprolol",
    "Sacubitril/Valsartan",
    "Enalapril",
    "Losartan",
    "Bisoprolol",
    "Empagliflozin",
    "Torsemide",
]

ALLERGY_POOL = ["None"] * 5 + ["Penicillin", "Sulfa drugs", "NSAIDs", "Aspirin"]

SYMPTOM_POOL = [
    "Dyspnea on exertion",
    "Orthopnea",
    "Paroxysmal nocturnal dyspnea",
    "Fatigue",
    "Leg edema",
    "Weight gain",
    "Palpitations",
    "Chest discomfort",
    "Cough",
    "Decreased appetite",
]

SEX_LABELS = {"M": "male", "F": "female"}


def _random_lab_results(rng):
    ef = rng.randint(15, 60)
    bnp = rng.randint(100, 1500)
    creatinine = round(rng.uniform(0.7, 2.5), 1)
    sodium = rng.randint(128, 142)
    potassium = round(rng.uniform(3.3, 5.4), 1)
    return (
        f"Ejection Fraction {ef}%, BNP {bnp} pg/mL, "
        f"Creatinine {creatinine} mg/dL, Sodium {sodium} mEq/L, "
        f"Potassium {potassium} mEq/L"
    )


def _make_clinical_note(rng, age, sex, chief_complaint, diagnosis, past_history,
                         medications, symptoms, lab_results, allergy):
    sex_word = SEX_LABELS[sex]
    allergy_text = "No known drug allergy" if allergy == "None" else f"Allergy to {allergy}"
    return (
        f"{age}-year-old {sex_word} presenting with {chief_complaint.lower()}. "
        f"Symptoms include {', '.join(s.lower() for s in symptoms)}. "
        f"Diagnosed with {diagnosis}. Past medical history of {past_history}. "
        f"Currently on {medications}. {allergy_text}. "
        f"Lab results: {lab_results}."
    )


def generate_emr(n_patients=None, seed=None):
    """가상 EMR DataFrame 을 생성한다."""
    n_patients = n_patients or config.N_PATIENTS
    seed = config.RANDOM_SEED if seed is None else seed
    rng = random.Random(seed)

    rows = []
    for i in range(1, n_patients + 1):
        age = rng.randint(45, 90)
        sex = rng.choice(["M", "F"])
        chief_complaint = rng.choice(CHIEF_COMPLAINTS)
        diagnosis = rng.choice(DIAGNOSES)
        past_history = ", ".join(rng.sample(PAST_HISTORY_POOL, k=rng.randint(1, 3)))
        medications = ", ".join(rng.sample(MEDICATION_POOL, k=rng.randint(2, 4)))
        allergy = rng.choice(ALLERGY_POOL)
        symptoms = rng.sample(SYMPTOM_POOL, k=rng.randint(2, 4))
        lab_results = _random_lab_results(rng)
        clinical_note = _make_clinical_note(
            rng, age, sex, chief_complaint, diagnosis, past_history,
            medications, symptoms, lab_results, allergy,
        )

        rows.append({
            "patient_id": f"P{i:03d}",
            "age": age,
            "sex": sex,
            "chief_complaint": chief_complaint,
            "diagnosis": diagnosis,
            "past_history": past_history,
            "medications": medications,
            "allergy": allergy,
            "symptoms": ", ".join(symptoms),
            "lab_results": lab_results,
            "clinical_note": clinical_note,
        })

    return pd.DataFrame(rows)


def run():
    df = generate_emr()
    df.to_csv(config.SYNTHETIC_EMR_CSV, index=False, encoding="utf-8-sig")
    print(f"  - {len(df)}명의 synthetic EMR 생성 완료 -> {config.SYNTHETIC_EMR_CSV}")
    return df


if __name__ == "__main__":
    run()
