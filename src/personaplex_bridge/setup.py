from setuptools import setup

package_name = "personaplex_bridge"

setup(
    name=package_name,
    version="1.0.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages",
         ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools", "aiohttp"],
    zip_safe=True,
    maintainer="Berat Atmaca",
    maintainer_email="atmaca1berat@users.noreply.github.com",
    description="PersonaPlex + Qwen3-ASR bridge node for ROS 2",
    license="MIT",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "bridge_node = personaplex_bridge.bridge_node:main",
        ],
    },
)
