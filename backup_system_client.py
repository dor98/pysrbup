import grpc
from backup_system_pb2 import UpdateDictRequest, ListBackupsRequest, UploadBackupRequest, GetMissingCodesRequest, PushBlocksRequest, Block, GetBackupRequest, GetBlocksRequest, DeleteBackupRequest
import sys
import os
import uuid 
import time
import pickle
import hashlib
import threading
from cryptography.fernet import Fernet
from queue import Queue

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
        queue = Queue()
        fernet_obj = Fernet(key)
        self.more_work = True
        threads = []   
        
        for _ in range(num_of_threads):
            thread = threading.Thread(target=self.update_missing_blocks, args=(codes_dict, queue, fernet_obj))
            thread.start()
            threads.append(thread) 
        
        backup_node = self.build_structure(path, codes_dict, queue)
        self.more_work = False
        backup_node = fernet_obj.encrypt(pickle.dumps(backup_node))
        upload_backup_request = UploadBackupRequest(id=backup_id, data=backup_node)
        self.stub.UploadBackup(upload_backup_request)    
        
        for thread in threads:
            thread.join()   
        
        print('Completed backup id: {}'.format(backup_id))
        return backup_id

    def update_missing_blocks(self, codes_dict, queue, fernet_object):      
        codes = list()
        
        while self.more_work or not queue.empty():
            
            try:
                codes.append(queue.get())
            
            except:
                continue
            
            if codes and queue.empty():
                missing_codes = self.stub.GetMissingCodes(GetMissingCodesRequest(codes=codes)).codes
                self.push_blocks(missing_codes, codes_dict, fernet_object)
                codes = list()
    
    def push_blocks(self, missing_codes, codes_dict, fernet_object):
        blocks = []
        
        for code in missing_codes:
            block_data = fernet_object.encrypt(codes_dict[code])   
            blocks.append(Block(code=code, data=block_data))
        
        self.stub.PushBlocks(PushBlocksRequest(blocks=blocks))
          
    def build_structure(self, root_path, codes_dict, queue):       
        root_name = os.path.basename(os.path.realpath(root_path))
        root_node = BackupNode('folder', root_name) 
        
        for child in os.listdir(root_path):
            child_path = os.path.join(root_path, child)
            
            if os.path.isdir(child_path):
                root_node.children.append(self.build_structure(child_path, codes_dict, queue))
            
            else:
                child_node = BackupNode('file', child)
                root_node.children.append(child_node) 
                
                with open(child_path, 'rb') as rf:
                    
                    while True:
                        block = rf.read(BLOCK_SIZE) 
                        
                        if not block: 
                            break
                        
                        hash_function = hashlib.sha256()
                        hash_function.update(block)
                        code = hash_function.hexdigest()
                        codes_dict[code] = block
                        child_node.codes.append(code) 
                        queue.put(code)              
        
        return root_node
    
    def restore_backup(self, id, restore_to_path, key):
        fernet_obj = Fernet(key)
        get_backup_request = GetBackupRequest(id=id)
        data = pickle.loads(fernet_obj.decrypt(self.stub.GetBackup(get_backup_request).data))
        self.restore(data, restore_to_path, fernet_obj)
        print('Backup {} has been restored to {}'.format(id, restore_to_path))

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
                
                get_blocks_response = self.stub.GetBlocks(GetBlocksRequest(codes=codes))
                
                with open(file_path, 'wb') as f:
                    
                    for block in get_blocks_response.blocks:
                        f.write(fernet_obj.decrypt(block.data))
    
    def delete_backup(self, id, key):
        delete_backup_request = DeleteBackupRequest(id=id)
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
            print('Backup ID: {}, Creation Time: {}'.format(row.col[0], row.col[1]))
    
    def generate_key(self):
        key = Fernet.generate_key()
        print('Your key: {}'.format(key))
        return key