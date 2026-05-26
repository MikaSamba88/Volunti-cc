import subprocess
import os
import sys

BRANCH = os.getenv("CI_COMMIT_REF_NAME")
DEFAULT_BRANCH = os.getenv("CI_DEFAULT_BRANCH", "main")
REGISTRY = os.getenv("REGISTRY_IMAGE")
TAG = os.getenv("CI_COMMIT_SHORT_SHA")
COMPONENT = sys.argv[1]

IS_MAIN = BRANCH == DEFAULT_BRANCH
OVERLAY = "K3s/overlays/stage" if IS_MAIN else "K3s/overlays/develop"
NAMESPACE = "doe25-group-13"
PREFIX = "burgundy-" if IS_MAIN else "burgundy-dev-"
DEPLOYMENT = f"deployment/{PREFIX}volunti-{COMPONENT}"
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
        f"volunti-{COMPONENT}={IMAGE}",
        "-n", NAMESPACE,
    ])

    run_script([
        "kubectl", "rollout", "status", DEPLOYMENT,
        "-n", NAMESPACE, "--timeout=120s",
    ])

    print(f"Successfully deployed {COMPONENT}")


if __name__ == "__main__":
    main()
