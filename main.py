import argparse 
import sys
from client import BackupTool

def create_args_parser():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')
    subparsers.required = True
    backup_parser = subparsers.add_parser('backup')
    backup_parser.add_argument('path')
    backup_parser.add_argument('--description')
    restore_parser = subparsers.add_parser('restore')
    restore_parser.add_argument('id')
    restore_parser.add_argument('restore_to')
    delete_backup_parser = subparsers.add_parser('delete')
    delete_backup_parser.add_argument('id')
    list_backups_parser = subparsers.add_parser('list')
    return parser

def main():
    args = create_args_parser().parse_args()
    obj = BackupTool()

    if args.command == 'backup':
        obj.backup(args.path, args.description)
        
    elif args.command == 'restore':
        obj.restore_backup(args.id, args.restore_to)
    
    elif args.command == 'delete':
        obj.delete_backup(args.id)
    
    elif args.command == 'list':
        obj.list_backups()


if __name__ == '__main__':
    main()