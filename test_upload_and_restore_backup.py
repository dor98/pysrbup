import grpc
from backup_system_pb2_grpc import add_BackupServicer_to_server, BackupStub
import filecmp
import tempfile
import os 
from backup_system_client import BackupClient
from backup_system_server import BackupServicer, create_dictionary
import threading
from concurrent import futures
import pytest

OPTIONS = [('grpc.max_send_message_length', 1024 ** 3), ('grpc.max_receive_message_length', 1024 ** 3)]
server_address = 'localhost:50000'
num_of_threads = 2

def start_server():    
    with tempfile.TemporaryDirectory() as backup_dir:
        dictionary_file = create_dictionary(backup_dir)
        server = grpc.server(futures.ThreadPoolExecutor(), options=OPTIONS)
        add_BackupServicer_to_server(BackupServicer(backup_dir, dictionary_file), server)
        server.add_insecure_port(server_address)
        server.start()
        server.wait_for_termination()

@pytest.fixture
def server():
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

@pytest.fixture
def client():
    channel = grpc.insecure_channel(server_address, options=OPTIONS)
    stub = BackupStub(channel)
    return BackupClient(stub)

def test_upload_backup_and_restore(server, client):  
    key = client.generate_key()
    dir_to_backup = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test_dir')
    backup_id = client.upload_backup(dir_to_backup, key)   
    
    with tempfile.TemporaryDirectory() as restore_to_dir:
        client.restore_backup(backup_id, restore_to_dir, key)
        assert are_equal_dirs(dir_to_backup, os.path.join(restore_to_dir, os.path.basename(dir_to_backup)))

def are_equal_dirs(dir1, dir2):
    comp_obj = filecmp.dircmp(dir1, dir2)   
    
    if len(comp_obj.left_only) > 0 or len(comp_obj.right_only) > 0:
        return False   
    
    common_dirs = comp_obj.common_dirs
    comp_result = filecmp.cmpfiles(dir1, dir2, comp_obj.common_files)
    
    return (not comp_result[1] and not comp_result[2])\
            and all (are_equal_dirs(os.path.join(dir1, common_dirs[i]), os.path.join(dir2, common_dirs[i])) for i in range(len(common_dirs)))