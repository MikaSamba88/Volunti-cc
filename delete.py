import subprocess
import os
import sys

BRANCH = os.getenv("CI_COMMIT_REF_NAME")
DEFAULT_BRANCH = os.getenv("CI_DEFAULT_BRANCH", "main")

OVERLAY = "K3s/overlays/stage" if BRANCH == DEFAULT_BRANCH else "K3s/overlays/develop"


def run_script(cmd, check=True):
    print(f"$ {' '.join(cmd)}", flush=True)
    result = subprocess.run(cmd, text=True)
    if check and result.returncode != 0:
        sys.exit(result.returncode)
    return result


def main():
    print(f"Deleting environment for branch '{BRANCH}' using overlay '{OVERLAY}'")
    run_script(["kubectl", "delete", "-k", OVERLAY, "--ignore-not-found"])
    print("Completed")


if __name__ == "__main__":
    main()
