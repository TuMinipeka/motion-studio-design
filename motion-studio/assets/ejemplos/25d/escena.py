"""Prueba original de recurso 2.5D: escenario 3D, personaje gráfico, un golpe y reacción.
Generar con scripts/recursos25d.py; componer/exportar con Motion Studio.
No es un rig universal ni una identidad para otros proyectos.
"""
import math
import bpy
from mathutils import Vector

cfg = globals().get('MOTION_CONFIG', {'ancho': 1080, 'alto': 1920})
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x, sc.render.resolution_y = cfg['ancho'], cfg['alto']
sc.view_settings.view_transform = 'Standard'
sc.view_settings.look = 'None'
sc.render.image_settings.color_depth = '8'
sc.world = bpy.data.worlds.new('cielo')
sc.world.color = (0.6, 0.7, 0.8)
try:
    sc.eevee.taa_render_samples = 16
except AttributeError:
    pass


def material(nombre, color, plano=False):
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    n = m.node_tree.nodes; n.clear(); links = m.node_tree.links
    out = n.new('ShaderNodeOutputMaterial')
    emit = n.new('ShaderNodeEmission')
    if plano:
        emit.inputs['Color'].default_value = (*color, 1)
    else:
        dif = n.new('ShaderNodeBsdfDiffuse')
        s2r = n.new('ShaderNodeShaderToRGB')
        ramp = n.new('ShaderNodeValToRGB')
        ramp.color_ramp.interpolation = 'CONSTANT'
        ramp.color_ramp.elements[0].position = 0.25
        ramp.color_ramp.elements[0].color = tuple(c * 0.55 for c in color) + (1,)
        ramp.color_ramp.elements[1].position = 0.55
        ramp.color_ramp.elements[1].color = (*color, 1)
        links.new(dif.outputs[0], s2r.inputs[0]); links.new(s2r.outputs[0], ramp.inputs[0])
        links.new(ramp.outputs[0], emit.inputs[0])
    links.new(emit.outputs[0], out.inputs[0])
    return m


ink = material('tinta', (0.012, 0.020, 0.028), True)
white = material('cara', (0.97, 0.95, 0.86), True)
blue = material('chaqueta', (0.10, 0.37, 0.53))
red = material('lata', (0.85, 0.24, 0.12))
floor = material('suelo', (0.71, 0.78, 0.71))
wood = material('mesa', (0.43, 0.25, 0.13))
green = material('fondo', (0.26, 0.49, 0.40))
steel = material('acero', (0.64, 0.74, 0.75))


def mesh(tipo, nombre, pos, escala, mat, parent=None, contorno=False):
    if tipo == 'sphere':
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, location=pos)
    elif tipo == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(vertices=24, location=pos)
    else:
        bpy.ops.mesh.primitive_cube_add(size=2, location=pos)
    o = bpy.context.object; o.name = nombre; o.scale = escala
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat)
    if parent: o.parent = parent
    if contorno:
        hull = o.copy(); hull.data = o.data.copy(); sc.collection.objects.link(hull)
        hull.name = nombre + '-tinta'; hull.parent = o; hull.location = (0, 0, 0)
        hull.rotation_euler = (0, 0, 0); hull.data.materials.clear(); hull.data.materials.append(ink)
        # Inverted hull: solo se ve el reverso del volumen expandido.
        for v in hull.data.vertices: v.co += v.normal * 0.017
        import bmesh
        bm = bmesh.new(); bm.from_mesh(hull.data); bmesh.ops.reverse_faces(bm, faces=list(bm.faces)); bm.to_mesh(hull.data); bm.free()
        ink.surface_render_method = 'DITHERED'
        ink.use_backface_culling = True
    return o


mesh('cube', 'suelo', (0, 0, -0.12), (12, 12, 0.1), floor)
mesh('cube', 'pared-fondo', (0, 3.0, 2.0), (8, 0.1, 2.2), green)
for x in (-3, -1.8, 0, 1.8, 3):
    mesh('cube', 'marco', (x, 2.84, 2.0), (0.045, 0.06, 2.2), wood)
for x in (-1.25, 1.25):
    mesh('cube', 'pata', (x, 0.35, 0.58), (0.07, 0.24, 0.58), wood)
mesh('cube', 'mesa', (0, 0.35, 1.17), (1.55, 0.58, 0.08), wood)

