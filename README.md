Strowger
========

Simple switching for your Twilio SMS app.

Why
---

[Twilio's SMS capabilities](http://www.twilio.com/sms) are awesome.
[Flask](http://flask.pocoo.org/) apps are awesome.

That 200-line cascade of if/else cases in all of your nontrivial SMS apps?

Not so awesome.

Remembering to return `unicode(response)` from all of your exit points?
Kinda annoying.

Strowger adds dispatch (based on SMS message contents) and TwiML formatting
on top of Flask.

Example
-------

Strowger's basic pattern should look very familiar to you if you've ever
written a Flask application:

    from strowger import Switch

    switch = Switch(__name__)

    @switch.connect('Hello')
    def hello(request, response):
        response.message(msg='Hello, world')
        return response

Strowger matches an incoming SMS body to the
[Python regular expressions](http://docs.python.org/2/library/re.html)
configured in its list of mappings, and invokes the corresponding function.

Handler functions get passed a request object that exposes all of the
fields on [Twilio's TwiML request](http://www.twilio.com/docs/api/twiml/sms/twilio_request),
and an empty `twilio.twiml.Response` object (see https://twilio-python.readthedocs.org/en/latest/usage/twiml.html).

Details
-------

### Routing

Works roughly like Flask routing. Parameters aren't as pretty because we're
matching freeform text rather than URL paths. Named groups are supported
in match patterns, and the match object's `groupdict` will be passed as
keyword objects to the handler function:

    @switch.connect('My name is (?P<name>\w+)')
    def greet(request, response, name):
        response.message(msg='Hello, {}. Nice to meet you.'.format(name))
        return response

`connect()` accepts a `flags` argument to specify behavior for the pattern
matching. (It's passed directly to re.compile.)

    @switch.connect('Goodbye', flags=re.IGNORECASE)
    def farewell(request, response):
        response.message(msg="Good day!")
        return response

By default, Strowger will return a 404 response to any message that doesn't
match a rule. You can change this by passing a handler function to
`app.set_default_handler()`.

### Request Objects

These provide a convenient interface to the elements of the incoming TwiML
request:

- `from_number`: The number the message was sent from.
- `to_number`: The number the message was sent to.
- `message_body`: The full body of the message.
- `media_count`: The number of media items attached to the message.
- `media_items`: A list of `MediaItem` objects with the `content_type`
and `url` of each attached media item.
- `raw_values`: The underlying map of request parameters taken from the Flask
request.
- `flask_request`: If you need to access the underlying Flask request, here
it is. You can always import `flask.request` as well.

### Deployment

Nice job getting this far! Let me know what you're using Strowger for.

The Switch object is a WSGI callable just like a Flask application. (Hint:
it just dispatches straight to the Flask application.)

### Flask Handlers and the Request Path

If your app is simple enough, you probably just have one or two other routes
you want to serve as a plain-old HTTP app. The Flask object is available as
`switch.app` and you can add routes to it as you see fit.

By default, Strowger configures itself as the Flask route for '/' and will
respond to both GET and POST requests. You can override this behavior with
the `request_path` and `methods` keyword arguments to the Switch initializer.

Requirements
------------

* [Flask](http://flask.pocoo.org/)
* [twilio-python](https://github.com/twilio/twilio-python)
