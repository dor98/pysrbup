import sys
import os
import csv
import uuid 
import time
import shutil
import pickle
import hashlib

BLOCK_SIZE = 100


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


class BackupTool:

    def __init__(self):
        self.backups_folder = r'C:\Users\dorse\OneDrive\Desktop\backups'
        self.meta_data = os.path.join(self.backups_folder, 'meta.csv')
        self.code_to_block_file = r'C:\Users\dorse\OneDrive\Desktop\backups\code_to_block'

        with open(self.code_to_block_file, 'rb') as f:
            self.code_to_block_dict = pickle.load(f)

   
    def build_structure(self, root_path):
        root_name = os.path.basename(os.path.realpath(root_path))
        root_node = Node('folder', root_name)

        for child in os.listdir(root_path):
            child_path = os.path.join(root_path, child)

            if os.path.isdir(child_path):
                root_node.children.append(self.build_structure(child_path))

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
                        
                        if code not in self.code_to_block_dict:
                            self.code_to_block_dict[code] = (block, 1)
                        
                        else:
                            self.code_to_block_dict[code] = (self.code_to_block_dict[code][0], self.code_to_block_dict[code][1] + 1)

                        child_node.codes.append(code)

        return root_node
    
    
    def restore_structrue(self, path, directory):

        directory_path = os.path.join(path, directory.name)
        os.mkdir(directory_path)

        for child in directory.children:

            if child.filetype == 'folder':
                self.restore_structrue(directory_path, child)
            
            else:
                file_path = os.path.join(directory_path, child.name)
                
                with open(file_path, 'wb') as f:
                    
                    for code in child.codes:
                        f.write(self.code_to_block[code])
    
    
    def update_code_to_block_dict(self, path, root):

        for child in root.children:

            if child.filetype == 'folder':
                self.update_code_to_block_dict(os.path.join(path, child.name), child)
            
            else:

                for code in child.codes:

                    if self.code_to_block_dict[code][1] == 1:
                        del self.code_to_block_dict[code]
                    
                    else:
                        self.code_to_block_dict[code] = (self.code_to_block_dict[code][0], self.code_to_block_dict[code][1] - 1)

    
    
    def backup(self, path, desc=None): 
        backup_id = str(uuid.uuid4()) 
        self.curr_backup_folder = os.path.join(self.backups_folder, backup_id)
        os.mkdir(self.curr_backup_folder)
        backup_content = self.build_structure(path)
        backup_file = os.path.join(self.curr_backup_folder, 'data.bin')

        with open(backup_file, 'wb') as f:
            pickle.dump(backup_content, f)
        
        with open(self.code_to_block_file, 'wb') as f:
            pickle.dump(self.code_to_block_dict, f)        

        with open(self.meta_data, 'a') as f:
            writer = csv.writer(f)
            writer.writerow([backup_id] + [time.asctime(time.gmtime())] + [desc])
        
        print('Backup has completed!')
         
    
    def restore_backup(self, backup_id, restore_to):

        if not backup_id in os.listdir(self.backups_folder):
            print('You have no backup with the specified id')
            sys.exit()
        
        file_to_restore = os.path.join(self.backups_folder, backup_id, 'data.bin')
        
        with open(file_to_restore, 'rb') as f:
            root_dir = pickle.load(f)
        
        self.restore_structure(restore_to, root_dir)            
        print('Backup {} has been restored'.format(backup_id))

    
    def delete_backup(self, backup_id):
        
        if backup_id not in os.listdir(self.backups_folder):
            print('You have no backups with the provided id')
            sys.exit()
        
        backup_folder = os.path.join(self.backups_folder, backup_id)
        backup_file = os.path.join(backup_folder, 'data.bin')
        
        with open(backup_file, 'rb') as f:
            root_obj = pickle.load(f)

        self.update_code_to_block_dict(backup_folder, root_obj)

        with open(self.code_to_block_file, 'wb') as f:
            pickle.dump(self.code_to_block_dict, f)

        shutil.rmtree(backup_folder)
        print('Backup {} has been deleted'.format(backup_id))


    def list_backups(self):
        
        with open(self.meta_data, 'r') as mf:
            rows = csv.reader(mf)
            count_backups = 0
            
            for row in rows:
                
                if row and row[0] != 'id':
                    backup = {'id': row[0], 'creation_date': row[1], 'description': row[2]}
                    print(backup, '\n')
                    count_backups += 1   

            print('Total number of backups: {}'.format(count_backups))
