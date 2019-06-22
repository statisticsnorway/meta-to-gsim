#################################################################################################
# OHV, 2019-06-19 Enkle fiks. Se OHV: kommentarer
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
import os
#OHV Lagt til
import copy

# TODO: import "cleanXsdFile.py" og kjør dette som første steg her !!!!

# Global variables:
gsimUnitDataSets = []
gsimInstanceVariables = []
numOfInstanceVariables = 0
sisteSkatteetatenHovedElement = ""
gruppePrefix = ""
sisteObject = ""

# Input metadata, dvs. leser XSD-filen fra Skatteetaten ("cleaned XSD file")
# tree = ET.parse('C://BNJ//prosjektutvikling//FREG//xsdFiles//Del_1_PersondokumentMedHistorikk.xsd')
tree = ET.parse(config.xsdSourcePath + config.xsdCleanedFile)
root = tree.getroot()


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
    printETree(xsdObject)
    elements = xsdObject.findall(".//"+getNs()+"element")
    #restrictions = xsdObject.findall(".//"+getNs()+"restriction")
    #print(elements)
    #if elements is not None:
    if  elements:
        return elements
    else:
        return None
    
#def findRestrictionsInObject(xsdObjectName):
#    xsdObject = root.find(".//*[@name='" + xsdObjectName + "']")
#    printETree(xsdObject)
#    #elements = xsdObject.findall(".//"+getNs()+"element")
#    restrictions = xsdObject.findall(".//"+getNs()+"restriction")
#    #print(elements)
#    #if elements is not None:
#    if  restrictions:
#        return restrictions
#    else:
#        return None    

def addGsimMeasureVariable(gsimInstanceVariable):
    global numOfInstanceVariables #OHV
    global gsimInstanceVariables
    #OHV Endret: copy.deepcopy lager nytt objekt. Gjør at vi ikke overskriver verdier når vi har variabler med samme name   
    instVar = copy.deepcopy(gsimInstanceVariable)

    instVar["id"] = str(uuid.uuid4())  # InstanceVariable.id
    instVar["dataStructureComponentType"] = "MEASURE"
    numOfInstanceVariables +=1
    #OHV flyttet telleren da det ble en for mye. Kan nok settes til bake nå
    #print(str(numOfInstanceVariables) + instVar["name"])
    gsimInstanceVariables.append(instVar)


def addGsimIdentifierVariables():
    global numOfInstanceVariables #OHV
    global gsimInstanceVariables
    for identifierVar in config.identifierComponents:
        instVar = {}
        instVar["id"] = str(uuid.uuid4())  # InstanceVariable.id
        instVar["dataStructureComponentType"] = "IDENTIFIER"
        instVar["name"] = identifierVar.get("name")
        instVar["type"] = identifierVar.get("type")
        instVar["dataStructureComponentRole"] = identifierVar.get("dataStructureComponentRole")
        instVar["rawDataSourcePath"] = identifierVar.get("rawDataSourcePath")
        #OHV flyttet telleren da det ble en for mye.Kan nok settes til bake nå
        numOfInstanceVariables +=1
        #print(str(numOfInstanceVariables) + instVar["name"])
        gsimInstanceVariables.append(instVar)

# TODO TODO TODO TODO:
#  Det må avklares hva som egentlig er en "primærnøkkel" (Identifiers) innenfor i XSD-ene til Skatteetaten, f.eks. i en FREG-meldingstype!
#  Skatteetaten eller S320 bør kunne svare på dette?
#  - foedselsEllerDNummer og ...
#  -  ajourholdstidspunkt som identifer (time)?
#  -  sekvensnummer og meldings-identifikator som measure?
#  se https://wiki.ssb.no/display/MAS2/Eks.+hendelse+FREG
# Må lage FREG identifer for hver hendelse hvis hver hendelse blir eget UnitDataSet i SSBs inndata.



def getGruppePrefix(instanceVariable):
    gr = instanceVariable.get("gruppePrefix")
    if gr is None or gr == "":
        return ""
    else:
        return gr.replace(".", "_")


