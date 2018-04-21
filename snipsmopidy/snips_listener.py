import collections
import json
import logging

import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish

from .snipsmopidy import SnipsMopidy

LOG = logging.getLogger(__name__)


def intent(name, namespace=None):
    def decorate(func):
        func._handles_intent = getattr(func, '_handles_intent', []).append((name, namespace))
        return func
    return decorate


def hotword_detected(func=None):
    def decorate(f):
        f._handles_hotword_detected = True
        return f
    if func is not None:
        return decorate(func)
    else:
        return decorate


HotwordDetected = collections.namedtuple('HotwordDetected', ('hotword_id', 'model_id', 'site_id'))
IntentDetected = collections.namedtuple(
    'IntentDetected', ('session_id', 'site_id', 'custom_data', 'input', 'intent_name', 'probability', 'slots')
)
Slot = collections.namedtuple('Slot', ('slot_name', 'raw_value', 'value', 'value_kind', 'range', 'entity', 'text'))
Range = collections.namedtuple('Range', ('start', 'end'))


class SnipsListener(object):

    def __init__(self, mqtt_host, mqtt_port=1883):
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.client = None
        self._intent_handlers = collections.defaultdict(list)
        self._hotword_detected_handlers = set()
        for attrname in dir(self):
            if attrname[:2] != '__':
                attr = getattr(self, attrname)
                if callable(attr):
                    if hasattr(attr, '_handles_intent'):
                        for intent_desc in attr._handles_intent:
                            self._intent_handlers[intent_desc].append(attr)
                    if getattr(attr, '_handles_hotword_detected', False):
                        self._hotword_detected_handlers.add(attr)

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, rc):
        LOG.debug("Connected to MQTT with result code %s", rc)

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        # TODO: only subscribe to recognized topics
        client.subscribe("hermes/intent/#")
        client.subscribe("hermes/hotword/+/detected")
        # client.subscribe("hermes/nlu/#")
        # client.subscribe("hermes/asr/#")
        # client.subscribe("hermes/dialogueManager/#")

    # def asr(self, client, userdata, msg):
    #     print(msg.topic+" "+str(msg.payload.decode()))
    #     data = json.loads(msg.payload.decode())
    #     print(data)
    #
    # def dialogueManager(self, client, userdata, msg):
    #     data = json.loads(msg.payload.decode())
    #     print(data)
    #     print(msg.topic+" "+str(msg.payload.decode()))

    # The callback for when a PUBLISH message is received from the server.
    def _handle_intent(self, client, userdata, msg):
        LOG.debug(msg.topic+" "+str(msg.payload.decode()))
        data = json.loads(msg.payload.decode())
        intent_data = data['intent']
        LOG.debug("data.sessionId="+data['sessionId'])
        LOG.debug("data.intent="+str(intent_data))
        LOG.debug("data.slots="+str(data['slots']))

        split_name = intent_data['intentName'].split(':', 1)
        if len(split_name) == 1:
            # no namespace
            lookup = (split_name[0], None)
        else:
            # name with namespace
            lookup = (split_name[1], split_name[0])


        LOG.debug("Looking for {} in {}".format(lookup, self._intent_handlers))
        handlers = self._intent_handlers.get(lookup)
        if handlers is None and lookup[1] is not None:
            # Try again with no namespace
            handlers = self._intent_handlers.get((lookup[0], None))
        LOG.debug("Lookup result: {}".format(handlers))

        if handlers is not None:
            intent_obj = IntentDetected(
                session_id=data['sessionId'],
                site_id=data['siteId'],
                custom_data=data['customData'],
                input=data['input'],
                intent_name=intent_data['intentName'],
                probability=intent_data['probability'],
                slots={
                    s['slotName']: Slot(
                        slot_name=s['slotName'],
                        raw_value=s['rawValue'],
                        value=s['value']['value'],
                        value_kind=s['value']['kind'],
                        range=Range(start=s['range']['start'], end=s['range']['end']),
                        entity=s['entity'],
                        text=data['input'][s['range']['start']:s['range']['end']]
                    )
                    for s in data.get('slots', [])
                }
            )

            LOG.debug("Intent object: {!r}".format(intent_obj))
            for h in handlers:
                h(intent_obj)

    def _handle_hotword_detected(self, client, userdata, msg):
        topic = msg.topic
        LOG.debug(topic+" "+str(msg.payload.decode()))
        _, _, hotword_id, _ = topic.split('/')
        data = json.loads(msg.payload.decode())
        for h in self._hotword_detected_handlers:
            h(HotwordDetected(hotword_id, data['modelId'], data['siteId']))

    # @intent('convertUnits', 'sigmaris')
    # def demo_intent(self, data):
    #     print("demo intent")
    #     print(repr(data))

        # # We didn't recognize that intent.
        # else:
        #     payload = {
        #         'sessionId': data.get('sessionId', ''),
        #         'text': "I am not sure what to do",
        #     }
        #     publish.single('hermes/dialogueManager/endSession',
        #                    payload=json.dumps(payload),
        #                    hostname=self.mqtt_host,
        #                    port=self.mqtt_port)
