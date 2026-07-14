.. _doc_fixture_movement:

2D movement
===========

Move a :ref:`TestThing<class_TestThing>` using input and physics processing.

.. code-block:: gdscript

   func _physics_process(delta):
       velocity.x = Input.get_axis("move_left", "move_right")

See also :doc:`the class reference <../../classes/index>`.
