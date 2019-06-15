import time
from datetime import datetime
from warema_wms import WmsController

# If commands are send to quickly after each other, an error is returned.
# Hence I needed a wait time between sending the ready request and the actual command.
TIME_BETWEEN_CMDS=2


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
        """
        Forces an update of the state of the shade
        """
        Shade._try_cmd_n_times(lambda: self.wms_ctrl.send_rx_check_ready(self.room.id, self.channel.id))
        time.sleep(TIME_BETWEEN_CMDS)
        shutter_xml = self.wms_ctrl.send_rx_shade_state(self.room.id, self.channel.id)
        self.is_moving = False if shutter_xml.find('fahrt').text == '0' else True
        self.position = int(shutter_xml.find('position').text)/2
        self.state_last_updated = datetime.now()

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
        Shade._try_cmd_n_times(lambda: self.wms_ctrl.send_rx_check_ready(self.room.id, self.channel.id))
        time.sleep(TIME_BETWEEN_CMDS)
        self.wms_ctrl.send_tx_move_shade(self.room.id, self.channel.id, new_position * 2)
        # This cmd is sent by the JS app of the web control server but its purpose is unclear is feedback is always 0
        #self.wms_ctrl.send_rx_move_shutter(self.room.id, self.channel.id)

    @staticmethod
    def _try_cmd_n_times(cmd, n=5):
        for i in range(n):
            ret = cmd()
            feedback = ret.find('feedback')
            if feedback is not None and feedback.text == '1':
                return ret
            time.sleep(0.1)


    @staticmethod
    def get_all_shades(wms_ctrl=WmsController()):
        """
        Returns all shades in the WMS network which the WmsController is connected to.
        :param wms_ctrl: The WmsController to use for the connection.
        """
        shutters = []
        for room in wms_ctrl.rooms:
            for channel in room.channels:
                shutters.append(Shade(wms_ctrl, room, channel))
        return shutters
