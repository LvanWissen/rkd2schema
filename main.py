"""
Built upon an adapted version of RDFAlchemy for Python (3.7). Install with:
```bash
pip install git+https://github.com/LvanWissen/RDFAlchemy.git
```
"""

import os
import json
from rdflib.term import BNode

import requests
from bs4 import BeautifulSoup

from rdflib import Dataset, Namespace, URIRef, Literal, OWL, RDFS, XSD, SKOS
from rdfalchemy import rdfSubject, rdfMultiple, rdfSingle

nsPerson = Namespace(
    "https://data.create.humanities.uva.nl/id/rkdimages/person/")
nsThesaurus = Namespace(
    "https://data.create.humanities.uva.nl/id/rkdimages/thesaurus/")

schema = Namespace("http://schema.org/")
sem = Namespace("http://semanticweb.cs.vu.nl/2009/11/sem/")
bio = Namespace("http://purl.org/vocab/bio/0.1/")
foaf = Namespace("http://xmlns.com/foaf/0.1/")
void = Namespace("http://rdfs.org/ns/void#")


class Entity(rdfSubject):
    rdf_type = URIRef('urn:entity')

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


class CreativeWork(Entity):
    rdf_type = schema.CreativeWork

    publication = rdfSingle(schema.publication)
    author = rdfMultiple(schema.author)

    text = rdfSingle(schema.text)

    mainEntity = rdfSingle(schema.mainEntity)

    isPartOf = rdfMultiple(schema.isPartOf)


class VisualArtwork(CreativeWork):
    rdf_type = schema.VisualArtwork

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

    parent = rdfMultiple(schema.parent)
    children = rdfMultiple(schema.children)


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


def parseURL(url, params={'format': 'json'}, thesaurusDict=dict()):

    r = requests.get(url, params=params).json()['response']['docs'][0]

    parseData(r, thesaurusDict=thesaurusDict)

    return thesaurusDict


