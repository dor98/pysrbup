import argparse 
import sys
import grpc
import os
import logging
import backup_system_client
import backup_system_pb2, backup_system_pb2_grpc

def create_args_parser():
    parser = argparse.ArgumentParser()
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
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = backup_system_pb2_grpc.BackupStub(channel)
        client = backup_system_client.BackupClient(stub)

        if args.command == 'backup':
            client.upload_backup(args.path, args.key)
        
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