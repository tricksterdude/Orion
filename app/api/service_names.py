def service_slug(value):

    return "".join(
        character.lower()
        for character in str(value or "")
        if character.isalnum()
    )
