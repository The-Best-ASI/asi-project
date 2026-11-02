from kedro.pipeline import Node


# First node
def return_greeting():
    return "Hello"


return_greeting_node = Node(func=return_greeting, inputs=None, outputs="my_salutation")


# Second node
def join_statements(greeting):
    return f"{greeting} Kedro!"


join_statements_node = Node(
    func=join_statements, inputs="my_salutation", outputs="my_message"
)