import subprocess
import os
import sys

BRANCH = os.getenv("CI_COMMIT_REF_NAME")
DEFAULT_BRANCH = os.getenv("CI_DEFAULT_BRANCH", "main")
REGISTRY = os.getenv("REGISTRY_IMAGE")
TAG = os.getenv("CI_COMMIT_SHORT_SHA")
COMPONENT = sys.argv[1]

OVERLAY = "K3s/overlays/stage" if BRANCH == DEFAULT_BRANCH else "K3s/overlays/develop"
NAMESPACE = "doe25-group-13" if BRANCH == DEFAULT_BRANCH else "doe25-group-13-dev"
DEPLOYMENT = f"deployment/burgundy-volunti-{COMPONENT}"
IMAGE = f"{REGISTRY}/{COMPONENT}:{TAG}"


def run_script(cmd, check=True):
    print(f"$ {' '.join(cmd)}", flush=True)
    result = subprocess.run(cmd, text=True)
    if check and result.returncode != 0:
        sys.exit(result.returncode)
    return result


def main():
    if not REGISTRY or not TAG:
        print("Please set REGISTRY_IMAGE and CI_COMMIT_SHORT_SHA", file=sys.stderr)
        sys.exit(1)

    print(f"Deploying {COMPONENT} from branch '{BRANCH}' using overlay '{OVERLAY}'")

    run_script(["kubectl", "apply", "-k", OVERLAY])

    run_script([
        "kubectl", "set", "image", DEPLOYMENT,
        f"burgundy-volunti-{COMPONENT}={IMAGE}",
        "-n", NAMESPACE,
    ])

    run_script([
        "kubectl", "rollout", "status", DEPLOYMENT,
        "-n", NAMESPACE, "--timeout=120s",
    ])

    print(f"Successfully deployed {COMPONENT}")


if __name__ == "__main__":
    main()
