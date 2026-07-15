# Godot 4 `.tscn` Authoring Guide

This guide is a practical, self-contained reference for generating Godot text
scene files (`.tscn`) without opening the Godot editor. It is intended for AI
systems and tools that need to emit scenes with the structure expected by
Godot's text resource loader.

The guide is based on the Godot 4.7 documentation snapshot.

The `.tscn` format is a text representation of one scene tree. It is mostly
human-readable and is suitable for version control. It is not a general
serialization format: every resource type, node type, property name, property
type, and method name must be valid in the target Godot project.

Read [`shared_concepts.md`](shared_concepts.md) for the
shared rules on project-specific facts, typed values, resource ownership,
identifier distinctions, dependencies, and validation. This guide retains the
`.tscn`-specific grammar and local-ID rules.

## 1. Compatibility rules

Use these rules as the default when generating a Godot 4 scene:

1. Start with a `[gd_scene ...]` header.
2. Use `format=3` for Godot 4 scenes.
3. Put sections in this order:
   1. file descriptor
   2. external resources
   3. internal resources
   4. nodes
   5. connections
4. Define every external or internal resource before it is referenced.
5. Define an internal resource before another internal resource that references
   it.
6. Define exactly one root node. The root node must be the first node and must
   not have a `parent` attribute.
7. Use `parent="."` for a node directly below the root. Do not include the
   root node's name in child parent paths.
8. Make every resource reference match an existing resource ID exactly.
9. Omit properties whose values are the engine defaults unless they are needed
   for clarity. Godot removes default-valued properties when saving.
10. Use Godot Variant syntax for property values, not JSON syntax.

A scene can omit optional metadata such as node `unique_id` values. A generated
scene should include them only when it can maintain stable, unique values.

## 2. Minimal valid scene

The smallest useful scene is:

```text
[gd_scene format=3]

[node name="Root" type="Node"]
```

A common modern form gives the scene a string UID:

```text
[gd_scene format=3 uid="uid://cecaux1sm7mo0"]

[node name="Root" type="Node"]
```

The UID must be a valid Godot string-based UID. Do not use a filesystem path as
the UID. If no trustworthy UID generator is available, omit the scene `uid`
rather than inventing a value that may collide with another resource.

When a scene UID is present, scripts and other resources can refer to the scene
with a `uid://...` resource path instead of its filesystem path. This lets
Godot continue resolving the resource after it is moved within the project.
The UID is not the same as a local `id` used by `ExtResource()` or
`SubResource()`.

## 3. File-level grammar

The file consists of headings followed by zero or more property assignments:

```text
[<resource_type> key1=value1 key2=value2 ...]
property_name = value
another/property_name = value
```

The documented heading types are:

- `ext_resource`: a resource stored outside the scene
- `sub_resource`: a resource stored inside the scene
- `node`: a node in the scene tree
- `connection`: a signal connection

The file descriptor is a special heading:

```text
[gd_scene format=3 uid="uid://cecaux1sm7mo0"]
```

Headings use space-separated attributes. Properties below a heading use
`key = value`. Whitespace is not significant outside strings. Extra whitespace
is normally discarded when Godot saves the file.

Single-line comments begin with `;`:

```text
[node name="Root" type="Node"] ; This comment is accepted while loading
```

Comments are discarded when the editor saves the file. Do not rely on comments
as persistent metadata.

## 4. Header and format version

Use:

```text
[gd_scene format=3 uid="uid://..."]
```

Important attributes:

- `format=3`: the Godot 4 scene/resource text format.
- `uid="uid://..."`: the scene's string-based unique identifier.
- `load_steps=<integer>`: found in scenes saved before Godot 4.6; deprecated
  and should not be generated for new files.

Godot 3 scenes use `format=2` and have substantially different serialization
for UIDs, meshes, skeletons, and animations. Do not mix Godot 3 and Godot 4
conventions.

The related `.escn` format has the same text structure, but indicates an
exported scene. Godot compiles an ESCN to a binary SCN in
`.godot/imported/`. Use `.tscn` for ordinary editable scenes.

## 5. Section ordering

