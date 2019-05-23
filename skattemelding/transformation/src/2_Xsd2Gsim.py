#################################################################################################
# BnJ, 2019-05-01
# Dette er et Python-script som er benyttet til prototyping ifm. "metadatafangst" av Skatteetatens
# XSD (XML-schema).
#
# OBS!
# Dette Python-scriptet er ikke tenkt brukt til en produksjonsløsning, men er benyttet til
# kompetansebygging (praktisk erfaring) knyttet til kartlegging av i hvor stor grad det er mulig
# å automatisere metadata-fangsten i SSB, og hvilke GSIM-objekter som kan genereres (helt eller delvis).
#################################################################################################

# Følgende må tilpasses hver XSD fra Skatt før dette scriptet kjøres:
# 1: Sett riktig konfigurering (stier, filnavn, osv.) i scriptet "./config.py"
# 2: Sjekk at alle hardkodede transformasjoner og forenklinger er satt riktig i scriptet "cleanXsdFile.py"
# (3: Eventuelle endringer/tilpassninger av dette scriptet)
# (4: Kjør dette scritpet)

import config

import xml.etree.ElementTree as ET
import pprint
import json
import uuid
import datetime
from pathlib import Path
import re

# TODO: import "cleanXsdFile.py" og kjør dette som første steg her !!!!

# Global variables:
gsimInstanceVariables = []
numOfInstanceVariables = 0
sisteSkatteetatenHovedElement = ""
gruppePrefix = ""
sisteObject = ""

# "Hjelpe-metode" som kun brukes til manuell debugging!
#  Skriver ut hele/deler av ElementTree som xml (tekst).
def printETree(eTree):
    #print(ET.tostring(eTree, encoding='utf8', method='xml'))
    print(ET.tostring(eTree, encoding='unicode', method='xml'))

# "Hjelpe-metode" som kun brukes til manuell debugging!
def printList(list):
    for elem in list:
        print(str(elem.attrib))

# "Hjelpe-metode" som kun brukes til manuell debugging!
def printDict(dict):
    pp = pprint.PrettyPrinter(indent=4, compact=False)
    pp.pprint(dict)


# Konverterer "camelCase" til space-separert string.
#def splitStringOnUpperCase(str):
#    return re.sub(r'([a-z])([A-Z])', r'\1 \2', str).lower()
def splitStringOnUpperCase(str):
    result = ""
    for c in str:
        if c.isupper():
            result += " " + c.lower()
        else:
            result += c
    return result

# Henter dato i Zulu-time format
def getZuluDateTime():
    d = datetime.datetime.now()
    return d.strftime('%Y-%m-%dT%H:%M:%S.000Z')

### OBS! Har tatt noen snarveier for å slippe unna NameSpace-biten. Dette MÅ bli bedre i en produksjonsversjon!
# Fjerner ns (xsd namespace) fra elementet.
# Eksempelvis henter vi "complexType" fra resultatet i xquery: {http://www.w3.org/2001/XMLSchema}complexType
def nsStrip(item):
    return str(item).split("}")[1][0:]

# Henter xsd ns (namespace)
def getNs():
    return '{http://www.w3.org/2001/XMLSchema}'


# Input metadata, dvs. leser XSD-filen fra Skatteetaten ("cleaned XSD file")
# tree = ET.parse('C://BNJ//prosjektutvikling//FREG//xsdFiles//Del_1_PersondokumentMedHistorikk.xsd')
tree = ET.parse(config.xsdSourcePath + config.xsdCleanedFile)
root = tree.getroot()


