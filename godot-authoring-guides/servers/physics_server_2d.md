# PhysicsServer2D Authoring Guide (Godot 4.7)

This guide explains how to create and control 2D physics objects directly through
`PhysicsServer2D`, without creating `Node2D`, `Area2D`, `RigidBody2D`, or other
scene-tree nodes. It is intended for AI-generated GDScript and for systems that
need server-owned physics objects, custom synchronization, or large numbers of
objects.

For ordinary gameplay, use the node-level APIs described by the shared physics,
2D physics, and 2D-specific guides. `PhysicsServer2D` is a low-level API: it
uses opaque `RID` handles, does not provide scene-tree ownership, and requires
manual lifetime management.

Read [`../shared_concepts.md`](../shared_concepts.md) for
the shared rules on project assumptions, typed values, RID ownership, resource
lifetime, timing, coordinate spaces, and validation.

## 1. What the server represents

`PhysicsServer2D` is the global Godot server responsible for 2D physics spaces,
shapes, areas, bodies, and joints. Nodes such as `RigidBody2D` and `Area2D` are
higher-level wrappers around equivalent server objects.

A server-created object:

- can exist without a scene-tree node;
- is identified by an opaque `RID`, not by a script object reference;
- must be assigned to a `PhysicsServer2D` space before it participates in that
  space's simulation;
- must be explicitly destroyed with `PhysicsServer2D.free_rid(rid)`;
- does not automatically create visual output;
- does not automatically synchronize a `Node2D`, `CanvasItem`, or custom
  renderer object.

The server is appropriate for node-independent simulations, custom physics
wrappers, procedural object pools, and performance-sensitive systems. It is not
automatically faster: every required feature, callback, visual synchronization
step, and cleanup path becomes the caller's responsibility.

## 2. RIDs and ownership

The shared concepts guide defines the general RID and ownership contract.
For this server, obtain an RID only from a `PhysicsServer2D` creation method or
from a valid physics-world resource; never construct or inspect it as ordinary
data.

Typical creation methods include:

```gdscript
var space: RID = PhysicsServer2D.space_create()
var shape: RID = PhysicsServer2D.rectangle_shape_create()
var body: RID = PhysicsServer2D.body_create()
var area: RID = PhysicsServer2D.area_create()
var joint: RID = PhysicsServer2D.joint_create()
```

Keep strong references to any `Shape2D` or other reference-counted resource
whose RID is used by the server. A RID does not keep the originating resource
alive. For server-created primitive shapes, keep the RID in a member variable
until all bodies and areas have stopped using it.

Free dependents before dependencies:

```gdscript
PhysicsServer2D.free_rid(joint)
PhysicsServer2D.free_rid(body)
PhysicsServer2D.free_rid(area)
PhysicsServer2D.free_rid(shape)
PhysicsServer2D.free_rid(space)
```

Only free `space` when it was created by your system with `space_create()`.
Never free `get_world_2d().space`; the world owns it.

Do not free a RID twice. Clear callbacks before freeing the object when the
callback's target or userdata may outlive the physics object. Never use a RID
after its owner has been freed.

## 3. Spaces and timing

Create an independent space with `space_create()`, or use the current world's
space:

```gdscript
var space: RID = get_world_2d().space
```

Configure a space with:

- `space_set_active(space, active)` to enable or disable simulation;
- `space_is_active(space)` to query activation;
- `space_set_param(space, param, value)` and `space_get_param(space, param)`
  for solver settings;
- `space_get_direct_state(space)` to access `PhysicsDirectSpaceState2D`.

The `SpaceParameter` values are:

