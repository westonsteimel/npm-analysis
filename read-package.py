#!/usr/bin/env python

import sys
import os
import gzip
import json
from esbulkstream import Documents
from pathlib import Path

file_dir = sys.argv[1]

es = Documents('npm-packages', mapping='')
es_one = Documents('npm-one-package', mapping='')

path = Path(file_dir)

for filename in path.rglob('*'):

    if os.path.isdir(filename):
        continue

    one_id = str(filename).split('/', 1)[1]
    one_data = { "name": one_id }

    with gzip.GzipFile(filename, mode="r") as fh:
        data = json.loads(fh.read())

        if "description" in data and data["description"] == "security holding package":
            one_data["security_holding"] = True

        if "name" not in data:
            print("No name %s" % filename)
            one_data["withdrawn"] = True
            es_one.add(one_data, one_id)
            continue
        if "time" not in data:
            print("No time %s" % filename)
            one_data["no_time"] = True
            es_one.add(one_data, one_id)
            continue
        package_name = data["name"]

        if "versions" in data:
            one_data["versions"] = len(data["versions"])
        elif "unpublished" in data["time"]:
            one_data["unpublished"] = True
            one_data["versions"] = len(data["time"]["unpublished"]["versions"])
        else:
            one_data["versions"] = len(data["time"])
            # The created and modified fields should always exist, but this
            # data gets pretty weird
            if one_data["versions"] > 2:
                one_data["versions"] = one_data["versions"] - 2

        es_one.add(one_data, one_id)

        for ver in data["time"].keys():

            # XXX Do something with these later
            #if ver == "created":
            #    continue
            #elif ver == "modified":
            #    continue
            if ver == "unpublished":
                continue

            package_version = ver
            package_time = data["time"][ver]

            doc_id = "%s-%s" % (package_name, package_version)

            doc = {
                "name": package_name,
                "version": package_version,
                "date": package_time
            }

            es.add(doc, doc_id)

es.done()
es_one.done()
