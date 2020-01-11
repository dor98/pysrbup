#!/usr/bin/env python3
import argparse
import csv
import os
import pickle
import shutil
import time
from concurrent import futures

import grpc

from pysrbup.backup_system_pb2 import (Block, DeleteBackupResponse,
                                       GetBackupResponse, GetBlocksResponse,
                                       GetMissingCodesResponse,
                                       ListBackupsResponse, PushBlocksResponse,
                                       Row, UpdateDictResponse,
                                       UploadBackupResponse)
from pysrbup.backup_system_pb2_grpc import add_BackupServicer_to_server


class BackupServicer():

    def __init__(self, backups_dir, dictionary_file):
        self.backups_dir = backups_dir
        self.meta_file = os.path.join(self.backups_dir, 'meta.csv')
        self.dictionary_file = dictionary_file
        with open(dictionary_file, 'rb') as f:
            self.dictionary = pickle.load(f)

    def UploadBackup(self, request, context):
        # pylint: disable=invalid-name,unused-argument
        curr_backup_dir = os.path.join(self.backups_dir, request.id)
        os.mkdir(curr_backup_dir)
        backup_file = os.path.join(curr_backup_dir, 'data.bin')
        with open(backup_file, 'wb') as f:
            f.write(request.data)
        with open(self.meta_file, 'a') as f:
            writer = csv.writer(f)
            writer.writerow([request.id, time.asctime(time.gmtime())])
        return UploadBackupResponse()

    def GetMissingCodes(self, request, context):
        # pylint: disable=invalid-name,unused-argument
        missing_codes = []
        for code in request.codes:
            if code not in self.dictionary:
                missing_codes.append(code)
            else:
                self.dictionary[code][1] += 1
        return GetMissingCodesResponse(codes=missing_codes)

    def PushBlocks(self, request, context):
        # pylint: disable=invalid-name,unused-argument
        for block in request.blocks:
            self.dictionary[block.code] = [block.data, 1]
        with open(self.dictionary_file, 'wb') as f:
            pickle.dump(self.dictionary, f)
        return PushBlocksResponse()

    def GetBackup(self, request, context):
        # pylint: disable=invalid-name,unused-argument
        if not request.id in os.listdir(self.backups_dir):
            return GetBackupResponse()
        file_to_restore = os.path.join(self.backups_dir, request.id, 'data.bin')
        with open(file_to_restore, 'rb') as f:
            data = f.read()
        return GetBackupResponse(data=data)

    # pylint: disable=invalid-name,unused-argument
    def GetBlocks(self, request, context):
        blocks = []
        for code in request.codes:
            block = Block(code=code, data=self.dictionary[code][0])
            blocks.append(block)
        return GetBlocksResponse(blocks=blocks)

    def DeleteBackup(self, request, context):
        # pylint: disable=invalid-name,unused-argument
        if request.id not in os.listdir(self.backups_dir):
            return GetBackupResponse()
        backup_dir_to_delete = os.path.join(self.backups_dir, request.id)
        backup_file = os.path.join(backup_dir_to_delete, 'data.bin')
        with open(backup_file, 'rb') as f:
            data = f.read()
        with open(self.meta_file, 'r') as infile:
            rows = []
            for row in csv.reader(infile):
                if row and row[0] != request.id:
                    rows.append(row)
        with open(self.meta_file, 'w') as outfile:
            writer = csv.writer(outfile)
            for row in rows:
                writer.writerow(row)
        shutil.rmtree(backup_dir_to_delete)
        return DeleteBackupResponse(data=data)

    def UpdateDict(self, request, context):
        # pylint: disable=invalid-name,unused-argument
        for code in request.codes:
            if self.dictionary[code][1] == 1:
                del self.dictionary[code]
            else:
                self.dictionary[code][1] -= 1
        with open(self.dictionary_file, 'wb') as d:
            pickle.dump(self.dictionary, d)
        return UpdateDictResponse()

    def ListBackups(self, request, context):
        # pylint: disable=invalid-name,unused-argument
        with open(self.meta_file, 'r') as mf:
            rows = []
            count = 0
            for row in csv.reader(mf):
                if row and count > 0:
                    rows.append(Row(col=row))
                count += 1
        print(rows)
        return ListBackupsResponse(rows=rows)


def create_args_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--server_address', default='localhost:50000')
    parser.add_argument('--num_threads', default=3)
    parser.add_argument('backups_dir')
    return parser


def create_dictionary(root_path):
    dictionary_file = os.path.join(root_path, 'dictionary')
    with open(dictionary_file, 'wb') as f:
        pickle.dump({}, f)
    return dictionary_file


def create_meta_file(root_path):
    meta_file = os.path.join(root_path, 'meta.csv')
    with open(meta_file, 'a') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'creation_time'])


def main():
    args = create_args_parser().parse_args()
    if 'dictionary' not in os.listdir(args.backups_dir):
        dictionary_file = create_dictionary(args.backups_dir)
    else:
        dictionary_file = os.path.join(args.backups_dir, 'dictionary')
    if 'meta.csv' not in os.listdir(args.backups_dir):
        create_meta_file(args.backups_dir)
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=args.num_threads))
    add_BackupServicer_to_server(
        BackupServicer(args.backups_dir, dictionary_file), server)
    server.add_insecure_port(args.server_address)
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    main()