# Sjekker om dette objektet er definert som en kodeliste i xsd-filen.
# Hvis xsd-objektet inneholder både elementet "restriction" og "enumeration"
# så er det nesten(?) 100% sikkert at dette er en kodeliste fra Skatteetaten.
def isCodeList(typeName):
    containsXsdRestriction = False
    containsXsdEnumeration = False
    xsdObject = root.find(".//*[@name='" + typeName + "']")
    if xsdObject is None:
        return False
    for item in xsdObject:
        if nsStrip(item.tag) == "restriction":
            containsXsdRestriction = True
        elif nsStrip(item.tag) == "enumeration":
            containsXsdEnumeration = True
        for subItem in item:
            if nsStrip(subItem.tag) == "restriction":
                containsXsdRestriction = True
            elif nsStrip(subItem.tag) == "enumeration":
                containsXsdEnumeration = True
    if containsXsdRestriction and containsXsdEnumeration:
        return True
    else:
        return False

# Henter alle elementer i kodelisten
def findCodelistElements(xsdObjectName):
    xsdObject = root.find(".//*[@name='" + xsdObjectName + "']")
    #printETree(xsdObject)
    elements = xsdObject.findall(".//"+getNs()+"enumeration")
    if elements is not None:
        return elements
    else:
        return None


# Sjekker om dette er en enkel "xsd basis-datatype" som string, date, integer, osv.
def isSimpleElementType(typeName):
    xsdBaseTypes = ["xsd:string", "xsd:date", "xsd:dateTime", "xsd:time", "xsd:integer", "xsd:long", "xsd:decimal", "xsd:boolean"]
    if typeName is None or typeName.strip() == "":
        return False
    if typeName in xsdBaseTypes:
        return True
    else:
        return False


# Arver dette xsd-objektet fra en xsd-extension type (abstrakt "base type")?
# Eksempelvis arv fra de abstrakte Skatteetaten FREG-typene "Registermetadata" og "RegistermetadataMedGyldighet"
def getBaseExtensionName(typeName):
    # Finner først xsd-objektet med "name=..."
    xsdObject = root.find(".//*[@name='" + typeName + "']")
    if xsdObject is None or typeName.strip() == "":
        return None  # Dette objektet har ikke en base-extension
    #printETree(xsdObject)
    # Sjekker så om dette xsd-objektet inneholder xsd-extension-elementer
    extensionInObject = xsdObject.find(".//"+getNs()+"extension")
    #printETree(extensionInObject)
    if extensionInObject is None or typeName.strip() == "":
        return None
    else:
        return extensionInObject.attrib.get("base")  # the "name"

# Henter elementer i fra xsd-entension type (abstrakt "base type")
# eksempelvis arv fra de abstrakte Skatteetaten FREG-typene "Registermetadata" og "RegistermetadataMedGyldighet"
def getBaseExtensionElements(extensionName):
    baseExtensionElements = findElementsInObject(extensionName)
    # TODO: Denne rutinen bør trolig gjøres rekursiv i og med at en base-type
    #       også kan være et hierariki av "base-extension arv".
    #       Nå støttes kun arv fra ett nivå, f.eks. mellom "Registermetadata" og "RegistermetadataMedGyldighet"
    subBaseExtensionName = getBaseExtensionName(extensionName)
    if subBaseExtensionName is not None:
        subBaseExtensionElements = findElementsInObject(subBaseExtensionName)
        baseExtensionElements = baseExtensionElements + subBaseExtensionElements
    return baseExtensionElements


# Henter ut et "sub-object" av XSD (simpleType eller complexType)
def findXsdObjectByName(xsdObjectName):
    dataTypeObject = root.find(".//*[@name='" + xsdObjectName + "']")
    return dataTypeObject


def findElementsInObject(xsdObjectName):
    xsdObject = root.find(".//*[@name='" + xsdObjectName + "']")
    #printETree(xsdObject)
    elements = xsdObject.findall(".//"+getNs()+"element")
    if elements is not None:
        return elements
    else:
        return None

def addGsimMeasureVariable(gsimInstanceVariable):
    global gsimInstanceVariables
    instVar = gsimInstanceVariable
    instVar["id"] = str(uuid.uuid4())  # InstanceVariable.id
    instVar["dataStructureComponentType"] = "MEASURE"
    gsimInstanceVariables.append(instVar)


