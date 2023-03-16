import os
import math

import bpy
import gpu
from gpu.types import GPUShader
from gpu_extras.batch import batch_for_shader

bl_info = {
    "name": "Bevy Blender Utils",
    "blender": (3, 4, 0),
    "category": "Game Engine",
}


class BBU_PROPERTIES_UL_List(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            column = layout.column()
            row = column.row()
            row.label(text=item.id)

            if item.type == "string":
                text = "\"{}\"".format(item.string)
                row.label(text=text)
            elif item.type == "bool":
                text = "{}".format(item.bool)
                row.label(text=text)
            elif item.type == "integer":
                text = "{}".format(item.integer)
                row.label(text=text)
            elif item.type == "float":
                text = "{:.2f}".format(item.float)
                row.label(text=text)
            elif item.type == "vector3":
                text = "x: {:.2f} y: {:.2f} z: {:.2f}".format(
                    item.vector3_x,
                    item.vector3_y,
                    item.vector3_z,
                )
                row.label(text=text)
            elif item.type == "cuboid":
                text = "x: {:.2f} y: {:.2f} z: {:.2f}".format(
                    item.cuboid_x,
                    item.cuboid_y,
                    item.cuboid_z,
                )
                row.label(text=text)
            elif item.type == "sphere":
                text = "radius: {:.2f}".format(item.radius)
                row.label(text=text)
            elif item.type == "capsule":
                text = "radius: {:.2f} height: {:.2f}".format(item.radius, item.height)
                row.label(text=text)
        elif self.layout_type == "GRID":
            layout.label(text="")


class BBU_PROPERTIES_OT_AddProperty(bpy.types.Operator):
    bl_idname = "bbu_properties.add_property"
    bl_label = "Add new property"

    def execute(self, context):
        properties = context.object.bbu_properties
        properties.add()
        context.object.bbu_properties_index = len(properties) - 1
        return {"FINISHED"}


class BBU_PROPERTIES_OT_RemoveProperty(bpy.types.Operator):
    bl_idname = "bbu_properties.remove_property"
    bl_label = "Remove property"

    @classmethod
    def poll(cls, context):
        return context.object.bbu_properties

    def execute(self, context):
        properties = context.object.bbu_properties
        index = context.object.bbu_properties_index

        properties.remove(index)
        context.object.bbu_properties_index = min(max(0, index - 1), len(properties) - 1)

        return {"FINISHED"}


class BBU_PROPERTIES_OT_MoveProperty(bpy.types.Operator):
    bl_idname = "bbu_properties.move_property"
    bl_label = "Move property"

    direction: bpy.props.EnumProperty(
        items=[
            ("UP", "Up", ""),
            ("DOWN", "Down", ""),
        ],
    )

    @classmethod
    def poll(cls, context):
        return context.object.bbu_properties

    def execute(self, context):
        properties = context.object.bbu_properties
        index = context.object.bbu_properties_index

        neighbour = index + (-1 if self.direction == "UP" else 1)
        properties.move(neighbour, index)

        length = len(properties) - 1
        context.object.bbu_properties_index = max(0, min(neighbour, length))

        return {"FINISHED"}


item_types = [
    ("string", "String", "String"),
    ("bool", "Boolean", "Boolean"),
    ("integer", "Integer", "Integer"),
    ("float", "Float", "Float"),
    ("vector3", "Vector3", "Vector3"),
    ("cuboid", "Cuboid", "Cuboid"),
    ("sphere", "Sphere", "Sphere"),
    ("capsule", "Capsule", "Capsule"),
]

up_vectors = [
    ("zp", "Z+", "Z+"),
    ("yp", "Y+", "Y+"),
    ("xp", "X+", "Z+"),
]

defaults = {
    "id": "unnamed",
    "type": "string",
    "string": "",
    "bool": False,
    "integer": 0,
    "float": 0.0,
    "vector3_x": 0.0,
    "vector3_y": 0.0,
    "vector3_z": 0.0,
    "offset_x": 0.0,
    "offset_y": 0.0,
    "offset_z": 0.0,
    "cuboid_x": 0.5,
    "cuboid_y": 0.5,
    "cuboid_z": 0.5,
    "radius": 0.5,
    "height": 1.0,
    "up_vector": "zp",
}


def del_if_exists(obj, prop):
    if prop in obj:
        del obj[prop]


def update_value(self, _context):
    del_if_exists(self, "string")
    del_if_exists(self, "bool")
    del_if_exists(self, "integer")
    del_if_exists(self, "float")

    del_if_exists(self, "vector3_x")
    del_if_exists(self, "vector3_y")
    del_if_exists(self, "vector3_z")

    del_if_exists(self, "offset_x")
    del_if_exists(self, "offset_y")
    del_if_exists(self, "offset_z")

    del_if_exists(self, "cuboid_x")
    del_if_exists(self, "cuboid_y")
    del_if_exists(self, "cuboid_z")

    del_if_exists(self, "radius")
    del_if_exists(self, "height")


class BBUDataListItem(bpy.types.PropertyGroup):
    id: bpy.props.StringProperty(name="id", default="unnamed")
    type: bpy.props.EnumProperty(items=item_types, default="string", update=update_value)
    string: bpy.props.StringProperty(name="string", default=defaults["string"])
    bool: bpy.props.BoolProperty(name="bool", default=defaults["bool"])
    integer: bpy.props.IntProperty(name="integer", default=defaults["integer"])
    float: bpy.props.FloatProperty(name="float", default=defaults["float"])

    vector3_x: bpy.props.FloatProperty(name="vector3_x", default=defaults["vector3_x"])
    vector3_y: bpy.props.FloatProperty(name="vector3_y", default=defaults["vector3_y"])
    vector3_z: bpy.props.FloatProperty(name="vector3_z", default=defaults["vector3_z"])

    offset_x: bpy.props.FloatProperty(name="offset_x", default=defaults["offset_x"])
    offset_y: bpy.props.FloatProperty(name="offset_y", default=defaults["offset_y"])
    offset_z: bpy.props.FloatProperty(name="offset_z", default=defaults["offset_z"])

    cuboid_x: bpy.props.FloatProperty(name="cuboid_x", default=defaults["cuboid_x"])
    cuboid_y: bpy.props.FloatProperty(name="cuboid_y", default=defaults["cuboid_y"])
    cuboid_z: bpy.props.FloatProperty(name="cuboid_z", default=defaults["cuboid_z"])

    radius: bpy.props.FloatProperty(name="radius", default=defaults["radius"])
    height: bpy.props.FloatProperty(name="height", default=defaults["height"])
    up_vector: bpy.props.EnumProperty(items=up_vectors, default=defaults["up_vector"])


class BBUPanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_bbu_panel"
    bl_label = "Bevy Blender Utils"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    def draw(self, context):
        layout = self.layout
        obj = context.object

        properties = obj.bbu_properties
        index = obj.bbu_properties_index

        row = layout.row()

        row.prop(obj, "bbu_visualization", text="Draw Visualization", toggle=True)
        column = row.column()
        column.prop(obj, "bbu_visualization_show_all", text="Show All", toggle=True)
        column.enabled = obj.bbu_visualization

        row = layout.row()
        row.template_list(
            "BBU_PROPERTIES_UL_List", "Bevy Properties", obj, "bbu_properties", obj, "bbu_properties_index"
        )

        row = layout.row()
        row.operator("bbu_properties.add_property", text="Add Property")
        row.operator("bbu_properties.remove_property", text="Remove Property")

        row = layout.row()
        row.operator("bbu_properties.move_property", text="Move Up").direction = "UP"
        row.operator("bbu_properties.move_property", text="Move Down").direction = "DOWN"

        if index < 0:
            return
        if index >= len(properties):
            return

        item = properties[index]

        layout.separator()

        ids = list(map(lambda x: x.id, properties))

        if len(ids) != len(set(ids)):
            row = layout.row()
            row.label(text="IDs must be unique!")

        row = layout.row()
        row.prop(item, "type", text="Type")
        row.prop(item, "id", text="ID")

        row = layout.row()

        if item.type == "string":
            row.prop(item, "string", text="Value")
        elif item.type == "bool":
            row.prop(item, "bool", text="Value")
        elif item.type == "integer":
            row.prop(item, "integer", text="Value")
        elif item.type == "float":
            row.prop(item, "float", text="Value")
        elif item.type == "vector3":
            row.prop(item, "vector3_x", text="x")
            row.prop(item, "vector3_y", text="y")
            row.prop(item, "vector3_z", text="z")
        elif item.type == "cuboid":
            row.prop(item, "cuboid_x", text="x")
            row.prop(item, "cuboid_y", text="y")
            row.prop(item, "cuboid_z", text="z")
            row = layout.row()
            row.prop(item, "offset_x", text="x")
            row.prop(item, "offset_y", text="y")
            row.prop(item, "offset_z", text="z")
        elif item.type == "sphere":
            row.prop(item, "radius", text="Radius")
            row = layout.row()
            row.prop(item, "offset_x", text="x")
            row.prop(item, "offset_y", text="y")
            row.prop(item, "offset_z", text="z")
        elif item.type == "capsule":
            row.prop(item, "up_vector", text="Up Vector")
            row = layout.row()
            row.prop(item, "radius", text="Radius")
            row.prop(item, "height", text="Height")
            row = layout.row()
            row.prop(item, "offset_x", text="x")
            row.prop(item, "offset_y", text="y")
            row.prop(item, "offset_z", text="z")


classes = (
    BBU_PROPERTIES_UL_List,
    BBU_PROPERTIES_OT_AddProperty,
    BBU_PROPERTIES_OT_RemoveProperty,
    BBU_PROPERTIES_OT_MoveProperty,
    BBUDataListItem,
    BBUPanel,
)


def addon_path():
    return os.path.dirname(os.path.realpath(__file__))


def load_shader(file_name):
    file = open(os.path.join(addon_path(), "shaders", file_name), 'r')
    data = file.read()
    file.close()

    return data


vector3_shader = GPUShader(load_shader("vector3.vert"), load_shader("vector3.frag"))
simple_color = GPUShader(load_shader("simple_color.vert"), load_shader("simple_color.frag"))

draw_handler = None


def draw():
    obj = bpy.context.object
    if obj is None:
        return
    if not hasattr(obj, "bbu_visualization"):
        return
    if not obj.bbu_visualization:
        return
    if not hasattr(obj, "bbu_properties"):
        return

    properties = obj.bbu_properties

    vector3_pos = []
    cuboid_pos = []
    cuboid_indices = []
    sphere_pos = []
    capsule_pos = []

    def parse_item(item):
        if item.type == "vector3":
            vector3_pos.append((item.vector3_x, item.vector3_y, item.vector3_z))
        elif item.type == "cuboid":
            hx = item.cuboid_x
            hy = item.cuboid_y
            hz = item.cuboid_z

            # offsets
            ox = item.offset_x
            oy = item.offset_y
            oz = item.offset_z

            xn = ox - hx
            xp = ox + hx
            yn = oy - hy
            yp = oy + hy
            zn = oz - hz
            zp = oz + hz

            index = len(cuboid_pos)
            cuboid_pos.extend((
                (xn, yn, zn), (xp, yn, zn),
                (xn, yp, zn), (xp, yp, zn),
                (xn, yn, zp), (xp, yn, zp),
                (xn, yp, zp), (xp, yp, zp),
            ))
            cuboid_indices.extend((
                (index + 0, index + 1), (index + 0, index + 2), (index + 1, index + 3), (index + 2, index + 3),
                (index + 4, index + 5), (index + 4, index + 6), (index + 5, index + 7), (index + 6, index + 7),
                (index + 0, index + 4), (index + 1, index + 5), (index + 2, index + 6), (index + 3, index + 7),
            ))
        elif item.type == "sphere":
            radius = item.radius

            # offsets
            ox = item.offset_x
            oy = item.offset_y
            oz = item.offset_z

            segments = 60
            deg = 360.0 / segments

            last_deg = 0
            next_deg = deg
            for _ in range(segments):
                ra = math.radians(last_deg)
                rb = math.radians(next_deg)

                a1 = math.sin(ra) * radius
                a2 = math.cos(ra) * radius
                b1 = math.sin(rb) * radius
                b2 = math.cos(rb) * radius

                sphere_pos.extend((
                    (ox + a1, oy     , oz + a2),
                    (ox + b1, oy     , oz + b2),
                    (ox     , oy + a1, oz + a2),
                    (ox     , oy + b1, oz + b2),
                    (ox + a1, oy + a2, oz     ),
                    (ox + b1, oy + b2, oz     ),
                ))

                last_deg += deg
                next_deg += deg
        elif item.type == "capsule":
            radius = item.radius
            height = item.height * 2.0
            up_direction = item.up_vector

            # offsets
            ox = item.offset_x
            oy = item.offset_y
            oz = item.offset_z

            segments = 60
            deg = 360.0 / segments

            last_deg = 0
            next_deg = deg

            d = height * 0.5 - radius

            for _ in range(segments):
                ra = math.radians(last_deg)
                rb = math.radians(next_deg)

                a1 = math.sin(ra) * radius
                a2 = math.cos(ra) * radius
                b1 = math.sin(rb) * radius
                b2 = math.cos(rb) * radius

                if up_direction == "zp":
                    capsule_pos.extend((
                        (ox + a1, oy + a2, oz + d),
                        (ox + b1, oy + b2, oz + d),
                        (ox + a1, oy + a2, oz - d),
                        (ox + b1, oy + b2, oz - d),
                    ))
                    if last_deg % 90.0 == 0.0:
                        capsule_pos.extend((
                            (ox + a1, oy + a2, oz + d),
                            (ox + a1, oy + a2, oz - d),
                        ))

                    dud = d if last_deg < 180.0 else -d

                    capsule_pos.extend((
                        (ox     , oy + a2, oz + dud + a1),
                        (ox     , oy + b2, oz + dud + b1),
                        (ox + a2, oy     , oz + dud + a1),
                        (ox + b2, oy     , oz + dud + b1),
                    ))
                elif up_direction == "yp":
                    capsule_pos.extend((
                        (ox + a1, oy + d, oz + a2),
                        (ox + b1, oy + d, oz + b2),
                        (ox + a1, oy - d, oz + a2),
                        (ox + b1, oy - d, oz + b2),
                    ))

                    if last_deg % 90.0 == 0.0:
                        capsule_pos.extend((
                            (ox + a1, oy + d, oz + a2),
                            (ox + a1, oy - d, oz + a2),
                        ))

                    dud = d if last_deg < 180.0 else -d

                    capsule_pos.extend((
                        (ox     , oy + dud + a1, oz + a2),
                        (ox     , oy + dud + b1, oz + b2),
                        (ox + a2, oy + dud + a1, oz     ),
                        (ox + b2, oy + dud + b1, oz     ),
                    ))
                elif up_direction == "xp":
                    capsule_pos.extend((
                        (ox + d, oy + a1, oz + a2),
                        (ox + d, oy + b1, oz + b2),
                        (ox - d, oy + a1, oz + a2),
                        (ox - d, oy + b1, oz + b2),
                    ))

                    if last_deg % 90.0 == 0.0:
                        capsule_pos.extend((
                            (ox + d, oy + a1, oz + a2),
                            (ox - d, oy + a1, oz + a2),
                        ))

                    dud = d if last_deg < 180.0 else -d

                    capsule_pos.extend((
                        (ox + dud + a1, oy     , oz + a2),
                        (ox + dud + b1, oy     , oz + b2),
                        (ox + dud + a1, oy + a2, oz     ),
                        (ox + dud + b1, oy + b2, oz     ),
                    ))

                last_deg += deg
                next_deg += deg

    if obj.bbu_visualization_show_all:
        for item in properties:
            parse_item(item)
    else:
        parse_item(properties[obj.bbu_properties_index])

    transform = obj.matrix_world;
    projection = bpy.context.region_data.perspective_matrix

    def draw_vector3():
        if not vector3_pos:
            return

        vector3_shader.uniform_float("transform", transform)
        vector3_shader.uniform_float("projection", projection)
        vector3_shader.uniform_float("color", (0.6, 0.0, 0.8, 1.0))
        batch = batch_for_shader(vector3_shader, "POINTS", {"pos": vector3_pos})
        gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.depth_mask_set(True)
        batch.draw(vector3_shader)
        gpu.state.depth_mask_set(False)

    def draw_cuboid():
        if not cuboid_pos:
            return

        simple_color.uniform_float("transform", transform)
        simple_color.uniform_float("projection", projection)
        simple_color.uniform_float("color", (0.4, 0.4, 0.8, 1.0))
        batch = batch_for_shader(simple_color, "LINES", {"pos": cuboid_pos}, indices=cuboid_indices)
        gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.depth_mask_set(True)
        batch.draw(simple_color)
        gpu.state.depth_mask_set(False)

    def draw_sphere():
        if not sphere_pos:
            return
        simple_color.uniform_float("transform", transform)
        simple_color.uniform_float("projection", projection)
        simple_color.uniform_float("color", (0.8, 0.2, 0.2, 1.0))
        batch = batch_for_shader(simple_color, "LINES", {"pos": sphere_pos})
        gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.depth_mask_set(True)
        batch.draw(simple_color)
        gpu.state.depth_mask_set(False)

    def draw_capsule():
        if not capsule_pos:
            return

        simple_color.uniform_float("transform", transform)
        simple_color.uniform_float("projection", projection)
        simple_color.uniform_float("color", (0.2, 0.8, 0.2, 1.0))
        batch = batch_for_shader(simple_color, "LINES", {"pos": capsule_pos})
        gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.depth_mask_set(True)
        batch.draw(simple_color)
        gpu.state.depth_mask_set(False)

    draw_vector3()
    draw_cuboid()
    draw_sphere()
    draw_capsule()


class glTF2ExportUserExtension:
    def __init__(self):
        from io_scene_gltf2.io.com.gltf2_io_extensions import Extension
        self.Extension = Extension

    def gather_node_hook(self, gltf2_object, _blender_object, _export_settings):
        if gltf2_object.extras is None:
            return
        if "bbu_properties" not in gltf2_object.extras:
            return

        properties = gltf2_object.extras["bbu_properties"]

        parsed = {}

        for item in properties:
            def get_or_default(name):
                return item[name] if name in item else defaults[name]

            def get_or_default_enum(lookup, name):
                return lookup[item[name]][0] if name in item else defaults[name]

            def get_vector(name):
                x = get_or_default("{}_x".format(name))
                y = get_or_default("{}_y".format(name))
                z = get_or_default("{}_z".format(name))

                # convert to bevy coordinate system
                return (x, z, y)

            id = get_or_default("id")

            if id == "":
                continue
            if id in parsed:
                continue

            item_type = get_or_default_enum(item_types, "type")

            if item_type == "string":
                parsed[id] = get_or_default("string")
            elif item_type == "bool":
                parsed[id] = get_or_default("bool")
            elif item_type == "integer":
                parsed[id] = get_or_default("integer")
            elif item_type == "float":
                parsed[id] = get_or_default("float")
            elif item_type == "vector3":
                parsed[id] = get_vector("vector3")
            elif item_type == "cuboid":
                parsed[id] = {
                    "cuboid": get_vector("cuboid"),
                    "offset": get_vector("offset"),
                }
            elif item_type == "sphere":
                parsed[id] = {
                    "radius": get_or_default("radius"),
                    "offset": get_vector("offset"),
                }
            elif item_type == "capsule":
                up_vector = get_or_default_enum("up_vector")
                bevy_up_vector = None

                if up_vector == "xp":
                    bevy_up_vector = (1, 0, 0)
                elif up_vector == "yp":
                    bevy_up_vector = (0, 0, 1)
                elif up_vector == "zp":
                    bevy_up_vector = (0, 1, 0)

                parsed[id] = {
                    "radius": get_or_default("radius"),
                    "height": get_or_default("height"),
                    "offset": get_vector("offset"),
                    "up_vector": bevy_up_vector,
                }

        del_if_exists(gltf2_object.extras, "bbu_properties")
        del_if_exists(gltf2_object.extras, "bbu_properties_index")
        del_if_exists(gltf2_object.extras, "bbu_visualization")
        del_if_exists(gltf2_object.extras, "bbu_visualization_show_all")

        gltf2_object.extras["bbu_object_data"] = parsed


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Object.bbu_properties = bpy.props.CollectionProperty(type=BBUDataListItem)
    bpy.types.Object.bbu_properties_index = bpy.props.IntProperty(name="Property Index", default=0)
    bpy.types.Object.bbu_visualization = bpy.props.BoolProperty(default=True)
    bpy.types.Object.bbu_visualization_show_all = bpy.props.BoolProperty(default=True)

    global draw_handler
    draw_handler = bpy.types.SpaceView3D.draw_handler_add(draw, (), "WINDOW", "POST_VIEW")


def unregister():
    bpy.types.SpaceView3D.draw_handler_remove(draw_handler, "WINDOW")
    del bpy.types.Object.bbu_properties
    del bpy.types.Object.bbu_properties_index
    del bpy.types.Object.bbu_visualization
    del bpy.types.Object.bbu_visualization_show_all

    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)


if __name__ == "__main__":
    register()
