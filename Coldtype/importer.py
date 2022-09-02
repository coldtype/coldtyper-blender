import importlib, bpy, time, os, sys

# apparently if you require this twice, it'll work the second time (??)
try:
    from ufo2ft.featureCompiler import FeatureCompiler
except ImportError:
    print("-- failed FeatureCompiler --")
    pass

def vt(v):
    return tuple(map(int, (v.split("."))))

REQUIRED_COLDTYPE = "0.9.10"
coldtype_status = 1

try:
    import coldtype as C
    import coldtype.text as ct
    import coldtype.blender as cb

    if vt(C.__version__) < vt(REQUIRED_COLDTYPE):
        C, ct, cb = None, None, None
        coldtype_status = 0

except ImportError:
    C, ct, cb = None, None, None
    coldtype_status = -1


def install_coldtype(context, global_vars, required_version):
    from subprocess import run

    args = [f"coldtype[blender]>={required_version}"]
    
    print("---"*20)
    print("> INSTALLING COLDTYPE")
    print(args)
    print("---"*20)
    time.sleep(1)
    environ_copy = dict(os.environ)
    environ_copy["PYTHONNOUSERSITE"] = "1"
    run([sys.executable, "-m", "pip", "install", *args], check=1, env=environ_copy)
    print("---"*20)
    print("/installed coldtype")

    time.sleep(0.25)
    print("/imported successfully")

    import coldtype as C
    importlib.reload(C)
    print(">>>", C.__version__)


def editor_needs_coldtype(layout, status):
    if status < 0:
        download = "Download & Install Coldtype"
        warning = """This addon requires coldtype
            (coldtype.xyz) as a Python package.
            -
            Clicking the button below will
            download and install Coldtype.
            It should only take a few moments
            to install."""
    else:
        download = "Update Coldtype"
        warning = """This version requires an update
            to the coldtype python package
            -
            Clicking the button below will download
            and install an updated coldtype-python.
            It should only take a few moments."""
    
    for line in warning.splitlines():
        if line.strip() == "-":
            layout.row().separator()
        else:
            row = layout.row()
            row.scale_y = 0.6
            row.label(text=line.strip())
    
    layout.row().separator()
    layout.row().operator("ctxyz.install_coldtype", icon="WORLD_DATA", text=download)


class Coldtype_OT_InstallColdtype(bpy.types.Operator):
    """In order to work properly, Coldtype needs to download and install the Coldtype python package. You can install that package by clicking this button."""

    bl_label = "Coldtype Install Coldtype"
    bl_idname = "ctxyz.install_coldtype"
    
    def execute(self, context):
        install_coldtype(context, globals(), REQUIRED_COLDTYPE)
        bpy.ops.script.reload()
        return {"FINISHED"}


class ColdtypeInstallPanel(bpy.types.Panel):
    bl_label = "Coldtype Install"
    bl_idname = "COLDTYPE_PT_0_INSTALLPANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Coldtype"

    @classmethod
    def poll(cls, context):
        return C is None
    
    def draw(self, context):
        return editor_needs_coldtype(self.layout, coldtype_status)


classes = [
    Coldtype_OT_InstallColdtype,
]

panels = [
    ColdtypeInstallPanel
]