| Constant | Meaning |
|---|---|
| `SPACE_PARAM_CONTACT_RECYCLE_RADIUS` | Motion distance after which contact status is recalculated. |
| `SPACE_PARAM_CONTACT_MAX_SEPARATION` | Maximum separation before a contact is discarded. |
| `SPACE_PARAM_CONTACT_MAX_ALLOWED_PENETRATION` | Penetration tolerated before it is treated as a collision. |
| `SPACE_PARAM_CONTACT_DEFAULT_BIAS` | Default contact depenetration bias. |
| `SPACE_PARAM_BODY_LINEAR_VELOCITY_SLEEP_THRESHOLD` | Linear speed below which a body can become inactive. |
| `SPACE_PARAM_BODY_ANGULAR_VELOCITY_SLEEP_THRESHOLD` | Angular speed below which a body can become inactive. |
| `SPACE_PARAM_BODY_TIME_TO_SLEEP` | Time an inactive body must remain inactive before sleeping. |
| `SPACE_PARAM_CONSTRAINT_DEFAULT_BIAS` | Default constraint correction bias. |
| `SPACE_PARAM_SOLVER_ITERATIONS` | Number of solver iterations for contacts and constraints. |

Server state changes are synchronized with physics processing. Follow the
shared timing rules and perform simulation work during `_physics_process()` or
documented direct-state callbacks. Avoid render-frame polling of getters that
can synchronize the physics server.

## 4. Shapes

Create shapes with these methods:

| Method | Shape and `shape_set_data()` payload |
|---|---|
| `world_boundary_shape_create()` | Infinite line with an origin and normal, represented by the shape's boundary data. |
| `separation_ray_shape_create()` | Separation ray; data describes ray length and whether it slides. |
| `segment_shape_create()` | Finite line from point A to point B, normally represented by `PackedVector2Array([a, b])`. |
| `circle_shape_create()` | Radius as a `float`. |
| `rectangle_shape_create()` | Half-extents as `Vector2` (half-width, half-height). |
| `capsule_shape_create()` | Capsule radius and height data as documented by the shape type. |
| `convex_polygon_shape_create()` | Convex point data, normally a `PackedVector2Array`. |
| `concave_polygon_shape_create()` | Segment-based polygon point data, normally a `PackedVector2Array`. |

The exact data structure for less common shapes must match the corresponding
shape resource (`CapsuleShape2D`, `ConvexPolygonShape2D`,
`ConcavePolygonShape2D`, and so on). Do not infer a dictionary schema merely
from the method name. When possible, create the matching `Shape2D` resource and
use its `get_rid()` instead.

Common shape methods:

- `shape_set_data(shape, data)` replaces the shape geometry.
- `shape_get_data(shape)` retrieves the stored shape data.
- `shape_get_type(shape)` returns a `ShapeType`.
- `body_add_shape()` and `area_add_shape()` attach a shape with a local
  `Transform2D`.
- `body_set_shape_transform()` and `area_set_shape_transform()` change one
  attached shape's local transform.
- `body_set_shape_disabled()` and `area_set_shape_disabled()` disable one
  attached shape without removing it.
- `body_remove_shape()` and `area_remove_shape()` remove an attached shape by
  index.
- `body_clear_shapes()` and `area_clear_shapes()` remove all attached shapes.

`ShapeType` identifies world boundaries, separation rays, segments, circles,
rectangles, capsules, convex polygons, concave polygons, and the internal
`SHAPE_CUSTOM` type. `SHAPE_CUSTOM` cannot be created by user code.

Prefer primitive convex shapes for dynamic bodies. Concave polygon shapes are
primarily for static collision geometry and are not a substitute for a
compound dynamic collider.

## 5. Creating and configuring a body

The minimum useful body sequence is:

1. Create a body with `body_create()`.
2. Select its `BodyMode`.
3. Attach one or more shapes.
4. Set its space.
5. Set its initial transform and physical parameters.
6. Add callbacks or synchronization.
7. Keep the body and shape RIDs alive.

