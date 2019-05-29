#################################################################################################
# BnJ, 2019-05-23
# Dette er et Python-script som er benyttet til prototyping ifm. "metadatafangst" av Skatteetatens
# XSD (XML-schema).
#
# OBS!
# Dette Python-scriptet er ikke tenkt brukt til en produksjonsløsning, men er benyttet til
# kompetansebygging (praktisk erfaring) knyttet til kartlegging av i hvor stor grad det er mulig
# å automatisere metadata-fangsten i SSB, og hvilke GSIM-objekter som kan genereres (helt eller delvis).
#################################################################################################


########################################
# I Skatteetatens XML schema (xsd-filer med modeller) er det definert flere "enkle typer"
# som "kompliserer" utlesing og tranformasjon av XSD-elementene i forhold til GSIM-behovet i SSB.
# Gjør derfor bare en enkel mapping av disse, eksempelvis oversetter vi bare
# FREG-typene "Tekst" og "Navn" til "xsd:string".
# TODO: Dette må fikses i en produksjonsløsning!

import config


# TODO: <xsd:restriction base="xsd:gYear"/> !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


xsdElementTypesMappedToString = [
    "Tekst",
    "Identifikator",
    "Foedselsnummer",
    "Kommunenummer",
    "Navn",
    "Landkode"
    "LandkodeIsoAlfa3",
    "Husnummer",
    "Postnummer",
    "Husbokstav",
    "Organisasjonsnavn",
    "Organisasjonsnummer"
    ]

xsdElementTypesMappedToDate = [
    "Dato"
    ]

xsdElementTypesMappedToDateTime = [
    "DatoKlokkeslett"
    ]

xsdElementTypesMappedToTime = []

xsdElementTypesMappedToInteger = [
    "Aarstall"
    ]

xsdElementTypesMappedToLong = [
    "Antall",
    "BeloepSomHeltall",
    "Heltall",
]

xsdElementTypesMappedToDecimal = [
    "Desimaltall",
    "Prosent"
]

xsdElementTypesMappedToBool = [
    "Boolsk"
    ]

# Veldig enkel mapping ved at vi leser xsd-filen som en string og kjører "string.replace()"
# TODO: Rutinen bør kanskje erstattes av en mer avansert rutine som leser XSD som et objekt?
def cleanXsdFile():
    #with open('.//xsdFiles//PersondokumentMedHistorikk_v1BETA2.xsd', encoding='utf8') as f:
    with open(config.xsdSourcePath + config.xsdSourceFile , encoding='utf8') as f:
        #xsd_file = f.read().strip()
        xsdFile = f.read()
        f.close()

    # Fjerner targetNamespace osv.
    #longXsdNs = '<xsd:schema xmlns="folkeregisteret:tilgjengeliggjoering:person:v1" xmlns:xsd="http://www.w3.org/2001/XMLSchema" targetNamespace="folkeregisteret:tilgjengeliggjoering:person:v1" elementFormDefault="qualified" attributeFormDefault="unqualified">'
    #shortXsdNs = '<xsd:schema <xsd:schema xmlns="folkeregisteret:tilgjengeliggjoering:person:v1" xmlns:xsd="http://www.w3.org/2001/XMLSchema">'
    #xsdFile = xsdFile.replace(longXsdNs, shortXsdNs)

    for item in xsdElementTypesMappedToString:
        xsdFile = xsdFile.replace('type="'+item+'"', 'type="xsd:string"')

    for item in xsdElementTypesMappedToDate:
        xsdFile = xsdFile.replace('type="'+item+'"', 'type="xsd:date"')

    for item in xsdElementTypesMappedToDateTime:
        xsdFile = xsdFile.replace('type="'+item+'"', 'type="xsd:dateTime"')

    for item in xsdElementTypesMappedToTime:
        xsdFile = xsdFile.replace('type="'+item+'"', 'type="xsd:time"')

    for item in xsdElementTypesMappedToInteger:
        xsdFile = xsdFile.replace('type="'+item+'"', 'type="xsd:integer"')

    for item in xsdElementTypesMappedToLong:
        xsdFile = xsdFile.replace('type="'+item+'"', 'type="xsd:long"')

    for item in xsdElementTypesMappedToDecimal:
        xsdFile = xsdFile.replace('type="'+item+'"', 'type="xsd:decimal"')

    for item in xsdElementTypesMappedToBool:
        xsdFile = xsdFile.replace('type="'+item+'"', 'type="xsd:boolean"')

    #with open(".//xsdFiles//Del_1_PersondokumentMedHistorikk.xsd", "w", encoding='utf8') as f:
    with open(config.xsdSourcePath + config.xsdCleanedFile, "w", encoding='utf8') as f:
        f.write(xsdFile)
        f.close()


# "Main" ################################
cleanXsdFile()
print("ferdig")
