"""
load_synthea.py
---------------
1. Parses Synthea FHIR JSON bundles from data/fhir/ and loads:
     Practitioner -> HealthCareProvider
     Patient      -> PatientInformation + PatientMedicalHistory
     Encounter    -> Appointments + Results

2. Randomly assigns Kaggle fertility rows to matching Synthea patients:
     FedCycleData071012.csv  -> FemalePatients  (female patients only)
     fertility.csv           -> MalePatients    (male patients only)
     semen_analysis_data.csv -> SpermSpecimen   (male patients only)

Run from project root:
    pixi run python load_synthea.py
"""

import os
import csv
import json
import random
import django
import uuid
from pathlib import Path
from datetime import date, time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fertility_clinic.settings')
django.setup()

from patients.models import PatientInformation, PatientMedicalHistory, FemalePatients, MalePatients
from providers.models import HealthCareProvider
from appointments.models import Appointment, Result
from specimens.models import SpermSpecimen, OocyteSpecimen, SampleInventory

FHIR_DIR  = Path('data/fhir')
DATA_DIR  = Path('data')

patient_map      = {}  # fhir_id -> PatientInformation
practitioner_map = {}  # fhir_id -> HealthCareProvider


# ── Helpers ───────────────────────────────────────────────────────────────────

def _int(val):
    try:
        return int(float(val)) if val not in ('', None) else None
    except (ValueError, TypeError):
        return None

def _dec(val):
    try:
        return float(val) if val not in ('', None) else None
    except (ValueError, TypeError):
        return None

def _bool(val):
    if val is None or val == '':
        return None
    if isinstance(val, str):
        return val.strip().lower() in ('1', 'yes', 'true')
    return bool(val)

def extract_resources(bundle: dict) -> dict:
    resources = {}
    for entry in bundle.get('entry', []):
        r  = entry.get('resource', {})
        rt = r.get('resourceType')
        if rt:
            resources.setdefault(rt, []).append(r)
    return resources


# ── FHIR loaders ─────────────────────────────────────────────────────────────

def load_practitioners(resources: dict):
    for p in resources.get('Practitioner', []):
        fhir_id  = p.get('id', '')
        name     = p.get('name', [{}])[0]
        family   = name.get('family', 'Unknown')
        given    = (name.get('given') or ['Unknown'])[0]
        qual     = p.get('qualification', [{}])[0]
        code_txt = (qual.get('code', {})
                       .get('coding', [{}])[0]
                       .get('display', 'Physician'))
        hcp, _ = HealthCareProvider.objects.get_or_create(
            first_name=given, last_name=family,
            defaults={'hcp_type': code_txt, 'specialty': code_txt}
        )
        practitioner_map[fhir_id] = hcp
        print(f"  HCP: {given} {family}")


def load_patients(resources: dict):
    for p in resources.get('Patient', []):
        # Skip deceased patients — fertility clinic patients must be alive
        if p.get('deceasedDateTime') or p.get('deceasedBoolean') is True:
            print(f"  Skipping deceased patient: {p.get('id', '')}")
            continue

        fhir_id  = p.get('id', '')
        name     = p.get('name', [{}])[0]
        family   = name.get('family', 'Unknown')
        given    = (name.get('given') or ['Unknown'])[0]
        gender   = p.get('gender', 'unknown')
        dob_str  = p.get('birthDate')
        dob      = date.fromisoformat(dob_str) if dob_str else None

        # Skip patients outside the fertility clinic age range (20–50)
        if dob:
            today = date.today()
            age   = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if not (20 <= age <= 50):
                print(f"  Skipping out-of-range age ({age}): {given} {family}")
                continue

        sex_at_birth = 'Male'
        for ext in p.get('extension', []):
            if 'birthsex' in ext.get('url', ''):
                sex_at_birth = 'Female' if ext.get('valueCode', 'M') == 'F' else 'Male'

        pt_type = 'Female' if gender.lower() == 'female' else 'Male'

        pt, created = PatientInformation.objects.get_or_create(
            first_name=given, last_name=family, dob=dob,
            defaults={
                'patient_type':   pt_type,
                'sex_at_birth':   sex_at_birth,
                'patient_gender': gender.capitalize(),
            }
        )
        if created:
            PatientMedicalHistory.objects.get_or_create(patient=pt)
            print(f"  Patient: {given} {family} ({pt_type})")
        else:
            print(f"  Patient (exists): {given} {family}")
        patient_map[fhir_id] = pt


