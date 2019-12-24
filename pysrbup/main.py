import argparse
import os
import sys

import grpc

from client import BackupClient
from backup_system_pb2_grpc import BackupStub


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