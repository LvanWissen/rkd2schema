"""
Built upon an adapted version of RDFAlchemy for Python (3.7). Install with:
```bash
pip install git+https://github.com/LvanWissen/RDFAlchemy.git
```
"""

import os
import json
import calendar
import urllib.parse
import uuid

import requests
from bs4 import BeautifulSoup

from rdflib import Dataset, Namespace, URIRef, Literal, BNode, OWL, RDFS, XSD, SKOS
from rdfalchemy import rdfSubject, rdfMultiple, rdfSingle

APIURL = "https://api.rkd.nl/api/record/portraits/"

nsPerson = Namespace("https://data.create.humanities.uva.nl/id/rkd/persons/")
nsThesaurus = Namespace(
    "https://data.create.humanities.uva.nl/id/rkd/thesaurus/")

schema = Namespace("http://schema.org/")
dc = Namespace("http://purl.org/dc/elements/1.1/")
sem = Namespace("http://semanticweb.cs.vu.nl/2009/11/sem/")
bio = Namespace("http://purl.org/vocab/bio/0.1/")
foaf = Namespace("http://xmlns.com/foaf/0.1/")
void = Namespace("http://rdfs.org/ns/void#")
nsIconClass = Namespace('http://iconclass.org/')

eventTranslationNL = {
    'Birth': 'Geboorte',
    'Baptism': 'Doop',
    'Death': 'Overlijden',
    'Burial': 'Begrafenis',
    'Marriage': 'Huwelijk'
}


class Entity(rdfSubject):
    rdf_type = URIRef('urn:entity')

    additionalType = rdfSingle(schema.additionalType)

    label = rdfMultiple(RDFS.label)
    name = rdfMultiple(schema.name)
    alternateName = rdfMultiple(schema.alternateName)
    description = rdfMultiple(schema.description)

    mainEntityOfPage = rdfSingle(schema.mainEntityOfPage)
    sameAs = rdfMultiple(OWL.sameAs)

    disambiguatingDescription = rdfMultiple(schema.disambiguatingDescription)

    keywords = rdfMultiple(schema.keywords)

    depiction = rdfSingle(foaf.depiction)
    subjectOf = rdfMultiple(schema.subjectOf)
    about = rdfMultiple(schema.about)
    url = rdfSingle(schema.url)

    inDataset = rdfSingle(void.inDataset)

    hasTimeStamp = rdfSingle(sem.hasTimeStamp)
    hasEarliestBeginTimeStamp = rdfSingle(sem.hasEarliestBeginTimeStamp)
    hasLatestEndTimeStamp = rdfSingle(sem.hasLatestEndTimeStamp)


class Role(Entity):
    rdf_type = schema.Role

    name = rdfSingle(schema.name)
    isPartOf = rdfSingle(schema.isPartOf)
    isRelatedTo = rdfSingle(schema.isRelatedTo)


class CreativeWork(Entity):
    rdf_type = schema.CreativeWork

    publication = rdfSingle(schema.publication)
    author = rdfMultiple(schema.author)

    text = rdfSingle(schema.text)

    mainEntity = rdfSingle(schema.mainEntity)

    isPartOf = rdfMultiple(schema.isPartOf)
    isRelatedTo = rdfMultiple(schema.isRelatedTo)


class VisualArtwork(CreativeWork):
    rdf_type = schema.VisualArtwork, schema.Product

    artist = rdfMultiple(schema.artist)

    dateCreated = rdfSingle(schema.dateCreated)
    dateModified = rdfSingle(schema.dateModified)

    temporal = rdfMultiple(schema.temporal)

    artworkSurface = rdfMultiple(schema.artworkSurface)
    artMedium = rdfMultiple(schema.artMedium)
    artform = rdfMultiple(schema.artform)

    width = rdfSingle(schema.width)
    height = rdfSingle(schema.height)
    depth = rdfSingle(schema.depth)
    image = rdfMultiple(schema.image)

    subject = rdfMultiple(dc.subject)


class QuantitativeValue(Entity):
    rdf_type = schema.QuantitativeValue

    unitCode = rdfSingle(schema.unitCode)
    value = rdfSingle(schema.value)


