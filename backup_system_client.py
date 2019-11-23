import grpc
from backup_system_pb2 import UploadBackupRequest, Block, AddBlocksRequest, GetBackupRequest, GetBlocksRequest, DeleteBackupRequest, UpdateDictRequest, ListBackupsRequest
import sys
import os
import uuid 
import time
import pickle
import hashlib
from cryptography.fernet import Fernet

class Node:
    def __init__(self, filetype, name, children=None, codes=None):  
        if children is None:
            children = []  
        if codes is None:
            codes = [] 
        self.filetype = filetype
        self.name = name
        self.children = children
        self.codes = codes

BLOCK_SIZE = 100

class BackupClient:
    
    def __init__(self, stub):
        self.stub = stub

    def upload_backup(self, path, key):
        backup_id = str(uuid.uuid4())
        codes = []
        codes_dict = {}
        f = Fernet(key)
        serialized_data = pickle.dumps(self.build_structure(path, codes, codes_dict))
        encrypted_data = f.encrypt(serialized_data)
        upload_backup_request = UploadBackupRequest(id=backup_id, data=encrypted_data, codes=codes)
        missing_codes = self.stub.UploadBackup(upload_backup_request).codes
        self.add_blocks(missing_codes, codes_dict, f)
        print('Completed backup!\nBackup id: {}'.format(backup_id))
        return backup_id

    def build_structure(self, root_path, codes, codes_dict):
        root_name = os.path.basename(os.path.realpath(root_path))
        root_node = Node('folder', root_name) 
        for child in os.listdir(root_path):
            child_path = os.path.join(root_path, child)
            if os.path.isdir(child_path):
                root_node.children.append(self.build_structure(child_path, codes, codes_dict))
            else:
                child_node = Node('file', child)
                root_node.children.append(child_node) 
                with open(child_path, 'rb') as rf:
                    while True:
                        block = rf.read(BLOCK_SIZE) 
                        if not block: 
                            break
                        hash_function = hashlib.sha256()
                        hash_function.update(block)
                        code = hash_function.hexdigest()
                        codes.append(code)
                        codes_dict[code] = block
                        child_node.codes.append(code) 
        return root_node
        
    def add_blocks(self, missing_codes, codes_dict, fernet_object):   
        missing_blocks = []
        for code in missing_codes:
            block_data = codes_dict[code] 
            encrypted_block_data = fernet_object.encrypt(block_data)    
            missing_blocks.append(Block(code=code, data=encrypted_block_data))
        add_blocks_request = AddBlocksRequest(blocks=missing_blocks)
        self.stub.AddBlocks(add_blocks_request)
    
    def restore_backup(self, id, restore_to_path, key):
        get_backup_request = GetBackupRequest(id=id)
        data = self.stub.GetBackup(get_backup_request).data
        f = Fernet(key)
        decrypted_data = f.decrypt(data)
        deserialized_data = pickle.loads(decrypted_data)
        self.restore(deserialized_data, restore_to_path, f)
        print('Backup {} has been restored to {}'.format(id, restore_to_path))

    def restore(self, root_dir, restore_to_path, fernet_object):
        dir_path = os.path.join(restore_to_path, root_dir.name)
        os.mkdir(dir_path)
        for child in root_dir.children:
            if child.filetype == 'folder':
                self.restore(child, dir_path, fernet_object)
            else:
                file_path = os.path.join(dir_path, child.name)
                codes = []
                for code in child.codes:
                    codes.append(code)
                get_blocks_request = GetBlocksRequest(codes=codes)
                get_blocks_response = self.stub.GetBlocks(get_blocks_request)
                with open(file_path, 'wb') as f:
                    for block in get_blocks_response.blocks:
                        decrypted_block = fernet_object.decrypt(block.data)
                        f.write(decrypted_block)
    
    def delete_backup(self, id, key):
        delete_backup_request = DeleteBackupRequest(id=id)
        backup_obj = self.stub.DeleteBackup(delete_backup_request).data
        if not backup_obj:
            print('You have no backup with the given id.')
            return
        f = Fernet(key)
        decrypted_backup_obj = f.decrypt(backup_obj)
        deserialized_backup_object = pickle.loads(decrypted_backup_obj)
        self.update_dict(deserialized_backup_object)
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
            print('Backup ID: {}, Creation Time: {}'.format(row.col[0], row.col[1]))
    
    def generate_key(self):
        key = Fernet.generate_key()
        print('Your key: {}'.format(key))
        return key