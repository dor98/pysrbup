import sys
import os
import csv
import uuid 
import time
import shutil

class BackupTool:

    def __init__(self):
        self.backups = r'C:\Users\dorse\OneDrive\Desktop\backups'
        self.meta_data = os.path.join(self.backups, 'meta.csv')

    def backup(self, path, desc=None): 
        backup_id = str(uuid.uuid4())
        curr_backup = os.path.join(self.backups, backup_id)
        os.mkdir(curr_backup)

        for filename in os.listdir(path):
            backup_file = os.path.join(curr_backup, filename)
            file_to_backup = os.path.join(path, filename)
            
            with open(file_to_backup) as rf, open(backup_file, 'w') as wf:
                data = rf.read()
                wf.write(data)
                rf.close()
                wf.close()
        
        with open(self.meta_data, 'a+') as mf:
            writer = csv.writer(mf)
            writer.writerow([backup_id] + [desc] + [time.asctime(time.gmtime())])
            mf.close()
        
        print('Backup has completed!')
         
    def restore_backup(self, id, restore_to):

        if not id in os.listdir(self.backups):
            print('You have no backup with the specified id')
            sys.exit()

        backup_to_restore = os.path.join(self.backups, id)
        restore_to_folder = os.path.join(restore_to, id)
        os.mkdir(restore_to_folder)

        for filename in os.listdir(backup_to_restore):
            file_to_restore = os.path.join(backup_to_restore, filename)
            restore_to_file = os.path.join(restore_to_folder, filename)
            
            with open(file_to_restore) as rf, open(restore_to_file, 'w') as wf:
                data = rf.read()
                wf.write(data)
                rf.close()
                wf.close()
        
        print('Backup {} has been restored'.format(id))


    def delete_backup(self, id):
        
        if id not in os.listdir(self.backups):
            print('You have no backups with the provided id')
            sys.exit()
        
        backup_to_delete = os.path.join(self.backups, id)
        shutil.rmtree(backup_to_delete)
        print('Backup {} has been deleted'.format(id))


    def list_backups(self):
        
        with open(self.meta_data, 'r') as mf:
            rows = csv.reader(mf)
            count_backups = 0
            
            for row in rows:
                
                if row and row[0] != 'id':
                    backup = {'id': row[0], 'description': row[1], 'creation_date': row[2]}
                    print(backup, '\n')
                    count_backups += 1   

            print('Total number of backups: {}'.format(count_backups))