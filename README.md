# B556_project

PATIENT IS-A HIERARCHY DESIGN NOTES
1. PatientInformation acts as the supertype holding all shared demographic attributes (name, DOB, gender, etc.). FemalePatients and MalePatients are subtypes that store only sex-specific clinical data, avoiding NULL-heavy rows if a single wide table were used instead.
2. The subtype PK (Patient_ID) doubles as a FK back to PatientInformation, enforcing a strict 1:1 relationship and preventing orphaned subtype records.
3. Patient_Type ENUM in PatientInformation serves as the discriminator, signalling which subtype table to join without needing a separate lookup table.

GAMETE SPECIMEN DESIGN NOTES
1. SpermSpecimen, OocyteSpecimen, and EmbryoInformation each carry their own Barcode PK (lab-assigned identifier) and independently reference both Patient_ID and Storage_ID, allowing each specimen type to be tracked, stored, and queried without joining across specimen tables.
2. Storage_ID uses ON DELETE SET NULL so that removing a storage slot does not cascade-delete irreplaceable specimen records; the specimen row is retained with Storage_ID = NULL to flag it for reassignment.
3. Sperm-to-Embryo and Oocyte-to-Embryo are modelled as M:M junction tables (Sperm_Embryo, Oocyte_Embryo) because one embryo can originate from multiple gamete specimens and one gamete specimen can contribute to multiple embryos.