class PublicationEvent(Entity):
    rdf_type = schema.PublicationEvent

    startDate = rdfSingle(schema.startDate)
    hasEarliestBeginTimeStamp = rdfSingle(sem.hasEarliestBeginTimeStamp)
    hasLatestEndTimeStamp = rdfSingle(sem.hasLatestEndTimeStamp)

    location = rdfSingle(schema.location)

    publishedBy = rdfMultiple(schema.publishedBy)


class Place(Entity):
    rdf_type = schema.Place


class Person(Entity):
    rdf_type = schema.Person

    birthPlace = rdfSingle(schema.birthPlace)
    deathPlace = rdfSingle(schema.deathPlace)

    birthDate = rdfSingle(schema.birthDate)
    deathDate = rdfSingle(schema.deathDate)

    birth = rdfSingle(bio.birth)
    death = rdfSingle(bio.death)
    event = rdfMultiple(bio.event)

    spouse = rdfMultiple(schema.spouse)
    parent = rdfMultiple(schema.parent)
    children = rdfMultiple(schema.children)

    gender = rdfSingle(schema.gender)


class Event(Entity):
    rdf_type = sem.Event, bio.Event

    place = rdfSingle(bio.place)

    principal = rdfSingle(bio.principal)
    partner = rdfMultiple(bio.partner)


class Birth(Event):
    rdf_type = bio.Birth


class Baptism(Event):
    rdf_type = bio.Baptism


class Death(Event):
    rdf_type = bio.Death


class Burial(Event):
    rdf_type = bio.Burial


class Marriage(Event):
    rdf_type = bio.Marriage


class Concept(Entity):
    rdf_type = SKOS.Concept

    prefLabel = rdfMultiple(SKOS.prefLabel)
    note = rdfMultiple(SKOS.note)

    related = rdfMultiple(SKOS.related)
    broader = rdfMultiple(SKOS.broader)
    narrower = rdfMultiple(SKOS.narrower)


def unique(*args):

    identifier = "".join(str(i) for i in args)  # order matters

    unique_id = uuid.uuid5(uuid.NAMESPACE_X500, identifier)

    return BNode(unique_id)


def getEventLabel(event):

    if event.hasTimeStamp:
        year = str(event.hasTimeStamp)[:4]
    elif event.hasEarliestBeginTimeStamp and event.hasLatestEndTimeStamp:
        year = f"ca. {str(event.hasEarliestBeginTimeStamp)[:4]}-{str(event.hasLatestEndTimeStamp)[:4]}"
    elif event.hasEarliestBeginTimeStamp:
        year = f"ca. {str(event.hasEarliestBeginTimeStamp)[:4]}-?"
    elif event.hasLatestEndTimeStamp:
        year = f"ca. ?-{str(event.hasLatestEndTimeStamp)[:4]}"
    else:
        year = "?"

    eventClassName = event.__class__.__name__

    eventNameNL = eventTranslationNL[eventClassName]
    eventNameEN = eventClassName

    if event.principal:
        persons = [event.principal.name[0]]
    elif event.partner:
        persons = sorted(i.name[0] for i in event.partner)
    else:
        persons = []

    if persons:
        labelNL = Literal(f"{eventNameNL} van {' en '.join(persons)} ({year})",
                          lang='nl')
        labelEN = Literal(f"{eventNameEN} of {' and '.join(persons)} ({year})",
                          lang='en')
    else:
        labelNL = Literal(f"{eventNameNL} ({year})", lang='nl')
        labelEN = Literal(f"{eventNameEN} ({year})", lang='en')

    return [labelNL, labelEN]


