from collections import Callable
from dataclasses import dataclass
from typing import List
from itertools import cycle, product


users = ['pkubik', 'mark', 'keanu', 'jack', 'mgod']
projects = ['nautilus', 'eog', 'gnome', 'gimp']
words = ['super', 'fancy', 'fast', 'neural', 'training']
phases = ['Done', 'Failed', 'Running']
priorities = ['Low', 'Normal', 'High']
nodes = ['citadel', 'dungeon', 'bastion']
suffixes = ['aaaa', 'bbbb', 'cccc']


def create_name(project, user, words_seq):
    return f'{project}.{user}.{"-".join(words_seq)}'


def job_name_generator():
    for project, user, words_seq in zip(cycle(projects), cycle(users), product(words, repeat=3)):
        yield create_name(project, user, words_seq)


@dataclass
class FakePod:
    name: str
    phase: str
    priority: str
    node: str


@dataclass
class FakeJob:
    name: str
    phase: str
    priority: str
    node: str
    directory: str
    pods: List[FakePod]


class FakeKubeCtl:
    def __init__(self):
        self.jobs = {}

        for job_name, priority, phase, node in zip(
                job_name_generator(), cycle(priorities), cycle(phases), cycle(nodes)):
            job = FakeJob(job_name, phase, priority, node, '/tmp', [])
            for suffix in suffixes:
                pod_name = job_name + '-' + suffix
                job.pods.append(FakePod(pod_name, phase, priority, node))
            self.jobs[job_name] = job

    def get_jobs(self):
        return list(self.jobs.values())

    def describe_cmd(self, name: str, filename: str) -> Callable:
        def fn():
            with open(filename, 'wt') as f:
                f.write(f"Fake description for {name}...\n")
                f.write(str(self.jobs[name]))

        return fn

    def kill_cmd(self, name: str) -> Callable:
        def fn():
            self.jobs.pop(name)

        return fn
