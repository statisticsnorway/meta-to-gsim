##################################################################################
### config-fil for transformasjon fra Skatteetatens XSD til SSBs GSIM-objekter ###
##################################################################################

# "Key-word" for data/metadata-området som XSD-en fra Skatteetaten dekker, f.eks. "FREG", "Folkeregisteret", "Skattemelding", osv.
# Brukes bl.a. til "tagging" og i description-felter i GSIM-objektene, men har ingen praktisk betydning utover dette.
dataCoverage = "Skattemelding"

# Sti og navn til XSD-filen fra Skatteetaten:
xsdSourcePath = '..//..//..//skattemelding//source_metadata//'
xsdSourceFile = 'UttrekkSkattemelding_v0.12_574259384.xsd'
# .. og navn på ryddet/forenklet XSD-fil (output fra scriptet "cleanXsdFile.py")
xsdCleanedFile = 'CLEANED_' + xsdSourceFile


# .. "innslagspunktet" i XSD (ønsket "start-punkt-element" i XSD hvor det skal leses rekursivt fra), eksempel "SkattemeldingUtflatet" og "folkeregisterperson"
xsdStartingPointElement = "SkattemeldingUtflatet"


# Sti til katalogen de genererte JSON-filene med GSIM-struktur skal lagres i (output fra scriptet "Xsd2Gsim.py")
jsonGsimTargetPath = '..//..//..//skattemelding//gsim_objects//'


# Sti til katalogen mapping-json-objektene fra rådata til inndata skal lagres (output fra scriptet "Xsd2Gsim.py")
mappingObjectSubPath = '_mapping//'
jsonMappingObjectFullPath = jsonGsimTargetPath + mappingObjectSubPath


# TODO:
#    gsimSource["populationId"] = "2aa9ab12-63ca-4458-aa00-95ea287bf2a5" # "Hardkoding" av "FREG Population" som er opprettet manuelt!
#    gsimSource["unitTypeId"] = "51a8dcde-127d-49de-84a4-a0a9c34f666f" # "Hardkoding" av "FREG UnitType" som er opprettet manuelt!

# TODO: legge inn identifier-variabler som en template her????

# TODO: rename til "cleanXsdFile.py" og "Xsd2Gsim.py"

# TODO:
#  men jeg har en fake Dataressource fil i felles, på Dummy-branchen. Denne bør med i genereringen.
# Samtidig så føler jer at den egentlig bør være noe mer spesifikt enn eks.  Dataressurs_Freg, den bør jo skille
# mellom de ulike dokumentene(person og hendelse, og hva med versjoneringen=