def parseURL(url,
             params={'format': 'json'},
             thesaurusDict=dict(),
             imageCache=dict()):

    r = requests.get(url, params=params).json()

    if r['response']['numFound'] > 1:
        nTotal = r['response']['numFound']
        start = 0

        while start < nTotal:
            # First retrieve the identifier through a search (one at the time)
            print(f"Fetching {start+1}/{nTotal}")
            params = {'format': 'json', 'start': start}
            r = requests.get(url, params=params).json()
            doc = r['response']['docs'][0]

            # Then, retrieve the individual image
            # this gives other keys in the json...
            identifier = str(doc['priref'])

            doc = imageCache.get(identifier)

            if doc is None:
                r = requests.get(APIURL + identifier,
                                 params={
                                     'format': 'json'
                                 }).json()
                doc = r['response']['docs'][0]
                imageCache[identifier] = doc

            parseData(doc, thesaurusDict=thesaurusDict)
            start += 1

            # save every 1000 requests
            if start % 1000 == 0:
                with open('imagecache.json', 'w') as outfile:
                    json.dump(imageCache, outfile)

    else:
        doc = r['response']['docs'][0]

        identifier = str(doc['priref'])
        if identifier not in imageCache:
            imageCache[identifier] = doc

        parseData(doc, thesaurusDict=thesaurusDict)

    return thesaurusDict, imageCache