# TODO TODO TODO TODO:
#  Det må avklares hva som egentlig er en "primærnøkkel" (Identifiers) innenfor i XSD-ene til Skatteetaten, f.eks. i en FREG-meldingstype!
#  Skatteetaten eller S320 bør kunne svare på dette?
#  - foedselsEllerDNummer og ...
#  -  ajourholdstidspunkt som identifer (time)?
#  -  sekvensnummer og meldings-identifikator som measure?
#  se https://wiki.ssb.no/display/MAS2/Eks.+hendelse+FREG
# Må lage FREG identifer for hver hendelse hvis hver hendelse blir eget UnitDataSet i SSBs inndata.
def addGsimIdentifierVariables():
    global gsimInstanceVariables
    instVar = {}
    instVar["id"] = str(uuid.uuid4())  # InstanceVariable.id
    instVar["dataStructureComponentType"] = "IDENTIFIER"
    instVar["name"] = "foedselsEllerDNummer"
    instVar["type"] = "xsd:string"
    instVar["identifierComponentRole"] = "ENTITY"
    gsimInstanceVariables.append(instVar)


def getGruppePrefix(instanceVariable):
    gr = instanceVariable.get("gruppePrefix")
    if gr is None or gr == "":
        return ""
    else:
        return gr.replace(".", "_")


# Leser igjennom hele XSD (rekursivt)
def iterateXsd(skatteetatenHovedElement):
    global numOfInstanceVariables
    global sisteSkatteetatenHovedElement
    global gruppePrefix
    global sisteObject
    if gruppePrefix == "":
        #print("#### LogicalRecord: " + skatteetatenHovedElement + " ####")
        print(" (Type: " + skatteetatenHovedElement + ") ####")
    baseExtensionName = getBaseExtensionName(skatteetatenHovedElement)
    if baseExtensionName is not None:
        if skatteetatenHovedElement != sisteSkatteetatenHovedElement: # "if" for å unngå evig løkke for noen "selv-refererende objekter", f.eks. "Folkeregisterpersonnavn.originaltNavn"
            sisteSkatteetatenHovedElement = skatteetatenHovedElement
            baseExtensionElements = getBaseExtensionElements(baseExtensionName)
            for baseE in baseExtensionElements:
                #print("  InstanceVariable: " + str(baseE.attrib))
                numOfInstanceVariables +=1
                addGsimMeasureVariable(baseE.attrib)
    elements_1 = findElementsInObject(skatteetatenHovedElement)
    if elements_1 is None:
        print("ERROR - UKJENT TYPE: " + skatteetatenHovedElement)
    else:
        for elem1 in elements_1:
            if isSimpleElementType(elem1.attrib.get("type")):
                #print("  InstanceVariable: ", end='')
                numOfInstanceVariables +=1
                #if gruppePrefix != "":
                    #print(gruppePrefix, end='')
                elem1.attrib["gruppePrefix"] = gruppePrefix
                addGsimMeasureVariable(elem1.attrib)
                #print(str(elem1.attrib))
            elif isCodeList(elem1.attrib.get("type")):
                #print("  InstanceVariable: ", end='')
                numOfInstanceVariables +=1
                #if gruppePrefix != "":
                    #print(gruppePrefix, end='')
                elem1.attrib["gruppePrefix"] = gruppePrefix
                codeList = findCodelistElements(elem1.attrib.get("type"))
                #print(str(elem1.attrib)+"\n   --> CODES: ", end='')
                codes = []
                for code in codeList:
                    #print(code.attrib.get("value"), end=',')
                    codes.append(code.attrib.get("value"))
                    elem1.attrib["codes"] = codes
                addGsimMeasureVariable(elem1.attrib)
                #print("")
            else:
                if sisteObject != elem1.attrib.get("type"):  # "if" for å unngå evig løkke for noen "selv-refererende objekter" (griseøre), f.eks. "Folkeregisterpersonnavn.originaltNavn"
                    sisteObject = elem1.attrib.get("type")
                    gruppePrefix += elem1.attrib.get("name") + "."
                    iterateXsd(elem1.attrib.get("type"))  # Rekursivt kall fordi dette er en sub-type (ComplexType)
                    gruppePrefix = gruppePrefix.replace(elem1.attrib.get("name")+".", "")