# Leser igjennom hele XSD (rekursivt)
def iterateXsd(skatteetatenHovedElement):
    #OHV:global numOfInstanceVariables
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
            #OHV flyttet telleren da det ble en for mye.Kan nok settes til bake nå
            #numOfInstanceVariables +=1
              #OHV: Skal ikke lage instanseVariabel hvis name er benyttet som Identifikator. Finnes sikkert en bedre måte å løse dette på. 
              if not baseE.attrib.get("name") in config.idNames:
                #print("Base: "+ str(baseE.attrib.get("name")), end='')  
                addGsimMeasureVariable(baseE.attrib)
 
    elements_1 = findElementsInObject(skatteetatenHovedElement)
    #print("elements_1" +str(elements_1))
    #OHV: Ser ut som denne må endres
    #if elements_1 is None:
    if not elements_1:
      if   isCodeList(skatteetatenHovedElement):
          print("Codelist uten element: Kan ikke lage instanceVariabel")

      else:   
        print("ERROR - UKJENT TYPE: " + skatteetatenHovedElement)
    else:
        #print("Nådaaaa: ")
        for elem1 in elements_1:
          #print("Nå: ")   
        #print(config.identifierComponents[1].get("name"))
        #printDict(config.identifierComponents)
          #OHV: Skal ikke lage instanseVariabel hvis name er benyttet som Identifikator. Finnes sikkert en bedre måte å løse dette på.
          if not elem1.attrib.get("name") in config.idNames:
            
            if isSimpleElementType(elem1.attrib.get("type")):  
                    #print("Simple: "+ str(elem1.attrib.get("name")), end='')
                    #and elem1.attrib.get("name") not in identifierComponents.get("name"):
                    #print("  InstanceVariable: ", end='')
                    #OHV flyttet telleren da det ble en for mye.Kan nok settes til bake nå
                    #numOfInstanceVariables +=1
                    #if gruppePrefix != "":
                    #print(gruppePrefix, end='')
                    elem1.attrib["gruppePrefix"] = gruppePrefix
                    addGsimMeasureVariable(elem1.attrib)
                #print(str(elem1.attrib))
            elif isCodeList(elem1.attrib.get("type")):
                #print("Kode: "+ str(elem1.attrib.get("name")), end='')
                #OHV flyttet telleren da det ble en for mye.Kan nok settes til bake nå
                #numOfInstanceVariables +=1
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
                #print("Else: "+ str(elem1.attrib.get("name")), end='')
                if sisteObject != elem1.attrib.get("type"):  # "if" for å unngå evig løkke for noen "selv-refererende objekter" (griseøre), f.eks. "Folkeregisterpersonnavn.originaltNavn"
                    sisteObject = elem1.attrib.get("type")
                    gruppePrefix += elem1.attrib.get("name") + "."
                    iterateXsd(elem1.attrib.get("type"))  # Rekursivt kall fordi dette er en sub-type (ComplexType)
                    gruppePrefix = gruppePrefix.replace(elem1.attrib.get("name")+".", "")
                
                    

# Bygger opp json-struktur for GSIM UnitDataSet. Se eksempel: https://github.com/statisticsnorway/gsim-raml-schema/blob/master/examples/_main/UnitDataSet_Person_1.json
def gsimCreateUnitDataSet(gsimSource):
    global gsimUnitDataSets
    js = {}
    js["id"] = gsimSource.get("dataSetId")  # TODO: eventuelt om vi skal bytte til ULID (Universally Unique Lexicographically Sortable Identifier)
    js["name"] = [{"languageCode": "nb", "languageText": gsimSource.get("dataSetName")}]
    js["description"] = [{"languageCode": "nb", "languageText": config.dataResource + " datasett " + splitStringOnUpperCase(gsimSource.get("dataSetName"))}]
    js["administrativeStatus"] = "DRAFT"
    js["versionValidFrom"] = getZuluDateTime()
    js["validFrom"] = getZuluDateTime()
    js["createdDate"] = getZuluDateTime()
    js["createdBy"] = "BNJ"
    js["unitDataStructure"] = "/UnitDataStructure/" + gsimSource.get("unitDataStructureId")
    js["dataSetState"] = "INPUT_DATA"
    js["temporalityType"] = "EVENT"
    #printDict(ds)
    gsimUnitDataSets.append(js)
    writeJsonFile(js, gsimSource.get("dataSetName"), 'UnitDataSet_' + gsimSource.get("dataSetName"))


