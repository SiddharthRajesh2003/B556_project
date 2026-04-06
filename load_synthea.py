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
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fertility_clinic.settings')
django.setup()

from patients.models import PatientInformation, PatientMedicalHistory, FemalePatients, MalePatients
from providers.models import HealthCareProvider
from appointments.models import Appointment, Result
from specimens.models import SpermSpecimen, SampleInventory

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
        fhir_id  = p.get('id', '')
        name     = p.get('name', [{}])[0]
        family   = name.get('family', 'Unknown')
        given    = (name.get('given') or ['Unknown'])[0]
        gender   = p.get('gender', 'unknown')
        dob_str  = p.get('birthDate')
        dob      = date.fromisoformat(dob_str) if dob_str else None

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

        locs = enc.get('location', [])
        room = locs[0].get('location', {}).get('display') if locs else None

        appt, created = Appointment.objects.get_or_create(
            patient=pt, hcp=hcp, scheduled_date=start,
            defaults={'room_number': room}
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
    load_female_cycle_data()
    load_male_fertility_data()
    load_semen_data()

    print("\n=== Summary ===")
    print(f"  Patients:     {PatientInformation.objects.count()}")
    print(f"  Providers:    {HealthCareProvider.objects.count()}")
    print(f"  Appointments: {Appointment.objects.count()}")
    print(f"  Results:      {Result.objects.count()}")
    print(f"  Female data:  {FemalePatients.objects.count()}")
    print(f"  Male data:    {MalePatients.objects.count()}")
    print(f"  Sperm spec.:  {SpermSpecimen.objects.count()}")


if __name__ == '__main__':
    main()