The canonical order is:

```text
[gd_scene ...]

[ext_resource ...]
[ext_resource ...]

[sub_resource ...]
[sub_resource ...]

[node ...]
property = value

[connection ...]
```

The loader distinguishes sections by heading type. Keep the documented order
because it makes dependencies clear and matches files produced by Godot.

Do not place a node before a resource it references. Do not place a connection
before the nodes and methods it addresses.

## 6. External resources

An external resource points to a file outside the TSCN. Its heading normally
contains:

- `type`: the Godot resource class
- `uid`: the resource UID, when available
- `path`: the resource path
- `id`: the local reference ID used in this TSCN

Example:

```text
[ext_resource type="Script" path="res://player.gd" id="1_script"]
[ext_resource type="Texture2D" uid="uid://ccbm14ebjmpy1" path="res://gradient.tres" id="2_texture"]
[ext_resource type="PackedScene" path="res://weapon.tscn" id="3_weapon"]
```

Reference an external resource with:

```text
script = ExtResource("1_script")
texture = ExtResource("2_texture")
scene = ExtResource("3_weapon")
```

Rules:

- The `id` is local to this scene and must be unique among external resources.
- The same string can also be used by a sub-resource because external and
  internal references use different namespaces.
- Godot-generated paths are normally project-absolute and begin with `res://`.
- A path relative to the TSCN file is also valid, but `res://` is less
  ambiguous and should be preferred.
- The `type` must agree with the referenced resource.
- The path must exist and contain a loadable resource when the scene is loaded.
- The UID maps the resource to its filesystem location; it is not the local
  `id` used by `ExtResource("...")`.

When a trustworthy UID is available, a script can load the resource by UID:

```gdscript
var scene: PackedScene = load("uid://REPLACE_WITH_PACKED_SCENE_UID")
```

The UID must identify the intended resource in the project. Do not copy an
example UID into a new project or use the UID as the argument to
`ExtResource()`.

For a script attached to a node:

```text
[ext_resource type="Script" path="res://player.gd" id="1_script"]

[node name="Player" type="Node"]
script = ExtResource("1_script")
```

## 7. Internal resources

An internal resource is embedded in the TSCN:

```text
[sub_resource type="CapsuleShape3D" id="CapsuleShape3D_fdxgg"]
radius = 1.0
height = 3.0
```

Reference it with:

```text
shape = SubResource("CapsuleShape3D_fdxgg")
```

Rules:

- Every sub-resource ID must be unique among sub-resources.
- The ID is an arbitrary string, but references must match it exactly.
- A sub-resource has no filesystem `path`.
- A sub-resource may contain ordinary properties and references to other
  resources.
- If sub-resource A refers to sub-resource B, B must be defined before A.
- A sub-resource can refer to an external resource with `ExtResource(...)`.
- A node can refer to a sub-resource with `SubResource(...)`.

Example with a dependency chain:

```text
[sub_resource type="StandardMaterial3D" id="StandardMaterial3D_mat"]
albedo_color = Color(0.2, 0.6, 1, 1)

[sub_resource type="BoxMesh" id="BoxMesh_mesh"]
size = Vector3(2, 1, 2)
material = SubResource("StandardMaterial3D_mat")

[node name="Box" type="MeshInstance3D"]
mesh = SubResource("BoxMesh_mesh")
```

## 8. Nodes and the scene tree

A node heading commonly contains:

```text
[node name="NodeName" type="NodeType" parent="Parent/Path" unique_id=123]
```

Attributes used by the format include:

- `name`: the node name.
- `type`: the node class, usually present except where an inherited/instanced
  structure supplies it.
- `parent`: the path to the parent within this scene, written relative to the
  scene root. It is not a filesystem path and must not include the root name.
- `unique_id`: a node identity used by newer Godot versions to track moved or
  renamed nodes; present in scenes saved with Godot 4.6 or later but optional.
- `instance`: a `PackedScene` external resource used to instance another scene.
- `instance_placeholder`: a placeholder for a scene instance, used by scene
  instantiation/editor workflows to represent a referenced scene without
  loading its complete hierarchy. It is not equivalent to a live instantiated
  node hierarchy.
