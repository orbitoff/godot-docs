# Godot 4 GDScript Authoring Guide

This is a self-contained reference for generating valid Godot 4 GDScript
source files (`.gd`) without relying on the Godot editor. It is written for AI
systems that need to create scripts with correct syntax, declarations, typing,
control flow, annotations, signals, exports, documentation comments, and
style.

A GDScript file is a class definition, whether or
not it registers a global name with `class_name`.

This guide is based on the Godot 4.7 documentation snapshot.

The language is tightly integrated with Godot but is independent from Python.
Python-like indentation does not mean Python compatibility.

Read [`shared_concepts.md`](shared_concepts.md) for the
cross-format rules on project-specific API verification, typed values,
resource sharing, identifiers, timing, and validation.

## 1. High-confidence generation rules

Use these rules when creating a new `.gd` file:

1. Save the file as UTF-8 text with LF line endings and no BOM.
2. Use tabs for indentation, not spaces.
3. Put one statement on each line.
4. Use `#` for ordinary comments and `##` for documentation comments.
5. Put annotations, `class_name`, and `extends` at the top of the file.
6. Declare signals, constants, and member variables before functions.
7. Use `@onready` for node lookups that require the scene tree to be ready.
8. Use static types when the intended type is known.
9. Use `:=` only when the initializer clearly determines the desired type.
10. Use typed arrays and dictionaries when their element types are known.
11. Use `await` for asynchronous signals and functions in Godot 4.
12. Apply the shared concepts guide's project-specific API verification rules.
13. Keep the script's inheritance and lifecycle methods consistent with the
    node or resource it is attached to.

Correct parsing is not enough. A script can be syntactically valid but fail at
runtime because an engine method, property, signal, node path, or resource does
not exist.

## 2. Minimal valid scripts

An empty script can be:

```gdscript
extends RefCounted
```

For a node script:

```gdscript
extends Node
```

For a script attached to a 2D node:

```gdscript
extends Node2D
```

For a named reusable class:

```gdscript
class_name HealthComponent
extends Node
```

If `extends` is omitted, the script uses the default base class described by
the GDScript reference. Explicitly writing the intended base class is clearer
and prevents accidental attachment to an incompatible object.

## 3. Canonical file layout

Use this order unless a project style guide requires otherwise:

```gdscript
@tool
@icon("res://art/health_component.svg")
class_name HealthComponent
extends Node

## Emitted when the health value reaches zero.
signal died

## Maximum health.
const DEFAULT_MAX_HEALTH: int = 100

## Current health.
@export var max_health: int = DEFAULT_MAX_HEALTH
var health: int = DEFAULT_MAX_HEALTH

@onready var owner_node: Node = get_parent()

func _ready() -> void:
    health = max_health

func take_damage(amount: int) -> void:
    health = maxi(health - amount, 0)
    if health == 0:
        died.emit()
```

The canonical order is:

1. File annotations such as `@tool` and `@icon`.
2. `class_name`.
3. `extends`.
4. File-level documentation comments.
5. Signals.
6. Enums.
7. Constants.
8. Exported member variables.
9. Other member variables.
10. `@onready` variables.
11. Static variables and static functions, where used.
12. Lifecycle and public functions.
13. Private helper functions.
14. Inner classes.

The parser does not require every style ordering rule, but consistent ordering
helps humans and AI systems understand the class.

## 4. Lexical syntax

### 4.1 Indentation

Indentation defines blocks. Use one tab per indentation level:

```gdscript
func example() -> void:
    if true:
        print("inside the if block")
    print("back in the function")
```

Do not mix tabs and spaces in the same indentation structure. A block begins
after a colon and continues while the indentation remains deeper.

### 4.2 Statements

Statements normally end at the newline:

```gdscript
var count: int = 0
count += 1
```

Semicolons are optional and should normally be avoided:

```gdscript
var a = 1; var b = 2
```

The second form is valid in contexts where the parser accepts it, but one
statement per line is clearer and follows the style guide.

### 4.3 Comments

Everything after `#` is an ordinary comment:

```gdscript
# This is not shown as API documentation.
var speed: float = 4.0
```

Documentation comments use `##`:

```gdscript
## Movement speed in pixels per second.
@export var speed: float = 4.0
```

Documentation comments must be immediately above the declaration they
describe, unless they are file-level documentation at the top of the script.

### 4.4 Identifiers

Identifiers can contain letters, digits, and underscores, but cannot begin
with a digit. Avoid reserved words and names that collide with inherited
methods or properties.

Recommended naming:

- Classes: `PascalCase`
- Functions and variables: `snake_case`
- Constants and enum members: `UPPER_SNAKE_CASE`
- Signals: `past_tense` or event-style `something_changed`
- Private members: a leading underscore, such as `_cache`

## 5. File-level declarations

### 5.1 `extends`

`extends` sets the base class:

```gdscript
extends CharacterBody2D
```

It may refer to a built-in Godot class, a globally registered GDScript class,
another script resource, or an inner class:

```gdscript
extends "res://characters/base_character.gd"
```

There is no multiple inheritance. A script has one direct base class.

### 5.2 `class_name`

`class_name` registers a script globally so other scripts can use it as a
type or instantiate it:

```gdscript
class_name Damageable
extends Node
```

The name must be a valid identifier and should not collide with another global
class. A global class whose name starts with `Editor` is hidden from some
editor creation dialogs.

### 5.3 `@icon`

`@icon` associates an editor icon with a globally named script:

```gdscript
@icon("res://icons/damageable.svg")
class_name Damageable
extends Node
```

The path must point to a valid project resource.

### 5.4 `@tool`

`@tool` runs the script inside the editor as well as in the game:

```gdscript
@tool
extends Node
```

Tool scripts can modify editor-visible objects and resources. They must be
written defensively because an editor crash or destructive operation can
affect the project itself. Do not assume that runtime-only nodes, resources, or
scene state exist while the editor is inspecting the script.

## 6. Variables

### 6.1 Basic declarations

```gdscript
var count = 0
var title: String = "Player"
var speed := 4.0
var uninitialized: int
```

`var` declares a mutable variable. A declaration can be:

- dynamically typed: `var value = expression`
- explicitly typed: `var value: Type = expression`
- inferred: `var value := expression`
- typed but uninitialized: `var value: Type`

Use explicit types when they communicate an important contract. Use `:=`
when the initializer unambiguously determines the intended type.

### 6.2 Constants

Constants are assigned once and must be initialized:

```gdscript
const MAX_SPEED: float = 12.0
const DEFAULT_NAME := "Player"
```

Constants may use constant expressions. They cannot depend on runtime state.
Use uppercase names for constants.

### 6.3 Static variables

Static variables belong to the script rather than to each object instance:

```gdscript
static var instance_count: int = 0
```

Use static state only when shared state is intentional. Static variables can
make tests and scene instances influence one another.

### 6.4 `@onready`

`@onready` delays initialization until the node's `_ready()` phase:

```gdscript
@onready var label: Label = $UI/Label
@onready var animation_player: AnimationPlayer = %AnimationPlayer
```

Use it for node lookups and other values that depend on the scene tree. A
normal member initializer runs before the node tree is ready and may produce a
null result or an invalid path.

### 6.5 Setters and getters

Properties can define custom accessors:

```gdscript
var health: int = 100:
    set(value):
        health = clampi(value, 0, max_health)
        health_changed.emit(health)
    get:
        return health
```

The setter runs when the property is assigned and the getter runs when it is
read. Avoid indirect assignments that call the same setter recursively. Keep
validation and side effects small and explicit.

In-editor setter/getter behavior depends on whether the script is a tool
script. `@tool` is required when the logic must execute while editing.

## 7. Signals

Signals declare events emitted by an object:

```gdscript
signal health_changed(value: int)
signal died
```

Argument names and types document the event payload:

```gdscript
signal hit(damage: int, source: Node)
```

Emit a signal with:

```gdscript
health_changed.emit(health)
died.emit()
```

Connect a signal with a `Callable`:

```gdscript
button.pressed.connect(_on_button_pressed)
health_component.died.connect(_on_died)
```

Disconnect with the same callable when necessary:

```gdscript
button.pressed.disconnect(_on_button_pressed)
```

Bind extra arguments with `Callable.bind()`:

```gdscript
button.pressed.connect(_on_button_pressed.bind(button))

func _on_button_pressed(button: BaseButton) -> void:
    print(button.name)
```

Prefer the Godot 4 `signal.connect(...)` form over legacy connection patterns.
The signal, target object, and callable must all exist at runtime.

## 8. Functions

### 8.1 Declaration and return type

```gdscript
func add(a: int, b: int) -> int:
    return a + b

func announce(message: String) -> void:
    print(message)
```

The return type follows `->`. Use `-> void` when the function intentionally
does not return a value.

### 8.2 Parameters and defaults

Parameters without defaults are required:

```gdscript
func move_to(target: Vector2, speed: float) -> void:
    pass
```

Trailing parameters may have defaults:

```gdscript
func spawn(position: Vector2, count: int = 1) -> void:
    pass
```

Once a parameter has a default, every following parameter must also have a
default. Callers can omit only the trailing optional parameters.

### 8.3 Variadic functions

Use `...args` for a variable number of arguments. It must be the final
parameter:

```gdscript
func log_values(...values: Array) -> void:
    for value in values:
        print(value)
```

The rest parameter collects excess arguments into an `Array`. `Array` is the
only supported static type for a typed rest parameter; `Array[int]` and other
typed-array rest annotations are not supported.

There is no general spread syntax for expanding an array into a call. Use
`callv()` when a call must receive an array of arguments.

### 8.4 Return paths

A non-void function should return a compatible value on every possible path:

```gdscript
func sign_label(value: int) -> String:
    if value > 0:
        return "positive"
    if value < 0:
        return "negative"
    return "zero"
```

Do not rely on an implicit null return from a function declared with a
non-nullable return type.

### 8.5 First-class functions and lambdas

Functions can be stored and passed as `Callable` values:

```gdscript
var callback: Callable = _on_finished
callback.call()
```

Lambda syntax:

```gdscript
var double_value := func(value: int) -> int:
    return value * 2
```

Lambdas can capture local variables. Captured values have important lifetime
and assignment semantics; do not assume that assigning to a captured local
inside a lambda mutates the outer local in the same way as a reference object.

## 9. Constructors and lifecycle methods

`_init()` is the constructor:

```gdscript
func _init(starting_health: int = 100) -> void:
    health = starting_health
```

For a `Node`, common lifecycle methods include:

```gdscript
func _enter_tree() -> void:
    pass

func _ready() -> void:
    pass

func _process(delta: float) -> void:
    pass

func _physics_process(delta: float) -> void:
    pass

func _exit_tree() -> void:
    pass
```

Only define lifecycle methods supported by the inherited class and needed by
the script. `_process()` and `_physics_process()` receive elapsed time in
seconds.

Lifecycle timing and intent:

| Method | Meaning |
| --- | --- |
| `_init()` | Constructs the script instance. The node may not yet be inside a scene tree, so scene-tree lookups are not valid assumptions here. |
| `_enter_tree()` | Runs when the node enters the scene tree, before children are necessarily ready. Use it for tree-presence setup and early notifications. |
| `_ready()` | Runs after the node and its children have entered the tree and become ready. Scene-tree-dependent lookups are normally safe here. |
| `_process(delta)` | Runs once per rendered frame when processing is enabled. `delta` is elapsed wall-clock time in seconds; do not use it for deterministic physics. |
| `_physics_process(delta)` | Runs on the fixed physics tick when physics processing is enabled. Use it for movement and physics calculations; `delta` is the fixed-step interval. |
| `_exit_tree()` | Runs when the node leaves the scene tree. Disconnect or release tree-dependent state here when needed. |
| `_static_init()` | Initializes static/class-level state once for the script type, before ordinary instances use it. |

Static initialization is available through `_static_init()` for static
initialization needs. Use it only when class-level initialization is required.

Engine virtual methods should be overridden with compatible signatures. Do not
shadow unrelated engine methods or properties with incompatible declarations.

## 10. Inheritance and `super`

Call the parent implementation with:

```gdscript
func _ready() -> void:
    super()
    setup_player()
```

Call a specific parent method with:

```gdscript
func reset() -> void:
    super.reset()
```

Use `super` when the parent behavior must remain active. Omitting it is valid
when the child intentionally replaces the behavior.

`self` refers to the current object:

```gdscript
self.speed = 0.0
self.call("refresh")
```

It is especially useful when accessing dynamic members or when a local
variable has the same name as a member.

## 11. Inner classes

An inner class is declared inside a script:

```gdscript
class InventoryEntry:
    var item_id: String
    var quantity: int = 1

    func _init(id: String, amount: int = 1) -> void:
        item_id = id
        quantity = amount
```

Instantiate it with `.new()`:

```gdscript
var entry := InventoryEntry.new("potion", 3)
```

Inner classes can inherit from a class:

```gdscript
class Entry extends RefCounted:
    var value: int
```

They are not globally registered unless the outer script exposes them through
its own API.

## 12. Built-in types and literals

Common GDScript types include:

