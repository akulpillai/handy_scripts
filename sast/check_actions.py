import os
import requests
import tempfile
import yaml

github_token = ""  # paste token here dear sir

# actions to be checked
actions_to_check = []

# GitHub API endpoint

headers = {
    "Authorization": f"token {github_token}",
    "Accept": "application/vnd.github.v3+json",
}


def update_actions_list():
    global actions_to_check
    with open("actions_list", "r") as actions_list_file:
        action_urls = actions_list_file.readlines()
        for action_url in action_urls:
            action_url = action_url.split("/")
            action_name = action_url[-1].strip()
            actions_to_check.append(action_name)


def get_workflow_files(url):
    response = requests.get(url, headers=headers)
    if response:
        return [file_info for file_info in response.json() if
                file_info['name'].endswith(('.yml', '.yaml'))]
    else:
        return []


def download_workflow_file(file_info, dir_path):
    download_url = file_info['download_url']
    response = requests.get(download_url)
    response.raise_for_status()

    file_path = os.path.join(dir_path, file_info['name'])
    with open(file_path, 'w') as file:
        file.write(response.text)


def check_actions_in_workflow(file_path):
    try:
        with open(file_path, 'r') as file:
            workflow = yaml.safe_load(file)

        actions_list = []
        jobs = workflow.get('jobs', {})
        for job in jobs.values():
            steps = job.get('steps', [])
            for step in steps:
                uses_action = step.get('uses')
                if uses_action:
                    for action in actions_to_check:
                        if action in uses_action:
                            actions_list.append(action)
        return actions_list
    except:  # we check manually if anything goes wrong
        return ["YML PARSE ERROR"]


def main():

    update_actions_list()

    with open("repo_list", "r") as repo_list_file:
        repo_urls = repo_list_file.readlines()
        for repo_url in repo_urls:
            repo_url = repo_url.split("/")
            repo_name = repo_url[-1].strip()
            owner_name = repo_url[-2].strip()

            url = f"https://api.github.com/repos/{owner_name}/{repo_name}/contents/.github/workflows"
            workflow_files = get_workflow_files(url)
            actions_used = []
            with tempfile.TemporaryDirectory() as temp_dir:
                for file_info in workflow_files:
                    download_workflow_file(file_info, temp_dir)
                    file_path = os.path.join(temp_dir, file_info['name'])
                    found_actions = check_actions_in_workflow(file_path)
                    for action in found_actions:
                        if action not in actions_used:
                            actions_used.append(action)

            print(f"{owner_name}/{repo_name}, {actions_used}")


if __name__ == "__main__":
    main()
