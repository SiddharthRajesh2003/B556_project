-- ============================================================
-- B556 Biological Database Management - Fertility Clinic DB
-- Created from: ERD_final-final.pdf
-- ============================================================
DROP DATABASE IF EXISTS fertility_clinic;

CREATE DATABASE IF NOT EXISTS fertility_clinic;
USE fertility_clinic;

-- ============================================================
-- CORE TABLES
-- ============================================================

-- Health Care Provider Information
CREATE TABLE HealthCareProvider (
    HCP_ID      INT AUTO_INCREMENT PRIMARY KEY,
    HCP_Type    VARCHAR(50),
    First_Name  VARCHAR(50) NOT NULL,
    Last_Name   VARCHAR(50) NOT NULL,
    Specialty   VARCHAR(100),
    Gender      VARCHAR(20)
);

-- Patient Information
CREATE TABLE PatientInformation (
    Patient_ID      INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT NULL,
    First_Name      VARCHAR(50)  NOT NULL,
    Last_Name       VARCHAR(50)  NOT NULL,
    DOB             DATE,
    Patient_Type    ENUM('Male', 'Female') NOT NULL,
    Sex_at_Birth    ENUM('Male', 'Female', 'Intersex'),
    Patient_Gender  VARCHAR(30),
    Treatment_Plan  TEXT
);