- `owner`: scene-ownership metadata used to determine which scene owns and
  serializes the node. It is not the same as the node's runtime parent.
- `index`: integer child ordering metadata. It is important when exact order is
  needed, especially alongside inherited or instanced nodes.
- `groups`: an array of group names assigned to the node when the scene is
  instantiated.
- `node_paths`: names of properties exported as Node references but serialized
  as `NodePath` values. This preserves the distinction between a serialized
  path and a runtime node reference.

Examples of optional node metadata:

```text
[node name="Enemy" type="Node3D" parent="." groups=["enemies", "damageable"]]

[node name="Light" type="OmniLight3D" parent="." node_paths=PackedStringArray("follow_node")]
follow_node = NodePath("../Player")
```

`groups` stores names, not node references. `node_paths` lists the property
names whose values are node paths; it does not itself point to the target
nodes. Only include these attributes when the corresponding scene behavior or
serialized property requires them.

The root node:

```text
[node name="Player" type="Node3D"]
```

A direct child:

```text
[node name="Arm" type="Node3D" parent="."]
```

A deeper descendant:

```text
[node name="Hand" type="Node3D" parent="Arm"]
[node name="Finger" type="Node3D" parent="Arm/Hand"]
```

The parent path is relative to the scene root and must not include the root
name. The first node is the only root and must not contain `parent=`.

Node properties follow the heading and continue until the next heading:

```text
[node name="Light" type="OmniLight3D" parent="."]
light_color = Color(1, 0.7, 0.3, 1)
omni_range = 10.0
```

Node ordering matters for the resulting tree and can matter for inherited
nodes. Without an explicit `index`, inherited nodes can take precedence over
ordinary nodes at the same insertion point. Use `index` when the exact child
order must be preserved:

```text
[node name="BoneAttachment" type="BoneAttachment3D" parent="." index="5"]
```

Only use node properties that exist on the specified node type or are provided
by an attached script. A syntactically valid property with the wrong type can
still make the scene fail to load.

## 9. Instanced scenes

A scene can instance another `.tscn` through an external `PackedScene`:

```text
[ext_resource type="PackedScene" path="res://weapon.tscn" id="1_weapon"]

[node name="Weapon" parent="." instance=ExtResource("1_weapon")]
```

The instance resource must be declared before the node. The instance's root
type and default properties come from the referenced scene. Additional
properties on an instance node are valid only when the instanced scene exposes
them in a way Godot can override.

An instanced node is a scene boundary: its children and defaults come from the
referenced `PackedScene`, while properties explicitly serialized on the
instance are overrides. Do not copy the source scene's child nodes into the
instance unless the target workflow intentionally makes those children
editable or uses a separate scene modification mechanism.

For an instance placeholder, preserve the exact form generated by the target
Godot version. A placeholder represents the referenced scene without loading
its complete node hierarchy, so it must not be treated as a normal node with
the source scene's child paths available.

Prefer an instance over copying a large scene tree when the source scene is
intended to be reusable.

## 10. NodePath values

A NodePath is serialized as:

```text
NodePath("path/to/node")
```

Paths are relative to the node containing the property:

- `NodePath(".")`: the current node.
- `NodePath("")`: no node.
- `NodePath("..")`: the parent node.
- `NodePath("Child/SubChild")`: a descendant.
- `NodePath("OtherNode:property")`: a node property.
- `NodePath("MeshInstance3D:scale.x")`: one component of a property.

Example:

```text
[node name="Mesh" type="MeshInstance3D" parent="Armature01"]
skeleton = NodePath("..")
```

Do not confuse these two concepts:

- A node heading's `parent="Arm/Hand"` locates the node in the scene tree.
- A property value `NodePath("Arm/Hand")` points to another node from the
  current node.

## 11. Variant value serialization

Property values use Godot's text Variant syntax. Common forms include:

