import grpc
from backup_system_pb2_grpc import add_BackupServicer_to_server
from backup_system_pb2 import UploadBackupResponse, AddBlocksResponse, GetBackupResponse, Block, GetBlocksResponse, DeleteBackupResponse, Row, UpdateDictResponse, ListBackupsResponse
from concurrent import futures
import os
import csv
import pickle
import time
import shutil
import argparse


class BackupServicer():

    def __init__(self, backups_dir, dictionary_file):
        self.backups_dir = backups_dir
        self.meta_file = os.path.join(self.backups_dir, 'meta.csv')
        self.dictionary_file = dictionary_file
        with open(dictionary_file, 'rb') as f:
            self.dictionary = pickle.load(f)
  
    def UploadBackup(self, request, context):
        curr_backup_dir = os.path.join(self.backups_dir, request.id)
        os.mkdir(curr_backup_dir)
        backup_file = os.path.join(curr_backup_dir, 'data.bin')     
        with open(backup_file, 'wb') as f:
            f.write(request.data)
        with open(self.meta_file, 'a') as f:
            writer = csv.writer(f)
            writer.writerow([request.id, time.asctime(time.gmtime())])     
        missing_codes = []      
        for code in request.codes:        
            if code not in self.dictionary:
                missing_codes.append(code)     
            else:
                self.dictionary[code][1] += 1    
        return UploadBackupResponse(codes=missing_codes)
        
    def AddBlocks(self, request, context):  
        for block in request.blocks:
            self.dictionary[block.code] = [block.data, 1] 
        with open(self.dictionary_file, 'wb') as d:
            pickle.dump(self.dictionary, d) 
        return AddBlocksResponse()

    def GetBackup(self, request, context):
        if not request.id in os.listdir(self.backups_dir):
            return GetBackupResponse()
        file_to_restore = os.path.join(self.backups_dir, request.id, 'data.bin')
        with open(file_to_restore, 'rb') as f:
            data = f.read()
        return GetBackupResponse(data=data)

    def GetBlocks(self, request, context):
        blocks = []
        for code in request.codes:
            block = Block(code=code, data=self.dictionary[code][0])
            blocks.append(block)
        return GetBlocksResponse(blocks=blocks)
    
    def DeleteBackup(self, request, context):
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
        for code in request.codes:            
            if self.dictionary[code][1] == 1:
                del self.dictionary[code]        
            else:
                self.dictionary[code][1] -= 1 
        with open(self.dictionary_file, 'wb') as d:
            pickle.dump(self.dictionary, d)
        return UpdateDictResponse()

    def ListBackups(self, request, context):
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
    parser.add_argument('backups_dir')
    return parser

def create_dictionary(root_path):
    dictionary_file = os.path.join(root_path, 'dictionary')
    with open(dictionary_file, 'wb') as d:
        pickle.dump({}, d)
    return dictionary_file

def create_meta_file(root_path):
    meta_file = os.path.join(root_path, 'meta.csv')
    with open(meta_file, 'a') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'creation_time'])

def serve():
    args = create_args_parser().parse_args()
    backups_dir = args.backups_dir
    server = grpc.server(futures.ThreadPoolExecutor())
    
    if 'dictionary' not in os.listdir(backups_dir):
        dictionary_file = create_dictionary(backups_dir)
    
    else:
        dictionary_file = os.path.join(backups_dir, 'dictionary')
    
    if 'meta.csv' not in os.listdir(backups_dir):
        create_meta_file(backups_dir)
    
    add_BackupServicer_to_server(BackupServicer(backups_dir, dictionary_file), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()