def parseData(d, thesaurusDict=dict()):

    identifier = d['priref']

    if d.get('picturae_images'):
        images = [
            f"https://images.rkd.nl/rkd/thumb/650x650/{img}.jpg"
            for img in d['picturae_images']
        ]
    elif d.get('afbeeldingsnummer_rkd_picturae_mapping'):
        images = [
            f"https://images.rkd.nl/rkd/thumb/650x650/{img}.jpg"
            for img in d['afbeeldingsnummer_rkd_picturae_mapping'].values()
        ]
    else:
        images = []

    # dateModified = Literal(d['modification'], datatype=XSD.datetime)
    names_nl = d['benaming_kunstwerk']
    names_en = [d['titel_engels']] if d['titel_engels'] else []
    alternateName = d['andere_benaming']

    disambiguatingDescription = d['opmerking_titel']
    description = d['opmerking_onderwerp']

    temporal = d['datumlabel']

    keywords = []
    keywordIdentifiers = [i for i in d['RKD_algemene_trefwoorden_linkref']]
    for k in keywordIdentifiers:
        concept, thesaurusDict = getThesaurus(k,
                                              thesaurusDict,
                                              returnType='uri')
        keywords.append(concept)

    attributedTo = [{
        'identifier': i['naam_linkref'],
        'name': i['naam_inverted']
    } for i in d['toeschrijving']
                    if i['status'] == 'huidig' and i.get('naam_linkref')]

    beginSearchDate = f"{d['zoekmarge_begindatum']}-01-01"
    endSearchDate = f"{d['zoekmarge_einddatum']}-12-31"

    publication = PublicationEvent(
        None,
        hasEarliestBeginTimeStamp=Literal(beginSearchDate, datatype=XSD.date),
        hasLatestEndTimeStamp=Literal(endSearchDate, datatype=XSD.date))

    artforms = []
    artformIdentifiers = d['objectcategorie_linkref']  # mapping AAT?
    for k in artformIdentifiers:
        concept, thesaurusDict = getThesaurus(k,
                                              thesaurusDict,
                                              returnType='uri')
        artforms.append(concept)

    artsurfaces = []
    artworkSurfaceIdentifiers = d['drager_lref']
    for k in artworkSurfaceIdentifiers:
        concept, thesaurusDict = getThesaurus(k,
                                              thesaurusDict,
                                              returnType='uri')
        artsurfaces.append(concept)

    materials = []
    materialIdentifiers = d['materiaal_lref']  # mapping AAT?
    for k in materialIdentifiers:
        concept, thesaurusDict = getThesaurus(k,
                                              thesaurusDict,
                                              returnType='uri')
        materials.append(concept)

    width = getQuantitativeValue(d['breedte'])

    height = getQuantitativeValue(d['hoogte'])

    depth = getQuantitativeValue(d['diepte'])

    externalURIs = []
    for u in d['urls']:
        if u.get('URL') and 'handle' in u['URL']:
            if ' ' in u['URL']:
                u['URL'] = u['URL'].split(' ')[0]
            externalURIs.append(URIRef(u['URL']))

    if d.get('iconclass_code'):
        iconclass_encoded = urllib.parse.quote(d['iconclass_code'][0])
        iconclass = nsIconClass.term(iconclass_encoded)
    else:
        iconclass = None

    related = []
    for r in d['onderdeel_van']:
        relIdentifier = str(r['object_onderdeel_van'][0]['priref'])
        related.append({
            'relatedTo':
            URIRef(f"https://rkd.nl/explore/images/{relIdentifier}"),
            'relation':
            r.get('onderdeel_van_verband')
        })

    for r in d['artistiek']:
        if r.get('artistiek_verband_koppeling'):
            relIdentifier = str(r['artistiek_verband_koppeling'][0]['priref'])
        else:
            relIdentifier = None

        related.append({
            'relatedTo':
            URIRef(f"https://rkd.nl/explore/images/{relIdentifier}")
            if relIdentifier else None,
            'relation':
            r.get('onderdeel_van_verband'),
            'description':
            ", ".join([
                i for i in [
                    r.get('beschrijving_verband'),
                    r.get('opmerking_artistiek_verband')
                ] if i
            ]),
            'relationThesaurus':
            r.get('artistiek_verband_linkref')
        })

    abouts = []
    for p in d['voorgestelde']:

        # Only take current attribution. Skip if field is absent
        if p.get('status_identificatie_portret') != "huidig":
            continue

        pURI = Person(nsPerson.term(str(p['persoonsnummer'])))

        marriages = []
        for m in p.get('huwelijk', []):
            marriages.append({
                'marriageDate':
                m.get('datum_huwelijk'),
                'marriagePartner':
                m.get('huwelijks_partner'),
                'marriagePartnerIdentifier':
                m.get('huwelijks_partner_nummer_lref'),
                'marriagePartnerNameWithIdentifier':
                m.get('naam_huw_partner_samenvoeging'),
                'marriagePlace':
                m.get('huwelijk_plaats'),
                'marriagePlaceIdentifier':
                m.get('huwelijk_plaats_lref')  # mapping TGN?
            })

        personData = {
            'identifier': p['persoonsnummer'],
            'name': p['naam_display'],
            'disambiguatingDescription': p.get('functie'),
            'gender': p.get('geslacht'),
            'birthPlace': p.get('geboorteplaats'),
            'birthPlaceIdentifier': p.get('geboorteplaats_lref'),
            'birthDateBegin': p.get('geboortedatum_begin'),
            'birthDateEnd': p.get('geboortedatum_eind'),
            'baptismDateBegin': p.get('doopdatum_begin'),
            'baptismDateEnd': p.get('doopdatum_eind'),
            'deathPlace': p.get('sterfplaats'),
            'deathPlaceIdentifier': p.get('sterfplaats_lref'),  # mapping TGN?
            'deathDateBegin': p.get('sterfdatum_begin'),
            'deathDateEnd': p.get('sterfdatum_eind'),
            'burialDate': p.get('begraafdatum'),
            'marriages': marriages
        }
        abouts.append(personData)

        parents = []

        # father
        if p.get('vader'):
            fatherData = p['vader'][0]
            fatherIdentifier = fatherData['vader']
            fatherName = fatherData['naam_vader_samenvoeging']
            father = Person(nsPerson.term(str(fatherIdentifier)),
                            name=[fatherName],
                            children=[pURI])
            parents.append(father)
        elif p.get('naam_vader'):
            father = Person(unique(p['persoonsnummer'], p['naam_vader']),
                            name=[p['naam_vader']],
                            children=[pURI])
            parents.append(father)

        # mother
        if p.get('moeder'):
            motherData = p['moeder'][0]
            motherIdentifier = motherData['moeder']
            motherName = motherData['naam_moeder_samenvoeging']
            mother = Person(nsPerson.term(str(motherIdentifier)),
                            name=[motherName],
                            children=[pURI])
            parents.append(mother)
        elif p.get('naam_moeder'):
            mother = Person(unique(p['persoonsnummer'], p['naam_moeder']),
                            name=[p['naam_moeder']],
                            children=[pURI])
            parents.append(mother)

        # children
        children = []
        if p.get('kinderen'):
            for k in p['kinderen']:
                childIdentifier = k['kind'][0]['persoonsnummer']
                childName = k['kind'][0]['naam_volledig']
                child = Person(nsPerson.term(str(childIdentifier)),
                               name=[childName],
                               parent=[pURI])
                children.append(child)

        pURI.parent = parents
        pURI.children = children

    depicted = []
    for p in abouts:
        depicted.append(getPerson(p))

    artists = []
    for a in attributedTo:

        artistURI = URIRef(f"https://data.rkd.nl/artists/{a['identifier']}")
        exploreArtistURI = URIRef(
            f"https://rkd.nl/explore/artists/{a['identifier']}")

        artist = Person(artistURI)
        artist.sameAs = [exploreArtistURI]
        artists.append(artist)

    visualArtwork = VisualArtwork(
        URIRef(f"https://rkd.nl/explore/images/{identifier}"),
        name=[Literal(name_nl, lang='nl') for name_nl in names_nl] +
        [Literal(name_en, lang='en') for name_en in names_en],
        alternateName=alternateName,
        disambiguatingDescription=disambiguatingDescription,
        description=description,
        about=depicted,
        keywords=keywords,
        artist=artists,
        artworkSurface=artsurfaces,
        artMedium=materials,
        artform=artforms,
        width=width,
        height=height,
        depth=depth,
        image=[URIRef(i) for i in images],
        # dateModified=dateModified,
        publication=publication,
        sameAs=externalURIs)

    if iconclass:
        visualArtwork.subject = [iconclass]

    relatedTos = []
    for r in related:
        if r['relatedTo']:
            otherWork = VisualArtwork(r['relatedTo'])
        else:
            otherWork = None

        if r.get('relationThesaurus'):
            relationThesaurus, thesaurusDict = getThesaurus(
                r['relationThesaurus'], thesaurusDict, returnType='uri')
        else:
            relationThesaurus = None

        if r.get('description'):
            description = [r['description']]
        else:
            description = []

        relatedTos.append(
            Role(None,
                 name=r['relation'],
                 additionalType=relationThesaurus,
                 description=description,
                 isRelatedTo=otherWork))
        # otherWork.isRelatedTo = [
        #     Role(None, name=r['relation'], isRelatedTo=visualArtwork)
        # ]

    visualArtwork.isRelatedTo = relatedTos


