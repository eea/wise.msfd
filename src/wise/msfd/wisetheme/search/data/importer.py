#!/usr/bin/env python3
# pylint: skip-file
from __future__ import absolute_import
from __future__ import print_function
import csv
import json
import os
from collections import defaultdict

import tqdm
from elasticsearch import Elasticsearch
from elasticsearch.helpers import streaming_bulk
from six.moves import range
from six.moves import zip

OM = 'Origin of the measure'


def read_details_csv_files(location):
    data = defaultdict(list)

    fnames = [f for f in os.listdir(location)
              if f.endswith('csv') and f != 'master.csv']
    for name in fnames:
        with open(os.path.join(location, name)) as f:
            reader = iter(csv.reader(f))

            headers = None
            for line in reader:
                headers = line
                break

            index = headers.index('Origin of the measure')

            for line in reader:
                items = list(zip([h.strip() for h in headers], line))
                item = dict(items)
                item['_id'] = get_id(item)
                data[line[index]].append(item)
                fix_misspellings(item)

    res = {}
    for index, items in data.items():
        res[index] = dict(zip([i['_id'] for i in items], items))

    return res


def read_master_csv_files(location):
    data = []
    with open(os.path.join(location, 'master.csv')) as f:
        reader = iter(csv.reader(f))

        headers = None
        for line in reader:
            headers = line
            break

        for line in reader:
            items = list(zip([h.strip() for h in headers], line))
            item = dict(items)
            item['_id'] = get_id(item)
            data.append(item)
            fix_misspellings(item)

    return data


def fix_descriptor(rec):
    descriptors = ['D{}'.format(n) for n in range(1, 12)]
    s = []
    for d in descriptors:
        if rec[d] == '1':
            s.append(d)
        del rec[d]
    rec['Descriptors'] = s


def fix_impacts(rec):
    s = []
    fields = [
        'IMPACTS Waste management', 'IMPACTS Air pollution',
        'IMPACTS Marine litter', 'IMPACTS NIS', 'IMPACTS Noise',
        'IMPACTS Pollution', 'IMPACTS Water pollution', 'IMPACTS Other'
    ]
    for f in fields:
        if f in rec:
            if rec[f] == '1':
                s.append(f.replace('IMPACTS ', ''))
            del rec[f]
    rec['Impacts'] = s


def fix_region(rec):
    regions = {
        "MATL": "Marine Atlantic Region",
        "MBAL": "Marine Baltic Region",
        "MBLS": "Marine Region Black Sea",
        "MMAC": "Marine Macaronesian Region",
        "MMED": "Marine Mediterranean Region	"
    }
    if 'Region' in rec and rec['Region']:
        rec['Region'] = regions[rec['Region']]


def fix_keywords(rec):
    s = []

    if 'Keywords' in rec:
        rec['Keywords'] = list(
            [_f for _f in [k.strip() for k in rec['Keywords'].split(',')] if _f])
        return

    fields = [
        'accident management', 'administrative', 'air pollution',
        'anchoring/mooring', 'awareness raising', 'ballast waters',
        'construction', 'dredging', 'EU policies', 'hull fouling',
        'international agreements', 'legislation/regulation', 'maintenence',
        'marine litter', 'navigation', 'NIS', 'noise', 'pollution',
        'regional sea convention', 'PSSA/ZMES', 'technical measures',
        'waste management', 'water pollution'
    ]
    for f in fields:
        if f in rec:
            if rec[f] == '1':
                s.append(f)
            del rec[f]
    rec['Keywords'] = s


def get_id(rec):
    if rec.get('MeasureCode'):
        return rec['MeasureCode']
    if rec.get('CodeCatalogue'):
        return rec['CodeCatalogue']


def remap(k):
    if k == 'Feature Name':
        k = 'Feature name'

    return k


def fix_misspellings(rec):
    for k, v in rec.items():
        if v == 'Nos specified':
            rec[k] = 'Not specified'
        rec[k] = rec[k].strip()
        # if rec[k].endswith('\n'):


def make_mappings(data):
    blacklist = ['_id', "_index"]
    fields = set()
    for line in data:
        for k in line.keys():
            fields.add(k)

    mapping = {}
    for f in fields:
        if f not in blacklist:
            mapping[f] = {"type": "keyword",
                          "copy_to": ['all_fields_for_freetext']}

    mapping['all_fields_for_freetext'] = {
        "type": "text", "analyzer": "standard"      # analyzer:freetext
    }
    return mapping

    # {
    # "Sector": {"type": "keyword"},
    # "did_you_mean": {"type": "text", "analyzer": "didYouMean"},
    # "autocomplete": {"type": "text", "analyzer": "autocomplete"},
    # "CodeCatalogue": {"type": "text", "analyzer": "none"},
    # "Use_or_activity": {"type": "text", "analyzer": "none",
    # "fielddata": True},
    # }


# def fix_fieldnames(rec):
    # for k, v in rec.items():
    #     k = k.replace(' ', '_').replace('(', '').replace(')')


def main():
    host = 'localhost'
    # host = '10.50.4.114'
    # host = '10.50.4.82'
    index = 'wise_catalogue_measures'

    # with open('./analyzers.json') as f:
    #     analyzers = json.loads(f.read())

    conn = Elasticsearch([host])
    master_data = read_master_csv_files('./csv')

    data = read_details_csv_files('./csv')

    for (i, main) in enumerate(master_data):
        measure_name = main[OM]
        rec = data[measure_name][main['_id']]

        keys = list(main.keys())
        for k, v in rec.items():
            # uses the key from master record
            for mk in keys:
                if k.lower().strip() == mk.lower().strip():
                    k = mk
            k = remap(k)
            if k in main \
                    and main[k] \
                    and main[k].lower() != v.lower():
                print("Data conflict at position: : {} ({})".format(
                    i, main['_id']))
                print("Key: {}. Conflicting sheet: {}.".format(k, measure_name))
                print("Master value: <{}>. Sheet value: <{}>".format(
                    main[k], v))
                print("")
            else:
                main[k] = v

        fix_descriptor(main)
        fix_impacts(main)
        fix_keywords(main)
        fix_region(main)
        # fix_fieldnames(main)

        _id = get_id(main)
        main['_id'] = _id
        main['_index'] = index

    ids = set([r['_id'] for r in master_data])
    print("Unique records: {}".format(len(ids)))

    resp = conn.indices.create(
        index,
        body={
            "mappings": {
                "properties": make_mappings(master_data)
            }

        })
    assert resp.get('acknowledged') is True

    body = []
    for doc in master_data:
        body.append(json.dumps({"create": doc}))

    print("Indexing {} documents".format(len(master_data)))
    num_docs = len(master_data)
    progress = tqdm.tqdm(unit="docs", total=num_docs)

    successes = 0

    for ok, action in streaming_bulk(
        client=conn, index=index, actions=iter(master_data),
    ):
        progress.update(1)
        successes += ok

    print(("Indexed %d/%d documents" % (successes, num_docs)))


if __name__ == "__main__":
    main()
