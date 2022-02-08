bl_info = {
    "name": "Terragen terrains (.ter)",
    "description": "Import .ter files",
    "author": "Walter Perdan, Shankar Sivarajan",
    "version": (0, 0, 2),
    "blender": (3, 0, 0),
    "location": "File > Import-Export",
    "category": "Import-Export"}


import bpy
import struct
import os  # glob

from bpy_extras.io_utils import ImportHelper
from bpy.props import (StringProperty, BoolProperty, EnumProperty,
                       IntProperty, FloatProperty, FloatVectorProperty)
from bpy.types import Operator


import time

def import_ter(operator, context, filepath, custom_properties,
               custom_scale, baseH, heightS):
    
    start_time = time.process_time()

    # variables initialization
    size = 0
    xpts = 0
    ypts = 0
    scalx = 0
    scaly = 0
    scalz = 0
    crad = 0
    crvm = 0
    heightscale = 0
    baseheight = 0

    try:
        ter = open(filepath, 'rb')
        print('start...\n')
    
    except IOError:
        print("Terragen .ter file cannot be imported.")
    
    else:

        if ter.read(8).decode() == "TERRAGEN":

            if ter.read(8).decode() == "TERRAIN ":

                print("Terragen terrain file: found -> continue...\n")
            else:
                print("TERRAIN keyword not found")
                return None
        else:
            print("TERRAGEN keyword not found")
            return None

        keys = ['SIZE', 'XPTS', 'YPTS', 'SCAL', 'CRAD', 'CRVM', 'ALTW']

        totest = ter.read(4).decode()

        while 1:
            if totest in keys:
                if totest == "SIZE":
                    print('reading SIZE')
                    (size,) = struct.unpack('h', ter.read(2))
                    # garbage = ter.read(2).decode()
                    garbage = ter.read(2)
                    print('garbage :', garbage)

                if totest == 'XPTS':
                    print('reading XPTS')
                    (xpts,) = struct.unpack('h', ter.read(2))
                    garbage = ter.read(2).decode()

                if totest == 'YPTS':
                    print('reading YPTS')
                    (ypts,) = struct.unpack('h', ter.read(2))
                    garbage = ter.read(2).decode()

                if totest == 'SCAL':
                    print('reading SCAL')
                    (scalx,) = struct.unpack('f', ter.read(4))
                    (scaly,) = struct.unpack('f', ter.read(4))
                    (scalz,) = struct.unpack('f', ter.read(4))

                if totest == 'CRAD':
                    print('reading CRAD')
                    (crad,) = struct.unpack('f', ter.read(4))

                if totest == 'CRVM':
                    print('reading CRVM')
                    (crvm,) = struct.unpack('H', ter.read(2))
                    garbage = ter.read(2).decode()

                if totest == 'ALTW':
                    print('reading ALTW')
                    (heightscale,) = struct.unpack('h', ter.read(2))
                    (baseheight,) = struct.unpack('h', ter.read(2))
                    break
                totest = ter.read(4).decode()
            else:
                break

        if xpts == 0:
            xpts = size + 1
        if ypts == 0:
            ypts = size + 1

        print('\n-----------------\n')
        print('size is: {0} x {0}'.format(size))
        print('scale is: {0}, {1}, {2}'.format(scalx, scaly, scalz))
        print('number x points are: ', xpts)
        print('number y points are: ', ypts)
        print('baseheight is: ', baseheight)
        print('heightscale is: ', heightscale)
        print('\n-----------------\n')

        # terrainName = bmesh.new()
        
        verts = []
        # Create vertices
        # ---------------
        # read them all...
        x0 = 0.0
        y0 = 0.0
        z0 = 0.0
        
        for y in range(0, ypts):
            for x in range(0, xpts):
                (h,) = struct.unpack('h', ter.read(2))
                # adding custom values
                if custom_properties is True:
                    x0 = x * custom_scale[0]
                    y0 = y * custom_scale[1]
                    baseheight = baseH
                    heightscale = heightS
                    z0 = custom_scale[2] * (baseheight + (h * heightscale / 65536.0))
                else:
                    # from VTP SetFValue(i, j, scale.z * (BaseHeight + ((float)svalue * HeightScale / 65536.0f)));
                    # see: https://github.com/kalwalt/terragen_utils/issues/2
                    x0 = x * scalx
                    y0 = y * scaly
                    z0 = scalz * (baseheight + (h * heightscale / 65536.0))

                verts.append((x0, y0, z0))

        xmax = xpts
        ymax = ypts

        ter.close()

        # Create faces
        # ------------
        faces = []
        
        for y in range(0, ymax - 1):
            for x in range(0, xmax - 1):

                a = x + y * (ymax)

                # terrainName.verts.ensure_lookup_table()

                v1 = verts[a]
                v2 = verts[a + ymax]
                v3 = verts[a + ymax + 1]
                v4 = verts[a + 1]

                # faces.append((v1, v2, v3, v4))

                faces.append((a, a + ymax, a + ymax + 1, a + 1))
        
        name = bpy.path.display_name_from_filepath(filepath)
        
        me = bpy.data.meshes.new(name)
          
        me.from_pydata(verts, [], faces)
          
        ob = bpy.data.objects.new(name, me)
          
        col = bpy.context.collection
        col.objects.link(ob)
        
        print('Terrain imported in %.4f sec.' % (time.process_time() - start_time))

    return {'FINISHED'}

    if __name__ == "__main__":
        register()



class ImportTer(Operator, ImportHelper):
    """Operator to import .ter Terragen files into blender as obj"""
    bl_idname = "import_ter.data"
    bl_label = "Import .ter"
    # bl_options = {'UNDO', 'PRESET'}

    filename_ext = ".ter"

    filter_glob: StringProperty(
        default="*.ter",
        options={'HIDDEN'},
        maxlen=255,)  # Max internal buffer length, longer would be clamped.

    # triangulate: BoolProperty(
    #     name="Triangulate",
    #     description="triangulate the terrain mesh",
    #     default=False)

    custom_properties: BoolProperty(
        name="CustomProperties",
        description="set custom properties of the terrain: size, scale,\
        baseheight, heightscale",
        default=False)

    custom_scale: FloatVectorProperty(
        name="CustomScale",
        description="set a custom scale of the terrain",
        default=(30.0, 30.0, 30.0))

    baseH: IntProperty(
        name="BaseHeight",
        description="set the baseheight of the terrain",
        default=0)

    heightS: IntProperty(
        name="HeightScale",
        description="set the maximum height of the terrain",
        default=100)

    def draw(self, context):
        layout = self.layout
        c = layout.column()
        c.label(text="Import a .ter file:", icon='IMPORT')
        layout.separator()
        # layout.prop(self, 'triangulate')
        layout.prop(self, 'custom_properties')
        if self.custom_properties is True:
            c = layout.column()
            c.prop(self, 'custom_scale', text='Set the scale(x,y,z)', expand=False)
            layout.prop(self, 'baseH')
            layout.prop(self, 'heightS')

    def execute(self, context):
        return import_ter(self, context, self.filepath, # self.triangulate,
                          self.custom_properties, self.custom_scale,
                          self.baseH, self.heightS)





def menu_func_import(self, context):
    self.layout.operator(ImportTer.bl_idname, text="Terragen (.ter)")

def register():
    bpy.utils.register_class(ImportTer)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ImportTer)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register()
