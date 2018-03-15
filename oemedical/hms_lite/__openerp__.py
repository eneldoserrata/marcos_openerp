{
	'name' : 'OpenERP 7 Hospital Management System (Lite)',  
	'version' : '1.0',
	'author' : 'The Proven Technology',
	'category' : 'Generic Modules/Others',
	'depends' : ['base','sale','purchase','account','product'],
	'description' : """

Hospital Management System (Lite) for OpenERP Version 7
=======================================================

Hospital Management System is a multi-user, highly scalable, centralized Electronic Medical Record (EMR) and Hospital Information System for openERP.
It provides a universal Health and Hospital Information System, so doctors and institutions all over the world, specially in developing countries will benefit from a centralized, high quality, secure and scalable system.


1) Main Module:


    * Strong focus in family medicine and Primary Health Care

    * Major interest in Socio-economics (housing conditions, substance abuse, education...)

    * Diseases and Medical procedures standards (like ICD-10 / ICD-10-PCS ...)

    * Patient Genetic and Hereditary risks : Over 4200 genes related to diseases (NCBI / Genecards)

    * Epidemiological and other statistical reports

    * 100% paperless patient examination and history taking

    * Patient Administration (creation, evaluations / consultations, history ... )

    * Doctor Administration

    * Lab Administration

    * Medicine / Drugs information

    * Medical stock and supply chain management

    * Hospital Financial Administration

    * Designed with industry standards in mind
    
2) Genetic Risks:

	* Family history, hereditary risks and genetic disorders. We included the NCBI and Genecard information, more than 4200 genes associated to diseases.

3) Lifestyle:

	* Eating habits and diets
	
	* Sleep patterns
		
	* Drug / alcohol addictions
	
	* Physical activity (workout / excercise )
	
	* Sexuality and sexual behaviours
	
4) Socioeconomics:

It takes care of the input of all the socio-economic factors that influence the health of the individual / family and society.
Among others, we include the following factors :

	* Living conditions
	
	* Educational level
	
	* Infrastructure (electricity, sewers, ... )
	
	* Family affection ( APGAR )
	
	* Drug addiction 
	
	* Hostile environment
	
	* Teenage Pregnancy
	
	* Working children

5) Inpatient Hospitalization:

	* Patient Registration
	
	* Bed reservation

	* Hospitalization

	* Nursing Plan
	
	* Discharge Plan
	
	* Reporting
	
6) World Health Organization International Classification of Diseases - ICD-10

7) Procedure Coding System for Medical : ICD-10-PCS. The ICD-10 Procedure Coding System (ICD-10-PCS) is system of medical classification used for procedural codes. The National Center for Health Statistics (NCHS) received permission from the World Health Organization (WHO) (the body responsible for publishing the International Classification of Diseases [ICD]) to create the ICD-10-PCS as a successor to Volume 3 of ICD-9-CM and a clinical modification of the original ICD-10.Each code consists of seven alphanumeric characters. The second through seventh characters mean the same thing within each section, but may mean different things in other sections. Each character can be any of 34 possible values the ten digits 0-9 and the 24 letters A-H,J-N and P-Z may be used in each character. The letters O and I excluded to avoid confusion with the numbers 0 and 1. There are no decimals in ICD-10-PCS.
   Check http://en.wikipedia.org/wiki/ICD-10_Procedure_Coding_System

""",
	"website" : "http://www.theproventechnology.com",
	"init" : [],
	"demo" : ["medical/demo/medical_demo.xml"],
	"data" : ["hms_menu.xml", "medical/medical_view.xml",
					"medical/medical_report.xml", 
					"medical/security/medical_security.xml",
					"medical/security/ir.model.access.csv",
					"medical/data/medical_sequences.xml",					
					"medical/data/ethnic_groups.xml",
					"medical/data/occupations.xml",
					"medical/data/dose_units.xml",
					"medical/data/HL7_drug_administration_routes.xml",
					"medical/data/medicament_form.xml",
					"medical/data/snomed_frequencies.xml",
					"medical/data/medicament_categories.xml",
					"medical/data/WHO_list_of_essential_medicines.xml",
					"medical/data/WHO_medicaments.xml",
					"medical/data/medical_specialties.xml",
					"medical/data/dose_units.xml",					
					"medical_genetics/medical_genetics_view.xml",
					"medical_genetics/data/genetic_risks.xml",
					"medical_lifestyle/medical_lifestyle_view.xml",
					"medical_lifestyle/data/recreational_drugs.xml",
					"medical_socioeconomics/medical_socioeconomics_view.xml",
					"medical_inpatient/medical_inpatient_view.xml", 
					"medical_inpatient/data/medical_inpatient_sequence.xml",
					"medical_icd10/data/disease_categories.xml",
			  		"medical_icd10/data/diseases.xml",
			  		"medical_icd10pcs/data/icd_10_pcs_2009_part1.xml",
			  		"medical_icd10pcs/data/icd_10_pcs_2009_part2.xml",
			  		"medical_icd10pcs/data/icd_10_pcs_2009_part3.xml"
			],
	"active": False 
}