def gsimCreateUnitDataStructure(gsimSource):
    js = {}
    js["id"] = gsimSource.get("unitDataStructureId")  # TODO: eventuelt om vi skal bytte til ULID (Universally Unique Lexicographically Sortable Identifier)
    js["name"] = [{"languageCode": "nb", "languageText": gsimSource.get("unitDataStructureName")}]
    js["description"] = [{"languageCode": "nb", "languageText": config.dataResource + " datastruktur " + splitStringOnUpperCase(gsimSource.get("unitDataStructureName"))}]
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
    js["description"] = [{"languageCode": "nb", "languageText": config.dataResource + " record (LogicalRecord) " + splitStringOnUpperCase(gsimSource.get("logicalRecordName"))}]
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


def gsimCreateInstanceVariables(gsimSource):
    js = {}
    for instVar in gsimSource.get("instanceVariables"):
        js["id"] = instVar.get("id")  # TODO: eventuelt om vi skal bytte til ULID (Universally Unique Lexicographically Sortable Identifier)
        js["name"] = [{"languageCode": "nb", "languageText": gsimSource.get("logicalRecordName") + " " + getGruppePrefix(instVar).replace("_", " ") + instVar.get("name")}]
        js["description"] = [{"languageCode": "nb", "languageText": config.dataResource + " - " + splitStringOnUpperCase(gsimSource.get("logicalRecordName")) + ", " + getGruppePrefix(instVar).replace("_", " ") + splitStringOnUpperCase(instVar.get("name"))}]
        js["administrativeStatus"] = "DRAFT"
        js["versionValidFrom"] = getZuluDateTime()
        js["validFrom"] = getZuluDateTime()
        js["createdDate"] = getZuluDateTime()
        js["createdBy"] = "BNJ"
        js["representedVariable"] = "/RepresentedVariable/" + config.representertVariableId
        js["population"] = "/Population/" + gsimSource.get("populationId")
        if instVar.get("dataStructureComponentType") == "IDENTIFIER":
            js["dataStructureComponentType"] = instVar.get("dataStructureComponentType")
            js["dataStructureComponentRole"] = instVar.get("dataStructureComponentRole")
        elif instVar.get("dataStructureComponentType") == "MEASURE":
            js["dataStructureComponentType"] = instVar.get("dataStructureComponentType")
        elif instVar.get("dataStructureComponentType") == "ATTRIBUTE":
            js["dataStructureComponentType"] = instVar.get("dataStructureComponentType")
        js["shortName"] = gsimSource.get("logicalRecordName").upper() + "_" + getGruppePrefix(instVar).upper() + instVar.get("name").upper()
        writeJsonFile(js, gsimSource.get("dataSetName"), 'InstanceVariable_' + gsimSource.get("logicalRecordName") + "_" + getGruppePrefix(instVar) + instVar.get("name"))


def gsimCreateDataResource():
    global gsimUnitDataSets
    js = {}
    js["id"] = str(uuid.uuid4())
    js["name"] = [{"languageCode": "nb", "languageText": config.dataResource }]
    js["description"] = [{"languageCode": "nb", "languageText": config.dataResource + " - " + config.xsdStartingPointElement}]
    js["administrativeStatus"] = "DRAFT"
    js["versionValidFrom"] = getZuluDateTime()
    js["validFrom"] = getZuluDateTime()
    js["createdDate"] = getZuluDateTime()
    js["createdBy"] = "BNJ"
    dataSets = []
    for unitDataSet in gsimUnitDataSets:
        dataSets.append("/UnitDataSet/" + unitDataSet.get("id"))
    js["dataSets"] = dataSets
    writeJsonFile(js, "", 'DataResource_' + config.dataResource)