#
# def intentNotParsed(client, userdata, msg):
#     print(msg.topic+" "+str(msg.payload.decode()))
#     data = json.loads(msg.payload.decode())
#     print(data)
#
#     # I am actually not sure what message is sent for partial queries
#     if 'sessionId' in data:
#         payload = {'text': 'I am not listening to you anymore',
#                    'sessionId': data.get('sessionId', '')
#                    }
#         publish.single('hermes/dialogueManager/endSession',
#                        payload=json.dumps(payload),
#                        hostname=mqtt_host,
#                        port=mqtt_port)
#
# def intentNotRecognized(client, userdata, msg):
#     print(msg.topic+" "+str(msg.payload.decode()))
#     data = json.loads(msg.payload.decode())
#     print(data)
#
#     # Intent isn't recognized so session will already have ended
#     # so we send a notification instead.
#     if 'sessionId' in data:
#         payload = {'siteId': data.get('siteId', ''),
#                    'init': {'type': 'notification',
#                             'text': "I didn't understand you"
#                            }
#                    }
#         publish.single('hermes/dialogueManager/startSession',
#                        payload=json.dumps(payload),
#                        hostname=mqtt_host,
#                        port=mqtt_port)
#
# def nlu(client, userdata, msg):
#     print(msg.topic+" "+str(msg.payload.decode()))
#     data = json.loads(msg.payload.decode())
#     print(data)
#
# # setTimer intent handler, doesn't actually do anything as you can see
# def setTimer(client, userdata, msg):
#     print(msg.topic+" "+str(msg.payload.decode()))
#     data = json.loads(msg.payload.decode())
#     print("data.sessionId"+data['sessionId'])
#     print("data.intent"+data['intent'])
#     print("data.slots"+data['slots'])

    def connect(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect

        # These are here just to print random info for you
        # client.message_callback_add("hermes/asr/#", self.asr)
        # client.message_callback_add("hermes/dialogueManager/#", self.dialogueManager)
        # client.message_callback_add("hermes/nlu/#", self.nlu)
        # client.message_callback_add("hermes/nlu/intentNotParsed", self.intentNotParsed)
        # client.message_callback_add("hermes/nlu/intentNotRecognized",
        #                             self.intentNotRecognized)

        # This function responds to all intents
        # TODO: intent namespacing? maybe that goes in subscription code
        self.client.message_callback_add("hermes/intent/#", self._handle_intent)
        self.client.message_callback_add("hermes/hotword/+/detected", self._handle_hotword_detected)

        # This responds specifically to the setTimer intent
        # client.message_callback_add("hermes/intent/setTimer", setTimer)

        self.client.connect(self.mqtt_host, self.mqtt_port, 60)

    def loop_forever(self):
        if self.client is None:
            self.connect()

        # Blocking call that processes network traffic, dispatches callbacks and
        # handles reconnecting.
        # Other loop*() functions are available that give a threaded interface and a
        # manual interface.
        self.client.loop_forever()


class SnipsMopidyListener(SnipsListener):

    def __init__(self, mqtt_host, mqtt_port=1883, mopidy_rooms={'default': {'host': '127.0.0.1', 'port': 6600}}):
        super().__init__(mqtt_host, mqtt_port)
        self.skill = SnipsMopidy(mopidy_rooms)

    @hotword_detected
    def set_to_low_volume(self, data):
        self.skill.set_to_low_volume(data.site_id)

    @intent('speakerInterrupt')
    def pause(self, data):
        self.skill.pause(data.site_id)

    @intent('volumeUp')
    def volume_up(self, data):
        self.skill.set_to_previous_volume(data.site_id)
        if 'volume_higher' in data.slots:
            volume_higher = data.slots['volume_higher'].value
            LOG.debug("volume_higher={}".format(volume_higher))
            self.skill.volume_up(data.site_id, volume_higher)
        else:
            self.skill.volume_up(data.site_id, None)

    @intent('volumeDown')
    def volume_down(self, data):
        self.skill.set_to_previous_volume(data.site_id)
        if 'volume_lower' in data.slots:
            volume_lower = data.slots['volume_lower'].value
            LOG.debug("volume_lower={}".format(volume_lower))
            self.skill.volume_down(data.site_id, volume_lower)
        else:
            self.skill.volume_down(data.site_id, None)

    @intent('playPlaylist')
    def play_playlist(self, data):
        if len(snips.intent.playlist_name):
            playlist_name = snips.intent.playlist_name[0]
        # playlist_lecture_mode = snips.intent.playlist_lecture_mode[0] if len(snips.intent.playlist_lecture_mode) else None
        snips.skill.play_playlist(snips.site_id, playlist_name, _shuffle=(
                    len(snips.intent.playlist_lecture_mode) and snips.intent.playlist_lecture_mode[0] == "shuffle"))

        snips.skill.set_to_previous_volume(snips.site_id)
    %}
    - intent: playArtist
    action: |
    { %
    if len(snips.intent.artist_name):
        artist_name = snips.intent.artist_name[0]
    snips.skill.play_artist(snips.site_id, artist_name)
    snips.skill.set_to_previous_volume(snips.site_id)
    %}
    - intent: playSong
    action: |
    { %
    if len(snips.intent.song_name):
        snips.skill.play_song(snips.site_id, snips.intent.song_name)
    snips.skill.set_to_previous_volume(snips.site_id)
    %}
    - intent: playAlbum
    action: |
    { %
    if len(snips.intent.album_name):
        album_name = snips.intent.album_name[0]
    snips.skill.play_album(snips.site_id, album_name, _shuffle=(
                len(snips.intent.album_lecture_mode) and snips.intent.album_lecture_mode[0] == "shuffle"))

    snips.skill.set_to_previous_volume(snips.site_id)
    %}
    - intent: resumeMusic
    action: |
    { % snips.skill.play(snips.site_id);
    snips.skill.set_to_previous_volume(snips.site_id) %}
    - intent: nextSong
    action: |
    { % snips.skill.play_next_item_in_queue(snips.site_id);
    snips.skill.set_to_previous_volume(snips.site_id) %}
    - intent: previousSong
    action: |
    { % snips.skill.play_previous_item_in_queue(snips.site_id);
    snips.skill.set_to_previous_volume(snips.site_id) %}
    - intent: addSong
    action: |
    { % snips.skill.add_song(snips.site_id);
    snips.skill.set_to_previous_volume(snips.site_id) %}
    - intent: getInfos
    action: |
    { %
    snips.skill.set_to_previous_volume(snips.site_id);
    snips.dialogue.speak("This is {} by {} on the album {}".format(*snips.skill.get_info(snips.site_id)))
    %}
    - intent: "*"
    action: |
    { %
    snips.skill.set_to_previous_volume(snips.site_id);
    %}