# Bygger opp json-struktur for GSIM UnitDataSet. Se eksempel: https://github.com/statisticsnorway/gsim-raml-schema/blob/master/examples/_main/UnitDataSet_Person_1.json
def gsimCreateUnitDataSet(gsimSource):
    js = {}
    js["id"] = gsimSource.get("dataSetId")  # TODO: eventuelt om vi skal bytte til ULID (Universally Unique Lexicographically Sortable Identifier)
    js["name"] = [{"languageCode": "nb", "languageText": gsimSource.get("dataSetName")}]
    js["description"] = [{"languageCode": "nb", "languageText": config.dataCoverage + " datasett " + splitStringOnUpperCase(gsimSource.get("dataSetName"))}]
    js["administrativeStatus"] = "DRAFT"
    js["versionValidFrom"] = getZuluDateTime()
    js["validFrom"] = getZuluDateTime()
    js["createdDate"] = getZuluDateTime()
    js["createdBy"] = "BNJ"
    js["unitDataStructure"] = "/UnitDataStructure/" + gsimSource.get("unitDataStructureId")
    js["dataSetState"] = "INPUT_DATA"
    js["temporalityType"] = "EVENT"
    #printDict(ds)
    writeJsonFile(js, gsimSource.get("dataSetName"), 'UnitDataSet_' + gsimSource.get("dataSetName"))


def gsimCreateUnitDataStructure(gsimSource):
    js = {}
    js["id"] = gsimSource.get("unitDataStructureId")  # TODO: eventuelt om vi skal bytte til ULID (Universally Unique Lexicographically Sortable Identifier)
    js["name"] = [{"languageCode": "nb", "languageText": gsimSource.get("unitDataStructureName")}]
    js["description"] = [{"languageCode": "nb", "languageText": config.dataCoverage + " datastruktur " + splitStringOnUpperCase(gsimSource.get("unitDataStructureName"))}]
    js["administrativeStatus"] = "DRAFT"
    js["versionValidFrom"] = getZuluDateTime()
    js["validFrom"] = getZuluDateTime()
    js["createdDate"] = getZuluDateTime()
    js["createdBy"] = "BNJ"
    js["logicalRecords"] = ["/LogicalRecord/" + gsimSource.get("logicalRecordId")]
    #printDict(ds)
    writeJsonFile(js, gsimSource.get("dataSetName"), 'UnitDataStructure_' + gsimSource.get("unitDataStructureName"))


def gsimCreateLogicalRecord(gsimSource):
    js = {}
    js["id"] = gsimSource.get("logicalRecordId")  # TODO: eventuelt om vi skal bytte til ULID (Universally Unique Lexicographically Sortable Identifier)
    js["name"] = [{"languageCode": "nb", "languageText": gsimSource.get("logicalRecordName")}]
    js["description"] = [{"languageCode": "nb", "languageText": config.dataCoverage + " record (LogicalRecord) " + splitStringOnUpperCase(gsimSource.get("logicalRecordName"))}]
    js["administrativeStatus"] = "DRAFT"
    js["versionValidFrom"] = getZuluDateTime()
    js["validFrom"] = getZuluDateTime()
    js["createdDate"] = getZuluDateTime()
    js["createdBy"] = "BNJ"
    arrInstVar = []
    for instVar in gsimSource.get("instanceVariables"):
        arrInstVar.append("/InstanceVariable/" + instVar.get("id"))
    js["instanceVariables"] = arrInstVar
    js["unitType"] = "/UnitType/" + gsimSource.get("unitTypeId")
    js["shortName"] = gsimSource.get("logicalRecordName").upper()
    #printDict(lr)
    writeJsonFile(js, gsimSource.get("dataSetName"), 'LogicalRecord_' + gsimSource.get("logicalRecordName"))


