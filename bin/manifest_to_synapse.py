#!/usr/bin/env python

import sys
import os
import json
import logging

import requests
import pandas
import boto3
import synapseclient
import nda_aws_token_generator
import ndasynapse

pandas.options.display.max_rows = None
pandas.options.display.max_columns = None
pandas.options.display.max_colwidth = 1000

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

def main():

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--dry_run", action="store_true", default=False)
    parser.add_argument("--verbose", action="store_true", default=False)
    parser.add_argument("--storage_location_id", type=str)
    parser.add_argument("--bucket_name", type=str)
    parser.add_argument("--synapse_data_folder", type=str)
    parser.add_argument("manifest_file", type=str)

    args = parser.parse_args()

    syn = synapseclient.Synapse(skip_checks=True)
    syn.login(silent=True)

    metadata_manifest = pandas.read_csv(args.manifest_file)

    fh_list = ndasynapse.synapse.create_synapse_filehandles(syn=syn,
                                                            metadata_manifest=metadata_manifest,
                                                            bucket_name=args.bucket_name,
                                                            storage_location_id=args.storage_location_id,
                                                            verbose=args.verbose)
    fh_ids = map(lambda x: x.get('id', None), fh_list)

    synapse_manifest = metadata_manifest
    synapse_manifest['dataFileHandleId'] = fh_ids
    synapse_manifest['path'] = None

    fh_names = map(synapseclient.utils.guess_file_name,
                   metadata_manifest.data_file.tolist())

    synapse_manifest['name'] = fh_names
    synapse_manifest['parentId'] = args.synapse_data_folder

    if not args.dry_run:
        syn = synapseclient.login(silent=True)

        f_list = ndasynapse.synapse.store(syn=syn,
                                          synapse_manifest=synapse_manifest,
                                          filehandles=fh_list,
                                          dry_run=False)

        sys.stderr.write("%s\n" % (f_list, ))
    else:
        synapse_manifest.to_csv("/dev/stdout", index=False, encoding='utf-8')

if __name__ == "__main__":
    main()