```text
enabled = true
count = 3
ratio = 0.5
label = "Hello"
color = Color(1, 0.5, 0.25, 1)
position = Vector2(10, 20)
position_3d = Vector3(1, 2, 3)
rotation = Quaternion(0, 0, 0, 1)
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 1, 2, 3)
path = NodePath("Player")
items = ["one", "two"]
settings = {"mode": 1, "enabled": true}
names = PackedStringArray("A", "B")
values = PackedFloat32Array(0, 1, 2)
resource = ExtResource("1_resource")
embedded = SubResource("MyResource_id")
```

Use the exact Variant type expected by the property. In particular:

- `Vector3` is not interchangeable with `Vector2`.
- `Quaternion` is not interchangeable with Euler angles.
- `NodePath("...")` is not the same as the string `"..."`.
- `PackedFloat32Array(...)` is not the same as a normal array.
- Resource references must use `ExtResource(...)` or `SubResource(...)`, not
  their IDs as bare strings.
- Dictionary keys and string values must use valid quoted strings where
  required.

Property names may contain `/`, as in:

```text
surface_material_override/0 = SubResource("StandardMaterial3D_mat")
```

## 12. Common scene construction pattern

This is a complete small 3D scene with internal resources:

```text
[gd_scene format=3 uid="uid://c4mpleball00001"]

[sub_resource type="SphereShape3D" id="SphereShape3D_shape"]

[sub_resource type="SphereMesh" id="SphereMesh_mesh"]

[sub_resource type="StandardMaterial3D" id="StandardMaterial3D_material"]
albedo_color = Color(1, 0.639216, 0.309804, 1)

[node name="Ball" type="RigidBody3D"]

[node name="CollisionShape3D" type="CollisionShape3D" parent="."]
shape = SubResource("SphereShape3D_shape")

[node name="MeshInstance3D" type="MeshInstance3D" parent="."]
mesh = SubResource("SphereMesh_mesh")
surface_material_override/0 = SubResource("StandardMaterial3D_material")

[node name="OmniLight3D" type="OmniLight3D" parent="."]
light_color = Color(1, 0.698039, 0.321569, 1)
omni_range = 10.0

[node name="Camera3D" type="Camera3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 0.939693, 0.34202, 0, -0.34202, 0.939693, 0, 1, 3)
```

The important relationships are:

- the shape exists before the collision node references it;
- the mesh and material exist before the mesh node references them;
- all child nodes use `parent="."`;
- properties use typed Variant values.

## 13. Skeleton3D data

A `Skeleton3D` node can store bone pose data using property names of the form:

```text
bones/<bone_id>/<attribute> = value
```

Supported attributes documented for this format are:

- `position`: `Vector3`
- `rotation`: `Quaternion`
- `scale`: `Vector3`

Each attribute is optional:

```text
[node name="Skeleton3D" type="Skeleton3D" parent="."]
bones/1/position = Vector3(0.114471, 2.19771, -0.197845)
bones/1/rotation = Quaternion(0.191422, -0.0471201, -0.00831942, 0.980341)
bones/2/position = Vector3(-2.59096e-05, 0.236002, 0.000347473)
bones/2/rotation = Quaternion(-0.0580488, 0.0310587, -0.0085914, 0.997794)
bones/2/scale = Vector3(0.9276, 0.9276, 0.9276)
```

The numeric bone ID is the skeleton's bone index, not an arbitrary resource
ID. Do not emit bone entries unless the target skeleton has corresponding bone
indices.

## 14. BoneAttachment3D

`BoneAttachment3D` is an intermediate node for attaching another node to one
bone of a skeleton. It normally contains:

- `bone_name`: the skeleton bone name.
- `bone_idx`: the matching bone index.

Example:

```text
[node name="GunBone" type="BoneAttachment3D" parent="Skeleton3D" index="5"]
transform = Transform3D(0.333531, 0.128981, -0.933896, 0.567174, 0.763886, 0.308015, 0.753209, -0.632331, 0.181604, -0.323915, 1.07098, 0.0497144)
bone_name = "hand.R"
bone_idx = 55

[node name="ShootFrom" type="Marker3D" parent="Skeleton3D/GunBone"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0.4, 0)
```

Keep `bone_name` and `bone_idx` consistent with the target Skeleton3D.