def load_encounters(resources: dict):
    for enc in resources.get('Encounter', []):
        pt_ref  = enc.get('subject', {}).get('reference', '')
        pt      = patient_map.get(pt_ref.split(':')[-1])
        if not pt:
            continue

        hcp = None
        for part in enc.get('participant', []):
            ref = part.get('individual', {}).get('reference', '')
            hcp = practitioner_map.get(ref.split(':')[-1])
            if hcp:
                break
        if not hcp:
            hcp = HealthCareProvider.objects.first()
        if not hcp:
            continue

        period = enc.get('period', {})
        start  = period.get('start', '')[:10] if period.get('start') else None
        if not start:
            continue

        room = str(random.randint(1, 10))
        hour = random.randint(9, 14)   # 9 AM – 2 PM so last slot ends by 3 PM
        appt_time = time(hour, random.choice([0, 30]))

        appt, created = Appointment.objects.update_or_create(
            patient=pt, hcp=hcp, scheduled_date=start,
            defaults={'room_number': room, 'scheduled_time': appt_time}
        )
        if created:
            reason     = enc.get('reasonCode', [{}])[0]
            reason_txt = (reason.get('coding', [{}])[0].get('display')
                          or reason.get('text', ''))
            if reason_txt:
                Result.objects.create(
                    appointment=appt,
                    procedure_name=reason_txt,
                    type='Encounter',
                    result='Recorded from Synthea FHIR export'
                )
            print(f"  Appointment: {pt} on {start}")


def process_bundle(path: Path):
    print(f"\nProcessing: {path.name}")
    with open(path, encoding='utf-8') as f:
        bundle = json.load(f)
    resources = extract_resources(bundle)
    load_practitioners(resources)
    load_patients(resources)
    load_encounters(resources)


# ── Kaggle CSV loaders ────────────────────────────────────────────────────────

FEMALE_ONLY_PROCEDURES   = {'ovarian cystectomy', 'histerectomy', 'bilateral masectomy'}
FEMALE_ONLY_CONDITIONS   = {'endometriosis', 'pcos'}
MALE_ONLY_PROCEDURES     = {'vasectomy', 'testicular removal', 'testicular torsion'}


def _row_gender(row):
    """Return 'F', 'M', or 'N' (neutral) based on procedure/condition in this row."""
    surgery   = row.get('Surgical History', '').strip().lower()
    condition = row.get('Medical Conditions', '').strip().lower()
    if surgery in FEMALE_ONLY_PROCEDURES or condition in FEMALE_ONLY_CONDITIONS:
        return 'F'
    if surgery in MALE_ONLY_PROCEDURES:
        return 'M'
    return 'N'


