# -*- coding: utf-8 -*-
from __future__ import print_function

import contextlib
import glob
import os
import sys
from shutil import rmtree

from invoke import task

try:
    input = raw_input
except NameError:
    pass

BASE_FOLDER = os.path.dirname(__file__)


class Log(object):
    def __init__(self, out=sys.stdout, err=sys.stderr):
        self.out = out
        self.err = err

    def flush(self):
        self.out.flush()
        self.err.flush()

    def write(self, message):
        self.flush()
        self.out.write(message + "\n")
        self.out.flush()

    def info(self, message):
        self.write("[INFO] %s" % message)

    def warn(self, message):
        self.write("[WARN] %s" % message)


log = Log()


def confirm(question):
    while True:
        response = input(question).lower().strip()

        if not response or response in ("n", "no"):
            return False

        if response in ("y", "yes"):
            return True

        print("Focus, kid! It is either (y)es or (n)o", file=sys.stderr)


@task(default=True)
def help(ctx):
    """Lists available tasks and usage."""
    ctx.run("invoke --list")
    log.write('Use "invoke -h <taskname>" to get detailed help for a task.')


@task(
    help={
        "docs": "True to clean up generated documentation, otherwise False",
        "bytecode": "True to clean up compiled python files, otherwise False.",
        "builds": "True to clean up build/packaging artifacts, otherwise False.",
    }
)
def clean(ctx, docs=True, bytecode=True, builds=True):
    """Cleans the local copy from compiled artifacts."""

    with chdir(BASE_FOLDER):
        if builds:
            ctx.run("python setup.py clean")

        if bytecode:
            for root, dirs, files in os.walk(BASE_FOLDER):
                for f in files:
                    if f.endswith(".pyc"):
                        os.remove(os.path.join(root, f))
                if ".git" in dirs:
                    dirs.remove(".git")

        folders = []

        if docs:
            folders.append("docs/api/generated")

        folders.append("dist/")

        if bytecode:
            for t in ("src", "tests"):
                folders.extend(glob.glob("{}/**/__pycache__".format(t), recursive=True))

        if builds:
            folders.append("build/")
            folders.append("src/compas_rcf.egg-info/")

        for folder in folders:
            rmtree(os.path.join(BASE_FOLDER, folder), ignore_errors=True)


@task(
    help={
        "rebuild": "True to clean all previously built docs before starting.",
        "doctest": "True to run doctests.",
        "check_links": "True to check all web links in docs for validity.",
    }
)
def docs(ctx, doctest=False, rebuild=True, check_links=False):
    """Builds package's HTML documentation."""

    if rebuild:
        clean(ctx)

    with chdir(BASE_FOLDER):
        if doctest:
            ctx.run("sphinx-build -b doctest docs build/docs")

        ctx.run("sphinx-build -b html docs build/docs")

        if check_links:
            ctx.run("sphinx-build -b linkcheck docs build/docs")


@task()
def check(ctx):
    """Check the consistency of documentation, coding style and a few other things."""

    with chdir(BASE_FOLDER):
        log.write("Checking metadata...")
        ctx.run("python setup.py check --strict --metadata")

        log.write("Running flake8 python linter...")
        ctx.run("flake8 --count --statistics src tests")

        log.write("Checking python imports...")
        ctx.run("isort --check-only --diff --recursive src tests setup.py")


@task(help={"checks": "True to run all checks before testing, otherwise False."})
def test(ctx, checks=False, doctest=False):
    """Run all tests."""
    if checks:
        check(ctx)

    with chdir(BASE_FOLDER):
        cmd = ["pytest"]
        if doctest:
            cmd.append("--doctest-modules")

        ctx.run(" ".join(cmd))


@task
def prepare_changelog(ctx):
    """Prepare changelog for next release."""
    UNRELEASED_CHANGELOG_TEMPLATE = (
        "## Unreleased\n\n### Added\n\n### Changed\n\n### Removed\n\n\n## "
    )

    with chdir(BASE_FOLDER):
        # Preparing changelog for next release
        with open("CHANGELOG.md", "r+") as changelog:
            content = changelog.read()
            changelog.seek(0)
            changelog.write(content.replace("## ", UNRELEASED_CHANGELOG_TEMPLATE, 1))

        ctx.run(
            'git add CHANGELOG.md && git commit -m "Prepare changelog for next release"'
        )


@task
def build(ctx):
    """Build project."""
    ctx.run("python setup.py clean --all sdist bdist_wheel")


@task(help={"new_version": "Version number to release"})
def release(ctx, new_version):
    """Releases the project in one swift command!"""
    # Run checks
    ctx.run("invoke check test build docs")

    # TODO: check if dirty

    # Bump version and git tag it
    ctx.run("git -s tag {}".format(new_version))

    prepare_changelog(ctx)


@contextlib.contextmanager
def chdir(dirname=None):
    current_dir = os.getcwd()
    try:
        if dirname is not None:
            os.chdir(dirname)
        yield
    finally:
        os.chdir(current_dir)
