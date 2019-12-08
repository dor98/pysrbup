import filecmp
import os
import tempfile
from concurrent import futures
from threading import Thread

import grpc
import pytest
from backup_system_client import BackupClient
from backup_system_pb2_grpc import BackupStub, add_BackupServicer_to_server
from backup_system_server import BackupServicer, create_dictionary


def start_server():
    with tempfile.TemporaryDirectory() as backup_dir:
        dictionary_file = create_dictionary(backup_dir)
        server = grpc.server(futures.ThreadPoolExecutor())
        add_BackupServicer_to_server(
            BackupServicer(backup_dir, dictionary_file), server)
        server.add_insecure_port('[::]:50051')
        server.start()
        server.wait_for_termination()
        return


@pytest.fixture
def server():
    server_thread = Thread(target=start_server, daemon=True)
    server_thread.start()


@pytest.fixture
def client():
    channel = grpc.insecure_channel('localhost:50051')
    stub = BackupStub(channel)
    return BackupClient(stub)


def test_upload_backup_and_restore(server, client):
    key = client.generate_key()
    dir_to_backup = r'C:\Users\dorse\OneDrive\Desktop\backup_tool\testing\test_dir'
    backup_id = client.upload_backup(dir_to_backup, key)
    with tempfile.TemporaryDirectory() as restore_to_dir:
        client.restore_backup(backup_id, restore_to_dir, key)
        assert are_equal_dirs(
            dir_to_backup,
            os.path.join(restore_to_dir, os.path.basename(dir_to_backup)))


def are_equal_dirs(dir1, dir2):
    c = filecmp.dircmp(dir1, dir2)
    if len(c.left_only) > 0 or len(c.right_only) > 0:
        return False
    common_dirs = c.common_dirs
    comp_result = filecmp.cmpfiles(dir1, dir2, c.common_files)
    return (not comp_result[1] and not comp_result[2])\
            and all (are_equal_dirs(os.path.join(dir1, common_dirs[i]), os.path.join(dir2, common_dirs[i])) for i in range(len(common_dirs)))
