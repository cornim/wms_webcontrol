import logging
import time
import xml.etree.ElementTree as ElemTree

import requests
from requests.compat import urljoin

ENDPOINT = 'protocol.xml'

GET_PARAM1 = 'protocol'
GET_PARAM2 = '_'

CMD_PREFIX = '90'
RX_LANG = '023dff'
RX_ROOM_NAME = '0203'
RX_CHANNAL_INFO = '0347'
RX_CHECK_READY = '0323'
RX_SHADE_STATE = '0431'

TX_MOVE_SHADE = '0821'
SHADE_POSITION = '03{}ffffff'

logger = logging.getLogger('warema_wms')


class WmsController:
    """
    This class is in charge of sending single commands to the WebControl server.
    Commands should contain no (or as little as possible) logic.

    Set log level to DEBUG to get a trace of sent commands and responses.
    """
    def _retrieve_setup(self):
        room_id = 0
        channel_id = 0
        rooms = []
        try:
            while True:
                room_xml = self.send_rx_room_name_command(room_id)
                room_name = room_xml.find('raumname').text
                if room_name is None:
                    break
                channels = []
                while True:
                    channel_xml = self.send_rx_channel_info(room_id, channel_id)
                    channel_name = channel_xml.find('kanalname').text
                    if channel_name is None:
                        channel_id = 0
                        break
                    channels.append(Channel(channel_name, channel_id))
                    channel_id += 1
                rooms.append(Room(room_name, room_id, channels))
                room_id += 1
        finally:
            self.send_rx_check_ready()
        return rooms

    def __init__(self, target='http://webcontrol.local'):
        self.target = target
        self.command_counter = 0
        self.initial_ts = int(time.time())
        self.rooms = self._retrieve_setup()

    def _increment(self):
        res = self.command_counter, self.initial_ts
        self.command_counter += 1
        if self.command_counter == 256:
            self.command_counter = 0
        self.initial_ts += 1
        return res

    def _send_command(self, cmd, additional_str=''):
        cc, ts = self._increment()
        params = {GET_PARAM1: CMD_PREFIX + format(cc, '02x') + cmd + additional_str, GET_PARAM2: str(ts)}
        r = requests.get(urljoin(self.target, ENDPOINT), params=params, timeout=10)
        logger.debug("Sending request: {}".format(r.request.path_url))
        logger.debug("Recieved response: {}".format(r.text))
        return ElemTree.fromstring(r.text)

    def send_rx_lang_command(self):
        return self._send_command(RX_LANG)

    def send_rx_room_name_command(self, room_id):
        return self._send_command(RX_ROOM_NAME, format(room_id, '02x'))

    def send_rx_channel_info(self, room_id, channel_id):
        return self._send_command(RX_CHANNAL_INFO, format(room_id, '02x') + format(channel_id, '02x'))

    def send_rx_shade_state(self, room_id, channel_id):
        return self._send_command(RX_SHADE_STATE, format(room_id, '02x') + format(channel_id, '02x') + '01')

    def send_tx_move_shade(self, room_id, channel_id, new_shade_pos):
        return self._send_command(TX_MOVE_SHADE, format(room_id, '02x') + format(channel_id, '02x')
                                  + SHADE_POSITION.format(format(new_shade_pos, '02x')))

    def send_rx_move_shade(self, room_id, channel_id):
        """
        This cmd is send out by the JS app of the web control server after the cmd to set a new shade position
        but seems to serve no purpose. (Response always contains feedback=0)
        :return: Parsed xml of the response as an xml.etree.ElementTree
        """
        return self._send_command(RX_SHADE_STATE, format(room_id, '02x') + format(channel_id, '02x') + '00')

    def send_rx_check_ready(self, room_id=0, channel_id=0):
        return self._send_command(RX_CHECK_READY, format(room_id, '02x') + format(channel_id, '02x'))


class Room:
    def __init__(self, name, id, channels):
        self.name = name
        self.id = id
        self.channels = channels


class Channel:
    def __init__(self, name, id):
        self.name = name
        self.id = id