# TODO: Det er mangel på NameSpace i Xpath for mappingen som genereres her (bør trolig se slik ut? --> eksempel fra lagretHendelse: /feed/entry/content/ns2:lagretHendelse/ns2:hendelse)
def mappingRawDataToInputData(gsimSource):
    # Oppretter mapping-katalogen hvis denne ikke eksisterer fra før.
    xsdStartingPointPath = config.xsdStartingPointPath
    jsonMappingPath = Path(config.jsonMappingObjectFullPath)
    if not jsonMappingPath.exists():
        jsonMappingPath.mkdir()
    js = {}
    for instVar in gsimSource.get("instanceVariables"):
        js["id"] = str(uuid.uuid4())
        js["sourceName"] = instVar.get("name")
        if instVar.get("dataStructureComponentType") == "IDENTIFIER":
            js["sourcePath"] = "/" + instVar.get("rawDataSourcePath")
        else:
            if instVar.get("gruppePrefix") is None or instVar.get("gruppePrefix").strip() == "":
                #js["sourcePath"] = "/folkeregisterperson/" + gsimSource.get("dataSetName") + "/"
                js["sourcePath"] = "/" + xsdStartingPointPath + gsimSource.get("dataSetName") + "/"
            else:
                #js["sourcePath"] = "/folkeregisterperson/" + gsimSource.get("dataSetName") + "/" + instVar.get("gruppePrefix").replace(".", "/")
                js["sourcePath"] = "/" + xsdStartingPointPath + gsimSource.get("dataSetName") + "/" + instVar.get("gruppePrefix").replace(".", "/")
        js["targetInstanceVariable"] = "/InstanceVariable/" + instVar.get("id")
        #writeJsonFile(js, "_mapping//" + gsimSource.get("dataSetName"), 'MappingRawDataToInputData_' + instVar.get("name"))
        #OHV Endret: Lagt til id for å få unike mappingnavn da vi kan ha flere som heter det samme, eks.postnummer
        writeJsonFile(js, config.mappingObjectSubPath + gsimSource.get("dataSetName"), 'MappingRawDataToInputData_' + instVar.get("name") + instVar.get("id"))
        #writeJsonFile(js, config.mappingObjectSubPath + gsimSource.get("dataSetName"), 'MappingRawDataToInputData_' + instVar.get("name"))


# Skriver JSON-filer med GSIM-metadata
def writeJsonFile(gsimObject, jsonSubPath, fileName):
    #targetPath = './/gsim_json//'
    targetPath = config.jsonGsimTargetPath
    jsonPath = Path(targetPath + jsonSubPath)
    if not jsonPath.exists():
        jsonPath.mkdir()
    # Fikk problemer med relative path og lange filnavn hvis dette utgjør ca. 180 tegn eller mer.
    # Det samme skjer hvis lengden av absolute path blir mer enn 256 tegn.
    # Ser ut til at kombinasjonen av r'\\?\\' (raw string) og absolute path løser problemet.
    fullPath = r'\\?\\' + os.path.abspath(targetPath + jsonSubPath + '//' + fileName + '.json')
    with open(fullPath, 'w') as fp:
        json.dump(gsimObject, fp, indent=4)


# "skatteetatenHovedElement" er f.eks. "FREG bostedsAdresse" eller "UttrekkSkattemelding Konto"
def generateGsimJsonForSkatteetatenHovedElement(skatteetatenHovedElement):
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

    skatteetatenElement = findXsdObjectByName(skatteetatenHovedElement)
    print("\n#### DataSet/DataStructure: " + skatteetatenHovedElement, end='')
    iterateXsd(skatteetatenElement.attrib.get("type"))
    gsimSource = {}
    gsimSource["dataSetName"] = skatteetatenElement.attrib.get("name")
    gsimSource["dataSetId"] = str(uuid.uuid4())
    gsimSource["populationId"] = config.populationId
    gsimSource["unitTypeId"] = config.unitTypeId
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
    print("Antall InstanceVariables:", numOfInstanceVariables)




