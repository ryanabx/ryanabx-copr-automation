import subprocess
import json
import requests
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

COPR = "ryanabx/cosmic-epoch"
toplevel_version_url = "https://pagure.io/fedora-cosmic/cosmic-packaging/raw/main/f/latest_tag"
toplevel_version_response = requests.get(url)

TOPLEVEL_VERSION = toplevel_version_response.text
print(f"Toplevel version is {TOPLEVEL_VERSION}")

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
    "Accept": "application/vnd.github.v3+json"  # Use the GitHub API version
}

# First, we list packages in the copr



copr_packages = json.loads(subprocess.run(["copr-cli", "list-packages", "--with-latest-succeeded-build", "--output-format", "json", COPR], capture_output=True, text=True).stdout.strip())


for i in copr_packages:
    # print(i.keys())
    package_name = i["name"]
    if package_name not in repos:
        continue
    # print(i["name"])
    # print(i["latest_succeeded_build"].keys())
    # print(i["latest_succeeded_build"]["source_package"]["version"])
    git_sha = i["latest_succeeded_build"]["source_package"]["version"].rsplit(".", 1)[1].split("-")[0]
    package_toplevel_version = i["latest_succeeded_build"]["source_package"]["version"].split("^", 1)[0]
    # print(git_sha)
    req = requests.get(f"https://api.github.com/repos/pop-os/{repos[package_name]}/commits", headers=headers)
    if req.status_code == 200:
        json_data = req.json()
        git_sha2 = json_data[0]["sha"][0:7]
        if git_sha != git_sha2 or (TOPLEVEL_VERSION != package_toplevel_version and package_name != "pop-launcher"):
            if (git_sha != git_sha2):
                print(f"[PACKAGE: {package_name}] git sha {git_sha} doesn't match newest sha {git_sha2}")
            else:
                pass
                print(f"[PACKAGE: {package_name}] toplevel version {package_toplevel_version} does not match newest version {TOPLEVEL_VERSION}")
            print(f"Will build new version for package {package_name}")
            try:
                subprocess.run(["copr-cli", "build-package", "--name", package_name, COPR], timeout=10)
            except subprocess.TimeoutExpired:
                pass
    else:
        print(f"Error: {req.status_code}, {req.text}")