def parseDate(begin, end=None):

    if begin and len(begin) == 4:
        begin += "-01-01"
    elif begin and len(begin) == 7:
        begin += "-01"

    if end and len(end) == 4:
        end += "-12-31"
    elif end and len(end) == 7:
        # last of the month
        year, month = end.split('-')
        _, lastday = calendar.monthrange(int(year), int(month))
        end += f"-{lastday}"

    if begin and begin == end:
        timeStamp = Literal(begin, datatype=XSD.date)

        return timeStamp, timeStamp, timeStamp

    elif begin and end:
        timeStamp = None
        earliestBeginTimeStamp = Literal(begin, datatype=XSD.date)
        latestEndTimeStamp = Literal(end, datatype=XSD.date)

        return timeStamp, earliestBeginTimeStamp, latestEndTimeStamp

    elif begin:
        earliestBeginTimeStamp = Literal(begin, datatype=XSD.date)
        return None, earliestBeginTimeStamp, None

    else:
        return None, None, None


def getQuantitativeValue(value):

    if value and value != "?":

        value = value.replace(',',
                              '.').replace(' ', '').replace('c.', '').replace(
                                  'ca', '').replace('cm', '')

        try:
            value = float(value) / 100
            literal = Literal(value, datatype=XSD.decimal)

            label = [f"{value} meter"]

            qv = QuantitativeValue(None,
                                   unitCode='MTR',
                                   value=literal,
                                   label=label)

            return qv

        except ValueError:
            print("Incorrect measurement:", value)
            return None


def getPlace(identifier, label=[]):

    if identifier:
        return nsThesaurus.term(str(identifier))
    else:
        return None