root = bpy.data.objects.new('actor', None); sc.collection.objects.link(root)
body = mesh('sphere', 'torso', (0, 0, 1.06), (0.25, 0.13, 0.37), blue, root, True)
head = mesh('sphere', 'cabeza', (0, -0.025, 1.64), (0.31, 0.11, 0.31), white, root, True)
for x in (-0.11, 0.11):
    mesh('sphere', 'ojo', (x, -0.136, 1.69), (0.025, 0.018, 0.037), ink, root)
    mesh('cube', 'ceja', (x, -0.144, 1.78), (0.064, 0.011, 0.015), ink, root)
mouth = mesh('sphere', 'boca', (0, -0.144, 1.55), (0.065, 0.014, 0.012), ink, root)
mesh('cylinder', 'gorra', (0, -0.01, 1.93), (0.34, 0.16, 0.065), blue, root, True)
for x in (-0.13, 0.13):
    mesh('cylinder', 'pierna', (x, 0, 0.41), (0.025, 0.025, 0.39), ink, root)
    mesh('sphere', 'pie', (x, -0.075, 0.055), (0.09, 0.14, 0.055), ink, root)
left = mesh('cylinder', 'brazo-izq', (-0.30, -0.04, 1.09), (0.024, 0.024, 0.28), ink, root)
arm = bpy.data.objects.new('brazo-derecho', None); sc.collection.objects.link(arm); arm.parent = root; arm.location = (0.25, 0.47, 1.31)
mesh('cylinder', 'antebrazo', (0.325, 0, 0), (0.025, 0.025, 0.325), ink, arm).rotation_euler[1] = math.pi / 2
mesh('sphere', 'mano', (0.65, 0, 0.05), (0.055, 0.05, 0.055), white, arm, True)
mesh('cylinder', 'mango', (0.65, 0, 0.34), (0.025, 0.025, 0.22), wood, arm)
mesh('cube', 'martillo', (0.65, 0, 0.57), (0.15, 0.07, 0.065), steel, arm, True)
can = mesh('cylinder', 'lata', (0.37, 0.10, 1.53), (0.17, 0.17, 0.27), red, None, True)
mesh('cylinder', 'tapa', (0, 0, 0.28), (0.18, 0.18, 0.025), steel, can)

light = bpy.data.lights.new('sol', 'AREA'); light.energy = 1000; light.shape = 'DISK'; light.size = 5
lamp = bpy.data.objects.new('sol', light); sc.collection.objects.link(lamp); lamp.location = (-3, -4, 7)
lamp.rotation_euler = (Vector((0, 0, 1)) - lamp.location).to_track_quat('-Z', 'Y').to_euler()
camera = bpy.data.objects.new('camara', bpy.data.cameras.new('camara')); sc.collection.objects.link(camera); sc.camera = camera
camera.data.lens = 46


def suave(x):
    x = max(0, min(1, x)); return x * x * (3 - 2 * x)


def seek(t):
    # Siempre restablece la pose; no depende del fotograma anterior.
    sc.frame_set(round(t * 120))
    root.location = (-0.53, -0.37, 0)
    root.rotation_euler = (0, 0, 0)
    root.scale = (1, 1, 1)
    arm.rotation_euler = (0, 0.15, 0)
    mouth.scale = (1, 1, 1)
    can.rotation_euler = (0, 0, 0)
    # Preparación -> martillazo -> lata intacta -> reacción sostenida.
    up = suave((t - 0.6) / 0.8)
    hit = suave((t - 1.9) / 0.18)
    arm.rotation_euler[1] = 0.15 - 1.25 * up + 1.10 * hit
    recoil = max(0, math.sin(min(math.pi, max(0, t - 2.08) * 9)))
    root.rotation_euler[1] = -0.12 * recoil
    root.location.z = 0.025 * recoil
    mouth.scale.z = 1 + 5 * suave((t - 2.15) / 0.25)
    can.rotation_euler[1] = 0.05 * math.sin(max(0, t - 2.08) * 22) * math.exp(-max(0, t - 2.08) * 8) if t >= 2.08 else 0
    # Una cámara acotada mantiene mesa, objeto y reacción en cuadro.
    if t < 1.5:
        camera.location = (0.3, -6.0, 2.5); objetivo = (0, 0.10, 1.32); camera.data.lens = 50
    elif t < 3.3:
        camera.location = (0.2, -4.3, 2.3); objetivo = (-0.05, 0.10, 1.65); camera.data.lens = 48
    else:
        camera.location = (-0.5, -3.2, 1.9); objetivo = (-0.45, -0.15, 1.63); camera.data.lens = 52
    camera.rotation_euler = (Vector(objetivo) - camera.location).to_track_quat('-Z', 'Y').to_euler()


seek(0)
