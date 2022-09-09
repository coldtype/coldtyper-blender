import bpy, tempfile
from mathutils import Vector
from pathlib import Path

try:
    import coldtype.text as ct
    import coldtype.blender as cb
    import coldtype as C
except ImportError:
    pass

MESH_CACHE_COLLECTION = "Coldtype.MeshCache"

def read_mesh_glyphs_into_cache(font, p, mesh_table):
    if MESH_CACHE_COLLECTION not in bpy.data.collections:
        coll = bpy.data.collections.new(MESH_CACHE_COLLECTION)
        bpy.context.scene.collection.children.link(coll)
    
    mcc = bpy.data.collections[MESH_CACHE_COLLECTION]
    mcc.hide_select = True
    mcc.hide_viewport = True
    mcc.hide_render = True
    
    font_name = font.path.stem

    for x in p:
        key = f"{font_name}.{x.glyphName}"
        
        if key not in bpy.data.objects:
            mg = mesh_table.strikes[1000].glyphs[x.glyphName]

            with tempfile.NamedTemporaryFile("wb", suffix=".glb", delete=False) as glbf:
                glbf.write(mg.meshData)
            
            bpy.ops.import_scene.gltf(filepath=glbf.name)
            Path(glbf.name).unlink()
            
            obj = bpy.context.object
            obj.name = key
            obj.ctxyz.meshOffsetX = mg.originOffsetX
            obj.ctxyz.meshOffsetY = mg.originOffsetY

            mcc.objects.link(obj)

            for c in obj.users_collection:
                if c != mcc:
                    c.objects.unlink(obj)
                
            print(">>> imported mesh:", x.glyphName)


