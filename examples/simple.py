import re

from strowger import Switch


switch = Switch(__name__)

@switch.connect('Test')
def test_handler(request, response):
    response.message(msg="Hello framework monkey!")
    return response


@switch.connect('More test')
def second_handler(request, response):
    response.message(msg="Look, a second message!")
    return response


@switch.connect('Echo (?P<message>\w+)', re.IGNORECASE)
def reply_handler(request, response, message):
    response.message(msg="Thanks for your message: {}".format(message))
    return response


if __name__ == '__main__':
    switch.run(debug=True)