def parseData(d, thesaurusDict=dict()):

    identifier = d['priref']
    images = [
        f"https://images.rkd.nl/rkd/thumb/650x650/{img}.jpg"
        for img in d['picturae_images']
    ]
    dateModified = Literal(d['modification'], datatype=XSD.datetime)
    names_nl = d['benaming_kunstwerk']
    name_en = d['titel_engels']
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
    } for i in d['toeschrijving']]

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

    width = QuantitativeValue(
        None,
        unitCode='MTR',
        value=Literal(float(d['breedte']) /
                      100, datatype=XSD.float)) if d['breedte'] else None
    height = QuantitativeValue(
        None,
        unitCode='MTR',
        value=Literal(float(d['hoogte'].replace(',', '.')) / 100,
                      datatype=XSD.float)) if d['hoogte'] else None
    depth = QuantitativeValue(
        None,
        unitCode='MTR',
        value=Literal(float(d['diepte']) /
                      100, datatype=XSD.float)) if d['diepte'] else None

    externalURIs = []
    for u in d['urls']:
        externalURIs.append(URIRef(u['URL']))

    related = []
    for r in d['onderdeel_van']:
        related.append({
            'relatedTo':
            URIRef(
                f"https://rkd.nl/explore/images/{r['object_onderdeel_van'][0]['priref']}"
            ),
            'relation':
            r.get('onderdeel_van_verband')
        })

    abouts = []
    for p in d['voorgestelde']:

        pURI = Person(nsPerson.term(str(p['persoonsnummer'])))

        marriages = []
        for m in p.get('huwelijk', []):
            marriages.append({
                'marriageDate':
                m['datum_huwelijk'],
                'marriagePartner':
                m.get('huwelijks_partner'),
                'marriagePartnerIdentifier':
                m.get('huwelijks_partner_nummer_lref'),
                'marriagePlace':
                m.get('huwelijk_plaats'),
                'marriagePlaceIdentifier':
                m.get('huwelijk_plaats_lref')  # mapping TGN?
            })

        personData = {
            'identifier': p['persoonsnummer'],
            'name': p['naam_display'],
            'birthPlace': p.get('geboorteplaats'),
            'birthPlaceIdentifier': p.get('geboorteplaats_lref'),
            'birthDateBegin': p.get('geboortedatum_begin'),
            'birthDateEnd': p.get('geboortedatum_eind'),
            'baptismDateBegin': p.get('doopdatum_begin'),
            'baptismDateEnd': p.get('doopdatum_eind'),
            'deathPlace': p.get('sterfplaats'),
            'deathPlaceIdentifier': p.get('sterfplaats_lref'),  # mapping TGN?
            'deathDateBegin': p.get('sterfdatum_begin'),
            'deathDateBegin': p.get('sterfdatum_begin'),
            'burialDate': p.get('begraafdatum'),
            # 'parents': p['ouders'],
            # 'mother': p['naam_moeder'],
            # 'father': p['naam_vader'],
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
            father = Person(None, name=[p['naam_vader']], children=[pURI])
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
            mother = Person(None, name=[p['naam_moeder']], children=[pURI])
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

        # parents
        #???

        pURI.parent = parents
        pURI.children = children

    depicted = []
    for p in abouts:
        depicted.append(getPerson(p))

    artists = [
        Person(URIRef(f"https://data.rkd.nl/artists/{a['identifier']}"))
        for a in attributedTo
    ]

    visualArtwork = VisualArtwork(
        URIRef(f"https://rkd.nl/explore/images/{identifier}"),
        name=[Literal(name_nl, lang='nl')
              for name_nl in names_nl] + [Literal(name_en, lang='en')],
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
        dateModified=dateModified,
        publication=publication,
        sameAs=externalURIs)

    partOfs = []
    for r in related:
        c = CreativeWork()
        partOfs.append(Role(None, name=r['relation'], isPartOf=c))
        VisualArtwork(r['relatedTo']).isPartOf = [
            Role(None, name=r['relation'], isPartOf=c)
        ]

    visualArtwork.isPartOf = partOfs


def parseDate(begin, end=None):

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


def getPlace(identifier, label=[]):

    if identifier:
        return Place(
            URIRef(f"https://data.rkd.nl/thesaurus/place/{identifier}"),
            name=label)
    else:
        return None


def getThesaurus(identifier,
                 cachedict=dict(),
                 returnType='uri',
                 THESAURUSURL_NL='https://rkd.nl/nl/explore/thesaurus?term=',
                 THESAURUSURL_EN='https://rkd.nl/en/explore/thesaurus?term=',
                 recursionDepth=0,
                 maxRecursionDepth=3):

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

    person = Person(nsPerson.term(str(p['identifier'])), name=[p['name']])

    events = []

    if p['birthPlace'] or p['birthDateBegin'] or p['birthDateEnd']:

        place = getPlace(p['birthPlaceIdentifier'], [p['birthPlace']])

        timeStamp, earliestBeginTimeStamp, latestEndTimeStamp = parseDate(
            p['birthDateBegin'], p['birthDateEnd'])

        birth = Birth(None,
                      principal=person,
                      place=place,
                      hasTimeStamp=timeStamp,
                      hasEarliestBeginTimeStamp=earliestBeginTimeStamp,
                      hasLatestEndTimeStamp=latestEndTimeStamp)

        person.birth = birth

    if p['baptismDateBegin'] or p['baptismDateEnd']:

        timeStamp, earliestBeginTimeStamp, latestEndTimeStamp = parseDate(
            p['baptismDateBegin'], p['baptismDateEnd'])

        baptism = Baptism(None,
                          principal=person,
                          hasTimeStamp=timeStamp,
                          hasEarliestBeginTimeStamp=earliestBeginTimeStamp,
                          hasLatestEndTimeStamp=latestEndTimeStamp)

        events.append(baptism)

    if p['deathPlace'] or p['deathDateBegin'] or p['deathDateEnd']:

        place = getPlace(p['deathPlaceIdentifier'], [p['deathPlace']])

        timeStamp, earliestBeginTimeStamp, latestEndTimeStamp = parseDate(
            p['deathDateBegin'], p.get('deathDateEnd'))

        death = Death(None,
                      principal=person,
                      place=place,
                      hasTimeStamp=timeStamp,
                      hasEarliestBeginTimeStamp=earliestBeginTimeStamp,
                      hasLatestEndTimeStamp=latestEndTimeStamp)

        person.death = death

    if p['burialDate']:

        date = Literal(p['burialDate'], datatype=XSD.date)

        burial = Burial(None, principal=person, hasTimeStamp=date)

        events.append(burial)

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
                partner = Person(
                    URIRef(
                        f"https://data.rkd.nl/artists/{m['marriagePartnerIdentifier']}"
                    ))
            elif m['marriagePartner']:
                partner = Person(None, name=[m['marriagePartner']])
            else:
                partner = None

            marriage = Marriage(None,
                                place=place,
                                hasTimeStamp=date,
                                partner=[person, partner])

            events.append(marriage)

    person.event = events

    return person


def main(identifiers, URL="https://api.rkd.nl/api/record/portraits/"):

    ns = Namespace("https://data.create.humanities.uva.nl/id/rkdimages/")

    ds = Dataset()
    ds.bind('rdfs', RDFS)
    ds.bind('schema', schema)
    ds.bind('sem', sem)
    ds.bind('bio', bio)
    ds.bind('foaf', foaf)
    ds.bind('void', void)
    ds.bind('skos', SKOS)
    ds.bind('owl', OWL)

    ## First the images

    rdfSubject.db = ds.graph(identifier=ns)

    # Load cache
    if os.path.isfile('rkdthesaurus.json'):
        with open('rkdthesaurus.json') as infile:
            thesaurusDict = json.load(infile)
    else:
        thesaurusDict = dict()

    for i in identifiers:
        thesaurusDict = parseURL(URL + str(i), thesaurusDict=thesaurusDict)

    ## Then the thesaurus

    rdfSubject.db = ds.graph(identifier=ns.term('thesaurus/'))

    ids = list(thesaurusDict.keys())
    for i in ids:
        _, thesaurusDict = getThesaurus(i, thesaurusDict, 'concept')

    # Save updated cache
    with open('rkdthesaurus.json', 'w') as outfile:
        json.dump(thesaurusDict, outfile)

    ## Serialize
    print("Serializing!")
    ds.serialize('rkdimages.trig', format='trig')


if __name__ == "__main__":
    main([3063, 147735, 125660])