def getThesaurus(identifier,
                 cachedict=dict(),
                 returnType='uri',
                 THESAURUSURL_NL='https://rkd.nl/nl/explore/thesaurus?term=',
                 THESAURUSURL_EN='https://rkd.nl/en/explore/thesaurus?term=',
                 recursionDepth=0,
                 maxRecursionDepth=2):

    identifier = str(identifier)
    uri = nsThesaurus.term(str(identifier))

    recursionDepth += 1
    if recursionDepth >= maxRecursionDepth:
        return uri, cachedict

    if cachedict.get(str(identifier)) is None:
        # get AAT and relations, use cachedict

        print("FETCHING", identifier)

        dataNL = parseThesaurusURL(identifier, THESAURUSURL_NL + identifier)
        dataEN = parseThesaurusURL(identifier, THESAURUSURL_EN + identifier)

        if dataNL or dataEN:

            data = {
                'identifier': identifier,
                'url': uri,
                'titleNL': dataNL['title'],
                'titleEN': dataEN['title'],
                'descriptionNL': dataNL['description'],
                'broader': dataNL['broader'],
                'narrower': dataNL['narrower'],
                'related': dataNL['related'],
                'targets': dataNL['targets'],
                'aat': dataNL['aat']
            }
        else:
            data = None

        if data:
            cachedict[identifier] = data
        else:
            return None, cachedict

    broaders = []
    for i in cachedict[identifier]['broader']:
        broader, cachedict = getThesaurus(i,
                                          cachedict,
                                          returnType=returnType,
                                          recursionDepth=recursionDepth)

        if broader:
            broaders.append(broader)

    narrowers = []
    for i in cachedict[identifier]['narrower']:
        narrower, cachedict = getThesaurus(i,
                                           cachedict,
                                           returnType=returnType,
                                           recursionDepth=recursionDepth)
        if narrower:
            narrowers.append(narrower)

    relateds = []
    for i in cachedict[identifier]['related']:
        related, cachedict = getThesaurus(i,
                                          cachedict,
                                          returnType=returnType,
                                          recursionDepth=recursionDepth)
        if related:
            relateds.append(related)

    # And the 'Used for' information stored in 'target'?

    if returnType == 'uri':
        return URIRef(cachedict[identifier]['url']), cachedict
    elif returnType == 'concept':

        concept = Concept(
            URIRef(cachedict[identifier]['url']),
            prefLabel=[
                Literal(cachedict[identifier]['titleNL'], lang='nl'),
                Literal(cachedict[identifier]['titleEN'], lang='en')
            ],
            note=[Literal(cachedict[identifier]['descriptionNL'], lang='nl')]
            if cachedict[identifier]['descriptionNL'] else [],
            related=relateds,
            broader=broaders,
            narrower=narrowers)

        if cachedict[identifier]['aat']:
            concept.sameAs = [URIRef(cachedict[identifier]['aat'])]

        return concept, cachedict
    else:
        return None, cachedict


def parseThesaurusURL(identifier, url):

    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')

    if 'Term not found' in soup.text:
        return None

    termElement = soup.find('div', class_='term')
    title = termElement.find('div', class_='title').text.strip()
    description = termElement.find('div', class_='description').text.strip()
    if 'No description available' in description or 'Geen beschrijving beschikbaar' in description:
        description = None

    broaders = []
    targets = []
    broaderElements = soup.findAll('div', class_='broader-terms')
    for broaderElement in broaderElements:
        if 'Broader term' in broaderElement.text or 'Ruimere term' in broaderElement.text:  # since class labels are screwed up
            broaderUrls = [
                e.attrs['href'] for e in broaderElement.findAll('a')
            ]
            broaders += [i.split('term=')[1] for i in broaderUrls]
        if 'Used for' in broaderElement.text or 'Gebruikt voor' in broaderElement.text:
            targetUrls = [e.attrs['href'] for e in broaderElement.findAll('a')]
            targets += [i.split('term=')[1] for i in targetUrls]

    narrowers = []
    relateds = []
    narrowElements = soup.findAll('div', class_='narrower-terms')
    for narrowElement in narrowElements:
        if 'Narrower term' in narrowElement.text or 'Nauwere term' in narrowElement.text:
            narrowerUrls = [
                e.attrs['href'] for e in narrowElement.findAll('a')
            ]
            narrowers += [i.split('term=')[1] for i in narrowerUrls]
        if 'Related term' in narrowElement.text or 'Verwante term' in narrowElement.text:  # since class labels are screwed up
            relatedUrls = [e.attrs['href'] for e in narrowElement.findAll('a')]
            relateds += [i.split('term=')[1] for i in relatedUrls]

    externalElement = soup.find('div', class_='external-list')
    if externalElement:
        externals = [e.attrs['href'] for e in externalElement.findAll('a')]

        aat = None
        for i in externals:
            if 'aat-ned' in i:
                identifier = i.replace('http://browser.aat-ned.nl/', '')
                aat = f"http://vocab.getty.edu/aat/{identifier.strip()}"
            else:
                aat = None
    else:
        aat = None

    return {
        'identifier': identifier,
        'url': url,
        'title': title,
        'description': description,
        'broader': broaders,
        'narrower': narrowers,
        'related': relateds,
        'targets': targets,
        'aat': aat
    }


