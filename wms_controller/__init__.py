import time
import requests
from requests.compat import urljoin
import xml.etree.ElementTree as ET
from datetime import datetime
import logging

ENDPOINT = 'protocol.xml'

GET_PARAM1 = 'protocol'
GET_PARAM2 = '_'

CMD_PREFIX = '90'
RX_LANG = '023dff'
RX_ROOM_NAME = '0203'
RX_CHANNAL_INFO = '0347'
RX_CHECK_READY = '0323'
RX_SHUTTER_STATE = '0431'

TX_MOVE_SHUTTER = '0821'
SHUTTER_POSITION = '03{}ffffff'

logger = logging.getLogger('wms_controller')


class WmsController:
    """
    This class is in charge of 
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
        r = requests.get(urljoin(self.target, ENDPOINT), params=params)
        logger.debug("Sending request: {}".format(r.request.path_url))
        logger.debug("Recieved response: {}".format(r.text))
        return ET.fromstring(r.text)

    def send_rx_lang_command(self):
        return self._send_command(RX_LANG)

    def send_rx_room_name_command(self, room_id):
        return self._send_command(RX_ROOM_NAME, format(room_id, '02x'))

    def send_rx_channel_info(self, room_id, channel_id):
        return self._send_command(RX_CHANNAL_INFO, format(room_id, '02x') + format(channel_id, '02x'))

    def send_rx_shutter_state(self, room_id, channel_id):
        return self._send_command(RX_SHUTTER_STATE, format(room_id, '02x') + format(channel_id, '02x') + '01')

    def send_tx_move_shutter(self, room_id, channel_id, new_shutter_pos):
        return self._send_command(TX_MOVE_SHUTTER, format(room_id, '02x') + format(channel_id, '02x')
                                  + SHUTTER_POSITION.format(format(new_shutter_pos, '02x')))

    def send_rx_move_shutter(self, room_id, channel_id):
        return self._send_command(RX_SHUTTER_STATE, format(room_id, '02x') + format(channel_id, '02x') + '00')

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


class Shade:
    def __init__(self, wms_ctrl: WmsController, room, channel, position=0, is_moving=False):
        self.wms_ctrl = wms_ctrl
        self.room = room
        self.channel = channel
        self.position = position #0 for open 100 for closed
        self.is_moving = is_moving
        self.state_last_updated = None

    def get_room_name(self):
        return self.room.name

    def get_channel_name(self):
        return self.channel.name

    def update_shade_state(self):
        shutter_xml = self.wms_ctrl.send_rx_shutter_state(self.room.id, self.channel.id)
        self.is_moving = False if shutter_xml.find('fahrt').text == 0 else True
        self.position = int(shutter_xml.find('position').text)/2
        self.state_last_updated = datetime.now()
        self._cmd_finished()

    def get_shade_state(self, force_update = False):
        """
        Returns the state that was received at the last update.
        :type update: bool Forces an updated if true
        :return: Returns position (0-100), is_moving (True/False), last_updated (datetime)
        """
        if force_update or self.state_last_updated is None:
            self.update_shade_state()
        return self.position, self.is_moving, self.state_last_updated

    def set_shade_position(self, new_position):
        """
        Sets shade to new_position.
        :param new_position: New position of shade (0=open, 100=closed)
        """
        self.wms_ctrl.send_tx_move_shutter(self.room.id, self.channel.id, new_position*2)
        self.wms_ctrl.send_rx_move_shutter(self.room.id, self.channel.id)
        self._cmd_finished()

    def _cmd_finished(self):
        time.sleep(0.1)
        ret = self.wms_ctrl.send_rx_check_ready(self.room.id, self.channel.id)
        feedback = ret.find('feedback')
        if feedback is None or feedback.text != '1':
            self._cmd_finished()

    @staticmethod
    def get_all_shades(wms_ctrl=WmsController()):
        shutters = []
        for room in wms_ctrl.rooms:
            for channel in room.channels:
                shutters.append(Shade(wms_ctrl, room, channel))
        return shutters