# TODO:
#  - ajourholdstidspunkt som identifer (time)?
#  - sekvensnummer og meldings-identifikator som measure?
#  se https://wiki.ssb.no/display/MAS2/Eks.+hendelse+FREG

def gsimCreateInstanceVariables(gsimSource):
    js = {}
    for instVar in gsimSource.get("instanceVariables"):
        js["id"] = instVar.get("id")  # TODO: eventuelt om vi skal bytte til ULID (Universally Unique Lexicographically Sortable Identifier)
        js["name"] = [{"languageCode": "nb", "languageText": gsimSource.get("logicalRecordName") + " " + getGruppePrefix(instVar).replace("_", " ") + instVar.get("name")}]
        js["description"] = [{"languageCode": "nb", "languageText": config.dataCoverage + " - " + splitStringOnUpperCase(gsimSource.get("logicalRecordName")) + ", " + getGruppePrefix(instVar).replace("_", " ") + splitStringOnUpperCase(instVar.get("name"))}]
        js["administrativeStatus"] = "DRAFT"
        js["versionValidFrom"] = getZuluDateTime()
        js["validFrom"] = getZuluDateTime()
        js["createdDate"] = getZuluDateTime()
        js["createdBy"] = "BNJ"
        js["representedVariable"] = "/RepresentedVariable/DRAFT"
        js["population"] = "/Population/" + gsimSource.get("populationId")
        if instVar.get("dataStructureComponentType") == "IDENTIFIER":
            js["dataStructureComponentType"] = instVar.get("dataStructureComponentType")
            js["dataStructureComponentRole"] = instVar.get("identifierComponentRole")
        elif instVar.get("dataStructureComponentType") == "MEASURE":
            js["dataStructureComponentType"] = instVar.get("dataStructureComponentType")
        elif instVar.get("dataStructureComponentType") == "ATTRIBUTE":
            js["dataStructureComponentType"] = instVar.get("dataStructureComponentType")
        js["shortName"] = gsimSource.get("logicalRecordName").upper() + "_" + getGruppePrefix(instVar).upper() + instVar.get("name").upper()
        writeJsonFile(js, gsimSource.get("dataSetName"), 'InstanceVariable_' + gsimSource.get("logicalRecordName") + "_" + getGruppePrefix(instVar) + instVar.get("name"))


# TODO: Det er mangel på NameSpace i Xpath for mappingen som genereres her (bør trolig se slik ut? --> eksempel fra lagretHendelse: /feed/entry/content/ns2:lagretHendelse/ns2:hendelse)
def mappingRawDataToInputData(gsimSource):
    # Oppretter mapping-katalogen hvis denne ikke eksisterer fra før.
    xsdStartingPoint = config.xsdStartingPointElement
    jsonMappingPath = Path(config.jsonMappingObjectFullPath)
    if not jsonMappingPath.exists():
        jsonMappingPath.mkdir()
    js = {}
    for instVar in gsimSource.get("instanceVariables"):
        js["id"] = str(uuid.uuid4())
        js["sourceName"] = instVar.get("name")
        if instVar.get("gruppePrefix") is None or instVar.get("gruppePrefix").strip() == "":
            #js["sourcePath"] = "/folkeregisterperson/" + gsimSource.get("dataSetName") + "/"
            js["sourcePath"] = "/" + xsdStartingPoint + "/" + gsimSource.get("dataSetName") + "/"
        else:
            #js["sourcePath"] = "/folkeregisterperson/" + gsimSource.get("dataSetName") + "/" + instVar.get("gruppePrefix").replace(".", "/")
            js["sourcePath"] = "/" + xsdStartingPoint + "/" + gsimSource.get("dataSetName") + "/" + instVar.get("gruppePrefix").replace(".", "/")
        js["targetInstanceVariable"] = "/InstanceVariable/" + instVar.get("id")
        #writeJsonFile(js, "_mapping//" + gsimSource.get("dataSetName"), 'MappingRawDataToInputData_' + instVar.get("name"))
        writeJsonFile(js, config.mappingObjectSubPath + gsimSource.get("dataSetName"), 'MappingRawDataToInputData_' + instVar.get("name"))