# TODO:
def generateGsimJsonForAllSkatteetatenHovedElementer():
    allSkatteetanenElements = findElementsInObject(config.xsdStartingPointElement)
    i = 0
    y = 0
    for elem in allSkatteetanenElements:
        if isSimpleElementType(elem.attrib.get("type")):
            # Dette er kun en enkel type, f.eks. "årstall", "personidentifikator" el.l. og kan ikke behandles som et DataSet/DataStructure/LogicalRecord
            print('\nOBS! XSD SimpleType element "' + elem.attrib.get("name") + " - " + elem.attrib.get("type") + '" ble oversett fordi det ikke kan behandles som et GSIM DataSet/DataStructure/LogicalRecord!\n' )
            y +=1
        else:
            generateGsimJsonForSkatteetatenHovedElement(elem.get("name"))
            i += 1
    gsimCreateDataResource()
    print("################ Oppsummering av genereringen #################")
    print("Antall UnitDataSet/DataStrucures generert totalt:", i)
    if y > 0:
        print("\nOBS! " + str(y) + " elementer kunne ikke behandles (se logg ovenfor)!\n")
    print("###############################################################")


# RUN SCRIPT (MAIN):
# Genererer GSIM-metadata (json-objekter) for alle meldingstyper/skatteobjer i Skatteetatens XSD
generateGsimJsonForAllSkatteetatenHovedElementer()


# Kan også kjøre ett og ett skatteobjekt.
# generateGsimJsonForSkatteetatenHovedElement("arbeidsoppholdUtenforHjemmet")
# generateGsimJsonForSkatteetatenHovedElement("arbeidsreise")
# generateGsimJsonForSkatteetatenHovedElement("barnSomGirRettTilForeldrefradrag")
# generateGsimJsonForSkatteetatenHovedElement("besoeksreiseTilHjemmet")
# generateGsimJsonForSkatteetatenHovedElement("eiendomSomUtleieobjekt")
# generateGsimJsonForSkatteetatenHovedElement("eiendom")
# generateGsimJsonForSkatteetatenHovedElement("fagforeningskontingent")
# generateGsimJsonForSkatteetatenHovedElement("fritidsbaatMedSalgsverdiOverSalgsverdigrense")
# generateGsimJsonForSkatteetatenHovedElement("gaveTilFrivilligOrganisasjon")
# generateGsimJsonForSkatteetatenHovedElement("individuellPensjonsordning")
# generateGsimJsonForSkatteetatenHovedElement("kjoeretoey")
# generateGsimJsonForSkatteetatenHovedElement("kollektivPensjonsordning")
# generateGsimJsonForSkatteetatenHovedElement("kontantbeloep")
# generateGsimJsonForSkatteetatenHovedElement("konto")
# generateGsimJsonForSkatteetatenHovedElement("livsforsikring")
# generateGsimJsonForSkatteetatenHovedElement("loennOgTilsvarendeYtelser")
# generateGsimJsonForSkatteetatenHovedElement("oppholdskostnaderVedPassOgStellAvBarn")
# generateGsimJsonForSkatteetatenHovedElement("pensjonspremierIArbeidsforhold")
# generateGsimJsonForSkatteetatenHovedElement("privatFordringUtenforVirksomhet")
# generateGsimJsonForSkatteetatenHovedElement("privatGjeldsforholdUtenforVirksomhet")
# generateGsimJsonForSkatteetatenHovedElement("skattefriArvGaveOgGevinst")
# generateGsimJsonForSkatteetatenHovedElement("skattefriStoenadTilBarnetilsyn")
# generateGsimJsonForSkatteetatenHovedElement("skattepliktigKundeutbytteUtenforVirksomhetPerUtbetaler")
# generateGsimJsonForSkatteetatenHovedElement("skyldigRestskatt")
# generateGsimJsonForSkatteetatenHovedElement("verdiForAnnetPrivatInnboOgLoesoere")
# generateGsimJsonForSkatteetatenHovedElement("oekonomiskeForholdKnyttetTilBoligsameieEllerBoligselskap")
# generateGsimJsonForSkatteetatenHovedElement("personidentifikator")