## 15. AnimationPlayer and animation resources

An `AnimationPlayer` uses one or more `AnimationLibrary` resources. An
animation library maps animation names to `Animation` sub-resources.

If the library name is empty, its animations can be played directly by name:

```text
autoplay = "scale_down"
libraries = {
"": SubResource("AnimationLibrary_library")
}
```

For a named library, playback uses:

```text
library_name/animation_name
```

An animation resource commonly contains:

```text
[sub_resource type="Animation" id="Animation_scale"]
resource_name = "scale_down"
length = 1.5
loop_mode = 2
step = 0.05
```

Animation properties:

- `length`: duration in seconds. Keys may exist outside `[0, length]`.
- `loop_mode`: `0` no loop, `1` wrap-around loop, `2` clamped loop.
- `step`: editor step size; it does not change playback.

The library:

```text
[sub_resource type="AnimationLibrary" id="AnimationLibrary_library"]
_data = {
"scale_down": SubResource("Animation_scale")
}
```

The `_data` dictionary maps animation names to `Animation` resources.

### 15.1 Animation track fields

Tracks use indexed properties:

```text
tracks/<track_id>/<attribute> = value
```

Documented track types:

- `value`: generic property track
- `position_3d`: optimized 3D position track
- `rotation_3d`: optimized 3D rotation track
- `scale_3d`: optimized 3D scale track
- `blend_shape`: optimized blend-shape track
- `method`: method-call track
- `bezier`: Bezier track
- `audio`: audio playback track
- `animation`: track that plays another animation

Common fields:

- `type`: track type.
- `imported`: `true` for imported tracks, otherwise normally `false`.
- `enabled`: whether the track is active.
- `path`: `NodePath` to the target. Generic value tracks normally include a
  property suffix such as `NodePath("Box:scale")`; optimized 3D tracks target
  the node itself, such as `NodePath("Box")`.
- `interp`: interpolation mode: `0` nearest, `1` linear, `2` cubic,
  `3` linear angle, `4` cubic angle.
- `loop_wrap`: whether the track wraps while looping.
- `keys`: track-specific key data.

Generic value track:

```text
tracks/0/type = "value"
tracks/0/imported = false
tracks/0/enabled = true
tracks/0/path = NodePath("Box:scale")
tracks/0/interp = 1
tracks/0/loop_wrap = true
tracks/0/keys = {
"times": PackedFloat32Array(0, 1),
"transitions": PackedFloat32Array(1, 1),
"update": 0,
"values": [Vector3(1, 1, 1), Vector3(0, 0, 0)]
}
```

For generic value tracks:

- `times` is a `PackedFloat32Array` of key times.
- `transitions` is a `PackedFloat32Array` of easing values.
- `update=0` means continuous.
- `update=1` means discrete.
- `update=2` means capture.
- `values` contains one Variant value for each key time.

The arrays must have compatible lengths, and every value must be compatible
with the animated property.

### 15.2 Optimized 3D tracks

Godot 4 uses separate position, rotation, and scale tracks instead of the
Godot 3 transform track. These tracks use a packed float array:

```text
tracks/<id>/keys = PackedFloat32Array(...)
```

Position and scale key layout:

```text
T, E, X, Y, Z,   T, E, X, Y, Z, ...
```

Rotation key layout:

```text
T, E, X, Y, Z, W,   T, E, X, Y, Z, W, ...
```

Here `T` is time, `E` is the transition value (currently normally `1`), and
the remaining values are the Vector3 or Quaternion components.

Example:

```text
tracks/0/type = "position_3d"
tracks/0/imported = false
tracks/0/enabled = true
tracks/0/path = NodePath("Box")
tracks/0/interp = 1
tracks/0/loop_wrap = true
tracks/0/keys = PackedFloat32Array(0, 1, 0, 0, 0, 1.5, 1, 1.5, 1, 0)

tracks/1/type = "rotation_3d"
tracks/1/imported = false
tracks/1/enabled = true
tracks/1/path = NodePath("Box")
tracks/1/interp = 1
tracks/1/loop_wrap = true
tracks/1/keys = PackedFloat32Array(0, 1, 0.211, -0.047, 0.211, 0.953, 1.5, 1, 0.005, 0.976, -0.216, 0.022)
```

