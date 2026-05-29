from setuptools import setup

package_name = "voice_task_executor"

setup(
    name=package_name,
    version="1.0.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages",
         ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Berat Atmaca",
    maintainer_email="atmaca1berat@gmail.com",
    description="MoveIt2 voice task executor for UR5e",
    license="MIT",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "voice_task_executor_node = voice_task_executor.voice_task_executor_node:main",
            "voice_safety_checker_node = voice_task_executor.voice_safety_checker_node:main",
            "voice_sequence_executor_node = voice_task_executor.voice_sequence_executor_node:main",
        ],
    },
)
