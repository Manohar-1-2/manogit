
from objects import objectRead
from ref import get_head_ref, get_ref_sha
from repository import repo_find



def traverse_commits(obj,sha,repo):
    if not "parent" in obj.kv.keys():
        print("<--- "+sha,end="")
        return
    print("<--- "+sha,end="")
    sha=obj.kv["parent"]
    obj=objectRead(repo,sha)
    traverse_commits(obj,sha,repo)


def cmd_log(args):
    repo=repo_find()
    latest_commit_ref=get_head_ref(repo)
    latest_commit_sha=get_ref_sha(repo,latest_commit_ref)
    obj=objectRead(repo,latest_commit_sha)
    traverse_commits(obj,latest_commit_sha,repo)