Optimized 3D tracks use linear key behavior and do not support custom easing
values. The track interpolation mode can still request nearest or cubic
interpolation for the track.

## 16. ArrayMesh serialization

An `ArrayMesh` stores surfaces in the `_surfaces` array. Each surface is a
dictionary. The documented surface keys are:

- `aabb`: computed axis-aligned bounding box.
- `attribute_data`: packed vertex attributes such as normals, tangents,
  colors, UV1, UV2, and custom vertex data.
- `bone_aabbs`: per-bone axis-aligned bounding boxes.
- `format`: surface buffer format.
- `index_count`: number of indices; must match `index_data`.
- `index_data`: indices selecting vertices from `vertex_data`.
- `lods`: pairs of screen-space percentage and packed index data.
- `material`: material used by the surface.
- `name`: surface name.
- `primitive`: primitive type:
  `0` points, `1` lines, `2` line strip, `3` triangles, `4` triangle strip.
- `skin_data`: bone weights.
- `vertex_count`: vertex count; must match `vertex_data`.
- `vertex_data`: packed vertex positions.

The structure is large and normally generated by an importer. Do not hand-write
the packed byte arrays unless the exact mesh data and format are known:

```text
[sub_resource type="ArrayMesh" id="ArrayMesh_mesh"]
resource_name = "mesh"
_surfaces = [{
"aabb": AABB(0, 0, 0, 1, 1, 1),
"attribute_data": PackedByteArray(...),
"bone_aabbs": [],
"format": 0,
"index_count": 0,
"index_data": PackedByteArray(...),
"lods": [],
"material": SubResource("StandardMaterial3D_material"),
"name": "surface",
"primitive": 3,
"skin_data": PackedByteArray(...),
"vertex_count": 0,
"vertex_data": PackedByteArray(...)
}]
blend_shape_mode = 0
```

The ellipsis above is explanatory notation, not valid TSCN syntax. Every
packed array must contain real data in an actual file.

## 17. Connections

Connections are the final section of a scene. The common form is:

```text
[connection signal="signal_name" from="Emitter/Path" to="Receiver/Path" method="_on_signal_name"]
```

Example:

```text
[connection signal="body_entered" from="Area3D" to="." method="_on_area_body_entered"]
```

The referenced signal must exist on the `from` node, the receiver path must
resolve, and the method must exist on the receiver script or supported object.
Keep connection headings after all nodes.

Additional connection attributes may be emitted by Godot for advanced signal
bindings, such as bound arguments or flags. Preserve their exact Variant types
when reproducing an editor-generated connection.

## 18. High-confidence generation workflow

Use this sequence when creating a scene from scratch:

1. Identify the target Godot major version. This guide targets Godot 4.
2. Decide the root node and complete tree before writing properties.
3. List every external resource and assign stable local IDs.
4. List every internal resource and topologically sort dependencies.
5. Write the header and resource headings.
6. Write sub-resource properties using the exact property types.
7. Write the root node with no `parent`.
8. Write child nodes in tree order with correct parent paths.
9. Add node properties and resource references.
10. Add signal connections last.
11. Check every path, ID, property name, resource type, and Variant type.
12. Omit defaults and optional metadata that cannot be generated reliably.

When converting an existing scene, the safest method is to save a minimal
example in Godot and copy its serialization patterns. The format is stable,
but node and resource properties are defined by the engine classes and project
scripts, not by the TSCN container alone.

## 19. Validation checklist

Before emitting a `.tscn`, verify:

The common project, type, identifier, ownership, dependency, and validation
checklist in `shared_concepts.md` also applies.

### File structure

- The first heading is `[gd_scene ...]`.
- `format=3` is used for Godot 4.
- Sections are ordered as header, external resources, sub-resources, nodes,
  and connections.
- There is exactly one root node.
- The root is the first node and has no `parent`.
- No deprecated `load_steps` attribute was added to a new scene.

### IDs and references

