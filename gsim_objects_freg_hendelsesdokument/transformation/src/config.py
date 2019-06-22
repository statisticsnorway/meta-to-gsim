##################################################################################
### config-fil for transformasjon fra Skatteetatens XSD til SSBs GSIM-objekter ###
##################################################################################
import pprint
# "Key-word" for data/metadata-området som XSD-en fra Skatteetaten dekker, f.eks. "FREG", "Folkeregisteret", "Skattemelding", osv.
# Brukes bl.a. ved generering av "GSIM DataResource"-objektet og til "tagging" og i description-felter i andre GSIM-objekter.
dataResource = "DokumentForHendelse"

# Sti og navn til XSD-filen fra Skatteetaten:
#xsdSourcePath = '..//..//..//skattemelding//source_metadata//'
xsdSourcePath = 'C:\\utvikling\\Test\\xsdFiles\\'
xsdSourceFile = 'Hendelsedokument_v1.2.xsd'
# .. og navn på ryddet/forenklet XSD-fil (output fra scriptet "cleanXsdFile.py")
xsdCleanedFile = 'CLEANED_' + xsdSourceFile


# "innslagspunktet" i XSD (ønsket "start-punkt-element" i XSD hvor det skal leses rekursivt fra), eksempel "SkattemeldingUtflatet" og "folkeregisterperson"
xsdStartingPointElement = "Registerdata"
# .. og xsd-path til "innslagspunktet" for "xsdStartingPointElement"
# xsdStartingPointPath = "uttrekkSkattemelding/skattepliktig/"
xsdStartingPointPath = "dokumentForHendelse/hendelse/egenskapshendelse/"

# Sti til katalogen de genererte JSON-filene med GSIM-struktur skal lagres i (output fra scriptet "Xsd2Gsim.py")
#jsonGsimTargetPath = '..//..//..//skattemelding//gsim_objects//'
jsonGsimTargetPath = 'C:\\utvikling\\Test\\gsim_objects_freg_hendelsesdokument\\'


# Sti til katalogen mapping-json-objektene fra rådata til inndata skal lagres (output fra scriptet "Xsd2Gsim.py")
mappingObjectSubPath = '_mapping//'
jsonMappingObjectFullPath = jsonGsimTargetPath + mappingObjectSubPath

def printDict(dict):
    pp = pprint.PrettyPrinter(indent=4, compact=False)
    pp.pprint(dict)
    

    
# Definere identifierComponents-variabler med name, type, rawDataSourcePath og dataStructureComponentRole
# TODO: Definere spesifikke indentifierCompnents for hver logiske record også, f.eks. "kontonummer" for "konto"?
identifierComponents = [
    {"name": "dokumentidentifikator",
     "type": "xsd:string",
     #"rawDataSourcePath": "uttrekkSkattemelding/skattepliktig/",
     "rawDataSourcePath": "dokumentForHendelse/",
     "dataStructureComponentRole": "ENTITY"
    },
    {"name": "folkeregisteridentifikator",
     "type": "xsd:string",
     #"rawDataSourcePath": "uttrekkSkattemelding/skattepliktig/",
     "rawDataSourcePath": "dokumentForHendelse/hendelse/egenskapshendelse/identifikasjonsnummer/",
     "dataStructureComponentRole": "ENTITY"
    },
    {"name": "hendelsestype",
     "type": "xsd:string",
     "rawDataSourcePath": "dokumentForHendelse/hendelse/",
     "dataStructureComponentRole": "ENTITY"
    },
    {"name": "ajourholdstidspunkt",
     "type": "xsd:dateTime",
     "rawDataSourcePath": "dokumentForHendelse/hendelse/",
     "dataStructureComponentRole": "TIME"
    }
]

# Peke på DEFAULT (eksisterende) eller DUMMY GSIM-objekt:
describedValueDomainId = "DescribedValueDomain_DUMMY"
#populationId = "Population_DUMMY"
populationId = "2aa9ab12-63ca-4458-aa00-95ea287bf2a5"
representertVariableId = "RepresentertVariable_DUMMY"
#unitTypeId = "UnitType_DUMMY"
unitTypeId = "51a8dcde-127d-49de-84a4-a0a9c34f666f"
universeId = "Universe_DUMMY"
variableId = "Variable_DUMMY"
#OHV: Laget en liste av alle identifikatornavn til bruk for å unngå å lage measures av identifikatorer
idNames = []
for dict in identifierComponents:
   idNames.append(dict['name'])   
# TODO: Hente begreps-url mv. fra Skatt XSD også (eksempel: https://data.skatteetaten.no/begrep/b57408db-d96a-11e6-8d9b-005056821322)?

# TODO: Se om vi kan finne en bedre løsning for lange filnavn (og "shortName" på IntanceVariable)

# TODO: Støtte for xsd:gYear (Skatt bruker dette bl.a. for "inntektsaar")?

# TODO: rename til "cleanXsdFile.py" og "Xsd2Gsim.py"