def _make_pool(rows, gender_code, count):
    """Return a shuffled pool of `count` rows compatible with gender_code (F or M)."""
    compatible = [r for r in rows if _row_gender(r) in (gender_code, 'N')]
    if not compatible:
        compatible = rows
    random.shuffle(compatible)
    return (compatible * ((count // len(compatible)) + 1))[:count]


def load_medical_history_data():
    """
    Randomly assign rows from 'Medical History.csv' to all patients whose
    PatientMedicalHistory record still has no data filled in.
    Female-only procedures/conditions go only to female patients; male-only to males.
    """
    csv_path = DATA_DIR / 'Medical History.csv'
    if not csv_path.exists():
        print("  'Medical History.csv' not found, skipping.")
        return

    with open(csv_path, encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))

    patients = list(
        PatientInformation.objects.filter(
            medical_history__height__isnull=True,
            medical_history__weight__isnull=True,
            medical_history__blood_type__isnull=True,
        )
    )
    if not patients:
        print("  No patients with empty medical history found.")
        return

    female_pts = [p for p in patients if p.patient_type == 'Female']
    male_pts   = [p for p in patients if p.patient_type == 'Male']

    female_pool = _make_pool(rows, 'F', len(female_pts))
    male_pool   = _make_pool(rows, 'M', len(male_pts))

    print(f"\nAssigning medical history data to {len(patients)} patient(s)...")
    for pt, row in list(zip(female_pts, female_pool)) + list(zip(male_pts, male_pool)):
        diabetes_raw = str(row.get('Diabetes Status', '')).strip().upper()
        alcohol_raw  = str(row.get('Alcohol Use', '')).strip().upper()
        PatientMedicalHistory.objects.update_or_create(
            patient=pt,
            defaults={
                'diabetes_status':    'Yes' if diabetes_raw == 'TRUE' else ('No' if diabetes_raw == 'FALSE' else None),
                'height':             _dec(row.get('Height')),
                'weight':             _dec(row.get('Weight ')),
                'blood_type':         row.get('Blood Type', '').strip() or None,
                'medical_conditions': row.get('Medical Conditions', '').strip() or None,
                'surgical_history':   row.get('Surgical History', '').strip() or None,
                'alcohol_use':        'Yes' if alcohol_raw == 'TRUE' else ('No' if alcohol_raw == 'FALSE' else None),
            }
        )
        print(f"  Medical history -> {pt}")


def load_female_cycle_data():
    """
    Randomly assign rows from FedCycleData071012.csv to female Synthea patients.
    Each patient gets one randomly sampled cycle row (without replacement where
    possible; wraps around if there are more patients than rows).
    """
    csv_path = DATA_DIR / 'FedCycleData071012.csv'
    if not csv_path.exists():
        print("  FedCycleData071012.csv not found, skipping.")
        return

    with open(csv_path, encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))

    female_patients = list(
        PatientInformation.objects.filter(patient_type='Female')
        .exclude(female_data__isnull=False)   # skip already assigned
    )
    if not female_patients:
        print("  No unassigned female patients found.")
        return

    # Shuffle rows so each run produces a different assignment
    random.shuffle(rows)
    # Cycle through rows if more patients than CSV rows
    row_pool = (rows * ((len(female_patients) // len(rows)) + 1))[:len(female_patients)]

    print(f"\nAssigning female cycle data to {len(female_patients)} patient(s)...")
    for pt, row in zip(female_patients, row_pool):
        FemalePatients.objects.update_or_create(
            patient=pt,
            defaults={
                'cycle_number':               _int(row.get('CycleNumber')),
                'length_of_cycle':            _int(row.get('LengthofCycle')),
                'mean_cycle_length':          _dec(row.get('MeanCycleLength')),
                'estimated_day_of_ovulation': _int(row.get('EstimatedDayofOvulation')),
                'reproductive_category':      _int(row.get('ReproductiveCategory')),
                'total_days_of_fertility':    _int(row.get('TotalDaysofFertility')),
                'mean_menses_length':         _dec(row.get('MeanMensesLength')),
                'total_menses_score':         _int(row.get('TotalMensesScore')),
                'unusual_bleeding':           _bool(row.get('UnusualBleeding')),
                'numberpreg':                 _int(row.get('Numberpreg')),
                'livingkids':                 _int(row.get('Livingkids')),
                'miscarriages':               _int(row.get('Miscarriages')),
                'abortions':                  _int(row.get('Abortions')),
                'breastfeeding':              _bool(row.get('Breastfeeding')),
            }
        )
        print(f"  Female data -> {pt}")


def load_male_fertility_data():
    """
    Randomly assign rows from fertility.csv to male Synthea patients.
    """
    csv_path = DATA_DIR / 'fertility.csv'
    if not csv_path.exists():
        print("  fertility.csv not found, skipping.")
        return

    with open(csv_path, encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))

    male_patients = list(
        PatientInformation.objects.filter(patient_type='Male')
        .exclude(male_data__isnull=False)
    )
    if not male_patients:
        print("  No unassigned male patients found.")
        return

    random.shuffle(rows)
    row_pool = (rows * ((len(male_patients) // len(rows)) + 1))[:len(male_patients)]

    # Map fertility.csv text values to model fields
    fever_map = {
        'more than 3 months ago': 'more than 3 months ago',
        'less than 3 months ago': 'less than 3 months ago',
        'no':                     'no fever',
    }

    print(f"\nAssigning male fertility data to {len(male_patients)} patient(s)...")
    for pt, row in zip(male_patients, row_pool):
        fever_raw = row.get('High fevers in the last year', '').strip().lower()
        MalePatients.objects.update_or_create(
            patient=pt,
            defaults={
                'trauma_history':  _bool(row.get('Accident or serious trauma')),
                'fever_history':   fever_map.get(fever_raw, fever_raw),
                'activity_levels': _dec(row.get('Number of hours spent sitting per day')),
                'diagnosis':       row.get('Diagnosis', '').strip() or None,
            }
        )
        print(f"  Male data -> {pt}")


def load_oocyte_data():
    """
    Randomly assign rows from merged-train-data-cleaned.csv to female patients
    as OocyteSpecimen records.  Maps Stage_at_Retrieval, Fert_Method, Sum_MII,
    and Fert_Status to the OocyteSpecimen model fields.
    """
    csv_path = DATA_DIR / 'merged-train-data-cleaned.csv'
    if not csv_path.exists():
        print("  merged-train-data-cleaned.csv not found, skipping.")
        return

    with open(csv_path, encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))

    female_patients = list(
        PatientInformation.objects.filter(patient_type='Female')
        .exclude(oocyte_specimens__isnull=False)
    )
    if not female_patients:
        print("  No unassigned female patients found for oocyte data.")
        return

    storage, _ = SampleInventory.objects.get_or_create(
        storage_id=1,
        defaults={'storage_temperature': -196.0}
    )

    # Only rows with a valid oocyte count
    valid_rows = [r for r in rows if r.get('Sum_MII', '').strip() not in ('', '*')]
    if not valid_rows:
        valid_rows = rows

    random.shuffle(valid_rows)
    row_pool = (valid_rows * ((len(female_patients) // len(valid_rows)) + 1))[:len(female_patients)]

    # Numeric codes used in the dataset
    fert_method_map = {'0': 'IVF', '1': 'ICSI', '2': 'GIFT', '3': 'ZIFT'}
    stage_map = {
        '1': 'MII', '2': 'MI', '3': 'GV',
        '4': '2-cell', '5': '4-cell', '6': '8-cell',
        '7': 'Morula', '8': 'Early Blastocyst', '9': 'Blastocyst',
        '10': 'Expanded Blastocyst',
    }
    fert_status_map = {
        '0': 'Unfertilized', '0.0': 'Unfertilized',
        '1': '1PN', '1.0': '1PN',
        '2': '2PN (Fertilized)', '2.0': '2PN (Fertilized)',
        '3': '3PN (Abnormal)', '3.0': '3PN (Abnormal)',
    }

    print(f"\nAssigning oocyte specimen data to {len(female_patients)} patient(s)...")
    for pt, row in zip(female_patients, row_pool):
        stage_raw  = str(row.get('Stage_at_Retrieval', '')).strip()
        method_raw = str(row.get('Fert_Method', '')).strip()
        status_raw = str(row.get('Fert_Status', '')).strip()

        barcode = f"OC-{uuid.uuid4().hex[:10].upper()}"
        OocyteSpecimen.objects.create(
            barcode=barcode,
            patient=pt,
            storage=storage,
            collection_date=date.today(),
            maturity=stage_map.get(stage_raw, f"Stage {stage_raw}" if stage_raw else None),
            retrieval_method=fert_method_map.get(method_raw, method_raw or None),
            count=_int(row.get('Sum_MII')),
            fertilization_status=fert_status_map.get(status_raw, status_raw or None),
        )
        print(f"  Oocyte specimen [{barcode}] -> {pt}")


def load_semen_data():
    """
    Randomly assign rows from semen_analysis_data.csv to male Synthea patients
    as SpermSpecimen records.  Each patient gets one specimen with a generated
    barcode and a randomly assigned storage slot.
    """
    csv_path = DATA_DIR / 'semen_analysis_data.csv'
    if not csv_path.exists():
        print("  semen_analysis_data.csv not found, skipping.")
        return

    with open(csv_path, encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))

    male_patients = list(
        PatientInformation.objects.filter(patient_type='Male')
        .exclude(sperm_specimens__isnull=False)
    )
    if not male_patients:
        print("  No unassigned male patients found for semen data.")
        return

    # Ensure at least one storage slot exists
    storage, _ = SampleInventory.objects.get_or_create(
        storage_id=1,
        defaults={'storage_temperature': -196.0}  # liquid nitrogen
    )

    random.shuffle(rows)
    row_pool = (rows * ((len(male_patients) // len(rows)) + 1))[:len(male_patients)]

    print(f"\nAssigning semen analysis data to {len(male_patients)} patient(s)...")
    for pt, row in zip(male_patients, row_pool):
        barcode = f"SP-{uuid.uuid4().hex[:10].upper()}"
        SpermSpecimen.objects.create(
            barcode=barcode,
            patient=pt,
            storage=storage,
            collection_date=date.today(),
            sperm_concentration=  _dec(row.get('Sperm concentration (x10⁶/mL)')),
            total_sperm_count=    _dec(row.get('Total sperm count (x10⁶)')),
            ejaculate_volume=     _dec(row.get('Ejaculate volume (mL)')),
            sperm_vitality=       _dec(row.get('Sperm vitality (%)')),
            normal_spermatozoa=   _dec(row.get('Normal spermatozoa (%)')),
            cytoplasmic_droplet=  _dec(row.get('Cytoplasmic droplet (%)')),
            teratozoospermia_index=_dec(row.get('Teratozoospermia index')),
            progressive_motility= _dec(row.get('Progressive motility (%)')),
            high_dna_stainability=_dec(row.get('High DNA stainability, HDS %')),
            dna_fragmentation_index=_dec(row.get('DNA fragmentation index,  DFI (%)')),
        )
        print(f"  Semen specimen [{barcode}] -> {pt}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    random.seed()  # non-deterministic; use random.seed(42) for reproducibility

    print("=== Loading Synthea FHIR bundles ===")
    for path in sorted(FHIR_DIR.glob('practitioner*.json')):
        process_bundle(path)
    for path in sorted(FHIR_DIR.glob('*.json')):
        if 'practitioner' in path.name or 'hospital' in path.name:
            continue
        process_bundle(path)

    print("\n=== Assigning Kaggle fertility data ===")
    load_medical_history_data()
    load_female_cycle_data()
    load_oocyte_data()
    load_male_fertility_data()
    load_semen_data()

    print("\n=== Summary ===")
    print(f"  Patients:     {PatientInformation.objects.count()}")
    print(f"  Providers:    {HealthCareProvider.objects.count()}")
    print(f"  Appointments: {Appointment.objects.count()}")
    print(f"  Results:      {Result.objects.count()}")
    print(f"  Med. history: {PatientMedicalHistory.objects.exclude(height__isnull=True).count()} filled")
    print(f"  Female data:  {FemalePatients.objects.count()}")
    print(f"  Male data:    {MalePatients.objects.count()}")
    print(f"  Oocyte spec.: {OocyteSpecimen.objects.count()}")
    print(f"  Sperm spec.:  {SpermSpecimen.objects.count()}")


if __name__ == '__main__':
    main()
