from cx_Freeze import setup, Executable

build_exe_options = {
    "include_files": [
        ("src", "src")
    ],
    "excludes" :[
        "Pyside6", "cx_Freeze"
    ]
}

setup(
    name="CulturApp",
    version="2.2",
    description="Application de gestion de contenus culturels",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            script="main.py",
            base=None,
            #icon="src/assets/app_icon.ico",
            target_name="CulturApp"
        )
    ]
)
