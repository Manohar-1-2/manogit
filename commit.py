
import difflib
import os
import time

from objects import GitCommit, object_write, objectRead
from ref import get_head_ref, update_ref_sha
from repository import repo_find
from tree import create_tree_from_index, deserialize_tree, serialize_tree
from utility.filehandling import repo_file


def create_commit(tree_sha, parent_sha, message, repo):
    timestamp = int(time.time())
    timezone = "+0530"
    author = "Manohar <manohar@example.com>"

    kv = {
        "tree": tree_sha,
        "author": f"{author} {timestamp} {timezone}",
        "committer": f"{author} {timestamp} {timezone}"
    }

    if parent_sha:
        kv["parent"] = parent_sha

    commit = GitCommit(kv=kv,message=message,isDeserialized=True)

    return object_write(commit, repo)

def get_parent_commit_sha(repo):
    head_path = repo_file(repo, "HEAD")

    with open(head_path, "r") as f:
        ref_line = f.read().strip()

    if ref_line.startswith("ref: "):
        ref_path = ref_line[5:]  # Remove 'ref: '
        full_ref_path = repo_file(repo, *ref_path.split("/"))

        if os.path.exists(full_ref_path):
            with open(full_ref_path, "r") as rf:
                return rf.read().strip()
    return None

def get_index(repo):
    index_path = repo_file(repo, "index", mkdir=True)
    lines = []
    if os.path.exists(index_path):
        with open(index_path, "r") as f:
            lines = f.readlines()
    index={}
    for line in lines:
        path,sha=line.split(" ")
        index[path]=sha
    return index

def print_tree(tree,index,dir="",):
    for file_node in tree.files:
        index[os.path.join(dir, file_node.name)]=file_node.sha
    
    for dir_node in tree.dirs:
        print_tree(dir_node.subtree,index, os.path.join(dir, dir_node.name))
    return index
def get_index_from_tree(repo):
    head_commit_sha=get_parent_commit_sha(repo)
    head_commit=objectRead(repo,head_commit_sha)
    if head_commit==None:
        return None
    root_tree_sha=head_commit.kv["tree"]
    tree=objectRead(repo,root_tree_sha)
    tree=deserialize_tree(tree,repo)
    # print(tree.files)
    index_from_tree=print_tree(tree,{},"")
    return index_from_tree


def compare_staged_committree(index1,index2):
    """
    index1: dict from HEAD tree (committed)
    index2: dict from current index (staged)
    """

    if index1==None or index2==None:
        return None
    paths1 = set(index1.keys())
    paths2 = set(index2.keys())

    added = paths2 - paths1
    deleted = paths1 - paths2
    modified = {path for path in paths1 & paths2 if index1[path].strip() != index2[path]}

    for path in sorted(added):
        print(f"Deleted: {path}")
    for path in sorted(deleted):
        print(f"Added: {path}")
    for path in sorted(modified):
        print(f"Modified: {path}")
    return [modified,added,deleted]



def cmd_create_commit(args):
    repo=repo_find()
    index1=get_index(repo)
    index2=get_index_from_tree(repo)
    if compare_staged_committree(index1,index2)!=None:
        modifed,added,deleted=compare_staged_committree(index1,index2)
        if len(modifed)==0 and len(added)==0 and len(deleted)==0 :
            print("nothing to commit,working tree is clean")
        else:
            tree=create_tree_from_index()
            tree_sha=serialize_tree(tree,repo)
            parent_sha=get_parent_commit_sha(repo)
            message=args.message
            print(message)
            commit_sha=create_commit(tree_sha,parent_sha,message,repo)
            update_ref_sha(repo,get_head_ref(repo),commit_sha)
    else:
        tree=create_tree_from_index()
        tree_sha=serialize_tree(tree,repo)
        parent_sha=get_parent_commit_sha(repo)
        message=args.message
        print(message)
        commit_sha=create_commit(tree_sha,parent_sha,message,repo)
        update_ref_sha(repo,get_head_ref(repo),commit_sha)
def diff_blobs(repo, sha1, sha2):
    blob1 = objectRead(repo, sha1).blobdata.decode()
    blob2 = objectRead(repo, sha2).blobdata.decode()

    diff = difflib.unified_diff(
        blob1.splitlines(),
        blob2.splitlines(),
        fromfile='old',
        tofile='new',
        lineterm=''
    )
    return '\n'.join(diff)

def cmd_status(args):
    repo=repo_find()
    modifed,added,deleted=compare_staged_committree(repo)

    sha1="6c2cdbcda4f2b7a1253c0f78320fabfa3f2517ea"
    sha2="e2894c98a2d21d34459695b1f5b4b895a48fc8a0"

    print(diff_blobs(repo,sha1,sha2))