- `null`
- `bool`
- `int`
- `float`
- `String`
- `StringName`
- `NodePath`
- `Vector2`, `Vector2i`
- `Rect2`, `Rect2i`
- `Vector3`, `Vector3i`
- `Vector4`, `Vector4i`
- `Transform2D`
- `Quaternion`
- `AABB`
- `Basis`
- `Transform3D`
- `Plane`
- `Color`
- `RID`
- `Object`
- `Callable`
- `Signal`
- `Variant`
- `void` (return type only)
- `Array`
- `Dictionary`
- packed arrays such as `PackedByteArray`, `PackedInt32Array`,
  `PackedFloat32Array`, `PackedStringArray`, and related types

### 12.1 Built-in type semantics

Use these meanings instead of inferring behavior from a type name:

| Type/value | Meaning and important behavior |
| --- | --- |
| `null` | Absence of a value. A missing object reference, failed object cast, or failed lookup can be null. Do not call methods or access properties until null has been handled. |
| `bool` | Boolean value, `true` or `false`. It is not interchangeable with an integer in typed APIs. |
| `int` | Signed integer value. Integer division truncates toward zero; division by zero is an error. |
| `float` | Floating-point value. Operations can produce `INF` or `NAN`; exact equality is unsafe for most calculated values. |
| `String` | Unicode text value. It is distinct from `StringName` and `NodePath`; conversions should be explicit when an API expects another type. |
| `StringName` | Interned name value optimized for repeated identifiers, property names, and signal names. `&"Player"` creates a StringName literal. |
| `NodePath` | A path identifying a node and optionally a property in the scene tree. It is data, not the referenced node itself. |
| `Vector2` | Two-component floating-point vector, normally used for 2D positions, directions, and sizes. |
| `Vector2i` | Two-component integer vector, useful for pixel coordinates, grid positions, and integer sizes. |
| `Vector3` | Three-component floating-point vector, normally used for 3D positions, directions, and sizes. |
| `Vector3i` | Three-component integer vector, useful for voxel or grid coordinates. |
| `Vector4` | Four-component floating-point vector, useful for packed values or homogeneous-style data. |
| `Vector4i` | Four-component integer vector. |
| `Rect2` | Axis-aligned 2D rectangle represented by position and size. |
| `Rect2i` | Integer-coordinate axis-aligned 2D rectangle. |
| `Transform2D` | 2D affine transform containing a basis and an origin; used for position, rotation, scale, and shear. |
| `Quaternion` | Four-component rotation representation for 3D orientation; it is not an Euler-angle vector. |
| `AABB` | Axis-aligned 3D bounding box represented by position and size. |
| `Basis` | 3x3 matrix representing 3D rotation, scale, and shear without translation. |
| `Transform3D` | 3D affine transform containing a `Basis` and an origin. |
| `Plane` | 3D plane represented by a normal and a distance component. |
| `Color` | RGBA color value with floating-point channels, normally in the `0..1` range. |
| `RID` | Opaque low-level handle to an engine resource. It is not the resource object and should not be inspected as ordinary data. |
| `Object` | Base class for Godot engine objects. Objects are identity-based and are not automatically reference-counted merely because they are typed as `Object`. |
| `RefCounted` | `Object` subclass whose lifetime is managed by reference counting. It is normally released when no references remain. |
| `Callable` | A callable wrapper containing a target object/function and optional bound arguments. Invoke it with `call()` or `callv()`, or connect it to a signal. |
| `Signal` | A typed event handle belonging to an object. Use `connect()`, `disconnect()`, and `emit()` on the signal instance. |
| `Variant` | Dynamic container that can hold any supported GDScript/engine value. It provides less static checking than a concrete type. |
| `void` | Return-type marker meaning a function does not return a value. It is not a value type for variables. |
| `Array` | Ordered dynamic container that can hold Variant values. It can be typed as `Array[T]` when all elements should have type `T`. |
| `Dictionary` | Key-value container. Untyped dictionaries can use heterogeneous key/value types; typed forms use `Dictionary[K, V]`. |
| `PackedByteArray` | Compact packed array of bytes, useful for binary data. |
| `PackedInt32Array` | Compact packed array of signed 32-bit integers. |
| `PackedInt64Array` | Compact packed array of signed 64-bit integers. |
| `PackedFloat32Array` | Compact packed array of 32-bit floating-point values. |
| `PackedFloat64Array` | Compact packed array of 64-bit floating-point values. |
| `PackedStringArray` | Compact packed array of strings. |
| `PackedVector2Array` | Compact packed array of `Vector2` values. |
| `PackedVector3Array` | Compact packed array of `Vector3` values. |
| `PackedColorArray` | Compact packed array of `Color` values. |

Special floating-point values:

| Value | Meaning |
| --- | --- |
| `INF` | Positive floating-point infinity. Comparisons and arithmetic involving it require deliberate handling. |
| `NAN` | Not-a-number floating-point value. `NAN == NAN` is false; use `is_nan()` or an appropriate validity check rather than equality. |

### 12.2 Engine classes used in this guide

These are Godot engine classes, not GDScript language primitives:

| Class | Meaning |
| --- | --- |
| `Node` | Base scene-tree object. It owns children, participates in lifecycle notifications, and can be attached to a scene. |
| `Node2D` | `Node` with a 2D transform and position/rotation/scale properties. |
| `Node3D` | `Node` with a 3D transform. |
| `CharacterBody2D` | Script-driven 2D physics body with a `velocity` property and movement helpers such as `move_and_slide()`. |
| `Control` | Base class for UI/layout nodes using anchors, offsets, and container layout. |
| `BaseButton` | Base class for clickable button controls; it provides button-related signals such as `pressed`. |
| `Label` | UI control that displays text. |
| `Camera2D` | 2D camera node that determines the visible 2D viewport region. |
| `SceneTree` | Runtime tree that owns the active scene, groups, processing, and scene-tree-wide operations. A node receives one from `get_tree()` only while it is inside a tree. |
| `AnimationPlayer` | Node that plays named `Animation` resources through animation libraries and emits playback signals. |
| `Animation` | Resource containing time-based tracks and keys that can animate properties, method calls, or other supported targets. |
| `Object` | Root engine-object class; see the built-in type table for lifetime implications. |
| `Resource` | Serializable data object that can be saved and loaded as a resource file. |
| `PackedScene` | Resource containing a saved scene tree. Call `instantiate()` to create a node hierarchy from it. |
| `Texture2D` | 2D image resource sampled by rendering nodes or shaders. |
| `Curve` | Resource representing a one-dimensional curve that can be sampled or edited. |
| `Material` | Base resource type for surface/material configuration. |
| `Enemy` | Example user-defined global class; it exists only if a project script registers it with `class_name Enemy`. |
| `HealthComponent` | Example user-defined class from this guide; it is not built into Godot. |