```gdscript
extends Node2D

var body: RID
var shape: RID

func _ready() -> void:
    body = PhysicsServer2D.body_create()
    shape = PhysicsServer2D.rectangle_shape_create()
    PhysicsServer2D.shape_set_data(shape, Vector2(32.0, 16.0)) # half-extents

    PhysicsServer2D.body_set_mode(body, PhysicsServer2D.BODY_MODE_RIGID)
    PhysicsServer2D.body_add_shape(body, shape)
    PhysicsServer2D.body_set_space(body, get_world_2d().space)
    PhysicsServer2D.body_set_state(
        body,
        PhysicsServer2D.BODY_STATE_TRANSFORM,
        Transform2D(0.0, Vector2(100.0, 100.0))
    )

func _exit_tree() -> void:
    if body.is_valid():
        PhysicsServer2D.free_rid(body)
    if shape.is_valid():
        PhysicsServer2D.free_rid(shape)
```

`BodyMode` has these meanings:

| Constant | Meaning |
|---|---|
| `BODY_MODE_STATIC` | Moved only by user code; does not perform swept collision along its manually changed path. |
| `BODY_MODE_KINEMATIC` | Moved by user code and collides along its path. |
| `BODY_MODE_RIGID` | Responds to forces, impulses, and other bodies. |
| `BODY_MODE_RIGID_LINEAR` | Rigid-like body that does not rotate; only linear velocity is affected by external forces. |

Configure collision filtering with:

- `body_set_collision_layer(body, layer)`: layers on which the body exists;
- `body_set_collision_mask(body, mask)`: layers the body scans for collision;
- `body_set_collision_priority(body, priority)`: depenetration priority;
- `body_add_collision_exception(body, other)` and
  `body_remove_collision_exception(body, other)`.

Attach an application-level identity with
`body_attach_object_instance_id(body, object_id)`. The ID is returned in area
monitor callbacks and can be used to map a body RID back to a `Node` or manager
object. This association does not keep the object alive.

Attach optional physics-rendering identity with
`body_attach_canvas_instance_id(body, canvas_id)`. This is metadata for the
canvas instance and does not draw anything by itself.

## 6. Body parameters and state

Use `body_set_param(body, parameter, value)` for physical properties:

| `BodyParameter` | Meaning |
|---|---|
| `BODY_PARAM_BOUNCE` | Restitution/bounce factor. |
| `BODY_PARAM_FRICTION` | Friction coefficient. |
| `BODY_PARAM_MASS` | Mass; may trigger automatic center-of-mass and inertia recalculation. |
| `BODY_PARAM_INERTIA` | Rotational inertia; values `<= 0` request automatic calculation. |
| `BODY_PARAM_CENTER_OF_MASS` | Local center-of-mass position. |
| `BODY_PARAM_GRAVITY_SCALE` | Multiplier applied to gravity. |
| `BODY_PARAM_LINEAR_DAMP_MODE` | Whether linear damping combines with or replaces environmental damping. |
| `BODY_PARAM_ANGULAR_DAMP_MODE` | Whether angular damping combines with or replaces environmental damping. |
| `BODY_PARAM_LINEAR_DAMP` | Linear damping factor. |
| `BODY_PARAM_ANGULAR_DAMP` | Angular damping factor. |

`BodyDampMode` is `BODY_DAMP_MODE_COMBINE` or
`BODY_DAMP_MODE_REPLACE`.

Use `body_set_state(body, state, value)` and `body_get_state()` for:

- `BODY_STATE_TRANSFORM` (`Transform2D`);
- `BODY_STATE_LINEAR_VELOCITY` (`Vector2`);
- `BODY_STATE_ANGULAR_VELOCITY` (`float`);
- `BODY_STATE_SLEEPING` (`bool`);
- `BODY_STATE_CAN_SLEEP` (`bool`).

For forces and motion:

- `body_apply_central_force()` applies a continuous force;
- `body_apply_central_impulse()` applies an instantaneous linear impulse;
- `body_apply_force()` applies a force at a position;
- `body_apply_impulse()` applies an impulse at a position;
- `body_apply_torque()` applies continuous rotational force;
- `body_apply_torque_impulse()` applies an instantaneous angular impulse;
- `body_add_constant_central_force()` and `body_add_constant_force()` add
  persistent forces;
- `body_add_constant_torque()` adds persistent torque;
- `body_set_axis_velocity()` changes velocity along a requested axis.

For fast bodies, use `body_set_continuous_collision_detection_mode()` with:

- `CCD_MODE_DISABLED`: fastest, but can miss fast or small collisions;
- `CCD_MODE_CAST_RAY`: ray-based CCD, faster and less precise;
- `CCD_MODE_CAST_SHAPE`: shape-cast CCD, slower and more precise.

## 7. Callbacks and custom integration

`body_set_force_integration_callback(body, callable, userdata)` calls a
`Callable` every physics tick before standard force integration. With no
userdata, the callable receives:

```gdscript
func integrate_body(state: PhysicsDirectBodyState2D) -> void:
    state.linear_velocity += Vector2(0.0, -10.0)
```

With userdata, it receives `(state, userdata)`. The state object can read and
modify the body's physics state. Use
`body_set_omit_force_integration(body, true)` only when the callback will
replace the standard integration; otherwise normal forces, torques, and
damping are skipped.

`body_set_state_sync_callback(body, callable)` calls the callable after an
active physics tick so the latest `PhysicsDirectBodyState2D` can be copied to a
visual object. Clear either callback with `Callable()`.

The direct body state is intended for physics-thread synchronization. Do not
retain it for later use and do not use it after the callback returns.

## 8. Areas and monitoring

Create an area with `area_create()`, attach shapes with `area_add_shape()`, and
assign a space with `area_set_space()`.

Configure:

- `area_set_collision_layer()` and `area_set_collision_mask()`;
- `area_set_transform()`;
- `area_set_monitorable(area, bool)`;
- `area_set_monitor_callback(area, callable)`;
- `area_set_area_monitor_callback(area, callable)`;
- `area_attach_object_instance_id(area, object_id)`;
- `area_attach_canvas_instance_id(area, canvas_id)`.

The body monitor callback receives five arguments:

```gdscript
func area_body_event(
    status: int,
    body_rid: RID,
    instance_id: int,
    body_shape_index: int,
    area_shape_index: int
) -> void:
    if status == PhysicsServer2D.AREA_BODY_ADDED:
        pass
    elif status == PhysicsServer2D.AREA_BODY_REMOVED:
        pass
```

`AREA_BODY_ADDED` and `AREA_BODY_REMOVED` describe shape-level transitions,
not necessarily whole-body transitions. Count or track shape pairs if a body
should be considered entered only when its first shape arrives and exited only
when its last shape leaves.

The area-area callback uses the same low-level style for area overlap events.
`area_set_monitorable()` controls whether other areas can detect this area.

Area physics overrides use `area_set_param()` with:

- `AREA_PARAM_GRAVITY_OVERRIDE_MODE`;
- `AREA_PARAM_GRAVITY`;
- `AREA_PARAM_GRAVITY_VECTOR`;
- `AREA_PARAM_GRAVITY_IS_POINT`;
- `AREA_PARAM_GRAVITY_POINT_UNIT_DISTANCE`;
- linear and angular damp override modes and values;
- `AREA_PARAM_PRIORITY`.

`AreaSpaceOverrideMode` values are `DISABLED`, `COMBINE`,
`COMBINE_REPLACE`, `REPLACE`, and `REPLACE_COMBINE`. These determine whether
the area's gravity/damping is ignored, accumulated, or replaces other areas.

## 9. Motion tests and direct queries

`body_test_motion(body, parameters, result)` tests whether a body would collide
along a requested motion without actually moving it. The parameters use
`PhysicsTestMotionParameters2D`; an optional `PhysicsTestMotionResult2D`
receives collision details.