def set_type(data, object=None, parent=None, baking=False, context=None, scene=None, framewise=True, glyphwise=False, shapewise=False, layerwise=False, collection=None, override_use_mesh=None):
    # if ufo, don't cache?

    font = ct.Font.Cacheable(data.font_path)

    try:
        mesh = font.font.ttFont["MESH"]
    except KeyError:
        mesh = None
    
    if override_use_mesh is not None:
        meshing = mesh and override_use_mesh
    else:
        meshing = mesh and data.use_mesh

    collection = collection or "Global"
    using_file = False

    if data.text_mode == "FILE":
        using_file = True
        if data.text_file:
            text_path = Path(data.text_file).expanduser().absolute()
            text = text_path.read_text()
            if data.text_indexed:
                lines = text.split("\n\n")
                try:
                    text = lines[data.text_index-1]
                except IndexError:
                    text = lines[-1]
        else:
            text = "Select file"
        fulltext = text
    elif data.text_mode == "BLOCK":
        using_file = True
        if data.text_block:
            try:
                text = bpy.data.texts[data.text_block].as_string()
                if data.text_indexed:
                    lines = text.split("\n\n")
                    try:
                        text = lines[data.text_index-1]
                    except IndexError:
                        text = lines[-1]
            except KeyError:
                text = "Invalid"
        else:
            text = "Enter block name"
        fulltext = text
    else:
        if data.text == "":
            text = "Text"
        else:
            text = data.text

        lines = text.split("¶")
        fulltext = "\n".join(lines)
        if data.text_indexed:
            try:
                text = lines[data.text_index-1]
            except IndexError:
                text = lines[-1]
        else:
            text = fulltext


    if data.case == "TYPED":
        pass
    elif data.case == "UPPER":
        text = text.upper()
    elif data.case == "LOWER":
        text = text.lower()
    
    features = {}
    for k, v in data.__annotations__.items():
        if k.startswith("fea_"):
            features[k[4:]] = getattr(data, k)

    variations = {}
    for idx, (k, v) in enumerate(font.variations().items()):
        variations[k] = getattr(data, f"fvar_axis{idx+1}")

    if not object or not object.ctxyz.has_keyframes(object):
        p = (ct.StSt(text, font
            , fontSize=3
            , leading=data.leading
            , tu=data.tracking
            , multiline=True
            , **features
            , **variations))
    else:
        def styler(x):
            _vars = {}
            for idx, (k, v) in enumerate(font.variations().items()):
                dp = f"fvar_axis{idx+1}"
                fvar_offset = getattr(data, f"{dp}_offset")
                found = False
                for fcu in object.animation_data.action.fcurves:
                    #print(fcu.data_path, dp)
                    if fcu.data_path.split(".")[-1] == dp:
                        found = True
                        _vars[k] = fcu.evaluate((scene.frame_current - x.i*fvar_offset)%(scene.frame_end+1 - scene.frame_start))
                
                if not found:
                    _vars[k] = getattr(data, dp)

            return ct.Style(font, 3,
                tu=data.tracking,
                **features,
                **_vars)

        p = ct.Glyphwise(text, styler, multiline=True)
        if data.leading:
            p.lead(data.leading)
    
    amb = p.ambit(
        th=not data.use_horizontal_font_metrics,
        tv=not data.use_vertical_font_metrics)

    p.xalign(rect=amb, x=data.align_lines_x, th=not data.use_horizontal_font_metrics)

    ax, ay, aw, ah = p.ambit(
        th=not data.use_horizontal_font_metrics,
        tv=not data.use_vertical_font_metrics)

    p.t(-ax, -ay)

    if data.align_x == "CX":
        p.t(-aw/2, 0)
    elif data.align_x == "E":
        p.t(-aw, 0)
    
    if data.align_y == "CY":
        p.t(0, -ah/2)
    elif data.align_y == "N":
        p.t(0, -ah)

    if meshing:
        p.mapv(lambda g: g.record(C.P(g.ambit(th=1, tv=1))))
    
    p.collapse()

    if meshing:
        read_mesh_glyphs_into_cache(font, p, mesh)
        
        def build_mesh(empty):
            current = {}
            for o in bpy.data.objects:
                if o.parent == empty:
                    idx = int(o.name.split(".")[-1])
                    current[idx] = o

            for idx, x in enumerate(p):
                key = f"{font.path.stem}.{x.glyphName}"
                prototype = bpy.data.objects[key]
                existing = current.get(idx, None)
                
                if existing:
                    mesh_glyph = existing
                else:
                    mesh_glyph = prototype.copy()
                
                mesh_glyph.data = prototype.data.copy()
                mesh_glyph.name = f"{empty.name}.glyph.{idx}"
                mesh_glyph.parent = empty
                mesh_glyph.ctxyz.parent = empty.name

                mesh_glyph.scale = (0.3, 0.3, 0.3)

                amb = x.ambit(th=0, tv=0)
                # 0.003 is b/c of the 3pt fontSize hardcoded above
                mesh_glyph.location = (
                    amb.x + prototype.ctxyz.meshOffsetX*0.003,
                    0, #mesh_glyph.location.y,
                    prototype.ctxyz.meshOffsetY*0.003)

                if existing is None:
                    empty.users_collection[0].objects.link(mesh_glyph)
            
            for idx, o in current.items():
                if idx >= len(p):
                    bpy.data.objects.remove(current[idx], do_unlink=True)
    
    # need to check baking glyphwise?

    if not mesh:
        if data.combine_glyphs and not glyphwise:
            p = p.pen()

        if data.remove_overlap:
            p.remove_overlap()
        
        if data.outline:
            if shapewise:
                p.mapv(lambda _p: _p.explode())
                p.collapse()

            ow = data.outline_weight/100
            if data.outline_outer or ow < 0:
                p_inner = p.copy()
            
            p.outline(data.outline_weight/100, miterLimit=data.outline_miter_limit)
            
            if ow < 0:
                p_inner.difference(p)
                p = p_inner
            elif data.outline_outer:
                p.difference(p_inner)
    
    output = []
    
    if object:
        if baking:
            # converting live text to non-live text

            def export(glyph=None):
                txtObj = (cb.BpyObj.Curve(f"{object.name}Frozen", collection))
                txtObj.obj.data = object.data.copy()
                txtObj.obj.animation_data_clear()
                txtObj.obj.scale = object.scale
                txtObj.obj.location = object.location
                txtObj.obj.rotation_euler = object.rotation_euler

                if glyph:
                    txtObj.draw(glyph, set_origin=False, fill=False)
                    # TODO option to set typographic origins
                else:
                    txtObj.draw(p, set_origin=False, fill=False)

                frame = context.scene.frame_current

                txtObj.obj.ctxyz.baked = True
                txtObj.obj.ctxyz.baked_from = object.name
                txtObj.obj.ctxyz.bake_frame = frame

                txtObj.obj.ctxyz._baked_frame = object

                if framewise:
                    def hide(hidden):
                        txtObj.obj.scale = Vector((0, 0, 0)) if hidden else object.scale
                        txtObj.obj.keyframe_insert(data_path="scale")
                    
                    context.scene.frame_set(frame-1)
                    hide(True)
                    context.scene.frame_set(frame)
                    hide(False)
                    context.scene.frame_set(frame+data.export_every_x_frame-1)
                    hide(False)
                    context.scene.frame_set(frame+data.export_every_x_frame)
                    hide(True)
                    context.scene.frame_set(frame)
                
                txtObj.obj.select_set(True)
                if data.export_meshes:
                    bpy.ops.object.convert(target="MESH")
                    if data.export_apply_transforms:
                        bpy.ops.object.transform_apply(location=0, rotation=1, scale=1, properties=0)
                    if data.export_rigidbody_active:
                        bpy.ops.rigidbody.object_add()
                        txtObj.obj.rigid_body.type = "ACTIVE"
                        #bpy.ops.object.transform_apply(location=0, rotation=1, scale=1, properties=0)
                        pass
                if data.export_geometric_origins:
                    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
                txtObj.obj.select_set(False)
                
                if parent:
                    txtObj.obj.parent = parent
                    #txtObj.obj.ctxyz.parent = parent.name
                
                txtObj.obj.ctxyz.updatable = True
                txtObj.obj.visible_camera = object.visible_camera
                return txtObj
            
            if glyphwise:
                if shapewise:
                    if not data.outline:
                        p.mapv(lambda _p: _p.explode())
                        p.collapse()
                #if layerwise:
                #    p.mapv(lambda _p: _p.explode())
                
                for glyph in p:
                    output.append(export(glyph))
            else:
                output.append(export())
        else:
            # interactive updating of live text

            txtObj = cb.BpyObj()
            txtObj.obj = object
            if meshing:
                build_mesh(object)
            else:
                txtObj.obj = object
                txtObj.draw(p, set_origin=False, fill=False)

                #if data.interpolated:
                #    txtObj.obj.name = "Text.interpolated"

                if data.auto_rename:
                    if using_file:
                        txtObj.obj.name = "Coldtype::File"
                    else:
                        txtObj.obj.name = "Coldtype:" + fulltext[:20]
            
            output.append(txtObj)
    else:
        # initial creation of live text

        if meshing:
            txtObj = (cb.BpyObj.Empty("Coldtype:Text", collection))
            build_mesh(txtObj.obj)
        else:
            txtObj = (cb.BpyObj.Curve("Coldtype:Text", collection))
            txtObj.draw(p, set_origin=False, fill=True)
            txtObj.extrude(0)
            #txtObj.rotate(x=90)
        
        output.append(txtObj)
    
    return output


classes = []
panels = []