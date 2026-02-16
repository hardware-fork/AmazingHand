# Maintainer Guide

## Run CI Workflow Locally

From the repository root, run the same steps as CI:

**1. Run pre-commit on PythonExample only**

```bash
pixi run pre-commit run --files $(find PythonExample -type f)
```

**2. Run unit tests**

```bash
pixi run test
```

To run pre-commit on all files (hooks still only process PythonExample per config):

```bash
pixi run pre-commit run --all-files
```

## Optional: Full GitHub Actions Locally

Use [act](https://github.com/nektos/act) (requires Docker) to run the workflow.

Install act (Linux):

```bash
curl -sSf https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
```

The script installs to `./bin/act` in the current directory. To make it available system-wide:

```bash
sudo mv ./bin/act /usr/local/bin/
```

On first run, act prompts for a default image. Choose Medium (~500MB); it works with most actions including setup-pixi.

Use `workflow_dispatch` (the CI workflow skips checkout when running under act and uses your local workspace):

```bash
act workflow_dispatch
```

Or simulate push/PR (may fail with "reference not found" if the branch is not on the remote):

```bash
act push
# or
act pull_request
```


