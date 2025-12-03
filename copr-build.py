import subprocess
import json
import requests
from urllib.request import urlopen
import os

# Packages::CosmicAppLibrary,
# Packages::CosmicApplets,
# Packages::CosmicBg,
# Packages::CosmicComp,
# Packages::CosmicEdit,
# Packages::CosmicFiles,
# Packages::CosmicGreeter,
# Packages::CosmicIcons,
# Packages::CosmicIdle,
# Packages::CosmicInitialSetup,
# Packages::CosmicLauncher,
# Packages::CosmicNotifications,
# Packages::CosmicOsd,
# Packages::CosmicPanel,
# Packages::CosmicRandr,
# Packages::CosmicScreenshot,
# Packages::CosmicSession,
# Packages::CosmicSettings,
# Packages::CosmicSettingsDaemon,
# Packages::CosmicStore,
# Packages::CosmicTerm,
# Packages::CosmicWorkspaces,
# Packages::PopLauncher,
# Packages::XdgDesktopPortalCosmic,

repos = {
    "cosmic-app-library": "cosmic-applibrary",
    "cosmic-applets": "cosmic-applets",
    "cosmic-bg": "cosmic-bg",
    "cosmic-comp": "cosmic-comp",
    "cosmic-edit": "cosmic-edit",
    "cosmic-files": "cosmic-files",
    "cosmic-greeter": "cosmic-greeter",
    "cosmic-icon-theme": "cosmic-icons",
    "cosmic-idle": "cosmic-idle",
    "cosmic-initial-setup": "cosmic-initial-setup",
    "cosmic-launcher": "cosmic-launcher",
    "cosmic-notifications": "cosmic-notifications",
    "cosmic-osd": "cosmic-osd",
    "cosmic-panel": "cosmic-panel",
    "cosmic-player": "cosmic-player",
    "cosmic-randr": "cosmic-randr",
    "cosmic-screenshot": "cosmic-screenshot",
    "cosmic-session": "cosmic-session",
    "cosmic-settings": "cosmic-settings",
    "cosmic-settings-daemon": "cosmic-settings-daemon",
    "cosmic-store": "cosmic-store",
    "cosmic-term": "cosmic-term",
    "cosmic-wallpapers": "cosmic-wallpapers",
    "cosmic-workspaces": "cosmic-workspaces-epoch",
    "pop-launcher": "launcher",
    "xdg-desktop-portal-cosmic": "xdg-desktop-portal-cosmic",
}


# Get the latest tag from the pop-os repo
def get_latest_tag(package: str) -> str:
    repo_name = repos[package]
    url = f"https://api.github.com/repos/pop-os/{repo_name}/tags"
    with urlopen(url) as response:
        data = json.load(response)
        res: str = data[0]["name"].strip()
        # Return the name with epoch- removed and with `-` replaced with `~`
        return res.split("epoch-", 1)[1].replace("-", "~")


COPR = "ryanabx/cosmic-epoch"
TAGGED_COPR = "ryanabx/cosmic-epoch-tagged"

copr_config = os.environ.get("COPR_AUTH")
if copr_config:
    # Get the path to ~/.config/copr
    config_dir = os.path.expanduser("~/.config")
    config_file = os.path.join(config_dir, "copr")

    # Ensure the .config directory exists
    os.makedirs(config_dir, exist_ok=True)
    # Write content to the file
    with open(config_file, "w") as file:
        file.write(copr_config)

    print(f"Configuration written to {config_file}")

# print(token)
# exit()
token = os.environ.get("PAT_GITHUB")
headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github.v3+json",  # Use the GitHub API version
}


def build_package(package, nightly):
    # print(i.keys())
    package_name = package["name"]
    if package_name not in repos:
        return
    latest_tag = get_latest_tag(package_name)
    # print(package["name"])
    # print(package["latest_succeeded_build"].keys())
    # print(package["latest_succeeded_build"]["source_package"]["version"])
    git_sha = (
        package["latest_succeeded_build"]["source_package"]["version"]
        .rsplit(".", 1)[1]
        .split("-")[0]
    ) if nightly else ""
    package_toplevel_version = package["latest_succeeded_build"]["source_package"][
        "version"
    ]
    # If it's nightly, remove the part of the tag after ^
    # i.e. {version}^git{tag}
    if nightly:
        package_toplevel_version = package_toplevel_version.split("^", 1)[0]
    else:
        package_toplevel_version = package_toplevel_version.rsplit("-", 1)[0]

    if package_toplevel_version == "":
        print(
            f"Error: Could not get package_toplevel_version for package {package_name}"
        )
        return
    print(f"Toplevel version for {package_name}: {latest_tag}")
    # print(git_sha)
    req = requests.get(
        f"https://api.github.com/repos/pop-os/{repos[package_name]}/commits",
        headers=headers,
    )
    if req.status_code == 200:
        json_data = req.json()
        git_sha2 = json_data[0]["sha"][0:7]
        if (nightly and git_sha != git_sha2) or (
            latest_tag != package_toplevel_version and package_name != "pop-launcher"
        ):
            if nightly and git_sha != git_sha2:
                print(
                    f"[PACKAGE: {package_name}] git sha {git_sha} doesn't match newest sha {git_sha2}"
                )
            else:
                pass
                print(
                    f"[PACKAGE: {package_name}] toplevel version {package_toplevel_version} does not match newest version {latest_tag}"
                )
            print(f"Will build new version for package {package_name} Nightly={nightly}")
            try:
                subprocess.run(
                    ["copr-cli", "build-package", "--name", package_name, COPR if nightly else TAGGED_COPR],
                    timeout=10,
                )
            except subprocess.TimeoutExpired:
                pass
    else:
        print(f"Error: {req.status_code}, {req.text}")


# First, we list packages in the coprs
copr_packages = json.loads(
    subprocess.run(
        [
            "copr-cli",
            "list-packages",
            "--with-latest-succeeded-build",
            "--output-format",
            "json",
            COPR,
        ],
        capture_output=True,
        text=True,
    ).stdout.strip()
)

copr_nightly_packages = json.loads(
    subprocess.run(
        [
            "copr-cli",
            "list-packages",
            "--with-latest-succeeded-build",
            "--output-format",
            "json",
            TAGGED_COPR,
        ],
        capture_output=True,
        text=True,
    ).stdout.strip()
)


for i in copr_packages:
    build_package(i, True)

for i in copr_nightly_packages:
    build_package(i, False)
