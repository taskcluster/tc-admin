import jsone
import json
import requests
import taskcluster
import os
import yaml
import slugid
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

SESSION = requests.Session()
adapter = HTTPAdapter(
    max_retries=Retry(
        total=3,
        read=3,
        connect=3,
        backoff_factor=0.3,
        status_forcelist=(500, 502, 503, 504),
    )
)
SESSION.mount("http://", adapter)
SESSION.mount("https://", adapter)


def get_tc_yml(pulse_payload):
    """
    Fetch .taskcluster.yml from the repository and parse it

    If TASKCLUSTER_YML_REPO is set, the file is fetched from the default branch
    of that repository; otherwise it is fetched from the repository where the
    push took place.
    """
    if "TASKCLUSTER_YML_REPO" in os.environ:
        repo = os.environ["TASKCLUSTER_YML_REPO"]
        head_rev = "default"
    else:
        repo = os.environ["REPO_URL"]
        head_rev = pulse_payload["data"]["heads"][0]
    res = SESSION.get("{}/raw-file/{}/.taskcluster.yml".format(repo, head_rev))
    res.raise_for_status()
    tcyml = res.text
    return yaml.safe_load(tcyml)


def render_tc_yml(tc_yml, push, head_rev):
    """
    Render .taskcluster.yml into an array of tasks.  This provides a context
    that is similar to that provided by actions and crons, but with `tasks-for`
    set to `hg-push`.
    """
    ownTaskId = slugid.nice().decode("ascii")
    context = dict(
        tasks_for="hg-push",
        push=dict(
            revision=head_rev,
            owner=push["user"],
            pushlog_id=push["pushid"],
            pushdate=push["time"],
        ),
        repository=dict(
            url=os.environ["REPO_URL"],
            project=os.environ["PROJECT"],
            level=os.environ["LEVEL"],
        ),
        ownTaskId=ownTaskId,
    )
    return jsone.render(tc_yml, context)


def main():
    pulse_message = json.loads(os.environ["PULSE_MESSAGE"])
    print("Pulse Message:")
    print(json.dumps(pulse_message, indent=4, sort_keys=True))

    pulse_payload = pulse_message["payload"]
    if pulse_payload["type"] != "changegroup.1":
        print("Not a changegroup.1 message")
        return

    push_count = len(pulse_payload["data"]["pushlog_pushes"])
    if push_count != 1:
        print("Message has {} pushes; only one supported".format(push_count))
        return

    head_count = len(pulse_payload["data"]["heads"])
    if head_count != 1:
        print("Message has {} heads; only one supported".format(head_count))
        return

    rendered = render_tc_yml(
        get_tc_yml(pulse_payload),
        pulse_payload["data"]["pushlog_pushes"][0],
        pulse_payload["data"]["heads"][0],
    )

    task_count = len(rendered["tasks"])
    if task_count != 1:
        print("Rendered result has {} tasks; only one supported".format(task_count))
        return
    task = rendered["tasks"][0]
    taskId = task.pop("taskId")

    print("Decision Task (taskId {}):".format(taskId))
    print(json.dumps(task, indent=4, sort_keys=True))

    if "TASKCLUSTER_PROXY_URL" in os.environ:
        queue = taskcluster.Queue({"rootUrl": os.environ["TASKCLUSTER_PROXY_URL"]})
    else:
        queue = taskcluster.Queue(taskcluster.optionsFromEnvironment())
    queue.createTask(taskId, task)


main()
