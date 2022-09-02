import bpy

try:
    import coldtype.text as ct
except ImportError:
    ct = None

from Coldtype import search


class ColdtypeText3DSettingsPanel(bpy.types.Panel):
    bl_label = "3D Settings"
    bl_idname = "COLDTYPE_PT_30_TEXT3DPANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Coldtype"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return bool(search.active_key_object(context))
    
    def draw(self, context):
        ko = search.active_key_object(context)
        layout = self.layout

        row = layout.row()
        row.prop(ko, "rotation_euler", text="Rotation")
        row = layout.row()
        row.prop(ko.data, "extrude", text="Extrude")
        row.prop(ko.data, "bevel_depth", text="Bevel")
        row = layout.row()
        row.prop(ko.data, "fill_mode", text="Fill Mode")
        


class ColdtypeFontVariationsPanel(bpy.types.Panel):
    bl_label = "Font Variations"
    bl_idname = "COLDTYPE_PT_31_FONTVARSPANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Coldtype"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        ko = search.active_key_object(context)
        if ko:
            font = ct.Font.Cacheable(ko.ctxyz.font_path)
            if font.variations():
                return True
        return False
    
    def draw(self, context):
        ko = search.active_key_object(context)
        
        layout = self.layout
        data = ko.ctxyz
        font = ct.Font.Cacheable(data.font_path)
        fvars = font.variations()
    
        for idx, (k, v) in enumerate(fvars.items()):
            layout.row().prop(data, f"fvar_axis{idx+1}", text=k)
    
        if ko.ctxyz.has_keyframes(ko):
            #layout.row().label(text="Variation Offsets")

            for idx, (k, v) in enumerate(fvars.items()):
                layout.row().prop(data, f"fvar_axis{idx+1}_offset", text=f"{k} offset")
        
        row = layout.row()
        row.operator("ctxyz.load_var_axes_defaults", icon="EMPTY_AXIS", text="Set to Defaults")


class ColdtypeFontStylisticSetsPanel(bpy.types.Panel):
    bl_label = "Font Stylistic Sets"
    bl_idname = "COLDTYPE_PT_32_FONTSTYLESPANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Coldtype"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        ko = search.active_key_object(context)
        if ko:
            font = ct.Font.Cacheable(ko.ctxyz.font_path)
            styles = [fea for fea in font.font.featuresGSUB if fea.startswith("ss")]

            if len(styles) > 0:
                return True
        return False
    
    def draw(self, context):
        ko = search.active_key_object(context)
        
        layout = self.layout
        data = ko.ctxyz
        font = ct.Font.Cacheable(data.font_path)

        fi = 0
        row = None

        styles = [fea for fea in font.font.featuresGSUB if fea.startswith("ss")]

        for style in styles:
            if fi%2 == 0 or row is None:
                row = layout.row()
            
            ss_name = font.font.stylisticSetNames.get(style)
            if not ss_name:
                ss_name = "Stylistic Set " + str(int(style[2:]))

            row.prop(data, f"fea_{style}", text=f"{style}: {ss_name}")
            
            fi += 1


class ColdtypeFontFeaturesPanel(bpy.types.Panel):
    bl_label = "Font Features"
    bl_idname = "COLDTYPE_PT_33_FONTFEATURESPANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Coldtype"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return bool(search.active_key_object(context))
    
    def draw(self, context):
        ko = search.active_key_object(context)
        
        layout = self.layout
        data = ko.ctxyz
        font = ct.Font.Cacheable(data.font_path)

        fi = 0
        row = None

        def show_fea(fea):
            nonlocal fi, row
            if fi%4 == 0 or row is None:
                row = layout.row()
            
            row.prop(data, f"fea_{fea}")
            fi += 1
        
        for fea in font.font.featuresGPOS:
            if not hasattr(data, f"fea_{fea}"):
                #print("!", fea)
                pass
            else:
                show_fea(fea)

        for fea in font.font.featuresGSUB:
            if not fea.startswith("cv") and not fea.startswith("ss"):
                if not hasattr(data, f"fea_{fea}"):
                    #print(fea)
                    pass
                else:
                    show_fea(fea)


classes = [
    
]

panels = [
    ColdtypeText3DSettingsPanel,
    ColdtypeFontVariationsPanel,
    ColdtypeFontStylisticSetsPanel,
    ColdtypeFontFeaturesPanel,
]