Examples:

```gdscript
var enabled: bool = true
var count: int = 3
var ratio: float = 0.5
var title: String = "Player"
var position_2d: Vector2 = Vector2(10.0, 20.0)
var position_3d: Vector3 = Vector3(1.0, 2.0, 3.0)
var color: Color = Color(1.0, 0.5, 0.25, 1.0)
var path: NodePath = NodePath("Player/Camera")
```

Use the exact type expected by an engine property. A string is not a
`StringName`, and a string is not a `NodePath`.

## 13. Arrays and dictionaries

### 13.1 Arrays

```gdscript
var values: Array = [1, 2, 3]
var names: Array[String] = ["A", "B", "C"]
var numbers := [1, 2, 3]
```

Typed arrays constrain the intended element type:

```gdscript
var enemies: Array[Enemy] = []
```

Nested typed arrays such as `Array[Array[int]]` are not supported by the
documented type system. Use an untyped outer array or a custom class when a
nested structure is required.

Array operations:

```gdscript
values.append(4)
values.push_back(5)
values.pop_back()
values.erase(2)
var first = values[0]
values[0] = 10
```

Do not assume that assigning a loop variable changes the array element:

```gdscript
for value in values:
    value += 1 # Changes only the local variable.
```

Use an index when mutating elements:

```gdscript
for index in values.size():
    values[index] += 1
```

### 13.2 Dictionaries

```gdscript
var data: Dictionary = {"name": "Player", "health": 100}
var settings: Dictionary[String, int] = {"lives": 3}
```

Keys may be different types in an untyped dictionary:

```gdscript
var mixed := {"name": "Player", 1: "first"}
```

Dictionary member syntax is convenient for identifier-like keys:

```gdscript
var data := {name = "Player", health = 100}
print(data.name)
```

Use bracket syntax for dynamic or non-identifier keys:

```gdscript
data["health"] = 90
var key := "name"
print(data[key])
```

### 13.3 Trailing commas

Use trailing commas in multiline collections:

```gdscript
var settings := {
    "speed": 4.0,
    "acceleration": 12.0,
}
```

This reduces diff noise when items are added or removed.

## 14. Operators and expressions

Common operators:

```gdscript
var sum = a + b
var difference = a - b
var product = a * b
var quotient = a / b
var remainder = a % b
var power = a ** b
var is_same = a == b
var is_different = a != b
var is_less = a < b
var is_less_or_equal = a <= b
var is_greater = a > b
var is_greater_or_equal = a >= b
var both = left and right
var either = left or right
var inverted = not value
```

Operator and keyword semantics:

| Operator/keyword | Meaning |
| --- | --- |
| `and` | Boolean conjunction with short-circuit evaluation; the right side is skipped when the left side is false. |
| `or` | Boolean disjunction with short-circuit evaluation; the right side is skipped when the left side is true. |
| `not` | Boolean negation. |
| `in` | Tests membership in a collection, and introduces the iterable expression in a `for` loop. |
| `is` | Tests whether an object/value is compatible with a specified type. |
| `as` | Attempts an object-type cast; a failed object cast returns null rather than producing a valid object of the requested type. |
| `==` | Equality comparison using GDScript equality rules. |
| `!=` | Inequality comparison. |
| `+`, `-`, `*`, `/`, `%`, `**` | Arithmetic operators; operand types affect conversion and result type. `**` is exponentiation. |
| `=`, `+=`, `-=`, `*=`, `/=`, `%=` | Assignment and compound assignment operators. |
| `if`, `elif`, `else` | Conditional branches; only the selected branch executes. |
| `for` | Iterates an array, dictionary, range, or other supported iterable. |
| `while` | Repeats while its condition remains true. |
| `match` | Performs pattern matching, which is stricter than ordinary `==` in cases such as `1` versus `1.0`. |
| `when` | Adds a guard condition to a `match` pattern. |
| `break` | Exits the nearest loop. |
| `continue` | Skips to the next iteration of the nearest loop. |
| `pass` | Explicitly does nothing and supplies a required statement in an empty block. |
| `return` | Exits the current function and optionally supplies its return value. |
| `await` | Suspends the current function until a signal or awaitable result completes, then resumes later. |
| `yield` | Godot 3-era coroutine syntax; do not use it in Godot 4. |

Use parentheses when precedence is not obvious:

```gdscript
var result := (base + bonus) * multiplier
```

The conditional expression is:

```gdscript
var label := "alive" if health > 0 else "dead"
```

Assignment operators include `=`, `+=`, `-=`, `*=`, `/=`, and `%=`:

```gdscript
health -= damage
position += velocity * delta
```

Binary operators are left-associative in the documented language rules.
Parenthesize expressions involving several operators rather than depending on
readers remembering precedence.

## 15. Type conversion and checking

Use explicit conversions when the desired type is not obvious:

```gdscript
var integer_value: int = int(float_value)
var text_value: String = str(integer_value)
var name_value: StringName = &"Player"
```

Use `is` for type checks:

```gdscript
if value is Node2D:
    var node := value as Node2D
    node.position = Vector2.ZERO
```

`as` returns a value converted to the requested object type or null when it
cannot be used as that type. Check the result before dereferencing it.

The `Variant` type represents a value whose concrete type is not fixed:

```gdscript
var value: Variant = get_value()
```

Use `Variant` when dynamic values are intentional, not as a replacement for
known types.

## 16. Static typing and inference

GDScript is gradually typed. Static typing is optional, but it improves editor
completion, catches errors earlier, documents contracts, and can improve
performance.

### 16.1 Typed variables

```gdscript
var health: int = 100
var target: Node2D
var names: Array[String] = []
var scores: Dictionary[String, int] = {}
```

### 16.2 Typed parameters and returns

```gdscript
func damage(target: Node, amount: int) -> bool:
    if target == null:
        return false
    target.queue_free()
    return true
```

### 16.3 Inference

Use `:=` when the initializer provides the intended type:

```gdscript
var speed := 5.0
var player := get_node("Player")
```

Be careful with inference from a broad return type:

```gdscript
var value := get_dynamic_value()
```

If the function returns `Variant`, the inferred variable may remain dynamic.
Use an explicit type or conversion when a narrower contract is required.

### 16.4 Typed loops

```gdscript
for enemy: Enemy in enemies:
    enemy.take_damage(10)
```

The collection and loop variable type must be compatible.

### 16.5 Custom types

The cleanest way to reuse a custom script as a type is `class_name`:

```gdscript
class_name Enemy
extends CharacterBody2D
```

Then:

```gdscript
var enemy: Enemy
func find_enemy() -> Enemy:
    return enemy
```

Other type sources include preloaded scripts, inner classes, built-in classes,
native classes, and enums.