For general space queries:

```gdscript
var state := PhysicsServer2D.space_get_direct_state(get_world_2d().space)
var hit := state.intersect_ray(query_parameters)
```

Use `PhysicsDirectSpaceState2D` methods such as ray intersection, point
intersection, shape intersection, and motion-collision queries. Direct-space
access is safest during `_physics_process()` or an engine-provided physics
callback while the space is unlocked. Do not perform arbitrary queries during
render callbacks.

## 10. Joints

Create a joint RID with `joint_create()`, then configure it with one of:

- `joint_make_pin(joint, anchor, body_a, body_b)`;
- `joint_make_groove(joint, groove_1_a, groove_2_a, anchor_b, body_a, body_b)`;
- `joint_make_damped_spring(joint, anchor_a, anchor_b, body_a, body_b)`.

Set or read the joint type with `joint_get_type()`. Use
`joint_disable_collisions_between_bodies()` to control whether the connected
bodies collide with each other.

2D joint families:

- pin joints keep two anchor points together and can have angular limits and a
  motor;
- groove joints constrain one anchor to a line;
- damped springs seek a rest length using stiffness and damping.

Use `joint_set_param()` for common bias/max-bias/max-force values,
`pin_joint_set_param()` and `pin_joint_set_flag()` for pin settings, and
`damped_spring_joint_set_param()` for rest length, stiffness, and damping.
`joint_clear()` removes the joint's body configuration while retaining the RID
for possible reuse.

## 11. Process information and activation

`set_active(active)` enables or disables the server's active processing.
This is a global server switch and should not be toggled casually by a
per-object system.

`get_process_info()` accepts:

- `INFO_ACTIVE_OBJECTS`: number of active, non-sleeping objects;
- `INFO_COLLISION_PAIRS`: number of possible collision pairs;
- `INFO_ISLAND_COUNT`: number of solver islands.

These are diagnostics, not a replacement for profiling.

## 12. Complete minimal body example

```gdscript
extends Node2D

var body: RID
var shape: RID

func _ready() -> void:
    body = PhysicsServer2D.body_create()
    shape = PhysicsServer2D.circle_shape_create()
    PhysicsServer2D.shape_set_data(shape, 12.0)
    PhysicsServer2D.body_set_mode(body, PhysicsServer2D.BODY_MODE_RIGID)
    PhysicsServer2D.body_add_shape(body, shape)
    PhysicsServer2D.body_set_space(body, get_world_2d().space)
    PhysicsServer2D.body_set_collision_layer(body, 1)
    PhysicsServer2D.body_set_collision_mask(body, 1)
    PhysicsServer2D.body_set_state(
        body,
        PhysicsServer2D.BODY_STATE_TRANSFORM,
        Transform2D(0.0, Vector2(200.0, 100.0))
    )

func _physics_process(_delta: float) -> void:
    var transform: Transform2D = PhysicsServer2D.body_get_state(
        body,
        PhysicsServer2D.BODY_STATE_TRANSFORM
    )
    # Copy `transform` to a custom CanvasItem here if one exists.

func _exit_tree() -> void:
    if body.is_valid():
        PhysicsServer2D.free_rid(body)
    if shape.is_valid():
        PhysicsServer2D.free_rid(shape)
```

## 13. Validation checklist

Before generating or reviewing server-level 2D code, verify:

- The common ownership, identifier, lifetime, timing, and type checklist in
  `../shared_concepts.md` passes.
- Every body or area has the intended space.
- Every attached shape was created with compatible 2D data.
- Collision layers and masks are intentional bitmasks.
- `BODY_MODE_RIGID` is used for force-driven simulation, not manual transform
  animation.
- Callback signatures match the documented `Callable` arguments.
- State callbacks are cleared or their targets remain valid until the RID is
  freed.
- Server-created bodies have an explicit visual synchronization path if they
  need to be seen.
