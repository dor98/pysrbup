# Secure Backup System

Command line app for remote, encrypted, compressed backups.

## Features

- Distributed with client-server architecture
- Data is encrypted client-side and server is untrusted
- Deduplication: identical data from multiple backups in the same repository take minimal additional space (32 byte for every 1 MB shared between backups)
- Compression
- Resumable backups: backups that are interrupted and restarted take almost no additional time
- Fast: data is processed concurrently by both client and server
- Network efficient: only the minimal amount of data is exchanged between client and server
- Backups to the same server can be done concurrently and asynchronously from different clients
- Configurable error correction
- Written in Python
- Uses gRPC for client-server communication

## Usage

First, you need to set up the server to run on the machine you want your backups to be stored. Then, whenever you want to back up a directory, you run the client and specify the server address.

### Server

```sh
pysrbup-server --bind-to=localhost:50000 --num-threads=2 <backups_dir>
```

### Client

The commands below use `localhost:50000` as the server address. Replace it with the address where your server is running.

#### Creating a backup

```sh
pysrbup-client --server-address=localhost:50000 --num-threads=2 backup <backup_dir> <key_file>
```

#### Restoring a backup

```sh
pysrbup-client --server-address=localhost:50000 --num-threads=2 restore <backup_id> <restore_dir> <key_file>
```

#### Deleting a backup

```sh
pysrbup-client --server-address=localhost:50000 --num-threads=2 delete <backup_id> <key_file>
```

#### Listing backups

```sh
pysrbup-client --server-address=localhost:50000 --num-threads=2 list
```

#### Generating an encryption key

```sh
pysrbup-client generate_key
```

## Building the project

```sh
# cd to project directory, create a python 3.6 virtual env and then:
./tools/build.sh
```

## Limitations

The following is a list of known limitations.

### Temporary limitations

These limitations are being worked on and expected to be removed in the near future.

- While the data is fully encrypted before it's sent to the server, a malicious server can track which set of encrypted blocks comprises each backup, and know when an encrypted block is shared among backups.
- Deduplication uses a fixed chunk size of 1 MB. Support for variable chunk sizes is planned.
- Partial restores are not supported (you must restore the backup in full to access the files)
- Asymmetric encryption is not supported

### Limitations from design

- All the backups in a repository must share the same encryption key. Users who want to use multiple keys must use separate repositories.

## Design

- The server is running continuously waiting for requests from clients. The server is responsible for storing the backups.
- The client initiates the communication with the server. The user invokes the client for creating and managing backups.
- The server is untrusted:
  - Data is encrypted before leaving the client and only minimal information is sent to the server.
  - When restoring, the data is authenticated by the client.
- No authentication between the client and server processes is done. This is a feature: it's intended to simplify the system. Authentication can be added by using lower level software like a VPN.
- Every file is split to chunks by the client. Identical chunks are only stored once in the server.
- Before exchanging any data, the client and server are synchronizing what data each of them have, in order to exchange the minimal amount of data needed, which reduces load from the network and improves the speed of the different operations.
- Cryptographic key management is done by the user: the client needs access to the key for the different operations, but is not responsible for storing the key.
- All the data in a backup repository is encrypted with the same key. This enables the system to deduplicate data within a backup and across backups in the same repository, which results in significant storage savings.

## Contributing

We welcome any contributions!
You can help by opening and commenting on bugs, writing documentation, and sending PRs. Please see the guidelines below before starting to contribute:

- Open an issue before starting any major work, in order to coordinate the development with the main developers and ensure your contribution is a good fit for the project's goals and design.
- We follow [Google's style guide for Python](https://google.github.io/styleguide/pyguide.html)
- Code must be compatible Python 3.6 and later
- Code must be formatted with [yapf](https://github.com/google/yapf)
- Code must pass [pylint](https://www.pylint.org/)
- Write tests for any new code you add