-- Patient Medical History  (1:1 with PatientInformation)
CREATE TABLE PatientMedicalHistory (
    Patient_ID          INT          PRIMARY KEY,
    Diabetes_Status     VARCHAR(50),
    Height              DECIMAL(5,2) COMMENT 'As recorded in source data',
    Weight              DECIMAL(5,2) COMMENT 'As recorded in source data',
    Blood_Type          VARCHAR(5),
    Medical_Conditions  TEXT,
    Surgical_History    TEXT,
    Alcohol_Use         VARCHAR(50),
    CONSTRAINT fk_medhistory_patient
        FOREIGN KEY (Patient_ID) REFERENCES PatientInformation(Patient_ID)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- Female Patients  (subtype of PatientInformation)
CREATE TABLE FemalePatients (
    Patient_ID                  INT          PRIMARY KEY,
    CycleNumber                 INT,
    LengthofCycle               INT,
    MeanCycleLength             DECIMAL(5,2),
    EstimatedDayofOvulation     INT,
    ReproductiveCategory        INT          COMMENT '0=normal, other values per study coding',
    TotalDaysofFertility        INT,
    MeanMensesLength            DECIMAL(5,2),
    TotalMensesScore            INT,
    UnusualBleeding             TINYINT(1),
    Numberpreg                  INT,
    Livingkids                  INT,
    Miscarriages                INT,
    Abortions                   INT,
    Breastfeeding               TINYINT(1),
    CONSTRAINT fk_female_patient
        FOREIGN KEY (Patient_ID) REFERENCES PatientInformation(Patient_ID)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- Male Patients  (subtype of PatientInformation)
CREATE TABLE MalePatients (
    Patient_ID      INT          PRIMARY KEY,
    Trauma_History  TINYINT(1)   COMMENT '1=yes, 0=no',
    Fever_History   VARCHAR(50)  COMMENT 'e.g. "more than 3 months ago", "less than 3 months ago"',
    Activity_Levels DECIMAL(4,1) COMMENT 'Hours spent sitting per day',
    Diagnosis       VARCHAR(20)  COMMENT 'Normal or Altered',
    CONSTRAINT fk_male_patient
        FOREIGN KEY (Patient_ID) REFERENCES PatientInformation(Patient_ID)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- ============================================================
-- APPOINTMENTS & RESULTS
-- ============================================================

-- Appointments
CREATE TABLE Appointments (
    Appointment_ID  INT AUTO_INCREMENT PRIMARY KEY,
    Patient_ID      INT  NOT NULL,
    HCP_ID          INT  NOT NULL,
    Scheduled_Date  DATE NOT NULL,
    Scheduled_Time  TIME,
    Duration        INT            COMMENT 'Duration in minutes',
    Room_Number     VARCHAR(20),
    CONSTRAINT fk_appt_patient
        FOREIGN KEY (Patient_ID) REFERENCES PatientInformation(Patient_ID)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_appt_hcp
        FOREIGN KEY (HCP_ID) REFERENCES HealthCareProvider(HCP_ID)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Results
CREATE TABLE Results (
    Result_ID       INT AUTO_INCREMENT PRIMARY KEY,
    Appointment_ID  INT NOT NULL,
    Procedure_Name  VARCHAR(100),
    Type            VARCHAR(50),
    Result          TEXT,
    CONSTRAINT fk_result_appt
        FOREIGN KEY (Appointment_ID) REFERENCES Appointments(Appointment_ID)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- ============================================================
-- SAMPLE INVENTORY & SPECIMENS
-- ============================================================

-- Sample Inventory
CREATE TABLE SampleInventory (
    Storage_ID          INT AUTO_INCREMENT PRIMARY KEY,
    Storage_Temperature DECIMAL(6,2) COMMENT 'Temperature in Celsius'
);

-- Sperm Specimen Information
CREATE TABLE SpermSpecimen (
    Barcode                   VARCHAR(50)  PRIMARY KEY,
    Patient_ID                INT          NOT NULL,
    Storage_ID                INT,
    Collection_Date           DATE,
    Sperm_Concentration       DECIMAL(10,2) COMMENT 'million/mL',
    Total_Sperm_Count         DECIMAL(10,2) COMMENT 'million',
    Ejaculate_Volume          DECIMAL(5,2)  COMMENT 'mL',
    Sperm_Vitality            DECIMAL(5,2)  COMMENT '%',
    Normal_Spermatozoa        DECIMAL(5,2)  COMMENT '%',
    Cytoplasmic_Droplet       DECIMAL(5,2)  COMMENT '%',
    Teratozoospermia_Index    DECIMAL(5,2),
    Progressive_Motility      DECIMAL(5,2)  COMMENT '%',
    High_DNA_Stainability     DECIMAL(5,2)  COMMENT '%',
    DNA_Fragmentation_Index   DECIMAL(5,2)  COMMENT '%',
    CONSTRAINT fk_sperm_patient
        FOREIGN KEY (Patient_ID) REFERENCES PatientInformation(Patient_ID)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_sperm_inventory
        FOREIGN KEY (Storage_ID) REFERENCES SampleInventory(Storage_ID)
        ON DELETE SET NULL ON UPDATE CASCADE
);

-- Oocyte Specimen Information
CREATE TABLE OocyteSpecimen (
    Barcode               VARCHAR(50) PRIMARY KEY,
    Patient_ID            INT         NOT NULL,
    Storage_ID            INT,
    Collection_Date       DATE,
    Maturity              VARCHAR(50),
    Retrieval_Method      VARCHAR(100),
    Count                 INT,
    Fertilization_Status  VARCHAR(50),
    CONSTRAINT fk_oocyte_patient
        FOREIGN KEY (Patient_ID) REFERENCES PatientInformation(Patient_ID)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_oocyte_inventory
        FOREIGN KEY (Storage_ID) REFERENCES SampleInventory(Storage_ID)
        ON DELETE SET NULL ON UPDATE CASCADE
);

-- Embryo Information
CREATE TABLE EmbryoInformation (
    Barcode         VARCHAR(50)   PRIMARY KEY,
    Patient_ID      INT           NOT NULL,
    Storage_ID      INT,
    Collection_Date DATE,
    Volume          DECIMAL(5,2)  COMMENT 'mL',
    Motility        DECIMAL(5,2)  COMMENT '%',
    Concentration   DECIMAL(10,2) COMMENT 'million/mL',
    CONSTRAINT fk_embryo_patient
        FOREIGN KEY (Patient_ID) REFERENCES PatientInformation(Patient_ID)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_embryo_inventory
        FOREIGN KEY (Storage_ID) REFERENCES SampleInventory(Storage_ID)
        ON DELETE SET NULL ON UPDATE CASCADE
);

-- ============================================================
-- JUNCTION TABLES  (Many-to-Many relationships)
-- ============================================================

-- Sperm <-> Embryo  (Sperm_Embryo)
CREATE TABLE Sperm_Embryo (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    Sperm_Barcode   VARCHAR(50),
    Embryo_Barcode  VARCHAR(50),
    UNIQUE KEY uq_sperm_embryo (Sperm_Barcode, Embryo_Barcode),
    CONSTRAINT fk_se_sperm
        FOREIGN KEY (Sperm_Barcode)  REFERENCES SpermSpecimen(Barcode)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_se_embryo
        FOREIGN KEY (Embryo_Barcode) REFERENCES EmbryoInformation(Barcode)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- Oocyte <-> Embryo  (Oocyte_Embryo)
CREATE TABLE Oocyte_Embryo (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    Oocyte_Barcode  VARCHAR(50),
    Embryo_Barcode  VARCHAR(50),
    UNIQUE KEY uq_oocyte_embryo (Oocyte_Barcode, Embryo_Barcode),
    CONSTRAINT fk_oe_oocyte
        FOREIGN KEY (Oocyte_Barcode) REFERENCES OocyteSpecimen(Barcode)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_oe_embryo
        FOREIGN KEY (Embryo_Barcode) REFERENCES EmbryoInformation(Barcode)
        ON DELETE CASCADE ON UPDATE CASCADE
);
