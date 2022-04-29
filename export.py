import cx_Freeze

executables = [cx_Freeze.Executable("main.py")]

cx_Freeze.setup(
    name="Gob",
    options={"build_exe": {"packages":["pygame"],
                           "include_files":["Assets", "sword_attack.py"]}},
    executables = executables

    )

"""This file can be used to export the pygame script into a .exe file.
Instructions for use:
    1. If you haven't already on this device, open the command terminal and execute this command: "py -m pip install cx-Freeze"
    2. Make sure the build folder is empty to prevent confusion with previous builds.
    3. Navigate the command terminal to this directory, then execute this command: "python export.py build"
    4. VOILA! The executable will be inside the build folder.
Along the way, if you add any files/folders into the same directory as these python scripts, you will need to add their names to the array in Line 8 of this script so that they are included with the executable.
    (Don't worry about the git-related files, the build folder, or files added into the Assets folder.)
Otherwise, we shouldn't have to make any other changes to this script. If something goes wrong, let me know. Enjoy!

 - Joshua"""