### 16.6 Overriding typed methods

An override must remain compatible with the parent signature. Return types and
parameter types follow the documented covariance and contravariance rules.
When in doubt, copy the inherited method signature from the class reference
and adapt only the implementation.

## 17. Control flow

### 17.1 `if`

```gdscript
if health <= 0:
    die()
elif health < max_health:
    regenerate()
else:
    idle()
```

The condition must evaluate to a boolean-compatible value.

### 17.2 `while`

```gdscript
while remaining > 0:
    remaining -= 1
```

Ensure that the loop condition can eventually become false or use `break`.

### 17.3 `for`

Iterate over a collection:

```gdscript
for enemy in enemies:
    enemy.update_target(player)
```

Iterate over a range:

```gdscript
for index in range(10):
    print(index)
```

The shorthand `for index in 10:` is also used for integer ranges in GDScript
examples. Prefer `range(...)` when clarity matters.

### 17.4 `break`, `continue`, and `pass`

```gdscript
for item in items:
    if item == null:
        continue
    if item.is_complete():
        break

func placeholder() -> void:
    pass
```

### 17.5 `return`

```gdscript
func find_player() -> Node:
    if player == null:
        return null
    return player
```

The returned value must satisfy the declared return type.

## 18. `match`

`match` selects a branch using pattern matching:

```gdscript
match state:
    State.IDLE:
        idle()
    State.RUNNING:
        run()
    _:
        reset()
```

The wildcard `_` matches anything and should normally be last.

Literal patterns:

```gdscript
match value:
    0:
        print("zero")
    "ready":
        print("ready")
    true:
        print("true")
```

Multiple patterns:

```gdscript
match value:
    1, 2, 3:
        print("small")
    _:
        print("other")
```

Array patterns:

```gdscript
match values:
    []:
        print("empty")
    [first, second]:
        print(first, second)
    [first, ..]:
        print(first)
```

Dictionary patterns:

```gdscript
match data:
    {"type": "enemy", "health": health}:
        print(health)
    _:
        print("unknown")
```

Pattern guards use `when`:

```gdscript
match value:
    number when number > 0:
        print("positive")
    _:
        print("not positive")
```

`match` pattern matching is stricter than `==` in important cases. For
example, `1` and `1.0` are not interchangeable match patterns. Do not use
`match` when ordinary equality semantics are required.

## 19. Asynchronous code and `await`

Await a signal:

```gdscript
func wait_for_animation(player: AnimationPlayer) -> void:
    player.animation_finished.connect(_on_animation_finished)
    await player.animation_finished
```

Await a function that returns a signal or awaitable result:

```gdscript
func wait_then_continue(timer: Timer) -> void:
    await timer.timeout
    continue_work()
```

An async function resumes later. Code after `await` must tolerate the object
being freed, the scene being changed, or the awaited event never occurring.
Do not use Godot 3 `yield` syntax in Godot 4 scripts.

## 20. Object lifetime

Reference-counted objects such as `RefCounted` are automatically released when
no references remain. `Node` and other `Object` instances are not managed in
the same way.

For nodes:

```gdscript
node.queue_free()
```

Use `queue_free()` for ordinary deferred node destruction. Do not call
`free()` casually from tool scripts or while iterating a tree; destruction can
invalidate references and editor state.

Always check whether an object may be null or already freed before using it
after an asynchronous boundary.

## 21. Exports and Inspector properties

`@export` exposes a member in the Inspector and causes its value to be saved
with a scene or resource:

```gdscript
@export var speed: float = 4.0
@export var target: Node2D
```

Exported variables need a type or a constant initializer:

```gdscript
@export var count: int
@export var label := "Player"
```

Do not use a runtime-only initializer when the Inspector needs a stable
default.

### 21.1 Export organization

```gdscript
@export_category("Movement")
@export var speed: float = 4.0

@export_group("Advanced movement")
@export var acceleration: float = 12.0

@export_subgroup("Air control")
@export var air_control: float = 0.5
```

Use one category or group hierarchy to make related properties easy to edit.

### 21.2 Export hints

Common export annotations include:

```gdscript
@export_file("*.json") var data_file: String
@export_dir var data_directory: String
@export_multiline var description: String
@export_range(0.0, 1.0, 0.01) var opacity: float = 1.0
@export_enum("Idle", "Run", "Jump") var state: String = "Idle"
@export_flags("Fire", "Ice", "Poison") var elements: int = 0
```

Other documented helpers include global file/directory pickers, node-path
exports, color alpha hints, and custom export hints. Use the annotation whose
value type matches the property.

`@export_custom` is intended for advanced Inspector hints and must use the
exact hint arguments expected by the target Godot version.

### 21.3 Exported resources and nodes

```gdscript
@export var material: Material
@export var scene: PackedScene
```

For typed resource constraints:

```gdscript
@export var texture: Texture2D
@export var curve: Curve
```

For a node path, use a separate path export:

```gdscript
@export var target_path: NodePath
```

`NodePath` stores a path and does not automatically resolve to a node. Call
`get_node(target_path)` when the node is needed, after confirming the path is
valid.

The editor and scene serializer use the declared type to choose valid
Inspector controls.

## 22. Annotations

Annotations begin with `@` and modify a declaration or script behavior.
Common annotations include:

- `@tool`: execute in the editor.
- `@icon("res://...")`: set a global script icon.
- `@onready`: initialize after the node enters the ready phase.
- `@export`: expose a member in the Inspector.
- `@export_group`, `@export_subgroup`, `@export_category`: organize exports.
- `@export_file`, `@export_dir`, `@export_global_file`,
  `@export_global_dir`: constrain path selection.
- `@export_multiline`: provide a multiline text editor.
- `@export_range`, `@export_enum`, `@export_flags`: constrain values.
- `@export_color_no_alpha`: export colors without editable alpha.
- `@export_storage`: serialize a property without displaying it in the
  Inspector.
- `@export_tool_button`: expose a callable as an Inspector button in a tool
  script.
- `@export_custom`: provide an advanced custom property hint.
- `@warning_ignore`: suppress a warning at a declaration or statement.
- `@warning_ignore_start`: suppress a warning for a block.
- `@warning_ignore_restore`: restore warnings after a suppression block.
- `@abstract`: mark a class or method as abstract where supported.
- `@rpc`: configure a remote procedure call.

Annotation spelling, placement, and arguments are strict. Do not place an
annotation on a declaration it does not support.

Annotation semantics:

