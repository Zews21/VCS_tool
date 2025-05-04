import datetime
import os
import json
from difflib import unified_diff
import argparse

log_path = ".vcs/log.json"


def init():
    os.makedirs(".vcs/commits", exist_ok=True)
    global log_path

    if not os.path.exists(log_path):
        with open(".vcs/log.json", 'w') as f:
            json.dump({'commits': []}, f, indent=2)
        print("Initialized empty VCS repository in .vcs/")
    else:
        print("VCS repository already initialized.")


def commit(directory: str, commit_message: str) -> None:
    directory = os.path.abspath(directory)
    nr_commits = len(os.listdir('.vcs/commits/'))
    commit_id = f"{nr_commits + 1:04d}"
    new_commit_path = os.path.join('.vcs/commits', commit_id)
    os.makedirs(new_commit_path, exist_ok=True)

    committed_files = []

    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)

            if '.vcs' in file_path or '.venv' in file_path or '.idea' in file_path or 'vcs.py' in file_path:
                continue

            print(file_path)
            relative_path = os.path.relpath(file_path, directory)
            commit_file_path = os.path.join(new_commit_path, relative_path)
            os.makedirs(os.path.dirname(commit_file_path), exist_ok=True)

            try:
                with open(file_path, 'r') as src, open(commit_file_path, 'w') as dest:
                    dest.write(src.read())
                committed_files.append(relative_path)
            except UnicodeDecodeError:
                print(f"Skipping binary or non-text file: {file_path}")

    log_commit(commit_id, commit_message, committed_files)
    print(f"Commit 000{nr_commits+1} created")


def log_commit(commit_id, message, commited_files):
    if os.stat(log_path).st_size == 0:
        log_data = {'commits': []}
    else:
        with open(log_path, 'r') as f:
            log_data = json.load(f)

    commit_entry = {
        "id": commit_id,
        "timestamp": datetime.datetime.now().isoformat(),
        "message": message,
        "files": commited_files
    }

    log_data["commits"].append(commit_entry)

    with open(log_path, 'w') as f:
        json.dump(log_data, f, indent=2)


def checkout(commit_id):
    commit_path = os.path.join(".vcs", "commits", commit_id)
    if not os.path.exists(commit_path):
        print(f"Commit {commit_id} does not exist.")
        return

    for root, _, files in os.walk(commit_path):
        for file in files:
            relative_path = os.path.relpath(os.path.join(root, file), commit_path)
            destination_path = os.path.join(os.getcwd(), relative_path)

            approve = input(f"Replace {relative_path} in working directory with version from commit {commit_id}?y/n: ").strip().lower()
            if approve == 'y':
                os.makedirs(os.path.dirname(destination_path), exist_ok=True)
                with open(os.path.join(root, file), 'r') as src, open(destination_path, 'w') as dest:
                    dest.write(src.read())
                print(f"{relative_path} replaced.")
            else:
                print(f"{relative_path} was not modified.")


def show_log():
    if not os.path.exists(log_path):
        print("No commits yet.")
        return

    with open(log_path, 'r') as log:
        log_data = json.load(log)

    for commit in log_data['commits']:
        timestamp = commit['timestamp'].split('.')[0].replace('T', ' ')
        print(f"{commit['id']} - {timestamp} - \" {commit['message']}\"")


def diff(file, commit_id):
    commited_file_path = os.path.join('.vcs/commits', commit_id, file)
    cwd_file_path = os.path.join('./', file)
    if not os.path.exists(commited_file_path):
        print(f"File name or commit id do not exist")
        return

    if not os.path.exists(cwd_file_path):
        print(f"Could not get current working directory path")
        return

    with open(cwd_file_path, 'r') as f1, open(commited_file_path, 'r') as f2:
        working_data = f1.read().splitlines()
        committed_data = f2.read().splitlines()

    delta = unified_diff(committed_data, working_data, fromfile='committed', tofile='working', lineterm='')
    print('\n'.join(list(delta)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="vcs", description="A simple version control system")
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Init
    init_parser = subparsers.add_parser('init', help='Initialise version control storage')

    # Commit
    commit_parser = subparsers.add_parser('commit', help='Create a new commit')
    commit_parser.add_argument('-m', '--message', required=True, help='Commit message')

    # Log
    log_parser = subparsers.add_parser('log', help='Show commit history')

    # Checkout
    checkout_parser = subparsers.add_parser("checkout", help="Restore files from a commit")
    checkout_parser.add_argument('commit_id', help='The commit ID to restore')

    # Diff
    diff_parser = subparsers.add_parser("diff", help="Compare file with a commit")
    diff_parser.add_argument('file', help="The file to compare")
    diff_parser.add_argument('commit_id', help="The commit ID to compare against")

    args = parser.parse_args()

    if args.command == 'commit':
        commit('.', args.message)
    elif args.command == 'log':
        show_log()
    elif args.command == 'checkout':
        checkout(args.commit_id)
    elif args.command == 'diff':
        diff(args.file, args.commit_id)
    elif args.command == 'init':
        init()