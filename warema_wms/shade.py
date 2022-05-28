import logging
import time
from datetime import datetime

from warema_wms.wms_controller import WmsController

logger = logging.getLogger('warema_wms')


class Shade:
    def __init__(self, wms_ctrl: WmsController, room, channel,
                 time_between_cmds=0.1, num_retries=3, position=0, is_moving=False):
        """
        Initializes a Shade entity
        :param wms_ctrl: Allows to pass in your own version of a WmsController
        :param room: Room name to which Shade belongs
        :param channel: Channel name under which Shade is reachable
        :param time_between_cmds: Time between commands if multiple commands are necessary.
        If commands are send to quickly after each other, an error is returned from the webcontrol server.
        Hence a wait time between sending the ready request and the actual command is needed.
        :param number to retry a failed command
        :param position:
        :param is_moving:
        """
        self.wms_ctrl = wms_ctrl
        self.room = room
        self.channel = channel
        self.time_between_cmds = time_between_cmds
        self.num_retries = num_retries
        self.position = position  # 0 for open 100 for closed
        self.is_moving = is_moving
        self.state_last_updated = None

    def get_room_name(self):
        return self.room.name

    def get_channel_name(self):
        return self.channel.name

    def update_shade_state(self):
        """
        Forces an update of the state of the shade
        """
        self._try_cmd_n_times(lambda: self.wms_ctrl.send_rx_check_ready(self.room.id, self.channel.id),
                              self.num_retries)
        time.sleep(self.time_between_cmds)
        shutter_xml = self.wms_ctrl.send_rx_shade_state(self.room.id, self.channel.id)
        try:
            self.is_moving = False if shutter_xml.find('fahrt').text == '0' else True
            self.position = int(shutter_xml.find('position').text) / 2
            self.state_last_updated = datetime.now()
            return True
        except AttributeError:
            logger.warning("Couldn't update shade {} in room {}. Invalid response from server."
                           .format(self.get_channel_name(), self.get_room_name()))
            return False
        except Exception:
            logger.exception("Unexpected exception while updating shade {} in room {}."
                             .format(self.get_channel_name(), self.get_room_name()))
            return False

    def get_shade_state(self, force_update=False):
        """
        Returns the state that was received at the last update.
        :type update: bool Forces an updated if true
        :return: Returns position (0[open]-100[closed]), is_moving (True/False), last_updated (datetime)
        """
        if force_update or self.state_last_updated is None:
            self.update_shade_state()
        return self.position, self.is_moving, self.state_last_updated

    def set_shade_position(self, new_position):
        """
        Sets shade to new_position.
        :param new_position: New position of shade (0=open, 100=closed)
        """
        for _ in range(self.num_retries):
            self._try_cmd_n_times(lambda: self.wms_ctrl.send_rx_check_ready(self.room.id, self.channel.id),
                                  self.num_retries)
            time.sleep(self.time_between_cmds)
            self.wms_ctrl.send_tx_move_shade(self.room.id, self.channel.id, new_position * 2)
            # This cmd is sent by the JS app of the web control server but its purpose is unclear and the feedback
            # is always 0
            # self.wms_ctrl.send_rx_move_shutter(self.room.id, self.channel.id)
            if self._verify_set_cmd_sent(new_position):
                return True
        logger.warning("Shade {}:{} could not be set to target position {}"
                       .format(self.room.name, self.channel.name, new_position))
        return False

    def _try_cmd_n_times(self, cmd, n=3):
        for i in range(n):
            ret = cmd()
            feedback = ret.find('feedback')
            if feedback is None or (feedback is not None and feedback.text == '1'):
                return ret
            time.sleep(self.time_between_cmds)

    def _verify_set_cmd_sent(self, target_position):
        time.sleep(self.time_between_cmds)
        for _ in range(self.num_retries):
            self.update_shade_state()
            if self.is_moving or self.position == target_position:
                return True
            time.sleep(self.time_between_cmds)
        return False

    @staticmethod
    def get_all_shades(wms_ctrl=None, time_between_cmds=0.1, num_retries=3):
        """
        Returns all shades in the WMS network which the WmsController is connected to.
        :param num_retries: number to retry a failed command
        :param time_between_cmds: Time between commands if multiple commands are necessary.
        :param wms_ctrl: The WmsController to use for the connection.
        """
        wms_ctrl = WmsController() if wms_ctrl is None else wms_ctrl
        shutters = []
        for room in wms_ctrl.rooms:
            for channel in room.channels:
                shutters.append(Shade(wms_ctrl, room, channel, time_between_cmds, num_retries))
        return shutters
