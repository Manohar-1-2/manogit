from repository import repo_find
from utility.filehandling import repo_file
import zlib
import os
import hashlib
import sys
import time

class GitObject:
    def __init__(self,data=None):
        if data!=None:
            self.deserialize(data)
        else:
            self.init()
    def deseriallize(self,data):
        raise Exception("Not implementd")
    def seriallize(self):
        raise Exception("Not implementd")
    def init():
        pass
class GitBlob(GitObject):
    fmt=b'blob'

    def serialize(self):
        return self.blobdata

    def deserialize(self, data):
        self.blobdata = data
class GitTree(GitObject):
    fmt = b'tree'
    def __init__(self, data=None,isDeserialized=False):
        if isDeserialized:
            self.entries=data
        else:
            self.entries = []
            self.deserialize(data)
    def serialize(self):
        result = b''
        for mode, name, sha in self.entries:
            result += f"{mode} {name}".encode() + b'\x00' + bytes.fromhex(sha)
        return result

    def deserialize(self, data):
        
        i = 0
        while i < len(data):
            space_idx = data.find(b' ', i)
            if space_idx == -1:
                break

            mode = data[i:space_idx].decode()

            null_idx = data.find(b'\x00', space_idx)
            name = data[space_idx + 1:null_idx].decode()

            sha_raw = data[null_idx + 1:null_idx + 21]
            sha_hex = sha_raw.hex()

            self.entries.append((mode, name, sha_hex))
            i = null_idx + 21
        

class GitCommit(GitObject):
    fmt = b'commit'

    def __init__(self, kv=None,message=None,isDeserialized=False):
        if isDeserialized:
            self.kv=kv
            self.message=message
        else:
            self.kv =  {}  # key-value fields (tree, parent, author, etc.)
            self.deserialize(kv)


    def serialize(self):
        content = ""
        for key, value in self.kv.items():
            content += f"{key} {value}\n"
        content += "\n" + self.message + "\n"
        return content.encode()

    def deserialize(self, data):
        
        lines = data.decode().split("\n")
        i = 0

        # Read key-value pairs
        while i < len(lines):
            line = lines[i]
            if line == "":
                i += 1
                break
            key, value = line.split(" ", 1)
            self.kv[key] = value
            i += 1
        self.message = "\n".join(lines[i:]).strip()

def objectRead(repo,sha):

    path=repo_file(repo,"objects",sha[:2],sha[2:])
    
    if not os.path.isfile(path):
        return None
    with open(path,"rb") as f:
        r=zlib.decompress(f.read())
        x=r.find(b' ')
        fmt=r[0:x]

        y=r.find(b'\x00',x)
        size=int(r[x:y].decode("ascii"))

        if size!=len(r)-y-1:
            raise Exception("Malformd bad length")
        match fmt:
            case b'blob'   : c=GitBlob
            case b'tree'   : c=GitTree
            case b'commit'   : c=GitCommit
            case _:
                raise Exception(f"Unknown type {fmt.decode('ascii')} for object {sha}")
        return c(r[y+1:])

def object_write(obj, repo=None):
    # Serialize object data
    data = obj.serialize()

    # Add header
    result = obj.fmt + b' ' + str(len(data)).encode() + b'\x00' + data
    # Compute hash
    sha = hashlib.sha1(result).hexdigest()

    if repo:
        # Compute path
        path=repo_file(repo, "objects", sha[0:2], sha[2:], mkdir=True)

        if not os.path.exists(path):
            with open(path, 'wb') as f:
                # Compress and write
                f.write(zlib.compress(result))
    return sha



def cat_file(args):
    repo = repo_find()
    obj = objectRead(repo, args.object)
    
    if args.type == "tree":
        for mode, name, sha in obj.entries:
            print(f"{mode} {name} {sha}")
    else:
        sys.stdout.buffer.write(obj.serialize())


def cmd_hash_object(args):
    if args.write:
        repo = repo_find()
    else:
        repo = None
    print(repo.gitdir)
    with open(args.path, "rb") as fd:
        sha = object_hash(fd, args.type.encode(), repo)
        print(sha)

def object_hash(fd, fmt, repo=None):
    """ Hash object, writing it to repo if provided."""
    data = fd.read()

    # Choose constructor according to fmt argument
    match fmt:
        case b'blob'   : obj=GitBlob(data)
        case _: raise Exception(f"Unknown type {fmt}!")

    return object_write(obj, repo)

def update_index(repo, path, sha):
    index_path = repo_file(repo, "index", mkdir=True)
    lines = []
    if os.path.exists(index_path):
        with open(index_path, "r") as f:
            lines = f.readlines()

    lines = [l.strip() for l in lines if not l.startswith(path)]
    lines.append(f"{path} {sha}")

    with open(index_path, "w") as f:
        f.write("\n".join(lines) + "\n")
def addFile(filePath,repo):
    
    filePath=os.path.join(repo.workingtree,filePath)
    if not os.path.exists(filePath):
        raise Exception("file not found")
    with open(filePath, "rb") as fd:
        sha = object_hash(fd, b'blob', repo)
    update_index(repo,os.path.relpath(filePath, repo.workingtree),sha)


def read_index(repo):
    index_path = os.path.join(repo.gitdir, "index")
    index = {}

    if not os.path.exists(index_path):
        return index  # Return empty if no index yet

    with open(index_path, "r") as f:
        for line in f:
            path, sha = line.strip().split(" ", 1)
            index[path] = sha

    return index
def write_index(repo, index):
    index_path = os.path.join(repo.gitdir, "index")

    with open(index_path, "w") as f:
        for path, sha in sorted(index.items()):
            f.write(f"{path} {sha}\n")
def remove_from_index(repo, path):
    index = read_index(repo)
    if path in index:
        del index[path]
        write_index(repo, index)

def cmd_add(args):
    repo = repo_find()
    
    # Get all currently indexed files
    index = read_index(repo)  # You must already have this function
    indexed_files = set(index.keys())

    # Track all files that exist now
    current_files = set()

    if os.path.isdir(args.path):
        for root, dirs, files in os.walk(args.path):
            # Skip .manogit directory
            if ".manogit" in dirs:
                dirs.remove(".manogit")

            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, repo.workingtree)
                current_files.add(rel_path)
                addFile(rel_path, repo)
    else:
        current_files.add(args.path)
        addFile(args.path, repo)

    # Remove deleted files from index
    deleted_files = indexed_files - current_files
    for path in deleted_files:
        remove_from_index(repo, path)  # You need to implement this

