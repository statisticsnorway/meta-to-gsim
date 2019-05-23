##################################################################################
### config-fil for transformasjon fra Skatteetatens XSD til SSBs GSIM-objekter ###
##################################################################################

# "Key-word" for data/metadata-området som XSD-en fra Skatteetaten dekker, f.eks. "FREG", "Folkeregisteret", "Skattemelding", osv.
dataCoverage = "Skattemelding"

# Sti og navn til XSD-filen fra Skatteetaten:
xsdSourcePath = '..//..//..//skattemelding//source_metadata//'
xsdSourceFile = 'UttrekkSkattemelding_v0.12_574259384.xsd'
# .. og navn på ryddet/forenklet XSD-fil (output fra scriptet "cleanXsdFile.py")
xsdCleanedFile = 'CLEANED_' + xsdSourceFile


# .. "innslagspunktet" i XSD (ønsket "start-punkt-element" i XSD hvor det skal leses rekursivt fra)
xsdStartingPointElement = "SkattemeldingUtflatet"


# Sti til katalogen de genererte JSON-filer med GSIM-struktur skal lagres (output fra scriptet "Xsd2Gsim.py")
jsonGsimTargetPath = '..//..//..//skattemelding//gsim_objects//'


# Sti til katalogen mapping-json-objektene fra rådata til inndata skal lagres (output fra scriptet "Xsd2Gsim.py")
mappingObjectSubPath = '_mapping//'
jsonMappingObjectFullPath = jsonGsimTargetPath + mappingObjectSubPath


# TODO: legge inn identifier-variabler som en template her????
