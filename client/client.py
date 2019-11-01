import argparse, os, sys, csv, uuid, time, shutil

class BackupTool:

    def __init__(self):
        parser = argparse.ArgumentParser(description= 'BACKUP TOOL', usage='''client.py <command> [<args>]
        
Available Commands:
        
   backup      Performs a new backup
   restore     Restores past backup
   delete      Deletes past backup
   list        Lists past bakcups for the specified date range''')
        
        parser.add_argument('command', help='Subcommand to run')
        args = parser.parse_args(sys.argv[1:2])

        if not hasattr(self, args.command):
            print ('Unrecognized command\n')
            parser.print_help()
            exit(1)
        
        getattr(self, args.command)()

    
    def backup(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('path')
        parser.add_argument('--description')
        args = parser.parse_args(sys.argv[2:]) 
        backup_id = str(uuid.uuid4())
        path_to_read_from = args.path + '/'
        path_to_write_to = 'C:/Users/dorse/OneDrive/Desktop/backups/' + backup_id + '/'
        os.mkdir(path_to_write_to)

        for filename in os.listdir(path_to_read_from): 
            
            with open(path_to_read_from + filename) as f, open(path_to_write_to + filename, 'w') as out:
                data = f.read()
                out.write(data)
                f.close()
                out.close()
        
        with open('C:/Users/dorse/OneDrive/Desktop/backups/meta.csv', 'a') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow([backup_id] + [args.description] + [str(time.time())])
            csv_file.close()
            
 
    def restore(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('id')
        parser.add_argument('restore_to')
        args = parser.parse_args(sys.argv[2:])
        backup_id = args.id
        restore_to = args.restore_to
        backups_directory = 'C:/Users/dorse/OneDrive/Desktop/backups'
        
        for folder in os.listdir(backups_directory):
            
            if folder == backup_id:
                restored_folder = restore_to + '/' + folder
                os.mkdir(restored_folder)
                directory_to_restore = backups_directory + '/' + folder
                
                for filename in os.listdir(directory_to_restore):
                    
                    with open(directory_to_restore + '/' + filename, 'r') as f, open(restored_folder + '/' + filename, 'w') as out:
                        data = f.read()
                        out.write(data)
                        f.close()
                        out.close()
                break

    
    def delete_backup(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('id')
        args = parser.parse_args(sys.argv[2:])
        backup_id = args.id
        backups_directory = 'C:/Users/dorse/OneDrive/Desktop/backups'

        if backup_id not in os.listdir(backups_directory):
            print('You have no backups with the provided id')
            exit(1)
        
        directory_to_delete = backups_directory + '/{}'.format(backup_id)
        shutil.rmtree(directory_to_delete)


    def list_backups(self):
        raise NotImplementedError
      
if __name__ == '__main__':
    BackupTool()