| Annotation | Meaning and constraints |
| --- | --- |
| `@tool` | Executes the script in the editor as well as at runtime. Editor-time code must tolerate incomplete scenes and must avoid destructive actions unless explicitly intended. |
| `@icon(path)` | Assigns an editor icon to a globally named script. The path must point to a valid project resource. |
| `@onready` | Defers a member initializer until the node's ready phase, making scene-tree-dependent lookups safe at the intended lifecycle point. |
| `@export` | Serializes a property and exposes it in the Inspector. The type/default must be compatible with Godot's serialized property types. |
| `@export_category(name)` | Starts a top-level Inspector category. It is a presentation grouping and does not change the property's type or runtime behavior. |
| `@export_group(name)` | Starts an export group that can be collapsed in the Inspector. |
| `@export_subgroup(name)` | Starts a nested group under the current export group. |
| `@export_file(filter...)` | Exposes a project-file picker and optionally filters file extensions. The stored value is a path string. |
| `@export_dir` | Exposes a project-directory picker. The stored value is a directory path string. |
| `@export_global_file(filter...)` | Exposes a file picker that can select outside the project, subject to editor/platform restrictions. |
| `@export_global_dir` | Exposes a directory picker that can select outside the project, subject to editor/platform restrictions. |
| `@export_multiline` | Uses a multiline text editor for a string property; it does not change the string's runtime type. |
| `@export_range(min, max, step, ...)` | Adds numeric range, step, and optional slider/hint behavior. It does not by itself clamp arbitrary runtime assignments unless the code also clamps them. |
| `@export_enum(values...)` | Presents named choices and stores the corresponding enum/string value according to the declared property type. |
| `@export_flags(values...)` | Presents independent bit flags and stores the combined integer mask. |
| `@export_color_no_alpha` | Exposes a `Color` without an editable alpha channel in the Inspector. |
| `@export_storage` | Serializes the property without showing it in the Inspector. |
| `@export_tool_button(label, callable, ...)` | Adds an Inspector button that invokes a callable in a tool script; it is an editor action, not a normal serialized data field. |
| `@export_custom(...)` | Supplies low-level Inspector hint data. Its arguments must match the target Godot version's hint API exactly. |
| `@warning_ignore(name)` | Suppresses the named warning for the annotated declaration or statement only. |
| `@warning_ignore_start(name)` | Starts a warning-suppression region for the named warning. |
| `@warning_ignore_restore(name)` | Ends a matching warning-suppression region. |
| `@abstract` | Marks a class as non-instantiable or a method as requiring implementation by concrete subclasses, where supported. |
| `@rpc(...)` | Marks a method for multiplayer remote invocation and configures authority, transfer mode, channel, and call behavior. Common options include `authority`/`any_peer`, `call_remote`/`call_local`, `reliable`/`unreliable`/`unreliable_ordered`, and an integer transfer channel. The annotation does not create peers, synchronize nodes, or make arbitrary methods network-safe. |

## 23. Abstract classes and methods

An abstract class cannot be instantiated directly:

```gdscript
@abstract
class_name MovementStrategy
extends RefCounted
```

An abstract method declares an interface for subclasses:

```gdscript
@abstract
func get_velocity() -> Vector2
```

Concrete subclasses must implement required abstract methods according to the
target Godot version's rules.

## 24. Remote procedure calls

RPC annotations configure a function for multiplayer calls:

```gdscript
@rpc
func receive_message(message: String) -> void:
    print(message)
```

RPC behavior depends on the multiplayer authority, node path, peer setup,
transfer mode, and annotation options. Do not generate an RPC method without
also ensuring the node exists at the same network path on all peers.

## 25. Documentation comments

Use `##` for comments that should appear in generated class documentation:

```gdscript
## A component that tracks hit points.
class_name HealthComponent
extends Node

## Emitted when [param amount] damage is applied.
signal damaged(amount: int)

## Current hit points.
@export var health: int = 100
```

Documentation comments can describe:

- the script itself;
- classes;
- signals;
- constants;
- variables;
- functions;
- parameters and return behavior.

They support BBCode-style documentation markup, including links to classes,
methods, properties, parameters, and other documented symbols. Use the
documented tags and link forms rather than inventing Markdown links.

Common tags include:

- `@tutorial`
- `@deprecated`
- `@experimental`

Inline documentation comments are allowed after declarations where supported,
but comments above the declaration are easier for tools to associate:

```gdscript
## Maximum number of retries.
const MAX_RETRIES: int = 3
```

Members beginning with `_` are treated as private by documentation tooling
unless they are explicitly documented.

## 26. Warnings

Warnings complement static typing. They are controlled by the GDScript warning
settings in Project Settings and may be promoted to errors.

Suppress one warning:

```gdscript
@warning_ignore("unused_parameter")
func _on_event(value: int) -> void:
    pass
```

Suppress a warning for a region:

```gdscript
@warning_ignore_start("integer_division")
var ratio := 1 / 2
@warning_ignore_restore("integer_division")
```

Only suppress a warning when the behavior is intentional and the suppression
name is correct for the target Godot version. Do not silence warnings
globally just to make generated code appear clean.

## 27. String literals

Normal strings:

```gdscript
var message := "Hello, world!"
var quoted := "He said \"hello\"."
```

Single-quoted strings are also supported:

```gdscript
var path := 'res://player.gd'
```

Prefer double quotes unless single quotes substantially reduce escaping.

Multiline strings:

```gdscript
var text := """
Line one
Line two
"""
```

Raw strings are useful when backslashes should not be interpreted as ordinary
escape sequences. Use the exact raw-string delimiter syntax supported by the
target Godot version.

Common escape sequences include `\n`, `\t`, `\\`, `\"`, and `\'`.

## 28. Format strings

### 28.1 `%` formatting

Use the `%` operator with printf-style placeholders:

```gdscript
var message := "Health: %d" % health
var label := "%s has %d points" % [player_name, score]
```

Documented placeholder types include:

- `%s`: string representation
- `%c`: character
- `%d`: decimal integer
- `%o`: octal integer
- `%x`: lowercase hexadecimal
- `%X`: uppercase hexadecimal
- `%f`: floating-point value
- `%v`: Variant representation
- `%%`: literal percent sign

Width, padding, alignment, precision, and dynamic width/precision are
supported by the documented format-string grammar:

```gdscript
var padded := "%04d" % 7
var precise := "%.2f" % 3.14159
```

The value after `%` must be a single value for one placeholder or an array
whose elements fill placeholders from left to right. `%%` consumes no value.
Formatting is conversion/output syntax; it does not mutate the original
values. A placeholder's conversion must be compatible with the supplied
value, and a malformed placeholder or missing argument is an error.

When there are multiple placeholders, pass an array in the same order:

```gdscript
var message := "%s: %d/%d" % [name, current, maximum]
```

### 28.2 `String.format()`

`String.format()` uses named or indexed placeholders:

```gdscript
var message := "{name} has {score} points".format({
    "name": player_name,
    "score": score,
})
```

Dictionary formatting resolves names from dictionary keys. Array formatting
resolves numeric/indexed placeholders from array positions. Literal braces
must use the escaping rules documented for the target Godot version; missing
keys or indexes are not silently valid substitutions.

Use the formatting method that best communicates the data. Do not mix `%`
placeholder rules and `String.format()` placeholder rules in one expression.

### 28.3 Concatenation

Concatenation is valid:

```gdscript
var path := "res://" + folder + "/" + filename
```

For several values or typed conversion, format strings are generally easier to
read.

## 29. Common engine integration patterns

### 29.1 Node references

```gdscript
@onready var camera: Camera2D = $Camera2D
@onready var label: Label = %StatusLabel
```

`$Path` is shorthand for a node lookup relative to the current node.
`%Name` refers to a unique-name node configured in the scene. Both depend on
the scene structure and should be checked against the target `.tscn`.

### 29.2 Input

```gdscript
func _physics_process(_delta: float) -> void:
    var direction := Input.get_vector("move_left", "move_right", "move_up", "move_down")
    velocity = direction * speed
    move_and_slide()
```

Input action names must exist in Project Settings. A script cannot create
valid behavior by guessing action names.

### 29.3 Resources

```gdscript
const CONFIG_PATH := "res://config/game_config.tres"

var config: Resource = load(CONFIG_PATH)
var scene: PackedScene = preload("res://characters/player.tscn")
```

`preload()` resolves a constant resource path while parsing/loading the
script. `load()` resolves at runtime. Use `preload()` only for known static
paths and `load()` for dynamic paths or deferred loading.

### 29.4 Groups

```gdscript
add_to_group("enemies")
remove_from_group("enemies")
get_tree().call_group("enemies", "take_damage", 10)
```

Group names and called methods must be defined consistently across the
project.

### 29.5 Built-in and engine API semantics used above

These calls are not interchangeable conveniences. Their receiver type,
arguments, timing, and return value matter:

| Call or operation | Meaning |
| --- | --- |
| `get_parent()` | Returns the current node's immediate parent, or `null` when it has no parent. |
| `get_node(path)` | Resolves a `NodePath` relative to the current node and returns the node. A missing path reports an error and yields no usable node; use `get_node_or_null(path)` when absence is expected. |
| `get_node_or_null(path)` | Resolves a path like `get_node()` but returns `null` when no node exists instead of reporting a failed lookup. |
| `$Path` | Syntax sugar for a node lookup relative to the current node. It is resolved from the scene tree and can be invalid when the path does not exist. |
| `%Name` | Looks up a node marked as unique by name in the scene. The node must be configured as a unique-name node and be in the relevant scene scope. |
| `get_tree()` | Returns the `SceneTree` containing the current node, or null when the node is not inside a tree. |
| `has_method(name)` | Tests whether an object exposes a method with the given name; it does not call the method. |
| `call(name, args...)` | Dynamically invokes a method by name with positional arguments. It sacrifices static checking. |
| `callv(name, arguments)` | Dynamically invokes a method by name using an `Array` of arguments; use it when arguments are already collected in an array. |
| `Callable.call(args...)` | Invokes the target stored in a `Callable`. The call fails if the callable is invalid or receives incompatible arguments. |
| `Callable.callv(arguments)` | Invokes a `Callable` with an array of arguments. |
| `Callable.bind(args...)` | Returns a new callable with extra arguments appended to calls. It does not mutate the original callable. |
| `Signal.connect(callable)` | Registers a callable to run when the signal emits. Reconnecting the same callable can be an error or duplicate behavior depending on the connection state. |
| `Signal.disconnect(callable)` | Removes a previously connected callable. Use the same target and bound arguments used for connection. |
| `Signal.emit(args...)` | Emits the signal synchronously to its connected callables with the supplied arguments. |
| `add_to_group(name)` | Adds the current node to a named scene-tree group. Group membership is project/runtime state, not a type declaration. |
| `remove_from_group(name)` | Removes the current node from a named group. |
| `get_tree().call_group(name, method, args...)` | Calls a named method on every node currently in the group. Each node must implement a compatible method. |
| `queue_free()` | Schedules a node for deletion safely at the end of the current frame. References become invalid after deletion. |
| `free()` | Immediately deletes an object/node. It is more dangerous than `queue_free()` and can invalidate the current call stack or editor state. |
| `move_and_slide()` | On `CharacterBody2D`/related character bodies, moves using the body's `velocity` and performs collision sliding. It updates collision state and must be called during the appropriate physics step. |
| `Input.get_vector(negative_x, positive_x, negative_y, positive_y)` | Reads four input actions and returns a 2D direction vector, normally limited to length `1`; opposing actions cancel. The action names must exist in the Input Map. |
| `load(path)` | Loads a resource at runtime from a path and returns the loaded resource, or `null` when loading fails. The path may be dynamic, but the result must be checked or typed for the expected resource class. |
| `preload(path)` | Loads a resource when the script is parsed/loaded. The path must be a constant string known to the parser; use it for fixed dependencies. |
| `PackedScene.instantiate()` | Creates a new node hierarchy from the saved scene resource. It does not automatically add the hierarchy to the scene tree. |
| `AnimationPlayer.play(name)` | Starts playback of the named animation/library entry on an `AnimationPlayer`; the name must exist. |
| `AnimationPlayer.animation_finished` | Signal emitted when an animation finishes, subject to looping and playback behavior. |
| `Array.append(value)` | Adds a value to the end of an array. |
| `Array.push_back(value)` | Alias-style operation that appends a value to the end of an array. |
| `Array.pop_back()` | Removes and returns the last array element; behavior must be handled when the array is empty. |
| `Array.erase(value)` | Removes the first matching value, not every duplicate. |
| `Array.size()` | Returns the current number of elements. |
| `Array[index]` | Reads or writes an element by zero-based index; out-of-range access is invalid. |
| `Dictionary[key]` | Reads or writes a value by key. Missing-key behavior differs from an existing key containing null, so use explicit key checks when necessary. |
| `String.format(values)` | Replaces named or indexed `{}` placeholders using a dictionary or array; it does not use `%` placeholder syntax. |
| `str(value)` | Converts a value to its string representation. |
| `int(value)` | Converts a value to an integer using GDScript conversion rules. |
| `float(value)` | Converts a value to a floating-point value. |
| `is_nan(value)` | Tests whether a floating-point value is `NAN`; use this instead of comparing a value to `NAN`. |
| `clampi(value, min, max)` | Clamps an integer inclusively between integer bounds. |
| `mini(a, b, ...)` | Returns the smallest integer argument. |
| `maxi(a, b, ...)` | Returns the largest integer argument. |
| `Vector2.move_toward(to, delta)` / `Vector3.move_toward(to, delta)` | Returns a vector moved toward `to` by at most `delta`; it does not mutate the original vector. |
| `print(values...)` | Writes values to Godot's output/log; it is a debugging/output operation, not a user-interface display operation. |
| `range(value)` | Produces an integer sequence usable by `for`; the one-argument form ranges from zero up to, but not including, `value`. |
| `new()` | Constructor call for a class, resource, or inner class; its parameters and ownership behavior depend on the constructed type. |