def getPerson(p):

    person = Person(nsPerson.term(str(p['identifier'])),
                    name=[p['name']],
                    disambiguatingDescription=[
                        Literal(p['disambiguatingDescription'], lang='nl')
                    ] if p['disambiguatingDescription'] else [])

    if p['gender']:
        if p['gender'].lower() == 'm':
            person.gender = schema.Male
        elif p['gender'].lower() == 'f':
            person.gender = schema.Female

    events = []

    if p['birthPlace'] or p['birthDateBegin'] or p['birthDateEnd']:

        place = getPlace(p['birthPlaceIdentifier'], [p['birthPlace']])

        timeStamp, earliestBeginTimeStamp, latestEndTimeStamp = parseDate(
            p['birthDateBegin'], p['birthDateEnd'])

        birth = Birth(nsPerson.term(str(p['identifier'] + '#birth')),
                      principal=person,
                      place=place,
                      hasTimeStamp=timeStamp,
                      hasEarliestBeginTimeStamp=earliestBeginTimeStamp,
                      hasLatestEndTimeStamp=latestEndTimeStamp)

        person.birth = birth
        events.append(birth)

    if p['baptismDateBegin'] or p['baptismDateEnd']:

        timeStamp, earliestBeginTimeStamp, latestEndTimeStamp = parseDate(
            p['baptismDateBegin'], p['baptismDateEnd'])

        baptism = Baptism(nsPerson.term(str(p['identifier'] + '#baptism')),
                          principal=person,
                          hasTimeStamp=timeStamp,
                          hasEarliestBeginTimeStamp=earliestBeginTimeStamp,
                          hasLatestEndTimeStamp=latestEndTimeStamp)

        events.append(baptism)

    if p['deathPlace'] or p['deathDateBegin'] or p['deathDateEnd']:

        place = getPlace(p['deathPlaceIdentifier'], [p['deathPlace']])

        timeStamp, earliestBeginTimeStamp, latestEndTimeStamp = parseDate(
            p['deathDateBegin'], p.get('deathDateEnd'))

        death = Death(nsPerson.term(str(p['identifier'] + '#death')),
                      principal=person,
                      place=place,
                      hasTimeStamp=timeStamp,
                      hasEarliestBeginTimeStamp=earliestBeginTimeStamp,
                      hasLatestEndTimeStamp=latestEndTimeStamp)

        person.death = death
        events.append(death)

    if p['burialDate']:

        date = Literal(p['burialDate'], datatype=XSD.date)

        burial = Burial(nsPerson.term(str(p['identifier'] + '#burial')),
                        principal=person,
                        hasTimeStamp=date)

        events.append(burial)

    spouses = []
    for m in p['marriages']:
        if m.get('marriagePlace') or m.get('marriageDate') or m.get(
                'marriagePartner') or m.get('marriagePartnerIdentifier'):

            place = getPlace(m['marriagePlaceIdentifier'],
                             [m['marriagePlace']])

            if m['marriageDate']:
                date = Literal(m['marriageDate'], datatype=XSD.date)
            else:
                date = None

            if m['marriagePartnerIdentifier']:
                if m['marriagePartnerNameWithIdentifier']:
                    name = [m['marriagePartnerNameWithIdentifier']]
                else:
                    name = []
                partner = Person(nsPerson.term(
                    str(m['marriagePartnerIdentifier'])),
                                 name=name)
            elif m['marriagePartner']:
                partner = Person(unique(p['identifier'], m['marriagePartner']),
                                 name=[m['marriagePartner']])
            else:
                partner = None

            partners = [person]
            if partner:
                partners.append(partner)
                spouses.append(partner)
                partner.spouse = [person]

            marriage = Marriage(unique(
                set([p['identifier'], m['marriagePartner'], 'marriage'])),
                                place=place,
                                hasTimeStamp=date,
                                partner=partners)
            if partner:
                partner.event = [marriage]

            events.append(marriage)

    person.event = events
    person.spouse = spouses

    for e in events:
        e.label = getEventLabel(e)

    return person


