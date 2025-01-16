def cookies_to_string(cookies_list):
    cookie_string = ''
    for cookie in cookies_list:
        cookie_string += f"{cookie['name']}={cookie['value']}; "
    
    # Remove o último '; ' se houver
    cookie_string = cookie_string.rstrip('; ')
    
    return cookie_string