# Skriver JSON-filer med GSIM-metadata
def writeJsonFile(gsimObject, jsonSubPath, fileName):
    #targetPath = './/gsim_json//'
    targetPath = config.jsonGsimTargetPath
    jsonPath = Path(targetPath + jsonSubPath)
    if not jsonPath.exists():
        jsonPath.mkdir()
    with open(targetPath + jsonSubPath + '//' + fileName + '.json', 'w') as fp:
        json.dump(gsimObject, fp, indent=4)


def generateGsimJsonForSkatteetatenHovedElement(skatteetatenHovedElement=None):
    global gsimInstanceVariables
    global numOfInstanceVariables
    global sisteSkatteetatenHovedElement
    global gruppePrefix
    global sisteObject
    # Reset global variables
    gsimInstanceVariables = []
    numOfInstanceVariables = 0
    sisteSkatteetatenHovedElement = ""
    gruppePrefix = ""
    sisteObject = ""

    # printList(findElementsInObject("Folkeregisterperson"))
    i = 0
    skatteetatenElement = findXsdObjectByName(skatteetatenHovedElement)
    i += 1
    print("\n#### LogicalRecord: " + skatteetatenHovedElement, end='')
    iterateXsd(skatteetatenElement.attrib.get("type"))
    gsimSource = {}
    gsimSource["dataSetName"] = skatteetatenElement.attrib.get("name")
    gsimSource["dataSetId"] = str(uuid.uuid4())
    gsimSource["populationId"] = "2aa9ab12-63ca-4458-aa00-95ea287bf2a5" # "Hardkoding" av "FREG Population" som er opprettet manuelt!
    gsimSource["unitTypeId"] = "51a8dcde-127d-49de-84a4-a0a9c34f666f" # "Hardkoding" av "FREG UnitType" som er opprettet manuelt!
    gsimSource["unitDataStructureName"] = skatteetatenElement.attrib.get("name")
    gsimSource["unitDataStructureId"] = str(uuid.uuid4())
    gsimSource["logicalRecordName"] = skatteetatenElement.attrib.get("name")
    gsimSource["logicalRecordId"] = str(uuid.uuid4())
    gsimSource["instanceVariables"] = gsimInstanceVariables
    addGsimIdentifierVariables()
    #printDict(gsimSource)
    gsimCreateUnitDataSet(gsimSource)
    gsimCreateUnitDataStructure(gsimSource)
    gsimCreateLogicalRecord(gsimSource)
    gsimCreateInstanceVariables(gsimSource)
    mappingRawDataToInputData(gsimSource)
    print("\nAntall UnitDataSet/LogicalRecords:", i)
    print("Antall InstanceVariables:", numOfInstanceVariables)



# RUN SCRIPT (MAIN):
# Genererer GSIM-metadata (json-objekter) for alle meldingstyper i FREG XSD
# TODO:
#   Det må avklares om SSB skal lage inndata av alle de 30+ FREG-meldingstypene?
#   Trolig har ikke SSB tilgang til å lese alle meldingstypene, men dette må avklares med Skatteetaten og S320?
#
#   Her forutsetter vi også at det genereres ett GSIM UnitDataSet/LogicalRecord per FREG meldingstype i inndata-tilstand,
#   men vi må vurdere om dette er fornuftig i en produksjonsløsning?
generateGsimJsonForSkatteetatenHovedElement("arbeidsoppholdUtenforHjemmet")