def main(search=None, cache=None, identifiers=[]):

    ns = Namespace("https://data.create.humanities.uva.nl/id/rkd/")

    ds = Dataset()
    ds.bind('rdfs', RDFS)
    ds.bind('schema', schema)
    ds.bind('sem', sem)
    ds.bind('bio', bio)
    ds.bind('foaf', foaf)
    ds.bind('void', void)
    ds.bind('skos', SKOS)
    ds.bind('owl', OWL)
    ds.bind('dc', dc)

    ds.bind('rkdArtist', URIRef("https://data.rkd.nl/artists/"))
    ds.bind('rkdThes', nsThesaurus)
    ds.bind('rkdPerson', nsPerson)
    ds.bind('rkdImage', URIRef("https://rkd.nl/explore/images/"))
    ds.bind('rkdThumb', URIRef("https://images.rkd.nl/rkd/thumb/650x650/"))

    ds.bind('aat', URIRef("http://vocab.getty.edu/aat/"))

    ## First the images

    g = rdfSubject.db = ds.graph(identifier=ns)

    # Load cache thesaurus
    if os.path.isfile('rkdthesaurus.json'):
        with open('rkdthesaurus.json') as infile:
            thesaurusDict = json.load(infile)
    else:
        thesaurusDict = dict()

    # Load cache images
    if os.path.isfile('imagecache.json'):
        with open('imagecache.json') as infile:
            imageCache = json.load(infile)
    else:
        imageCache = dict()

    # to fetch all identifiers from the search
    if search:
        thesaurusDict, imageCache = parseURL(search,
                                             thesaurusDict=thesaurusDict,
                                             imageCache=imageCache)
    elif cache:
        # assume that everything in the thesaurus is also cached
        for doc in cache.values():
            parseData(doc, thesaurusDict=thesaurusDict)
    elif identifiers:
        for i in identifiers:
            thesaurusDict, imageCache = parseURL(APIURL + str(i),
                                                 thesaurusDict=thesaurusDict,
                                                 imageCache=imageCache)

    # Any images without labels?
    # These were not included in the search, but fetch them anyway.
    print("Finding referred images that were not included")
    q = """
    PREFIX schema: <http://schema.org/>
    SELECT ?uri WHERE {
        ?role a schema:Role ; schema:isRelatedTo ?uri .

        FILTER NOT EXISTS { ?uri schema:name ?name }
    }
    """
    images = g.query(q)
    print(f"Found {len(images)}!")
    for i in images:
        identifier = str(i['uri']).replace('https://rkd.nl/explore/images/',
                                           '')
        thesaurusDict, imageCache = parseURL(
            "https://api.rkd.nl/api/record/images/" + str(identifier),
            thesaurusDict=thesaurusDict,
            imageCache=imageCache)

    ## Then the thesaurus
    print("Converting the thesaurus")
    rdfSubject.db = ds.graph(identifier=ns.term('thesaurus/'))

    ids = list(thesaurusDict.keys())
    for i in ids:
        _, thesaurusDict = getThesaurus(i, thesaurusDict, 'concept')

    # Save updated cache
    with open('rkdthesaurus.json', 'w') as outfile:
        json.dump(thesaurusDict, outfile)

    with open('imagecache.json', 'w') as outfile:
        json.dump(imageCache, outfile)

    ## Serialize
    print("Serializing!")
    ds.serialize('rkdportraits14751825.trig', format='trig')


if __name__ == "__main__":
    # main(identifiers=[197253, 3063, 147735, 125660, 237150])

    # main(
    #     search=
    #     "https://api.rkd.nl/api/search/portraits?filters[periode]=1475||1825&format=json"
    # )

    with open('imagecache.json') as infile:
        imageCache = json.load(infile)

    main(cache=imageCache)
