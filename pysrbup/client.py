import argparse
import hashlib
import os
import pickle
import queue
import threading
import uuid

import grpc
from cryptography.fernet import Fernet

from pysrbup.backup_system_pb2 import (Block, DeleteBackupRequest,
                                       GetBackupRequest, GetBlocksRequest,
                                       GetMissingCodesRequest,
                                       ListBackupsRequest, PushBlocksRequest,
                                       UpdateDictRequest, UploadBackupRequest)
from pysrbup.backup_system_pb2_grpc import BackupStub

BLOCK_SIZE = 1000


class BackupNode:

    def __init__(self, filetype, name, children=None, codes=None):
        if children is None:
            children = []
        if codes is None:
            codes = []
        self.filetype = filetype
        self.name = name
        self.children = children
        self.codes = codes


class BackupClient:

    def __init__(self, stub):
        self.stub = stub
        self.more_work = False

    def upload_backup(self, path, key, num_of_threads):
        backup_id = str(uuid.uuid4())
        codes_dict = dict()
        work_queue = queue.Queue()
        fernet_obj = Fernet(key)
        self.more_work = True
        threads = []
        for _ in range(num_of_threads):
            thread = threading.Thread(target=self.update_missing_blocks,
                                      args=(codes_dict, work_queue, fernet_obj))
            thread.start()
            threads.append(thread)
        backup_node = self.build_structure(path, codes_dict, work_queue)
        self.more_work = False
        backup_node = fernet_obj.encrypt(pickle.dumps(backup_node))
        upload_backup_request = UploadBackupRequest(id=backup_id,
                                                    data=backup_node)
        self.stub.UploadBackup(upload_backup_request)
        for thread in threads:
            thread.join()
        print('Completed backup id: {}'.format(backup_id))
        return backup_id

    def update_missing_blocks(self, codes_dict, work_queue, fernet_object):
        codes = list()
        while self.more_work or not work_queue.empty():
            try:
                codes.append(work_queue.get())
            except queue.Empty:
                continue
            if codes and work_queue.empty():
                missing_codes = self.stub.GetMissingCodes(
                    GetMissingCodesRequest(codes=codes)).codes
                self.push_blocks(missing_codes, codes_dict, fernet_object)
                codes = list()

    def push_blocks(self, missing_codes, codes_dict, fernet_object):
        blocks = []
        for code in missing_codes:
            block_data = fernet_object.encrypt(codes_dict[code])
            blocks.append(Block(code=code, data=block_data))
        self.stub.PushBlocks(PushBlocksRequest(blocks=blocks))

    def build_structure(self, root_path, codes_dict, work_queue):
        root_name = os.path.basename(os.path.realpath(root_path))
        root_node = BackupNode('folder', root_name)
        for child in os.listdir(root_path):
            child_path = os.path.join(root_path, child)
            if os.path.isdir(child_path):
                root_node.children.append(
                    self.build_structure(child_path, codes_dict, work_queue))
            else:
                child_node = BackupNode('file', child)
                root_node.children.append(child_node)
                with open(child_path, 'rb') as f:
                    while True:
                        block = f.read(BLOCK_SIZE)
                        if not block:
                            break
                        hash_function = hashlib.sha256()
                        hash_function.update(block)
                        code = hash_function.hexdigest()
                        codes_dict[code] = block
                        child_node.codes.append(code)
                        work_queue.put(code)
        return root_node

    def restore_backup(self, backup_id, restore_to_path, key):
        fernet_obj = Fernet(key)
        get_backup_request = GetBackupRequest(id=backup_id)
        data = pickle.loads(
            fernet_obj.decrypt(self.stub.GetBackup(get_backup_request).data))
        self.restore(data, restore_to_path, fernet_obj)
        print('Backup {} has been restored to {}'.format(
            backup_id, restore_to_path))

    def restore(self, root_dir, restore_to_path, fernet_obj):
        dir_path = os.path.join(restore_to_path, root_dir.name)
        os.mkdir(dir_path)
        for child in root_dir.children:
            if child.filetype == 'folder':
                self.restore(child, dir_path, fernet_obj)
            else:
                file_path = os.path.join(dir_path, child.name)
                codes = []
                for code in child.codes:
                    codes.append(code)
                get_blocks_response = self.stub.GetBlocks(
                    GetBlocksRequest(codes=codes))
                with open(file_path, 'wb') as f:
                    for block in get_blocks_response.blocks:
                        f.write(fernet_obj.decrypt(block.data))

    def delete_backup(self, backup_id, key):
        delete_backup_request = DeleteBackupRequest(id=backup_id)
        backup_obj = self.stub.DeleteBackup(delete_backup_request).data
        if not backup_obj:
            print('You have no backup with the given id.')
            return
        fernet_obj = Fernet(key)
        backup_obj = pickle.loads(fernet_obj.decrypt(backup_obj))
        self.update_dict(backup_obj)
        print('Backup has been deleted')

    def update_dict(self, backup_obj):
        for child in backup_obj.children:
            if child.filetype == 'folder':
                self.update_dict(child)
            else:
                codes = []
                for code in child.codes:
                    codes.append(code)
                update_dict_request = UpdateDictRequest(codes=codes)
                self.stub.UpdateDict(update_dict_request)

    def list_backups(self):
        list_backups_response = self.stub.ListBackups(ListBackupsRequest())
        for row in list_backups_response.rows:
            print('Backup ID: {}, Creation Time: {}'.format(
                row.col[0], row.col[1]))

    @staticmethod
    def generate_key():
        key = Fernet.generate_key()
        print('Your key: {}'.format(key))
        return key


def create_args_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--server_address', default='localhost:50000')
    parser.add_argument('--num_of_threads', default=2)
    subparsers = parser.add_subparsers(dest='command')
    subparsers.required = True
    backup_parser = subparsers.add_parser('backup')
    backup_parser.add_argument('path')
    backup_parser.add_argument('key')
    restore_parser = subparsers.add_parser('restore')
    restore_parser.add_argument('id')
    restore_parser.add_argument('restore_to')
    restore_parser.add_argument('key')
    delete_backup_parser = subparsers.add_parser('delete')
    delete_backup_parser.add_argument('id')
    delete_backup_parser.add_argument('key')
    subparsers.add_parser('list')
    subparsers.add_parser('generate_key')
    return parser


def main():
    args = create_args_parser().parse_args()
    with grpc.insecure_channel(args.server_address) as channel:
        stub = BackupStub(channel)
        client = BackupClient(stub)
        if args.command == 'backup':
            client.upload_backup(args.path, args.key, args.num_of_threads)
        elif args.command == 'restore':
            client.restore_backup(args.id, args.restore_to, args.key)
        elif args.command == 'delete':
            client.delete_backup(args.id, args.key)
        elif args.command == 'list':
            client.list_backups()
        elif args.command == 'generate_key':
            client.generate_key()


if __name__ == '__main__':
    main()
