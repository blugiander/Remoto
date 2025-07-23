import json

def click(x, y):
    return json.dumps({
        'type': 'message',
        'role': 'technician',
        'target_id': 'cliente-001',
        'content': {
            'tipo': 'click',
            'x': x,
            'y': y
        }
    })

def keypress(key):
    return json.dumps({
        'type': 'message',
        'role': 'technician',
        'target_id': 'cliente-001',
        'content': {
            'tipo': 'keypress',
            'key': key
        }
    })
