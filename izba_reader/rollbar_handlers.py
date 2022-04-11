def ignore_handler(payload):
    if payload["data"]["environment"] == "test":
        return False
    else:
        return payload
