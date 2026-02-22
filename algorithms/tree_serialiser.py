"""
  Given the root to a binary tree, implement serialize(root), which serializes the tree into a string, and
   deserialize(s), which deserializes the string back into the tree.

  For example, given the following Node class

  class Node:
      def __init__(self, val, left=None, right=None):
          self.val = val
          self.left = left
          self.right = right
  The following test should pass:

  node = Node('root', Node('left', Node('left.left')), Node('right'))
  assert deserialize(serialize(node)).left.left.val == 'left.left'
"""

class Node:
    def __init__(self, val, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def serialize(root):
    if root:
        return "{},{},{}".format(root.val, serialize(root.left), serialize(root.right))
    else:
        return "1"

# >>> serialize(node)
'[root,[left,[left.left,,],],[right,,]]'
'root,left,left.left,1,1,1,right,1,1'

def deserialize(values_list):
    if isinstance(values_list, str):
        values_list = values_list.split(",")
    if not values_list:
        return None
    value = values_list.pop(0)
    if value == 1:
        return None
    left = Node(deserialize(values_list))
    right = Node(deserialize(values_list))
    return Node(value, left, right)
