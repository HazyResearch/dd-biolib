PYTHONPATH=/Users/fries/Code/ddbiolib/ python create_dictionary.py -t "Pathologic Function|Sign or Symptom" > /users/fries/desktop/pathologic_function_symptom.txt

PYTHONPATH=/Users/fries/Code/ddbiolib/ python create_dictionary.py -t "Cell or Molecular Dysfunction" > /users/fries/desktop/cell_molecular_dysfunction.txt



PYTHONPATH=/Users/fries/Code/ddbiolib/ python create_dictionary.py -t "Embryonic Structure|Tissue|Body Part, Organ, or Organ Component|Anatomical Abnormality|Congenital Abnormality|Acquired Abnormality|Body Location or Region|Body Space or Junction" > /users/fries/desktop/umls_human_anatomy.txt


PYTHONPATH=/Users/fries/Code/ddbiolib/ python create_dictionary.py -t "Geographic Area" > /users/fries/desktop/umls_geographic_areas.txt



# Disorders

Cell or Molecular Dysfunction

PYTHONPATH=/Users/fries/Code/ddbiolib/ python create_dictionary.py -t "Acquired Abnormality|Anatomical Abnormality|Congenital Abnormality|Disease or Syndrome|Experimental Model of Disease|Finding|Injury or Poisoning|Mental or Behavioral Dysfunction|Neoplastic Process|Pathologic Function|Sign or Symptom" > /users/fries/desktop/umls_disorders.txt


export PYTHONPATH=/Users/fries/Code/ddbiolib/

python create_dictionary.py -t "Disease or Syndrome" -s "SNOMEDCT_US" > /users/fries/desktop/snomedct_disease_or_syndrome.txt
python create_dictionary.py -t "Sign or Symptom" -s "SNOMEDCT_US" > /users/fries/desktop/snomedct_sign_or_symptom.txt
python create_dictionary.py -t "Finding" -s "SNOMEDCT_US" > /users/fries/desktop/snomedct_finding.txt
python create_dictionary.py -t "Mental or Behavioral Dysfunction" -s "SNOMEDCT_US" > /users/fries/desktop/snomedct_finding.txt


python create_dictionary.py -t "Amino Acid, Peptide, or Protein" -s "SNOMEDCT_US" > /users/fries/desktop/snomedct.proteins.txt
python create_dictionary.py -t "Enzyme" -s "SNOMEDCT_US" > /users/fries/desktop/snomedct.enzyme.txt

python create_dictionary.py -t "Neoplastic Process" -s "SNOMEDCT_US" > /users/fries/desktop/snomedct.neoplastic_process.txt

python create_dictionary.py -t "Laboratory Procedure" -s "SNOMEDCT_US" > /users/fries/desktop/snomedct.lab_procedure.txt



python create_dictionary.py -t "Amino Acid, Peptide, or Protein|Enzyme|Gene or Genome" > /users/fries/desktop/all.proteins_enzymes.txt
