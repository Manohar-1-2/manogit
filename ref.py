from utility.filehandling import repo_file
import os
def get_head_ref(repo):
    head_path = repo_file(repo, "HEAD")
    with open(head_path, "r") as f:
        ref_line = f.read().strip()

    if not ref_line.startswith("ref: "):
        raise Exception("HEAD is not a symbolic reference")

    return ref_line[5:] 

def get_ref_sha(repo, ref_path):
    ref_file = repo_file(repo, *ref_path.split("/"))
    if os.path.exists(ref_file):
        with open(ref_file, "r") as f:
            return f.read().strip()
    return None  

def update_ref_sha(repo, ref_path, new_sha):
    ref_file = repo_file(repo, *ref_path.split("/"), mkdir=True)
    with open(ref_file, "w") as f:
        f.write(new_sha + "\n")

