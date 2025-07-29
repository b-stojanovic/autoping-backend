# state_memory.py

state = {}

def get_state(phone_number):
    return state.get(phone_number, "intro_sent")

def set_state(phone_number, new_state):
    state[phone_number] = new_state