- Every `ExtResource("id")` has one matching `ext_resource id="id"`.
- Every `SubResource("id")` has one matching `sub_resource id="id"`.
- Internal resource dependencies appear before their users.
- Resource IDs do not contain accidental whitespace or mismatched casing.
- External paths use the intended project location and resource type.

### Scene tree

- Every non-root node has a valid parent path.
- Direct children use `parent="."`.
- Parent paths omit the root name.
- Node names are valid and unique among siblings.
- `instance` references a `PackedScene`.
- `unique_id` values, when included, are stable and not duplicated.

### Properties

- Every property exists on the node/resource type.
- Every value has the property's exact Variant type.
- `NodePath(...)` is used for node paths.
- `Transform3D`, `Quaternion`, and packed arrays have the correct number and
  order of components.
- Arrays and dictionaries have valid delimiters and compatible contents.
- Default values are not emitted unnecessarily.

### Animations, skeletons, and signals

- Animation track paths resolve from the animation player.
- Generic track arrays have matching lengths.
- Optimized 3D track arrays follow their documented element stride.
- Skeleton bone indices match the actual skeleton.
- `bone_name` and `bone_idx` agree.
- Connections refer to existing nodes, signals, and methods.

## 20. Failure patterns to avoid

Do not:

- use JSON objects such as `{"x": 1}` where Godot expects a typed Variant;
- use `ExtResource("res://file.tres")`; the argument is the local resource ID;
- use `SubResource("res://file.tres")`; sub-resources have no path;
- define a sub-resource after a sub-resource that references it;
- put `parent="Root"` on a child of the root;
- give the root a `parent` attribute;
- reference a node with a filesystem path instead of `NodePath(...)`;
- use a Godot 3 `format=2` scene with Godot 4 serialization;
- use `...` as a placeholder in a real packed array;
- invent node properties from their names without checking the target class;
- assume a script method or signal exists merely because its name looks valid;
- rely on comments or whitespace for behavior;
- assume a generated scene is valid merely because its text parses.

Parsing and semantic loading are different checks. A scene can have valid
brackets and headings but still fail because a class, resource, property,
method, path, UID, or value is invalid for the target project.

## 21. Canonical generation template

Use this as a starting point and remove sections that are not needed:

```text
[gd_scene format=3 uid="uid://REPLACE_WITH_VALID_SCENE_UID"]

; External resources
[ext_resource type="Script" path="res://REPLACE_WITH_SCRIPT.gd" id="1_script"]
[ext_resource type="PackedScene" path="res://REPLACE_WITH_SCENE.tscn" id="2_scene"]

; Internal resources. Dependencies must come first.
[sub_resource type="StandardMaterial3D" id="StandardMaterial3D_material"]
albedo_color = Color(1, 1, 1, 1)

[sub_resource type="BoxMesh" id="BoxMesh_mesh"]
material = SubResource("StandardMaterial3D_material")

; Root node: no parent attribute.
[node name="Root" type="Node3D"]
script = ExtResource("1_script")

; Child nodes: parent paths omit the root name.
[node name="Mesh" type="MeshInstance3D" parent="."]
mesh = SubResource("BoxMesh_mesh")

[node name="Instance" parent="." instance=ExtResource("2_scene")]

; Connections must be last.
; [connection signal="signal_name" from="Emitter" to="." method="_on_signal_name"]
```

Replace every placeholder. The commented connection is not active until it is
turned into a real heading with valid node, signal, and method names.

## 22. Source authority and limits

This guide describes the TSCN container and the specialized structures covered
by the Godot file-format documentation. It does not define every property of
every Godot node or resource. Those properties are documented by the class
reference and by the project itself, including custom scripts.

When a generated scene uses a property not shown here:

1. Confirm the target class and inheritance chain.
2. Confirm the exact property name and Variant type.
3. Inspect a Godot-generated scene or resource containing that property.
4. Preserve the generated value shape and ordering.

The authoritative loader is Godot's `ResourceFormatLoaderText`. If this guide
conflicts with a scene generated by the target Godot version, prefer the
target-version output and update the guide with a minimal reproducible example.