`load()` and `preload()` return a general resource value until the result is
typed or checked. A failed load must not be treated as a valid resource.

## 30. Style guide

Follow these formatting rules for generated code:

- Use tabs for indentation.
- Use UTF-8, LF line endings, and no BOM.
- Keep lines under 100 characters where practical; under 80 is preferable.
- Put spaces around binary operators.
- Put a space after commas.
- Use one statement per line.
- Prefer parentheses for multiline expressions over backslash continuation.
- Use trailing commas in multiline arrays, dictionaries, and enums.
- Prefer double quotes unless escaping makes single quotes clearer.
- Use explicit parentheses when operator precedence is not obvious.

Naming:

- Classes and globally registered scripts use `PascalCase`.
- Functions, local variables, and member variables use `snake_case`.
- Constants use `CONSTANT_CASE`.
- Signals use event-style names such as `health_changed` or `died`.
- Private implementation details commonly begin with `_`.

Prefer small functions with one clear responsibility. Keep public APIs near the
top of the class and private helpers below them. Use documentation comments
for public classes and members.

## 31. Complete example

```gdscript
@icon("res://icons/player.svg")
class_name PlayerController
extends CharacterBody2D

## Emitted when the player reaches zero health.
signal died

const DEFAULT_SPEED: float = 240.0

@export_category("Movement")
@export var speed: float = DEFAULT_SPEED
@export var acceleration: float = 1200.0

@export_category("Health")
@export_range(0, 100, 1) var max_health: int = 100

@onready var animation_player: AnimationPlayer = $AnimationPlayer

var health: int

func _ready() -> void:
    health = max_health

func _physics_process(delta: float) -> void:
    var direction := Input.get_vector(
        "move_left",
        "move_right",
        "move_up",
        "move_down",
    )
    var target_velocity := direction * speed
    velocity = velocity.move_toward(target_velocity, acceleration * delta)
    move_and_slide()

func take_damage(amount: int) -> void:
    health = maxi(health - amount, 0)
    if health == 0:
        died.emit()
        animation_player.play("die")

func heal(amount: int) -> void:
    health = mini(health + amount, max_health)

func _on_hitbox_body_entered(body: Node2D) -> void:
    if body.has_method("get_contact_damage"):
        take_damage(int(body.get_contact_damage()))
```

The example is only valid when the scene contains an `AnimationPlayer`, the
animation exists, the input actions exist, and the body API is compatible.

## 32. Generation workflow

Use this process when generating a script:

1. Identify the target Godot version and the node/resource class being
   extended.
2. Decide whether the file is a global class (`class_name`) or a local script.
3. Write annotations, `class_name`, and `extends`.
4. List the public signals and document their arguments.
5. Define enums and constants.
6. Define exported configuration values with types and stable defaults.
7. Define regular member state.
8. Add `@onready` references only for nodes that exist in the scene.
9. Implement lifecycle methods supported by the base class.
10. Implement public methods with typed parameters and return values.
11. Add private helpers and inner classes.
12. Check every engine API call against the target class reference.
13. Check every node path, input action, resource path, signal, and method.
14. Run the parser and project tests if available.
15. Fix warnings deliberately rather than suppressing them blindly.

## 33. Validation checklist

The common project, type, ownership, identifier, timing, and validation
checklist in `shared_concepts.md` also applies.

### Syntax

- The filename ends in `.gd`.
- Indentation uses tabs consistently.
- Every block after `:` is indented.
- Strings, arrays, dictionaries, and parentheses are balanced.
- Annotations use valid names and argument forms.
- No Python-only syntax or Godot 3 `yield` syntax is present.

### Declarations

- `class_name` is unique when present.
- `extends` names an existing built-in class, script, or inner class.
- Constants have constant initializers.
- Exported variables have a type or constant initializer.
- Static members are used intentionally.
- Setter/getter declarations do not recurse.

### Types

- Parameters, returns, variables, arrays, and dictionaries use compatible
  types.
- `Variant` is used only where dynamic values are intended.
- `:=` does not infer an unexpectedly broad type.
- `as` results are checked before use.
- Overrides remain compatible with parent signatures.

### Runtime integration

- Node paths resolve from the correct node.
- `@onready` is used for scene-tree-dependent references.
- Input actions exist.
- Resource paths exist and match the expected resource type.
- Signals exist and are connected with compatible callables.
- RPC nodes and methods exist at matching network paths.
- Awaited objects and signals remain valid after suspension.

### Quality

- Public API is documented with `##`.
- Warnings are addressed rather than hidden.
- Code follows naming and line-length conventions.
- Tool scripts avoid unsafe editor-time assumptions.
- Destruction uses the correct lifetime method for the object type.

## 34. Failure patterns to avoid

Do not:

- write Python syntax and assume it is valid GDScript;
- use spaces mixed with tabs for indentation;
- use `yield` in a Godot 4 script;
- use `await` without considering the resumed object's lifetime;
- use `$Path` or `%Name` for a node that is not in the scene;
- call a guessed method on an engine object;
- connect a signal to a method with incompatible arguments;
- export a runtime expression that cannot be serialized as an Inspector default;
- use a dynamic value where a typed property is required;
- assume a loop variable assignment mutates the source array;
- use `match` when loose equality is required;
- create recursive setters or getters;
- free nodes unsafely from a tool script;
- suppress warnings without documenting why;
- treat documentation comments as ordinary `#` comments;
- use `%` formatting placeholders with `String.format()` syntax;
- assume a class is globally available without `class_name` or a preload;
- shadow an inherited engine method with an incompatible signature;
- invent input actions, node paths, resources, or signals.

## 35. Limits of a standalone language guide

This document describes GDScript syntax and the language features covered by
the GDScript documentation. It cannot define every API available on every
Godot class or every custom script in a project.

For any engine-specific declaration or call:

1. Confirm the base class and inheritance chain.
2. Confirm the exact method, property, signal, or constant name.
3. Confirm parameter and return types.
4. Confirm whether the call is valid in the current lifecycle phase.
5. Confirm the scene tree, project settings, and resource paths.

When the target project's generated code conflicts with a generic example,
prefer the target project's class reference and existing source code.
