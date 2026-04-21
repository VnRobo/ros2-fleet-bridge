from setuptools import setup, find_packages
import os
from glob import glob

package_name = "vnrobo_fleet_bridge"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (os.path.join("share", package_name, "launch"), glob("launch/*.py")),
        (os.path.join("share", package_name, "config"), glob("config/*.yaml")),
    ],
    install_requires=["setuptools", "requests"],
    zip_safe=True,
    maintainer="VnRobo",
    maintainer_email="hello@vnrobo.com",
    description="ROS 2 bridge that sends robot telemetry to VnRobo Fleet Monitor",
    license="MIT",
    entry_points={
        "console_scripts": [
            "fleet_bridge = vnrobo_fleet_bridge.fleet_bridge_node:main",
        ],
    },
)
